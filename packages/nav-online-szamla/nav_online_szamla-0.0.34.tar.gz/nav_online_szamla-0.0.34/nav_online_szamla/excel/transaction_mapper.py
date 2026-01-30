"""
Field mapping logic for converting QueryTransactionStatusResponse to Excel row structures.

This module provides mapping functionality between transaction status responses
and flat Excel row representations.
"""

import logging
import base64
import gzip
from datetime import datetime
from typing import List, Tuple, Optional, Any
from xml.etree import ElementTree as ET

from ..models import QueryTransactionStatusResponse, InvoiceData, ManageInvoiceOperationType
from ..excel.mapper import ExcelFieldMapper
from .models import InvoiceHeaderRow, InvoiceLineRow, TransactionStatusRow
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser

logger = logging.getLogger(__name__)


class TransactionFieldMapper:
    """
    Handles mapping between QueryTransactionStatusResponse objects and Excel row structures.
    """
    
    # Request status mapping to Hungarian
    REQUEST_STATUS_MAPPING = {
        'RECEIVED': 'Befogadva',
        'PROCESSING': 'Feldolgozás alatt',
        'SAVED': 'Elmentve',
        'FINISHED': 'Feldolgozás befejezve',
        'NOTIFIED': 'Lekérdezve',
    }
    
    def __init__(self):
        """Initialize the transaction field mapper."""
        self.invoice_mapper = ExcelFieldMapper()
    
    def _map_request_status(self, status: Optional[str]) -> str:
        """
        Map request status enum value to Hungarian text.
        
        Args:
            status: Request status value (e.g., 'RECEIVED', 'PROCESSING')
            
        Returns:
            str: Hungarian translation or original value if not found
        """
        if not status or status == "n/a":
            return "n/a"
        return self.REQUEST_STATUS_MAPPING.get(status, status)
    
    def _map_boolean_to_hungarian(self, value: Optional[bool]) -> str:
        """
        Map boolean value to Hungarian text.
        
        Args:
            value: Boolean value (True, False, or None)
            
        Returns:
            str: "Igen" for True, "Nem" for False, "n/a" for None
        """
        if value is None:
            return "n/a"
        return "Igen" if value else "Nem"
    
    def transaction_response_to_rows(
        self, 
        transaction_response: QueryTransactionStatusResponse,
        transaction_id: str = None,
        request_status: str = None,
        technical_annulment: bool = None,
        ins_date: str = None
    ) -> Tuple[List[InvoiceHeaderRow], List[InvoiceLineRow], List[TransactionStatusRow]]:
        """
        Convert transaction status response to Excel row data.
        
        Args:
            transaction_response: The transaction status response
            transaction_id: The original transaction ID from the transaction list
            request_status: The request status from the transaction list
            technical_annulment: Whether the transaction contains technical annulment
            ins_date: The submission timestamp (ins_date) from the transaction
            
        Returns:
            Tuple of (header_rows, line_rows, status_rows)
        """
        header_rows = []
        line_rows = []
        status_rows = []
        
        try:
            # Use provided transaction_id parameter, fall back to response if not provided
            if transaction_id is None:
                transaction_id = getattr(transaction_response, 'transaction_id', None)
            
            # Extract processing results if available
            processing_results = getattr(transaction_response, 'processing_results', None)
            if not processing_results:
                # Create a basic status row even if no processing results
                status_row = self._create_basic_status_row(
                    transaction_response, 
                    transaction_id,
                    request_status,
                    technical_annulment,
                    ins_date
                )
                status_rows.append(status_row)
                return header_rows, line_rows, status_rows
            
            # Check if processing_results is iterable
            if not hasattr(processing_results, '__iter__'):
                # If it's not a list, try to access as a single object or convert to list
                if hasattr(processing_results, 'processing_result'):
                    # Handle case where it's a container with processing_result items
                    results_list = processing_results.processing_result
                    if not hasattr(results_list, '__iter__'):
                        results_list = [results_list]
                else:
                    # Treat as single result
                    results_list = [processing_results]
            else:
                results_list = processing_results
            
            # Process each result in the processing results
            for result in results_list:
                try:
                    # Extract invoice data from original request if available
                    invoice_data = self._extract_invoice_data_from_original_request(result)
                    if invoice_data:
                        # Check if this is a full InvoiceData object or just an AnnulmentData
                        if hasattr(invoice_data, 'invoice_issue_date'):
                            # This is a full InvoiceData object - process header and lines
                            operation_type = self._extract_operation_type(result)
                            
                            header_row = self.invoice_mapper.invoice_data_to_header_row(invoice_data, operation_type)
                            header_rows.append(header_row)
                            
                            line_row_list = self.invoice_mapper.invoice_data_to_line_rows(invoice_data, operation_type)
                            line_rows.extend(line_row_list)
                        # For AnnulmentData objects, we skip header/line processing since annulments 
                        # only reference the original invoice - they don't contain invoice structure
                    
                    # Create status row for this result
                    status_row = self._create_status_row(
                        transaction_response, 
                        result, 
                        transaction_id,
                        request_status,
                        technical_annulment,
                        ins_date
                    )
                    status_rows.append(status_row)
                    
                except Exception as e:
                    logger.warning(f"Failed to process individual result in transaction {transaction_id}: {e}")
                    # Create error status row
                    error_status_row = self._create_error_status_row(transaction_response, str(e), ins_date)
                    status_rows.append(error_status_row)
                    continue
            
            return header_rows, line_rows, status_rows
            
        except Exception as e:
            logger.error(f"Failed to convert transaction response {transaction_id}: {e}")
            # Create error status row
            error_status_row = self._create_error_status_row(transaction_response, str(e), ins_date)
            status_rows.append(error_status_row)
            return header_rows, line_rows, status_rows
    
    def _extract_operation_type(self, result) -> ManageInvoiceOperationType:
        """
        Extract operation type from processing result.
        
        Args:
            result: Processing result object
            
        Returns:
            ManageInvoiceOperationType: The operation type
        """
        try:
            # Try to get operation type from result
            operation = getattr(result, 'invoice_operation', None)
            if operation:
                operation_type = getattr(operation, 'operation_type', None)
                if operation_type:
                    return operation_type
            
            # Default to CREATE if not found
            return ManageInvoiceOperationType.CREATE
            
        except Exception:
            return ManageInvoiceOperationType.CREATE
    
    def _extract_invoice_data_from_original_request(self, result) -> Optional[Any]:
        """
        Extract InvoiceData or InvoiceAnnulment from the originalRequest field of a processing result.
        
        Args:
            result: Processing result object that may contain originalRequest
            
        Returns:
            Optional[Any]: Extracted invoice data/annulment data or None
        """
        try:
            # Get the original request
            original_request = getattr(result, 'original_request', None)
            if not original_request:
                return None

            # Check if content is compressed
            compressed = getattr(result, 'compressed_content_indicator', False)
            
            # Debug: Log what we have
            logger.debug(f"Original request type: {type(original_request)}")
            logger.debug(f"Compressed: {compressed}")
            
            # Convert to bytes if needed
            xml_data = None
            
            if isinstance(original_request, str):
                xml_data_bytes = original_request.encode('utf-8')
            elif isinstance(original_request, bytes):
                xml_data_bytes = original_request
            else:
                xml_data_bytes = str(original_request).encode('utf-8')
            
            # Check if data is already raw gzip (starts with gzip magic bytes)
            is_gzip = xml_data_bytes[:2] == b'\x1f\x8b'
            
            if is_gzip:
                # Data is already raw gzip bytes, skip BASE64 decoding
                logger.debug("Detected raw gzip data, skipping BASE64 decode")
                xml_data = xml_data_bytes
            else:
                # Try BASE64 decoding (data should be BASE64 encoded)
                try:
                    # Try to parse as XML first (might already be plain XML)
                    ET.fromstring(xml_data_bytes)
                    xml_data = xml_data_bytes
                    logger.debug("Data is already plain XML")
                except ET.ParseError:
                    # Not plain XML, try BASE64 decoding with padding fix
                    try:
                        # Fix padding if needed
                        missing_padding = len(xml_data_bytes) % 4
                        if missing_padding:
                            xml_data_bytes = xml_data_bytes + b'=' * (4 - missing_padding)
                        xml_data = base64.b64decode(xml_data_bytes)
                        logger.debug("Successfully BASE64 decoded")
                    except Exception as e:
                        logger.debug(f"BASE64 decode failed, using data as-is: {e}")
                        xml_data = xml_data_bytes
            
            # Decompress if needed (only if compressed flag is set or data is gzip)
            if compressed or is_gzip:
                try:
                    xml_data = gzip.decompress(xml_data)
                    logger.debug("Successfully decompressed gzip data")
                except gzip.BadGzipFile as e:
                    logger.debug(f"Gzip decompress failed (data may not be compressed): {e}")
                    # Data might not actually be compressed, continue with original
                    pass
            
            # Parse XML to find InvoiceData or InvoiceAnnulment element
            try:
                root = ET.fromstring(xml_data)
            except ET.ParseError as e:
                logger.debug(f"Failed to parse XML from original request: {e}")
                return None
            
            # Check schema version - only v3.0 is supported
            namespace = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
            if '2.0' in namespace or '1.0' in namespace:
                logger.warning(f"Skipping invoice data extraction - unsupported schema version in namespace: {namespace}")
                logger.warning("Only API v3.0 invoice data can be fully parsed. Transaction status will still be exported.")
                return None
            
            # Look for InvoiceData elements first (regular transactions)
            if root.tag.endswith('InvoiceData'):
                invoice_data_element = root
            else:
                # If not direct InvoiceData, search for it
                invoice_data_element = None
                for elem in root.iter():
                    if elem.tag.endswith('InvoiceData'):
                        invoice_data_element = elem
                        break
            
            if invoice_data_element is not None:
                # Convert XML element back to InvoiceData object using xsdata
                context = XmlContext()
                parser = XmlParser(context=context)
                
                # Convert the XML element to string and parse it as InvoiceData
                invoice_xml = ET.tostring(invoice_data_element, encoding='unicode')
                invoice_data = parser.from_string(invoice_xml, InvoiceData)
                
                return invoice_data
            
            # Look for InvoiceAnnulment elements (technical annulment transactions)
            annulment_element = None
            if root.tag.endswith('InvoiceAnnulment'):
                annulment_element = root
            else:
                # If not direct InvoiceAnnulment, search for it
                for elem in root.iter():
                    if elem.tag.endswith('InvoiceAnnulment'):
                        annulment_element = elem
                        break
            
            if annulment_element is not None:
                # For technical annulments, extract the annulmentReference as invoice number
                annulment_ref = None
                for elem in annulment_element.iter():
                    if elem.tag.endswith('annulmentReference'):
                        annulment_ref = elem.text
                        break
                
                if annulment_ref:
                    # Create a minimal object with invoice_number attribute to match InvoiceData interface
                    class AnnulmentData:
                        def __init__(self, invoice_number: str):
                            self.invoice_number = invoice_number
                    
                    return AnnulmentData(annulment_ref)
            
            logger.warning("No InvoiceData or InvoiceAnnulment element found in original request")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract invoice data from original request: {e}")
            logger.error(f" Original request content: {result}")
            return None
    
    def _create_basic_status_row(
        self, 
        transaction_response: QueryTransactionStatusResponse,
        transaction_id: str = None,
        request_status: str = None,
        technical_annulment: bool = None,
        ins_date: str = None
    ) -> TransactionStatusRow:
        """
        Create a basic status row when no processing results are available.
        
        Args:
            transaction_response: The transaction status response
            transaction_id: The original transaction ID from the transaction list
            request_status: The request status from the transaction list
            technical_annulment: Whether the transaction contains technical annulment
            ins_date: The submission timestamp from the transaction
            
        Returns:
            TransactionStatusRow: Basic status row
        """
        return TransactionStatusRow(
            transaction_id=transaction_id or getattr(transaction_response, 'transaction_id', None),
            submission_timestamp=self._format_timestamp(ins_date),
            request_status=self._map_request_status(request_status) if request_status else "n/a",
            technical_annulment=self._map_boolean_to_hungarian(technical_annulment),
        )
    
    def _create_status_row(
        self, 
        transaction_response: QueryTransactionStatusResponse, 
        result,
        transaction_id: str = None,
        request_status: str = None,
        technical_annulment: bool = None,
        ins_date: str = None
    ) -> TransactionStatusRow:
        """
        Create a status row from transaction response and processing result.
        
        Args:
            transaction_response: The transaction status response
            result: Individual processing result
            transaction_id: The original transaction ID from the transaction list
            request_status: The request status from the transaction list
            technical_annulment: Whether the transaction contains technical annulment
            ins_date: The submission timestamp from the transaction
            
        Returns:
            TransactionStatusRow: Status row with detailed information
        """
        try:
            # Get basic identifiers from response header and parameters
            transaction_id = transaction_id or "n/a"  # Use provided transaction_id
            submission_timestamp = self._format_timestamp(ins_date)
            
            # Extract invoice number from original request if available
            invoice_number = "n/a"
            if hasattr(result, 'original_request') and result.original_request:
                invoice_data = self._extract_invoice_data_from_original_request(result)
                if invoice_data and hasattr(invoice_data, 'invoice_number'):
                    invoice_number = invoice_data.invoice_number
            
            # Get invoice status from processing result
            invoice_status = "n/a"
            if hasattr(result, 'invoice_status') and result.invoice_status:
                invoice_status = str(result.invoice_status.value) if hasattr(result.invoice_status, 'value') else str(result.invoice_status)
            
            # Extract validation messages
            business_validation_messages = self._extract_validation_messages(result, 'business_validation_messages')
            technical_validation_messages = self._extract_validation_messages(result, 'technical_validation_messages')
            
            # get operation type
            operation_type = 'CREATE'
            if hasattr(invoice_data, 'invoice_main') and hasattr(invoice_data.invoice_main, 'invoice') and hasattr(invoice_data.invoice_main.invoice, 'invoice_reference') and invoice_data.invoice_main.invoice.invoice_reference is not None:
                operation_type = 'MODIFY/STORNO'

            return TransactionStatusRow(
                transaction_id=transaction_id,
                submission_timestamp=submission_timestamp,
                invoice_number=invoice_number,
                invoice_status=invoice_status,
                operation_type=operation_type,
                request_status=self._map_request_status(request_status),
                technical_annulment=self._map_boolean_to_hungarian(technical_annulment),
                business_validation_messages=business_validation_messages,
                technical_validation_messages=technical_validation_messages
            )
            
        except Exception as e:
            logger.error(f"Failed to create status row: {e}")
            return self._create_error_status_row(transaction_response, str(e), ins_date)
    
    def _create_error_status_row(
        self, 
        transaction_response: QueryTransactionStatusResponse, 
        error_message: str,
        ins_date: str = None
    ) -> TransactionStatusRow:
        """
        Create an error status row when processing fails.
        
        Args:
            transaction_response: The transaction status response
            error_message: Error message to include
            ins_date: The submission timestamp from the transaction
            
        Returns:
            TransactionStatusRow: Error status row
        """
        return TransactionStatusRow(
            transaction_id=getattr(transaction_response, 'transaction_id', None),
            submission_timestamp=self._format_timestamp(ins_date),
            request_status="HIBA",
            technical_validation_messages=error_message
        )
    
    def _extract_validation_messages(self, result, field_name: str) -> Optional[str]:
        """
        Extract and concatenate validation messages from a result field.
        
        Args:
            result: Processing result object
            field_name: Name of the field containing messages
            
        Returns:
            Optional[str]: Concatenated messages in format "result_code:validation_error_code:message | ..." or None
        """
        try:
            messages = getattr(result, field_name, None)
            if not messages:
                return None
            
            message_strings = []
            
            # Handle both single message and list of messages
            if isinstance(messages, list):
                for msg in messages:
                    result_code = msg.validation_result_code.value if msg.validation_result_code else "UNKNOWN"
                    error_code = msg.validation_error_code or ""
                    message = msg.message or ""
                    message_strings.append(f"{result_code}|:{error_code}|:{message}")
            else:
                # Single message
                result_code = messages.validation_result_code.value if messages.validation_result_code else "UNKNOWN"
                error_code = messages.validation_error_code or ""
                message = messages.message or ""
                message_strings.append(f"{result_code}|:{error_code}|:{message}")
            
            return "||".join(message_strings) if message_strings else None
                    
        except Exception as e:
            logger.warning(f"Failed to extract {field_name}: {e}")
            return None
    
    def _format_timestamp(self, timestamp) -> Optional[str]:
        """
        Format timestamp for Excel display.
        
        Args:
            timestamp: Timestamp object or string
            
        Returns:
            Optional[str]: Formatted timestamp string
        """
        try:
            if not timestamp:
                return None
            
            if isinstance(timestamp, str):
                return timestamp
            
            if hasattr(timestamp, 'isoformat'):
                return timestamp.isoformat()
            
            return str(timestamp)
            
        except Exception:
            return str(timestamp) if timestamp else None