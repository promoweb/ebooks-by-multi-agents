"""
BookWriterAI - Professional Book Generation Platform

This package provides a comprehensive, modular architecture for
AI-powered book generation with literary quality and structural coherence.

Main Components:
- core: Core infrastructure, configuration, and LLM client
- narrative: Long-term narrative memory and context synthesis
- knowledge: Advanced RAG system with multi-vector embeddings
- style: Stylistic consistency engine
- refinement: Iterative refinement pipeline
- characters: Character development framework
- genre: Genre-specific templates and conventions
- technical: Scientific/technical content support

Usage:
    from src import BookWriterConfig, NarrativeStateGraph, KnowledgeBase
    from src import StyleProfileManager, IterativeRefinementPipeline
    from src import GenreTemplateManager, CitationManager
"""

# Version
__version__ = "2.0.0"
__author__ = "BookWriterAI Team"

# Core
from src.core import (
    BookWriterAIError,
    ConfigurationError,
    LLMError,
    BookWriterConfig,
    LLMClient,
    BaseAgent,
)

# Narrative Memory
from src.narrative import (
    NarrativeEvent,
    EventsStore,
    Entity,
    EntityRegistry,
    Relation,
    RelationsGraph,
    ContextSynthesizer,
    NarrativeStateGraph,
    EmotionalArc,
    EmotionalBeat,
    EmotionalArcPlanner,
    TensionManager,
)

# Knowledge/RAG
from src.knowledge import (
    DocumentParser,
    PDFParser,
    TXTParser,
    MarkdownParser,
    TextChunker,
    Chunk,
    VectorStore,
    MultiVectorStore,
    HierarchicalRetriever,
    ContextualRetriever,
    QueryRewriter,
    ContextAssembler,
    ContextCompressor,
    KnowledgeBase,
)

# Style
from src.style import (
    StyleProfile,
    StyleProfileManager,
    StylePromptInjector,
    StyleValidator,
    StyleCorrector,
    StyleValidationReport,
)

# Refinement
from src.refinement import (
    QualityScore,
    QualityIssue,
    QualityAssessor,
    StructuralRefiner,
    ProseRefiner,
    ConsistencyCorrector,
    IterativeRefinementPipeline,
    RefinementResult,
)

# Characters
from src.characters import (
    PersonalityProfile,
    SpeechPatterns,
    CharacterProfile,
    CharacterArc,
    ArcMoment,
    DialogueGenerator,
    RelationshipDynamics,
    CharacterConsistencyValidator,
)

# Genre
from src.genre import (
    GenreCategory,
    Act,
    TurningPoint,
    ActStructure,
    ChapterTemplate,
    CharacterArchetype,
    PlotDeviceTemplate,
    GenreTemplate,
    GenreTemplateManager,
    GENRE_TEMPLATES,
)

# Technical
from src.technical import (
    CitationStyle,
    Author,
    Reference,
    CitationManager,
    ClaimType,
    VerificationStatus,
    FactualClaim,
    VerificationResult,
    ContentVerificationReport,
    FactVerificationSystem,
    TechnicalAccuracyChecker,
    TechnicalAccuracyReport,
    DocumentType,
    Section,
    AcademicStructure,
    AcademicStructureManager,
)

# Book Writer API
from src.book_writer import (
    BookConfig,
    GenerationProgress,
    Chapter,
    Book,
    BookGenerationResult,
    ProfessionalBookWriter,
    generate_book,
)

# CLI
from src.cli import main as cli_main


__all__ = [
    # Version
    "__version__",
    "__author__",
    
    # Core
    "BookWriterAIError",
    "ConfigurationError",
    "LLMError",
    "BookWriterConfig",
    "LLMClient",
    "BaseAgent",
    
    # Narrative
    "NarrativeEvent",
    "EventsStore",
    "Entity",
    "EntityRegistry",
    "Relation",
    "RelationsGraph",
    "ContextSynthesizer",
    "NarrativeStateGraph",
    "EmotionalArc",
    "EmotionalBeat",
    "EmotionalArcPlanner",
    "TensionManager",
    
    # Knowledge
    "DocumentParser",
    "PDFParser",
    "TXTParser",
    "MarkdownParser",
    "TextChunker",
    "Chunk",
    "VectorStore",
    "MultiVectorStore",
    "HierarchicalRetriever",
    "ContextualRetriever",
    "QueryRewriter",
    "ContextAssembler",
    "ContextCompressor",
    "KnowledgeBase",
    
    # Style
    "StyleProfile",
    "StyleProfileManager",
    "StylePromptInjector",
    "StyleValidator",
    "StyleCorrector",
    "StyleValidationReport",
    
    # Refinement
    "QualityScore",
    "QualityIssue",
    "QualityAssessor",
    "StructuralRefiner",
    "ProseRefiner",
    "ConsistencyCorrector",
    "IterativeRefinementPipeline",
    "RefinementResult",
    
    # Characters
    "PersonalityProfile",
    "SpeechPatterns",
    "CharacterProfile",
    "CharacterArc",
    "ArcMoment",
    "DialogueGenerator",
    "RelationshipDynamics",
    "CharacterConsistencyValidator",
    
    # Genre
    "GenreCategory",
    "Act",
    "TurningPoint",
    "ActStructure",
    "ChapterTemplate",
    "CharacterArchetype",
    "PlotDeviceTemplate",
    "GenreTemplate",
    "GenreTemplateManager",
    "GENRE_TEMPLATES",
    
    # Technical
    "CitationStyle",
    "Author",
    "Reference",
    "CitationManager",
    "ClaimType",
    "VerificationStatus",
    "FactualClaim",
    "VerificationResult",
    "ContentVerificationReport",
    "FactVerificationSystem",
    "TechnicalAccuracyChecker",
    "TechnicalAccuracyReport",
    "DocumentType",
    "Section",
    "AcademicStructure",
    "AcademicStructureManager",
    
    # Book Writer API
    "BookConfig",
    "GenerationProgress",
    "Chapter",
    "Book",
    "BookGenerationResult",
    "ProfessionalBookWriter",
    "generate_book",
    
    # CLI
    "cli_main",
]