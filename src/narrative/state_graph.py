"""
Narrative State Graph for Long-Term Narrative Memory System.

This module provides the NarrativeStateGraph facade that coordinates
all narrative memory components (events, entities, relations) and
provides a unified interface for narrative state management.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from src.core.config import NarrativeMemoryConfig
from src.core.exceptions import NarrativeError, EntityNotFoundError
from src.narrative.events import EventsStore, NarrativeEvent, EventType
from src.narrative.entities import EntityRegistry, Entity, EntityState, EntityType, StateType
from src.narrative.relations import RelationsGraph, Relation, RelationState, RelationType
from src.narrative.context_synthesizer import ContextSynthesizer, NarrativeContext


logger = logging.getLogger("BookWriterAI")


class NarrativeStateGraph:
    """
    Facade for the Long-Term Narrative Memory System.
    
    Coordinates:
    - EventsStore: Plot events and their relationships
    - EntityRegistry: Characters, locations, objects, concepts
    - RelationsGraph: Relationships between entities
    - ContextSynthesizer: Context generation for chapter writing
    
    Provides a unified interface for:
    - Tracking narrative state across chapters
    - Maintaining consistency
    - Generating context for AI generation
    - Extracting narrative elements from generated content
    """
    
    def __init__(self, config: NarrativeMemoryConfig):
        """
        Initialize the narrative state graph.
        
        Args:
            config: Narrative memory configuration
        """
        self.config = config
        self.db_path = config.persistence_path
        
        # Initialize components
        self.events = EventsStore(self.db_path)
        self.entities = EntityRegistry(self.db_path)
        self.relations = RelationsGraph(self.db_path)
        self.context_synthesizer = ContextSynthesizer(
            self.events, self.entities, self.relations, config
        )
        
        # Track current state
        self._current_chapter = 0
        self._current_timestamp = "Beginning"
        
        logger.info(f"Initialized NarrativeStateGraph with db: {self.db_path}")
    
    # =========================================================================
    # Event Management
    # =========================================================================
    
    def add_event(
        self,
        event_type: str,
        description: str,
        entities_involved: List[str] = None,
        chapter_id: Optional[int] = None,
        timestamp: Optional[str] = None,
        emotional_valence: float = 0.0,
        importance_weight: float = 0.5,
        **kwargs
    ) -> str:
        """
        Add a narrative event.
        
        Args:
            event_type: Type of event (plot_point, character_action, etc.)
            description: What happened
            entities_involved: IDs of entities involved
            chapter_id: Chapter where event occurs
            timestamp: Narrative time
            emotional_valence: Emotional impact (-1 to 1)
            importance_weight: Importance (0 to 1)
            
        Returns:
            Event ID
        """
        import uuid
        
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        chapter_id = chapter_id or self._current_chapter
        timestamp = timestamp or self._current_timestamp
        
        event = NarrativeEvent(
            event_id=event_id,
            event_type=event_type,
            chapter_id=chapter_id,
            timestamp=timestamp,
            description=description,
            entities_involved=entities_involved or [],
            emotional_valence=emotional_valence,
            importance_weight=importance_weight,
            **kwargs
        )
        
        return self.events.add_event(event)
    
    def get_event(self, event_id: str) -> Optional[NarrativeEvent]:
        """Get an event by ID."""
        return self.events.get_event(event_id)
    
    def get_chapter_events(self, chapter_id: int) -> List[NarrativeEvent]:
        """Get all events in a chapter."""
        return self.events.get_events_by_chapter(chapter_id)
    
    def link_events(
        self, 
        cause_event_id: str, 
        effect_event_id: str,
        relationship: str = "causes"
    ) -> None:
        """Link two events with a relationship."""
        self.events.link_events(cause_event_id, effect_event_id, relationship)
    
    # =========================================================================
    # Entity Management
    # =========================================================================
    
    def register_entity(
        self,
        name: str,
        entity_type: str = "character",
        entity_id: Optional[str] = None,
        description: str = "",
        attributes: Dict[str, Any] = None,
        aliases: List[str] = None,
        importance: float = 0.5
    ) -> str:
        """
        Register a new entity.
        
        Args:
            name: Entity name
            entity_type: Type (character, location, object, etc.)
            entity_id: Optional custom ID
            description: Entity description
            attributes: Additional attributes
            aliases: Alternative names
            importance: Importance weight
            
        Returns:
            Entity ID
        """
        import uuid
        
        entity_id = entity_id or f"ent_{uuid.uuid4().hex[:8]}"
        
        entity = Entity(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            aliases=aliases or [],
            first_appearance=self._current_chapter,
            description=description,
            attributes=attributes or {},
            importance=importance
        )
        
        return self.entities.register_entity(entity)
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self.entities.get_entity(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get an entity by name or alias."""
        return self.entities.get_entity_by_name(name)
    
    def update_entity_state(
        self,
        entity_id: str,
        state_type: str,
        attributes: Dict[str, Any],
        chapter_id: Optional[int] = None,
        changed_by_event: Optional[str] = None,
        notes: str = ""
    ) -> None:
        """
        Update an entity's state.
        
        Args:
            entity_id: The entity ID
            state_type: Type of state change
            attributes: New/changed attributes
            chapter_id: Chapter where change occurs
            changed_by_event: Event that caused the change
            notes: Additional notes
        """
        chapter_id = chapter_id or self._current_chapter
        
        state = EntityState(
            chapter_id=chapter_id,
            timestamp=self._current_timestamp,
            state_type=state_type,
            attributes=attributes,
            changed_by_event=changed_by_event,
            notes=notes
        )
        
        self.entities.update_entity_state(entity_id, state)
    
    def get_characters(self) -> List[Entity]:
        """Get all character entities."""
        return self.entities.get_entities_by_type("character")
    
    def get_locations(self) -> List[Entity]:
        """Get all location entities."""
        return self.entities.get_entities_by_type("location")
    
    # =========================================================================
    # Relation Management
    # =========================================================================
    
    def add_relation(
        self,
        source_entity: str,
        target_entity: str,
        relation_type: str,
        strength: float = 0.5,
        sentiment: float = 0.0,
        chapter_id: Optional[int] = None
    ) -> str:
        """
        Add a relationship between entities.
        
        Args:
            source_entity: Source entity ID
            target_entity: Target entity ID
            relation_type: Type of relationship
            strength: Relationship strength (0-1)
            sentiment: Sentiment (-1 hostile to 1 friendly)
            chapter_id: Chapter where relationship established
            
        Returns:
            Relation ID
        """
        import uuid
        
        relation_id = f"rel_{uuid.uuid4().hex[:8]}"
        chapter_id = chapter_id or self._current_chapter
        
        relation = Relation(
            relation_id=relation_id,
            source_entity=source_entity,
            target_entity=target_entity,
            relation_type=relation_type,
            strength=strength,
            sentiment=sentiment,
            established_chapter=chapter_id
        )
        
        return self.relations.add_relation(relation)
    
    def get_relation(
        self, 
        entity_a: str, 
        entity_b: str,
        relation_type: Optional[str] = None
    ) -> Optional[Relation]:
        """Get the relation between two entities."""
        return self.relations.get_relation_between(entity_a, entity_b, relation_type)
    
    def get_entity_relations(
        self, 
        entity_id: str,
        relation_type: Optional[str] = None
    ) -> List[Relation]:
        """Get all relations involving an entity."""
        return self.relations.get_relations(entity_id, relation_type)
    
    def update_relation(
        self,
        relation_id: str,
        strength: Optional[float] = None,
        sentiment: Optional[float] = None,
        status: str = "active",
        notes: str = "",
        changed_by_event: Optional[str] = None,
        chapter_id: Optional[int] = None
    ) -> None:
        """Update a relation's state."""
        relation = self.relations.get_relation(relation_id)
        if not relation:
            raise ValueError(f"Relation not found: {relation_id}")
        
        chapter_id = chapter_id or self._current_chapter
        
        state = RelationState(
            chapter_id=chapter_id,
            strength=strength if strength is not None else relation.strength,
            sentiment=sentiment if sentiment is not None else relation.sentiment,
            status=status,
            notes=notes,
            changed_by_event=changed_by_event
        )
        
        self.relations.update_relation(relation_id, state)
    
    # =========================================================================
    # Context Generation
    # =========================================================================
    
    def get_context_for_chapter(
        self, 
        chapter_id: int,
        chapter_info: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None
    ) -> NarrativeContext:
        """
        Get narrative context for chapter generation.
        
        This is the primary method for retrieving context before
        generating a new chapter.
        """
        max_tokens = max_tokens or self.config.context_synthesis_tokens
        return self.context_synthesizer.synthesize_context(
            chapter_id, 
            chapter_info or {}, 
            max_tokens
        )
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get the current narrative state as a dictionary."""
        return {
            "current_chapter": self._current_chapter,
            "current_timestamp": self._current_timestamp,
            "recent_events": [
                e.description for e in self.events.get_recent_events(5)
            ],
            "active_entities": [
                e.name for e in self.entities.get_all_entities()[:10]
            ],
            "unresolved_threads": len(self.events.get_unresolved_events())
        }
    
    # =========================================================================
    # State Management
    # =========================================================================
    
    def set_chapter(self, chapter_id: int, timestamp: Optional[str] = None) -> None:
        """Set the current chapter context."""
        self._current_chapter = chapter_id
        self._current_timestamp = timestamp or f"Chapter {chapter_id}"
        logger.debug(f"Set current chapter: {chapter_id}")
    
    def advance_chapter(self) -> int:
        """Advance to the next chapter."""
        self._current_chapter += 1
        self._current_timestamp = f"Chapter {self._current_chapter}"
        return self._current_chapter
    
    # =========================================================================
    # Automatic Extraction
    # =========================================================================
    
    def extract_from_content(
        self,
        content: str,
        chapter_id: int,
        extract_characters: bool = True,
        extract_events: bool = True,
        extract_relations: bool = True
    ) -> Dict[str, List[str]]:
        """
        Extract narrative elements from generated content.
        
        Uses pattern matching and heuristics to identify:
        - Character mentions
        - Key events
        - Relationship indicators
        
        Args:
            content: Generated chapter content
            chapter_id: Chapter number
            extract_characters: Whether to extract characters
            extract_events: Whether to extract events
            extract_relations: Whether to extract relations
            
        Returns:
            Dictionary of extracted element IDs
        """
        extracted = {
            "characters": [],
            "events": [],
            "relations": []
        }
        
        if extract_characters:
            extracted["characters"] = self._extract_characters(content, chapter_id)
        
        if extract_events:
            extracted["events"] = self._extract_events(content, chapter_id)
        
        if extract_relations:
            extracted["relations"] = self._extract_relations(content, chapter_id)
        
        return extracted
    
    def _extract_characters(self, content: str, chapter_id: int) -> List[str]:
        """Extract character mentions from content."""
        import re
        
        # Find capitalized words that might be names
        potential_names = re.findall(r'\b([A-Z][a-z]+)\b', content)
        
        # Filter out common non-name words
        non_names = {"The", "A", "An", "But", "And", "Or", "In", "On", "At", 
                    "To", "For", "It", "He", "She", "They", "We", "I", "You",
                    "This", "That", "There", "Here", "When", "Where", "What",
                    "Chapter", "Section", "Part"}
        
        extracted_ids = []
        
        for name in potential_names:
            if name in non_names:
                continue
            
            # Check if already registered
            entity = self.entities.get_entity_by_name(name)
            
            if entity:
                # Update last mention
                if entity.last_mention != chapter_id:
                    self.entities.update_entity_state(
                        entity.entity_id,
                        "mention",
                        {"mentioned": True},
                        chapter_id=chapter_id
                    )
                extracted_ids.append(entity.entity_id)
            else:
                # Register new character
                entity_id = self.register_entity(
                    name=name,
                    entity_type="character",
                    description=f"Character mentioned in chapter {chapter_id}",
                    importance=0.3
                )
                extracted_ids.append(entity_id)
        
        return extracted_ids
    
    def _extract_events(self, content: str, chapter_id: int) -> List[str]:
        """Extract key events from content."""
        # This is a simplified extraction - in production, would use NLP/LLM
        import re
        
        # Look for action verbs and their subjects
        action_patterns = [
            r'(\w+)\s+(discovered|found|realized|decided|announced|revealed|attacked|defeated|met|left|arrived)',
            r'(Suddenly|Then|Finally),\s+(\w+)\s+(\w+)',
        ]
        
        extracted_ids = []
        
        for pattern in action_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:3]:  # Limit extractions
                description = ' '.join(match) if isinstance(match, tuple) else match
                
                event_id = self.add_event(
                    event_type="character_action",
                    description=description,
                    chapter_id=chapter_id,
                    importance_weight=0.3
                )
                extracted_ids.append(event_id)
        
        return extracted_ids
    
    def _extract_relations(self, content: str, chapter_id: int) -> List[str]:
        """Extract relationship indicators from content."""
        import re
        
        # Look for relationship indicators
        relation_patterns = [
            (r'(\w+)\s+and\s+(\w+)\s+were\s+(friends|enemies|lovers|allies)', 'friend'),
            (r'(\w+)\s+(loved|hated|trusted|betrayed)\s+(\w+)', 'emotional'),
        ]
        
        extracted_ids = []
        
        for pattern, rel_type in relation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:  # Limit extractions
                if len(match) >= 2:
                    name1, name2 = match[0], match[1]
                    
                    # Get or create entities
                    entity1 = self.entities.get_entity_by_name(name1)
                    entity2 = self.entities.get_entity_by_name(name2)
                    
                    if entity1 and entity2:
                        # Check if relation exists
                        existing = self.relations.get_relation_between(
                            entity1.entity_id, entity2.entity_id
                        )
                        
                        if not existing:
                            relation_id = self.add_relation(
                                source_entity=entity1.entity_id,
                                target_entity=entity2.entity_id,
                                relation_type=rel_type,
                                chapter_id=chapter_id
                            )
                            extracted_ids.append(relation_id)
        
        return extracted_ids
    
    # =========================================================================
    # Consistency Validation
    # =========================================================================
    
    def validate_consistency(
        self,
        chapter_id: int,
        content: str
    ) -> List[Dict[str, Any]]:
        """
        Validate content for narrative consistency.
        
        Checks for:
        - Character behavior consistency
        - Timeline consistency
        - Fact contradictions
        
        Args:
            chapter_id: Chapter being validated
            content: Chapter content
            
        Returns:
            List of consistency issues found
        """
        issues = []
        
        # Check character states
        characters = self.entities.get_entities_by_type("character")
        for char in characters:
            char_issues = self.entities.validate_consistency(
                char.entity_id,
                chapter_id,
                {}  # Would extract proposed states from content
            )
            for issue in char_issues:
                issues.append({
                    "type": "character_consistency",
                    "entity": char.name,
                    "issue": issue
                })
        
        # Check for unresolved threads that should be addressed
        unresolved = self.events.get_unresolved_events()
        old_threads = [e for e in unresolved if e.chapter_id < chapter_id - 5]
        for thread in old_threads:
            if thread.description.lower() not in content.lower():
                issues.append({
                    "type": "unresolved_thread",
                    "event_id": thread.event_id,
                    "description": thread.description,
                    "suggestion": f"Consider addressing or advancing this plot thread"
                })
        
        return issues
    
    # =========================================================================
    # Statistics and Export
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the narrative state."""
        return {
            "events": self.events.get_statistics(),
            "entities": self.entities.get_statistics(),
            "relations": self.relations.get_statistics(),
            "current_chapter": self._current_chapter
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export the entire narrative state as a dictionary."""
        return {
            "current_chapter": self._current_chapter,
            "current_timestamp": self._current_timestamp,
            "events": [e.to_dict() for e in self.events.get_events_in_range(0, 1000)],
            "entities": [e.to_dict() for e in self.entities.get_all_entities()],
            "relations": [r.to_dict() for r in self.relations.get_relations("")],
            "statistics": self.get_statistics()
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import narrative state from a dictionary."""
        # Clear existing state
        self.events.clear()
        self.entities.clear()
        self.relations.clear()
        
        # Import events
        for event_data in state.get("events", []):
            event = NarrativeEvent.from_dict(event_data)
            self.events.add_event(event)
        
        # Import entities
        for entity_data in state.get("entities", []):
            entity = Entity.from_dict(entity_data)
            self.entities.register_entity(entity)
        
        # Import relations
        for relation_data in state.get("relations", []):
            relation = Relation.from_dict(relation_data)
            self.relations.add_relation(relation)
        
        # Set current state
        self._current_chapter = state.get("current_chapter", 0)
        self._current_timestamp = state.get("current_timestamp", "Beginning")
        
        logger.info(f"Imported narrative state: {len(state.get('events', []))} events, "
                   f"{len(state.get('entities', []))} entities")
    
    def clear(self) -> None:
        """Clear all narrative state."""
        self.events.clear()
        self.entities.clear()
        self.relations.clear()
        self._current_chapter = 0
        self._current_timestamp = "Beginning"
        logger.info("Cleared all narrative state")
    
    def close(self) -> None:
        """Close all database connections."""
        self.events.close()
        self.entities.close()
        self.relations.close()
        logger.info("Closed narrative state graph")