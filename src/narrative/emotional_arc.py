"""
Emotional Arc Planning Module for BookWriterAI.

This module provides emotional arc planning and tension management
for narrative content, based on research in narrative emotional structures.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import math


logger = logging.getLogger("BookWriterAI")


class ArcShape(Enum):
    """
    Story shape types based on Kurt Vonnegut's story shapes.
    
    These represent the emotional trajectory of a narrative.
    """
    RAGS_TO_RICHES = "rags_to_riches"  # Steady rise
    TRAGEDY = "tragedy"  # Fall from grace
    MAN_IN_HOLE = "man_in_hole"  # Fall then rise
    ICARUS = "icarus"  # Rise then fall
    CINDERELLA = "cinderella"  # Rise, fall, rise
    OEDIPUS = "oedipus"  # Fall, rise, fall
    KAFKA = "kafka"  # Steady decline
    BILDUNGSROMAN = "bildungsroman"  # Gradual growth with setbacks


class Emotion(Enum):
    """Primary emotions for narrative beats."""
    HOPE = "hope"
    FEAR = "fear"
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    ANTICIPATION = "anticipation"
    TRUST = "trust"
    LOVE = "love"
    HATE = "hate"
    CONFUSION = "confusion"
    RELIEF = "relief"
    TENSION = "tension"
    WONDER = "wonder"
    SATISFACTION = "satisfaction"


class ResolutionStyle(Enum):
    """How emotional beats are resolved."""
    IMMEDIATE = "immediate"  # Resolved quickly
    DELAYED = "delayed"  # Resolved later in narrative
    UNRESOLVED = "unresolved"  # Left open (for series)
    PARTIAL = "partial"  # Partially resolved


@dataclass
class EmotionalBeat:
    """
    A single emotional moment in the narrative.
    
    Represents a planned emotional impact at a specific point
    in the story.
    """
    position: float  # 0.0 to 1.0 of content
    target_emotion: Emotion
    intensity: float  # 0.0 to 1.0
    duration: float = 0.1  # Relative duration (0.0 to 1.0)
    trigger_event: str = ""  # What causes this emotion
    resolution_style: ResolutionStyle = ResolutionStyle.IMMEDIATE
    resolution_position: Optional[float] = None  # When resolved
    description: str = ""
    character_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "position": self.position,
            "target_emotion": self.target_emotion.value,
            "intensity": self.intensity,
            "duration": self.duration,
            "trigger_event": self.trigger_event,
            "resolution_style": self.resolution_style.value,
            "resolution_position": self.resolution_position,
            "description": self.description,
            "character_ids": self.character_ids
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EmotionalBeat":
        """Create from dictionary."""
        return cls(
            position=data.get("position", 0.0),
            target_emotion=Emotion(data.get("target_emotion", "hope")),
            intensity=data.get("intensity", 0.5),
            duration=data.get("duration", 0.1),
            trigger_event=data.get("trigger_event", ""),
            resolution_style=ResolutionStyle(data.get("resolution_style", "immediate")),
            resolution_position=data.get("resolution_position"),
            description=data.get("description", ""),
            character_ids=data.get("character_ids", [])
        )


@dataclass
class EmotionalArc:
    """
    Defines emotional trajectory for content.
    
    Manages the planned emotional journey through a narrative,
    including beats, tension curve, and resolution.
    """
    arc_id: str
    arc_shape: ArcShape = ArcShape.MAN_IN_HOLE
    beats: List[EmotionalBeat] = field(default_factory=list)
    current_position: float = 0.0
    
    # Arc parameters
    starting_emotion: Emotion = Emotion.HOPE
    ending_emotion: Emotion = Emotion.SATISFACTION
    emotional_range: Tuple[float, float] = (0.2, 0.9)  # Min and max intensity
    
    # Tension parameters
    baseline_tension: float = 0.3
    peak_tension: float = 0.9
    tension_curve: List[float] = field(default_factory=list)
    
    def add_beat(self, beat: EmotionalBeat) -> None:
        """Add an emotional beat to the arc."""
        self.beats.append(beat)
        self.beats.sort(key=lambda b: b.position)
    
    def get_beats_at_position(self, position: float, tolerance: float = 0.05) -> List[EmotionalBeat]:
        """Get beats near a specific position."""
        return [
            b for b in self.beats
            if abs(b.position - position) <= tolerance
        ]
    
    def get_emotional_state(self, position: float) -> Dict[str, Any]:
        """
        Get the emotional state at a specific position.
        
        Returns the dominant emotion and intensity based on
        the arc shape and nearby beats.
        """
        # Get base emotion from arc shape
        base_intensity = self._get_base_intensity(position)
        
        # Modify based on nearby beats
        active_beats = self.get_beats_at_position(position, 0.1)
        
        if active_beats:
            # Use the most intense beat
            dominant_beat = max(active_beats, key=lambda b: b.intensity)
            return {
                "emotion": dominant_beat.target_emotion,
                "intensity": dominant_beat.intensity,
                "active_beats": [b.to_dict() for b in active_beats]
            }
        
        # Use arc shape to determine emotion
        emotion = self._get_arc_emotion(position)
        
        return {
            "emotion": emotion,
            "intensity": base_intensity,
            "active_beats": []
        }
    
    def _get_base_intensity(self, position: float) -> float:
        """Get base intensity from arc shape at position."""
        min_i, max_i = self.emotional_range
        range_i = max_i - min_i
        
        shape_intensities = {
            ArcShape.RAGS_TO_RICHES: lambda p: min_i + range_i * p,
            ArcShape.TRAGEDY: lambda p: max_i - range_i * p,
            ArcShape.MAN_IN_HOLE: lambda p: min_i + range_i * (1 - abs(2 * p - 1)),
            ArcShape.ICARUS: lambda p: max_i - range_i * (1 - abs(2 * p - 1)),
            ArcShape.CINDERELLA: lambda p: min_i + range_i * (
                0.5 + 0.5 * math.sin(3 * math.pi * p - math.pi / 2)
            ),
            ArcShape.OEDIPUS: lambda p: max_i - range_i * (
                0.5 + 0.5 * math.sin(3 * math.pi * p - math.pi / 2)
            ),
            ArcShape.KAFKA: lambda p: max_i - range_i * p * 0.7,
            ArcShape.BILDUNGSROMAN: lambda p: min_i + range_i * (
                p + 0.1 * math.sin(5 * math.pi * p)
            )
        }
        
        calc_func = shape_intensities.get(self.arc_shape)
        if calc_func:
            return max(min_i, min(max_i, calc_func(position)))
        
        return (min_i + max_i) / 2
    
    def _get_arc_emotion(self, position: float) -> Emotion:
        """Get the dominant emotion from arc shape at position."""
        # Simplified mapping based on arc shape and position
        if self.arc_shape == ArcShape.RAGS_TO_RICHES:
            if position < 0.3:
                return Emotion.HOPE
            elif position < 0.7:
                return Emotion.ANTICIPATION
            else:
                return Emotion.JOY
        
        elif self.arc_shape == ArcShape.TRAGEDY:
            if position < 0.3:
                return Emotion.JOY
            elif position < 0.7:
                return Emotion.FEAR
            else:
                return Emotion.SADNESS
        
        elif self.arc_shape == ArcShape.MAN_IN_HOLE:
            if position < 0.4:
                return Emotion.FEAR
            elif position < 0.6:
                return Emotion.HOPE
            else:
                return Emotion.JOY
        
        elif self.arc_shape == ArcShape.ICARUS:
            if position < 0.4:
                return Emotion.JOY
            elif position < 0.6:
                return Emotion.FEAR
            else:
                return Emotion.SADNESS
        
        elif self.arc_shape == ArcShape.CINDERELLA:
            if position < 0.3:
                return Emotion.HOPE
            elif position < 0.5:
                return Emotion.SADNESS
            elif position < 0.8:
                return Emotion.ANTICIPATION
            else:
                return Emotion.JOY
        
        return self.starting_emotion
    
    def generate_tension_curve(self, num_points: int = 20) -> List[float]:
        """Generate tension values across the arc."""
        curve = []
        for i in range(num_points):
            position = i / (num_points - 1)
            intensity = self._get_base_intensity(position)
            # Tension correlates with intensity but has its own dynamics
            tension = self.baseline_tension + (
                (self.peak_tension - self.baseline_tension) * intensity
            )
            curve.append(tension)
        
        self.tension_curve = curve
        return curve
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "arc_id": self.arc_id,
            "arc_shape": self.arc_shape.value,
            "beats": [b.to_dict() for b in self.beats],
            "current_position": self.current_position,
            "starting_emotion": self.starting_emotion.value,
            "ending_emotion": self.ending_emotion.value,
            "emotional_range": self.emotional_range,
            "baseline_tension": self.baseline_tension,
            "peak_tension": self.peak_tension,
            "tension_curve": self.tension_curve
        }


@dataclass
class TensionProfile:
    """Tension analysis of content."""
    overall_tension: float = 0.5
    tension_variance: float = 0.0
    peak_tension: float = 0.5
    peak_position: float = 0.5
    low_points: List[float] = field(default_factory=list)
    high_points: List[float] = field(default_factory=list)
    tension_curve: List[float] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "overall_tension": self.overall_tension,
            "tension_variance": self.tension_variance,
            "peak_tension": self.peak_tension,
            "peak_position": self.peak_position,
            "low_points": self.low_points,
            "high_points": self.high_points,
            "tension_curve": self.tension_curve
        }


@dataclass
class TensionAdjustment:
    """Suggested adjustment to tension."""
    position: float
    current_tension: float
    target_tension: float
    adjustment_type: str  # increase, decrease, maintain
    suggested_technique: str
    reason: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "position": self.position,
            "current_tension": self.current_tension,
            "target_tension": self.target_tension,
            "adjustment_type": self.adjustment_type,
            "suggested_technique": self.suggested_technique,
            "reason": self.reason
        }


class EmotionalArcPlanner:
    """
    Plans and manages emotional arcs.
    
    Uses research on narrative emotional structures to plan
    the emotional journey through a book or chapter.
    """
    
    # Standard arc templates by genre
    GENRE_ARC_TEMPLATES = {
        "thriller": {
            "shape": ArcShape.MAN_IN_HOLE,
            "baseline_tension": 0.5,
            "peak_tension": 0.95,
            "key_beats": [
                (0.1, Emotion.FEAR, 0.6),  # Inciting incident
                (0.25, Emotion.TENSION, 0.7),  # First obstacle
                (0.5, Emotion.SURPRISE, 0.8),  # Midpoint twist
                (0.75, Emotion.FEAR, 0.9),  # All is lost
                (0.9, Emotion.TENSION, 0.95),  # Climax
                (0.98, Emotion.RELIEF, 0.5),  # Resolution
            ]
        },
        "romance": {
            "shape": ArcShape.CINDERELLA,
            "baseline_tension": 0.3,
            "peak_tension": 0.7,
            "key_beats": [
                (0.1, Emotion.ANTICIPATION, 0.5),  # Meet cute
                (0.25, Emotion.LOVE, 0.6),  # Growing attraction
                (0.5, Emotion.SADNESS, 0.7),  # Conflict/separation
                (0.75, Emotion.HOPE, 0.6),  # Reconciliation attempt
                (0.9, Emotion.LOVE, 0.8),  # Declaration
                (0.98, Emotion.JOY, 0.7),  # Happy ending
            ]
        },
        "fantasy": {
            "shape": ArcShape.BILDUNGSROMAN,
            "baseline_tension": 0.4,
            "peak_tension": 0.85,
            "key_beats": [
                (0.1, Emotion.WONDER, 0.5),  # Discovery
                (0.25, Emotion.ANTICIPATION, 0.6),  # Call to adventure
                (0.5, Emotion.FEAR, 0.7),  # Major challenge
                (0.75, Emotion.TENSION, 0.8),  # Confrontation
                (0.9, Emotion.SATISFACTION, 0.7),  # Victory
                (0.98, Emotion.HOPE, 0.6),  # New beginning
            ]
        },
        "mystery": {
            "shape": ArcShape.MAN_IN_HOLE,
            "baseline_tension": 0.4,
            "peak_tension": 0.8,
            "key_beats": [
                (0.05, Emotion.SURPRISE, 0.6),  # Discovery of crime
                (0.2, Emotion.CONFUSION, 0.5),  # Investigation begins
                (0.4, Emotion.ANTICIPATION, 0.6),  # Clue found
                (0.6, Emotion.SURPRISE, 0.7),  # Twist
                (0.8, Emotion.TENSION, 0.8),  # Confrontation
                (0.95, Emotion.SATISFACTION, 0.6),  # Resolution
            ]
        },
        "literary": {
            "shape": ArcShape.BILDUNGSROMAN,
            "baseline_tension": 0.3,
            "peak_tension": 0.6,
            "key_beats": [
                (0.15, Emotion.CONFUSION, 0.4),  # Question raised
                (0.35, Emotion.SADNESS, 0.5),  # Struggle
                (0.55, Emotion.WONDER, 0.5),  # Insight
                (0.75, Emotion.HOPE, 0.5),  # Growth
                (0.95, Emotion.SATISFACTION, 0.4),  # Resolution
            ]
        }
    }
    
    def __init__(self, llm_client=None):
        """
        Initialize the emotional arc planner.
        
        Args:
            llm_client: LLM client for advanced planning
        """
        self.llm_client = llm_client
    
    def plan_book_arc(
        self,
        genre: str,
        theme: str,
        target_emotional_experience: str = "engaging",
        customizations: Optional[Dict[str, Any]] = None
    ) -> EmotionalArc:
        """
        Plan the overall emotional arc for a book.
        
        Args:
            genre: Book genre
            theme: Central theme
            target_emotional_experience: Desired reader experience
            customizations: Optional customizations
        
        Returns:
            EmotionalArc for the book
        """
        import hashlib
        
        # Generate arc ID
        arc_id = f"arc_{hashlib.md5(f'{genre}_{theme}'.encode()).hexdigest()[:8]}"
        
        # Get template for genre
        template = self.GENRE_ARC_TEMPLATES.get(
            genre.lower(),
            self.GENRE_ARC_TEMPLATES["literary"]
        )
        
        # Create arc
        arc = EmotionalArc(
            arc_id=arc_id,
            arc_shape=template["shape"],
            baseline_tension=template["baseline_tension"],
            peak_tension=template["peak_tension"]
        )
        
        # Add key beats from template
        for position, emotion, intensity in template["key_beats"]:
            beat = EmotionalBeat(
                position=position,
                target_emotion=emotion,
                intensity=intensity
            )
            arc.add_beat(beat)
        
        # Apply customizations
        if customizations:
            if "arc_shape" in customizations:
                arc.arc_shape = ArcShape(customizations["arc_shape"])
            if "baseline_tension" in customizations:
                arc.baseline_tension = customizations["baseline_tension"]
            if "peak_tension" in customizations:
                arc.peak_tension = customizations["peak_tension"]
        
        # Generate tension curve
        arc.generate_tension_curve()
        
        return arc
    
    def plan_chapter_arc(
        self,
        chapter_position: float,  # Position in book (0.0 to 1.0)
        book_arc: EmotionalArc,
        chapter_content: str = "",
        chapter_summary: str = ""
    ) -> List[EmotionalBeat]:
        """
        Plan emotional beats for a chapter.
        
        Args:
            chapter_position: Where this chapter falls in the book
            book_arc: The overall book arc
            chapter_content: Existing chapter content (if any)
            chapter_summary: Summary of chapter events
        
        Returns:
            List of EmotionalBeats for the chapter
        """
        # Get the emotional state from the book arc at this position
        book_state = book_arc.get_emotional_state(chapter_position)
        
        # Create chapter-specific beats
        beats = []
        
        # Opening beat - establish chapter emotion
        opening_beat = EmotionalBeat(
            position=0.0,
            target_emotion=book_state["emotion"],
            intensity=book_state["intensity"] * 0.8,
            description=f"Chapter opening - {book_state['emotion'].value}"
        )
        beats.append(opening_beat)
        
        # Middle beat - develop or contrast
        mid_emotion = self._get_contrasting_emotion(book_state["emotion"])
        mid_beat = EmotionalBeat(
            position=0.5,
            target_emotion=mid_emotion,
            intensity=book_state["intensity"] * 0.9,
            description=f"Chapter development - {mid_emotion.value}"
        )
        beats.append(mid_beat)
        
        # Closing beat - set up next chapter
        next_position = min(1.0, chapter_position + 0.1)
        next_state = book_arc.get_emotional_state(next_position)
        closing_beat = EmotionalBeat(
            position=0.9,
            target_emotion=next_state["emotion"],
            intensity=next_state["intensity"],
            description=f"Chapter closing - leading to {next_state['emotion'].value}"
        )
        beats.append(closing_beat)
        
        return beats
    
    def _get_contrasting_emotion(self, emotion: Emotion) -> Emotion:
        """Get an emotion that contrasts with the given one."""
        contrasts = {
            Emotion.HOPE: Emotion.FEAR,
            Emotion.FEAR: Emotion.HOPE,
            Emotion.JOY: Emotion.SADNESS,
            Emotion.SADNESS: Emotion.JOY,
            Emotion.LOVE: Emotion.HATE,
            Emotion.HATE: Emotion.LOVE,
            Emotion.TENSION: Emotion.RELIEF,
            Emotion.RELIEF: Emotion.TENSION,
            Emotion.ANTICIPATION: Emotion.SURPRISE,
            Emotion.SURPRISE: Emotion.ANTICIPATION,
            Emotion.TRUST: Emotion.FEAR,
            Emotion.CONFUSION: Emotion.WONDER,
            Emotion.WONDER: Emotion.CONFUSION,
            Emotion.SATISFACTION: Emotion.ANTICIPATION,
            Emotion.ANGER: Emotion.SADNESS,
            Emotion.DISGUST: Emotion.SURPRISE
        }
        return contrasts.get(emotion, emotion)
    
    def validate_emotional_progression(
        self,
        content: str,
        planned_beats: List[EmotionalBeat]
    ) -> dict:
        """
        Validate content matches planned emotional trajectory.
        
        Args:
            content: Generated content
            planned_beats: Planned emotional beats
        
        Returns:
            Validation report
        """
        # Analyze content for emotional content
        detected_emotions = self._analyze_emotions(content)
        
        # Compare with planned beats
        matches = []
        mismatches = []
        
        for beat in planned_beats:
            # Find corresponding content section
            content_position = int(beat.position * len(content.split()))
            content_section = " ".join(
                content.split()[max(0, content_position - 50):content_position + 50]
            )
            
            # Check if target emotion is present
            target = beat.target_emotion.value.lower()
            if target in content_section.lower():
                matches.append({
                    "beat": beat.to_dict(),
                    "found": True
                })
            else:
                mismatches.append({
                    "beat": beat.to_dict(),
                    "found": False,
                    "suggestion": f"Consider adding {target} emotional content"
                })
        
        return {
            "matches": matches,
            "mismatches": mismatches,
            "detected_emotions": detected_emotions,
            "compliance_score": len(matches) / len(planned_beats) if planned_beats else 1.0
        }
    
    def _analyze_emotions(self, content: str) -> Dict[str, float]:
        """Analyze content for emotional content."""
        emotion_keywords = {
            "hope": ["hope", "hopeful", "optimistic", "dream", "wish"],
            "fear": ["fear", "afraid", "scared", "terror", "dread"],
            "joy": ["joy", "happy", "delighted", "elated", "cheerful"],
            "sadness": ["sad", "sorrow", "grief", "melancholy", "tears"],
            "anger": ["anger", "furious", "rage", "irate", "wrath"],
            "love": ["love", "adore", "cherish", "devoted", "passion"],
            "tension": ["tension", "suspense", "anxiety", "nervous", "edge"],
            "surprise": ["surprise", "shock", "astonished", "amazed", "unexpected"]
        }
        
        content_lower = content.lower()
        detected = {}
        
        for emotion, keywords in emotion_keywords.items():
            count = sum(content_lower.count(kw) for kw in keywords)
            if count > 0:
                # Normalize by content length
                normalized = count / (len(content.split()) / 100)
                detected[emotion] = min(1.0, normalized)
        
        return detected


class TensionManager:
    """
    Manages narrative tension.
    
    Analyzes and suggests adjustments to maintain optimal
    tension throughout the narrative.
    """
    
    # Tension-building techniques
    TENSION_TECHNIQUES = {
        "increase": [
            "Add a time constraint or deadline",
            "Introduce a new obstacle or complication",
            "Reveal a hidden threat",
            "Create a moral dilemma",
            "Increase stakes",
            "Add conflict between characters",
            "Use dramatic irony (reader knows more than character)",
            "Create anticipation through foreshadowing"
        ],
        "decrease": [
            "Resolve a subplot",
            "Provide a moment of relief or humor",
            "Allow character reflection",
            "Reveal positive information",
            "Create a bonding moment between characters",
            "Offer a temporary safe haven"
        ],
        "maintain": [
            "Sustain current conflict",
            "Add complexity without resolution",
            "Introduce a mystery element",
            "Create anticipation for upcoming events"
        ]
    }
    
    def __init__(self, llm_client=None):
        """
        Initialize the tension manager.
        
        Args:
            llm_client: LLM client for advanced analysis
        """
        self.llm_client = llm_client
    
    def calculate_tension_profile(
        self,
        content: str
    ) -> TensionProfile:
        """
        Analyze tension throughout content.
        
        Args:
            content: Text to analyze
        
        Returns:
            TensionProfile with analysis
        """
        # Split content into sections
        words = content.split()
        section_size = max(100, len(words) // 20)
        
        tension_curve = []
        
        for i in range(0, len(words), section_size):
            section = " ".join(words[i:i + section_size])
            tension = self._calculate_section_tension(section)
            tension_curve.append(tension)
        
        if not tension_curve:
            return TensionProfile()
        
        # Calculate profile metrics
        overall = sum(tension_curve) / len(tension_curve)
        variance = sum((t - overall) ** 2 for t in tension_curve) / len(tension_curve)
        peak = max(tension_curve)
        peak_pos = tension_curve.index(peak) / len(tension_curve)
        
        # Find low and high points
        avg = overall
        low_points = [i / len(tension_curve) for i, t in enumerate(tension_curve) if t < avg - 0.2]
        high_points = [i / len(tension_curve) for i, t in enumerate(tension_curve) if t > avg + 0.2]
        
        return TensionProfile(
            overall_tension=overall,
            tension_variance=variance,
            peak_tension=peak,
            peak_position=peak_pos,
            low_points=low_points,
            high_points=high_points,
            tension_curve=tension_curve
        )
    
    def _calculate_section_tension(self, section: str) -> float:
        """Calculate tension for a text section."""
        # Tension indicators
        high_tension_words = [
            'danger', 'threat', 'fear', 'terror', 'panic', 'crisis',
            'urgent', 'deadline', 'risk', 'peril', 'menace', 'doom'
        ]
        
        medium_tension_words = [
            'worry', 'concern', 'tension', 'stress', 'pressure',
            'conflict', 'struggle', 'challenge', 'obstacle', 'problem'
        ]
        
        low_tension_words = [
            'peace', 'calm', 'relax', 'safe', 'secure', 'comfort',
            'ease', 'tranquil', 'serene', 'rest', 'quiet'
        ]
        
        section_lower = section.lower()
        
        high_count = sum(section_lower.count(w) for w in high_tension_words)
        medium_count = sum(section_lower.count(w) for w in medium_tension_words)
        low_count = sum(section_lower.count(w) for w in low_tension_words)
        
        # Calculate tension score
        word_count = len(section.split())
        if word_count == 0:
            return 0.5
        
        # Weighted calculation
        tension = (
            (high_count * 0.3) +
            (medium_count * 0.15) -
            (low_count * 0.2)
        ) / (word_count / 100)
        
        # Normalize to 0-1 range
        return max(0.0, min(1.0, 0.5 + tension))
    
    def suggest_tension_adjustments(
        self,
        current_profile: TensionProfile,
        target_profile: TensionProfile
    ) -> List[TensionAdjustment]:
        """
        Suggest adjustments to match target tension.
        
        Args:
            current_profile: Current tension analysis
            target_profile: Target tension profile
        
        Returns:
            List of TensionAdjustment suggestions
        """
        adjustments = []
        
        # Compare tension curves
        current_curve = current_profile.tension_curve
        target_curve = target_profile.tension_curve
        
        if not current_curve or not target_curve:
            return adjustments
        
        # Align curve lengths
        min_len = min(len(current_curve), len(target_curve))
        
        for i in range(min_len):
            position = i / min_len
            current = current_curve[i]
            target = target_curve[i]
            
            diff = target - current
            
            if abs(diff) > 0.15:  # Significant difference
                if diff > 0:
                    adjustment_type = "increase"
                else:
                    adjustment_type = "decrease"
                
                # Select technique
                import random
                techniques = self.TENSION_TECHNIQUES[adjustment_type]
                technique = random.choice(techniques)
                
                adjustments.append(TensionAdjustment(
                    position=position,
                    current_tension=current,
                    target_tension=target,
                    adjustment_type=adjustment_type,
                    suggested_technique=technique,
                    reason=f"Tension {'too low' if diff > 0 else 'too high'} at {position:.0%}"
                ))
        
        return adjustments
    
    def get_tension_at_position(
        self,
        content: str,
        position: float
    ) -> float:
        """Get tension at a specific position in content."""
        words = content.split()
        if not words:
            return 0.5
        
        # Get section around position
        center = int(position * len(words))
        window = 50  # words
        
        section = " ".join(
            words[max(0, center - window):min(len(words), center + window)]
        )
        
        return self._calculate_section_tension(section)


__all__ = [
    "ArcShape",
    "Emotion",
    "ResolutionStyle",
    "EmotionalBeat",
    "EmotionalArc",
    "TensionProfile",
    "TensionAdjustment",
    "EmotionalArcPlanner",
    "TensionManager",
]