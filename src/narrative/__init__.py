"""
Narrative Memory System for BookWriterAI.

This module provides the Long-Term Narrative Memory System for tracking
plot events, characters, locations, and their relationships throughout
the book generation process.

Key Components:
- EventsStore: Track narrative events and plot points
- EntityRegistry: Manage characters, locations, objects, concepts
- RelationsGraph: Track relationships between entities
- ContextSynthesizer: Generate context for chapter generation
- NarrativeStateGraph: Unified facade for all components
- EmotionalArc: Plan and manage emotional trajectories
- TensionManager: Analyze and adjust narrative tension
"""

from src.narrative.events import (
    EventsStore,
    NarrativeEvent,
    EventType,
)
from src.narrative.entities import (
    EntityRegistry,
    Entity,
    EntityState,
    EntityType,
    StateType,
)
from src.narrative.relations import (
    RelationsGraph,
    Relation,
    RelationState,
    RelationType,
)
from src.narrative.context_synthesizer import (
    ContextSynthesizer,
    NarrativeContext,
)
from src.narrative.state_graph import NarrativeStateGraph
from src.narrative.emotional_arc import (
    ArcShape,
    Emotion,
    ResolutionStyle,
    EmotionalBeat,
    EmotionalArc,
    TensionProfile,
    TensionAdjustment,
    EmotionalArcPlanner,
    TensionManager,
)

__all__ = [
    # Events
    "EventsStore",
    "NarrativeEvent",
    "EventType",
    # Entities
    "EntityRegistry",
    "Entity",
    "EntityState",
    "EntityType",
    "StateType",
    # Relations
    "RelationsGraph",
    "Relation",
    "RelationState",
    "RelationType",
    # Context
    "ContextSynthesizer",
    "NarrativeContext",
    # Facade
    "NarrativeStateGraph",
    # Emotional Arc
    "ArcShape",
    "Emotion",
    "ResolutionStyle",
    "EmotionalBeat",
    "EmotionalArc",
    "TensionProfile",
    "TensionAdjustment",
    "EmotionalArcPlanner",
    "TensionManager",
]