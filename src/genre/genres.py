"""
Additional genre templates for BookWriterAI.

This module provides additional genre-specific templates including
science fiction, literary fiction, and non-fiction/technical genres.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from .templates import (
    GenreTemplate,
    GenreCategory,
    ActStructure,
    Act,
    TurningPoint,
    ChapterTemplate,
    CharacterArchetype,
    PlotDeviceTemplate,
)


# ============================================================================
# SCIENCE FICTION TEMPLATE
# ============================================================================

SCIFI_TEMPLATE = GenreTemplate(
    genre_name="science_fiction",
    category=GenreCategory.FICTION,
    subgenres=["hard_sf", "soft_sf", "space_opera", "cyberpunk", "dystopian", "time_travel", "first_contact"],
    description="Stories exploring scientific concepts, technology, and their impact on society",
    
    act_structure=ActStructure(
        name="three_act",
        acts=[
            Act(
                name="Setup & World",
                start_position=0.0,
                end_position=0.25,
                purpose="Establish world, technology, and central conflict",
                key_events=["World introduction", "Technology/concept established", "Inciting incident"],
                emotional_arc="Wonder to disruption",
                percentage_of_book=0.25
            ),
            Act(
                name="Exploration & Conflict",
                start_position=0.25,
                end_position=0.75,
                purpose="Explore implications and escalate conflict",
                key_events=["Technology impact explored", "Rising conflict", "Midpoint revelation", "Stakes escalate"],
                emotional_arc="Fascination to tension",
                percentage_of_book=0.50
            ),
            Act(
                name="Resolution",
                start_position=0.75,
                end_position=1.0,
                purpose="Resolve conflict and explore consequences",
                key_events=["Climax", "Resolution", "New equilibrium"],
                emotional_arc="Tension to contemplation",
                percentage_of_book=0.25
            )
        ],
        turning_points=[
            TurningPoint("Technology Introduction", 0.1, "Key technology/concept revealed", "Wonder", "Sets premise"),
            TurningPoint("Inciting Incident", 0.15, "Central conflict emerges", "Disruption", "Starts main plot"),
            TurningPoint("Midpoint Discovery", 0.5, "Major revelation about technology/world", "Surprise", "Raises stakes"),
            TurningPoint("Crisis", 0.75, "Technology threatens everything", "Fear", "Forces resolution"),
            TurningPoint("Resolution", 0.9, "Conflict resolved, new understanding", "Satisfaction", "Concludes story")
        ]
    ),
    
    required_elements=["speculative_technology", "world_building", "scientific_concepts", "impact_exploration"],
    forbidden_elements=["magic_in_hard_sf", "inconsistent_technology"],
    
    pov_conventions=["third_limited", "third_omniscient", "multiple_pov"],
    tense_conventions=["past", "present"],
    
    typical_length_ranges={
        "novel": (80000, 120000),
        "space_opera": (100000, 150000)
    },
    
    typical_tone="thoughtful",
    dialogue_style="technical and philosophical",
    description_density=0.5,
    action_to_reflection_ratio=0.5,
    
    plot_devices=[
        PlotDeviceTemplate(
            name="Technology Gone Wrong",
            description="Technology creates unintended consequences",
            typical_position=(0.3, 0.8),
            payoff_type="revelation",
            examples=["AI rebellion", "Environmental disaster", "Genetic mutation"]
        ),
        PlotDeviceTemplate(
            name="First Contact",
            description="Humanity encounters alien intelligence",
            typical_position=(0.1, 0.5),
            payoff_type="revelation",
            examples=["Alien arrival", "Signal received", "Discovery of ruins"]
        ),
        PlotDeviceTemplate(
            name="Time Paradox",
            description="Time travel creates complications",
            typical_position=(0.4, 0.9),
            payoff_type="twist",
            examples=["Grandfather paradox", "Bootstrap paradox", "Alternate timeline"]
        )
    ],
    
    character_archetypes=[
        CharacterArchetype(
            name="Scientist/Explorer",
            role="protagonist",
            typical_traits=["curious", "intelligent", "ethical", "determined"],
            typical_arc="discovery and consequence",
            common_relationships=["colleague", "antagonist", "AI companion"]
        ),
        CharacterArchetype(
            name="Corporate Executive",
            role="antagonist",
            typical_traits=["ambitious", "ruthless", "pragmatic", "powerful"],
            typical_arc="revealed and confronted",
            common_relationships=["employees", "competitors", "protagonist"]
        )
    ],
    
    setting_conventions=["future", "space", "alternate_present", "dystopian"],
    
    typical_pacing="varied",
    tension_curve=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.7, 0.5],
    climax_position=0.85,
    
    reader_expectations=["Sense of wonder", "Intellectual stimulation", "Plausible speculation", "Big ideas"],
    genre_promises=["Technology will be central", "Ideas will be explored", "World will be immersive"]
)


# ============================================================================
# LITERARY FICTION TEMPLATE
# ============================================================================

LITERARY_FICTION_TEMPLATE = GenreTemplate(
    genre_name="literary_fiction",
    category=GenreCategory.FICTION,
    subgenres=["contemporary", "historical", "experimental", "magical_realism"],
    description="Character-driven narratives focused on themes, style, and human experience",
    
    act_structure=ActStructure(
        name="character_arc",
        acts=[
            Act(
                name="Introduction",
                start_position=0.0,
                end_position=0.3,
                purpose="Establish character and situation",
                key_events=["Character introduction", "Situation established", "Internal conflict hinted"],
                emotional_arc="Observation",
                percentage_of_book=0.30
            ),
            Act(
                name="Development",
                start_position=0.3,
                end_position=0.7,
                purpose="Deepen character and explore themes",
                key_events=["Character development", "Relationships explored", "Internal conflict deepens"],
                emotional_arc="Understanding",
                percentage_of_book=0.40
            ),
            Act(
                name="Resolution",
                start_position=0.7,
                end_position=1.0,
                purpose="Character transformation or realization",
                key_events=["Moment of truth", "Transformation or acceptance", "New understanding"],
                emotional_arc="Insight",
                percentage_of_book=0.30
            )
        ],
        turning_points=[
            TurningPoint("Opening Image", 0.05, "Establishes character's world", "Introduction", "Sets tone"),
            TurningPoint("Inciting Moment", 0.2, "Something changes", "Disruption", "Begins journey"),
            TurningPoint("Midpoint Reflection", 0.5, "Character gains insight", "Understanding", "Deepens theme"),
            TurningPoint("Epiphany", 0.8, "Character's moment of truth", "Revelation", "Transforms understanding")
        ]
    ),
    
    required_elements=["character_depth", "theme", "literary_style", "emotional_truth"],
    forbidden_elements=["formulaic_plot", "genre_conventions", "shallow_characters"],
    
    pov_conventions=["third_limited", "first_person", "stream_of_consciousness"],
    tense_conventions=["past", "present"],
    
    typical_length_ranges={
        "novel": (60000, 100000),
        "novella": (20000, 50000)
    },
    
    typical_tone="reflective",
    dialogue_style="natural and revealing",
    description_density=0.6,
    action_to_reflection_ratio=0.3,
    
    typical_pacing="slow",
    tension_curve=[0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.5, 0.45, 0.4],
    climax_position=0.8,
    
    reader_expectations=["Beautiful prose", "Deep characters", "Meaningful themes", "Emotional resonance"],
    genre_promises=["Characters will be complex", "Style will matter", "Themes will be explored"]
)


# ============================================================================
# HORROR TEMPLATE
# ============================================================================

HORROR_TEMPLATE = GenreTemplate(
    genre_name="horror",
    category=GenreCategory.FICTION,
    subgenres=["psychological", "supernatural", "slasher", "gothic", "cosmic", "body_horror"],
    description="Stories designed to frighten, unsettle, and create dread",
    
    act_structure=ActStructure(
        name="horror_structure",
        acts=[
            Act(
                name="Normalcy & Dread",
                start_position=0.0,
                end_position=0.3,
                purpose="Establish normal world and introduce threat",
                key_events=["Normal world", "Something wrong", "First scare", "Threat hinted"],
                emotional_arc="Unease",
                percentage_of_book=0.30
            ),
            Act(
                name="Escalation",
                start_position=0.3,
                end_position=0.7,
                purpose="Threat escalates and characters are threatened",
                key_events=["Threat revealed", "Isolation", "Attempts to fight", "Rising body count"],
                emotional_arc="Fear",
                percentage_of_book=0.40
            ),
            Act(
                name="Confrontation",
                start_position=0.7,
                end_position=1.0,
                purpose="Final confrontation and aftermath",
                key_events=["Final confrontation", "Apparent victory", "Final scare", "Aftermath"],
                emotional_arc="Terror to relief",
                percentage_of_book=0.30
            )
        ],
        turning_points=[
            TurningPoint("First Scare", 0.1, "First hint of horror", "Unease", "Establishes threat"),
            TurningPoint("Isolation", 0.3, "Characters cut off from help", "Vulnerability", "Increases danger"),
            TurningPoint("False Hope", 0.6, "Seems like solution found", "Hope", "Will be crushed"),
            TurningPoint("Final Confrontation", 0.85, "Face the horror", "Terror", "Climax"),
            TurningPoint("Final Scare", 0.95, "One last scare", "Lingering dread", "Haunts reader")
        ]
    ),
    
    required_elements=["threat", "atmosphere", "fear", "isolation", "stakes"],
    forbidden_elements=["easy_solutions", "comic_relief_overuse", "safe_characters"],
    
    pov_conventions=["third_limited", "first_person"],
    tense_conventions=["past", "present"],
    
    typical_length_ranges={
        "novel": (70000, 100000),
        "novella": (25000, 50000)
    },
    
    typical_tone="dread",
    dialogue_style="tense and fearful",
    description_density=0.5,
    action_to_reflection_ratio=0.6,
    
    typical_pacing="building",
    tension_curve=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.7],
    climax_position=0.9,
    
    reader_expectations=["Fear", "Atmosphere", "Suspense", "Memorable scares"],
    genre_promises=["You will be scared", "The threat is real", "Not everyone survives"]
)


# ============================================================================
# NON-FICTION TEMPLATE
# ============================================================================

NONFICTION_TEMPLATE = GenreTemplate(
    genre_name="non_fiction",
    category=GenreCategory.NON_FICTION,
    subgenres=["memoir", "biography", "history", "self_help", "popular_science", "true_crime", "travel"],
    description="Factual narratives about real people, events, or topics",
    
    act_structure=ActStructure(
        name="narrative_nonfiction",
        acts=[
            Act(
                name="Introduction",
                start_position=0.0,
                end_position=0.15,
                purpose="Introduce subject and establish relevance",
                key_events=["Hook", "Subject introduction", "Context established"],
                emotional_arc="Interest",
                percentage_of_book=0.15
            ),
            Act(
                name="Development",
                start_position=0.15,
                end_position=0.85,
                purpose="Explore subject in depth",
                key_events=["Background", "Key events", "Analysis", "Themes explored"],
                emotional_arc="Understanding",
                percentage_of_book=0.70
            ),
            Act(
                name="Conclusion",
                start_position=0.85,
                end_position=1.0,
                purpose="Synthesize and provide takeaway",
                key_events=["Synthesis", "Takeaways", "Conclusion"],
                emotional_arc="Insight",
                percentage_of_book=0.15
            )
        ],
        turning_points=[
            TurningPoint("Hook", 0.05, "Captures reader interest", "Curiosity", "Engages reader"),
            TurningPoint("Thesis Statement", 0.1, "Main argument or theme", "Understanding", "Sets direction"),
            TurningPoint("Key Revelation", 0.5, "Major insight or turning point", "Insight", "Deepens understanding"),
            TurningPoint("Conclusion", 0.9, "Final synthesis", "Satisfaction", "Resolves narrative")
        ]
    ),
    
    required_elements=["factual_accuracy", "research", "clear_structure", "engaging_narrative"],
    forbidden_elements=["fabrication", "plagiarism", "bias_without_acknowledgment"],
    
    pov_conventions=["third_person", "first_person"],
    tense_conventions=["past", "present"],
    
    typical_length_ranges={
        "standard": (60000, 90000),
        "memoir": (70000, 100000)
    },
    
    typical_tone="informative",
    dialogue_style="varies by subgenre",
    description_density=0.5,
    action_to_reflection_ratio=0.4,
    
    typical_pacing="moderate",
    tension_curve=[0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.5, 0.45, 0.4],
    climax_position=0.5,
    
    reader_expectations=["Accuracy", "Engagement", "Learning", "New perspectives"],
    genre_promises=["Facts are verified", "Narrative is engaging", "Reader will learn"]
)


# ============================================================================
# TECHNICAL BOOK TEMPLATE
# ============================================================================

TECHNICAL_TEMPLATE = GenreTemplate(
    genre_name="technical",
    category=GenreCategory.TECHNICAL,
    subgenres=["programming", "engineering", "science", "manual", "textbook", "reference"],
    description="Educational content focused on technical skills and knowledge",
    
    act_structure=ActStructure(
        name="technical_structure",
        acts=[
            Act(
                name="Foundations",
                start_position=0.0,
                end_position=0.25,
                purpose="Establish fundamentals and prerequisites",
                key_events=["Introduction", "Prerequisites", "Core concepts", "First examples"],
                emotional_arc="Building foundation",
                percentage_of_book=0.25
            ),
            Act(
                name="Core Content",
                start_position=0.25,
                end_position=0.75,
                purpose="Present main technical content",
                key_events=["Concepts explained", "Examples worked", "Exercises provided", "Common pitfalls"],
                emotional_arc="Learning",
                percentage_of_book=0.50
            ),
            Act(
                name="Advanced & Application",
                start_position=0.75,
                end_position=1.0,
                purpose="Advanced topics and real-world application",
                key_events=["Advanced concepts", "Case studies", "Best practices", "Resources"],
                emotional_arc="Mastery",
                percentage_of_book=0.25
            )
        ],
        turning_points=[
            TurningPoint("Introduction", 0.05, "What the book covers", "Orientation", "Sets expectations"),
            TurningPoint("First Concept", 0.1, "First technical concept", "Learning begins", "Starts instruction"),
            TurningPoint("Midpoint Review", 0.5, "Review and consolidation", "Reinforcement", "Solidifies learning"),
            TurningPoint("Advanced Topics", 0.75, "Move to advanced content", "Progression", "Advances difficulty")
        ]
    ),
    
    chapter_templates=[
        ChapterTemplate(
            name="Concept Chapter",
            chapter_type="instructional",
            typical_position=(0.0, 1.0),
            purpose="Explain a technical concept",
            typical_length=(3000, 6000),
            key_elements=["Explanation", "Examples", "Diagrams", "Exercises"],
            pacing="moderate"
        ),
        ChapterTemplate(
            name="Tutorial Chapter",
            chapter_type="tutorial",
            typical_position=(0.2, 0.8),
            purpose="Step-by-step practical guide",
            typical_length=(4000, 8000),
            key_elements=["Step-by-step instructions", "Screenshots", "Code samples", "Expected results"],
            pacing="slow"
        ),
        ChapterTemplate(
            name="Reference Chapter",
            chapter_type="reference",
            typical_position=(0.7, 1.0),
            purpose="Quick reference material",
            typical_length=(2000, 5000),
            key_elements=["API reference", "Cheat sheets", "Common patterns", "Troubleshooting"],
            pacing="varied"
        )
    ],
    
    required_elements=["clear_explanations", "examples", "exercises", "accuracy"],
    forbidden_elements=["assumed_knowledge", "unclear_instructions", "outdated_information"],
    
    pov_conventions=["second_person", "third_person"],
    tense_conventions=["present"],
    
    typical_length_ranges={
        "textbook": (300000, 500000),  # Words
        "technical_guide": (50000, 100000),
        "reference": (100000, 300000)
    },
    
    typical_tone="instructional",
    dialogue_style="direct and clear",
    description_density=0.3,
    action_to_reflection_ratio=0.2,
    
    typical_pacing="moderate",
    tension_curve=[0.3, 0.35, 0.4, 0.45, 0.5, 0.45, 0.4, 0.35, 0.3],
    climax_position=0.5,
    
    reader_expectations=["Clear instruction", "Working examples", "Practical skills", "Accuracy"],
    genre_promises=["Content is accurate", "Examples work", "Skills are transferable"]
)


# ============================================================================
# ACADEMIC BOOK TEMPLATE
# ============================================================================

ACADEMIC_TEMPLATE = GenreTemplate(
    genre_name="academic",
    category=GenreCategory.ACADEMIC,
    subgenres=["thesis", "dissertation", "research_monograph", "textbook", "edited_volume"],
    description="Scholarly works for academic audiences with rigorous methodology",
    
    act_structure=ActStructure(
        name="academic_structure",
        acts=[
            Act(
                name="Introduction & Framework",
                start_position=0.0,
                end_position=0.2,
                purpose="Establish research context and framework",
                key_events=["Introduction", "Literature review", "Theoretical framework", "Methodology"],
                emotional_arc="Foundation",
                percentage_of_book=0.20
            ),
            Act(
                name="Analysis & Findings",
                start_position=0.2,
                end_position=0.8,
                purpose="Present research and analysis",
                key_events=["Data presentation", "Analysis", "Findings", "Discussion"],
                emotional_arc="Investigation",
                percentage_of_book=0.60
            ),
            Act(
                name="Conclusion",
                start_position=0.8,
                end_position=1.0,
                purpose="Synthesize findings and implications",
                key_events=["Conclusion", "Implications", "Future research", "References"],
                emotional_arc="Synthesis",
                percentage_of_book=0.20
            )
        ],
        turning_points=[
            TurningPoint("Research Question", 0.05, "Central question posed", "Inquiry", "Sets direction"),
            TurningPoint("Methodology", 0.15, "Method established", "Framework", "Establishes rigor"),
            TurningPoint("Key Finding", 0.5, "Major result presented", "Discovery", "Central contribution"),
            TurningPoint("Conclusion", 0.9, "Final synthesis", "Resolution", "Concludes argument")
        ]
    ),
    
    chapter_templates=[
        ChapterTemplate(
            name="Literature Review",
            chapter_type="review",
            typical_position=(0.05, 0.15),
            purpose="Survey existing research",
            typical_length=(5000, 15000),
            key_elements=["Previous research", "Gaps identified", "Theoretical positioning"],
            pacing="moderate"
        ),
        ChapterTemplate(
            name="Methodology Chapter",
            chapter_type="methodology",
            typical_position=(0.1, 0.2),
            purpose="Explain research methods",
            typical_length=(3000, 8000),
            key_elements=["Method description", "Justification", "Limitations"],
            pacing="moderate"
        ),
        ChapterTemplate(
            name="Findings Chapter",
            chapter_type="findings",
            typical_position=(0.2, 0.8),
            purpose="Present research findings",
            typical_length=(5000, 15000),
            key_elements=["Data presentation", "Analysis", "Tables/figures", "Interpretation"],
            pacing="moderate"
        )
    ],
    
    required_elements=["citations", "methodology", "rigor", "peer_review_ready"],
    forbidden_elements=["plagiarism", "unsupported_claims", "informal_language"],
    
    pov_conventions=["third_person", "first_person_plural"],
    tense_conventions=["past", "present"],
    
    typical_length_ranges={
        "monograph": (80000, 120000),
        "textbook": (150000, 300000),
        "thesis": (50000, 100000)
    },
    
    typical_tone="scholarly",
    dialogue_style="formal and precise",
    description_density=0.4,
    action_to_reflection_ratio=0.2,
    
    typical_pacing="moderate",
    tension_curve=[0.3, 0.35, 0.4, 0.45, 0.5, 0.45, 0.4, 0.35, 0.3],
    climax_position=0.5,
    
    reader_expectations=["Rigor", "Citations", "Original contribution", "Clear argument"],
    genre_promises=["Research is sound", "Claims are supported", "Contribution is clear"]
)


# Additional templates to add to registry
ADDITIONAL_GENRE_TEMPLATES = {
    "science_fiction": SCIFI_TEMPLATE,
    "literary_fiction": LITERARY_FICTION_TEMPLATE,
    "horror": HORROR_TEMPLATE,
    "non_fiction": NONFICTION_TEMPLATE,
    "technical": TECHNICAL_TEMPLATE,
    "academic": ACADEMIC_TEMPLATE,
}


__all__ = [
    "SCIFI_TEMPLATE",
    "LITERARY_FICTION_TEMPLATE",
    "HORROR_TEMPLATE",
    "NONFICTION_TEMPLATE",
    "TECHNICAL_TEMPLATE",
    "ACADEMIC_TEMPLATE",
    "ADDITIONAL_GENRE_TEMPLATES",
]