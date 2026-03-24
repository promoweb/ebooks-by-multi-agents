"""
Embeddings and Multi-Vector Store for Knowledge Base System.

This module provides embedding generation and multi-vector storage
for semantic search capabilities.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import math


logger = logging.getLogger("BookWriterAI")


@dataclass
class EmbeddingVector:
    """Represents an embedding vector with metadata."""
    id: str
    vector: List[float]
    content: str
    source: str
    embedding_type: str  # semantic, narrative, entity, style
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "vector": self.vector,
            "content": self.content,
            "source": self.source,
            "embedding_type": self.embedding_type,
            "metadata": self.metadata
        }


@dataclass
class SearchResult:
    """Represents a search result with relevance score."""
    id: str
    content: str
    source: str
    score: float
    embedding_type: str
    metadata: dict = field(default_factory=dict)


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return model name."""
        pass


class MockEmbeddingModel(EmbeddingModel):
    """
    Mock embedding model for testing.
    
    Generates deterministic embeddings based on text hash.
    Not suitable for production use.
    """
    
    def __init__(self, dimension: int = 384):
        self._dimension = dimension
    
    def embed(self, text: str) -> List[float]:
        """Generate mock embedding from text hash."""
        # Create deterministic embedding from hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Use hash to generate pseudo-random but deterministic values
        vector = []
        for i in range(self._dimension):
            # Get 8 hex characters at a time
            start = (i * 8) % len(text_hash)
            hex_val = text_hash[start:start+8]
            # Convert to float between -1 and 1
            val = int(hex_val, 16) / (16**8) * 2 - 1
            vector.append(val)
        
        # Normalize
        magnitude = math.sqrt(sum(v**2 for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return "mock-embedding-model"


class OpenAIEmbeddingModel(EmbeddingModel):
    """OpenAI embedding model wrapper."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-ada-002",
        dimension: int = 1536
    ):
        self.api_key = api_key
        self._model = model
        self._dimension = dimension
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package required for OpenAI embeddings. "
                    "Install with: pip install openai"
                )
        return self._client
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        client = self._get_client()
        response = client.embeddings.create(
            model=self._model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        client = self._get_client()
        response = client.embeddings.create(
            model=self._model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return self._model


class VectorStore:
    """
    Vector store for a single embedding type.
    
    Uses SQLite for persistence with vector similarity search.
    """
    
    def __init__(
        self,
        db_path: str,
        embedding_model: EmbeddingModel,
        store_type: str = "semantic"
    ):
        """
        Initialize vector store.
        
        Args:
            db_path: Path to SQLite database
            embedding_model: Model for generating embeddings
            store_type: Type of embeddings (semantic, narrative, entity, style)
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.store_type = store_type
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create embeddings table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.store_type}_embeddings (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT,
                vector BLOB NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on source
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.store_type}_source
            ON {self.store_type}_embeddings(source)
        """)
        
        conn.commit()
        conn.close()
    
    def add(
        self,
        id: str,
        content: str,
        source: str = "",
        metadata: Optional[dict] = None
    ) -> None:
        """Add a document to the store."""
        vector = self.embedding_model.embed(content)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            INSERT OR REPLACE INTO {self.store_type}_embeddings
            (id, content, source, vector, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            id,
            content,
            source,
            json.dumps(vector),
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
    
    def add_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> None:
        """Add multiple documents to the store."""
        if not items:
            return
        
        # Generate embeddings in batch
        contents = [item["content"] for item in items]
        vectors = self.embedding_model.embed_batch(contents)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item, vector in zip(items, vectors):
            cursor.execute(f"""
                INSERT OR REPLACE INTO {self.store_type}_embeddings
                (id, content, source, vector, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item["id"],
                item["content"],
                item.get("source", ""),
                json.dumps(vector),
                json.dumps(item.get("metadata", {}))
            ))
        
        conn.commit()
        conn.close()
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """Search for similar documents."""
        query_vector = self.embedding_model.embed(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, content, source, vector, metadata
            FROM {self.store_type}_embeddings
        """)
        
        results = []
        for row in cursor.fetchall():
            id, content, source, vector_blob, metadata_blob = row
            stored_vector = json.loads(vector_blob)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, stored_vector)
            
            results.append(SearchResult(
                id=id,
                content=content,
                source=source,
                score=similarity,
                embedding_type=self.store_type,
                metadata=json.loads(metadata_blob)
            ))
        
        conn.close()
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def get(self, id: str) -> Optional[EmbeddingVector]:
        """Get a specific embedding by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, content, source, vector, metadata
            FROM {self.store_type}_embeddings
            WHERE id = ?
        """, (id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return EmbeddingVector(
                id=row[0],
                vector=json.loads(row[3]),
                content=row[1],
                source=row[2],
                embedding_type=self.store_type,
                metadata=json.loads(row[4])
            )
        
        return None
    
    def delete(self, id: str) -> bool:
        """Delete an embedding by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            DELETE FROM {self.store_type}_embeddings
            WHERE id = ?
        """, (id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def delete_by_source(self, source: str) -> int:
        """Delete all embeddings from a source."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            DELETE FROM {self.store_type}_embeddings
            WHERE source = ?
        """, (source,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def count(self) -> int:
        """Count total embeddings in store."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM {self.store_type}_embeddings
        """)
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a**2 for a in vec1))
        magnitude2 = math.sqrt(sum(b**2 for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class MultiVectorStore:
    """
    Manages multiple embedding types for different content aspects.
    
    Supports both external documents and generated content with
    separate stores for semantic, narrative, entity, and style embeddings.
    """
    
    def __init__(
        self,
        db_path: str,
        embedding_models: Optional[Dict[str, EmbeddingModel]] = None
    ):
        """
        Initialize multi-vector store.
        
        Args:
            db_path: Path to SQLite database
            embedding_models: Dict of embedding models by type
        """
        self.db_path = db_path
        
        # Default to mock model if none provided
        default_model = MockEmbeddingModel()
        
        self.embedding_models = embedding_models or {
            "semantic": default_model,
            "narrative": default_model,
            "entity": default_model,
            "style": default_model
        }
        
        # Initialize stores
        self.stores: Dict[str, VectorStore] = {}
        for store_type, model in self.embedding_models.items():
            self.stores[store_type] = VectorStore(
                db_path=db_path,
                embedding_model=model,
                store_type=store_type
            )
    
    def index_content(
        self,
        content: str,
        content_type: str,
        source: str,
        metadata: Optional[dict] = None,
        stores: Optional[List[str]] = None
    ) -> None:
        """
        Index content across specified stores.
        
        Args:
            content: Text content to index
            content_type: Type of content (document, chapter, character, event)
            source: Source identifier
            metadata: Additional metadata
            stores: List of stores to index in (default: all)
        """
        stores = stores or list(self.stores.keys())
        metadata = metadata or {}
        metadata["content_type"] = content_type
        
        # Generate unique ID
        content_id = self._generate_id(content, source)
        
        for store_type in stores:
            if store_type in self.stores:
                self.stores[store_type].add(
                    id=f"{content_id}_{store_type}",
                    content=content,
                    source=source,
                    metadata=metadata
                )
    
    def hybrid_search(
        self,
        query: str,
        stores: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Perform weighted hybrid search across multiple stores.
        
        Args:
            query: Search query
            stores: List of stores to search (default: all)
            weights: Weight for each store (default: equal weights)
            top_k: Number of results to return
        
        Returns:
            List of SearchResult objects sorted by combined score
        """
        stores = stores or list(self.stores.keys())
        
        # Default to equal weights
        if not weights:
            weight = 1.0 / len(stores)
            weights = {s: weight for s in stores}
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Search each store
        all_results: Dict[str, SearchResult] = {}
        
        for store_type in stores:
            if store_type not in self.stores:
                continue
            
            store_results = self.stores[store_type].search(
                query=query,
                top_k=top_k * 2  # Get more for merging
            )
            
            for result in store_results:
                # Weight the score
                weighted_score = result.score * weights.get(store_type, 1.0)
                
                if result.id in all_results:
                    # Combine scores for same result
                    all_results[result.id].score += weighted_score
                else:
                    result.score = weighted_score
                    all_results[result.id] = result
        
        # Sort by combined score
        results = sorted(
            all_results.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return results[:top_k]
    
    def get_store(self, store_type: str) -> Optional[VectorStore]:
        """Get a specific vector store."""
        return self.stores.get(store_type)
    
    def clear_store(self, store_type: str) -> None:
        """Clear all embeddings from a store."""
        if store_type in self.stores:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {store_type}_embeddings")
            conn.commit()
            conn.close()
    
    def clear_all(self) -> None:
        """Clear all embeddings from all stores."""
        for store_type in self.stores:
            self.clear_store(store_type)
    
    def stats(self) -> Dict[str, int]:
        """Get statistics for all stores."""
        return {
            store_type: store.count()
            for store_type, store in self.stores.items()
        }
    
    def _generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for content."""
        hash_input = f"{source}:{content[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


__all__ = [
    "EmbeddingVector",
    "SearchResult",
    "EmbeddingModel",
    "MockEmbeddingModel",
    "OpenAIEmbeddingModel",
    "VectorStore",
    "MultiVectorStore",
]