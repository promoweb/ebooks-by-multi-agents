"""
Entity Registry for Long-Term Narrative Memory System.

This module provides the EntityRegistry for tracking characters, locations,
objects, and concepts throughout the narrative with their evolving states.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

from src.core.exceptions import EntityNotFoundError, NarrativeConsistencyError


logger = logging.getLogger("BookWriterAI")


class EntityType(Enum):
    """Types of narrative entities."""
    CHARACTER = "character"
    LOCATION = "location"
    OBJECT = "object"
    CONCEPT = "concept"
    ORGANIZATION = "organization"
    EVENT = "event"


class StateType(Enum):
    """Types of entity states."""
    PHYSICAL = "physical"
    EMOTIONAL = "emotional"
    RELATIONAL = "relational"
    KNOWLEDGE = "knowledge"
    POSSESSION = "possession"
    STATUS = "status"


@dataclass
class EntityState:
    """
    Snapshot of entity state at a point in narrative time.
    
    Tracks how an entity changes throughout the narrative,
    enabling consistency checking and context synthesis.
    """
    chapter_id: int
    timestamp: str  # Narrative time
    state_type: str  # StateType value
    attributes: Dict[str, Any] = field(default_factory=dict)
    changed_by_event: Optional[str] = None  # event_id
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityState":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Entity:
    """
    Base class for all narrative entities.
    
    Entities are the "nouns" of the narrative: characters, locations,
    objects, concepts, and organizations. Each entity has a unique ID,
    type, and tracks its state throughout the narrative.
    """
    entity_id: str
    entity_type: str  # EntityType value
    name: str
    aliases: List[str] = field(default_factory=list)
    first_appearance: Optional[int] = None  # chapter_id
    last_mention: Optional[int] = None  # chapter_id
    attributes: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    importance: float = 0.5  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # State history is stored separately in the database
    state_history: List[EntityState] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # State history is stored separately
        data.pop('state_history', None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create from dictionary."""
        data.pop('state_history', None)  # Loaded separately
        return cls(**data)
    
    def get_current_state(self) -> Optional[EntityState]:
        """Get the most recent state."""
        if self.state_history:
            return self.state_history[-1]
        return None
    
    def get_state_at_chapter(self, chapter_id: int) -> Optional[EntityState]:
        """Get the entity state at a specific chapter."""
        for state in reversed(self.state_history):
            if state.chapter_id <= chapter_id:
                return state
        return None


class EntityRegistry:
    """
    Central registry for all narrative entities.
    
    Provides:
    - Entity registration and retrieval
    - State tracking and history
    - Consistency validation
    - SQLite persistence
    """
    
    def __init__(self, db_path: str = "checkpoints/narrative_memory.db"):
        """
        Initialize the entity registry.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Entity] = {}
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
        
        # Entities table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                aliases TEXT,
                first_appearance INTEGER,
                last_mention INTEGER,
                attributes TEXT,
                description TEXT,
                importance REAL,
                metadata TEXT,
                created_at TEXT
            )
        """)
        
        # Entity states table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                chapter_id INTEGER,
                timestamp TEXT,
                state_type TEXT,
                attributes TEXT,
                changed_by_event TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
            )
        """)
        
        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entities_type 
            ON entities(entity_type)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entities_name 
            ON entities(name)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_states_entity 
            ON entity_states(entity_id, chapter_id)
        """)
        
        conn.commit()
    
    def register_entity(self, entity: Entity) -> str:
        """
        Register a new entity.
        
        Args:
            entity: The entity to register
            
        Returns:
            The entity ID
        """
        conn = self.conn
        
        conn.execute("""
            INSERT OR REPLACE INTO entities (
                entity_id, entity_type, name, aliases, first_appearance,
                last_mention, attributes, description, importance, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.entity_id,
            entity.entity_type,
            entity.name,
            json.dumps(entity.aliases),
            entity.first_appearance,
            entity.last_mention,
            json.dumps(entity.attributes),
            entity.description,
            entity.importance,
            json.dumps(entity.metadata),
            entity.created_at
        ))
        
        conn.commit()
        
        # Update cache
        self._cache[entity.entity_id] = entity
        
        logger.debug(f"Registered entity: {entity.entity_id} ({entity.entity_type})")
        
        return entity.entity_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        # Check cache first
        if entity_id in self._cache:
            return self._cache[entity_id]
        
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM entities WHERE entity_id = ?",
            (entity_id,)
        )
        row = cursor.fetchone()
        
        if row:
            entity = self._row_to_entity(row)
            # Load state history
            entity.state_history = self._load_state_history(entity_id)
            self._cache[entity_id] = entity
            return entity
        
        return None
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get an entity by name or alias."""
        conn = self.conn
        
        # Check exact name match
        cursor = conn.execute(
            "SELECT * FROM entities WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        
        if row:
            return self.get_entity(row["entity_id"])
        
        # Check aliases
        cursor = conn.execute(
            "SELECT * FROM entities WHERE aliases LIKE ?",
            (f'%"{name}"%',)
        )
        row = cursor.fetchone()
        
        if row:
            return self.get_entity(row["entity_id"])
        
        return None
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM entities WHERE entity_type = ? ORDER BY importance DESC",
            (entity_type,)
        )
        
        entities = []
        for row in cursor.fetchall():
            entity = self._row_to_entity(row)
            entity.state_history = self._load_state_history(entity.entity_id)
            entities.append(entity)
        
        return entities
    
    def get_all_entities(self) -> List[Entity]:
        """Get all registered entities."""
        conn = self.conn
        cursor = conn.execute(
            "SELECT * FROM entities ORDER BY entity_type, importance DESC"
        )
        
        entities = []
        for row in cursor.fetchall():
            entity = self._row_to_entity(row)
            entity.state_history = self._load_state_history(entity.entity_id)
            entities.append(entity)
        
        return entities
    
    def update_entity_state(
        self, 
        entity_id: str, 
        state: EntityState
    ) -> None:
        """
        Update an entity's state.
        
        Args:
            entity_id: The entity ID
            state: The new state
        """
        entity = self.get_entity(entity_id)
        if not entity:
            raise EntityNotFoundError(entity_id)
        
        conn = self.conn
        
        # Add state to history
        conn.execute("""
            INSERT INTO entity_states (
                entity_id, chapter_id, timestamp, state_type,
                attributes, changed_by_event, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            state.chapter_id,
            state.timestamp,
            state.state_type,
            json.dumps(state.attributes),
            state.changed_by_event,
            state.notes,
            state.created_at
        ))
        
        # Update last_mention if needed
        if entity.last_mention is None or state.chapter_id > entity.last_mention:
            conn.execute(
                "UPDATE entities SET last_mention = ? WHERE entity_id = ?",
                (state.chapter_id, entity_id)
            )
        
        conn.commit()
        
        # Update cache
        entity.state_history.append(state)
        entity.last_mention = state.chapter_id
        
        logger.debug(f"Updated state for entity {entity_id} at chapter {state.chapter_id}")
    
    def get_entity_state_at(
        self, 
        entity_id: str, 
        chapter_id: int
    ) -> Optional[EntityState]:
        """
        Get entity state at a specific chapter.
        
        Returns the most recent state up to and including the chapter.
        """
        conn = self.conn
        cursor = conn.execute("""
            SELECT * FROM entity_states 
            WHERE entity_id = ? AND chapter_id <= ?
            ORDER BY chapter_id DESC, created_at DESC
            LIMIT 1
        """, (entity_id, chapter_id))
        
        row = cursor.fetchone()
        if row:
            return EntityState(
                chapter_id=row["chapter_id"],
                timestamp=row["timestamp"],
                state_type=row["state_type"],
                attributes=json.loads(row["attributes"]) if row["attributes"] else {},
                changed_by_event=row["changed_by_event"],
                notes=row["notes"] or "",
                created_at=row["created_at"]
            )
        
        return None
    
    def find_entities_by_attribute(
        self, 
        key: str, 
        value: Any
    ) -> List[Entity]:
        """Find entities with a specific attribute value."""
        conn = self.conn
        # JSON search in attributes
        cursor = conn.execute(
            "SELECT * FROM entities WHERE attributes LIKE ?",
            (f'%"{key}":%',)
        )
        
        entities = []
        for row in cursor.fetchall():
            entity = self._row_to_entity(row)
            if entity.attributes.get(key) == value:
                entity.state_history = self._load_state_history(entity.entity_id)
                entities.append(entity)
        
        return entities
    
    def get_entities_in_chapter(self, chapter_id: int) -> List[Entity]:
        """Get all entities mentioned in a specific chapter."""
        conn = self.conn
        cursor = conn.execute("""
            SELECT DISTINCT e.* FROM entities e
            JOIN entity_states es ON e.entity_id = es.entity_id
            WHERE es.chapter_id = ?
            UNION
            SELECT * FROM entities WHERE first_appearance = ?
        """, (chapter_id, chapter_id))
        
        entities = []
        for row in cursor.fetchall():
            entity = self._row_to_entity(row)
            entity.state_history = self._load_state_history(entity.entity_id)
            entities.append(entity)
        
        return entities
    
    def validate_consistency(
        self, 
        entity_id: str, 
        chapter_id: int, 
        proposed_state: Dict[str, Any]
    ) -> List[str]:
        """
        Validate consistency of proposed state with history.
        
        Returns list of inconsistencies found.
        """
        inconsistencies = []
        
        entity = self.get_entity(entity_id)
        if not entity:
            return ["Entity not found"]
        
        current_state = self.get_entity_state_at(entity_id, chapter_id - 1)
        if not current_state:
            return []  # No previous state to compare
        
        # Check for contradictions
        for key, value in proposed_state.items():
            if key in current_state.attributes:
                current_value = current_state.attributes[key]
                
                # Simple contradiction check
                if isinstance(value, bool) and isinstance(current_value, bool):
                    if value != current_value:
                        inconsistencies.append(
                            f"Attribute '{key}' changed from {current_value} to {value} "
                            f"without explanation"
                        )
                
                # Check for impossible changes
                if key == "location" and current_value != value:
                    # Location change should be explained
                    inconsistencies.append(
                        f"Location changed from '{current_value}' to '{value}' - "
                        f"ensure this is explained in the narrative"
                    )
        
        return inconsistencies
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered entities."""
        conn = self.conn
        
        total = conn.execute("SELECT COUNT(*) as count FROM entities").fetchone()["count"]
        
        by_type = {}
        cursor = conn.execute(
            "SELECT entity_type, COUNT(*) as count FROM entities GROUP BY entity_type"
        )
        for row in cursor.fetchall():
            by_type[row["entity_type"]] = row["count"]
        
        total_states = conn.execute(
            "SELECT COUNT(*) as count FROM entity_states"
        ).fetchone()["count"]
        
        return {
            "total_entities": total,
            "by_type": by_type,
            "total_states": total_states,
            "avg_states_per_entity": total_states / max(1, total)
        }
    
    def clear(self) -> None:
        """Clear all entities from the registry."""
        conn = self.conn
        conn.execute("DELETE FROM entity_states")
        conn.execute("DELETE FROM entities")
        conn.commit()
        self._cache.clear()
        logger.info("Cleared all entities from registry")
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _row_to_entity(self, row: sqlite3.Row) -> Entity:
        """Convert a database row to an Entity."""
        return Entity(
            entity_id=row["entity_id"],
            entity_type=row["entity_type"],
            name=row["name"],
            aliases=json.loads(row["aliases"]) if row["aliases"] else [],
            first_appearance=row["first_appearance"],
            last_mention=row["last_mention"],
            attributes=json.loads(row["attributes"]) if row["attributes"] else {},
            description=row["description"] or "",
            importance=row["importance"] or 0.5,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"]
        )
    
    def _load_state_history(self, entity_id: str) -> List[EntityState]:
        """Load state history for an entity."""
        conn = self.conn
        cursor = conn.execute("""
            SELECT * FROM entity_states 
            WHERE entity_id = ?
            ORDER BY chapter_id, created_at
        """, (entity_id,))
        
        states = []
        for row in cursor.fetchall():
            states.append(EntityState(
                chapter_id=row["chapter_id"],
                timestamp=row["timestamp"],
                state_type=row["state_type"],
                attributes=json.loads(row["attributes"]) if row["attributes"] else {},
                changed_by_event=row["changed_by_event"],
                notes=row["notes"] or "",
                created_at=row["created_at"]
            ))
        
        return states