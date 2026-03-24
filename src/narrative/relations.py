"""
Relations Graph for Long-Term Narrative Memory System.

This module provides the RelationsGraph for tracking relationships between
entities (characters, locations, organizations) and how they evolve.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

from src.core.exceptions import EntityNotFoundError


logger = logging.getLogger("BookWriterAI")


class RelationType(Enum):
    """Types of relationships between entities."""
    # Character-Character
    FAMILY = "family"
    FRIEND = "friend"
    ENEMY = "enemy"
    ROMANTIC = "romantic"
    COLLEAGUE = "colleague"
    ACQUAINTANCE = "acquaintance"
    RIVAL = "rival"
    MENTOR = "mentor"
    STUDENT = "student"
    
    # Character-Location
    LIVES_AT = "lives_at"
    WORKS_AT = "works_at"
    VISITS = "visits"
    OWNS = "owns"
    
    # Character-Organization
    MEMBER_OF = "member_of"
    LEADER_OF = "leader_of"
    EMPLOYEE_OF = "employee_of"
    
    # Location-Location
    LOCATED_IN = "located_in"
    NEAR = "near"
    CONNECTED_TO = "connected_to"
    
    # Generic
    KNOWS = "knows"
    ASSOCIATED_WITH = "associated_with"


@dataclass
class RelationState:
    """
    Snapshot of relation state at a point in narrative time.
    
    Tracks how a relationship changes throughout the narrative.
    """
    chapter_id: int
    strength: float  # 0.0 to 1.0
    sentiment: float  # -1.0 (hostile) to 1.0 (friendly)
    status: str = "active"  # active, ended, transformed
    notes: str = ""
    changed_by_event: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationState":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Relation:
    """
    Represents a relationship between two entities.
    
    Relations are directed (source -> target) and track
    the evolution of the relationship over time.
    """
    relation_id: str
    source_entity: str  # Entity ID
    target_entity: str  # Entity ID
    relation_type: str  # RelationType value
    strength: float = 0.5  # 0.0 to 1.0
    sentiment: float = 0.0  # -1.0 to 1.0
    established_chapter: Optional[int] = None
    last_updated_chapter: Optional[int] = None
    history: List[RelationState] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data.pop('history', None)  # Stored separately
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relation":
        """Create from dictionary."""
        data.pop('history', None)
        return cls(**data)
    
    def get_current_state(self) -> Optional[RelationState]:
        """Get the most recent state."""
        if self.history:
            return self.history[-1]
        return None
    
    def is_active(self) -> bool:
        """Check if the relation is currently active."""
        state = self.get_current_state()
        return state is None or state.status == "active"


class RelationsGraph:
    """
    Graph-based relationship management.
    
    Provides:
    - Relation registration and retrieval
    - Relationship evolution tracking
    - Social network analysis
    - SQLite persistence
    """
    
    def __init__(self, db_path: str = "checkpoints/narrative_memory.db"):
        """
        Initialize the relations graph.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Relation] = {}
        self._initialize_db()
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _initialize_db(self):
        """Initialize database schema."""
        conn = self.conn
        
        # Relations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                relation_id TEXT PRIMARY KEY,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                strength REAL,
                sentiment REAL,
                established_chapter INTEGER,
                last_updated_chapter INTEGER,
                metadata TEXT,
                created_at TEXT
            )
        """)
        
        # Relation states table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relation_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relation_id TEXT NOT NULL,
                chapter_id INTEGER,
                strength REAL,
                sentiment REAL,
                status TEXT,
                notes TEXT,
                changed_by_event TEXT,
                created_at TEXT,
                FOREIGN KEY (relation_id) REFERENCES relations(relation_id)
            )
        """)
        
        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_relations_source 
            ON relations(source_entity)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_relations_target 
            ON relations(target_entity)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_relations_type 
            ON relations(relation_type)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_relation_states_relation 
            ON relation_states(relation_id, chapter_id)
        """)
        
        conn.commit()
    
    def add_relation(self, relation: Relation) -> str:
        """
        Add a relation to the graph.
        
        Args:
            relation: The relation to add
            
        Returns:
            The relation ID
        """
        conn = self.conn
        
        conn.execute("""
            INSERT OR REPLACE INTO relations (
                relation_id, source_entity, target_entity, relation_type,
                strength, sentiment, established_chapter, last_updated_chapter,
                metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            relation.relation_id,
            relation.source_entity,
            relation.target_entity,
            relation.relation_type,
            relation.strength,
            relation.sentiment,
            relation.established_chapter,
            relation.last_updated_chapter,
            json.dumps(relation.metadata),
            relation.created_at
        ))
        
        conn.commit()
        
        # Update cache
        self._cache[relation.relation_id] = relation
        
        logger.debug(f"Added relation: {relation.relation_id} "
                    f"({relation.source_entity} -> {relation.target_entity})")
        
        return relation.relation_id
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """Get a relation by ID."""
        if relation_id in self._cache:
            return self._cache[relation_id]
        
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM relations WHERE relation_id = ?",
            (relation_id,)
        )
        row = cursor.fetchone()
        
        if row:
            relation = self._row_to_relation(row)
            relation.history = self._load_relation_history(relation_id)
            self._cache[relation_id] = relation
            return relation
        
        return None
    
    def get_relation_between(
        self, 
        entity_a: str, 
        entity_b: str,
        relation_type: Optional[str] = None
    ) -> Optional[Relation]:
        """
        Get the relation between two entities.
        
        Args:
            entity_a: First entity ID
            entity_b: Second entity ID
            relation_type: Optional specific relation type
            
        Returns:
            The relation if found, None otherwise
        """
        conn = self.conn
        
        if relation_type:
            cursor = conn.execute("""
                SELECT * FROM relations 
                WHERE source_entity = ? AND target_entity = ? AND relation_type = ?
                UNION
                SELECT * FROM relations 
                WHERE source_entity = ? AND target_entity = ? AND relation_type = ?
            """, (entity_a, entity_b, relation_type, entity_b, entity_a, relation_type))
        else:
            cursor = conn.execute("""
                SELECT * FROM relations 
                WHERE source_entity = ? AND target_entity = ?
                UNION
                SELECT * FROM relations 
                WHERE source_entity = ? AND target_entity = ?
            """, (entity_a, entity_b, entity_b, entity_a))
        
        row = cursor.fetchone()
        
        if row:
            return self.get_relation(row["relation_id"])
        
        return None
    
    def get_relations(
        self, 
        entity_id: str, 
        relation_type: Optional[str] = None,
        direction: str = "both"
    ) -> List[Relation]:
        """
        Get all relations involving an entity.
        
        Args:
            entity_id: The entity ID
            relation_type: Optional filter by type
            direction: 'outgoing', 'incoming', or 'both'
            
        Returns:
            List of relations
        """
        conn = self.conn
        relations = []
        
        if direction in ["outgoing", "both"]:
            if relation_type:
                cursor = conn.execute(
                    "SELECT * FROM relations WHERE source_entity = ? AND relation_type = ?",
                    (entity_id, relation_type)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM relations WHERE source_entity = ?",
                    (entity_id,)
                )
            
            for row in cursor.fetchall():
                relation = self.get_relation(row["relation_id"])
                if relation:
                    relations.append(relation)
        
        if direction in ["incoming", "both"]:
            if relation_type:
                cursor = conn.execute(
                    "SELECT * FROM relations WHERE target_entity = ? AND relation_type = ?",
                    (entity_id, relation_type)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM relations WHERE target_entity = ?",
                    (entity_id,)
                )
            
            for row in cursor.fetchall():
                relation = self.get_relation(row["relation_id"])
                if relation and relation not in relations:
                    relations.append(relation)
        
        return relations
    
    def update_relation(
        self, 
        relation_id: str, 
        new_state: RelationState
    ) -> None:
        """
        Update a relation with a new state.
        
        Args:
            relation_id: The relation ID
            new_state: The new state
        """
        relation = self.get_relation(relation_id)
        if not relation:
            raise ValueError(f"Relation not found: {relation_id}")
        
        conn = self.conn
        
        # Add state to history
        conn.execute("""
            INSERT INTO relation_states (
                relation_id, chapter_id, strength, sentiment,
                status, notes, changed_by_event, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            relation_id,
            new_state.chapter_id,
            new_state.strength,
            new_state.sentiment,
            new_state.status,
            new_state.notes,
            new_state.changed_by_event,
            new_state.created_at
        ))
        
        # Update relation's current values
        conn.execute("""
            UPDATE relations SET 
                strength = ?,
                sentiment = ?,
                last_updated_chapter = ?
            WHERE relation_id = ?
        """, (new_state.strength, new_state.sentiment, new_state.chapter_id, relation_id))
        
        conn.commit()
        
        # Update cache
        relation.history.append(new_state)
        relation.strength = new_state.strength
        relation.sentiment = new_state.sentiment
        relation.last_updated_chapter = new_state.chapter_id
        
        logger.debug(f"Updated relation {relation_id} at chapter {new_state.chapter_id}")
    
    def get_social_network(
        self, 
        entity_id: str, 
        depth: int = 2
    ) -> Dict[str, List[Relation]]:
        """
        Get the social network around an entity.
        
        Args:
            entity_id: Starting entity
            depth: How many degrees of separation to include
            
        Returns:
            Dictionary mapping entity IDs to their relations
        """
        network: Dict[str, List[Relation]] = {}
        visited: Set[str] = set()
        
        def traverse(eid: str, current_depth: int):
            if current_depth > depth or eid in visited:
                return
            visited.add(eid)
            
            relations = self.get_relations(eid)
            network[eid] = relations
            
            for rel in relations:
                other = (rel.target_entity if rel.source_entity == eid 
                        else rel.source_entity)
                traverse(other, current_depth + 1)
        
        traverse(entity_id, 0)
        return network
    
    def get_relation_path(
        self, 
        entity_a: str, 
        entity_b: str,
        max_depth: int = 4
    ) -> List[Tuple[Relation, str]]:
        """
        Find a path of relations between two entities.
        
        Uses BFS to find the shortest path.
        
        Args:
            entity_a: Starting entity
            entity_b: Target entity
            max_depth: Maximum search depth
            
        Returns:
            List of (relation, direction) tuples forming the path
        """
        if entity_a == entity_b:
            return []
        
        visited: Set[str] = {entity_a}
        queue: List[Tuple[str, List[Tuple[Relation, str]]]] = [(entity_a, [])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            for rel in self.get_relations(current):
                other = (rel.target_entity if rel.source_entity == current 
                        else rel.source_entity)
                direction = "outgoing" if rel.source_entity == current else "incoming"
                
                new_path = path + [(rel, direction)]
                
                if other == entity_b:
                    return new_path
                
                if other not in visited:
                    visited.add(other)
                    queue.append((other, new_path))
        
        return []  # No path found
    
    def get_relations_by_chapter(self, chapter_id: int) -> List[Relation]:
        """Get all relations established or updated in a chapter."""
        conn = self.conn
        cursor = conn.execute("""
            SELECT * FROM relations 
            WHERE established_chapter = ? OR last_updated_chapter = ?
        """, (chapter_id, chapter_id))
        
        relations = []
        for row in cursor.fetchall():
            relation = self.get_relation(row["relation_id"])
            if relation:
                relations.append(relation)
        
        return relations
    
    def get_strong_relations(
        self, 
        entity_id: str, 
        min_strength: float = 0.7
    ) -> List[Relation]:
        """Get relations with strength above threshold."""
        relations = self.get_relations(entity_id)
        return [r for r in relations if r.strength >= min_strength]
    
    def get_positive_relations(
        self, 
        entity_id: str, 
        min_sentiment: float = 0.3
    ) -> List[Relation]:
        """Get relations with positive sentiment."""
        relations = self.get_relations(entity_id)
        return [r for r in relations if r.sentiment >= min_sentiment]
    
    def get_negative_relations(
        self, 
        entity_id: str, 
        max_sentiment: float = -0.3
    ) -> List[Relation]:
        """Get relations with negative sentiment."""
        relations = self.get_relations(entity_id)
        return [r for r in relations if r.sentiment <= max_sentiment]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored relations."""
        conn = self.conn
        
        total = conn.execute(
            "SELECT COUNT(*) as count FROM relations"
        ).fetchone()["count"]
        
        by_type = {}
        cursor = conn.execute(
            "SELECT relation_type, COUNT(*) as count FROM relations GROUP BY relation_type"
        )
        for row in cursor.fetchall():
            by_type[row["relation_type"]] = row["count"]
        
        total_states = conn.execute(
            "SELECT COUNT(*) as count FROM relation_states"
        ).fetchone()["count"]
        
        avg_strength = conn.execute(
            "SELECT AVG(strength) as avg FROM relations"
        ).fetchone()["avg"] or 0
        
        avg_sentiment = conn.execute(
            "SELECT AVG(sentiment) as avg FROM relations"
        ).fetchone()["avg"] or 0
        
        return {
            "total_relations": total,
            "by_type": by_type,
            "total_state_changes": total_states,
            "avg_strength": avg_strength,
            "avg_sentiment": avg_sentiment
        }
    
    def clear(self) -> None:
        """Clear all relations from the graph."""
        conn = self.conn
        conn.execute("DELETE FROM relation_states")
        conn.execute("DELETE FROM relations")
        conn.commit()
        self._cache.clear()
        logger.info("Cleared all relations from graph")
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _row_to_relation(self, row: sqlite3.Row) -> Relation:
        """Convert a database row to a Relation."""
        return Relation(
            relation_id=row["relation_id"],
            source_entity=row["source_entity"],
            target_entity=row["target_entity"],
            relation_type=row["relation_type"],
            strength=row["strength"] or 0.5,
            sentiment=row["sentiment"] or 0.0,
            established_chapter=row["established_chapter"],
            last_updated_chapter=row["last_updated_chapter"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"]
        )
    
    def _load_relation_history(self, relation_id: str) -> List[RelationState]:
        """Load state history for a relation."""
        conn = self.conn
        cursor = conn.execute("""
            SELECT * FROM relation_states 
            WHERE relation_id = ?
            ORDER BY chapter_id, created_at
        """, (relation_id,))
        
        states = []
        for row in cursor.fetchall():
            states.append(RelationState(
                chapter_id=row["chapter_id"],
                strength=row["strength"] or 0.5,
                sentiment=row["sentiment"] or 0.0,
                status=row["status"] or "active",
                notes=row["notes"] or "",
                changed_by_event=row["changed_by_event"],
                created_at=row["created_at"]
            ))
        
        return states