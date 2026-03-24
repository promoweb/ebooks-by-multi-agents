"""
Text Chunker for Knowledge Base System.

This module provides text chunking capabilities for breaking
large documents into smaller, manageable pieces for retrieval.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class ChunkStrategy(Enum):
    """Strategy for chunking text."""
    FIXED_SIZE = "fixed_size"  # Fixed character/word count
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking
    SEMANTIC = "semantic"  # Semantic similarity-based (requires embeddings)
    SLIDING_WINDOW = "sliding_window"  # Overlapping windows


@dataclass
class Chunk:
    """Represents a text chunk."""
    id: str
    content: str
    source: str
    start_index: int
    end_index: int
    token_count: int
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "token_count": self.token_count,
            "metadata": self.metadata
        }


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""
    strategy: ChunkStrategy = ChunkStrategy.SLIDING_WINDOW
    chunk_size: int = 500  # Target tokens per chunk
    chunk_overlap: int = 50  # Overlap between chunks (tokens)
    min_chunk_size: int = 100  # Minimum chunk size
    max_chunk_size: int = 1000  # Maximum chunk size
    respect_sentence_boundaries: bool = True
    respect_paragraph_boundaries: bool = False
    include_context: bool = True  # Include surrounding context


class TextChunker:
    """
    Chunks text into smaller pieces for retrieval.
    
    Supports multiple chunking strategies:
    - Fixed size: Simple character/word count
    - Sentence: Respects sentence boundaries
    - Paragraph: Respects paragraph boundaries
    - Sliding window: Overlapping windows for better context
    """
    
    # Approximate characters per token (for estimation)
    CHARS_PER_TOKEN = 4
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize the text chunker.
        
        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkingConfig()
    
    def chunk(
        self,
        text: str,
        source: str = "",
        metadata: Optional[dict] = None
    ) -> List[Chunk]:
        """
        Chunk text according to configured strategy.
        
        Args:
            text: Text to chunk
            source: Source identifier
            metadata: Additional metadata to include in chunks
        
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        # Select chunking strategy
        if self.config.strategy == ChunkStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, source, metadata)
        elif self.config.strategy == ChunkStrategy.SENTENCE:
            return self._chunk_by_sentence(text, source, metadata)
        elif self.config.strategy == ChunkStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, source, metadata)
        elif self.config.strategy == ChunkStrategy.SLIDING_WINDOW:
            return self._chunk_sliding_window(text, source, metadata)
        else:
            logger.warning(
                f"Unknown strategy {self.config.strategy}, "
                f"using sliding window"
            )
            return self._chunk_sliding_window(text, source, metadata)
    
    def _chunk_fixed_size(
        self,
        text: str,
        source: str,
        metadata: dict
    ) -> List[Chunk]:
        """Chunk text into fixed-size pieces."""
        chunks = []
        
        # Estimate character positions
        chars_per_chunk = self.config.chunk_size * self.CHARS_PER_TOKEN
        overlap_chars = self.config.chunk_overlap * self.CHARS_PER_TOKEN
        
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + chars_per_chunk, len(text))
            chunk_text = text[start:end]
            
            # Calculate token count
            token_count = self._estimate_tokens(chunk_text)
            
            chunk = Chunk(
                id=f"{source}_chunk_{chunk_id}",
                content=chunk_text,
                source=source,
                start_index=start,
                end_index=end,
                token_count=token_count,
                metadata={
                    **metadata,
                    "chunk_index": chunk_id,
                    "strategy": "fixed_size"
                }
            )
            chunks.append(chunk)
            
            chunk_id += 1
            start = end - overlap_chars if end < len(text) else len(text)
        
        return chunks
    
    def _chunk_by_sentence(
        self,
        text: str,
        source: str,
        metadata: dict
    ) -> List[Chunk]:
        """Chunk text respecting sentence boundaries."""
        chunks = []
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_tokens = 0
        current_start = 0
        chunk_id = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self._estimate_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.config.chunk_size:
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(Chunk(
                        id=f"{source}_chunk_{chunk_id}",
                        content=chunk_text,
                        source=source,
                        start_index=current_start,
                        end_index=current_start + len(chunk_text),
                        token_count=current_tokens,
                        metadata={
                            **metadata,
                            "chunk_index": chunk_id,
                            "strategy": "sentence",
                            "sentence_count": len(current_chunk)
                        }
                    ))
                    chunk_id += 1
                
                current_chunk = [sentence]
                current_tokens = sentence_tokens
                current_start = text.find(sentence, current_start)
            else:
                if not current_chunk:
                    current_start = text.find(sentence)
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Chunk(
                id=f"{source}_chunk_{chunk_id}",
                content=chunk_text,
                source=source,
                start_index=current_start,
                end_index=current_start + len(chunk_text),
                token_count=current_tokens,
                metadata={
                    **metadata,
                    "chunk_index": chunk_id,
                    "strategy": "sentence",
                    "sentence_count": len(current_chunk)
                }
            ))
        
        return chunks
    
    def _chunk_by_paragraph(
        self,
        text: str,
        source: str,
        metadata: dict
    ) -> List[Chunk]:
        """Chunk text respecting paragraph boundaries."""
        chunks = []
        paragraphs = self._split_paragraphs(text)
        
        current_chunk = []
        current_tokens = 0
        current_start = 0
        chunk_id = 0
        
        for paragraph in paragraphs:
            para_tokens = self._estimate_tokens(paragraph)
            
            if current_tokens + para_tokens > self.config.chunk_size:
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(Chunk(
                        id=f"{source}_chunk_{chunk_id}",
                        content=chunk_text,
                        source=source,
                        start_index=current_start,
                        end_index=current_start + len(chunk_text),
                        token_count=current_tokens,
                        metadata={
                            **metadata,
                            "chunk_index": chunk_id,
                            "strategy": "paragraph",
                            "paragraph_count": len(current_chunk)
                        }
                    ))
                    chunk_id += 1
                
                current_chunk = [paragraph]
                current_tokens = para_tokens
                current_start = text.find(paragraph)
            else:
                if not current_chunk:
                    current_start = text.find(paragraph)
                current_chunk.append(paragraph)
                current_tokens += para_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(Chunk(
                id=f"{source}_chunk_{chunk_id}",
                content=chunk_text,
                source=source,
                start_index=current_start,
                end_index=current_start + len(chunk_text),
                token_count=current_tokens,
                metadata={
                    **metadata,
                    "chunk_index": chunk_id,
                    "strategy": "paragraph",
                    "paragraph_count": len(current_chunk)
                }
            ))
        
        return chunks
    
    def _chunk_sliding_window(
        self,
        text: str,
        source: str,
        metadata: dict
    ) -> List[Chunk]:
        """
        Chunk text using sliding window with overlap.
        
        This strategy provides better context preservation
        by overlapping chunks.
        """
        chunks = []
        
        # Convert token sizes to character sizes
        chars_per_chunk = self.config.chunk_size * self.CHARS_PER_TOKEN
        overlap_chars = self.config.chunk_overlap * self.CHARS_PER_TOKEN
        step = chars_per_chunk - overlap_chars
        
        if step <= 0:
            step = chars_per_chunk // 2
        
        chunk_id = 0
        start = 0
        
        while start < len(text):
            end = min(start + chars_per_chunk, len(text))
            
            # Adjust boundaries to respect sentence boundaries if configured
            if self.config.respect_sentence_boundaries and end < len(text):
                # Find the last sentence boundary within the chunk
                last_period = text.rfind('.', start, end)
                last_question = text.rfind('?', start, end)
                last_exclaim = text.rfind('!', start, end)
                
                last_sentence_end = max(last_period, last_question, last_exclaim)
                
                if last_sentence_end > start + self.config.min_chunk_size * self.CHARS_PER_TOKEN:
                    end = last_sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                token_count = self._estimate_tokens(chunk_text)
                
                chunk = Chunk(
                    id=f"{source}_chunk_{chunk_id}",
                    content=chunk_text,
                    source=source,
                    start_index=start,
                    end_index=end,
                    token_count=token_count,
                    metadata={
                        **metadata,
                        "chunk_index": chunk_id,
                        "strategy": "sliding_window",
                        "overlap_tokens": self.config.chunk_overlap
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
            
            start += step
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        This is a simple estimation. For accurate counts,
        use a tokenizer like tiktoken.
        """
        # Simple estimation: ~4 characters per token
        return len(text) // self.CHARS_PER_TOKEN + 1
    
    def merge_chunks(
        self,
        chunks: List[Chunk],
        max_tokens: int
    ) -> List[Chunk]:
        """
        Merge small chunks into larger ones.
        
        Args:
            chunks: List of chunks to potentially merge
            max_tokens: Maximum tokens per merged chunk
        
        Returns:
            List of merged chunks
        """
        if not chunks:
            return []
        
        merged = []
        current_group = [chunks[0]]
        current_tokens = chunks[0].token_count
        
        for chunk in chunks[1:]:
            if current_tokens + chunk.token_count <= max_tokens:
                current_group.append(chunk)
                current_tokens += chunk.token_count
            else:
                # Create merged chunk
                if len(current_group) == 1:
                    merged.append(current_group[0])
                else:
                    merged_content = " ".join(c.content for c in current_group)
                    merged.append(Chunk(
                        id=f"{current_group[0].source}_merged_{len(merged)}",
                        content=merged_content,
                        source=current_group[0].source,
                        start_index=current_group[0].start_index,
                        end_index=current_group[-1].end_index,
                        token_count=current_tokens,
                        metadata={
                            "merged_from": [c.id for c in current_group],
                            "merge_count": len(current_group)
                        }
                    ))
                
                current_group = [chunk]
                current_tokens = chunk.token_count
        
        # Handle remaining group
        if current_group:
            if len(current_group) == 1:
                merged.append(current_group[0])
            else:
                merged_content = " ".join(c.content for c in current_group)
                merged.append(Chunk(
                    id=f"{current_group[0].source}_merged_{len(merged)}",
                    content=merged_content,
                    source=current_group[0].source,
                    start_index=current_group[0].start_index,
                    end_index=current_group[-1].end_index,
                    token_count=current_tokens,
                    metadata={
                        "merged_from": [c.id for c in current_group],
                        "merge_count": len(current_group)
                    }
                ))
        
        return merged


__all__ = [
    "ChunkStrategy",
    "Chunk",
    "ChunkingConfig",
    "TextChunker",
]