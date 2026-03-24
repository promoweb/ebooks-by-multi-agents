"""
Hierarchical Retrieval System for Knowledge Base.

This module provides hierarchical retrieval for long-form content,
supporting Book → Chapter → Section → Paragraph navigation.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class ContentType(Enum):
    """Type of content in hierarchy."""
    BOOK = "book"
    CHAPTER = "chapter"
    SECTION = "section"
    PARAGRAPH = "paragraph"


@dataclass
class HierarchicalContent:
    """Content at a specific level in the hierarchy."""
    content_type: ContentType
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    children: List['HierarchicalContent'] = field(default_factory=list)
    parent_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "content_type": self.content_type.value,
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "children": [c.to_dict() for c in self.children],
            "parent_id": self.parent_id,
            "metadata": self.metadata
        }


@dataclass
class HierarchicalContext:
    """
    Retrieved context with hierarchical structure.
    
    Provides context at multiple levels:
    - book_context: High-level book summary
    - chapter_contexts: Relevant chapter summaries
    - section_contexts: Relevant section summaries
    - detailed_content: Specific paragraphs/passages
    """
    book_context: Optional[str] = None
    chapter_contexts: List[str] = field(default_factory=list)
    section_contexts: List[str] = field(default_factory=list)
    detailed_content: List[str] = field(default_factory=list)
    total_tokens: int = 0
    sources: List[str] = field(default_factory=list)
    
    def to_prompt_context(self) -> str:
        """Format as context string for prompts."""
        parts = []
        
        if self.book_context:
            parts.append(f"=== Book Overview ===\n{self.book_context}\n")
        
        if self.chapter_contexts:
            parts.append("=== Chapter Context ===")
            for ctx in self.chapter_contexts:
                parts.append(ctx)
            parts.append("")
        
        if self.section_contexts:
            parts.append("=== Section Context ===")
            for ctx in self.section_contexts:
                parts.append(ctx)
            parts.append("")
        
        if self.detailed_content:
            parts.append("=== Relevant Content ===")
            for content in self.detailed_content:
                parts.append(content)
            parts.append("")
        
        return "\n".join(parts)


@dataclass
class RetrievalConfig:
    """Configuration for hierarchical retrieval."""
    max_tokens: int = 4000
    book_summary_tokens: int = 200
    chapter_summary_tokens: int = 300
    section_summary_tokens: int = 200
    detailed_content_tokens: int = 500
    max_chapters: int = 3
    max_sections: int = 5
    max_detailed_items: int = 10
    relevance_threshold: float = 0.5


class HierarchicalRetriever:
    """
    Implements hierarchical retrieval for long-form content.
    
    Retrieves content at multiple levels:
    Book → Chapter → Section → Paragraph
    
    This provides both broad context and specific details.
    """
    
    def __init__(
        self,
        vector_store,
        config: Optional[RetrievalConfig] = None
    ):
        """
        Initialize hierarchical retriever.
        
        Args:
            vector_store: MultiVectorStore for semantic search
            config: Retrieval configuration
        """
        self.vector_store = vector_store
        self.config = config or RetrievalConfig()
        
        # Content hierarchy storage
        self.hierarchy: Dict[str, HierarchicalContent] = {}
        self.book_summaries: Dict[str, str] = {}
        self.chapter_summaries: Dict[str, str] = {}
        self.section_summaries: Dict[str, str] = {}
    
    def index_hierarchy(
        self,
        book: HierarchicalContent
    ) -> None:
        """
        Index a book with its hierarchical structure.
        
        Args:
            book: HierarchicalContent representing the book
        """
        self.hierarchy[book.id] = book
        
        # Index each level
        self._index_content(book, ContentType.BOOK)
        
        for chapter in book.children:
            self._index_content(chapter, ContentType.CHAPTER)
            
            for section in chapter.children:
                self._index_content(section, ContentType.SECTION)
                
                for paragraph in section.children:
                    self._index_content(paragraph, ContentType.PARAGRAPH)
    
    def _index_content(
        self,
        content: HierarchicalContent,
        content_type: ContentType
    ) -> None:
        """Index content at a specific level."""
        # Store summary if available
        if content.summary:
            if content_type == ContentType.BOOK:
                self.book_summaries[content.id] = content.summary
            elif content_type == ContentType.CHAPTER:
                self.chapter_summaries[content.id] = content.summary
            elif content_type == ContentType.SECTION:
                self.section_summaries[content.id] = content.summary
        
        # Index in vector store
        text_to_index = content.summary or content.content
        self.vector_store.index_content(
            content=text_to_index,
            content_type=content_type.value,
            source=content.id,
            metadata={
                "title": content.title,
                "parent_id": content.parent_id,
                "level": content_type.value
            },
            stores=["semantic", "narrative"]
        )
    
    def retrieve_with_context(
        self,
        query: str,
        max_tokens: Optional[int] = None
    ) -> HierarchicalContext:
        """
        Retrieve relevant content with hierarchical context.
        
        Args:
            query: Search query
            max_tokens: Maximum tokens to retrieve (uses config if not provided)
        
        Returns:
            HierarchicalContext with content at multiple levels
        """
        max_tokens = max_tokens or self.config.max_tokens
        
        context = HierarchicalContext()
        remaining_tokens = max_tokens
        
        # Step 1: Get book-level context
        book_tokens = min(remaining_tokens, self.config.book_summary_tokens)
        book_context = self._retrieve_book_context(query, book_tokens)
        if book_context:
            context.book_context = book_context
            context.total_tokens += book_tokens
            remaining_tokens -= book_tokens
        
        # Step 2: Get chapter-level context
        if remaining_tokens > 0:
            chapter_tokens = min(
                remaining_tokens,
                self.config.chapter_summary_tokens * self.config.max_chapters
            )
            chapter_contexts = self._retrieve_chapter_contexts(
                query,
                chapter_tokens
            )
            context.chapter_contexts = chapter_contexts
            context.total_tokens += len(chapter_contexts) * self.config.chapter_summary_tokens
            remaining_tokens -= len(chapter_contexts) * self.config.chapter_summary_tokens
        
        # Step 3: Get section-level context
        if remaining_tokens > 0:
            section_tokens = min(
                remaining_tokens,
                self.config.section_summary_tokens * self.config.max_sections
            )
            section_contexts = self._retrieve_section_contexts(
                query,
                section_tokens
            )
            context.section_contexts = section_contexts
            context.total_tokens += len(section_contexts) * self.config.section_summary_tokens
            remaining_tokens -= len(section_contexts) * self.config.section_summary_tokens
        
        # Step 4: Get detailed content
        if remaining_tokens > 0:
            detailed_tokens = min(
                remaining_tokens,
                self.config.detailed_content_tokens * self.config.max_detailed_items
            )
            detailed_content = self._retrieve_detailed_content(
                query,
                detailed_tokens
            )
            context.detailed_content = detailed_content
            context.total_tokens += len(detailed_content) * self.config.detailed_content_tokens
        
        return context
    
    def _retrieve_book_context(
        self,
        query: str,
        max_tokens: int
    ) -> Optional[str]:
        """Retrieve book-level context."""
        results = self.vector_store.hybrid_search(
            query=query,
            stores=["semantic"],
            top_k=1
        )
        
        for result in results:
            if result.metadata.get("level") == "book":
                return result.content
        
        # Fallback to any high-level summary
        if self.book_summaries:
            return list(self.book_summaries.values())[0]
        
        return None
    
    def _retrieve_chapter_contexts(
        self,
        query: str,
        max_tokens: int
    ) -> List[str]:
        """Retrieve chapter-level contexts."""
        results = self.vector_store.hybrid_search(
            query=query,
            stores=["semantic", "narrative"],
            weights={"semantic": 0.6, "narrative": 0.4},
            top_k=self.config.max_chapters
        )
        
        contexts = []
        for result in results:
            if result.metadata.get("level") == "chapter":
                contexts.append(result.content)
                if len(contexts) >= self.config.max_chapters:
                    break
        
        return contexts
    
    def _retrieve_section_contexts(
        self,
        query: str,
        max_tokens: int
    ) -> List[str]:
        """Retrieve section-level contexts."""
        results = self.vector_store.hybrid_search(
            query=query,
            stores=["semantic", "narrative"],
            weights={"semantic": 0.5, "narrative": 0.5},
            top_k=self.config.max_sections
        )
        
        contexts = []
        for result in results:
            if result.metadata.get("level") == "section":
                contexts.append(result.content)
                if len(contexts) >= self.config.max_sections:
                    break
        
        return contexts
    
    def _retrieve_detailed_content(
        self,
        query: str,
        max_tokens: int
    ) -> List[str]:
        """Retrieve detailed paragraph-level content."""
        results = self.vector_store.hybrid_search(
            query=query,
            stores=["semantic", "narrative"],
            weights={"semantic": 0.7, "narrative": 0.3},
            top_k=self.config.max_detailed_items
        )
        
        contents = []
        for result in results:
            if result.metadata.get("level") == "paragraph":
                contents.append(result.content)
                if len(contents) >= self.config.max_detailed_items:
                    break
        
        return contents
    
    def get_children(
        self,
        parent_id: str
    ) -> List[HierarchicalContent]:
        """Get children of a content item."""
        if parent_id in self.hierarchy:
            return self.hierarchy[parent_id].children
        
        # Search in all items
        children = []
        for content in self.hierarchy.values():
            if content.parent_id == parent_id:
                children.append(content)
        
        return children
    
    def get_ancestors(
        self,
        content_id: str
    ) -> List[HierarchicalContent]:
        """Get ancestor chain of a content item."""
        ancestors = []
        current = self.hierarchy.get(content_id)
        
        while current and current.parent_id:
            parent = self.hierarchy.get(current.parent_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_siblings(
        self,
        content_id: str
    ) -> List[HierarchicalContent]:
        """Get siblings of a content item."""
        content = self.hierarchy.get(content_id)
        if not content or not content.parent_id:
            return []
        
        return self.get_children(content.parent_id)


class ContextualRetriever:
    """
    Retrieves content considering narrative context.
    
    Used for chapter generation to provide relevant context
    from previous chapters, active plot threads, and character states.
    """
    
    def __init__(
        self,
        vector_store,
        narrative_state_graph=None
    ):
        """
        Initialize contextual retriever.
        
        Args:
            vector_store: MultiVectorStore for semantic search
            narrative_state_graph: NarrativeStateGraph for context
        """
        self.vector_store = vector_store
        self.narrative_state = narrative_state_graph
    
    def retrieve_for_chapter(
        self,
        chapter_info: Dict[str, Any],
        max_tokens: int = 4000
    ) -> HierarchicalContext:
        """
        Retrieve context specifically for chapter generation.
        
        Considers:
        - Previous chapter events
        - Active plot threads
        - Character states
        - Unresolved conflicts
        - Relevant external documents
        
        Args:
            chapter_info: Information about the chapter to generate
            max_tokens: Maximum tokens for context
        
        Returns:
            HierarchicalContext with relevant information
        """
        context = HierarchicalContext()
        
        # Build query from chapter info
        query_parts = []
        
        if "title" in chapter_info:
            query_parts.append(chapter_info["title"])
        
        if "summary" in chapter_info:
            query_parts.append(chapter_info["summary"])
        
        if "characters" in chapter_info:
            query_parts.extend(chapter_info["characters"])
        
        query = " ".join(query_parts)
        
        # Get narrative context if available
        if self.narrative_state:
            narrative_context = self._get_narrative_context(
                chapter_info.get("chapter_number", 0),
                max_tokens // 2
            )
            if narrative_context:
                context.chapter_contexts.append(narrative_context)
        
        # Get relevant content from vector store
        if query:
            results = self.vector_store.hybrid_search(
                query=query,
                stores=["semantic", "narrative", "entity"],
                weights={
                    "semantic": 0.4,
                    "narrative": 0.4,
                    "entity": 0.2
                },
                top_k=10
            )
            
            for result in results:
                if result.score >= 0.5:
                    context.detailed_content.append(result.content)
                    context.sources.append(result.source)
        
        return context
    
    def _get_narrative_context(
        self,
        chapter_number: int,
        max_tokens: int
    ) -> Optional[str]:
        """Get narrative context from state graph."""
        if not self.narrative_state:
            return None
        
        # Get unresolved events
        unresolved = self.narrative_state.get_unresolved_events()
        
        # Get recent events
        recent = self.narrative_state.events_store.get_events_by_chapter(
            max(0, chapter_number - 1)
        )
        
        # Build context string
        parts = []
        
        if unresolved:
            parts.append("Unresolved plot threads:")
            for event in unresolved[:5]:
                parts.append(f"- {event.description}")
        
        if recent:
            parts.append("\nRecent events:")
            for event in recent[:5]:
                parts.append(f"- {event.description}")
        
        return "\n".join(parts) if parts else None


__all__ = [
    "ContentType",
    "HierarchicalContent",
    "HierarchicalContext",
    "RetrievalConfig",
    "HierarchicalRetriever",
    "ContextualRetriever",
]