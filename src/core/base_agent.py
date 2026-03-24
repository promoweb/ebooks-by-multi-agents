"""
Base Agent for BookWriterAI.

This module provides the base class for all specialized agents in the system,
with integrated LLM client, knowledge base access, and narrative memory support.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from src.core.config import Config
from src.core.llm_client import BaseLLMClient, LLMClientFactory, LLMResponse

if TYPE_CHECKING:
    from src.knowledge.base import KnowledgeBase
    from src.narrative.state_graph import NarrativeStateGraph


logger = logging.getLogger("BookWriterAI")


class BaseAgent(ABC):
    """
    Base class for all specialized agents.
    
    Provides:
    - LLM client access
    - Knowledge base integration
    - Narrative memory access
    - Logging and error handling
    """
    
    def __init__(
        self,
        config: Config,
        name: str,
        knowledge_base: Optional["KnowledgeBase"] = None,
        narrative_memory: Optional["NarrativeStateGraph"] = None
    ):
        """
        Initialize the agent.
        
        Args:
            config: Master configuration
            name: Agent name for logging
            knowledge_base: Optional knowledge base for context retrieval
            narrative_memory: Optional narrative memory for consistency
        """
        self.config = config
        self.name = name
        self.knowledge_base = knowledge_base
        self.narrative_memory = narrative_memory
        
        # Initialize LLM client
        self._llm_client: Optional[BaseLLMClient] = None
        
        # Track usage
        self._total_tokens_used = 0
        self._total_calls = 0
    
    @property
    def llm_client(self) -> BaseLLMClient:
        """Lazy initialization of LLM client."""
        if self._llm_client is None:
            self._llm_client = LLMClientFactory.create(self.config.llm)
        return self._llm_client
    
    def call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Make a call to the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Generated text content
        """
        logger.debug(f"[{self.name}] Calling LLM with prompt length: {len(prompt)}")
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens or self.config.llm.max_tokens_per_call,
            temperature=temperature if temperature is not None else self.config.llm.temperature,
            **kwargs
        )
        
        # Track usage
        self._total_tokens_used += response.usage.get("total_tokens", 0)
        self._total_calls += 1
        
        logger.debug(f"[{self.name}] LLM response: {len(response.content)} chars, "
                    f"{response.usage.get('total_tokens', 0)} tokens")
        
        return response.content
    
    def call_ai_with_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Make a call to the LLM and return full response.
        
        Same as call_ai but returns the full LLMResponse object
        with usage information.
        """
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens or self.config.llm.max_tokens_per_call,
            temperature=temperature if temperature is not None else self.config.llm.temperature,
            **kwargs
        )
        
        # Track usage
        self._total_tokens_used += response.usage.get("total_tokens", 0)
        self._total_calls += 1
        
        return response
    
    def get_context_for_query(self, query: str, max_chunks: Optional[int] = None) -> str:
        """
        Retrieve relevant context from knowledge base.
        
        Args:
            query: Search query
            max_chunks: Maximum number of chunks to retrieve
            
        Returns:
            Formatted context string
        """
        if not self.knowledge_base or not self.knowledge_base.is_loaded():
            return ""
        
        return self.knowledge_base.get_relevant_context(
            query, 
            top_k=max_chunks or self.config.knowledge_base.max_context_chunks
        )
    
    def get_narrative_context(self, chapter_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get narrative context from memory.
        
        Args:
            chapter_id: Optional chapter ID for chapter-specific context
            
        Returns:
            Narrative context dictionary
        """
        if not self.narrative_memory or not self.config.narrative_memory.enabled:
            return {}
        
        if chapter_id is not None:
            return self.narrative_memory.get_context_for_chapter(chapter_id)
        
        return self.narrative_memory.get_current_context()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the LLM client's tokenizer."""
        return self.llm_client.count_tokens(text)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics for this agent."""
        return {
            "name": self.name,
            "total_tokens": self._total_tokens_used,
            "total_calls": self._total_calls,
            "avg_tokens_per_call": self._total_tokens_used / max(1, self._total_calls)
        }
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's primary function.
        
        This method must be implemented by all subclasses.
        """
        pass


class AgentRegistry:
    """Registry for managing agents."""
    
    _agents: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """Register an agent."""
        cls._agents[agent.name] = agent
        logger.debug(f"Registered agent: {agent.name}")
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return cls._agents.get(name)
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get usage stats for all registered agents."""
        return {name: agent.get_usage_stats() for name, agent in cls._agents.items()}
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents."""
        cls._agents.clear()


# =============================================================================
# Specialized Agent Mixins
# =============================================================================

class KnowledgeAwareMixin:
    """Mixin for agents that heavily use knowledge base."""
    
    def enrich_prompt_with_context(
        self,
        prompt: str,
        query: str,
        max_context_tokens: int = 2000
    ) -> str:
        """
        Enrich a prompt with knowledge base context.
        
        Args:
            prompt: Original prompt
            query: Query for context retrieval
            max_context_tokens: Maximum tokens for context
            
        Returns:
            Enriched prompt
        """
        if not hasattr(self, 'knowledge_base') or not self.knowledge_base:
            return prompt
        
        context = self.get_context_for_query(query)
        
        if not context:
            return prompt
        
        # Check token budget
        context_tokens = self.count_tokens(context)
        if context_tokens > max_context_tokens:
            # Truncate context
            ratio = max_context_tokens / context_tokens
            truncate_chars = int(len(context) * ratio)
            context = context[:truncate_chars] + "\n[...truncated...]"
        
        return f"{prompt}\n\n=== CONTESTO DI RIFERIMENTO ===\n{context}\n=== FINE CONTESTO ===\n"


class NarrativeAwareMixin:
    """Mixin for agents that need narrative consistency."""
    
    def get_character_context(self, character_ids: List[str]) -> str:
        """Get context about specific characters."""
        if not hasattr(self, 'narrative_memory') or not self.narrative_memory:
            return ""
        
        context_parts = []
        for char_id in character_ids:
            entity = self.narrative_memory.entities.get_entity(char_id)
            if entity:
                context_parts.append(f"- {entity.name}: {entity.attributes}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def get_recent_events(self, n: int = 10) -> str:
        """Get summary of recent events."""
        if not hasattr(self, 'narrative_memory') or not self.narrative_memory:
            return ""
        
        events = self.narrative_memory.events.get_recent_events(n)
        if not events:
            return ""
        
        return "\n".join(f"- {e.description}" for e in events)
    
    def get_unresolved_threads(self) -> List[str]:
        """Get list of unresolved plot threads."""
        if not hasattr(self, 'narrative_memory') or not self.narrative_memory:
            return []
        
        unresolved = self.narrative_memory.events.get_unresolved_events()
        return [e.description for e in unresolved]


class StyleAwareMixin:
    """Mixin for agents that need style consistency."""
    
    def get_style_instructions(self) -> str:
        """Get style instructions for generation."""
        if not hasattr(self, 'config'):
            return ""
        
        style_config = self.config.style
        if not style_config.enabled:
            return ""
        
        instructions = []
        
        if style_config.narrative_voice:
            voice_map = {
                "first_person": "Write in first-person perspective",
                "third_limited": "Write in third-person limited perspective",
                "third_omniscient": "Write in third-person omniscient perspective"
            }
            instructions.append(voice_map.get(style_config.narrative_voice, ""))
        
        if style_config.primary_tone:
            instructions.append(f"Maintain a {style_config.primary_tone} tone")
        
        if style_config.vocabulary_level:
            vocab_map = {
                "simple": "Use simple, accessible vocabulary",
                "moderate": "Use moderate vocabulary suitable for general readers",
                "sophisticated": "Use sophisticated, literary vocabulary"
            }
            instructions.append(vocab_map.get(style_config.vocabulary_level, ""))
        
        return "\n".join(i for i in instructions if i)