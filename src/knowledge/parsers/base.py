"""
Base Document Parser for Knowledge Base System.

This module provides the abstract base class for document parsers,
implementing the Strategy pattern for different document formats.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """
    Represents a parsed document with content and metadata.
    
    Attributes:
        content: The extracted text content
        source: Path to the source file
        metadata: Document metadata (title, author, etc.)
        error: Error message if parsing failed
        chunks: List of chunk IDs after chunking
    """
    content: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    chunks: list = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if the document was parsed successfully."""
        return self.error is None and bool(self.content.strip())
    
    @property
    def word_count(self) -> int:
        """Get the word count of the content."""
        return len(self.content.split()) if self.content else 0


class DocumentParser(ABC):
    """
    Abstract base class for document parsers.
    
    Implements the Strategy pattern to allow different parsing
    strategies for different document formats.
    """
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a document and extract its content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ParsedDocument with content and metadata
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """
        Check if this parser supports the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if this parser can handle the file
        """
        pass
    
    def get_file_extension(self, file_path: Path) -> str:
        """Get the lowercase file extension."""
        return file_path.suffix.lower()
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size if file_path.exists() else 0
    
    def validate_file(self, file_path: Path) -> Optional[str]:
        """
        Validate that the file can be parsed.
        
        Returns:
            Error message if validation fails, None otherwise
        """
        if not file_path.exists():
            return f"File does not exist: {file_path}"
        
        if not file_path.is_file():
            return f"Path is not a file: {file_path}"
        
        if self.get_file_size(file_path) == 0:
            return f"File is empty: {file_path}"
        
        return None