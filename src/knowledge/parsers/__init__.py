"""
Document Parsers for Knowledge Base System.

This module provides parsers for various document formats.
"""

from typing import Dict, Type, List
from pathlib import Path

from src.knowledge.parsers.base import DocumentParser, ParsedDocument
from src.knowledge.parsers.pdf import PDFParser
from src.knowledge.parsers.txt import TXTParser
from src.knowledge.parsers.markdown import MarkdownParser


# Registry of all available parsers
PARSER_REGISTRY: Dict[str, Type[DocumentParser]] = {
    "pdf": PDFParser,
    "txt": TXTParser,
    "markdown": MarkdownParser,
}


def get_parser(parser_type: str) -> DocumentParser:
    """
    Get a parser instance by type.
    
    Args:
        parser_type: Type of parser ('pdf', 'txt', 'markdown')
    
    Returns:
        DocumentParser instance
    
    Raises:
        ValueError: If parser type is not recognized
    """
    if parser_type not in PARSER_REGISTRY:
        raise ValueError(
            f"Unknown parser type: {parser_type}. "
            f"Available types: {list(PARSER_REGISTRY.keys())}"
        )
    
    return PARSER_REGISTRY[parser_type]()


def get_parser_for_file(file_path: Path) -> DocumentParser:
    """
    Get appropriate parser for a file based on its extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        DocumentParser that can handle the file
    
    Raises:
        ValueError: If no parser supports the file type
    """
    for parser_class in PARSER_REGISTRY.values():
        parser = parser_class()
        if parser.supports(file_path):
            return parser
    
    raise ValueError(
        f"No parser supports file: {file_path}. "
        f"Supported extensions: {get_supported_extensions()}"
    )


def get_supported_extensions() -> List[str]:
    """Get list of all supported file extensions."""
    extensions = set()
    for parser_class in PARSER_REGISTRY.values():
        parser = parser_class()
        extensions.update(parser.SUPPORTED_EXTENSIONS)
    return sorted(list(extensions))


def parse_file(file_path: Path) -> ParsedDocument:
    """
    Parse a file using the appropriate parser.
    
    Args:
        file_path: Path to the file to parse
    
    Returns:
        ParsedDocument with content and metadata
    """
    parser = get_parser_for_file(file_path)
    return parser.parse(file_path)


def parse_files(file_paths: List[Path]) -> List[ParsedDocument]:
    """
    Parse multiple files.
    
    Args:
        file_paths: List of file paths to parse
    
    Returns:
        List of ParsedDocument objects
    """
    return [parse_file(fp) for fp in file_paths]


__all__ = [
    # Base classes
    "DocumentParser",
    "ParsedDocument",
    
    # Concrete parsers
    "PDFParser",
    "TXTParser",
    "MarkdownParser",
    
    # Registry and utilities
    "PARSER_REGISTRY",
    "get_parser",
    "get_parser_for_file",
    "get_supported_extensions",
    "parse_file",
    "parse_files",
]