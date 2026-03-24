"""
Quality Assessment Layer for BookWriterAI.

This module provides multi-dimensional quality assessment for
generated content including narrative coherence, stylistic
consistency, and content depth.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from collections import Counter


logger = logging.getLogger("BookWriterAI")


class QualityDimension(Enum):
    """Dimensions of quality assessment."""
    NARRATIVE_COHERENCE = "narrative_coherence"
    STYLISTIC_CONSISTENCY = "stylistic_consistency"
    CONTENT_DEPTH = "content_depth"
    CHARACTER_CONSISTENCY = "character_consistency"
    PLOT_PROGRESSION = "plot_progression"
    EMOTIONAL_RESONANCE = "emotional_resonance"
    PROSE_QUALITY = "prose_quality"


class IssueSeverity(Enum):
    """Severity levels for quality issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Identified quality problem."""
    issue_type: str
    severity: IssueSeverity
    dimension: QualityDimension
    location: str  # Text location or description
    description: str
    suggested_fix: str
    context: str = ""  # Surrounding text for context
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity.value,
            "dimension": self.dimension.value,
            "location": self.location,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "context": self.context
        }


@dataclass
class QualityScore:
    """Multi-dimensional quality assessment."""
    narrative_coherence: float = 0.0  # 0.0 to 1.0
    stylistic_consistency: float = 0.0
    content_depth: float = 0.0
    character_consistency: float = 0.0
    plot_progression: float = 0.0
    emotional_resonance: float = 0.0
    prose_quality: float = 0.0
    overall_score: float = 0.0
    issues: List[QualityIssue] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "narrative_coherence": self.narrative_coherence,
            "stylistic_consistency": self.stylistic_consistency,
            "content_depth": self.content_depth,
            "character_consistency": self.character_consistency,
            "plot_progression": self.plot_progression,
            "emotional_resonance": self.emotional_resonance,
            "prose_quality": self.prose_quality,
            "overall_score": self.overall_score,
            "issues": [i.to_dict() for i in self.issues]
        }
    
    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Check if quality meets threshold."""
        return self.overall_score >= threshold
    
    def get_critical_issues(self) -> List['QualityIssue']:
        """Get only critical and high severity issues."""
        return [
            i for i in self.issues
            if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
        ]


@dataclass
class BookQualityReport:
    """Quality report for an entire book."""
    chapter_scores: List[QualityScore] = field(default_factory=list)
    overall_coherence: float = 0.0
    consistency_issues: List[QualityIssue] = field(default_factory=list)
    pacing_analysis: Dict[str, Any] = field(default_factory=dict)
    character_arc_analysis: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def average_score(self) -> float:
        """Calculate average score across chapters."""
        if not self.chapter_scores:
            return 0.0
        return sum(s.overall_score for s in self.chapter_scores) / len(self.chapter_scores)


class QualityAssessor:
    """
    Multi-dimensional quality assessment.
    
    Evaluates content across multiple dimensions:
    - Narrative coherence
    - Stylistic consistency
    - Content depth
    - Character consistency
    - Plot progression
    - Emotional resonance
    - Prose quality
    """
    
    def __init__(self, llm_client=None, style_validator=None):
        """
        Initialize the quality assessor.
        
        Args:
            llm_client: LLM client for advanced assessment
            style_validator: StyleValidator for style checks
        """
        self.llm_client = llm_client
        self.style_validator = style_validator
    
    def assess_chapter(
        self,
        chapter_content: str,
        chapter_info: Dict[str, Any],
        narrative_context: Optional[Any] = None,
        style_profile: Optional[Any] = None
    ) -> QualityScore:
        """
        Perform comprehensive quality assessment.
        
        Args:
            chapter_content: The chapter text to assess
            chapter_info: Information about the chapter
            narrative_context: Current narrative state
            style_profile: Target style profile
        
        Returns:
            QualityScore with multi-dimensional assessment
        """
        if not chapter_content or not chapter_content.strip():
            return QualityScore(
                overall_score=0.0,
                issues=[QualityIssue(
                    issue_type="empty_content",
                    severity=IssueSeverity.CRITICAL,
                    dimension=QualityDimension.CONTENT_DEPTH,
                    location="entire chapter",
                    description="Chapter content is empty",
                    suggested_fix="Generate chapter content"
                )]
            )
        
        issues: List[QualityIssue] = []
        
        # Assess each dimension
        narrative_score = self._assess_narrative_coherence(
            chapter_content, narrative_context, issues
        )
        
        style_score = self._assess_stylistic_consistency(
            chapter_content, style_profile, issues
        )
        
        depth_score = self._assess_content_depth(
            chapter_content, chapter_info, issues
        )
        
        character_score = self._assess_character_consistency(
            chapter_content, narrative_context, issues
        )
        
        plot_score = self._assess_plot_progression(
            chapter_content, chapter_info, narrative_context, issues
        )
        
        emotional_score = self._assess_emotional_resonance(
            chapter_content, chapter_info, issues
        )
        
        prose_score = self._assess_prose_quality(
            chapter_content, issues
        )
        
        # Calculate overall score
        overall = self._calculate_overall(
            narrative_score,
            style_score,
            depth_score,
            character_score,
            plot_score,
            emotional_score,
            prose_score
        )
        
        return QualityScore(
            narrative_coherence=narrative_score,
            stylistic_consistency=style_score,
            content_depth=depth_score,
            character_consistency=character_score,
            plot_progression=plot_score,
            emotional_resonance=emotional_score,
            prose_quality=prose_score,
            overall_score=overall,
            issues=issues
        )
    
    def assess_book(
        self,
        chapters: List[Dict[str, Any]],
        narrative_state: Optional[Any] = None
    ) -> BookQualityReport:
        """
        Assess entire book for coherence and quality.
        
        Args:
            chapters: List of chapter dictionaries with content and info
            narrative_state: Final narrative state
        
        Returns:
            BookQualityReport with comprehensive analysis
        """
        report = BookQualityReport()
        
        # Assess each chapter
        for chapter in chapters:
            content = chapter.get("content", "")
            info = chapter.get("info", {})
            
            score = self.assess_chapter(
                chapter_content=content,
                chapter_info=info,
                narrative_context=narrative_state
            )
            report.chapter_scores.append(score)
        
        # Analyze overall coherence
        report.overall_coherence = self._analyze_book_coherence(chapters)
        
        # Analyze pacing
        report.pacing_analysis = self._analyze_pacing(chapters)
        
        # Analyze character arcs
        report.character_arc_analysis = self._analyze_character_arcs(
            chapters, narrative_state
        )
        
        # Find cross-chapter consistency issues
        report.consistency_issues = self._find_consistency_issues(chapters)
        
        return report
    
    def _assess_narrative_coherence(
        self,
        content: str,
        narrative_context: Optional[Any],
        issues: List[QualityIssue]
    ) -> float:
        """Assess narrative coherence."""
        score = 0.8  # Start with high score, reduce for issues
        
        # Check for basic coherence
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if len(paragraphs) < 3:
            issues.append(QualityIssue(
                issue_type="thin_content",
                severity=IssueSeverity.MEDIUM,
                dimension=QualityDimension.NARRATIVE_COHERENCE,
                location="entire chapter",
                description="Chapter has very few paragraphs",
                suggested_fix="Expand chapter content with more development"
            ))
            score -= 0.2
        
        # Check for transition words
        transition_words = [
            'however', 'therefore', 'meanwhile', 'subsequently',
            'nevertheless', 'furthermore', 'moreover', 'consequently'
        ]
        content_lower = content.lower()
        transition_count = sum(1 for w in transition_words if w in content_lower)
        
        if transition_count < 2 and len(content) > 1000:
            issues.append(QualityIssue(
                issue_type="lacking_transitions",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.NARRATIVE_COHERENCE,
                location="throughout",
                description="Few transition words between ideas",
                suggested_fix="Add transition words to improve flow"
            ))
            score -= 0.1
        
        # Check for unresolved references
        pronouns = re.findall(r'\b(he|she|it|they)\b', content, re.IGNORECASE)
        # This is simplified - would need more sophisticated analysis
        
        return max(0.0, min(1.0, score))
    
    def _assess_stylistic_consistency(
        self,
        content: str,
        style_profile: Optional[Any],
        issues: List[QualityIssue]
    ) -> float:
        """Assess stylistic consistency."""
        if not style_profile:
            return 0.7  # Default score if no profile
        
        if self.style_validator:
            report = self.style_validator.validate(content, style_profile)
            
            # Convert style violations to quality issues
            for violation in report.violations:
                issues.append(QualityIssue(
                    issue_type=violation.violation_type,
                    severity=IssueSeverity(violation.severity),
                    dimension=QualityDimension.STYLISTIC_CONSISTENCY,
                    location=violation.location,
                    description=violation.description,
                    suggested_fix=violation.suggestion
                ))
            
            return report.overall_score
        
        return 0.7
    
    def _assess_content_depth(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        """Assess content depth and substance."""
        score = 0.7
        
        # Check word count
        word_count = len(content.split())
        
        if word_count < 500:
            issues.append(QualityIssue(
                issue_type="insufficient_length",
                severity=IssueSeverity.MEDIUM,
                dimension=QualityDimension.CONTENT_DEPTH,
                location="entire chapter",
                description=f"Chapter is too short ({word_count} words)",
                suggested_fix="Expand chapter with more detail and development"
            ))
            score -= 0.2
        elif word_count < 1000:
            score -= 0.1
        
        # Check for descriptive content
        descriptive_words = [
            'dark', 'bright', 'soft', 'hard', 'warm', 'cold',
            'beautiful', 'ugly', 'loud', 'quiet', 'sweet', 'bitter'
        ]
        content_lower = content.lower()
        descriptive_count = sum(1 for w in descriptive_words if w in content_lower)
        
        if descriptive_count < 5 and word_count > 500:
            issues.append(QualityIssue(
                issue_type="lacking_description",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.CONTENT_DEPTH,
                location="throughout",
                description="Content lacks descriptive language",
                suggested_fix="Add more sensory details and descriptions"
            ))
            score -= 0.1
        
        # Check for dialogue
        dialogue_matches = re.findall(r'"[^"]*"', content)
        if not dialogue_matches and word_count > 1000:
            issues.append(QualityIssue(
                issue_type="no_dialogue",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.CONTENT_DEPTH,
                location="entire chapter",
                description="Chapter has no dialogue",
                suggested_fix="Consider adding dialogue to bring characters to life"
            ))
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _assess_character_consistency(
        self,
        content: str,
        narrative_context: Optional[Any],
        issues: List[QualityIssue]
    ) -> float:
        """Assess character consistency."""
        score = 0.8
        
        # This would require integration with the character system
        # For now, do basic checks
        
        # Check for character names (capitalized words)
        potential_names = re.findall(r'\b[A-Z][a-z]+\b', content)
        # Filter out common sentence starters
        common_words = {'The', 'A', 'An', 'But', 'And', 'Or', 'So', 'Yet', 'Still', 
                       'Then', 'When', 'Where', 'What', 'Why', 'How', 'This', 'That', 
                       'These', 'Those', 'There', 'Here'}
        character_names = [n for n in set(potential_names) if n not in common_words]
        
        if len(character_names) > 10:
            # Many characters mentioned - could be confusing
            issues.append(QualityIssue(
                issue_type="many_characters",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.CHARACTER_CONSISTENCY,
                location="throughout",
                description=f"Many characters mentioned ({len(character_names)})",
                suggested_fix="Consider focusing on fewer characters for clarity"
            ))
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_plot_progression(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        narrative_context: Optional[Any],
        issues: List[QualityIssue]
    ) -> float:
        """Assess plot progression."""
        score = 0.75
        
        # Check for action/conflict indicators
        action_words = [
            'fought', 'ran', 'discovered', 'revealed', 'confronted',
            'escaped', 'attacked', 'defended', 'argued', 'decided'
        ]
        content_lower = content.lower()
        action_count = sum(1 for w in action_words if w in content_lower)
        
        if action_count < 2:
            issues.append(QualityIssue(
                issue_type="lacking_action",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.PLOT_PROGRESSION,
                location="throughout",
                description="Chapter lacks significant plot action",
                suggested_fix="Add events that advance the plot"
            ))
            score -= 0.1
        
        # Check chapter position for pacing expectations
        chapter_num = chapter_info.get("chapter_number", 0)
        total_chapters = chapter_info.get("total_chapters", 10)
        position = chapter_num / total_chapters if total_chapters > 0 else 0
        
        # Early chapters should establish, middle should develop, late should resolve
        # This is simplified - would need more sophisticated analysis
        
        return max(0.0, min(1.0, score))
    
    def _assess_emotional_resonance(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        issues: List[QualityIssue]
    ) -> float:
        """Assess emotional resonance."""
        score = 0.7
        
        # Check for emotional words
        emotional_words = [
            'love', 'hate', 'fear', 'joy', 'sadness', 'anger',
            'hope', 'despair', 'excitement', 'grief', 'passion',
            'terror', 'happiness', 'sorrow', 'rage'
        ]
        content_lower = content.lower()
        emotional_count = sum(1 for w in emotional_words if w in content_lower)
        
        word_count = len(content.split())
        emotional_ratio = emotional_count / (word_count / 100) if word_count > 0 else 0
        
        if emotional_ratio < 0.5:
            issues.append(QualityIssue(
                issue_type="lacking_emotion",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.EMOTIONAL_RESONANCE,
                location="throughout",
                description="Content lacks emotional depth",
                suggested_fix="Add more emotional content and character feelings"
            ))
            score -= 0.1
        elif emotional_ratio > 2:
            score += 0.1  # Bonus for emotional content
        
        return max(0.0, min(1.0, score))
    
    def _assess_prose_quality(
        self,
        content: str,
        issues: List[QualityIssue]
    ) -> float:
        """Assess prose quality."""
        score = 0.75
        
        # Check for repetitive sentence starts
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 5:
            first_words = [s.split()[0].lower() if s.split() else '' for s in sentences]
            word_counts = Counter(first_words)
            
            for word, count in word_counts.items():
                if count > len(sentences) * 0.2:  # More than 20% of sentences
                    issues.append(QualityIssue(
                        issue_type="repetitive_starts",
                        severity=IssueSeverity.LOW,
                        dimension=QualityDimension.PROSE_QUALITY,
                        location="throughout",
                        description=f"Many sentences start with '{word}'",
                        suggested_fix="Vary sentence structure and opening words"
                    ))
                    score -= 0.05
        
        # Check for passive voice (simplified)
        passive_patterns = ['was being', 'were being', 'is being', 'are being', 'had been']
        content_lower = content.lower()
        passive_count = sum(1 for p in passive_patterns if p in content_lower)
        
        if passive_count > 3:
            issues.append(QualityIssue(
                issue_type="passive_voice",
                severity=IssueSeverity.LOW,
                dimension=QualityDimension.PROSE_QUALITY,
                location="throughout",
                description="Excessive use of passive voice",
                suggested_fix="Convert passive constructions to active voice"
            ))
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_overall(
        self,
        narrative: float,
        style: float,
        depth: float,
        character: float,
        plot: float,
        emotional: float,
        prose: float
    ) -> float:
        """Calculate weighted overall score."""
        # Weights for each dimension
        weights = {
            'narrative': 0.2,
            'style': 0.15,
            'depth': 0.15,
            'character': 0.15,
            'plot': 0.15,
            'emotional': 0.1,
            'prose': 0.1
        }
        
        return (
            narrative * weights['narrative'] +
            style * weights['style'] +
            depth * weights['depth'] +
            character * weights['character'] +
            plot * weights['plot'] +
            emotional * weights['emotional'] +
            prose * weights['prose']
        )
    
    def _analyze_book_coherence(self, chapters: List[Dict]) -> float:
        """Analyze overall book coherence."""
        # Simplified analysis
        if not chapters:
            return 0.0
        
        # Check for consistent chapter lengths
        lengths = [len(c.get("content", "").split()) for c in chapters]
        if not lengths:
            return 0.5
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        
        # Lower variance = higher coherence
        if avg_length > 0:
            cv = std_dev / avg_length  # Coefficient of variation
            coherence = max(0.0, 1.0 - cv)
        else:
            coherence = 0.5
        
        return coherence
    
    def _analyze_pacing(self, chapters: List[Dict]) -> Dict[str, Any]:
        """Analyze book pacing."""
        if not chapters:
            return {}
        
        lengths = [len(c.get("content", "").split()) for c in chapters]
        
        return {
            "chapter_lengths": lengths,
            "average_length": sum(lengths) / len(lengths) if lengths else 0,
            "length_variance": len(set(lengths)) > 1,
            "pacing_pattern": "consistent" if len(set(lengths)) == 1 else "varied"
        }
    
    def _analyze_character_arcs(
        self,
        chapters: List[Dict],
        narrative_state: Optional[Any]
    ) -> Dict[str, Any]:
        """Analyze character development across chapters."""
        # This would require integration with character system
        return {
            "characters_tracked": 0,
            "arcs_completed": 0,
            "arcs_in_progress": 0
        }
    
    def _find_consistency_issues(
        self,
        chapters: List[Dict]
    ) -> List[QualityIssue]:
        """Find cross-chapter consistency issues."""
        issues = []
        
        # This would require more sophisticated analysis
        # For now, return empty list
        
        return issues


__all__ = [
    "QualityDimension",
    "IssueSeverity",
    "QualityIssue",
    "QualityScore",
    "BookQualityReport",
    "QualityAssessor",
]