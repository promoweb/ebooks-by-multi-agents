"""
Context Assembler for Knowledge Base System.

This module assembles optimal context for generation by combining
retrieval results with narrative context and token budget optimization.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import re


logger = logging.getLogger("BookWriterAI")


class Priority(Enum):
    """Priority levels for context items."""
    CRITICAL = 0  # Must include (e.g., current chapter info)
    HIGH = 1      # Very important (e.g., recent events)
    MEDIUM = 2    # Important (e.g., character states)
    LOW = 3       # Nice to have (e.g., background info)


@dataclass
class ContextItem:
    """A single item in the assembled context."""
    content: str
    source: str
    priority: Priority
    token_count: int
    metadata: dict = field(default_factory=dict)
    
    def __lt__(self, other: "ContextItem") -> bool:
        """Compare by priority for sorting."""
        return self.priority.value < other.priority.value


@dataclass
class PriorityRule:
    """Rule for assigning priority to context items."""
    name: str
    condition: Callable[[ContextItem], bool]
    priority: Priority


@dataclass
class AssembledContext:
    """
    Assembled context ready for generation.
    
    Contains optimized context within token budget with
    proper formatting and prioritization.
    """
    items: List[ContextItem] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 4000
    formatted_context: str = ""
    sources: List[str] = field(default_factory=list)
    excluded_items: List[ContextItem] = field(default_factory=list)
    
    def to_prompt_string(self) -> str:
        """Format as string for LLM prompt."""
        if self.formatted_context:
            return self.formatted_context
        
        parts = []
        
        # Group by priority
        critical = [i for i in self.items if i.priority == Priority.CRITICAL]
        high = [i for i in self.items if i.priority == Priority.HIGH]
        medium = [i for i in self.items if i.priority == Priority.MEDIUM]
        low = [i for i in self.items if i.priority == Priority.LOW]
        
        if critical:
            parts.append("=== Essential Context ===")
            for item in critical:
                parts.append(item.content)
            parts.append("")
        
        if high:
            parts.append("=== Important Context ===")
            for item in high:
                parts.append(item.content)
            parts.append("")
        
        if medium:
            parts.append("=== Additional Context ===")
            for item in medium:
                parts.append(item.content)
            parts.append("")
        
        if low:
            parts.append("=== Background Information ===")
            for item in low:
                parts.append(item.content)
        
        return "\n".join(parts)


class ContextAssembler:
    """
    Assembles optimal context for generation.
    
    Features:
    - Token budget optimization
    - Priority-based selection
    - Deduplication
    - Proper formatting
    """
    
    # Approximate characters per token
    CHARS_PER_TOKEN = 4
    
    def __init__(
        self,
        max_tokens: int = 4000,
        priority_rules: Optional[List[PriorityRule]] = None
    ):
        """
        Initialize context assembler.
        
        Args:
            max_tokens: Maximum tokens for assembled context
            priority_rules: Custom priority rules
        """
        self.max_tokens = max_tokens
        self.priority_rules = priority_rules or self._default_priority_rules()
    
    def _default_priority_rules(self) -> List[PriorityRule]:
        """Get default priority rules."""
        return [
            PriorityRule(
                name="current_chapter",
                condition=lambda item: item.metadata.get("content_type") == "current_chapter",
                priority=Priority.CRITICAL
            ),
            PriorityRule(
                name="recent_events",
                condition=lambda item: item.metadata.get("content_type") == "recent_event",
                priority=Priority.HIGH
            ),
            PriorityRule(
                name="character_state",
                condition=lambda item: item.metadata.get("content_type") == "character_state",
                priority=Priority.HIGH
            ),
            PriorityRule(
                name="unresolved_threads",
                condition=lambda item: item.metadata.get("content_type") == "unresolved_thread",
                priority=Priority.MEDIUM
            ),
            PriorityRule(
                name="background",
                condition=lambda item: item.metadata.get("content_type") == "background",
                priority=Priority.LOW
            ),
        ]
    
    def assemble(
        self,
        retrieval_results: List[Any],
        narrative_context: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        additional_items: Optional[List[ContextItem]] = None
    ) -> AssembledContext:
        """
        Assemble context with token budget optimization.
        
        Args:
            retrieval_results: Results from vector search
            narrative_context: Narrative state context
            max_tokens: Override max tokens
            additional_items: Additional context items to include
        
        Returns:
            AssembledContext with optimized content
        """
        max_tokens = max_tokens or self.max_tokens
        
        # Convert retrieval results to context items
        items = self._convert_retrieval_results(retrieval_results)
        
        # Add narrative context items
        if narrative_context:
            narrative_items = self._extract_narrative_context(narrative_context)
            items.extend(narrative_items)
        
        # Add additional items
        if additional_items:
            items.extend(additional_items)
        
        # Assign priorities
        items = [self._assign_priority(item) for item in items]
        
        # Deduplicate
        items = self._deduplicate(items)
        
        # Sort by priority
        items.sort()
        
        # Select items within budget
        selected, excluded, total_tokens = self._select_within_budget(
            items, max_tokens
        )
        
        # Create assembled context
        assembled = AssembledContext(
            items=selected,
            total_tokens=total_tokens,
            max_tokens=max_tokens,
            sources=list(set(item.source for item in selected)),
            excluded_items=excluded
        )
        
        # Format context
        assembled.formatted_context = self._format_context(selected)
        
        return assembled
    
    def _convert_retrieval_results(
        self,
        results: List[Any]
    ) -> List[ContextItem]:
        """Convert retrieval results to context items."""
        items = []
        
        for result in results:
            # Handle different result types
            if hasattr(result, 'content'):
                content = result.content
                source = getattr(result, 'source', 'unknown')
                score = getattr(result, 'score', 0.0)
                metadata = getattr(result, 'metadata', {})
            elif isinstance(result, dict):
                content = result.get('content', '')
                source = result.get('source', 'unknown')
                score = result.get('score', 0.0)
                metadata = result.get('metadata', {})
            else:
                continue
            
            token_count = self._estimate_tokens(content)
            
            items.append(ContextItem(
                content=content,
                source=source,
                priority=Priority.MEDIUM,  # Default, will be reassigned
                token_count=token_count,
                metadata={
                    **metadata,
                    "relevance_score": score
                }
            ))
        
        return items
    
    def _extract_narrative_context(
        self,
        narrative_context: Any
    ) -> List[ContextItem]:
        """Extract context items from narrative state."""
        items = []
        
        # Handle NarrativeContext type
        if hasattr(narrative_context, 'relevant_events'):
            for event in narrative_context.relevant_events:
                content = getattr(event, 'description', str(event))
                items.append(ContextItem(
                    content=content,
                    source="narrative_events",
                    priority=Priority.HIGH,
                    token_count=self._estimate_tokens(content),
                    metadata={"content_type": "recent_event"}
                ))
        
        if hasattr(narrative_context, 'active_entities'):
            for entity in narrative_context.active_entities:
                content = self._format_entity_state(entity)
                items.append(ContextItem(
                    content=content,
                    source="narrative_entities",
                    priority=Priority.HIGH,
                    token_count=self._estimate_tokens(content),
                    metadata={"content_type": "character_state"}
                ))
        
        if hasattr(narrative_context, 'unresolved_threads'):
            for thread in narrative_context.unresolved_threads:
                content = str(thread)
                items.append(ContextItem(
                    content=content,
                    source="narrative_threads",
                    priority=Priority.MEDIUM,
                    token_count=self._estimate_tokens(content),
                    metadata={"content_type": "unresolved_thread"}
                ))
        
        # Handle dict type
        if isinstance(narrative_context, dict):
            if "events" in narrative_context:
                for event in narrative_context["events"]:
                    content = event.get('description', str(event))
                    items.append(ContextItem(
                        content=content,
                        source="narrative_events",
                        priority=Priority.HIGH,
                        token_count=self._estimate_tokens(content),
                        metadata={"content_type": "recent_event"}
                    ))
            
            if "entities" in narrative_context:
                for entity in narrative_context["entities"]:
                    content = self._format_entity_dict(entity)
                    items.append(ContextItem(
                        content=content,
                        source="narrative_entities",
                        priority=Priority.HIGH,
                        token_count=self._estimate_tokens(content),
                        metadata={"content_type": "character_state"}
                    ))
        
        return items
    
    def _format_entity_state(self, entity: Any) -> str:
        """Format entity state for context."""
        name = getattr(entity, 'name', 'Unknown')
        entity_type = getattr(entity, 'entity_type', 'entity')
        
        parts = [f"{name} ({entity_type})"]
        
        if hasattr(entity, 'attributes'):
            for key, value in entity.attributes.items():
                parts.append(f"  - {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_entity_dict(self, entity: dict) -> str:
        """Format entity dict for context."""
        name = entity.get('name', 'Unknown')
        entity_type = entity.get('entity_type', 'entity')
        
        parts = [f"{name} ({entity_type})"]
        
        if 'attributes' in entity:
            for key, value in entity['attributes'].items():
                parts.append(f"  - {key}: {value}")
        
        return "\n".join(parts)
    
    def _assign_priority(self, item: ContextItem) -> ContextItem:
        """Assign priority based on rules."""
        for rule in self.priority_rules:
            if rule.condition(item):
                item.priority = rule.priority
                break
        
        return item
    
    def _deduplicate(self, items: List[ContextItem]) -> List[ContextItem]:
        """Remove duplicate items."""
        seen_content = set()
        unique_items = []
        
        for item in items:
            # Normalize content for comparison
            normalized = self._normalize_content(item.content)
            
            if normalized not in seen_content:
                seen_content.add(normalized)
                unique_items.append(item)
        
        return unique_items
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for deduplication."""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        # Lowercase
        content = content.lower().strip()
        # Take first 100 chars for comparison
        return content[:100]
    
    def _select_within_budget(
        self,
        items: List[ContextItem],
        max_tokens: int
    ) -> tuple:
        """Select items within token budget."""
        selected = []
        excluded = []
        total_tokens = 0
        
        for item in items:
            if total_tokens + item.token_count <= max_tokens:
                selected.append(item)
                total_tokens += item.token_count
            else:
                excluded.append(item)
        
        return selected, excluded, total_tokens
    
    def _format_context(self, items: List[ContextItem]) -> str:
        """Format selected items into context string."""
        parts = []
        
        # Group by source
        sources: Dict[str, List[ContextItem]] = {}
        for item in items:
            if item.source not in sources:
                sources[item.source] = []
            sources[item.source].append(item)
        
        for source, source_items in sources.items():
            parts.append(f"=== {source.replace('_', ' ').title()} ===")
            for item in source_items:
                parts.append(item.content)
            parts.append("")
        
        return "\n".join(parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // self.CHARS_PER_TOKEN + 1


class ContextCompressor:
    """
    Compresses context while preserving essential information.
    
    Strategies:
    - Summarize: Create summary of long content
    - Extract: Extract key sentences
    - Hybrid: Combine both approaches
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize context compressor.
        
        Args:
            llm_client: LLM client for summarization (optional)
        """
        self.llm_client = llm_client
    
    def compress(
        self,
        context: str,
        target_tokens: int,
        strategy: str = "hybrid"
    ) -> str:
        """
        Compress context to fit token budget.
        
        Args:
            context: Context to compress
            target_tokens: Target token count
            strategy: Compression strategy (summarize, extract, hybrid)
        
        Returns:
            Compressed context
        """
        current_tokens = len(context) // 4
        
        if current_tokens <= target_tokens:
            return context
        
        if strategy == "summarize":
            return self._summarize(context, target_tokens)
        elif strategy == "extract":
            return self._extract(context, target_tokens)
        else:  # hybrid
            return self._hybrid_compress(context, target_tokens)
    
    def _summarize(
        self,
        context: str,
        target_tokens: int
    ) -> str:
        """Summarize context using LLM."""
        if not self.llm_client:
            return self._extract(context, target_tokens)
        
        try:
            prompt = f"""Summarize the following context concisely while preserving key information:

{context}

Provide a concise summary in approximately {target_tokens} tokens:"""
            
            summary = self.llm_client.generate(
                prompt,
                max_tokens=target_tokens + 100
            )
            
            return summary.strip()
        
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return self._extract(context, target_tokens)
    
    def _extract(
        self,
        context: str,
        target_tokens: int
    ) -> str:
        """Extract key sentences from context."""
        sentences = context.split('. ')
        
        # Score sentences by importance
        scored = []
        for sentence in sentences:
            score = self._score_sentence(sentence)
            scored.append((score, sentence))
        
        # Sort by score
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Select top sentences within budget
        selected = []
        current_tokens = 0
        
        for score, sentence in scored:
            sentence_tokens = len(sentence) // 4
            if current_tokens + sentence_tokens <= target_tokens:
                selected.append(sentence)
                current_tokens += sentence_tokens
        
        # Reorder by original position
        selected.sort(key=lambda s: context.find(s))
        
        return '. '.join(selected)
    
    def _hybrid_compress(
        self,
        context: str,
        target_tokens: int
    ) -> str:
        """Combine extraction and summarization."""
        # First extract key content
        extracted = self._extract(context, target_tokens * 2)
        
        # Then summarize if still too long
        if len(extracted) // 4 > target_tokens:
            return self._summarize(extracted, target_tokens)
        
        return extracted
    
    def _score_sentence(self, sentence: str) -> float:
        """Score sentence importance."""
        score = 0.0
        
        # Length bonus (not too short, not too long)
        length = len(sentence)
        if 50 < length < 200:
            score += 1.0
        elif 20 < length < 300:
            score += 0.5
        
        # Keyword bonus
        important_words = [
            'character', 'plot', 'conflict', 'resolution',
            'protagonist', 'antagonist', 'climax', 'turning',
            'important', 'key', 'critical', 'major'
        ]
        
        sentence_lower = sentence.lower()
        for word in important_words:
            if word in sentence_lower:
                score += 0.5
        
        # Entity mention bonus (capitalized words)
        capitals = sum(1 for c in sentence if c.isupper())
        score += min(capitals * 0.1, 1.0)
        
        return score


__all__ = [
    "Priority",
    "ContextItem",
    "PriorityRule",
    "AssembledContext",
    "ContextAssembler",
    "ContextCompressor",
]