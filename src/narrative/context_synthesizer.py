"""
Context Synthesizer for Long-Term Narrative Memory System.

This module provides the ContextSynthesizer for generating relevant context
for chapter generation by combining events, entities, and relations.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field

from src.core.config import NarrativeMemoryConfig
from src.core.llm_client import count_tokens
from src.narrative.events import EventsStore, NarrativeEvent
from src.narrative.entities import EntityRegistry, Entity
from src.narrative.relations import RelationsGraph, Relation


logger = logging.getLogger("BookWriterAI")


@dataclass
class NarrativeContext:
    """
    Synthesized narrative context for chapter generation.
    
    Contains all relevant information needed to maintain consistency
    and coherence when generating a new chapter.
    """
    # Relevant events that should be referenced
    relevant_events: List[NarrativeEvent] = field(default_factory=list)
    
    # Current state of involved entities
    active_entities: List[Entity] = field(default_factory=list)
    
    # Current relationship states
    active_relations: List[Relation] = field(default_factory=list)
    
    # Plot threads that need attention
    unresolved_threads: List[NarrativeEvent] = field(default_factory=list)
    
    # Timeline context
    timeline_context: Dict[str, Any] = field(default_factory=dict)
    
    # Foreshadowing opportunities
    foreshadowing_opportunities: List[NarrativeEvent] = field(default_factory=list)
    
    # Formatted context string
    formatted_context: str = ""
    
    # Token count
    token_count: int = 0
    
    def to_prompt_section(self) -> str:
        """Convert to a formatted prompt section."""
        if self.formatted_context:
            return self.formatted_context
        
        parts = []
        
        if self.relevant_events:
            parts.append("=== RECENT EVENTS ===")
            for event in self.relevant_events[-5:]:  # Last 5 events
                parts.append(f"- Ch.{event.chapter_id}: {event.description}")
            parts.append("")
        
        if self.active_entities:
            parts.append("=== ACTIVE CHARACTERS ===")
            for entity in self.active_entities[:10]:  # Top 10
                state = entity.get_current_state()
                state_str = ""
                if state:
                    state_str = f" | {state.attributes}"
                parts.append(f"- {entity.name}{state_str}")
            parts.append("")
        
        if self.active_relations:
            parts.append("=== KEY RELATIONSHIPS ===")
            for rel in self.active_relations[:10]:
                parts.append(f"- {rel.source_entity} -> {rel.target_entity}: "
                           f"{rel.relation_type} (strength: {rel.strength:.1f})")
            parts.append("")
        
        if self.unresolved_threads:
            parts.append("=== UNRESOLVED PLOT THREADS ===")
            for thread in self.unresolved_threads[:5]:
                parts.append(f"- {thread.description}")
            parts.append("")
        
        if self.foreshadowing_opportunities:
            parts.append("=== FORESHADOWING OPPORTUNITIES ===")
            for event in self.foreshadowing_opportunities[:3]:
                parts.append(f"- Consider foreshadowing: {event.description}")
            parts.append("")
        
        return "\n".join(parts)


class ContextSynthesizer:
    """
    Synthesizes relevant context for chapter generation.
    
    Implements relevance scoring and context window optimization
    to provide the most useful context within token limits.
    """
    
    def __init__(
        self,
        events_store: EventsStore,
        entity_registry: EntityRegistry,
        relations_graph: RelationsGraph,
        config: NarrativeMemoryConfig
    ):
        """
        Initialize the context synthesizer.
        
        Args:
            events_store: Events storage
            entity_registry: Entity registry
            relations_graph: Relations graph
            config: Narrative memory configuration
        """
        self.events = events_store
        self.entities = entity_registry
        self.relations = relations_graph
        self.config = config
    
    def synthesize_context(
        self,
        current_chapter: int,
        chapter_info: Dict[str, Any],
        max_tokens: int
    ) -> NarrativeContext:
        """
        Produce optimized context for generation.
        
        Args:
            current_chapter: The chapter being generated
            chapter_info: Information about the chapter (title, description, etc.)
            max_tokens: Maximum tokens for context
            
        Returns:
            NarrativeContext with relevant information
        """
        context = NarrativeContext()
        
        # 1. Get relevant events
        context.relevant_events = self._get_relevant_events(current_chapter, chapter_info)
        
        # 2. Get active entities
        context.active_entities = self._get_active_entities(current_chapter, chapter_info)
        
        # 3. Get active relations
        context.active_relations = self._get_active_relations(context.active_entities)
        
        # 4. Get unresolved threads
        context.unresolved_threads = self._get_unresolved_threads(current_chapter)
        
        # 5. Get timeline context
        context.timeline_context = self._get_timeline_context(current_chapter)
        
        # 6. Get foreshadowing opportunities
        if self.config.enable_foreshadowing_tracking:
            context.foreshadowing_opportunities = self._get_foreshadowing_opportunities(current_chapter)
        
        # 7. Format and optimize for token budget
        context.formatted_context = self._format_context(context, max_tokens)
        context.token_count = count_tokens(context.formatted_context)
        
        logger.debug(f"Synthesized context for chapter {current_chapter}: "
                    f"{context.token_count} tokens")
        
        return context
    
    def _get_relevant_events(
        self, 
        current_chapter: int, 
        chapter_info: Dict[str, Any]
    ) -> List[NarrativeEvent]:
        """Get events relevant to the current chapter."""
        # Get events from recent chapters
        lookback = min(3, current_chapter)
        start_chapter = max(1, current_chapter - lookback)
        
        events = self.events.get_events_in_range(start_chapter, current_chapter - 1)
        
        # Score events by relevance
        scored_events = []
        chapter_keywords = self._extract_keywords(chapter_info)
        
        for event in events:
            score = self._score_event_relevance(event, chapter_keywords, current_chapter)
            scored_events.append((score, event))
        
        # Sort by score and return
        scored_events.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored_events[:self.config.max_events_per_chapter]]
    
    def _get_active_entities(
        self, 
        current_chapter: int,
        chapter_info: Dict[str, Any]
    ) -> List[Entity]:
        """Get entities that should be active in the current chapter."""
        entities = []
        
        # Get entities from recent chapters
        lookback = min(5, current_chapter)
        for ch in range(max(1, current_chapter - lookback), current_chapter):
            chapter_entities = self.entities.get_entities_in_chapter(ch)
            for entity in chapter_entities:
                if entity not in entities:
                    entities.append(entity)
        
        # Get entities mentioned in chapter info
        mentioned_names = self._extract_entity_names(chapter_info)
        for name in mentioned_names:
            entity = self.entities.get_entity_by_name(name)
            if entity and entity not in entities:
                entities.append(entity)
        
        # Sort by importance
        entities.sort(key=lambda e: e.importance, reverse=True)
        
        return entities[:self.config.max_entities]
    
    def _get_active_relations(self, active_entities: List[Entity]) -> List[Relation]:
        """Get relations between active entities."""
        relations = []
        entity_ids = {e.entity_id for e in active_entities}
        
        for entity in active_entities:
            entity_relations = self.relations.get_relations(entity.entity_id)
            for rel in entity_relations:
                # Only include relations between active entities
                other_id = (rel.target_entity if rel.source_entity == entity.entity_id 
                           else rel.source_entity)
                if other_id in entity_ids and rel not in relations:
                    relations.append(rel)
        
        # Sort by strength
        relations.sort(key=lambda r: r.strength, reverse=True)
        
        return relations[:self.config.max_relations]
    
    def _get_unresolved_threads(self, current_chapter: int) -> List[NarrativeEvent]:
        """Get unresolved plot threads that should be addressed."""
        unresolved = self.events.get_unresolved_events()
        
        # Filter out threads that are too old or not relevant
        relevant_threads = []
        for thread in unresolved:
            # Include if recent or high importance
            if (thread.chapter_id >= current_chapter - 10 or 
                thread.importance_weight >= 0.7):
                relevant_threads.append(thread)
        
        return relevant_threads
    
    def _get_timeline_context(self, current_chapter: int) -> Dict[str, Any]:
        """Get timeline-related context."""
        # Get events that establish timeline
        timeline_events = self.events.get_events_by_type("milestone")
        
        return {
            "current_chapter": current_chapter,
            "milestones": [
                {"chapter": e.chapter_id, "description": e.description}
                for e in timeline_events[:5]
            ]
        }
    
    def _get_foreshadowing_opportunities(
        self, 
        current_chapter: int
    ) -> List[NarrativeEvent]:
        """Get opportunities for foreshadowing future events."""
        # Get important future events that could be foreshadowed
        opportunities = self.events.get_foreshadowing_opportunities()
        
        # Filter to events in future chapters
        future_opportunities = [
            e for e in opportunities 
            if e.chapter_id > current_chapter
        ]
        
        return future_opportunities[:3]
    
    def _score_event_relevance(
        self, 
        event: NarrativeEvent, 
        chapter_keywords: Set[str],
        current_chapter: int
    ) -> float:
        """Score an event's relevance to the current chapter."""
        score = 0.0
        
        # Recency bonus
        recency = current_chapter - event.chapter_id
        score += max(0, 1.0 - recency * 0.1)
        
        # Importance weight
        score += event.importance_weight * 0.5
        
        # Keyword overlap
        event_words = set(event.description.lower().split())
        keyword_overlap = len(event_words & chapter_keywords)
        score += keyword_overlap * 0.1
        
        # Unresolved bonus
        if not event.is_resolved():
            score += 0.3
        
        return score
    
    def _extract_keywords(self, chapter_info: Dict[str, Any]) -> Set[str]:
        """Extract keywords from chapter info."""
        keywords = set()
        
        title = chapter_info.get("title", "")
        description = chapter_info.get("description", "")
        
        # Simple keyword extraction
        text = f"{title} {description}".lower()
        words = text.split()
        
        # Filter to meaningful words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        keywords = {w for w in words if len(w) > 3 and w not in stop_words}
        
        return keywords
    
    def _extract_entity_names(self, chapter_info: Dict[str, Any]) -> Set[str]:
        """Extract entity names from chapter info."""
        names = set()
        
        # Check for explicit character mentions
        characters = chapter_info.get("characters", [])
        if characters:
            names.update(characters)
        
        # Check description for capitalized names
        description = chapter_info.get("description", "")
        import re
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', description)
        names.update(capitalized)
        
        return names
    
    def _format_context(
        self, 
        context: NarrativeContext, 
        max_tokens: int
    ) -> str:
        """Format context within token budget."""
        # Start with full context
        formatted = context.to_prompt_section()
        token_count = count_tokens(formatted)
        
        if token_count <= max_tokens:
            return formatted
        
        # Need to truncate - prioritize sections
        sections = []
        remaining_tokens = max_tokens
        
        # Always include unresolved threads (most important for consistency)
        if context.unresolved_threads:
            section = "=== UNRESOLVED PLOT THREADS ===\n"
            for thread in context.unresolved_threads[:3]:
                section += f"- {thread.description}\n"
            section += "\n"
            section_tokens = count_tokens(section)
            if section_tokens <= remaining_tokens:
                sections.append(section)
                remaining_tokens -= section_tokens
        
        # Include recent events
        if context.relevant_events and remaining_tokens > 100:
            section = "=== RECENT EVENTS ===\n"
            for event in context.relevant_events[:5]:
                section += f"- Ch.{event.chapter_id}: {event.description}\n"
            section += "\n"
            section_tokens = count_tokens(section)
            if section_tokens <= remaining_tokens:
                sections.append(section)
                remaining_tokens -= section_tokens
        
        # Include active entities
        if context.active_entities and remaining_tokens > 100:
            section = "=== ACTIVE CHARACTERS ===\n"
            for entity in context.active_entities[:5]:
                section += f"- {entity.name}\n"
            section += "\n"
            section_tokens = count_tokens(section)
            if section_tokens <= remaining_tokens:
                sections.append(section)
                remaining_tokens -= section_tokens
        
        # Include key relationships
        if context.active_relations and remaining_tokens > 100:
            section = "=== KEY RELATIONSHIPS ===\n"
            for rel in context.active_relations[:5]:
                section += f"- {rel.source_entity} <-> {rel.target_entity}: {rel.relation_type}\n"
            section += "\n"
            section_tokens = count_tokens(section)
            if section_tokens <= remaining_tokens:
                sections.append(section)
                remaining_tokens -= section_tokens
        
        return "\n".join(sections)
    
    def get_context_for_chapter(
        self, 
        chapter_id: int,
        max_tokens: Optional[int] = None
    ) -> NarrativeContext:
        """
        Get context specifically for chapter generation.
        
        Convenience method that synthesizes context with default settings.
        """
        max_tokens = max_tokens or self.config.context_synthesis_tokens
        return self.synthesize_context(chapter_id, {}, max_tokens)
    
    def get_summary(self, chapter_id: int) -> str:
        """Get a brief summary of narrative state at a chapter."""
        events = self.events.get_events_by_chapter(chapter_id)
        entities = self.entities.get_entities_in_chapter(chapter_id)
        
        summary_parts = [f"Chapter {chapter_id} Summary:"]
        
        if events:
            summary_parts.append(f"Events: {len(events)}")
            for event in events[:3]:
                summary_parts.append(f"  - {event.event_type}: {event.description[:50]}...")
        
        if entities:
            summary_parts.append(f"Entities: {', '.join(e.name for e in entities[:5])}")
        
        return "\n".join(summary_parts)