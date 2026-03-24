"""
Knowledge Base System for BookWriterAI.

This module provides comprehensive knowledge management capabilities
including document parsing, chunking, embeddings, and retrieval.

Components:
- Document Parsers: Parse various document formats (PDF, TXT, Markdown)
- Text Chunker: Break documents into manageable chunks
- Embeddings: Multi-vector storage for semantic search
- Retrieval: Hierarchical and contextual retrieval
- Query Rewriter: Improve search effectiveness
- Context Assembler: Optimize context for generation
- Knowledge Base: Unified facade for all operations

Example usage:
    from src.knowledge import KnowledgeBase, create_knowledge_base
    
    # Create knowledge base
    kb = create_knowledge_base(db_path="knowledge.db")
    
    # Ingest documents
    kb.ingest_documents(["book.pdf", "notes.md"])
    
    # Search
    results = kb.search("character development")
    
    # Get context for generation
    context = kb.get_context_for_chapter(chapter_info)
"""

# Parsers
from src.knowledge.parsers import (
    DocumentParser,
    ParsedDocument,
    PDFParser,
    TXTParser,
    MarkdownParser,
    parse_file,
    parse_files,
    get_parser,
    get_parser_for_file,
    get_supported_extensions,
)

# Chunker
from src.knowledge.chunker import (
    Chunk,
    ChunkStrategy,
    ChunkingConfig,
    TextChunker,
)

# Embeddings
from src.knowledge.embeddings import (
    EmbeddingVector,
    SearchResult,
    EmbeddingModel,
    MockEmbeddingModel,
    OpenAIEmbeddingModel,
    VectorStore,
    MultiVectorStore,
)

# Retrieval
from src.knowledge.retrieval import (
    ContentType,
    HierarchicalContent,
    HierarchicalContext,
    RetrievalConfig,
    HierarchicalRetriever,
    ContextualRetriever,
)

# Query Rewriter
from src.knowledge.query_rewriter import (
    RewriteStrategy,
    RewrittenQuery,
    QueryRewriter,
)

# Context Assembler
from src.knowledge.context_assembler import (
    Priority,
    ContextItem,
    PriorityRule,
    AssembledContext,
    ContextAssembler,
    ContextCompressor,
)

# Knowledge Base Facade
from src.knowledge.base import (
    KnowledgeBaseConfig,
    KnowledgeBase,
    create_knowledge_base,
)


__all__ = [
    # Parsers
    "DocumentParser",
    "ParsedDocument",
    "PDFParser",
    "TXTParser",
    "MarkdownParser",
    "parse_file",
    "parse_files",
    "get_parser",
    "get_parser_for_file",
    "get_supported_extensions",
    
    # Chunker
    "Chunk",
    "ChunkStrategy",
    "ChunkingConfig",
    "TextChunker",
    
    # Embeddings
    "EmbeddingVector",
    "SearchResult",
    "EmbeddingModel",
    "MockEmbeddingModel",
    "OpenAIEmbeddingModel",
    "VectorStore",
    "MultiVectorStore",
    
    # Retrieval
    "ContentType",
    "HierarchicalContent",
    "HierarchicalContext",
    "RetrievalConfig",
    "HierarchicalRetriever",
    "ContextualRetriever",
    
    # Query Rewriter
    "RewriteStrategy",
    "RewrittenQuery",
    "QueryRewriter",
    
    # Context Assembler
    "Priority",
    "ContextItem",
    "PriorityRule",
    "AssembledContext",
    "ContextAssembler",
    "ContextCompressor",
    
    # Knowledge Base
    "KnowledgeBaseConfig",
    "KnowledgeBase",
    "create_knowledge_base",
]