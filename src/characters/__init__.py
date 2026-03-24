"""
Character System for BookWriterAI.

This module provides comprehensive character management including
profile creation, dialogue generation, and consistency validation.

Components:
- Character Profiles: Personality, speech patterns, and arcs
- Dialogue Generation: Character-appropriate dialogue
- Relationship Dynamics: Evolving character relationships
- Consistency Validation: Ensure character behavior consistency

Example usage:
    from src.characters import CharacterProfileManager, DialogueGenerator
    
    # Create character
    manager = CharacterProfileManager()
    hero = manager.create_profile("John Doe", role="protagonist")
    
    # Generate dialogue
    generator = DialogueGenerator(llm_client=client)
    dialogue = generator.generate_dialogue(
        speaker_id=hero.character_id,
        listener_ids=["char_villain_123"],
        context="Confrontation at the warehouse",
        emotional_state="angry",
        intent="Get information"
    )
"""

# Profile System
from src.characters.profile import (
    MoralAlignment,
    ArcType,
    MomentType,
    SpeechPatterns,
    PersonalityProfile,
    CharacterState,
    ArcMoment,
    CharacterArc,
    CharacterProfile,
    CharacterProfileManager,
)

# Dialogue System
from src.characters.dialogue import (
    InteractionType,
    EmotionalTone,
    InteractionDynamics,
    DialogueContext,
    DialogueLine,
    GeneratedDialogue,
    DialogueGenerator,
    RelationshipDynamics,
    CharacterConsistencyValidator,
)


__all__ = [
    # Profile System
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
    
    # Dialogue System
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