"""
Style Enforcement Layer for BookWriterAI.

This module provides style enforcement capabilities including
prompt injection, output validation, and style correction.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class ContentType(Enum):
    """Type of content being generated."""
    NARRATION = "narration"
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"
    ACTION = "action"
    INTERNAL_MONOLOGUE = "internal_monologue"
    EXPOSITION = "exposition"


@dataclass
class StyleViolation:
    """Represents a style violation in generated content."""
    violation_type: str
    severity: str  # low, medium, high, critical
    location: str  # Text location or description
    description: str
    suggestion: str
    context: str = ""  # Surrounding text


@dataclass
class StyleValidationReport:
    """Report from style validation."""
    is_compliant: bool
    overall_score: float  # 0.0 to 1.0
    violations: List[StyleViolation] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Sentence metrics
    avg_sentence_length: float = 0.0
    sentence_length_std: float = 0.0
    
    # Vocabulary metrics
    vocabulary_richness: float = 0.0
    avg_word_length: float = 0.0
    
    # Structure metrics
    dialogue_ratio: float = 0.0
    paragraph_count: int = 0
    avg_paragraph_length: float = 0.0
    
    # Style metrics
    figurative_language_count: int = 0
    sensory_language_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "is_compliant": self.is_compliant,
            "overall_score": self.overall_score,
            "violations": [
                {
                    "type": v.violation_type,
                    "severity": v.severity,
                    "location": v.location,
                    "description": v.description,
                    "suggestion": v.suggestion
                }
                for v in self.violations
            ],
            "metrics": self.metrics,
            "avg_sentence_length": self.avg_sentence_length,
            "sentence_length_std": self.sentence_length_std,
            "vocabulary_richness": self.vocabulary_richness,
            "avg_word_length": self.avg_word_length,
            "dialogue_ratio": self.dialogue_ratio,
            "paragraph_count": self.paragraph_count,
            "avg_paragraph_length": self.avg_paragraph_length,
            "figurative_language_count": self.figurative_language_count,
            "sensory_language_count": self.sensory_language_count
        }


class StylePromptInjector:
    """
    Injects style requirements into generation prompts.
    
    Creates detailed style instructions that guide the LLM
    to generate content matching the desired style profile.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the style prompt injector.
        
        Args:
            llm_client: LLM client for advanced prompt generation
        """
        self.llm_client = llm_client
    
    def create_style_prompt(
        self,
        style_profile,
        content_type: ContentType = ContentType.NARRATION,
        context: str = "",
        additional_instructions: Optional[List[str]] = None
    ) -> str:
        """
        Create a detailed style instruction prompt.
        
        Args:
            style_profile: StyleProfile to use
            content_type: Type of content being generated
            context: Additional context for the generation
            additional_instructions: Extra style instructions
        
        Returns:
            Formatted style instruction string
        """
        sections = []
        
        # Header
        sections.append("=== STYLE REQUIREMENTS ===\n")
        
        # Voice
        voice_section = self._format_voice_section(style_profile)
        sections.append(voice_section)
        
        # Tone
        tone_section = self._format_tone_section(style_profile)
        sections.append(tone_section)
        
        # Vocabulary
        vocab_section = self._format_vocabulary_section(style_profile)
        sections.append(vocab_section)
        
        # Sentence structure
        sentence_section = self._format_sentence_section(style_profile)
        sections.append(sentence_section)
        
        # Content-specific instructions
        content_section = self._format_content_section(
            style_profile, content_type
        )
        sections.append(content_section)
        
        # Pacing
        pacing_section = self._format_pacing_section(style_profile)
        sections.append(pacing_section)
        
        # Forbidden elements
        if style_profile.forbidden_words or style_profile.forbidden_phrases:
            forbidden_section = self._format_forbidden_section(style_profile)
            sections.append(forbidden_section)
        
        # Additional instructions
        if additional_instructions:
            sections.append("\n=== ADDITIONAL INSTRUCTIONS ===")
            for instruction in additional_instructions:
                sections.append(f"- {instruction}")
        
        return "\n".join(sections)
    
    def _format_voice_section(self, profile) -> str:
        """Format voice section of style prompt."""
        lines = ["\n=== NARRATIVE VOICE ==="]
        
        # Narrative voice
        voice_map = {
            "first_person": "First-person perspective (use 'I', 'me', 'my')",
            "third_limited": "Third-person limited (one character's perspective)",
            "third_omniscient": "Third-person omniscient (all-knowing narrator)",
            "second_person": "Second-person perspective (use 'you')"
        }
        voice_desc = voice_map.get(
            profile.narrative_voice.value,
            profile.narrative_voice.value
        )
        lines.append(f"- Perspective: {voice_desc}")
        
        # Authorial voice
        authorial_map = {
            "invisible": "Invisible narrator - let the story speak for itself",
            "moderate": "Moderate authorial presence",
            "prominent": "Prominent authorial voice with distinct personality",
            "intrusive": "Intrusive narrator who directly addresses the reader"
        }
        authorial_desc = authorial_map.get(
            profile.authorial_voice.value,
            profile.authorial_voice.value
        )
        lines.append(f"- Authorial presence: {authorial_desc}")
        
        # Narrator personality
        if profile.narrator_personality:
            lines.append(f"- Narrator personality: {profile.narrator_personality}")
        
        return "\n".join(lines)
    
    def _format_tone_section(self, profile) -> str:
        """Format tone section of style prompt."""
        lines = ["\n=== TONE ==="]
        
        lines.append(f"- Primary tone: {profile.primary_tone.value.replace('_', ' ').title()}")
        
        if profile.secondary_tones:
            secondary = ", ".join(
                t.value.replace('_', ' ').title()
                for t in profile.secondary_tones
            )
            lines.append(f"- Secondary tones: {secondary}")
        
        lines.append(f"- Tone variation: {self._describe_variation(profile.tone_variation)}")
        
        min_emotion, max_emotion = profile.emotional_range
        lines.append(
            f"- Emotional intensity: {min_emotion:.0%} to {max_emotion:.0%}"
        )
        
        return "\n".join(lines)
    
    def _describe_variation(self, variation: float) -> str:
        """Describe variation level."""
        if variation < 0.2:
            return "Consistent throughout"
        elif variation < 0.4:
            return "Slight variation allowed"
        elif variation < 0.6:
            return "Moderate variation"
        elif variation < 0.8:
            return "Significant variation"
        else:
            return "Highly variable"
    
    def _format_vocabulary_section(self, profile) -> str:
        """Format vocabulary section of style prompt."""
        lines = ["\n=== VOCABULARY ==="]
        
        vocab_map = {
            "simple": "Simple, accessible vocabulary suitable for all readers",
            "moderate": "Standard vocabulary with occasional sophisticated words",
            "sophisticated": "Rich, sophisticated vocabulary with literary flair",
            "academic": "Technical, scholarly vocabulary appropriate for experts"
        }
        vocab_desc = vocab_map.get(
            profile.vocabulary_complexity.value,
            profile.vocabulary_complexity.value
        )
        lines.append(f"- Level: {vocab_desc}")
        
        if profile.jargon_level > 0:
            lines.append(f"- Technical/specialized terms: {profile.jargon_level:.0%}")
        
        if profile.figurative_language_density > 0:
            density = profile.figurative_language_density
            if density < 0.2:
                fig_desc = "Sparingly"
            elif density < 0.4:
                fig_desc = "Moderately"
            elif density < 0.6:
                fig_desc = "Frequently"
            else:
                fig_desc = "Extensively"
            lines.append(f"- Use figurative language (metaphors, similes): {fig_desc}")
        
        if profile.sensory_language_ratio > 0.3:
            lines.append("- Emphasize sensory details (sight, sound, touch, smell, taste)")
        
        return "\n".join(lines)
    
    def _format_sentence_section(self, profile) -> str:
        """Format sentence structure section."""
        lines = ["\n=== SENTENCE STRUCTURE ==="]
        
        lines.append(f"- Target sentence length: ~{profile.average_sentence_length} words")
        
        variation = profile.sentence_length_variation
        if variation < 0.2:
            lines.append("- Sentence length: Consistent, uniform")
        elif variation < 0.4:
            lines.append("- Sentence length: Some variation")
        elif variation < 0.6:
            lines.append("- Sentence length: Varied rhythm")
        else:
            lines.append("- Sentence length: Highly varied for dramatic effect")
        
        lines.append(f"- Target paragraph length: ~{profile.paragraph_length} sentences")
        
        return "\n".join(lines)
    
    def _format_content_section(
        self,
        profile,
        content_type: ContentType
    ) -> str:
        """Format content-specific section."""
        lines = ["\n=== CONTENT GUIDELINES ==="]
        
        # Dialogue ratio
        if content_type in [ContentType.NARRATION, ContentType.DIALOGUE]:
            ratio = profile.dialogue_narration_ratio
            if ratio < 0.2:
                lines.append("- Dialogue: Minimal, focus on narration")
            elif ratio < 0.4:
                lines.append("- Dialogue: Moderate amount")
            elif ratio < 0.6:
                lines.append("- Dialogue: Balanced with narration")
            else:
                lines.append("- Dialogue: Heavy emphasis on dialogue")
        
        # Description vs action
        balance = profile.description_action_balance
        if content_type in [ContentType.NARRATION, ContentType.ACTION, ContentType.DESCRIPTION]:
            if balance < 0.3:
                lines.append("- Pacing: Fast, action-focused")
            elif balance < 0.5:
                lines.append("- Pacing: Leans toward action")
            elif balance < 0.7:
                lines.append("- Pacing: Balanced action and description")
            else:
                lines.append("- Pacing: Slower, description-focused")
        
        return "\n".join(lines)
    
    def _format_pacing_section(self, profile) -> str:
        """Format pacing section."""
        lines = ["\n=== PACING ==="]
        
        lines.append(f"- Scene breaks: ~{profile.scene_break_frequency} per chapter")
        
        if profile.cliffhanger_probability > 0.6:
            lines.append("- Chapter endings: Strong cliffhangers preferred")
        elif profile.cliffhanger_probability > 0.3:
            lines.append("- Chapter endings: Occasional cliffhangers")
        else:
            lines.append("- Chapter endings: Natural conclusions")
        
        return "\n".join(lines)
    
    def _format_forbidden_section(self, profile) -> str:
        """Format forbidden elements section."""
        lines = ["\n=== AVOID ==="]
        
        if profile.forbidden_words:
            words = ", ".join(profile.forbidden_words[:10])
            lines.append(f"- Forbidden words: {words}")
        
        if profile.forbidden_phrases:
            phrases = ", ".join(f'"{p}"' for p in profile.forbidden_phrases[:5])
            lines.append(f"- Forbidden phrases: {phrases}")
        
        return "\n".join(lines)


class StyleValidator:
    """
    Validates generated content against style profile.
    
    Analyzes text for style compliance across multiple dimensions:
    - Sentence length distribution
    - Vocabulary complexity
    - Figurative language density
    - Dialogue/narration ratio
    - Tone consistency
    - Perspective consistency
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the style validator.
        
        Args:
            llm_client: LLM client for advanced validation
        """
        self.llm_client = llm_client
    
    def validate(
        self,
        text: str,
        style_profile,
        strict: bool = False
    ) -> StyleValidationReport:
        """
        Validate text against style profile.
        
        Args:
            text: Text to validate
            style_profile: StyleProfile to validate against
            strict: Whether to apply strict validation
        
        Returns:
            StyleValidationReport with findings
        """
        if not text or not text.strip():
            return StyleValidationReport(
                is_compliant=False,
                overall_score=0.0,
                violations=[StyleViolation(
                    violation_type="empty_content",
                    severity="critical",
                    location="entire text",
                    description="Content is empty",
                    suggestion="Provide content to validate"
                )]
            )
        
        violations = []
        metrics = {}
        
        # Analyze sentences
        sentence_metrics = self._analyze_sentences(text)
        sentence_violations = self._check_sentence_compliance(
            sentence_metrics, style_profile, strict
        )
        violations.extend(sentence_violations)
        metrics.update(sentence_metrics)
        
        # Analyze vocabulary
        vocab_metrics = self._analyze_vocabulary(text)
        vocab_violations = self._check_vocabulary_compliance(
            vocab_metrics, style_profile, strict
        )
        violations.extend(vocab_violations)
        metrics.update(vocab_metrics)
        
        # Analyze structure
        structure_metrics = self._analyze_structure(text)
        structure_violations = self._check_structure_compliance(
            structure_metrics, style_profile, strict
        )
        violations.extend(structure_violations)
        metrics.update(structure_metrics)
        
        # Check forbidden elements
        forbidden_violations = self._check_forbidden_elements(
            text, style_profile
        )
        violations.extend(forbidden_violations)
        
        # Check perspective consistency
        perspective_violations = self._check_perspective(
            text, style_profile, strict
        )
        violations.extend(perspective_violations)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(violations, metrics)
        
        # Determine compliance
        is_compliant = overall_score >= 0.7 and not any(
            v.severity == "critical" for v in violations
        )
        
        return StyleValidationReport(
            is_compliant=is_compliant,
            overall_score=overall_score,
            violations=violations,
            metrics=metrics,
            avg_sentence_length=sentence_metrics.get("avg_length", 0),
            sentence_length_std=sentence_metrics.get("std", 0),
            vocabulary_richness=vocab_metrics.get("richness", 0),
            avg_word_length=vocab_metrics.get("avg_word_length", 0),
            dialogue_ratio=structure_metrics.get("dialogue_ratio", 0),
            paragraph_count=structure_metrics.get("paragraph_count", 0),
            avg_paragraph_length=structure_metrics.get("avg_paragraph_length", 0),
            figurative_language_count=metrics.get("figurative_count", 0),
            sensory_language_count=metrics.get("sensory_count", 0)
        )
    
    def _analyze_sentences(self, text: str) -> Dict[str, float]:
        """Analyze sentence metrics."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"avg_length": 0, "std": 0, "count": 0}
        
        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        
        # Standard deviation
        if len(lengths) > 1:
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            std = variance ** 0.5
        else:
            std = 0
        
        return {
            "avg_length": avg_length,
            "std": std,
            "count": len(sentences),
            "lengths": lengths
        }
    
    def _analyze_vocabulary(self, text: str) -> Dict[str, float]:
        """Analyze vocabulary metrics."""
        words = text.split()
        words = [w.strip('.,!?;:"\'-').lower() for w in words]
        words = [w for w in words if w]
        
        if not words:
            return {"richness": 0, "avg_word_length": 0}
        
        # Vocabulary richness (type-token ratio)
        unique_words = set(words)
        richness = len(unique_words) / len(words)
        
        # Average word length
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        return {
            "richness": richness,
            "avg_word_length": avg_word_length,
            "word_count": len(words),
            "unique_count": len(unique_words)
        }
    
    def _analyze_structure(self, text: str) -> Dict[str, float]:
        """Analyze structural metrics."""
        # Paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Dialogue
        dialogue_matches = re.findall(r'"[^"]*"', text)
        dialogue_chars = sum(len(d) for d in dialogue_matches)
        total_chars = len(text)
        dialogue_ratio = dialogue_chars / total_chars if total_chars > 0 else 0
        
        # Paragraph metrics
        if paragraphs:
            sentences_per_para = []
            for p in paragraphs:
                sentences = [s for s in re.split(r'[.!?]+', p) if s.strip()]
                sentences_per_para.append(len(sentences))
            avg_paragraph_length = sum(sentences_per_para) / len(sentences_per_para)
        else:
            avg_paragraph_length = 0
        
        return {
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": avg_paragraph_length,
            "dialogue_ratio": dialogue_ratio,
            "dialogue_count": len(dialogue_matches)
        }
    
    def _check_sentence_compliance(
        self,
        metrics: Dict,
        profile,
        strict: bool
    ) -> List[StyleViolation]:
        """Check sentence metrics against profile."""
        violations = []
        
        target_length = profile.average_sentence_length
        actual_length = metrics.get("avg_length", 0)
        
        # Allow 30% deviation normally, 20% in strict mode
        tolerance = 0.2 if strict else 0.3
        
        if actual_length > 0:
            deviation = abs(actual_length - target_length) / target_length
            
            if deviation > tolerance:
                severity = "medium" if deviation < 0.5 else "high"
                violations.append(StyleViolation(
                    violation_type="sentence_length",
                    severity=severity,
                    location="throughout text",
                    description=f"Average sentence length ({actual_length:.1f}) differs from target ({target_length})",
                    suggestion=f"Adjust sentence lengths toward {target_length} words average"
                ))
        
        return violations
    
    def _check_vocabulary_compliance(
        self,
        metrics: Dict,
        profile,
        strict: bool
    ) -> List[StyleViolation]:
        """Check vocabulary metrics against profile."""
        violations = []
        
        # Check word length based on complexity
        avg_word_length = metrics.get("avg_word_length", 0)
        richness = metrics.get("richness", 0)
        
        expected_ranges = {
            "simple": (3.5, 4.5, 0.4, 0.55),
            "moderate": (4.0, 5.0, 0.45, 0.6),
            "sophisticated": (4.5, 5.5, 0.5, 0.7),
            "academic": (5.0, 6.5, 0.55, 0.75)
        }
        
        complexity = profile.vocabulary_complexity.value
        if complexity in expected_ranges:
            min_len, max_len, min_rich, max_rich = expected_ranges[complexity]
            
            if avg_word_length < min_len or avg_word_length > max_len:
                violations.append(StyleViolation(
                    violation_type="vocabulary_complexity",
                    severity="low",
                    location="throughout text",
                    description=f"Word length ({avg_word_length:.1f}) doesn't match {complexity} style",
                    suggestion=f"Use more {'complex' if avg_word_length < min_len else 'simple'} vocabulary"
                ))
        
        return violations
    
    def _check_structure_compliance(
        self,
        metrics: Dict,
        profile,
        strict: bool
    ) -> List[StyleViolation]:
        """Check structural metrics against profile."""
        violations = []
        
        # Check dialogue ratio
        target_ratio = profile.dialogue_narration_ratio
        actual_ratio = metrics.get("dialogue_ratio", 0)
        
        if target_ratio > 0:
            deviation = abs(actual_ratio - target_ratio)
            if deviation > 0.2:
                violations.append(StyleViolation(
                    violation_type="dialogue_ratio",
                    severity="low",
                    location="throughout text",
                    description=f"Dialogue ratio ({actual_ratio:.1%}) differs from target ({target_ratio:.1%})",
                    suggestion=f"{'Add more dialogue' if actual_ratio < target_ratio else 'Reduce dialogue'}"
                ))
        
        return violations
    
    def _check_forbidden_elements(
        self,
        text: str,
        profile
    ) -> List[StyleViolation]:
        """Check for forbidden words and phrases."""
        violations = []
        text_lower = text.lower()
        
        # Check forbidden words
        for word in profile.forbidden_words:
            if word.lower() in text_lower:
                violations.append(StyleViolation(
                    violation_type="forbidden_word",
                    severity="medium",
                    location=f"contains '{word}'",
                    description=f"Text contains forbidden word: '{word}'",
                    suggestion=f"Replace '{word}' with an alternative"
                ))
        
        # Check forbidden phrases
        for phrase in profile.forbidden_phrases:
            if phrase.lower() in text_lower:
                violations.append(StyleViolation(
                    violation_type="forbidden_phrase",
                    severity="medium",
                    location=f"contains '{phrase}'",
                    description=f"Text contains forbidden phrase: '{phrase}'",
                    suggestion=f"Rephrase to avoid '{phrase}'"
                ))
        
        return violations
    
    def _check_perspective(
        self,
        text: str,
        profile,
        strict: bool
    ) -> List[StyleViolation]:
        """Check perspective consistency."""
        violations = []
        
        voice = profile.narrative_voice.value
        
        if voice == "first_person":
            # Check for third-person pronouns that might indicate perspective shift
            third_person = re.findall(r'\b(he|she|they)\b(?!\s+said)', text, re.IGNORECASE)
            # This is a simplified check - would need more sophisticated analysis
        
        elif voice in ["third_limited", "third_omniscient"]:
            # Check for first-person pronouns outside dialogue
            # This is simplified - would need dialogue detection
            pass
        
        return violations
    
    def _calculate_overall_score(
        self,
        violations: List[StyleViolation],
        metrics: Dict[str, float]
    ) -> float:
        """Calculate overall compliance score."""
        if not violations:
            return 1.0
        
        # Weight violations by severity
        severity_weights = {
            "low": 0.05,
            "medium": 0.1,
            "high": 0.2,
            "critical": 0.5
        }
        
        total_penalty = sum(
            severity_weights.get(v.severity, 0.1)
            for v in violations
        )
        
        # Score is 1.0 minus penalty, minimum 0.0
        return max(0.0, 1.0 - total_penalty)


class StyleCorrector:
    """
    Applies corrections to bring content closer to style profile.
    
    Can perform:
    - Sentence length adjustment
    - Vocabulary substitution
    - Tone adjustment
    - Perspective correction
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the style corrector.
        
        Args:
            llm_client: LLM client for advanced corrections
        """
        self.llm_client = llm_client
    
    def correct(
        self,
        text: str,
        style_profile,
        validation_report: StyleValidationReport,
        max_corrections: int = 5
    ) -> str:
        """
        Apply targeted corrections to text.
        
        Args:
            text: Text to correct
            style_profile: Target style profile
            validation_report: Validation report with violations
            max_corrections: Maximum number of corrections to apply
        
        Returns:
            Corrected text
        """
        if not text:
            return text
        
        corrected_text = text
        
        # Sort violations by severity
        violations = sorted(
            validation_report.violations,
            key=lambda v: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(v.severity, 4)
        )
        
        corrections_applied = 0
        
        for violation in violations:
            if corrections_applied >= max_corrections:
                break
            
            if violation.violation_type == "forbidden_word":
                corrected_text = self._correct_forbidden_word(
                    corrected_text, violation
                )
                corrections_applied += 1
            
            elif violation.violation_type == "forbidden_phrase":
                corrected_text = self._correct_forbidden_phrase(
                    corrected_text, violation
                )
                corrections_applied += 1
            
            elif violation.violation_type == "sentence_length":
                # Sentence length correction requires LLM
                if self.llm_client:
                    corrected_text = self._correct_sentence_length(
                        corrected_text, style_profile, violation
                    )
                    corrections_applied += 1
        
        return corrected_text
    
    def _correct_forbidden_word(
        self,
        text: str,
        violation: StyleViolation
    ) -> str:
        """Remove or replace forbidden word."""
        # Simple removal for now - would need LLM for intelligent replacement
        # This is a placeholder
        return text
    
    def _correct_forbidden_phrase(
        self,
        text: str,
        violation: StyleViolation
    ) -> str:
        """Remove or replace forbidden phrase."""
        # Simple removal for now
        return text
    
    def _correct_sentence_length(
        self,
        text: str,
        style_profile,
        violation: StyleViolation
    ) -> str:
        """Adjust sentence lengths using LLM."""
        if not self.llm_client:
            return text
        
        target = style_profile.average_sentence_length
        
        prompt = f"""Adjust the following text to have an average sentence length of approximately {target} words.
Maintain the same meaning and style. Combine or split sentences as needed.

Text:
{text}

Adjusted text:"""
        
        try:
            corrected = self.llm_client.generate(prompt, max_tokens=len(text) + 500)
            return corrected.strip()
        except Exception as e:
            logger.warning(f"Sentence length correction failed: {e}")
            return text


__all__ = [
    "ContentType",
    "StyleViolation",
    "StyleValidationReport",
    "StylePromptInjector",
    "StyleValidator",
    "StyleCorrector",
]