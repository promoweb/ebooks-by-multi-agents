"""
Tests for the Narrative Memory System.

Tests cover EventsStore, EntityRegistry, RelationsGraph,
ContextSynthesizer, and NarrativeStateGraph.
"""

import pytest
import tempfile
import os
from datetime import datetime

from src.narrative import (
    NarrativeEvent,
    EventsStore,
    Entity,
    EntityRegistry,
    Relation,
    RelationsGraph,
    ContextSynthesizer,
    NarrativeStateGraph,
)


class TestEventsStore:
    """Tests for EventsStore."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def events_store(self, temp_db):
        """Create an EventsStore with temporary database."""
        return EventsStore(db_path=temp_db)
    
    def test_add_event(self, events_store):
        """Test adding an event."""
        event = NarrativeEvent(
            event_id="test_1",
            event_type="plot_point",
            chapter_id=1,
            timestamp="2024-01-01",
            description="Test event",
            entities_involved=["char_1"],
            consequences=[],
            emotional_valence=0.5,
            importance_weight=0.8
        )
        
        event_id = events_store.add_event(event)
        assert event_id == "test_1"
    
    def test_get_events_by_chapter(self, events_store):
        """Test retrieving events by chapter."""
        # Add events
        for i in range(3):
            event = NarrativeEvent(
                event_id=f"event_{i}",
                event_type="plot_point",
                chapter_id=1,
                timestamp=f"2024-01-0{i+1}",
                description=f"Event {i}",
                entities_involved=[],
                consequences=[],
                emotional_valence=0.5,
                importance_weight=0.5
            )
            events_store.add_event(event)
        
        # Add event in different chapter
        event = NarrativeEvent(
            event_id="event_3",
            event_type="plot_point",
            chapter_id=2,
            timestamp="2024-01-04",
            description="Event in chapter 2",
            entities_involved=[],
            consequences=[],
            emotional_valence=0.5,
            importance_weight=0.5
        )
        events_store.add_event(event)
        
        # Get events for chapter 1
        events = events_store.get_events_by_chapter(1)
        assert len(events) == 3
    
    def test_get_unresolved_events(self, events_store):
        """Test retrieving unresolved events."""
        # Add resolved event
        event1 = NarrativeEvent(
            event_id="resolved_1",
            event_type="plot_point",
            chapter_id=1,
            timestamp="2024-01-01",
            description="Resolved event",
            entities_involved=[],
            consequences=[],
            emotional_valence=0.5,
            importance_weight=0.5,
            resolution_refs=["some_event"]
        )
        events_store.add_event(event1)
        
        # Add unresolved event
        event2 = NarrativeEvent(
            event_id="unresolved_1",
            event_type="plot_point",
            chapter_id=1,
            timestamp="2024-01-02",
            description="Unresolved event",
            entities_involved=[],
            consequences=[],
            emotional_valence=0.5,
            importance_weight=0.5
        )
        events_store.add_event(event2)
        
        unresolved = events_store.get_unresolved_events()
        assert len(unresolved) == 1
        assert unresolved[0].event_id == "unresolved_1"


class TestEntityRegistry:
    """Tests for EntityRegistry."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def entity_registry(self, temp_db):
        """Create an EntityRegistry with temporary database."""
        return EntityRegistry(db_path=temp_db)
    
    def test_register_entity(self, entity_registry):
        """Test registering an entity."""
        entity = Entity(
            entity_id="char_1",
            entity_type="character",
            name="John Doe",
            aliases=["Johnny"],
            first_appearance=1,
            last_mention=1,
            attributes={"role": "protagonist"}
        )
        
        entity_id = entity_registry.register_entity(entity)
        assert entity_id == "char_1"
    
    def test_get_entity(self, entity_registry):
        """Test retrieving an entity."""
        entity = Entity(
            entity_id="char_1",
            entity_type="character",
            name="John Doe",
            aliases=[],
            first_appearance=1,
            last_mention=1,
            attributes={}
        )
        entity_registry.register_entity(entity)
        
        retrieved = entity_registry.get_entity("char_1")
        assert retrieved is not None
        assert retrieved.name == "John Doe"
    
    def test_find_entities_by_type(self, entity_registry):
        """Test finding entities by type."""
        # Add entities of different types
        for i, etype in enumerate(["character", "character", "location"]):
            entity = Entity(
                entity_id=f"entity_{i}",
                entity_type=etype,
                name=f"Entity {i}",
                aliases=[],
                first_appearance=1,
                last_mention=1,
                attributes={}
            )
            entity_registry.register_entity(entity)
        
        characters = entity_registry.find_entities_by_type("character")
        assert len(characters) == 2


class TestRelationsGraph:
    """Tests for RelationsGraph."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def relations_graph(self, temp_db):
        """Create a RelationsGraph with temporary database."""
        return RelationsGraph(db_path=temp_db)
    
    def test_add_relation(self, relations_graph):
        """Test adding a relation."""
        relation = Relation(
            relation_id="rel_1",
            source_entity="char_1",
            target_entity="char_2",
            relation_type="friend",
            strength=0.8,
            sentiment=0.7,
            established_chapter=1,
            last_updated_chapter=1
        )
        
        relation_id = relations_graph.add_relation(relation)
        assert relation_id == "rel_1"
    
    def test_get_relations(self, relations_graph):
        """Test retrieving relations for an entity."""
        # Add relations
        for i in range(2):
            relation = Relation(
                relation_id=f"rel_{i}",
                source_entity="char_1",
                target_entity=f"char_{i+2}",
                relation_type="friend",
                strength=0.5,
                sentiment=0.5,
                established_chapter=1,
                last_updated_chapter=1
            )
            relations_graph.add_relation(relation)
        
        relations = relations_graph.get_relations("char_1")
        assert len(relations) == 2
    
    def test_get_relation_between(self, relations_graph):
        """Test retrieving relation between two entities."""
        relation = Relation(
            relation_id="rel_1",
            source_entity="char_1",
            target_entity="char_2",
            relation_type="sibling",
            strength=0.9,
            sentiment=0.8,
            established_chapter=1,
            last_updated_chapter=1
        )
        relations_graph.add_relation(relation)
        
        retrieved = relations_graph.get_relation_between("char_1", "char_2")
        assert retrieved is not None
        assert retrieved.relation_type == "sibling"


class TestNarrativeStateGraph:
    """Tests for NarrativeStateGraph facade."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def state_graph(self, temp_db):
        """Create a NarrativeStateGraph with temporary database."""
        return NarrativeStateGraph(db_path=temp_db)
    
    def test_add_event(self, state_graph):
        """Test adding an event through the facade."""
        event = NarrativeEvent(
            event_id="event_1",
            event_type="plot_point",
            chapter_id=1,
            timestamp="2024-01-01",
            description="Test event",
            entities_involved=["char_1"],
            consequences=[],
            emotional_valence=0.5,
            importance_weight=0.8
        )
        
        event_id = state_graph.add_event(event)
        assert event_id == "event_1"
    
    def test_register_entity(self, state_graph):
        """Test registering an entity through the facade."""
        entity = Entity(
            entity_id="char_1",
            entity_type="character",
            name="John Doe",
            aliases=[],
            first_appearance=1,
            last_mention=1,
            attributes={}
        )
        
        entity_id = state_graph.register_entity(entity)
        assert entity_id == "char_1"
    
    def test_get_narrative_summary(self, state_graph):
        """Test getting narrative summary."""
        # Add some data
        event = NarrativeEvent(
            event_id="event_1",
            event_type="plot_point",
            chapter_id=1,
            timestamp="2024-01-01",
            description="Important event",
            entities_involved=[],
            consequences=[],
            emotional_valence=0.5,
            importance_weight=0.8
        )
        state_graph.add_event(event)
        
        summary = state_graph.get_narrative_summary()
        assert "total_events" in summary
        assert summary["total_events"] == 1


class TestContextSynthesizer:
    """Tests for ContextSynthesizer."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def context_synthesizer(self, temp_db):
        """Create a ContextSynthesizer with test data."""
        state_graph = NarrativeStateGraph(db_path=temp_db)
        
        # Add test data
        entity = Entity(
            entity_id="char_1",
            entity_type="character",
            name="John Doe",
            aliases=[],
            first_appearance=1,
            last_mention=1,
            attributes={"role": "protagonist"}
        )
        state_graph.register_entity(entity)
        
        event = NarrativeEvent(
            event_id="event_1",
            event_type="plot_point",
            chapter_id=1,
            timestamp="2024-01-01",
            description="John discovered the truth",
            entities_involved=["char_1"],
            consequences=[],
            emotional_valence=0.7,
            importance_weight=0.9
        )
        state_graph.add_event(event)
        
        return ContextSynthesizer(state_graph)
    
    def test_synthesize_context(self, context_synthesizer):
        """Test synthesizing context for chapter generation."""
        chapter_info = {
            "title": "Chapter 2",
            "summary": "John faces new challenges"
        }
        
        context = context_synthesizer.synthesize_context(
            current_chapter=2,
            chapter_info=chapter_info,
            max_tokens=1000
        )
        
        assert context is not None
        assert hasattr(context, 'relevant_events')
        assert hasattr(context, 'active_entities')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])