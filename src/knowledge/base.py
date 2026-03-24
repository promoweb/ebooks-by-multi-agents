"""
Knowledge Base Facade for BookWriterAI.

This module provides a unified interface for the knowledge management
system, combining document parsing, chunking, embeddings, and retrieval.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from src.knowledge.parsers import (
    DocumentParser,
    ParsedDocument,
    parse_file,
    parse_files,
    get_supported_extensions
)
from src.knowledge.chunker import (
    TextChunker,
    Chunk,
    ChunkingConfig,
    ChunkStrategy
)
from src.knowledge.embeddings import (
    MultiVectorStore,
    VectorStore,
    EmbeddingModel,
    MockEmbeddingModel,
    SearchResult
)
from src.knowledge.retrieval import (
    HierarchicalRetriever,
    ContextualRetriever,
    HierarchicalContext,
    RetrievalConfig
)
from src.knowledge.query_rewriter import (
    QueryRewriter,
    RewriteStrategy,
    RewrittenQuery
)
from src.knowledge.context_assembler import (
    ContextAssembler,
    ContextCompressor,
    AssembledContext
)


logger = logging.getLogger("BookWriterAI")


@dataclass
class KnowledgeBaseConfig:
    """Configuration for the Knowledge Base."""
    db_path: str = "knowledge_base.db"
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunk_strategy: ChunkStrategy = ChunkStrategy.SLIDING_WINDOW
    max_context_tokens: int = 4000
    embedding_model: Optional[EmbeddingModel] = None
    use_query_rewriting: bool = True
    use_context_compression: bool = True


class KnowledgeBase:
    """
    Facade for the Knowledge Base system.
    
    Provides a unified interface for:
    - Document ingestion and parsing
    - Text chunking
    - Embedding generation and storage
    - Semantic search and retrieval
    - Context assembly for generation
    
    Example usage:
        kb = KnowledgeBase(config)
        
        # Ingest documents
        kb.ingest_documents(["doc1.pdf", "doc2.md"])
        
        # Search
        results = kb.search("character development")
        
        # Get context for generation
        context = kb.get_context_for_chapter(chapter_info)
    """
    
    def __init__(
        self,
        config: Optional[KnowledgeBaseConfig] = None,
        llm_client=None,
        narrative_state_graph=None
    ):
        """
        Initialize the Knowledge Base.
        
        Args:
            config: Knowledge base configuration
            llm_client: LLM client for advanced features
            narrative_state_graph: Narrative state for contextual retrieval
        """
        self.config = config or KnowledgeBaseConfig()
        self.llm_client = llm_client
        self.narrative_state = narrative_state_graph
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize all knowledge base components."""
        # Embedding model
        embedding_model = self.config.embedding_model or MockEmbeddingModel()
        
        # Multi-vector store
        self.vector_store = MultiVectorStore(
            db_path=self.config.db_path,
            embedding_models={
                "semantic": embedding_model,
                "narrative": embedding_model,
                "entity": embedding_model,
                "style": embedding_model
            }
        )
        
        # Text chunker
        chunking_config = ChunkingConfig(
            strategy=self.config.chunk_strategy,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        self.chunker = TextChunker(config=chunking_config)
        
        # Hierarchical retriever
        retrieval_config = RetrievalConfig(
            max_tokens=self.config.max_context_tokens
        )
        self.retriever = HierarchicalRetriever(
            vector_store=self.vector_store,
            config=retrieval_config
        )
        
        # Contextual retriever
        self.contextual_retriever = ContextualRetriever(
            vector_store=self.vector_store,
            narrative_state_graph=self.narrative_state
        )
        
        # Query rewriter
        self.query_rewriter = QueryRewriter(llm_client=self.llm_client)
        
        # Context assembler
        self.context_assembler = ContextAssembler(
            max_tokens=self.config.max_context_tokens
        )
        
        # Context compressor
        self.context_compressor = ContextCompressor(llm_client=self.llm_client)
        
        # Document registry
        self.ingested_documents: Dict[str, Dict[str, Any]] = {}
    
    def ingest_document(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Ingest a single document into the knowledge base.
        
        Args:
            file_path: Path to the document
            metadata: Additional metadata for the document
        
        Returns:
            List of created chunks
        """
        file_path = Path(file_path)
        
        # Parse document
        parsed = parse_file(file_path)
        
        if parsed.error:
            logger.error(f"Error parsing {file_path}: {parsed.error}")
            return []
        
        # Create chunks
        chunks = self.chunker.chunk(
            text=parsed.content,
            source=str(file_path),
            metadata={
                **(metadata or {}),
                **parsed.metadata
            }
        )
        
        # Index chunks in vector store
        for chunk in chunks:
            self.vector_store.index_content(
                content=chunk.content,
                content_type="document_chunk",
                source=chunk.source,
                metadata=chunk.metadata
            )
        
        # Register document
        self.ingested_documents[str(file_path)] = {
            "chunks": len(chunks),
            "metadata": parsed.metadata
        }
        
        logger.info(f"Ingested {file_path}: {len(chunks)} chunks")
        
        return chunks
    
    def ingest_documents(
        self,
        file_paths: List[Union[str, Path]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Chunk]]:
        """
        Ingest multiple documents.
        
        Args:
            file_paths: List of document paths
            metadata: Additional metadata for all documents
        
        Returns:
            Dict mapping file paths to their chunks
        """
        results = {}
        
        for file_path in file_paths:
            chunks = self.ingest_document(file_path, metadata)
            results[str(file_path)] = chunks
        
        return results
    
    def ingest_text(
        self,
        text: str,
        source: str,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Ingest raw text into the knowledge base.
        
        Args:
            text: Text content to ingest
            source: Source identifier
            content_type: Type of content
            metadata: Additional metadata
        
        Returns:
            List of created chunks
        """
        # Create chunks
        chunks = self.chunker.chunk(
            text=text,
            source=source,
            metadata={
                **(metadata or {}),
                "content_type": content_type
            }
        )
        
        # Index chunks
        for chunk in chunks:
            self.vector_store.index_content(
                content=chunk.content,
                content_type=content_type,
                source=chunk.source,
                metadata=chunk.metadata
            )
        
        return chunks
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        stores: Optional[List[str]] = None,
        use_rewriting: bool = True
    ) -> List[SearchResult]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            top_k: Number of results to return
            stores: Vector stores to search (default: all)
            use_rewriting: Whether to use query rewriting
        
        Returns:
            List of search results
        """
        # Rewrite query if enabled
        if use_rewriting and self.config.use_query_rewriting:
            rewritten = self.query_rewriter.rewrite_for_retrieval(
                original_query=query,
                strategies=[
                    RewriteStrategy.EXPANSION,
                    RewriteStrategy.PARAPHRASE
                ]
            )
            
            # Search with original and variations
            all_results = []
            
            # Original query
            results = self.vector_store.hybrid_search(
                query=query,
                stores=stores,
                top_k=top_k
            )
            all_results.extend(results)
            
            # Variations
            for variation in rewritten.variations[:3]:
                var_results = self.vector_store.hybrid_search(
                    query=variation,
                    stores=stores,
                    top_k=top_k // 2
                )
                all_results.extend(var_results)
            
            # Deduplicate and sort
            seen = set()
            unique_results = []
            for result in all_results:
                if result.id not in seen:
                    seen.add(result.id)
                    unique_results.append(result)
            
            unique_results.sort(key=lambda x: x.score, reverse=True)
            return unique_results[:top_k]
        
        # Simple search without rewriting
        return self.vector_store.hybrid_search(
            query=query,
            stores=stores,
            top_k=top_k
        )
    
    def get_context(
        self,
        query: str,
        max_tokens: Optional[int] = None
    ) -> HierarchicalContext:
        """
        Get hierarchical context for a query.
        
        Args:
            query: Query for context retrieval
            max_tokens: Maximum tokens for context
        
        Returns:
            HierarchicalContext with multi-level content
        """
        return self.retriever.retrieve_with_context(
            query=query,
            max_tokens=max_tokens or self.config.max_context_tokens
        )
    
    def get_context_for_chapter(
        self,
        chapter_info: Dict[str, Any],
        max_tokens: Optional[int] = None
    ) -> AssembledContext:
        """
        Get assembled context for chapter generation.
        
        This is the primary method for retrieving context
        when generating a new chapter.
        
        Args:
            chapter_info: Information about the chapter
            max_tokens: Maximum tokens for context
        
        Returns:
            AssembledContext optimized for generation
        """
        # Get hierarchical context
        hierarchical = self.contextual_retriever.retrieve_for_chapter(
            chapter_info=chapter_info,
            max_tokens=max_tokens or self.config.max_context_tokens
        )
        
        # Get narrative context if available
        narrative_context = None
        if self.narrative_state:
            narrative_context = self.narrative_state.synthesize_context(
                current_chapter=chapter_info.get("chapter_number", 0),
                chapter_info=chapter_info,
                max_tokens=max_tokens or self.config.max_context_tokens
            )
        
        # Assemble final context
        assembled = self.context_assembler.assemble(
            retrieval_results=self._hierarchical_to_results(hierarchical),
            narrative_context=narrative_context,
            max_tokens=max_tokens
        )
        
        return assembled
    
    def _hierarchical_to_results(
        self,
        hierarchical: HierarchicalContext
    ) -> List[SearchResult]:
        """Convert hierarchical context to search results."""
        results = []
        
        for content in hierarchical.detailed_content:
            results.append(SearchResult(
                id="",
                content=content,
                source="hierarchical",
                score=1.0,
                embedding_type="semantic"
            ))
        
        return results
    
    def add_narrative_content(
        self,
        content: str,
        content_type: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add narrative content to the knowledge base.
        
        Used for indexing generated chapters and narrative elements.
        
        Args:
            content: Content to index
            content_type: Type (chapter, event, character, etc.)
            source: Source identifier
            metadata: Additional metadata
        """
        self.vector_store.index_content(
            content=content,
            content_type=content_type,
            source=source,
            metadata=metadata,
            stores=["semantic", "narrative"]
        )
    
    def clear(self) -> None:
        """Clear all content from the knowledge base."""
        self.vector_store.clear_all()
        self.ingested_documents.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "vector_stores": self.vector_store.stats(),
            "ingested_documents": len(self.ingested_documents),
            "total_chunks": sum(
                doc["chunks"] for doc in self.ingested_documents.values()
            )
        }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        return get_supported_extensions()


def create_knowledge_base(
    db_path: str = "knowledge_base.db",
    chunk_size: int = 500,
    max_context_tokens: int = 4000,
    embedding_model: Optional[EmbeddingModel] = None,
    llm_client=None,
    narrative_state_graph=None
) -> KnowledgeBase:
    """
    Factory function to create a KnowledgeBase instance.
    
    Args:
        db_path: Path to SQLite database
        chunk_size: Target chunk size in tokens
        max_context_tokens: Maximum tokens for context
        embedding_model: Embedding model to use
        llm_client: LLM client for advanced features
        narrative_state_graph: Narrative state for contextual retrieval
    
    Returns:
        Configured KnowledgeBase instance
    """
    config = KnowledgeBaseConfig(
        db_path=db_path,
        chunk_size=chunk_size,
        max_context_tokens=max_context_tokens,
        embedding_model=embedding_model
    )
    
    return KnowledgeBase(
        config=config,
        llm_client=llm_client,
        narrative_state_graph=narrative_state_graph
    )


__all__ = [
    "KnowledgeBaseConfig",
    "KnowledgeBase",
    "create_knowledge_base",
]