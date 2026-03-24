"""
Events Store for Long-Term Narrative Memory System.

This module provides the EventsStore for tracking narrative events,
plot points, and their relationships throughout the book generation process.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

from src.core.exceptions import NarrativeError, EventConflictError


logger = logging.getLogger("BookWriterAI")


class EventType(Enum):
    """Types of narrative events."""
    PLOT_POINT = "plot_point"
    CHARACTER_ACTION = "character_action"
    REVELATION = "revelation"
    CONFLICT = "conflict"
    RESOLUTION = "resolution"
    FORESHADOWING = "foreshadowing"
    TWIST = "twist"
    MILESTONE = "milestone"
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"


@dataclass
class NarrativeEvent:
    """
    Represents a significant event in the narrative.
    
    Events are the building blocks of the narrative memory system,
    tracking what happens, when, who's involved, and how it relates
    to other events.
    """
    event_id: str
    event_type: str  # EventType value
    chapter_id: int
    timestamp: str  # Narrative time (e.g., "Day 1", "Chapter 3", "1984-06-15")
    description: str
    entities_involved: List[str] = field(default_factory=list)  # Entity IDs
    consequences: List[str] = field(default_factory=list)  # Event IDs of consequences
    emotional_valence: float = 0.0  # -1.0 (negative) to 1.0 (positive)
    importance_weight: float = 0.5  # 0.0 to 1.0
    foreshadowing_refs: List[str] = field(default_factory=list)  # Event IDs this foreshadows
    resolution_refs: List[str] = field(default_factory=list)  # Event IDs this resolves
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NarrativeEvent":
        """Create from dictionary."""
        return cls(**data)
    
    def is_resolved(self) -> bool:
        """Check if this event has been resolved."""
        return len(self.resolution_refs) > 0
    
    def is_foreshadowing(self) -> bool:
        """Check if this event is foreshadowing something."""
        return len(self.foreshadowing_refs) > 0


class EventsStore:
    """
    Persistent storage for narrative events with semantic indexing.
    
    Uses SQLite for persistence and provides efficient querying
    by chapter, entity, type, and resolution status.
    """
    
    def __init__(self, db_path: str = "checkpoints/narrative_memory.db"):
        """
        Initialize the events store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
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
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                chapter_id INTEGER,
                timestamp TEXT,
                description TEXT,
                entities_involved TEXT,
                consequences TEXT,
                emotional_valence REAL,
                importance_weight REAL,
                foreshadowing_refs TEXT,
                resolution_refs TEXT,
                metadata TEXT,
                created_at TEXT
            )
        """)
        
        # Create indexes for efficient querying
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_chapter 
            ON events(chapter_id)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type 
            ON events(event_type)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_importance 
            ON events(importance_weight DESC)
        """)
        
        conn.commit()
    
    def add_event(self, event: NarrativeEvent) -> str:
        """
        Add an event to the store.
        
        Args:
            event: The event to add
            
        Returns:
            The event ID
        """
        conn = self.conn
        
        conn.execute("""
            INSERT OR REPLACE INTO events (
                event_id, event_type, chapter_id, timestamp, description,
                entities_involved, consequences, emotional_valence,
                importance_weight, foreshadowing_refs, resolution_refs,
                metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.event_type,
            event.chapter_id,
            event.timestamp,
            event.description,
            json.dumps(event.entities_involved),
            json.dumps(event.consequences),
            event.emotional_valence,
            event.importance_weight,
            json.dumps(event.foreshadowing_refs),
            json.dumps(event.resolution_refs),
            json.dumps(event.metadata),
            event.created_at
        ))
        
        conn.commit()
        logger.debug(f"Added event: {event.event_id} ({event.event_type})")
        
        return event.event_id
    
    def get_event(self, event_id: str) -> Optional[NarrativeEvent]:
        """Get an event by ID."""
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM events WHERE event_id = ?",
            (event_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return self._row_to_event(row)
        return None
    
    def get_events_by_chapter(self, chapter_id: int) -> List[NarrativeEvent]:
        """Get all events in a chapter."""
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM events WHERE chapter_id = ? ORDER BY importance_weight DESC",
            (chapter_id,)
        )
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_events_by_type(self, event_type: str) -> List[NarrativeEvent]:
        """Get all events of a specific type."""
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM events WHERE event_type = ? ORDER BY chapter_id",
            (event_type,)
        )
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_events_by_entity(self, entity_id: str) -> List[NarrativeEvent]:
        """Get all events involving an entity."""
        conn = self.conn
        # Use JSON search for entities_involved array
        cursor = conn.execute(
            """SELECT * FROM events 
               WHERE entities_involved LIKE ? 
               ORDER BY chapter_id""",
            (f'%"{entity_id}"%',)
        )
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_unresolved_events(self) -> List[NarrativeEvent]:
        """Get all unresolved events (plot threads)."""
        conn = self.conn
        # Events that are not resolutions and have no resolution_refs pointing to them
        cursor = conn.execute("""
            SELECT * FROM events 
            WHERE event_type NOT IN ('resolution', 'description')
            AND (resolution_refs IS NULL OR resolution_refs = '[]')
            ORDER BY importance_weight DESC
        """)
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_foreshadowing_opportunities(self) -> List[NarrativeEvent]:
        """
        Get events that could be foreshadowed.
        
        Returns important future events that haven't been foreshadowed yet.
        """
        conn = self.conn
        # Get events with high importance that aren't foreshadowed
        cursor = conn.execute("""
            SELECT * FROM events 
            WHERE importance_weight >= 0.7
            AND foreshadowing_refs = '[]'
            AND event_type IN ('plot_point', 'revelation', 'twist', 'milestone')
            ORDER BY chapter_id
        """)
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_recent_events(self, n: int = 10) -> List[NarrativeEvent]:
        """Get the N most recent events by chapter."""
        conn = self.conn
        cursor = conn.execute("""
            SELECT * FROM events 
            ORDER BY chapter_id DESC, created_at DESC 
            LIMIT ?
        """, (n,))
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_events_in_range(
        self, 
        start_chapter: int, 
        end_chapter: int
    ) -> List[NarrativeEvent]:
        """Get events within a chapter range."""
        conn = self.conn
        cursor = conn.execute(
            """SELECT * FROM events 
               WHERE chapter_id >= ? AND chapter_id <= ?
               ORDER BY chapter_id""",
            (start_chapter, end_chapter)
        )
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def link_events(
        self, 
        event_id_1: str, 
        event_id_2: str, 
        relationship: str
    ) -> None:
        """
        Link two events with a relationship.
        
        Args:
            event_id_1: First event ID
            event_id_2: Second event ID
            relationship: Type of relationship ('causes', 'foreshadows', 'resolves')
        """
        event_1 = self.get_event(event_id_1)
        event_2 = self.get_event(event_id_2)
        
        if not event_1 or not event_2:
            raise NarrativeError(f"Cannot link events: one or both not found")
        
        if relationship == "causes":
            if event_id_2 not in event_1.consequences:
                event_1.consequences.append(event_id_2)
                self.add_event(event_1)
                
        elif relationship == "foreshadows":
            if event_id_2 not in event_1.foreshadowing_refs:
                event_1.foreshadowing_refs.append(event_id_2)
                self.add_event(event_1)
                
        elif relationship == "resolves":
            if event_id_2 not in event_1.resolution_refs:
                event_1.resolution_refs.append(event_id_2)
                self.add_event(event_1)
        
        logger.debug(f"Linked events: {event_id_1} --[{relationship}]--> {event_id_2}")
    
    def get_event_chain(self, event_id: str) -> List[NarrativeEvent]:
        """
        Get the chain of events leading to/from an event.
        
        Returns events connected by cause-effect relationships.
        """
        chain = []
        visited = set()
        
        def traverse(eid: str, direction: str = "forward"):
            if eid in visited:
                return
            visited.add(eid)
            
            event = self.get_event(eid)
            if not event:
                return
            
            chain.append(event)
            
            if direction in ["forward", "both"]:
                for consequence_id in event.consequences:
                    traverse(consequence_id, "forward")
            
            if direction in ["backward", "both"]:
                # Find events that have this as a consequence
                conn = self.conn
                cursor = conn.execute(
                    "SELECT event_id FROM events WHERE consequences LIKE ?",
                    (f'%"{eid}"%',)
                )
                for row in cursor.fetchall():
                    traverse(row["event_id"], "backward")
        
        traverse(event_id, "both")
        return chain
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored events."""
        conn = self.conn
        
        total = conn.execute("SELECT COUNT(*) as count FROM events").fetchone()["count"]
        
        by_type = {}
        cursor = conn.execute(
            "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type"
        )
        for row in cursor.fetchall():
            by_type[row["event_type"]] = row["count"]
        
        unresolved = len(self.get_unresolved_events())
        
        return {
            "total_events": total,
            "by_type": by_type,
            "unresolved_count": unresolved,
            "avg_importance": conn.execute(
                "SELECT AVG(importance_weight) as avg FROM events"
            ).fetchone()["avg"] or 0
        }
    
    def clear(self) -> None:
        """Clear all events from the store."""
        conn = self.conn
        conn.execute("DELETE FROM events")
        conn.commit()
        logger.info("Cleared all events from store")
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _row_to_event(self, row: sqlite3.Row) -> NarrativeEvent:
        """Convert a database row to a NarrativeEvent."""
        return NarrativeEvent(
            event_id=row["event_id"],
            event_type=row["event_type"],
            chapter_id=row["chapter_id"],
            timestamp=row["timestamp"],
            description=row["description"],
            entities_involved=json.loads(row["entities_involved"]) if row["entities_involved"] else [],
            consequences=json.loads(row["consequences"]) if row["consequences"] else [],
            emotional_valence=row["emotional_valence"] or 0.0,
            importance_weight=row["importance_weight"] or 0.5,
            foreshadowing_refs=json.loads(row["foreshadowing_refs"]) if row["foreshadowing_refs"] else [],
            resolution_refs=json.loads(row["resolution_refs"]) if row["resolution_refs"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"]
        )