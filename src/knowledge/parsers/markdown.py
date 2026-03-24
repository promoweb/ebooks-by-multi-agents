"""
Markdown Document Parser for Knowledge Base System.

This module provides Markdown parsing capabilities with
YAML frontmatter support.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List

from src.knowledge.parsers.base import DocumentParser, ParsedDocument


logger = logging.getLogger("BookWriterAI")


class MarkdownParser(DocumentParser):
    """Parser for Markdown documents with YAML frontmatter support."""
    
    SUPPORTED_EXTENSIONS = {'.md', '.markdown', '.mdown'}
    
    def supports(self, file_path: Path) -> bool:
        """Check if file is a Markdown file."""
        return self.get_file_extension(file_path) in self.SUPPORTED_EXTENSIONS
    
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a Markdown document with optional YAML frontmatter."""
        # Validate file
        validation_error = self.validate_file(file_path)
        if validation_error:
            return ParsedDocument(
                content="",
                source=str(file_path),
                error=validation_error
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            metadata: Dict[str, Any] = {
                "source": str(file_path),
                "format": "markdown"
            }
            
            content = raw_content
            
            # Parse YAML frontmatter if present
            if raw_content.startswith('---'):
                content, frontmatter = self._parse_frontmatter(raw_content)
                if frontmatter:
                    metadata.update(frontmatter)
                    metadata["has_frontmatter"] = True
            
            # Extract document structure
            headers = self._extract_headers(content)
            if headers:
                metadata["headers"] = headers
                metadata["title"] = headers[0] if headers else ""
            
            # Extract links
            links = self._extract_links(content)
            if links:
                metadata["links"] = links
            
            # Extract code blocks
            code_blocks = self._extract_code_blocks(content)
            if code_blocks:
                metadata["code_blocks"] = len(code_blocks)
                metadata["languages"] = list(set(cb["language"] for cb in code_blocks if cb["language"]))
            
            return ParsedDocument(
                content=content,
                source=str(file_path),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing Markdown {file_path}: {e}")
            return ParsedDocument(
                content="",
                source=str(file_path),
                error=f"Error parsing Markdown: {str(e)}"
            )
    
    def _parse_frontmatter(self, content: str) -> tuple:
        """
        Parse YAML frontmatter from Markdown content.
        
        Returns:
            Tuple of (content_without_frontmatter, frontmatter_dict)
        """
        parts = content.split('---', 2)
        
        if len(parts) < 3:
            return content, {}
        
        frontmatter_str = parts[1].strip()
        content = parts[2].strip()
        
        # Simple YAML parsing (key: value)
        frontmatter = {}
        for line in frontmatter_str.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                frontmatter[key] = value
        
        return content, frontmatter
    
    def _extract_headers(self, content: str) -> List[str]:
        """Extract all headers from Markdown content."""
        pattern = r'^#{1,6}\s+(.+)$'
        return re.findall(pattern, content, re.MULTILINE)
    
    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract all links from Markdown content."""
        links = []
        
        # Markdown links: [text](url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(pattern, content):
            links.append({
                "text": match.group(1),
                "url": match.group(2)
            })
        
        return links
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract code blocks from Markdown content."""
        blocks = []
        
        # Fenced code blocks: ```language\ncode\n```
        pattern = r'```(\w*)\n(.*?)```'
        for match in re.finditer(pattern, content, re.DOTALL):
            blocks.append({
                "language": match.group(1) or "unknown",
                "code": match.group(2)
            })
        
        return blocks
    
    def get_outline(self, content: str) -> List[Dict[str, Any]]:
        """
        Get the document outline based on headers.
        
        Returns:
            List of headers with level and text
        """
        outline = []
        
        for line in content.split('\n'):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text = match.group(2)
                outline.append({
                    "level": level,
                    "text": text
                })
        
        return outline