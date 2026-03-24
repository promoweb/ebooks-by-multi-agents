"""
Character Profile System for BookWriterAI.

This module provides comprehensive character modeling including
personality profiles, motivations, speech patterns, and character arcs.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json


logger = logging.getLogger("BookWriterAI")


class MoralAlignment(Enum):
    """Moral alignment based on D&D system."""
    LAWFUL_GOOD = "lawful_good"
    NEUTRAL_GOOD = "neutral_good"
    CHAOTIC_GOOD = "chaotic_good"
    LAWFUL_NEUTRAL = "lawful_neutral"
    TRUE_NEUTRAL = "true_neutral"
    CHAOTIC_NEUTRAL = "chaotic_neutral"
    LAWFUL_EVIL = "lawful_evil"
    NEUTRAL_EVIL = "neutral_evil"
    CHAOTIC_EVIL = "chaotic_evil"


class ArcType(Enum):
    """Types of character arcs."""
    GROWTH = "growth"  # Character improves/learns
    FALL = "fall"  # Character declines
    FLAT = "flat"  # Character stays same (catalyst for others)
    TRANSFORMATION = "transformation"  # Major change in identity
    REDEMPTION = "redemption"  # Villain becomes hero
    CORRUPTION = "corruption"  # Hero becomes villain


class MomentType(Enum):
    """Types of arc moments."""
    CATALYST = "catalyst"  # Initial trigger
    CHALLENGE = "challenge"  # Obstacle to overcome
    REVELATION = "revelation"  # New understanding
    TURNING_POINT = "turning_point"  # Major decision
    CLIMAX = "climax"  # Peak of arc
    RESOLUTION = "resolution"  # Arc conclusion


@dataclass
class SpeechPatterns:
    """
    Defines character voice and dialogue patterns.
    
    Captures how a character speaks including vocabulary,
    sentence structure, and verbal habits.
    """
    vocabulary_level: str = "moderate"  # simple, moderate, sophisticated, academic
    sentence_structure: str = "varied"  # short, complex, poetic, varied
    common_phrases: List[str] = field(default_factory=list)
    verbal_tics: List[str] = field(default_factory=list)  # Words/phrases frequently used
    emotional_expressiveness: float = 0.5  # 0.0 to 1.0
    formality: float = 0.5  # 0.0 to 1.0
    humor_style: Optional[str] = None  # witty, dry, slapstick, sarcastic
    accent_dialect: Optional[str] = None
    speech_tempo: str = "moderate"  # slow, moderate, fast
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "vocabulary_level": self.vocabulary_level,
            "sentence_structure": self.sentence_structure,
            "common_phrases": self.common_phrases,
            "verbal_tics": self.verbal_tics,
            "emotional_expressiveness": self.emotional_expressiveness,
            "formality": self.formality,
            "humor_style": self.humor_style,
            "accent_dialect": self.accent_dialect,
            "speech_tempo": self.speech_tempo
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SpeechPatterns":
        """Create from dictionary."""
        return cls(
            vocabulary_level=data.get("vocabulary_level", "moderate"),
            sentence_structure=data.get("sentence_structure", "varied"),
            common_phrases=data.get("common_phrases", []),
            verbal_tics=data.get("verbal_tics", []),
            emotional_expressiveness=data.get("emotional_expressiveness", 0.5),
            formality=data.get("formality", 0.5),
            humor_style=data.get("humor_style"),
            accent_dialect=data.get("accent_dialect"),
            speech_tempo=data.get("speech_tempo", "moderate")
        )


@dataclass
class PersonalityProfile:
    """
    Comprehensive personality model based on Big Five + narrative traits.
    
    The Big Five (OCEAN) model provides a foundation, extended with
    narrative-specific traits for character development.
    """
    # Big Five traits (0.0 to 1.0)
    openness: float = 0.5  # Curiosity, creativity, novelty-seeking
    conscientiousness: float = 0.5  # Organization, dependability, discipline
    extraversion: float = 0.5  # Sociability, assertiveness, positive emotions
    agreeableness: float = 0.5  # Cooperation, trust, helpfulness
    neuroticism: float = 0.5  # Emotional instability, anxiety, moodiness
    
    # Narrative-specific traits
    moral_alignment: MoralAlignment = MoralAlignment.TRUE_NEUTRAL
    primary_drives: List[str] = field(default_factory=list)  # power, love, knowledge, freedom, etc.
    fears: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    
    # Behavioral patterns
    decision_making_style: str = "balanced"  # analytical, emotional, impulsive, balanced
    conflict_style: str = "avoidant"  # confrontational, avoidant, collaborative, compromising
    risk_tolerance: float = 0.5  # 0.0 to 1.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
            "moral_alignment": self.moral_alignment.value,
            "primary_drives": self.primary_drives,
            "fears": self.fears,
            "secrets": self.secrets,
            "flaws": self.flaws,
            "strengths": self.strengths,
            "values": self.values,
            "decision_making_style": self.decision_making_style,
            "conflict_style": self.conflict_style,
            "risk_tolerance": self.risk_tolerance
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PersonalityProfile":
        """Create from dictionary."""
        return cls(
            openness=data.get("openness", 0.5),
            conscientiousness=data.get("conscientiousness", 0.5),
            extraversion=data.get("extraversion", 0.5),
            agreeableness=data.get("agreeableness", 0.5),
            neuroticism=data.get("neuroticism", 0.5),
            moral_alignment=MoralAlignment(
                data.get("moral_alignment", "true_neutral")
            ),
            primary_drives=data.get("primary_drives", []),
            fears=data.get("fears", []),
            secrets=data.get("secrets", []),
            flaws=data.get("flaws", []),
            strengths=data.get("strengths", []),
            values=data.get("values", []),
            decision_making_style=data.get("decision_making_style", "balanced"),
            conflict_style=data.get("conflict_style", "avoidant"),
            risk_tolerance=data.get("risk_tolerance", 0.5)
        )
    
    def get_trait_summary(self) -> str:
        """Get a summary of key personality traits."""
        traits = []
        
        if self.openness > 0.7:
            traits.append("highly creative and curious")
        elif self.openness < 0.3:
            traits.append("practical and conventional")
        
        if self.conscientiousness > 0.7:
            traits.append("organized and disciplined")
        elif self.conscientiousness < 0.3:
            traits.append("spontaneous and flexible")
        
        if self.extraversion > 0.7:
            traits.append("outgoing and energetic")
        elif self.extraversion < 0.3:
            traits.append("reserved and introspective")
        
        if self.agreeableness > 0.7:
            traits.append("compassionate and cooperative")
        elif self.agreeableness < 0.3:
            traits.append("competitive and skeptical")
        
        if self.neuroticism > 0.7:
            traits.append("emotionally sensitive")
        elif self.neuroticism < 0.3:
            traits.append("emotionally stable")
        
        return ", ".join(traits) if traits else "balanced personality"


@dataclass
class CharacterState:
    """Snapshot of character state at a point in narrative time."""
    chapter_id: int
    timestamp: str = ""
    emotional_state: str = "neutral"
    physical_state: str = "healthy"
    location: str = ""
    knowledge: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    relationships: Dict[str, float] = field(default_factory=dict)  # entity_id -> sentiment
    inventory: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "chapter_id": self.chapter_id,
            "timestamp": self.timestamp,
            "emotional_state": self.emotional_state,
            "physical_state": self.physical_state,
            "location": self.location,
            "knowledge": self.knowledge,
            "goals": self.goals,
            "relationships": self.relationships,
            "inventory": self.inventory,
            "notes": self.notes
        }


@dataclass
class ArcMoment:
    """A significant moment in character development."""
    chapter_id: int
    moment_type: MomentType
    description: str
    state_before: Optional[CharacterState] = None
    state_after: Optional[CharacterState] = None
    trigger_event: str = ""  # event_id
    changes: Dict[str, Any] = field(default_factory=dict)  # What changed
    significance: float = 0.5  # 0.0 to 1.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "chapter_id": self.chapter_id,
            "moment_type": self.moment_type.value,
            "description": self.description,
            "state_before": self.state_before.to_dict() if self.state_before else None,
            "state_after": self.state_after.to_dict() if self.state_after else None,
            "trigger_event": self.trigger_event,
            "changes": self.changes,
            "significance": self.significance
        }


@dataclass
class CharacterArc:
    """
    Manages character development trajectory.
    
    Tracks the character's journey from starting state to
    target state through key moments.
    """
    character_id: str
    arc_type: ArcType = ArcType.GROWTH
    starting_state: Optional[CharacterState] = None
    current_state: Optional[CharacterState] = None
    target_state: Optional[CharacterState] = None
    key_moments: List[ArcMoment] = field(default_factory=list)
    current_progress: float = 0.0  # 0.0 to 1.0
    
    def add_moment(self, moment: ArcMoment) -> None:
        """Add a moment to the arc."""
        self.key_moments.append(moment)
        self._update_progress()
    
    def _update_progress(self) -> None:
        """Update progress based on moments."""
        if not self.key_moments:
            self.current_progress = 0.0
            return
        
        # Weight by significance
        total_significance = sum(m.significance for m in self.key_moments)
        max_significance = 5.0  # Expected total significance for complete arc
        
        self.current_progress = min(1.0, total_significance / max_significance)
    
    def get_moments_by_type(self, moment_type: MomentType) -> List[ArcMoment]:
        """Get moments of a specific type."""
        return [m for m in self.key_moments if m.moment_type == moment_type]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "character_id": self.character_id,
            "arc_type": self.arc_type.value,
            "starting_state": self.starting_state.to_dict() if self.starting_state else None,
            "current_state": self.current_state.to_dict() if self.current_state else None,
            "target_state": self.target_state.to_dict() if self.target_state else None,
            "key_moments": [m.to_dict() for m in self.key_moments],
            "current_progress": self.current_progress
        }


@dataclass
class CharacterProfile:
    """
    Complete character profile combining all character data.
    
    This is the main character data structure that includes
    identity, personality, speech, and development arc.
    """
    # Identity
    character_id: str
    name: str
    aliases: List[str] = field(default_factory=list)
    role: str = "supporting"  # protagonist, antagonist, supporting, minor
    
    # Physical description
    age: Optional[int] = None
    gender: Optional[str] = None
    appearance: str = ""
    distinctive_features: List[str] = field(default_factory=list)
    
    # Background
    backstory: str = ""
    occupation: str = ""
    social_class: str = ""
    education: str = ""
    
    # Personality and voice
    personality: PersonalityProfile = field(default_factory=PersonalityProfile)
    speech_patterns: SpeechPatterns = field(default_factory=SpeechPatterns)
    
    # Development
    arc: Optional[CharacterArc] = None
    current_state: CharacterState = field(default_factory=lambda: CharacterState(chapter_id=0))
    
    # Narrative tracking
    first_appearance: int = 0  # chapter_id
    last_appearance: int = 0  # chapter_id
    total_appearances: int = 0
    pov_chapters: List[int] = field(default_factory=list)  # Chapters from this character's POV
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "character_id": self.character_id,
            "name": self.name,
            "aliases": self.aliases,
            "role": self.role,
            "age": self.age,
            "gender": self.gender,
            "appearance": self.appearance,
            "distinctive_features": self.distinctive_features,
            "backstory": self.backstory,
            "occupation": self.occupation,
            "social_class": self.social_class,
            "education": self.education,
            "personality": self.personality.to_dict(),
            "speech_patterns": self.speech_patterns.to_dict(),
            "arc": self.arc.to_dict() if self.arc else None,
            "current_state": self.current_state.to_dict(),
            "first_appearance": self.first_appearance,
            "last_appearance": self.last_appearance,
            "total_appearances": self.total_appearances,
            "pov_chapters": self.pov_chapters,
            "tags": self.tags,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CharacterProfile":
        """Create from dictionary."""
        personality_data = data.get("personality", {})
        speech_data = data.get("speech_patterns", {})
        state_data = data.get("current_state", {})
        arc_data = data.get("arc")
        
        personality = PersonalityProfile.from_dict(personality_data)
        speech_patterns = SpeechPatterns.from_dict(speech_data)
        current_state = CharacterState(
            chapter_id=state_data.get("chapter_id", 0),
            timestamp=state_data.get("timestamp", ""),
            emotional_state=state_data.get("emotional_state", "neutral"),
            physical_state=state_data.get("physical_state", "healthy"),
            location=state_data.get("location", ""),
            knowledge=state_data.get("knowledge", []),
            goals=state_data.get("goals", []),
            relationships=state_data.get("relationships", {}),
            inventory=state_data.get("inventory", []),
            notes=state_data.get("notes", "")
        )
        
        arc = None
        if arc_data:
            arc = CharacterArc(
                character_id=arc_data.get("character_id", data.get("character_id", "")),
                arc_type=ArcType(arc_data.get("arc_type", "growth")),
                current_progress=arc_data.get("current_progress", 0.0)
            )
        
        return cls(
            character_id=data.get("character_id", ""),
            name=data.get("name", ""),
            aliases=data.get("aliases", []),
            role=data.get("role", "supporting"),
            age=data.get("age"),
            gender=data.get("gender"),
            appearance=data.get("appearance", ""),
            distinctive_features=data.get("distinctive_features", []),
            backstory=data.get("backstory", ""),
            occupation=data.get("occupation", ""),
            social_class=data.get("social_class", ""),
            education=data.get("education", ""),
            personality=personality,
            speech_patterns=speech_patterns,
            arc=arc,
            current_state=current_state,
            first_appearance=data.get("first_appearance", 0),
            last_appearance=data.get("last_appearance", 0),
            total_appearances=data.get("total_appearances", 0),
            pov_chapters=data.get("pov_chapters", []),
            tags=data.get("tags", []),
            notes=data.get("notes", "")
        )
    
    def get_description(self) -> str:
        """Get a prose description of the character."""
        parts = []
        
        # Basic info
        parts.append(f"{self.name}")
        
        if self.age:
            parts.append(f", {self.age} years old")
        
        if self.gender:
            parts.append(f" {self.gender}")
        
        if self.occupation:
            parts.append(f", works as a {self.occupation}")
        
        # Appearance
        if self.appearance:
            parts.append(f". {self.appearance}")
        
        # Personality
        parts.append(f". {self.name} is {self.personality.get_trait_summary()}")
        
        # Role
        if self.role == "protagonist":
            parts.append(". As the protagonist, ")
        elif self.role == "antagonist":
            parts.append(". As the antagonist, ")
        
        return "".join(parts)
    
    def update_appearance(self, chapter_id: int) -> None:
        """Update appearance tracking."""
        if self.first_appearance == 0:
            self.first_appearance = chapter_id
        self.last_appearance = chapter_id
        self.total_appearances += 1


class CharacterProfileManager:
    """
    Manages character profiles for a book.
    
    Provides functionality to create, store, retrieve, and
    manage character profiles throughout the writing process.
    """
    
    def __init__(self):
        """Initialize the character profile manager."""
        self.profiles: Dict[str, CharacterProfile] = {}
        self.name_index: Dict[str, str] = {}  # name -> character_id
    
    def create_profile(
        self,
        name: str,
        role: str = "supporting",
        **kwargs
    ) -> CharacterProfile:
        """
        Create a new character profile.
        
        Args:
            name: Character name
            role: Character role (protagonist, antagonist, supporting, minor)
            **kwargs: Additional profile attributes
        
        Returns:
            Created CharacterProfile
        """
        character_id = self._generate_id(name)
        
        profile = CharacterProfile(
            character_id=character_id,
            name=name,
            role=role,
            **kwargs
        )
        
        self.profiles[character_id] = profile
        self.name_index[name.lower()] = character_id
        
        return profile
    
    def get_profile(self, character_id: str) -> Optional[CharacterProfile]:
        """Get a character profile by ID."""
        return self.profiles.get(character_id)
    
    def get_profile_by_name(self, name: str) -> Optional[CharacterProfile]:
        """Get a character profile by name."""
        character_id = self.name_index.get(name.lower())
        if character_id:
            return self.profiles.get(character_id)
        return None
    
    def update_profile(self, profile: CharacterProfile) -> None:
        """Update a character profile."""
        self.profiles[profile.character_id] = profile
        self.name_index[profile.name.lower()] = profile.character_id
    
    def delete_profile(self, character_id: str) -> bool:
        """Delete a character profile."""
        if character_id in self.profiles:
            profile = self.profiles[character_id]
            del self.profiles[character_id]
            if profile.name.lower() in self.name_index:
                del self.name_index[profile.name.lower()]
            return True
        return False
    
    def get_all_profiles(self) -> List[CharacterProfile]:
        """Get all character profiles."""
        return list(self.profiles.values())
    
    def get_by_role(self, role: str) -> List[CharacterProfile]:
        """Get all characters with a specific role."""
        return [p for p in self.profiles.values() if p.role == role]
    
    def get_protagonists(self) -> List[CharacterProfile]:
        """Get all protagonist characters."""
        return self.get_by_role("protagonist")
    
    def get_antagonists(self) -> List[CharacterProfile]:
        """Get all antagonist characters."""
        return self.get_by_role("antagonist")
    
    def _generate_id(self, name: str) -> str:
        """Generate a unique character ID."""
        import hashlib
        base = name.lower().replace(" ", "_")
        hash_suffix = hashlib.md5(name.encode()).hexdigest()[:6]
        return f"char_{base}_{hash_suffix}"
    
    def to_dict(self) -> dict:
        """Convert all profiles to dictionary."""
        return {
            "profiles": {
                cid: profile.to_dict()
                for cid, profile in self.profiles.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CharacterProfileManager":
        """Create manager from dictionary."""
        manager = cls()
        profiles_data = data.get("profiles", {})
        
        for cid, profile_data in profiles_data.items():
            profile = CharacterProfile.from_dict(profile_data)
            manager.profiles[cid] = profile
            manager.name_index[profile.name.lower()] = cid
        
        return manager


__all__ = [
    "MoralAlignment",
    "ArcType",
    "MomentType",
    "SpeechPatterns",
    "PersonalityProfile",
    "CharacterState",
    "ArcMoment",
    "CharacterArc",
    "CharacterProfile",
    "CharacterProfileManager",
]