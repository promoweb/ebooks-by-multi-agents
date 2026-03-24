"""
Style Profile System for BookWriterAI.

This module provides comprehensive style definition and management
for ensuring stylistic consistency across generated content.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class NarrativeVoice(Enum):
    """Narrative voice types."""
    FIRST_PERSON = "first_person"
    THIRD_LIMITED = "third_limited"
    THIRD_OMNISCIENT = "third_omniscient"
    SECOND_PERSON = "second_person"


class AuthorialVoice(Enum):
    """Authorial voice presence levels."""
    INVISIBLE = "invisible"  # Neutral, unobtrusive
    MODERATE = "moderate"    # Occasional authorial presence
    PROMINENT = "prominent"  # Strong authorial voice
    INTRUSIVE = "intrusive"  # Author directly addresses reader


class VocabularyComplexity(Enum):
    """Vocabulary complexity levels."""
    SIMPLE = "simple"           # Basic vocabulary, accessible
    MODERATE = "moderate"       # Standard vocabulary
    SOPHISTICATED = "sophisticated"  # Rich vocabulary
    ACADEMIC = "academic"       # Technical/scholarly vocabulary


class Tone(Enum):
    """Primary tone types."""
    SERIOUS = "serious"
    HUMOROUS = "humorous"
    MELANCHOLIC = "melancholic"
    HOPEFUL = "hopeful"
    DARK = "dark"
    LIGHT = "light"
    SATIRICAL = "satirical"
    ROMANTIC = "romantic"
    SUSPENSEFUL = "suspenseful"
    ADVENTUROUS = "adventurous"


@dataclass
class SpeechPatterns:
    """Defines character voice and dialogue patterns."""
    vocabulary_level: str = "moderate"  # simple, moderate, sophisticated, academic
    sentence_structure: str = "varied"  # short, complex, poetic, varied
    common_phrases: List[str] = field(default_factory=list)
    verbal_tics: List[str] = field(default_factory=list)  # Words/phrases frequently used
    emotional_expressiveness: float = 0.5  # 0.0 to 1.0
    formality: float = 0.5  # 0.0 to 1.0
    humor_style: Optional[str] = None  # witty, dry, slapstick, sarcastic
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "vocabulary_level": self.vocabulary_level,
            "sentence_structure": self.sentence_structure,
            "common_phrases": self.common_phrases,
            "verbal_tics": self.verbal_tics,
            "emotional_expressiveness": self.emotional_expressiveness,
            "formality": self.formality,
            "humor_style": self.humor_style
        }


@dataclass
class StyleProfile:
    """
    Comprehensive style definition for generated content.
    
    Defines all aspects of writing style including voice, tone,
    vocabulary, syntax, and pacing.
    """
    # Identity
    name: str = "default"
    description: str = ""
    
    # Voice characteristics
    narrative_voice: NarrativeVoice = NarrativeVoice.THIRD_LIMITED
    narrator_personality: Optional[str] = None  # For distinct narrator voice
    authorial_voice: AuthorialVoice = AuthorialVoice.MODERATE
    
    # Tone characteristics
    primary_tone: Tone = Tone.SERIOUS
    secondary_tones: List[Tone] = field(default_factory=list)
    tone_variation: float = 0.3  # 0.0 to 1.0, how much tone can vary
    emotional_range: Tuple[float, float] = (0.3, 0.7)  # Min and max emotional intensity
    
    # Lexical characteristics
    vocabulary_complexity: VocabularyComplexity = VocabularyComplexity.MODERATE
    jargon_level: float = 0.2  # 0.0 to 1.0
    figurative_language_density: float = 0.3  # Metaphors, similes per 1000 words
    sensory_language_ratio: float = 0.3  # Sensory details ratio
    
    # Syntactic characteristics
    average_sentence_length: int = 15  # Target words per sentence
    sentence_length_variation: float = 0.4  # Standard deviation factor
    paragraph_length: int = 4  # Target sentences per paragraph
    dialogue_narration_ratio: float = 0.3  # Target ratio
    
    # Rhythm and pacing
    scene_break_frequency: int = 3  # Scenes per chapter
    cliffhanger_probability: float = 0.5  # Chapter endings
    description_action_balance: float = 0.5  # 0.0 = all action, 1.0 = all description
    
    # Dialogue style
    dialogue_style: SpeechPatterns = field(default_factory=SpeechPatterns)
    
    # Forbidden elements
    forbidden_words: List[str] = field(default_factory=list)
    forbidden_phrases: List[str] = field(default_factory=list)
    
    # Required elements
    required_elements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "narrative_voice": self.narrative_voice.value,
            "narrator_personality": self.narrator_personality,
            "authorial_voice": self.authorial_voice.value,
            "primary_tone": self.primary_tone.value,
            "secondary_tones": [t.value for t in self.secondary_tones],
            "tone_variation": self.tone_variation,
            "emotional_range": self.emotional_range,
            "vocabulary_complexity": self.vocabulary_complexity.value,
            "jargon_level": self.jargon_level,
            "figurative_language_density": self.figurative_language_density,
            "sensory_language_ratio": self.sensory_language_ratio,
            "average_sentence_length": self.average_sentence_length,
            "sentence_length_variation": self.sentence_length_variation,
            "paragraph_length": self.paragraph_length,
            "dialogue_narration_ratio": self.dialogue_narration_ratio,
            "scene_break_frequency": self.scene_break_frequency,
            "cliffhanger_probability": self.cliffhanger_probability,
            "description_action_balance": self.description_action_balance,
            "dialogue_style": self.dialogue_style.to_dict(),
            "forbidden_words": self.forbidden_words,
            "forbidden_phrases": self.forbidden_phrases,
            "required_elements": self.required_elements
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StyleProfile":
        """Create from dictionary."""
        # Handle enum conversions
        narrative_voice = NarrativeVoice(data.get("narrative_voice", "third_limited"))
        authorial_voice = AuthorialVoice(data.get("authorial_voice", "moderate"))
        primary_tone = Tone(data.get("primary_tone", "serious"))
        vocabulary_complexity = VocabularyComplexity(
            data.get("vocabulary_complexity", "moderate")
        )
        
        secondary_tones = [
            Tone(t) for t in data.get("secondary_tones", [])
        ]
        
        dialogue_style_data = data.get("dialogue_style", {})
        dialogue_style = SpeechPatterns(
            vocabulary_level=dialogue_style_data.get("vocabulary_level", "moderate"),
            sentence_structure=dialogue_style_data.get("sentence_structure", "varied"),
            common_phrases=dialogue_style_data.get("common_phrases", []),
            verbal_tics=dialogue_style_data.get("verbal_tics", []),
            emotional_expressiveness=dialogue_style_data.get("emotional_expressiveness", 0.5),
            formality=dialogue_style_data.get("formality", 0.5),
            humor_style=dialogue_style_data.get("humor_style")
        )
        
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            narrative_voice=narrative_voice,
            narrator_personality=data.get("narrator_personality"),
            authorial_voice=authorial_voice,
            primary_tone=primary_tone,
            secondary_tones=secondary_tones,
            tone_variation=data.get("tone_variation", 0.3),
            emotional_range=tuple(data.get("emotional_range", (0.3, 0.7))),
            vocabulary_complexity=vocabulary_complexity,
            jargon_level=data.get("jargon_level", 0.2),
            figurative_language_density=data.get("figurative_language_density", 0.3),
            sensory_language_ratio=data.get("sensory_language_ratio", 0.3),
            average_sentence_length=data.get("average_sentence_length", 15),
            sentence_length_variation=data.get("sentence_length_variation", 0.4),
            paragraph_length=data.get("paragraph_length", 4),
            dialogue_narration_ratio=data.get("dialogue_narration_ratio", 0.3),
            scene_break_frequency=data.get("scene_break_frequency", 3),
            cliffhanger_probability=data.get("cliffhanger_probability", 0.5),
            description_action_balance=data.get("description_action_balance", 0.5),
            dialogue_style=dialogue_style,
            forbidden_words=data.get("forbidden_words", []),
            forbidden_phrases=data.get("forbidden_phrases", []),
            required_elements=data.get("required_elements", [])
        )


# Predefined style profiles
STYLE_PROFILES: Dict[str, StyleProfile] = {
    "literary": StyleProfile(
        name="literary",
        description="Literary fiction style with sophisticated prose",
        narrative_voice=NarrativeVoice.THIRD_LIMITED,
        authorial_voice=AuthorialVoice.PROMINENT,
        primary_tone=Tone.SERIOUS,
        vocabulary_complexity=VocabularyComplexity.SOPHISTICATED,
        figurative_language_density=0.6,
        sensory_language_ratio=0.5,
        average_sentence_length=20,
        sentence_length_variation=0.6,
        description_action_balance=0.6
    ),
    
    "thriller": StyleProfile(
        name="thriller",
        description="Fast-paced thriller style with tension and suspense",
        narrative_voice=NarrativeVoice.THIRD_LIMITED,
        authorial_voice=AuthorialVoice.INVISIBLE,
        primary_tone=Tone.SUSPENSEFUL,
        secondary_tones=[Tone.DARK],
        vocabulary_complexity=VocabularyComplexity.MODERATE,
        figurative_language_density=0.2,
        average_sentence_length=12,
        sentence_length_variation=0.3,
        dialogue_narration_ratio=0.4,
        cliffhanger_probability=0.8,
        description_action_balance=0.3
    ),
    
    "romance": StyleProfile(
        name="romance",
        description="Romance style with emotional depth and character focus",
        narrative_voice=NarrativeVoice.THIRD_LIMITED,
        authorial_voice=AuthorialVoice.MODERATE,
        primary_tone=Tone.ROMANTIC,
        secondary_tones=[Tone.HOPEFUL],
        vocabulary_complexity=VocabularyComplexity.MODERATE,
        figurative_language_density=0.4,
        sensory_language_ratio=0.5,
        average_sentence_length=15,
        dialogue_narration_ratio=0.5,
        description_action_balance=0.5
    ),
    
    "fantasy": StyleProfile(
        name="fantasy",
        description="Epic fantasy style with rich world-building",
        narrative_voice=NarrativeVoice.THIRD_OMNISCIENT,
        authorial_voice=AuthorialVoice.MODERATE,
        primary_tone=Tone.ADVENTUROUS,
        secondary_tones=[Tone.SERIOUS],
        vocabulary_complexity=VocabularyComplexity.SOPHISTICATED,
        figurative_language_density=0.5,
        sensory_language_ratio=0.6,
        average_sentence_length=18,
        description_action_balance=0.5
    ),
    
    "scifi": StyleProfile(
        name="scifi",
        description="Science fiction style with technical elements",
        narrative_voice=NarrativeVoice.THIRD_LIMITED,
        authorial_voice=AuthorialVoice.MODERATE,
        primary_tone=Tone.SERIOUS,
        secondary_tones=[Tone.ADVENTUROUS],
        vocabulary_complexity=VocabularyComplexity.SOPHISTICATED,
        jargon_level=0.4,
        figurative_language_density=0.3,
        average_sentence_length=16,
        description_action_balance=0.4
    ),
    
    "mystery": StyleProfile(
        name="mystery",
        description="Mystery style with clues and suspense",
        narrative_voice=NarrativeVoice.THIRD_LIMITED,
        authorial_voice=AuthorialVoice.INVISIBLE,
        primary_tone=Tone.SUSPENSEFUL,
        secondary_tones=[Tone.SERIOUS],
        vocabulary_complexity=VocabularyComplexity.MODERATE,
        figurative_language_density=0.2,
        average_sentence_length=14,
        dialogue_narration_ratio=0.4,
        cliffhanger_probability=0.6
    ),
    
    "academic": StyleProfile(
        name="academic",
        description="Academic writing style for non-fiction",
        narrative_voice=NarrativeVoice.THIRD_OMNISCIENT,
        authorial_voice=AuthorialVoice.MODERATE,
        primary_tone=Tone.SERIOUS,
        vocabulary_complexity=VocabularyComplexity.ACADEMIC,
        jargon_level=0.5,
        figurative_language_density=0.1,
        sensory_language_ratio=0.1,
        average_sentence_length=25,
        sentence_length_variation=0.3,
        paragraph_length=6,
        dialogue_narration_ratio=0.0
    ),
    
    "casual": StyleProfile(
        name="casual",
        description="Casual, accessible style for general audiences",
        narrative_voice=NarrativeVoice.THIRD_LIMITED,
        authorial_voice=AuthorialVoice.MODERATE,
        primary_tone=Tone.LIGHT,
        vocabulary_complexity=VocabularyComplexity.SIMPLE,
        figurative_language_density=0.2,
        average_sentence_length=12,
        sentence_length_variation=0.4,
        dialogue_narration_ratio=0.4
    )
}


class StyleProfileManager:
    """
    Manages style profiles and their application.
    
    Provides functionality to:
    - Create profiles from examples
    - Create genre-specific profiles
    - Merge profiles with weighted preferences
    - Store and retrieve profiles
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the style profile manager.
        
        Args:
            llm_client: LLM client for advanced profile creation
        """
        self.llm_client = llm_client
        self.custom_profiles: Dict[str, StyleProfile] = {}
    
    def get_profile(self, name: str) -> Optional[StyleProfile]:
        """
        Get a style profile by name.
        
        Args:
            name: Profile name
        
        Returns:
            StyleProfile or None if not found
        """
        # Check predefined profiles
        if name in STYLE_PROFILES:
            return STYLE_PROFILES[name]
        
        # Check custom profiles
        if name in self.custom_profiles:
            return self.custom_profiles[name]
        
        return None
    
    def create_profile(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> StyleProfile:
        """
        Create a custom style profile.
        
        Args:
            name: Profile name
            config: Profile configuration
        
        Returns:
            Created StyleProfile
        """
        profile = StyleProfile.from_dict({"name": name, **config})
        self.custom_profiles[name] = profile
        return profile
    
    def create_profile_from_examples(
        self,
        name: str,
        example_texts: List[str]
    ) -> StyleProfile:
        """
        Analyze example texts to create a style profile.
        
        Args:
            name: Profile name
            example_texts: List of example texts to analyze
        
        Returns:
            StyleProfile based on analysis
        """
        if not example_texts:
            return StyleProfile(name=name)
        
        # Analyze texts
        combined_text = " ".join(example_texts)
        
        # Calculate metrics
        avg_sentence_length = self._calculate_avg_sentence_length(combined_text)
        avg_paragraph_length = self._calculate_avg_paragraph_length(combined_text)
        dialogue_ratio = self._calculate_dialogue_ratio(combined_text)
        figurative_density = self._estimate_figurative_density(combined_text)
        
        # Detect narrative voice
        narrative_voice = self._detect_narrative_voice(combined_text)
        
        # Detect tone
        primary_tone = self._detect_tone(combined_text)
        
        # Estimate vocabulary complexity
        vocab_complexity = self._estimate_vocabulary_complexity(combined_text)
        
        profile = StyleProfile(
            name=name,
            description=f"Auto-generated from {len(example_texts)} example texts",
            narrative_voice=narrative_voice,
            primary_tone=primary_tone,
            vocabulary_complexity=vocab_complexity,
            average_sentence_length=avg_sentence_length,
            paragraph_length=avg_paragraph_length,
            dialogue_narration_ratio=dialogue_ratio,
            figurative_language_density=figurative_density
        )
        
        self.custom_profiles[name] = profile
        return profile
    
    def create_genre_profile(
        self,
        genre: str,
        subgenre: Optional[str] = None,
        customizations: Optional[Dict[str, Any]] = None
    ) -> StyleProfile:
        """
        Create a style profile based on genre conventions.
        
        Args:
            genre: Primary genre
            subgenre: Optional subgenre
            customizations: Optional customizations to apply
        
        Returns:
            StyleProfile for the genre
        """
        # Get base profile for genre
        base_profile = self.get_profile(genre.lower())
        
        if not base_profile:
            # Create default profile
            base_profile = StyleProfile(
                name=genre,
                description=f"Style profile for {genre}"
            )
        
        # Apply customizations
        if customizations:
            profile_dict = base_profile.to_dict()
            profile_dict.update(customizations)
            return StyleProfile.from_dict(profile_dict)
        
        return base_profile
    
    def merge_profiles(
        self,
        base_profile: StyleProfile,
        override_profile: StyleProfile,
        merge_weights: Optional[Dict[str, float]] = None
    ) -> StyleProfile:
        """
        Merge two profiles with weighted preferences.
        
        Args:
            base_profile: Base profile
            override_profile: Profile to merge
            merge_weights: Weights for each attribute (0.0 = base, 1.0 = override)
        
        Returns:
            Merged StyleProfile
        """
        merge_weights = merge_weights or {}
        
        base_dict = base_profile.to_dict()
        override_dict = override_profile.to_dict()
        
        merged = {}
        
        for key in base_dict:
            if key in ["name", "description"]:
                merged[key] = base_dict[key]
                continue
            
            base_value = base_dict.get(key)
            override_value = override_dict.get(key)
            
            weight = merge_weights.get(key, 0.5)
            
            # Handle numeric values
            if isinstance(base_value, (int, float)) and isinstance(override_value, (int, float)):
                merged[key] = base_value * (1 - weight) + override_value * weight
            # Handle enum values
            elif isinstance(base_value, str) and isinstance(override_value, str):
                merged[key] = override_value if weight > 0.5 else base_value
            # Handle lists
            elif isinstance(base_value, list) and isinstance(override_value, list):
                if weight > 0.5:
                    merged[key] = override_value
                else:
                    merged[key] = base_value
            else:
                merged[key] = base_value
        
        return StyleProfile.from_dict(merged)
    
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        return list(STYLE_PROFILES.keys()) + list(self.custom_profiles.keys())
    
    # Analysis helper methods
    
    def _calculate_avg_sentence_length(self, text: str) -> int:
        """Calculate average sentence length."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 15
        
        total_words = sum(len(s.split()) for s in sentences)
        return total_words // len(sentences)
    
    def _calculate_avg_paragraph_length(self, text: str) -> int:
        """Calculate average paragraph length in sentences."""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return 4
        
        total_sentences = sum(
            len([s for s in re.split(r'[.!?]+', p) if s.strip()])
            for p in paragraphs
        )
        return total_sentences // len(paragraphs)
    
    def _calculate_dialogue_ratio(self, text: str) -> float:
        """Calculate dialogue to narration ratio."""
        # Find dialogue (text in quotes)
        dialogue_matches = re.findall(r'"[^"]*"', text)
        dialogue_chars = sum(len(d) for d in dialogue_matches)
        
        total_chars = len(text)
        if total_chars == 0:
            return 0.0
        
        return dialogue_chars / total_chars
    
    def _estimate_figurative_density(self, text: str) -> float:
        """Estimate figurative language density."""
        # Count similes and metaphors indicators
        simile_patterns = [
            r'\blike\b',
            r'\bas if\b',
            r'\bas though\b',
            r'\bsimilar to\b'
        ]
        
        count = 0
        text_lower = text.lower()
        for pattern in simile_patterns:
            count += len(re.findall(pattern, text_lower))
        
        # Estimate per 1000 words
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        return (count * 1000) / word_count
    
    def _detect_narrative_voice(self, text: str) -> NarrativeVoice:
        """Detect narrative voice from text."""
        # Check for first person
        first_person_patterns = [r'\bI\b', r'\bme\b', r'\bmy\b', r'\bmine\b']
        first_person_count = sum(
            len(re.findall(p, text))
            for p in first_person_patterns
        )
        
        # Check for second person
        second_person_patterns = [r'\byou\b', r'\byour\b', r'\byours\b']
        second_person_count = sum(
            len(re.findall(p, text, re.IGNORECASE))
            for p in second_person_patterns
        )
        
        # Simple heuristic
        word_count = len(text.split())
        if word_count == 0:
            return NarrativeVoice.THIRD_LIMITED
        
        first_person_ratio = first_person_count / word_count
        
        if first_person_ratio > 0.02:
            return NarrativeVoice.FIRST_PERSON
        elif second_person_count > first_person_count:
            return NarrativeVoice.SECOND_PERSON
        else:
            return NarrativeVoice.THIRD_LIMITED
    
    def _detect_tone(self, text: str) -> Tone:
        """Detect primary tone from text."""
        # Simple keyword-based detection
        tone_keywords = {
            Tone.SERIOUS: ['serious', 'grave', 'solemn', 'important'],
            Tone.HUMOROUS: ['funny', 'amusing', 'humorous', 'comic'],
            Tone.MELANCHOLIC: ['sad', 'melancholy', 'sorrow', 'grief'],
            Tone.HOPEFUL: ['hope', 'optimistic', 'bright', 'future'],
            Tone.DARK: ['dark', 'shadow', 'evil', 'sinister'],
            Tone.ROMANTIC: ['love', 'romantic', 'passion', 'heart'],
            Tone.SUSPENSEFUL: ['suspense', 'tension', 'mystery', 'danger'],
            Tone.ADVENTUROUS: ['adventure', 'journey', 'quest', 'explore']
        }
        
        text_lower = text.lower()
        scores = {}
        
        for tone, keywords in tone_keywords.items():
            score = sum(text_lower.count(kw) for kw in keywords)
            scores[tone] = score
        
        if not scores or max(scores.values()) == 0:
            return Tone.SERIOUS
        
        return max(scores, key=scores.get)
    
    def _estimate_vocabulary_complexity(self, text: str) -> VocabularyComplexity:
        """Estimate vocabulary complexity."""
        words = text.split()
        if not words:
            return VocabularyComplexity.MODERATE
        
        # Calculate average word length
        avg_length = sum(len(w) for w in words) / len(words)
        
        # Count unique words
        unique_words = set(w.lower() for w in words)
        unique_ratio = len(unique_words) / len(words)
        
        # Simple heuristic
        if avg_length > 6 and unique_ratio > 0.6:
            return VocabularyComplexity.ACADEMIC
        elif avg_length > 5 and unique_ratio > 0.5:
            return VocabularyComplexity.SOPHISTICATED
        elif avg_length > 4:
            return VocabularyComplexity.MODERATE
        else:
            return VocabularyComplexity.SIMPLE


__all__ = [
    "NarrativeVoice",
    "AuthorialVoice",
    "VocabularyComplexity",
    "Tone",
    "SpeechPatterns",
    "StyleProfile",
    "STYLE_PROFILES",
    "StyleProfileManager",
]