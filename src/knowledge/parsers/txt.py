"""
Text Document Parser for Knowledge Base System.

This module provides plain text parsing capabilities with
multi-encoding support.
"""

import logging
from pathlib import Path
from typing import List

from src.knowledge.parsers.base import DocumentParser, ParsedDocument


logger = logging.getLogger("BookWriterAI")


class TXTParser(DocumentParser):
    """Parser for plain text documents with multi-encoding support."""
    
    # Common encodings to try
    SUPPORTED_ENCODINGS: List[str] = [
        'utf-8',
        'utf-16',
        'utf-16-le',
        'utf-16-be',
        'iso-8859-1',
        'iso-8859-15',
        'cp1252',
        'cp1250',
        'ascii',
        'latin-1'
    ]
    
    SUPPORTED_EXTENSIONS = {'.txt', '.text', '.log'}
    
    def supports(self, file_path: Path) -> bool:
        """Check if file is a text file."""
        return self.get_file_extension(file_path) in self.SUPPORTED_EXTENSIONS
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a text document with automatic encoding detection."""
        # Validate file
        validation_error = self.validate_file(file_path)
        if validation_error:
            return ParsedDocument(
                content="",
                source=str(file_path),
                error=validation_error
            )
        
        # Try different encodings
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                # Success - return with metadata
                return ParsedDocument(
                    content=content,
                    source=str(file_path),
                    metadata={
                        "source": str(file_path),
                        "format": "text",
                        "encoding": encoding,
                        "size_bytes": self.get_file_size(file_path)
                    }
                )
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading {file_path} with encoding {encoding}: {e}")
                return ParsedDocument(
                    content="",
                    source=str(file_path),
                    error=f"Error reading file: {str(e)}"
                )
        
        # All encodings failed
        return ParsedDocument(
            content="",
            source=str(file_path),
            error=f"Could not decode file with any supported encoding: {self.SUPPORTED_ENCODINGS}"
        )