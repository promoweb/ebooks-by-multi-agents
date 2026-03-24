"""
PDF Document Parser for Knowledge Base System.

This module provides PDF parsing capabilities using PyPDF2.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.knowledge.parsers.base import DocumentParser, ParsedDocument


logger = logging.getLogger("BookWriterAI")

# Check for PDF support
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PyPDF2 not installed. PDF support disabled. Install with: pip install PyPDF2")


class PDFParser(DocumentParser):
    """Parser for PDF documents."""
    
    def supports(self, file_path: Path) -> bool:
        """Check if file is a PDF and PDF support is available."""
        return PDF_SUPPORT and self.get_file_extension(file_path) == '.pdf'
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a PDF document and extract text content."""
        if not PDF_SUPPORT:
            return ParsedDocument(
                content="",
                source=str(file_path),
                error="PyPDF2 not installed. Install with: pip install PyPDF2"
            )
        
        # Validate file
        validation_error = self.validate_file(file_path)
        if validation_error:
            return ParsedDocument(
                content="",
                source=str(file_path),
                error=validation_error
            )
        
        try:
            text_parts = []
            metadata: Dict[str, Any] = {
                "source": str(file_path),
                "format": "pdf",
                "pages": 0
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                # Extract PDF metadata if available
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    if pdf_meta.get('/Title'):
                        metadata["title"] = pdf_meta['/Title']
                    if pdf_meta.get('/Author'):
                        metadata["author"] = pdf_meta['/Author']
                    if pdf_meta.get('/Subject'):
                        metadata["subject"] = pdf_meta['/Subject']
                    if pdf_meta.get('/Creator'):
                        metadata["creator"] = pdf_meta['/Creator']
                    if pdf_meta.get('/Producer'):
                        metadata["producer"] = pdf_meta['/Producer']
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1} from {file_path}: {e}")
                        continue
            
            content = "\n".join(text_parts)
            
            if not content.strip():
                return ParsedDocument(
                    content="",
                    source=str(file_path),
                    metadata=metadata,
                    error="No text extracted from PDF (may be scanned or image-based)"
                )
            
            return ParsedDocument(
                content=content,
                source=str(file_path),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return ParsedDocument(
                content="",
                source=str(file_path),
                error=f"Error parsing PDF: {str(e)}"
            )