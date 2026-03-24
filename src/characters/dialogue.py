"""
Character Interaction Engine for BookWriterAI.

This module provides dialogue generation and relationship dynamics
for character interactions.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class InteractionType(Enum):
    """Types of character interactions."""
    CONVERSATION = "conversation"
    CONFRONTATION = "confrontation"
    COLLABORATION = "collaboration"
    ROMANTIC = "romantic"
    CONFLICT = "conflict"
    NEGOTIATION = "negotiation"
    INTERROGATION = "interrogation"
    REUNION = "reunion"
    FAREWELL = "farewell"


class EmotionalTone(Enum):
    """Emotional tones for dialogue."""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    ROMANTIC = "romantic"
    TENSE = "tense"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"


@dataclass
class InteractionDynamics:
    """
    Calculated dynamics for an interaction between characters.
    
    Determines how characters should interact based on their
    relationship, emotional states, and the situation.
    """
    character_a: str  # character_id
    character_b: str  # character_id
    relationship_strength: float = 0.5  # 0.0 to 1.0
    relationship_sentiment: float = 0.0  # -1.0 to 1.0
    power_dynamic: float = 0.0  # -1.0 (B dominant) to 1.0 (A dominant)
    trust_level: float = 0.5  # 0.0 to 1.0
    hidden_agendas: List[str] = field(default_factory=list)
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    tension_level: float = 0.3  # 0.0 to 1.0
    topics_to_avoid: List[str] = field(default_factory=list)
    shared_history: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "character_a": self.character_a,
            "character_b": self.character_b,
            "relationship_strength": self.relationship_strength,
            "relationship_sentiment": self.relationship_sentiment,
            "power_dynamic": self.power_dynamic,
            "trust_level": self.trust_level,
            "hidden_agendas": self.hidden_agendas,
            "emotional_tone": self.emotional_tone.value,
            "tension_level": self.tension_level,
            "topics_to_avoid": self.topics_to_avoid,
            "shared_history": self.shared_history
        }


@dataclass
class DialogueContext:
    """Context for dialogue generation."""
    speaker_id: str
    listener_ids: List[str]
    situation: str
    emotional_state: str
    intent: str  # What the speaker wants to achieve
    subtext: Optional[str] = None  # What's not being said
    recent_events: List[str] = field(default_factory=list)
    location: str = ""
    time_of_day: str = ""
    other_characters_present: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "speaker_id": self.speaker_id,
            "listener_ids": self.listener_ids,
            "situation": self.situation,
            "emotional_state": self.emotional_state,
            "intent": self.intent,
            "subtext": self.subtext,
            "recent_events": self.recent_events,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "other_characters_present": self.other_characters_present
        }


@dataclass
class DialogueLine:
    """A single line of dialogue."""
    speaker_id: str
    content: str
    action: Optional[str] = None  # Action tag
    internal_thought: Optional[str] = None
    emotional_cue: Optional[str] = None
    is_interruption: bool = False
    is_response: bool = False
    
    def to_prose(self) -> str:
        """Convert to prose format."""
        parts = []
        
        if self.action:
            parts.append(self.action)
        
        parts.append(f'"{self.content}"')
        
        if self.emotional_cue:
            parts.append(f"[{self.emotional_cue}]")
        
        return " ".join(parts)


@dataclass
class GeneratedDialogue:
    """Result of dialogue generation."""
    lines: List[DialogueLine]
    narrative_bridge: str = ""
    interaction_type: InteractionType = InteractionType.CONVERSATION
    emotional_arc: List[EmotionalTone] = field(default_factory=list)
    
    def to_prose(self) -> str:
        """Convert to prose format."""
        parts = []
        
        if self.narrative_bridge:
            parts.append(self.narrative_bridge)
        
        for line in self.lines:
            parts.append(line.to_prose())
        
        return "\n\n".join(parts)


class DialogueGenerator:
    """
    Generates character-appropriate dialogue.
    
    Creates dialogue that reflects:
    - Speaker's personality and voice
    - Relationship dynamics with listeners
    - Current emotional state
    - Communication intent
    """
    
    def __init__(self, llm_client=None, character_profiles=None):
        """
        Initialize the dialogue generator.
        
        Args:
            llm_client: LLM client for generation
            character_profiles: CharacterProfileManager instance
        """
        self.llm_client = llm_client
        self.character_profiles = character_profiles
    
    def generate_dialogue(
        self,
        speaker_id: str,
        listener_ids: List[str],
        context: str,
        emotional_state: str,
        intent: str,
        interaction_dynamics: Optional[InteractionDynamics] = None,
        max_lines: int = 5
    ) -> GeneratedDialogue:
        """
        Generate dialogue for a character.
        
        Args:
            speaker_id: ID of the speaking character
            listener_ids: IDs of listener characters
            context: Situation context
            emotional_state: Speaker's emotional state
            intent: What the speaker wants to achieve
            interaction_dynamics: Pre-calculated dynamics
            max_lines: Maximum dialogue lines
        
        Returns:
            GeneratedDialogue with lines
        """
        # Get character profiles
        speaker = self._get_profile(speaker_id)
        listeners = [self._get_profile(lid) for lid in listener_ids]
        
        if not speaker:
            return GeneratedDialogue(
                lines=[DialogueLine(
                    speaker_id=speaker_id,
                    content="[Character not found]"
                )]
            )
        
        # Build dialogue prompt
        prompt = self._build_dialogue_prompt(
            speaker=speaker,
            listeners=listeners,
            context=context,
            emotional_state=emotional_state,
            intent=intent,
            interaction_dynamics=interaction_dynamics,
            max_lines=max_lines
        )
        
        # Generate dialogue
        if self.llm_client:
            try:
                response = self.llm_client.generate(
                    prompt,
                    max_tokens=500 * max_lines
                )
                
                return self._parse_dialogue_response(
                    response,
                    speaker_id,
                    listener_ids
                )
            
            except Exception as e:
                logger.warning(f"Dialogue generation failed: {e}")
        
        # Fallback: return placeholder
        return GeneratedDialogue(
            lines=[DialogueLine(
                speaker_id=speaker_id,
                content=f"[Dialogue for {speaker.name} in response to: {context}]"
            )]
        )
    
    def generate_internal_monologue(
        self,
        character_id: str,
        situation: str,
        hidden_thoughts: bool = True
    ) -> str:
        """
        Generate internal thoughts reflecting character's inner world.
        
        Args:
            character_id: ID of the character
            situation: Current situation
            hidden_thoughts: Whether to include hidden thoughts
        
        Returns:
            Internal monologue text
        """
        character = self._get_profile(character_id)
        
        if not character:
            return ""
        
        if not self.llm_client:
            return f"[{character.name}'s thoughts about {situation}]"
        
        # Build prompt
        prompt = f"""Generate internal monologue for the following character:

Character: {character.name}
Personality: {character.personality.get_trait_summary()}
Current emotional state: {character.current_state.emotional_state}
Current goals: {', '.join(character.current_state.goals) if character.current_state.goals else 'None specific'}
Fears: {', '.join(character.personality.fears) if character.personality.fears else 'None specific'}
Secrets: {', '.join(character.personality.secrets[:2]) if character.personality.secrets and hidden_thoughts else 'None'}

Situation: {situation}

Generate a brief internal monologue (2-3 sentences) showing what this character is thinking but not saying. Use their voice and reflect their personality:"""
        
        try:
            response = self.llm_client.generate(prompt, max_tokens=150)
            return response.strip()
        except Exception as e:
            logger.warning(f"Internal monologue generation failed: {e}")
            return f"[{character.name}'s thoughts]"
    
    def _build_dialogue_prompt(
        self,
        speaker,
        listeners,
        context: str,
        emotional_state: str,
        intent: str,
        interaction_dynamics: Optional[InteractionDynamics],
        max_lines: int
    ) -> str:
        """Build the dialogue generation prompt."""
        parts = []
        
        # Speaker info
        parts.append(f"Speaker: {speaker.name}")
        parts.append(f"Role: {speaker.role}")
        parts.append(f"Personality: {speaker.personality.get_trait_summary()}")
        
        # Speech patterns
        speech = speaker.speech_patterns
        speech_info = []
        speech_info.append(f"Vocabulary: {speech.vocabulary_level}")
        speech_info.append(f"Formality: {speech.formality:.0%}")
        if speech.verbal_tics:
            speech_info.append(f"Verbal tics: {', '.join(speech.verbal_tics[:3])}")
        if speech.common_phrases:
            speech_info.append(f"Common phrases: {', '.join(speech.common_phrases[:3])}")
        parts.append(f"Speech style: {'; '.join(speech_info)}")
        
        # Listeners
        if listeners:
            listener_names = [l.name for l in listeners if l]
            parts.append(f"\nSpeaking to: {', '.join(listener_names)}")
        
        # Relationship dynamics
        if interaction_dynamics:
            parts.append(f"\nRelationship dynamics:")
            parts.append(f"- Sentiment: {interaction_dynamics.relationship_sentiment:.1f} (-1 hostile to 1 friendly)")
            parts.append(f"- Trust: {interaction_dynamics.trust_level:.0%}")
            parts.append(f"- Tension: {interaction_dynamics.tension_level:.0%}")
        
        # Context
        parts.append(f"\nSituation: {context}")
        parts.append(f"Emotional state: {emotional_state}")
        parts.append(f"Intent: {intent}")
        
        # Generation instructions
        parts.append(f"\nGenerate {max_lines} lines of dialogue for {speaker.name}.")
        parts.append("Format each line as:")
        parts.append('"Dialogue text here"')
        parts.append("Include action tags in italics where appropriate.")
        
        return "\n".join(parts)
    
    def _parse_dialogue_response(
        self,
        response: str,
        speaker_id: str,
        listener_ids: List[str]
    ) -> GeneratedDialogue:
        """Parse LLM response into dialogue structure."""
        import re
        
        lines = []
        
        # Extract dialogue lines
        dialogue_pattern = r'"([^"]*)"'
        matches = re.findall(dialogue_pattern, response)
        
        for i, content in enumerate(matches[:5]):
            lines.append(DialogueLine(
                speaker_id=speaker_id,
                content=content,
                is_response=(i > 0)
            ))
        
        if not lines:
            # Fallback: use entire response
            lines.append(DialogueLine(
                speaker_id=speaker_id,
                content=response[:200]
            ))
        
        return GeneratedDialogue(lines=lines)
    
    def _get_profile(self, character_id: str):
        """Get character profile by ID."""
        if self.character_profiles:
            return self.character_profiles.get_profile(character_id)
        return None


class RelationshipDynamics:
    """
    Manages evolving relationships between characters.
    
    Tracks and calculates how relationships change over time
    based on events and interactions.
    """
    
    def __init__(self, narrative_state=None):
        """
        Initialize relationship dynamics manager.
        
        Args:
            narrative_state: NarrativeStateGraph for event tracking
        """
        self.narrative_state = narrative_state
    
    def calculate_interaction_dynamics(
        self,
        character_a_id: str,
        character_b_id: str,
        context: Optional[Any] = None
    ) -> InteractionDynamics:
        """
        Calculate how two characters should interact.
        
        Considers:
        - Relationship history
        - Current emotional states
        - Recent events between them
        - Power dynamics
        - Hidden agendas
        
        Args:
            character_a_id: First character ID
            character_b_id: Second character ID
            context: Additional context
        
        Returns:
            InteractionDynamics for the interaction
        """
        dynamics = InteractionDynamics(
            character_a=character_a_id,
            character_b=character_b_id
        )
        
        # Get relationship from narrative state if available
        if self.narrative_state:
            relation = self.narrative_state.relations_graph.get_relation_between(
                character_a_id, character_b_id
            )
            
            if relation:
                dynamics.relationship_strength = relation.strength
                dynamics.relationship_sentiment = relation.sentiment
        
        # Adjust based on context
        if context:
            # Check for recent conflicts
            if hasattr(context, 'recent_events'):
                conflicts = [
                    e for e in context.recent_events
                    if 'conflict' in str(e).lower()
                ]
                if conflicts:
                    dynamics.tension_level = min(1.0, dynamics.tension_level + 0.3)
        
        return dynamics
    
    def update_from_event(
        self,
        character_a_id: str,
        character_b_id: str,
        event_type: str,
        event_description: str
    ) -> None:
        """
        Update relationship based on an event.
        
        Args:
            character_a_id: First character ID
            character_b_id: Second character ID
            event_type: Type of event
            event_description: Description of what happened
        """
        if not self.narrative_state:
            return
        
        # Get current relationship
        relation = self.narrative_state.relations_graph.get_relation_between(
            character_a_id, character_b_id
        )
        
        if not relation:
            return
        
        # Calculate sentiment change based on event type
        sentiment_change = 0.0
        
        if event_type in ['conflict', 'betrayal', 'argument']:
            sentiment_change = -0.2
        elif event_type in ['reconciliation', 'help', 'support']:
            sentiment_change = 0.2
        elif event_type in ['romance', 'intimacy', 'confession']:
            sentiment_change = 0.3
        elif event_type in ['revelation', 'discovery']:
            sentiment_change = 0.1  # Depends on what's revealed
        
        # Update relationship
        new_sentiment = max(-1.0, min(1.0, relation.sentiment + sentiment_change))
        
        # Update in relations graph
        self.narrative_state.relations_graph.update_relation(
            relation.relation_id,
            {'sentiment': new_sentiment}
        )


class CharacterConsistencyValidator:
    """
    Validates character behavior consistency.
    
    Checks if actions and dialogue are consistent with
    the character's established personality and state.
    """
    
    def __init__(self, character_profiles=None):
        """
        Initialize the consistency validator.
        
        Args:
            character_profiles: CharacterProfileManager instance
        """
        self.character_profiles = character_profiles
    
    def validate_action(
        self,
        character_id: str,
        action: str,
        context: Optional[Any] = None
    ) -> dict:
        """
        Validate if an action is consistent with character profile.
        
        Args:
            character_id: ID of the character
            action: Description of the action
            context: Additional context
        
        Returns:
            Dict with:
            - is_consistent: bool
            - consistency_score: float
            - violations: List of trait violations
            - suggested_modifications: List of alternatives
        """
        profile = self._get_profile(character_id)
        
        if not profile:
            return {
                "is_consistent": True,
                "consistency_score": 0.5,
                "violations": [],
                "suggested_modifications": []
            }
        
        violations = []
        score = 1.0
        
        personality = profile.personality
        
        # Check against moral alignment
        action_lower = action.lower()
        
        # Check for alignment violations
        if personality.moral_alignment in [
            'lawful_good', 'lawful_neutral', 'lawful_evil'
        ]:
            if any(w in action_lower for w in ['breaks law', 'violates', 'illegal']):
                violations.append({
                    "type": "alignment_violation",
                    "description": f"Action conflicts with {personality.moral_alignment.value} alignment"
                })
                score -= 0.2
        
        # Check against personality traits
        if personality.agreeableness > 0.7:
            if any(w in action_lower for w in ['attacks', 'insults', 'betrays']):
                violations.append({
                    "type": "trait_violation",
                    "description": "Action conflicts with high agreeableness"
                })
                score -= 0.15
        
        if personality.conscientiousness > 0.7:
            if any(w in action_lower for w in ['impulsive', 'reckless', 'careless']):
                violations.append({
                    "type": "trait_violation",
                    "description": "Action conflicts with high conscientiousness"
                })
                score -= 0.15
        
        # Check against fears
        for fear in personality.fears:
            if fear.lower() in action_lower:
                violations.append({
                    "type": "fear_confrontation",
                    "description": f"Action directly confronts character's fear: {fear}"
                })
                score -= 0.1
        
        return {
            "is_consistent": len(violations) == 0,
            "consistency_score": max(0.0, score),
            "violations": violations,
            "suggested_modifications": []
        }
    
    def validate_dialogue(
        self,
        character_id: str,
        dialogue: str
    ) -> dict:
        """
        Validate dialogue matches character voice and patterns.
        
        Args:
            character_id: ID of the character
            dialogue: The dialogue to validate
        
        Returns:
            Dict with validation results
        """
        profile = self._get_profile(character_id)
        
        if not profile:
            return {
                "is_consistent": True,
                "consistency_score": 0.5,
                "issues": []
            }
        
        issues = []
        score = 1.0
        
        speech = profile.speech_patterns
        
        # Check vocabulary level
        words = dialogue.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        if speech.vocabulary_level == "simple" and avg_word_length > 6:
            issues.append({
                "type": "vocabulary_mismatch",
                "description": "Dialogue vocabulary too sophisticated for character"
            })
            score -= 0.1
        
        elif speech.vocabulary_level == "academic" and avg_word_length < 5:
            issues.append({
                "type": "vocabulary_mismatch",
                "description": "Dialogue vocabulary too simple for character"
            })
            score -= 0.1
        
        # Check for verbal tics
        if speech.verbal_tics:
            has_tic = any(
                tic.lower() in dialogue.lower()
                for tic in speech.verbal_tics
            )
            if not has_tic and len(dialogue) > 100:
                issues.append({
                    "type": "missing_verbal_tic",
                    "description": f"Dialogue missing character's verbal tics: {speech.verbal_tics}"
                })
                score -= 0.05
        
        # Check formality
        informal_markers = ['gonna', 'wanna', 'yeah', 'nah', 'kinda']
        formal_markers = ['therefore', 'however', 'nevertheless', 'consequently']
        
        has_informal = any(m in dialogue.lower() for m in informal_markers)
        has_formal = any(m in dialogue.lower() for m in formal_markers)
        
        if speech.formality > 0.7 and has_informal:
            issues.append({
                "type": "formality_mismatch",
                "description": "Dialogue too informal for character"
            })
            score -= 0.1
        
        if speech.formality < 0.3 and has_formal:
            issues.append({
                "type": "formality_mismatch",
                "description": "Dialogue too formal for character"
            })
            score -= 0.1
        
        return {
            "is_consistent": len(issues) == 0,
            "consistency_score": max(0.0, score),
            "issues": issues
        }
    
    def _get_profile(self, character_id: str):
        """Get character profile by ID."""
        if self.character_profiles:
            return self.character_profiles.get_profile(character_id)
        return None


__all__ = [
    "InteractionType",
    "EmotionalTone",
    "InteractionDynamics",
    "DialogueContext",
    "DialogueLine",
    "GeneratedDialogue",
    "DialogueGenerator",
    "RelationshipDynamics",
    "CharacterConsistencyValidator",
]