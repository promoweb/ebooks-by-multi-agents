"""
Configuration management for BookWriterAI.

This module provides comprehensive configuration for all aspects of book generation,
including LLM settings, content generation parameters, quality thresholds,
and feature flags for the new architectural components.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

from src.core.exceptions import (
    ConfigurationError, 
    MissingAPIKeyError, 
    InvalidProviderError
)


# Load environment variables
load_dotenv()


class Provider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    BAILIAN = "bailian"
    QWEN = "qwen"
    CUSTOM = "custom"


class ContentType(Enum):
    """Types of content that can be generated."""
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    TECHNICAL = "technical"
    ACADEMIC = "academic"


class OutputFormat(Enum):
    """Supported output formats."""
    MARKDOWN = "markdown"
    EPUB = "epub"
    PDF = "pdf"
    DOCX = "docx"


# =============================================================================
# Provider Configuration
# =============================================================================

PROVIDER_CONFIGS = {
    Provider.OPENAI: {
        "default_model": "gpt-4",
        "base_url": None,
        "env_var": "OPENAI_API_KEY",
    },
    Provider.BAILIAN: {
        "default_model": "qwen3.5-plus",
        "base_url": "https://coding-intl.dashscope.aliyuncs.com/v1",
        "env_var": "BAILIAN_API_KEY",
        "fallback_env_var": "DASHSCOPE_API_KEY",
    },
    Provider.QWEN: {
        "default_model": "qwen-max",
        "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        "env_var": "DASHSCOPE_API_KEY",
    },
}

# Model context windows for token budgeting
MODEL_CONTEXT_WINDOWS = {
    # Qwen/Bailian models
    "qwen3.5-plus": 1_000_000,
    "qwen3-coder-plus": 1_000_000,
    "qwen3-max-2026-01-23": 262_144,
    "qwen3-coder-next": 262_144,
    "kimi-k2.5": 262_144,
    "MiniMax-M2.5": 196_608,
    "glm-5": 202_752,
    "glm-4.7": 202_752,
    # OpenAI models
    "gpt-4": 8_192,
    "gpt-4-turbo": 128_000,
    "gpt-4-turbo-preview": 128_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-3.5-turbo": 16_384,
    # Legacy
    "qwen-max": 8_192,
}


# =============================================================================
# Configuration Dataclasses
# =============================================================================

@dataclass
class LLMConfig:
    """Configuration for LLM interactions."""
    provider: Provider = Provider.OPENAI
    model: str = "gpt-4"
    api_key: str = ""
    endpoint: Optional[str] = None  # Custom base URL
    temperature: float = 0.7
    max_tokens_per_call: int = 2000
    max_retries: int = 3
    retry_delay: float = 2.0  # Exponential backoff base
    
    def __post_init__(self):
        """Validate and set up LLM configuration."""
        # Resolve API key from environment if not provided
        if not self.api_key:
            self.api_key = self._resolve_api_key()
        
        if not self.api_key:
            env_var = PROVIDER_CONFIGS.get(self.provider, {}).get("env_var", "API_KEY")
            raise MissingAPIKeyError(self.provider.value, env_var)
    
    def _resolve_api_key(self) -> str:
        """Resolve API key from environment variables."""
        if self.provider == Provider.OPENAI:
            return os.getenv("OPENAI_API_KEY", "")
        elif self.provider == Provider.BAILIAN:
            return os.getenv("BAILIAN_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")
        elif self.provider == Provider.QWEN:
            return os.getenv("DASHSCOPE_API_KEY", "")
        elif self.provider == Provider.CUSTOM:
            return os.getenv("CUSTOM_API_KEY", "")
        return ""
    
    def get_base_url(self) -> Optional[str]:
        """Get the base URL for the provider."""
        if self.endpoint:
            return self.endpoint
        return PROVIDER_CONFIGS.get(self.provider, {}).get("base_url")
    
    def get_context_window(self) -> int:
        """Get the context window size for the current model."""
        return MODEL_CONTEXT_WINDOWS.get(self.model, 8_192)


@dataclass
class BookConfig:
    """Configuration for book structure and content."""
    title: str = "Untitled Book"
    topic: str = "Intelligenza artificiale e futuro del lavoro"
    genre: str = "non_fiction"
    subgenre: Optional[str] = None
    content_type: ContentType = ContentType.NON_FICTION
    target_pages: int = 400
    target_audience: str = "general"
    num_chapters: int = 20
    words_per_page: int = 400
    words_per_chapter: int = 8000
    
    def __post_init__(self):
        """Calculate derived values."""
        # Auto-calculate words_per_chapter if not set
        if self.words_per_chapter == 8000:  # Default value
            total_words = self.target_pages * self.words_per_page
            self.words_per_chapter = total_words // max(self.num_chapters, 1)
        
        # Ensure minimum chapters
        min_chapters = max(10, self.target_pages // 40)
        if self.num_chapters < min_chapters:
            self.num_chapters = min_chapters


@dataclass
class ContentGenerationConfig:
    """Configuration for content generation process."""
    # Multi-layered content expansion
    min_chapter_words: int = 6000
    chapter_density_threshold: float = 0.8
    enable_recursive_sections: bool = True
    enable_content_validation: bool = True
    enable_progressive_outline: bool = True
    max_section_depth: int = 3
    enable_adaptive_token_budget: bool = True
    
    # Hard limits for generation control
    section_token_limit_multiplier: float = 1.3
    section_token_interrupt_threshold: float = 1.1
    section_timeout_seconds: int = 180
    max_overgeneration_threshold: float = 1.2
    enable_section_checkpointing: bool = True
    
    # Validation settings
    max_regeneration_attempts: int = 3
    compensatory_content_threshold: int = 245  # Minimum pages


@dataclass
class KnowledgeBaseConfig:
    """Configuration for RAG/Knowledge Base system."""
    context_path: Optional[str] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_context_chunks: int = 5
    use_semantic_retrieval: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    cache_dir: str = "checkpoints/kb_cache"


@dataclass
class NarrativeMemoryConfig:
    """Configuration for Long-Term Narrative Memory System."""
    enabled: bool = True
    persistence_path: str = "checkpoints/narrative_memory.db"
    max_events_per_chapter: int = 50
    max_entities: int = 1000
    max_relations: int = 2000
    context_synthesis_tokens: int = 2000
    enable_auto_extraction: bool = True
    enable_foreshadowing_tracking: bool = True


@dataclass
class CharacterConfig:
    """Configuration for Character Development Framework."""
    enabled: bool = True
    max_characters: int = 100
    enable_arc_tracking: bool = True
    enable_dialogue_style_matching: bool = True
    enable_consistency_validation: bool = True
    character_context_tokens: int = 500


@dataclass
class StyleConfig:
    """Configuration for Stylistic Consistency Engine."""
    enabled: bool = True
    profile_name: Optional[str] = None
    narrative_voice: str = "third_limited"  # first_person, third_limited, third_omniscient
    primary_tone: str = "professional"
    vocabulary_level: str = "moderate"  # simple, moderate, sophisticated
    figurative_language_density: float = 0.5
    enable_style_validation: bool = True
    enable_style_correction: bool = True
    style_tolerance: float = 0.15


@dataclass
class QualityConfig:
    """Configuration for Quality Assurance."""
    enabled: bool = True
    enable_iterative_refinement: bool = True
    max_refinement_iterations: int = 3
    quality_threshold: float = 0.85
    convergence_threshold: float = 0.02
    enable_fact_checking: bool = False
    enable_consistency_checking: bool = True


@dataclass
class EmotionalArcConfig:
    """Configuration for Emotional Arc Planning."""
    enabled: bool = True
    arc_type: str = "rags_to_riches"  # rags_to_riches, tragedy, man_in_hole, icarus, cinderella, oedipus
    enable_tension_management: bool = True
    tension_check_frequency: int = 5  # Check every N paragraphs


@dataclass
class GenreTemplateConfig:
    """Configuration for Genre-Specific Templates."""
    enabled: bool = True
    enforce_conventions: bool = True
    custom_template_path: Optional[str] = None


@dataclass
class ScientificConfig:
    """Configuration for Scientific/Technical Content Support."""
    enabled: bool = False
    citation_style: str = "apa"  # apa, mla, chicago, ieee, harvard
    required_citations_per_section: int = 3
    technical_depth: str = "intermediate"  # introductory, intermediate, advanced, expert
    include_exercises: bool = False
    include_case_studies: bool = True
    include_examples: bool = True
    enable_fact_verification: bool = True


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    output_file: str = "book_output.md"
    output_format: OutputFormat = OutputFormat.MARKDOWN
    checkpoint_dir: str = "checkpoints"
    include_front_matter: bool = True
    include_back_matter: bool = True
    include_table_of_contents: bool = True
    include_bibliography: bool = False
    include_index: bool = False
    include_glossary: bool = False


@dataclass
class Config:
    """
    Master configuration for BookWriterAI.
    
    This class aggregates all configuration sections and provides
    a unified interface for configuration management.
    """
    # Core configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    book: BookConfig = field(default_factory=BookConfig)
    content: ContentGenerationConfig = field(default_factory=ContentGenerationConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # New architectural components
    narrative_memory: NarrativeMemoryConfig = field(default_factory=NarrativeMemoryConfig)
    character: CharacterConfig = field(default_factory=CharacterConfig)
    style: StyleConfig = field(default_factory=StyleConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    emotional_arc: EmotionalArcConfig = field(default_factory=EmotionalArcConfig)
    genre_template: GenreTemplateConfig = field(default_factory=GenreTemplateConfig)
    scientific: ScientificConfig = field(default_factory=ScientificConfig)
    
    # Legacy compatibility fields (for backward compatibility with ebooks.py)
    # These map to the new structured config
    topic: str = field(default="")
    output_file: str = field(default="")
    checkpoint_dir: str = field(default="")
    context_path: Optional[str] = field(default=None)
    provider: str = field(default="")
    model: str = field(default="")
    api_key: str = field(default="")
    endpoint: Optional[str] = field(default=None)
    temperature: float = field(default=0.7)
    max_tokens_per_call: int = field(default=2000)
    words_per_page: int = field(default=400)
    target_pages: int = field(default=400)
    num_chapters: int = field(default=20)
    words_per_chapter: int = field(default=8000)
    chunk_size: int = field(default=1000)
    chunk_overlap: int = field(default=200)
    max_context_chunks: int = field(default=5)
    use_semantic_retrieval: bool = field(default=True)
    min_chapter_words: int = field(default=6000)
    chapter_density_threshold: float = field(default=0.8)
    enable_recursive_sections: bool = field(default=True)
    enable_content_validation: bool = field(default=True)
    enable_progressive_outline: bool = field(default=True)
    compensatory_content_threshold: int = field(default=245)
    max_section_depth: int = field(default=3)
    enable_adaptive_token_budget: bool = field(default=True)
    section_token_limit_multiplier: float = field(default=1.3)
    section_token_interrupt_threshold: float = field(default=1.1)
    section_timeout_seconds: int = field(default=180)
    max_overgeneration_threshold: float = field(default=1.2)
    enable_section_checkpointing: bool = field(default=True)
    
    def __post_init__(self):
        """Synchronize legacy fields with structured config and validate."""
        # Sync legacy fields to structured config
        self._sync_legacy_to_structured()
        
        # Validate configuration
        self._validate()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _sync_legacy_to_structured(self):
        """Synchronize legacy flat fields to structured configuration."""
        # LLM config
        if self.provider:
            try:
                self.llm.provider = Provider(self.provider)
            except ValueError:
                valid = [p.value for p in Provider]
                raise InvalidProviderError(self.provider, valid)
        if self.model:
            self.llm.model = self.model
        if self.api_key:
            self.llm.api_key = self.api_key
        if self.endpoint:
            self.llm.endpoint = self.endpoint
        if self.temperature != 0.7:
            self.llm.temperature = self.temperature
        if self.max_tokens_per_call != 2000:
            self.llm.max_tokens_per_call = self.max_tokens_per_call
        
        # Book config
        if self.topic:
            self.book.topic = self.topic
        if self.target_pages != 400:
            self.book.target_pages = self.target_pages
        if self.num_chapters != 20:
            self.book.num_chapters = self.num_chapters
        if self.words_per_page != 400:
            self.book.words_per_page = self.words_per_page
        if self.words_per_chapter != 8000:
            self.book.words_per_chapter = self.words_per_chapter
        
        # Output config
        if self.output_file:
            self.output.output_file = self.output_file
        if self.checkpoint_dir:
            self.output.checkpoint_dir = self.checkpoint_dir
        
        # Knowledge base config
        if self.context_path:
            self.knowledge_base.context_path = self.context_path
        if self.chunk_size != 1000:
            self.knowledge_base.chunk_size = self.chunk_size
        if self.chunk_overlap != 200:
            self.knowledge_base.chunk_overlap = self.chunk_overlap
        if self.max_context_chunks != 5:
            self.knowledge_base.max_context_chunks = self.max_context_chunks
        
        # Content generation config
        if self.min_chapter_words != 6000:
            self.content.min_chapter_words = self.min_chapter_words
        if self.chapter_density_threshold != 0.8:
            self.content.chapter_density_threshold = self.chapter_density_threshold
    
    def _validate(self):
        """Validate configuration values."""
        # Validate temperature range
        if not 0 <= self.llm.temperature <= 2:
            raise ConfigurationError(
                "Temperature must be between 0 and 2",
                {"temperature": self.llm.temperature}
            )
        
        # Validate target pages
        if self.book.target_pages < 50:
            raise ConfigurationError(
                "Target pages must be at least 50",
                {"target_pages": self.book.target_pages}
            )
        
        # Validate chapter density threshold
        if not 0 < self.content.chapter_density_threshold <= 1:
            raise ConfigurationError(
                "Chapter density threshold must be between 0 and 1",
                {"chapter_density_threshold": self.content.chapter_density_threshold}
            )
        
        # Validate quality threshold
        if not 0 < self.quality.quality_threshold <= 1:
            raise ConfigurationError(
                "Quality threshold must be between 0 and 1",
                {"quality_threshold": self.quality.quality_threshold}
            )
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        Path(self.output.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        Path(self.knowledge_base.cache_dir).mkdir(parents=True, exist_ok=True)
        
        if self.narrative_memory.enabled:
            Path(self.narrative_memory.persistence_path).parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def from_args(cls, args) -> "Config":
        """Create configuration from argparse Namespace."""
        return cls(
            topic=getattr(args, 'topic', ''),
            output_file=getattr(args, 'output', 'book_output.md'),
            target_pages=getattr(args, 'pages', 400),
            context_path=getattr(args, 'context', None),
            provider=getattr(args, 'provider', 'openai'),
            model=getattr(args, 'model', None),
            endpoint=getattr(args, 'endpoint', None),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict
        return asdict(self)
    
    def get_total_target_words(self) -> int:
        """Calculate total target word count."""
        return self.book.target_pages * self.book.words_per_page
    
    def get_estimated_generation_time(self, words_per_minute: int = 1000) -> float:
        """Estimate total generation time in minutes."""
        total_words = self.get_total_target_words()
        return total_words / words_per_minute


# =============================================================================
# Configuration Factory
# =============================================================================

def create_config(
    topic: str,
    output_file: str = "book_output.md",
    target_pages: int = 400,
    context_path: Optional[str] = None,
    provider: str = "openai",
    model: Optional[str] = None,
    endpoint: Optional[str] = None,
    **kwargs
) -> Config:
    """
    Factory function to create configuration with common parameters.
    
    Args:
        topic: Book topic/title
        output_file: Output file path
        target_pages: Target number of pages
        context_path: Path to context documents
        provider: LLM provider
        model: Specific model to use
        endpoint: Custom API endpoint
        **kwargs: Additional configuration options
        
    Returns:
        Configured Config instance
    """
    # Set default model based on provider
    if model is None:
        provider_enum = Provider(provider)
        model = PROVIDER_CONFIGS.get(provider_enum, {}).get("default_model", "gpt-4")
    
    return Config(
        topic=topic,
        output_file=output_file,
        target_pages=target_pages,
        context_path=context_path,
        provider=provider,
        model=model,
        endpoint=endpoint,
        **kwargs
    )