# Implementation Plan: Architectural Evolution Proposal

## Overview

This document provides a detailed implementation plan for the architectural evolution proposal. The implementation is organized into 4 phases, each building upon the previous to transform BookWriterAI into a professional-grade automated writing platform.

## Current State Analysis

### Existing Codebase Structure
```
ebooks-by-multi-agents/
├── ebooks.py                 # Monolithic ~2000 lines
├── src/                      # Empty directories
│   ├── characters/
│   ├── cli/
│   ├── core/
│   ├── knowledge/
│   ├── narrative/
│   ├── refinement/
│   └── style/
├── tests/                    # Empty
├── configs/                  # Empty
├── checkpoints/              # Runtime data
└── plans/                    # Documentation
```

### Existing Capabilities (Already Implemented)
- Multi-layered content expansion with recursive section generation
- Basic RAG system with TF-IDF retrieval
- Adaptive token budgeting based on chapter complexity
- Progressive outline enrichment in 3 phases
- Content validation with regeneration triggers
- Checkpoint-based resilience
- Character density estimation for page count

### Critical Gaps to Address
1. No long-term narrative memory or plot consistency tracking
2. No character development or relationship management
3. No stylistic consistency enforcement
4. Limited RAG capabilities (keyword-based only)
5. Single-pass refinement without iterative improvement
6. No genre-specific templates or conventions
7. No emotional arc planning or pacing control
8. Limited scientific/technical content support

---

## Target Architecture

```
src/
├── core/                    # Core infrastructure
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── base_agent.py       # Base agent class
│   ├── llm_client.py       # LLM API client abstraction
│   └── exceptions.py       # Custom exceptions
│
├── narrative/               # Long-Term Narrative Memory System
│   ├── __init__.py
│   ├── events.py           # EventsStore, NarrativeEvent
│   ├── entities.py         # EntityRegistry, Entity, EntityState
│   ├── relations.py        # RelationsGraph, Relation
│   ├── context_synthesizer.py  # ContextSynthesizer
│   └── state_graph.py      # NarrativeStateGraph
│
├── characters/              # Character Development Framework
│   ├── __init__.py
│   ├── profile.py          # PersonalityProfile, SpeechPatterns
│   ├── arc.py              # CharacterArc, ArcMoment
│   ├── dialogue.py         # DialogueGenerator
│   ├── relationships.py    # RelationshipDynamics
│   └── consistency.py      # CharacterConsistencyValidator
│
├── style/                   # Stylistic Consistency Engine
│   ├── __init__.py
│   ├── profile.py          # StyleProfile
│   ├── manager.py          # StyleProfileManager
│   ├── injector.py         # StylePromptInjector
│   ├── validator.py        # StyleValidator
│   └── corrector.py        # StyleCorrector
│
├── knowledge/               # Advanced RAG Architecture
│   ├── __init__.py
│   ├── document_loader.py  # DocumentLoader (existing)
│   ├── parsers/            # Document parsers
│   │   ├── __init__.py
│   │   ├── base.py         # DocumentParser ABC
│   │   ├── pdf.py          # PDFParser
│   │   ├── txt.py          # TXTParser
│   │   └── markdown.py     # MarkdownParser
│   ├── chunker.py          # TextChunker (existing)
│   ├── embeddings.py       # MultiVectorStore
│   ├── retrieval.py        # HierarchicalRetriever
│   ├── query_rewriter.py   # QueryRewriter
│   └── context_assembler.py # ContextAssembler
│
├── refinement/              # Iterative Refinement Pipeline
│   ├── __init__.py
│   ├── quality.py          # QualityAssessor, QualityScore
│   ├── structural.py       # StructuralRefiner
│   ├── prose.py            # ProseRefiner
│   ├── consistency.py      # ConsistencyCorrector
│   └── pipeline.py         # IterativeRefinementPipeline
│
├── genre/                   # Genre-Specific Templates
│   ├── __init__.py
│   ├── base.py             # GenreTemplate, ActStructure
│   ├── templates/          # Genre-specific implementations
│   │   ├── __init__.py
│   │   ├── thriller.py
│   │   ├── romance.py
│   │   ├── scifi.py
│   │   ├── fantasy.py
│   │   ├── mystery.py
│   │   ├── literary.py
│   │   └── non_fiction.py
│   └── manager.py          # GenreTemplateManager
│
├── emotional/               # Emotional Arc Planning
│   ├── __init__.py
│   ├── arc.py              # EmotionalArc, EmotionalBeat
│   ├── planner.py          # EmotionalArcPlanner
│   └── tension.py          # TensionManager
│
├── scientific/              # Scientific/Technical Content Support
│   ├── __init__.py
│   ├── citation.py         # CitationManager
│   ├── fact_check.py       # FactVerificationSystem
│   ├── accuracy.py         # TechnicalAccuracyChecker
│   └── academic.py         # AcademicStructureManager
│
├── agents/                  # Specialized Agents
│   ├── __init__.py
│   ├── outline.py          # OutlineAgent
│   ├── chapter_writer.py   # ChapterWriterAgent
│   ├── editor.py           # EditorAgent
│   └── compiler.py         # CompilerAgent
│
├── orchestrator/            # Main Orchestration
│   ├── __init__.py
│   ├── book_orchestrator.py # BookOrchestrator
│   ├── checkpoint.py       # Checkpoint management
│   └── progress.py         # Progress tracking
│
└── cli/                     # Command Line Interface
    ├── __init__.py
    └── main.py             # CLI entry point
```

---

## Phase 1: Foundation (Priority: Critical Infrastructure)

### 1.1 Project Structure Setup

**Tasks:**
- [ ] Create all package directories with `__init__.py` files
- [ ] Set up pyproject.toml for modern Python packaging
- [ ] Configure pytest and test structure
- [ ] Set up logging configuration module

**Files to Create:**
```
src/__init__.py
src/core/__init__.py
src/core/exceptions.py
pyproject.toml
pytest.ini
```

### 1.2 Core Infrastructure Migration

**Tasks:**
- [ ] Extract Config dataclass to `src/core/config.py`
- [ ] Create LLM client abstraction in `src/core/llm_client.py`
- [ ] Extract BaseAgent to `src/core/base_agent.py`
- [ ] Create custom exceptions in `src/core/exceptions.py`

**Dependencies:** None

**Files to Create:**
```
src/core/config.py         # Config dataclass with all settings
src/core/llm_client.py     # LLMClient abstraction for OpenAI/Bailian/Qwen
src/core/base_agent.py     # BaseAgent class
src/core/exceptions.py     # BookWriterError, ValidationError, etc.
```

### 1.3 Long-Term Narrative Memory System

**Tasks:**
- [ ] Implement NarrativeEvent dataclass
- [ ] Implement EventsStore with SQLite persistence
- [ ] Implement Entity and EntityState dataclasses
- [ ] Implement EntityRegistry
- [ ] Implement Relation and RelationsGraph
- [ ] Implement ContextSynthesizer
- [ ] Create NarrativeStateGraph facade

**Dependencies:** Core Infrastructure

**Files to Create:**
```
src/narrative/__init__.py
src/narrative/events.py           # NarrativeEvent, EventsStore
src/narrative/entities.py         # Entity, EntityState, EntityRegistry
src/narrative/relations.py        # Relation, RelationsGraph
src/narrative/context_synthesizer.py  # ContextSynthesizer
src/narrative/state_graph.py      # NarrativeStateGraph
tests/test_narrative/
    test_events.py
    test_entities.py
    test_relations.py
    test_context_synthesizer.py
```

**Database Schema (SQLite):**
```sql
-- events table
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    chapter_id INTEGER,
    timestamp TEXT,
    description TEXT,
    entities_involved TEXT,  -- JSON array
    consequences TEXT,       -- JSON array
    emotional_valence REAL,
    importance_weight REAL,
    foreshadowing_refs TEXT, -- JSON array
    resolution_refs TEXT     -- JSON array
);

-- entities table
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    aliases TEXT,            -- JSON array
    first_appearance INTEGER,
    last_mention INTEGER,
    attributes TEXT          -- JSON object
);

-- entity_states table
CREATE TABLE entity_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    chapter_id INTEGER,
    timestamp TEXT,
    state_type TEXT,
    attributes TEXT,         -- JSON object
    changed_by_event TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

-- relations table
CREATE TABLE relations (
    relation_id TEXT PRIMARY KEY,
    source_entity TEXT,
    target_entity TEXT,
    relation_type TEXT,
    strength REAL,
    sentiment REAL,
    established_chapter INTEGER,
    last_updated_chapter INTEGER,
    history TEXT             -- JSON array
);
```

### 1.4 Advanced RAG Architecture

**Tasks:**
- [ ] Migrate existing document parsers to modular structure
- [ ] Implement MultiVectorStore with embedding support
- [ ] Implement HierarchicalRetriever
- [ ] Implement QueryRewriter
- [ ] Implement ContextAssembler with token budget optimization
- [ ] Add semantic embedding support (optional: sentence-transformers)

**Dependencies:** Core Infrastructure

**Files to Create:**
```
src/knowledge/__init__.py
src/knowledge/document_loader.py   # DocumentLoader
src/knowledge/parsers/__init__.py
src/knowledge/parsers/base.py      # DocumentParser ABC
src/knowledge/parsers/pdf.py       # PDFParser
src/knowledge/parsers/txt.py       # TXTParser
src/knowledge/parsers/markdown.py  # MarkdownParser
src/knowledge/chunker.py           # TextChunker (migrated)
src/knowledge/embeddings.py        # MultiVectorStore
src/knowledge/retrieval.py         # HierarchicalRetriever
src/knowledge/query_rewriter.py    # QueryRewriter
src/knowledge/context_assembler.py # ContextAssembler
tests/test_knowledge/
    test_parsers.py
    test_chunker.py
    test_embeddings.py
    test_retrieval.py
```

---

## Phase 2: Content Quality (Priority: Quality Assurance)

### 2.1 Stylistic Consistency Engine

**Tasks:**
- [ ] Implement StyleProfile dataclass
- [ ] Implement StyleProfileManager
- [ ] Implement StylePromptInjector
- [ ] Implement StyleValidator
- [ ] Implement StyleCorrector

**Dependencies:** Phase 1

**Files to Create:**
```
src/style/__init__.py
src/style/profile.py      # StyleProfile dataclass
src/style/manager.py      # StyleProfileManager
src/style/injector.py     # StylePromptInjector
src/style/validator.py    # StyleValidator
src/style/corrector.py    # StyleCorrector
tests/test_style/
    test_profile.py
    test_validator.py
    test_corrector.py
```

### 2.2 Iterative Refinement Pipeline

**Tasks:**
- [ ] Implement QualityScore and QualityIssue dataclasses
- [ ] Implement QualityAssessor
- [ ] Implement StructuralRefiner
- [ ] Implement ProseRefiner
- [ ] Implement ConsistencyCorrector
- [ ] Implement IterativeRefinementPipeline with convergence detection

**Dependencies:** Phase 1, Stylistic Consistency Engine

**Files to Create:**
```
src/refinement/__init__.py
src/refinement/quality.py       # QualityScore, QualityIssue, QualityAssessor
src/refinement/structural.py    # StructuralRefiner
src/refinement/prose.py         # ProseRefiner
src/refinement/consistency.py   # ConsistencyCorrector
src/refinement/pipeline.py      # IterativeRefinementPipeline
tests/test_refinement/
    test_quality.py
    test_pipeline.py
```

---

## Phase 3: Narrative Depth (Priority: Literary Quality)

### 3.1 Character Development Framework

**Tasks:**
- [ ] Implement PersonalityProfile and SpeechPatterns dataclasses
- [ ] Implement CharacterArc and ArcMoment dataclasses
- [ ] Implement DialogueGenerator
- [ ] Implement RelationshipDynamics
- [ ] Implement CharacterConsistencyValidator

**Dependencies:** Phase 1, Phase 2

**Files to Create:**
```
src/characters/__init__.py
src/characters/profile.py       # PersonalityProfile, SpeechPatterns
src/characters/arc.py           # CharacterArc, ArcMoment
src/characters/dialogue.py      # DialogueGenerator
src/characters/relationships.py # RelationshipDynamics
src/characters/consistency.py   # CharacterConsistencyValidator
tests/test_characters/
    test_profile.py
    test_arc.py
    test_dialogue.py
    test_consistency.py
```

### 3.2 Emotional Arc Planning Module

**Tasks:**
- [ ] Implement EmotionalArc and EmotionalBeat dataclasses
- [ ] Implement EmotionalArcPlanner
- [ ] Implement TensionManager

**Dependencies:** Phase 1, Character Development Framework

**Files to Create:**
```
src/emotional/__init__.py
src/emotional/arc.py        # EmotionalArc, EmotionalBeat
src/emotional/planner.py    # EmotionalArcPlanner
src/emotional/tension.py    # TensionManager
tests/test_emotional/
    test_arc.py
    test_planner.py
    test_tension.py
```

---

## Phase 4: Specialization (Priority: Market Readiness)

### 4.1 Genre-Specific Template System

**Tasks:**
- [ ] Implement GenreTemplate and ActStructure base classes
- [ ] Implement ThrillerTemplate
- [ ] Implement RomanceTemplate
- [ ] Implement SciFiTemplate
- [ ] Implement FantasyTemplate
- [ ] Implement MysteryTemplate
- [ ] Implement LiteraryFictionTemplate
- [ ] Implement NonFictionTemplate
- [ ] Implement GenreTemplateManager

**Dependencies:** Phase 1, Phase 2, Phase 3

**Files to Create:**
```
src/genre/__init__.py
src/genre/base.py               # GenreTemplate, ActStructure, Act
src/genre/templates/__init__.py
src/genre/templates/thriller.py
src/genre/templates/romance.py
src/genre/templates/scifi.py
src/genre/templates/fantasy.py
src/genre/templates/mystery.py
src/genre/templates/literary.py
src/genre/templates/non_fiction.py
src/genre/manager.py            # GenreTemplateManager
tests/test_genre/
    test_templates.py
    test_manager.py
```

### 4.2 Scientific/Technical Content Support

**Tasks:**
- [ ] Implement CitationManager with multiple citation styles
- [ ] Implement FactVerificationSystem
- [ ] Implement TechnicalAccuracyChecker
- [ ] Implement AcademicStructureManager

**Dependencies:** Phase 1, Advanced RAG

**Files to Create:**
```
src/scientific/__init__.py
src/scientific/citation.py      # CitationManager, Reference
src/scientific/fact_check.py    # FactVerificationSystem
src/scientific/accuracy.py      # TechnicalAccuracyChecker
src/scientific/academic.py      # AcademicStructureManager
tests/test_scientific/
    test_citation.py
    test_fact_check.py
    test_accuracy.py
```

---

## Migration Strategy

### Step 1: Parallel Development
- Keep `ebooks.py` as the stable version
- Develop new modules in `src/` directory
- Create adapter layer to test new components with existing code

### Step 2: Gradual Migration
1. Migrate core infrastructure (Config, BaseAgent)
2. Migrate Knowledge Base system
3. Migrate agents (OutlineAgent, ChapterWriterAgent, etc.)
4. Integrate new systems (Narrative Memory, Style Engine, etc.)
5. Update CLI to use new architecture

### Step 3: Deprecation
- Once all functionality is migrated and tested
- Mark `ebooks.py` as deprecated
- Remove in future version

---

## Configuration Schema

```python
@dataclass
class ProfessionalBookConfig:
    """Comprehensive configuration for professional book generation."""
    
    # Basic settings
    title: str
    genre: str
    subgenre: Optional[str]
    target_length: int  # pages
    target_audience: str
    
    # Content type
    content_type: str  # fiction, non_fiction, technical, academic
    
    # Narrative settings (for fiction)
    narrative_config: Optional[NarrativeConfig]
    
    # Technical settings (for non-fiction)
    technical_config: Optional[TechnicalConfig]
    
    # Style settings
    style_config: StyleConfig
    
    # Quality settings
    quality_config: QualityConfig
    
    # RAG settings
    rag_config: RAGConfig
    
    # Output settings
    output_format: str  # markdown, epub, pdf, docx
    include_front_matter: bool
    include_back_matter: bool
```

---

## Testing Strategy

### Unit Tests
- Each module has corresponding test file
- Test dataclasses, business logic, edge cases
- Mock LLM calls for deterministic testing

### Integration Tests
- Test module interactions
- Test full pipeline with mock LLM
- Test checkpoint/resume functionality

### End-to-End Tests
- Generate short books (5-10 pages) with real LLM
- Validate output quality metrics
- Performance benchmarks

---

## Dependencies

### Core Dependencies (existing)
- openai >= 1.0.0
- tiktoken
- requests
- python-dotenv
- PyPDF2 (optional, for PDF support)
- markdown (optional, for Markdown support)

### New Dependencies
- sentence-transformers (optional, for semantic embeddings)
- sqlite3 (stdlib, for persistence)
- dataclasses (stdlib)
- typing_extensions (for Python < 3.10)

---

## Risk Mitigation

### Technical Risks
1. **LLM API Rate Limits**: Implement exponential backoff and retry logic
2. **Token Budget Overflow**: Hard limits and interrupt mechanisms (already implemented)
3. **Data Persistence Corruption**: Regular checkpointing with validation
4. **Memory Usage for Large Books**: Streaming generation and chunked processing

### Migration Risks
1. **Breaking Changes**: Maintain backward compatibility during migration
2. **Feature Parity**: Comprehensive test coverage before deprecation
3. **Performance Regression**: Benchmark before/after migration

---

## Success Metrics

| Metric | Current State | Target State |
|--------|--------------|--------------|
| Narrative Consistency Score | ~60% | >90% |
| Character Consistency Score | N/A | >85% |
| Style Consistency Score | ~50% | >90% |
| Average Quality Score | ~65% | >85% |
| Fact Accuracy (non-fiction) | N/A | >95% |
| Reader Satisfaction (estimated) | ~60% | >80% |
| Test Coverage | 0% | >80% |
| Code Modularity | Monolithic | Fully modular |

---

## Next Steps

1. **Review and approve this implementation plan**
2. **Begin Phase 1.1: Project Structure Setup**
3. **Implement Core Infrastructure Migration**
4. **Implement Long-Term Narrative Memory System**
5. **Implement Advanced RAG Architecture**

---

*Document Version: 1.0*
*Created: 2026-03-24*
*Based on: architectural-evolution-proposal.md v1.0*