"""
Professional Book Writer - Main API for BookWriterAI.

This module provides the main API for professional book generation,
integrating all components of the modular architecture.

Usage:
    from src.book_writer import ProfessionalBookWriter, BookConfig
    
    config = BookConfig(
        title="My Novel",
        genre="thriller",
        target_length=80000
    )
    
    writer = ProfessionalBookWriter(config)
    result = writer.generate_book()
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from src.core import BookWriterConfig, LLMClient, BaseAgent
from src.core.exceptions import BookWriterAIError, ConfigurationError, LLMError

from src.narrative import (
    NarrativeStateGraph,
    ContextSynthesizer,
    EmotionalArcPlanner,
    TensionManager,
)

from src.knowledge import (
    KnowledgeBase,
    ContextAssembler,
)

from src.style import (
    StyleProfile,
    StyleProfileManager,
    StylePromptInjector,
    StyleValidator,
)

from src.refinement import (
    QualityAssessor,
    IterativeRefinementPipeline,
)

from src.characters import (
    CharacterProfile,
    DialogueGenerator,
    CharacterConsistencyValidator,
)

from src.genre import (
    GenreTemplate,
    GenreTemplateManager,
)

from src.technical import (
    CitationManager,
    FactVerificationSystem,
    AcademicStructureManager,
)


logger = logging.getLogger("BookWriterAI")


@dataclass
class BookConfig:
    """
    Simplified book configuration.
    
    Provides a user-friendly interface for configuring book generation
    while internally creating the full BookWriterConfig.
    """
    # Basic settings
    title: str
    genre: str = "literary_fiction"
    subgenre: Optional[str] = None
    target_length: int = 80000  # words
    target_audience: str = "general"
    
    # Content type
    content_type: str = "fiction"  # fiction, non_fiction, technical, academic
    
    # Style settings
    style: str = "literary"  # literary, commercial, academic, technical
    tone: Optional[str] = None
    pov: str = "third_limited"  # first_person, third_limited, third_omniscient
    tense: str = "past"  # past, present
    
    # Quality settings
    enable_refinement: bool = True
    max_refinement_iterations: int = 3
    quality_threshold: float = 0.85
    
    # Features
    enable_character_tracking: bool = True
    enable_emotional_arcs: bool = True
    enable_fact_checking: bool = False
    
    # RAG settings
    context_documents: List[str] = field(default_factory=list)
    
    # Output
    output_format: str = "markdown"
    output_path: str = "output"
    
    # LLM settings
    llm_provider: str = "openai"
    llm_model: Optional[str] = None
    api_key: Optional[str] = None
    
    def to_full_config(self) -> BookWriterConfig:
        """Convert to full BookWriterConfig."""
        return BookWriterConfig(
            title=self.title,
            genre=self.genre,
            subgenre=self.subgenre,
            target_length=self.target_length,
            target_audience=self.target_audience,
            content_type=self.content_type,
            pov=self.pov,
            tense=self.tense,
            enable_refinement=self.enable_refinement,
            max_refinement_iterations=self.max_refinement_iterations,
            quality_threshold=self.quality_threshold,
            context_documents=self.context_documents,
            output_format=self.output_format,
            output_path=self.output_path,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            api_key=self.api_key,
        )


@dataclass
class GenerationProgress:
    """Progress information for book generation."""
    current_phase: str
    current_chapter: int
    total_chapters: int
    progress_percent: float
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "current_phase": self.current_phase,
            "current_chapter": self.current_chapter,
            "total_chapters": self.total_chapters,
            "progress_percent": self.progress_percent,
            "message": self.message,
            "timestamp": self.timestamp
        }


@dataclass
class Chapter:
    """Represents a generated chapter."""
    chapter_id: int
    title: str
    content: str
    word_count: int
    quality_score: float
    summary: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "chapter_id": self.chapter_id,
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "quality_score": self.quality_score,
            "summary": self.summary,
            "events": self.events
        }


@dataclass
class Book:
    """Represents a generated book."""
    title: str
    author: str
    genre: str
    chapters: List[Chapter]
    total_word_count: int
    generation_metadata: Dict[str, Any]
    quality_report: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "chapters": [c.to_dict() for c in self.chapters],
            "total_word_count": self.total_word_count,
            "generation_metadata": self.generation_metadata,
            "quality_report": self.quality_report
        }
    
    def to_markdown(self) -> str:
        """Convert book to markdown format."""
        lines = [
            f"# {self.title}",
            "",
            f"*by {self.author}*",
            "",
            "---",
            ""
        ]
        
        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for chapter in self.chapters:
            lines.append(f"- [Chapter {chapter.chapter_id}: {chapter.title}](#chapter-{chapter.chapter_id})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Chapters
        for chapter in self.chapters:
            lines.append(f"## Chapter {chapter.chapter_id}: {chapter.title}")
            lines.append("")
            lines.append(chapter.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)


@dataclass
class BookGenerationResult:
    """Result of book generation."""
    success: bool
    book: Optional[Book]
    quality_report: Optional[Dict[str, Any]]
    generation_metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "book": self.book.to_dict() if self.book else None,
            "quality_report": self.quality_report,
            "generation_metadata": self.generation_metadata,
            "errors": self.errors
        }


class ProfessionalBookWriter:
    """
    Main API for professional book generation.
    
    Integrates all components of the BookWriterAI platform
    to provide comprehensive book generation capabilities.
    """
    
    def __init__(self, config: BookConfig):
        """
        Initialize the professional book writer.
        
        Args:
            config: Book configuration
        """
        self.config = config
        self.full_config = config.to_full_config()
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            provider=self.full_config.llm_provider,
            model=self.full_config.llm_model,
            api_key=self.full_config.api_key
        )
        
        # Initialize components
        self._init_components()
        
        # State
        self.current_book: Optional[Book] = None
        self.generation_history: List[Dict[str, Any]] = []
    
    def _init_components(self) -> None:
        """Initialize all components."""
        # Genre
        self.genre_manager = GenreTemplateManager()
        self.genre_template = self.genre_manager.get_template(
            self.config.genre,
            self.config.subgenre
        )
        
        # Style
        self.style_manager = StyleProfileManager()
        self.style_profile = self.style_manager.get_profile(self.config.style)
        if self.config.tone and self.style_profile:
            self.style_profile.primary_tone = self.config.tone
        
        self.style_injector = StylePromptInjector()
        self.style_validator = StyleValidator()
        
        # Narrative memory
        self.narrative_graph = NarrativeStateGraph()
        self.context_synthesizer = ContextSynthesizer(self.narrative_graph)
        
        # Emotional arcs
        if self.config.enable_emotional_arcs:
            self.emotional_planner = EmotionalArcPlanner()
            self.tension_manager = TensionManager()
        else:
            self.emotional_planner = None
            self.tension_manager = None
        
        # Characters
        if self.config.enable_character_tracking:
            self.dialogue_generator = DialogueGenerator({}, self.llm_client)
            self.character_validator = CharacterConsistencyValidator()
        else:
            self.dialogue_generator = None
            self.character_validator = None
        
        # Knowledge base
        self.knowledge_base = KnowledgeBase()
        self.context_assembler = ContextAssembler()
        
        # Load context documents
        for doc_path in self.config.context_documents:
            try:
                self.knowledge_base.add_document(doc_path)
            except Exception as e:
                logger.warning(f"Failed to load document {doc_path}: {e}")
        
        # Refinement
        if self.config.enable_refinement:
            self.quality_assessor = QualityAssessor(self.llm_client)
            self.refinement_pipeline = IterativeRefinementPipeline(
                llm_client=self.llm_client,
                max_iterations=self.config.max_refinement_iterations,
                quality_threshold=self.config.quality_threshold
            )
        else:
            self.quality_assessor = None
            self.refinement_pipeline = None
        
        # Technical support
        if self.config.content_type in ["technical", "academic"]:
            self.citation_manager = CitationManager()
            self.fact_verifier = FactVerificationSystem() if self.config.enable_fact_checking else None
            self.academic_manager = AcademicStructureManager()
        else:
            self.citation_manager = None
            self.fact_verifier = None
            self.academic_manager = None
    
    def generate_book(
        self,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None
    ) -> BookGenerationResult:
        """
        Generate a complete book.
        
        Args:
            progress_callback: Optional callback for progress updates
        
        Returns:
            BookGenerationResult with the generated book
        """
        start_time = datetime.now()
        errors = []
        
        try:
            # Phase 1: Planning
            self._report_progress(
                progress_callback, "planning", 0, 0, 0.0, "Planning book structure..."
            )
            
            outline = self._generate_outline()
            total_chapters = len(outline.get("chapters", []))
            
            # Phase 2: Generate chapters
            chapters = []
            for i, chapter_info in enumerate(outline.get("chapters", [])):
                self._report_progress(
                    progress_callback,
                    "generation",
                    i + 1,
                    total_chapters,
                    (i + 1) / total_chapters * 0.9,
                    f"Generating Chapter {i + 1}: {chapter_info.get('title', '')}"
                )
                
                chapter = self._generate_chapter(i + 1, chapter_info)
                chapters.append(chapter)
            
            # Phase 3: Final refinement
            self._report_progress(
                progress_callback, "refinement", 0, 0, 0.95, "Final quality check..."
            )
            
            quality_report = self._assess_book_quality(chapters)
            
            # Create book object
            total_words = sum(c.word_count for c in chapters)
            
            self.current_book = Book(
                title=self.config.title,
                author="BookWriterAI",
                genre=self.config.genre,
                chapters=chapters,
                total_word_count=total_words,
                generation_metadata={
                    "config": self.config.to_full_config().to_dict(),
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "genre_template": self.genre_template.genre_name if self.genre_template else None,
                    "style_profile": self.style_profile.name if self.style_profile else None
                },
                quality_report=quality_report
            )
            
            self._report_progress(
                progress_callback, "complete", 0, 0, 1.0, "Book generation complete!"
            )
            
            return BookGenerationResult(
                success=True,
                book=self.current_book,
                quality_report=quality_report,
                generation_metadata=self.current_book.generation_metadata
            )
            
        except Exception as e:
            logger.error(f"Book generation failed: {e}")
            errors.append(str(e))
            
            return BookGenerationResult(
                success=False,
                book=self.current_book,
                quality_report=None,
                generation_metadata={
                    "error": str(e),
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat()
                },
                errors=errors
            )
    
    def _report_progress(
        self,
        callback: Optional[Callable[[GenerationProgress], None]],
        phase: str,
        current_chapter: int,
        total_chapters: int,
        percent: float,
        message: str
    ) -> None:
        """Report progress to callback if provided."""
        if callback:
            progress = GenerationProgress(
                current_phase=phase,
                current_chapter=current_chapter,
                total_chapters=total_chapters,
                progress_percent=percent,
                message=message
            )
            callback(progress)
    
    def _generate_outline(self) -> Dict[str, Any]:
        """Generate book outline."""
        # Calculate number of chapters based on target length
        avg_chapter_length = 3000  # words
        num_chapters = max(5, self.config.target_length // avg_chapter_length)
        
        # Get genre-specific structure if available
        if self.genre_template and self.genre_template.act_structure:
            acts = self.genre_template.act_structure.acts
            chapters_per_act = num_chapters // len(acts)
        else:
            acts = []
            chapters_per_act = num_chapters
        
        # Generate outline via LLM
        prompt = self._build_outline_prompt(num_chapters)
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            # Parse outline from response
            outline = self._parse_outline_response(response, num_chapters)
            
        except Exception as e:
            logger.warning(f"LLM outline generation failed, using default: {e}")
            outline = self._create_default_outline(num_chapters)
        
        return outline
    
    def _build_outline_prompt(self, num_chapters: int) -> str:
        """Build prompt for outline generation."""
        prompt_parts = [
            f"Create a detailed outline for a {self.config.genre} book titled '{self.config.title}'.",
            f"Target length: {self.config.target_length} words.",
            f"Number of chapters: {num_chapters}.",
            f"Style: {self.config.style}.",
            f"POV: {self.config.pov}.",
            ""
        ]
        
        if self.genre_template:
            prompt_parts.append(
                f"Genre conventions: {', '.join(self.genre_template.required_elements[:5])}"
            )
        
        prompt_parts.extend([
            "",
            "For each chapter, provide:",
            "- Chapter number and title",
            "- Brief summary (2-3 sentences)",
            "- Key events",
            "- Emotional tone",
            "",
            "Format as JSON with 'chapters' array."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_outline_response(
        self,
        response: str,
        num_chapters: int
    ) -> Dict[str, Any]:
        """Parse outline from LLM response."""
        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                outline = json.loads(response[json_start:json_end])
                return outline
        except (json.JSONDecodeError, ValueError):
            pass
        
        return self._create_default_outline(num_chapters)
    
    def _create_default_outline(self, num_chapters: int) -> Dict[str, Any]:
        """Create a default outline structure."""
        chapters = []
        
        for i in range(num_chapters):
            position = i / num_chapters
            
            if position < 0.25:
                phase = "Setup"
            elif position < 0.5:
                phase = "Rising Action"
            elif position < 0.75:
                phase = "Climax"
            else:
                phase = "Resolution"
            
            chapters.append({
                "chapter_id": i + 1,
                "title": f"Chapter {i + 1}",
                "summary": f"Events continue in the {phase.lower()} phase.",
                "key_events": [],
                "emotional_tone": "neutral",
                "phase": phase
            })
        
        return {
            "title": self.config.title,
            "genre": self.config.genre,
            "chapters": chapters
        }
    
    def _generate_chapter(
        self,
        chapter_id: int,
        chapter_info: Dict[str, Any]
    ) -> Chapter:
        """Generate a single chapter."""
        # Get narrative context
        narrative_context = self.context_synthesizer.synthesize_context(
            current_chapter=chapter_id,
            chapter_info=chapter_info,
            max_tokens=2000
        )
        
        # Build chapter prompt
        prompt = self._build_chapter_prompt(chapter_id, chapter_info, narrative_context)
        
        # Generate content
        response = self.llm_client.generate(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.8
        )
        
        content = response.strip()
        word_count = len(content.split())
        
        # Apply refinement if enabled
        quality_score = 0.0
        if self.refinement_pipeline:
            result = self.refinement_pipeline.refine_chapter(
                content=content,
                chapter_info=chapter_info,
                style_profile=self.style_profile
            )
            content = result.final_content
            word_count = len(content.split())
            quality_score = result.final_quality_score
        else:
            quality_score = 0.75  # Default score without refinement
        
        # Extract events and update narrative state
        events = self._extract_chapter_events(content, chapter_id)
        for event in events:
            self.narrative_graph.add_event(event)
        
        return Chapter(
            chapter_id=chapter_id,
            title=chapter_info.get("title", f"Chapter {chapter_id}"),
            content=content,
            word_count=word_count,
            quality_score=quality_score,
            summary=chapter_info.get("summary", ""),
            events=events
        )
    
    def _build_chapter_prompt(
        self,
        chapter_id: int,
        chapter_info: Dict[str, Any],
        narrative_context: Any
    ) -> str:
        """Build prompt for chapter generation."""
        prompt_parts = []
        
        # Style instructions
        if self.style_profile:
            style_instructions = self.style_injector.create_style_prompt(
                self.style_profile,
                "narration",
                chapter_info.get("summary", "")
            )
            prompt_parts.append(style_instructions)
            prompt_parts.append("")
        
        # Context
        prompt_parts.append(f"Book: {self.config.title}")
        prompt_parts.append(f"Genre: {self.config.genre}")
        prompt_parts.append(f"Chapter {chapter_id}: {chapter_info.get('title', '')}")
        prompt_parts.append("")
        
        # Chapter info
        if chapter_info.get("summary"):
            prompt_parts.append(f"Chapter summary: {chapter_info['summary']}")
            prompt_parts.append("")
        
        if chapter_info.get("key_events"):
            prompt_parts.append("Key events to include:")
            for event in chapter_info["key_events"]:
                prompt_parts.append(f"- {event}")
            prompt_parts.append("")
        
        # Narrative context
        if narrative_context and hasattr(narrative_context, 'relevant_events'):
            if narrative_context.relevant_events:
                prompt_parts.append("Previous events to reference:")
                for event in narrative_context.relevant_events[:3]:
                    prompt_parts.append(f"- {event.description}")
                prompt_parts.append("")
        
        # Target length
        target_words = self.config.target_length // 10  # Approximate words per chapter
        prompt_parts.append(f"Target length: approximately {target_words} words")
        prompt_parts.append("")
        
        prompt_parts.append("Write the complete chapter content:")
        
        return "\n".join(prompt_parts)
    
    def _extract_chapter_events(
        self,
        content: str,
        chapter_id: int
    ) -> List[Dict[str, Any]]:
        """Extract narrative events from chapter content."""
        # This is a simplified extraction
        # In production, this would use NLP or LLM-based extraction
        events = []
        
        # Simple sentence-based event detection
        sentences = content.split(". ")
        for i, sentence in enumerate(sentences[:10]):  # Limit to first 10
            if len(sentence) > 20 and any(
                keyword in sentence.lower()
                for keyword in ["said", "did", "went", "saw", "felt", "thought"]
            ):
                events.append({
                    "event_id": f"ch{chapter_id}_e{i}",
                    "description": sentence[:200],
                    "chapter_id": chapter_id,
                    "importance": 0.5
                })
        
        return events
    
    def _assess_book_quality(
        self,
        chapters: List[Chapter]
    ) -> Dict[str, Any]:
        """Assess overall book quality."""
        if not self.quality_assessor:
            return {"overall_score": 0.75, "note": "Quality assessment disabled"}
        
        # Calculate average chapter quality
        scores = [c.quality_score for c in chapters]
        avg_score = sum(scores) / len(scores) if scores else 0.75
        
        # Check consistency
        if scores:
            score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            consistency = max(0, 1 - score_variance)
        else:
            consistency = 1.0
        
        return {
            "overall_score": avg_score,
            "consistency_score": consistency,
            "chapter_scores": scores,
            "total_chapters": len(chapters),
            "total_words": sum(c.word_count for c in chapters)
        }
    
    def generate_outline_only(self) -> Dict[str, Any]:
        """Generate book outline without full content."""
        return self._generate_outline()
    
    def generate_chapter(
        self,
        chapter_id: int,
        chapter_info: Optional[Dict[str, Any]] = None
    ) -> Chapter:
        """Generate a single chapter."""
        if not chapter_info:
            chapter_info = {
                "title": f"Chapter {chapter_id}",
                "summary": ""
            }
        return self._generate_chapter(chapter_id, chapter_info)
    
    def refine_chapter(
        self,
        chapter: Chapter,
        quality_issues: Optional[List[Dict[str, Any]]] = None
    ) -> Chapter:
        """Refine an existing chapter."""
        if not self.refinement_pipeline:
            return chapter
        
        result = self.refinement_pipeline.refine_chapter(
            content=chapter.content,
            chapter_info={"title": chapter.title},
            style_profile=self.style_profile
        )
        
        return Chapter(
            chapter_id=chapter.chapter_id,
            title=chapter.title,
            content=result.final_content,
            word_count=len(result.final_content.split()),
            quality_score=result.final_quality_score,
            summary=chapter.summary,
            events=chapter.events
        )
    
    def export_book(
        self,
        book: Book,
        format: str,
        output_path: str
    ) -> str:
        """
        Export book to specified format.
        
        Args:
            book: Book to export
            format: Output format (markdown, json, txt)
            output_path: Path to save the file
        
        Returns:
            Path to the exported file
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        if format == "markdown" or format == "md":
            content = book.to_markdown()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        elif format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(book.to_dict(), f, indent=2)
        
        elif format == "txt":
            content = book.to_markdown()
            # Remove markdown formatting
            content = content.replace("#", "").replace("*", "")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return output_path


# Convenience function
def generate_book(
    title: str,
    genre: str = "literary_fiction",
    target_length: int = 80000,
    **kwargs
) -> BookGenerationResult:
    """
    Convenience function to generate a book.
    
    Args:
        title: Book title
        genre: Book genre
        target_length: Target word count
        **kwargs: Additional configuration options
    
    Returns:
        BookGenerationResult
    """
    config = BookConfig(
        title=title,
        genre=genre,
        target_length=target_length,
        **kwargs
    )
    
    writer = ProfessionalBookWriter(config)
    return writer.generate_book()


__all__ = [
    "BookConfig",
    "GenerationProgress",
    "Chapter",
    "Book",
    "BookGenerationResult",
    "ProfessionalBookWriter",
    "generate_book",
]