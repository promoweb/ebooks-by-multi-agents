"""
Iterative Refinement Pipeline for BookWriterAI.

This module provides iterative refinement capabilities for
improving generated content through multiple passes.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class RefinementType(Enum):
    """Types of refinement operations."""
    STRUCTURAL = "structural"  # Pacing, section balance, transitions
    PROSE = "prose"  # Sentence variety, word choice, flow
    CONSISTENCY = "consistency"  # Character, timeline, fact checking
    STYLE = "style"  # Style profile compliance
    EXPANSION = "expansion"  # Add detail and depth
    COMPRESSION = "compression"  # Reduce redundancy


@dataclass
class RefinementResult:
    """Result of a refinement operation."""
    original_content: str
    refined_content: str
    refinement_type: RefinementType
    iterations: int
    initial_score: float
    final_score: float
    improvement: float
    changes_made: List[str] = field(default_factory=list)
    issues_addressed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "original_content": self.original_content[:500] + "..." if len(self.original_content) > 500 else self.original_content,
            "refined_content": self.refined_content[:500] + "..." if len(self.refined_content) > 500 else self.refined_content,
            "refinement_type": self.refinement_type.value,
            "iterations": self.iterations,
            "initial_score": self.initial_score,
            "final_score": self.final_score,
            "improvement": self.improvement,
            "changes_made": self.changes_made,
            "issues_addressed": self.issues_addressed
        }


@dataclass
class PipelineConfig:
    """Configuration for the refinement pipeline."""
    max_iterations: int = 3
    quality_threshold: float = 0.85
    convergence_threshold: float = 0.02  # Stop if improvement < this
    enable_structural_refinement: bool = True
    enable_prose_refinement: bool = True
    enable_consistency_correction: bool = True
    enable_style_correction: bool = True
    min_content_length: int = 100  # Minimum words to refine


class StructuralRefiner:
    """
    Refines content structure.
    
    Addresses:
    - Pacing problems
    - Section balance
    - Transition quality
    - Information flow
    """
    
    def __init__(self, llm_client=None):
        """Initialize structural refiner."""
        self.llm_client = llm_client
    
    def refine(
        self,
        content: str,
        quality_issues: List[Any]
    ) -> tuple:
        """
        Refine content structure.
        
        Args:
            content: Content to refine
            quality_issues: List of quality issues to address
        
        Returns:
            Tuple of (refined_content, changes_made)
        """
        if not self.llm_client:
            return content, []
        
        # Filter structural issues
        structural_issues = [
            i for i in quality_issues
            if hasattr(i, 'issue_type') and i.issue_type in [
                'pacing', 'section_balance', 'transitions', 'flow'
            ]
        ]
        
        if not structural_issues:
            return content, []
        
        # Build refinement prompt
        issues_desc = "\n".join(
            f"- {i.description}" for i in structural_issues
        )
        
        prompt = f"""Improve the structure of the following content while maintaining its meaning and style.

Issues to address:
{issues_desc}

Content:
{content}

Improved content:"""
        
        try:
            refined = self.llm_client.generate(
                prompt,
                max_tokens=len(content.split()) + 500
            )
            
            changes = [
                f"Addressed: {i.description}"
                for i in structural_issues
            ]
            
            return refined.strip(), changes
        
        except Exception as e:
            logger.warning(f"Structural refinement failed: {e}")
            return content, []


class ProseRefiner:
    """
    Refines prose quality.
    
    Addresses:
    - Sentence variety
    - Word choice
    - Figurative language
    - Rhythm and flow
    """
    
    def __init__(self, llm_client=None):
        """Initialize prose refiner."""
        self.llm_client = llm_client
    
    def refine(
        self,
        content: str,
        style_profile: Optional[Any] = None,
        quality_issues: List[Any] = None
    ) -> tuple:
        """
        Refine prose quality.
        
        Args:
            content: Content to refine
            style_profile: Target style profile
            quality_issues: List of quality issues
        
        Returns:
            Tuple of (refined_content, changes_made)
        """
        if not self.llm_client:
            return content, []
        
        quality_issues = quality_issues or []
        
        # Filter prose issues
        prose_issues = [
            i for i in quality_issues
            if hasattr(i, 'issue_type') and i.issue_type in [
                'repetitive_starts', 'passive_voice', 'word_choice',
                'sentence_variety', 'prose_quality'
            ]
        ]
        
        # Build refinement prompt
        issues_desc = ""
        if prose_issues:
            issues_desc = "\nIssues to address:\n" + "\n".join(
                f"- {i.description}" for i in prose_issues
            )
        
        style_guidance = ""
        if style_profile:
            style_guidance = f"\nTarget style: {style_profile.name}\n"
            style_guidance += f"Average sentence length: {style_profile.average_sentence_length} words\n"
        
        prompt = f"""Improve the prose quality of the following content.
{style_guidance}
{issues_desc}

Maintain the same meaning and narrative voice. Focus on:
- Varying sentence structure
- Using active voice
- Improving word choice
- Enhancing rhythm and flow

Content:
{content}

Improved content:"""
        
        try:
            refined = self.llm_client.generate(
                prompt,
                max_tokens=len(content.split()) + 500
            )
            
            changes = []
            if prose_issues:
                changes.extend([
                    f"Addressed: {i.description}"
                    for i in prose_issues
                ])
            else:
                changes.append("General prose improvement")
            
            return refined.strip(), changes
        
        except Exception as e:
            logger.warning(f"Prose refinement failed: {e}")
            return content, []


class ConsistencyCorrector:
    """
    Corrects consistency issues.
    
    Addresses:
    - Character behavior
    - Timeline errors
    - Fact contradictions
    - Name inconsistencies
    """
    
    def __init__(self, llm_client=None, narrative_state=None):
        """
        Initialize consistency corrector.
        
        Args:
            llm_client: LLM client for corrections
            narrative_state: Narrative state for context
        """
        self.llm_client = llm_client
        self.narrative_state = narrative_state
    
    def correct(
        self,
        content: str,
        narrative_context: Optional[Any] = None,
        consistency_issues: List[Any] = None
    ) -> tuple:
        """
        Correct consistency issues.
        
        Args:
            content: Content to correct
            narrative_context: Narrative context for validation
            consistency_issues: List of consistency issues
        
        Returns:
            Tuple of (corrected_content, changes_made)
        """
        if not self.llm_client:
            return content, []
        
        consistency_issues = consistency_issues or []
        
        if not consistency_issues:
            return content, []
        
        # Build correction prompt
        issues_desc = "\n".join(
            f"- {i.description}" for i in consistency_issues
            if hasattr(i, 'description')
        )
        
        context_info = ""
        if narrative_context:
            # Add relevant context
            if hasattr(narrative_context, 'active_entities'):
                entities = narrative_context.active_entities
                if entities:
                    context_info += "\nKnown characters:\n"
                    for entity in entities[:5]:
                        context_info += f"- {getattr(entity, 'name', str(entity))}\n"
        
        prompt = f"""Correct the consistency issues in the following content.
{context_info}

Issues to fix:
{issues_desc}

Content:
{content}

Corrected content:"""
        
        try:
            corrected = self.llm_client.generate(
                prompt,
                max_tokens=len(content.split()) + 200
            )
            
            changes = [
                f"Fixed: {i.description}"
                for i in consistency_issues
                if hasattr(i, 'description')
            ]
            
            return corrected.strip(), changes
        
        except Exception as e:
            logger.warning(f"Consistency correction failed: {e}")
            return content, []


class IterativeRefinementPipeline:
    """
    Manages iterative refinement process.
    
    Process:
    1. Assess quality
    2. If quality >= threshold, return
    3. Identify issues
    4. Apply targeted refinements
    5. Re-assess
    6. Check convergence
    7. Repeat or return
    """
    
    def __init__(
        self,
        llm_client=None,
        quality_assessor=None,
        style_validator=None,
        narrative_state=None,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the refinement pipeline.
        
        Args:
            llm_client: LLM client for refinements
            quality_assessor: QualityAssessor instance
            style_validator: StyleValidator instance
            narrative_state: Narrative state for context
            config: Pipeline configuration
        """
        self.llm_client = llm_client
        self.quality_assessor = quality_assessor
        self.style_validator = style_validator
        self.narrative_state = narrative_state
        self.config = config or PipelineConfig()
        
        # Initialize refiners
        self.structural_refiner = StructuralRefiner(llm_client)
        self.prose_refiner = ProseRefiner(llm_client)
        self.consistency_corrector = ConsistencyCorrector(
            llm_client, narrative_state
        )
    
    def refine_chapter(
        self,
        initial_content: str,
        chapter_info: Dict[str, Any],
        narrative_context: Optional[Any] = None,
        style_profile: Optional[Any] = None,
        progress_callback: Optional[Callable] = None
    ) -> RefinementResult:
        """
        Iteratively refine chapter until quality threshold met.
        
        Args:
            initial_content: Initial chapter content
            chapter_info: Information about the chapter
            narrative_context: Current narrative state
            style_profile: Target style profile
            progress_callback: Optional callback for progress updates
        
        Returns:
            RefinementResult with refined content and metrics
        """
        # Check minimum length
        word_count = len(initial_content.split())
        if word_count < self.config.min_content_length:
            logger.warning(
                f"Content too short for refinement ({word_count} words)"
            )
            return RefinementResult(
                original_content=initial_content,
                refined_content=initial_content,
                refinement_type=RefinementType.PROSE,
                iterations=0,
                initial_score=0.0,
                final_score=0.0,
                improvement=0.0,
                changes_made=["Content too short for refinement"]
            )
        
        # Initial assessment
        initial_score = self._assess_quality(
            initial_content, chapter_info, narrative_context, style_profile
        )
        
        current_content = initial_content
        current_score = initial_score
        all_changes: List[str] = []
        all_issues_addressed: List[str] = []
        
        iteration = 0
        previous_score = 0.0
        
        while iteration < self.config.max_iterations:
            # Check if quality threshold met
            if current_score >= self.config.quality_threshold:
                logger.info(
                    f"Quality threshold met at iteration {iteration}"
                )
                break
            
            # Check for convergence
            if iteration > 0:
                improvement = current_score - previous_score
                if improvement < self.config.convergence_threshold:
                    logger.info(
                        f"Converged at iteration {iteration} "
                        f"(improvement: {improvement:.4f})"
                    )
                    break
            
            previous_score = current_score
            
            # Get current issues
            quality_result = self._get_quality_issues(
                current_content, chapter_info, narrative_context, style_profile
            )
            
            if not quality_result or not quality_result.issues:
                break
            
            # Apply refinements
            refined_content, changes = self._apply_refinements(
                current_content,
                quality_result.issues,
                narrative_context,
                style_profile
            )
            
            if refined_content == current_content:
                # No changes made, stop iterating
                break
            
            current_content = refined_content
            all_changes.extend(changes)
            
            # Re-assess
            current_score = self._assess_quality(
                current_content, chapter_info, narrative_context, style_profile
            )
            
            # Track issues addressed
            for issue in quality_result.issues[:3]:  # Top 3 issues
                all_issues_addressed.append(issue.description)
            
            iteration += 1
            
            # Progress callback
            if progress_callback:
                progress_callback({
                    "iteration": iteration,
                    "score": current_score,
                    "improvement": current_score - initial_score
                })
        
        return RefinementResult(
            original_content=initial_content,
            refined_content=current_content,
            refinement_type=RefinementType.PROSE,  # Primary type
            iterations=iteration,
            initial_score=initial_score,
            final_score=current_score,
            improvement=current_score - initial_score,
            changes_made=all_changes,
            issues_addressed=all_issues_addressed
        )
    
    def _assess_quality(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        narrative_context: Optional[Any],
        style_profile: Optional[Any]
    ) -> float:
        """Assess content quality."""
        if self.quality_assessor:
            result = self.quality_assessor.assess_chapter(
                chapter_content=content,
                chapter_info=chapter_info,
                narrative_context=narrative_context,
                style_profile=style_profile
            )
            return result.overall_score
        
        # Simple heuristic if no assessor
        word_count = len(content.split())
        if word_count < 500:
            return 0.5
        elif word_count < 1000:
            return 0.6
        elif word_count < 2000:
            return 0.7
        else:
            return 0.75
    
    def _get_quality_issues(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        narrative_context: Optional[Any],
        style_profile: Optional[Any]
    ):
        """Get quality issues for content."""
        if self.quality_assessor:
            return self.quality_assessor.assess_chapter(
                chapter_content=content,
                chapter_info=chapter_info,
                narrative_context=narrative_context,
                style_profile=style_profile
            )
        
        # Return empty result if no assessor
        from src.refinement.quality import QualityScore
        return QualityScore(issues=[])
    
    def _apply_refinements(
        self,
        content: str,
        quality_issues: List[Any],
        narrative_context: Optional[Any],
        style_profile: Optional[Any]
    ) -> tuple:
        """
        Apply appropriate refinements based on issues.
        
        Returns:
            Tuple of (refined_content, changes_made)
        """
        current_content = content
        all_changes = []
        
        # Categorize issues
        structural_issues = []
        prose_issues = []
        consistency_issues = []
        style_issues = []
        
        for issue in quality_issues:
            if not hasattr(issue, 'issue_type'):
                continue
            
            issue_type = issue.issue_type
            
            if issue_type in ['pacing', 'section_balance', 'transitions']:
                structural_issues.append(issue)
            elif issue_type in ['repetitive_starts', 'passive_voice', 'prose_quality']:
                prose_issues.append(issue)
            elif issue_type in ['character_consistency', 'timeline', 'facts']:
                consistency_issues.append(issue)
            elif issue_type in ['style_violation', 'tone', 'vocabulary']:
                style_issues.append(issue)
        
        # Apply structural refinement
        if structural_issues and self.config.enable_structural_refinement:
            refined, changes = self.structural_refiner.refine(
                current_content, structural_issues
            )
            if refined != current_content:
                current_content = refined
                all_changes.extend(changes)
        
        # Apply prose refinement
        if prose_issues and self.config.enable_prose_refinement:
            refined, changes = self.prose_refiner.refine(
                current_content, style_profile, prose_issues
            )
            if refined != current_content:
                current_content = refined
                all_changes.extend(changes)
        
        # Apply consistency correction
        if consistency_issues and self.config.enable_consistency_correction:
            corrected, changes = self.consistency_corrector.correct(
                current_content, narrative_context, consistency_issues
            )
            if corrected != current_content:
                current_content = corrected
                all_changes.extend(changes)
        
        return current_content, all_changes
    
    def refine_book(
        self,
        chapters: List[Dict[str, Any]],
        narrative_context: Optional[Any] = None,
        style_profile: Optional[Any] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[RefinementResult]:
        """
        Refine all chapters in a book.
        
        Args:
            chapters: List of chapter dictionaries
            narrative_context: Narrative state
            style_profile: Target style profile
            progress_callback: Progress callback
        
        Returns:
            List of RefinementResult for each chapter
        """
        results = []
        
        for i, chapter in enumerate(chapters):
            content = chapter.get("content", "")
            info = chapter.get("info", {})
            info["chapter_number"] = i + 1
            info["total_chapters"] = len(chapters)
            
            result = self.refine_chapter(
                initial_content=content,
                chapter_info=info,
                narrative_context=narrative_context,
                style_profile=style_profile,
                progress_callback=progress_callback
            )
            
            results.append(result)
            
            # Update chapter content
            chapter["content"] = result.refined_content
        
        return results


__all__ = [
    "RefinementType",
    "RefinementResult",
    "PipelineConfig",
    "StructuralRefiner",
    "ProseRefiner",
    "ConsistencyCorrector",
    "IterativeRefinementPipeline",
]