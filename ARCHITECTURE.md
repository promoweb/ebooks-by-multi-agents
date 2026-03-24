# BookWriterAI Architecture Documentation

## Overview

BookWriterAI is a professional-grade automated writing platform capable of generating books with literary quality, emotional depth, and structural coherence. The system uses a modular architecture designed for extensibility, maintainability, and testability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BookWriterAI Platform                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ProfessionalBookWriter API                       │  │
│  │                     (src/book_writer.py)                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         │                          │                          │            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │    Core     │           │  Narrative  │           │  Knowledge  │      │
│  │  (config,   │           │   Memory    │           │     RAG     │      │
│  │   llm,      │           │   System    │           │   System    │      │
│  │  agents)    │           │             │           │             │      │
│  └─────────────┘           └─────────────┘           └─────────────┘      │
│                                                                              │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │   Style     │           │ Refinement  │           │  Characters │      │
│  │   Engine    │           │  Pipeline   │           │  Framework  │      │
│  └─────────────┘           └─────────────┘           └─────────────┘      │
│                                                                              │
│  ┌─────────────┐           ┌─────────────┐                                   │
│  │   Genre     │           │  Technical  │                                   │
│  │  Templates  │           │   Support   │                                   │
│  └─────────────┘           └─────────────┘                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
src/
├── __init__.py              # Package exports
├── book_writer.py           # Main API
│
├── core/                    # Core Infrastructure
│   ├── __init__.py
│   ├── exceptions.py        # Exception hierarchy
│   ├── config.py            # Configuration management
│   ├── llm_client.py        # LLM client abstraction
│   └── base_agent.py        # Base agent with mixins
│
├── narrative/               # Long-Term Narrative Memory
│   ├── __init__.py
│   ├── events.py            # EventsStore
│   ├── entities.py          # EntityRegistry
│   ├── relations.py         # RelationsGraph
│   ├── context_synthesizer.py
│   ├── state_graph.py       # NarrativeStateGraph facade
│   └── emotional_arc.py     # Emotional arc planning
│
├── knowledge/               # Advanced RAG System
│   ├── __init__.py
│   ├── parsers/             # Document parsers
│   │   ├── base.py
│   │   ├── pdf.py
│   │   ├── txt.py
│   │   └── markdown.py
│   ├── chunker.py           # Text chunking
│   ├── embeddings.py        # Multi-vector store
│   ├── retrieval.py         # Hierarchical retrieval
│   ├── query_rewriter.py    # Query optimization
│   ├── context_assembler.py # Context assembly
│   └── base.py              # KnowledgeBase facade
│
├── style/                   # Stylistic Consistency
│   ├── __init__.py
│   ├── profile.py           # Style profiles
│   └── enforcement.py       # Style enforcement
│
├── refinement/              # Iterative Refinement
│   ├── __init__.py
│   ├── quality.py           # Quality assessment
│   └── pipeline.py          # Refinement pipeline
│
├── characters/              # Character Development
│   ├── __init__.py
│   ├── profile.py           # Character profiles
│   └── dialogue.py          # Dialogue generation
│
├── genre/                   # Genre Templates
│   ├── __init__.py
│   ├── templates.py         # Core templates
│   └── genres.py            # Specific genres
│
└── technical/               # Technical Content Support
    ├── __init__.py
    ├── citations.py         # Citation management
    ├── verification.py      # Fact verification
    └── structure.py         # Academic structure
```

## Core Components

### 1. Long-Term Narrative Memory System

The narrative memory system maintains consistency across long-form content through:

- **EventsStore**: SQLite-backed storage for narrative events with semantic indexing
- **EntityRegistry**: Central registry for characters, locations, and objects
- **RelationsGraph**: Graph-based relationship management
- **ContextSynthesizer**: Relevance-based context retrieval for generation

```python
from src.narrative import NarrativeStateGraph

# Initialize narrative memory
narrative = NarrativeStateGraph()

# Add an event
event = NarrativeEvent(
    event_id="event_1",
    event_type="plot_point",
    chapter_id=1,
    description="John discovered the hidden passage",
    entities_involved=["john"],
    importance_weight=0.8
)
narrative.add_event(event)

# Get context for next chapter
context = narrative.synthesize_context(current_chapter=2)
```

### 2. Advanced RAG Architecture

Multi-vector retrieval system for intelligent context management:

- **MultiVectorStore**: Separate embeddings for semantic, narrative, entity, and style
- **HierarchicalRetriever**: Book → Chapter → Section → Paragraph retrieval
- **ContextAssembler**: Token-budget optimized context assembly

```python
from src.knowledge import KnowledgeBase

# Initialize knowledge base
kb = KnowledgeBase()

# Add documents
kb.add_document("research.pdf")

# Retrieve relevant context
results = kb.retrieve("What is the protagonist's motivation?")
```

### 3. Stylistic Consistency Engine

Ensures consistent voice and style throughout:

- **StyleProfile**: Comprehensive style definition
- **StylePromptInjector**: Injects style requirements into prompts
- **StyleValidator**: Validates output against style profile

```python
from src.style import StyleProfileManager, StylePromptInjector

manager = StyleProfileManager()
profile = manager.get_profile("literary")

injector = StylePromptInjector()
prompt = injector.create_style_prompt(profile, "narration", context)
```

### 4. Iterative Refinement Pipeline

Quality improvement through iterative feedback:

- **QualityAssessor**: Multi-dimensional quality scoring
- **StructuralRefiner**: Pacing and structure improvements
- **ProseRefiner**: Sentence-level improvements
- **ConsistencyCorrector**: Narrative consistency fixes

```python
from src.refinement import IterativeRefinementPipeline

pipeline = IterativeRefinementPipeline(
    max_iterations=3,
    quality_threshold=0.85
)

result = pipeline.refine_chapter(content, chapter_info, style_profile)
```

### 5. Character Development Framework

Manages character consistency and development:

- **CharacterProfile**: Personality, voice, and arc management
- **DialogueGenerator**: Character-appropriate dialogue
- **CharacterConsistencyValidator**: Behavior validation

```python
from src.characters import CharacterProfile, DialogueGenerator

profile = CharacterProfile(
    name="John Doe",
    personality=PersonalityProfile(
        openness=0.8,
        conscientiousness=0.6,
        extraversion=0.4
    )
)

dialogue = DialogueGenerator({profile.name: profile}, llm_client)
```

### 6. Genre-Specific Templates

Pre-configured templates for different genres:

- **ThrillerTemplate**: Fast-paced, tension-focused structure
- **RomanceTemplate**: Relationship arc with HEA guarantee
- **FantasyTemplate**: Hero's journey structure
- **MysteryTemplate**: Puzzle-focused with fair-play rules
- **TechnicalTemplate**: Educational structure with exercises

```python
from src.genre import GenreTemplateManager

manager = GenreTemplateManager()
template = manager.get_template("thriller")

# Access genre-specific structure
acts = template.act_structure.acts
required = template.required_elements
```

### 7. Emotional Arc Planning

Plans and validates emotional trajectories:

- **EmotionalArcPlanner**: Plans emotional beats
- **TensionManager**: Manages narrative tension

```python
from src.narrative import EmotionalArcPlanner

planner = EmotionalArcPlanner()
arc = planner.plan_book_arc(genre_template, theme="redemption")
```

### 8. Technical Content Support

Support for academic and technical writing:

- **CitationManager**: Multi-style citation formatting (APA, MLA, Chicago, IEEE)
- **FactVerificationSystem**: Claim extraction and verification
- **AcademicStructureManager**: Document structure templates

```python
from src.technical import CitationManager, AcademicStructureManager

# Citations
citations = CitationManager(style="apa")
citations.create_reference(
    reference_type="book",
    title="Example",
    authors=[{"first_name": "John", "last_name": "Smith"}],
    year=2024
)

# Academic structure
struct_manager = AcademicStructureManager()
structure = struct_manager.create_structure("thesis", "My Thesis")
```

## Main API

### ProfessionalBookWriter

The main entry point for book generation:

```python
from src.book_writer import ProfessionalBookWriter, BookConfig

config = BookConfig(
    title="My Novel",
    genre="thriller",
    target_length=80000,
    style="commercial",
    enable_refinement=True
)

writer = ProfessionalBookWriter(config)

# Generate with progress tracking
def on_progress(progress):
    print(f"{progress.current_phase}: {progress.progress_percent:.0%}")

result = writer.generate_book(progress_callback=on_progress)

if result.success:
    print(f"Generated {result.book.total_word_count} words")
    writer.export_book(result.book, "markdown", "output.md")
```

### Convenience Function

```python
from src.book_writer import generate_book

result = generate_book(
    title="Quick Novel",
    genre="fantasy",
    target_length=60000
)
```

## Configuration

### BookConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | str | required | Book title |
| `genre` | str | "literary_fiction" | Genre template |
| `subgenre` | str | None | Subgenre specification |
| `target_length` | int | 80000 | Target word count |
| `content_type` | str | "fiction" | fiction, non_fiction, technical, academic |
| `style` | str | "literary" | Style profile name |
| `tone` | str | None | Override tone |
| `pov` | str | "third_limited" | Point of view |
| `tense` | str | "past" | Narrative tense |
| `enable_refinement` | bool | True | Enable iterative refinement |
| `max_refinement_iterations` | int | 3 | Max refinement passes |
| `quality_threshold` | float | 0.85 | Quality target |
| `enable_character_tracking` | bool | True | Track character consistency |
| `enable_emotional_arcs` | bool | True | Plan emotional arcs |
| `enable_fact_checking` | bool | False | Enable for non-fiction |
| `context_documents` | list | [] | RAG context documents |
| `llm_provider` | str | "openai" | LLM provider |
| `llm_model` | str | None | Specific model |

## Data Models

### NarrativeEvent

```python
@dataclass
class NarrativeEvent:
    event_id: str
    event_type: str  # plot_point, character_action, revelation, conflict, resolution
    chapter_id: int
    timestamp: str
    description: str
    entities_involved: List[str]
    consequences: List[str]
    emotional_valence: float  # -1.0 to 1.0
    importance_weight: float  # 0.0 to 1.0
    foreshadowing_refs: List[str]
    resolution_refs: List[str]
```

### Entity

```python
@dataclass
class Entity:
    entity_id: str
    entity_type: str  # character, location, object, concept, organization
    name: str
    aliases: List[str]
    first_appearance: int
    last_mention: int
    attributes: Dict[str, Any]
    state_history: List[EntityState]
```

### QualityScore

```python
@dataclass
class QualityScore:
    narrative_coherence: float
    stylistic_consistency: float
    content_depth: float
    character_consistency: float
    plot_progression: float
    emotional_resonance: float
    prose_quality: float
    overall_score: float
    issues: List[QualityIssue]
```

## Extending the System

### Adding a New Genre Template

```python
from src.genre import GenreTemplate, GenreCategory, Act, ActStructure

my_genre = GenreTemplate(
    genre_name="my_genre",
    category=GenreCategory.FICTION,
    subgenres=["sub1", "sub2"],
    act_structure=ActStructure(
        name="custom",
        acts=[
            Act("Part 1", 0.0, 0.5, "First half"),
            Act("Part 2", 0.5, 1.0, "Second half")
        ]
    ),
    required_elements=["element1"],
    typical_pacing="moderate"
)

# Register it
from src.genre import GenreTemplateManager
manager = GenreTemplateManager()
manager.register_template(my_genre)
```

### Adding a New Style Profile

```python
from src.style import StyleProfile, StyleProfileManager

profile = StyleProfile(
    name="my_style",
    narrative_voice="third_limited",
    primary_tone="contemplative",
    vocabulary_complexity="sophisticated",
    average_sentence_length=20
)

manager = StyleProfileManager()
manager.register_profile(profile)
```

### Adding a New Document Parser

```python
from src.knowledge.parsers import DocumentParser

class MyParser(DocumentParser):
    def parse(self, content: bytes) -> str:
        # Extract text from your format
        return extracted_text
    
    def supports(self, file_path: str) -> bool:
        return file_path.endswith(".myformat")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_narrative.py -v

# Run with coverage
pytest tests/ --cov=src
```

## Performance Considerations

- **SQLite Persistence**: Narrative memory uses SQLite for efficient storage and querying
- **Token Budgeting**: Context synthesis optimizes for token limits
- **Lazy Loading**: Components are initialized only when needed
- **Caching**: Embedding results are cached for repeated queries

## Error Handling

The system uses a custom exception hierarchy:

```python
from src.core.exceptions import (
    BookWriterAIError,     # Base exception
    ConfigurationError,    # Config issues
    LLMError,              # LLM API issues
    NarrativeError,        # Narrative memory issues
    KnowledgeError,        # RAG system issues
    StyleError,            # Style enforcement issues
    QualityError,          # Quality assessment issues
)
```

## Version History

- **2.0.0**: Complete architectural evolution with modular components
- **1.0.0**: Initial monolithic implementation

## License

MIT License - See LICENSE file for details.
