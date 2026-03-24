"""
Genre-Specific Template System for BookWriterAI.

This module provides genre-specific templates and conventions
for different types of books including fiction genres and
non-fiction/technical content.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class GenreCategory(Enum):
    """Major genre categories."""
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    TECHNICAL = "technical"
    ACADEMIC = "academic"


@dataclass
class Act:
    """
    A single act in the narrative structure.
    
    Based on three-act structure but extensible to other
    structures (five-act, hero's journey, etc.)
    """
    name: str
    start_position: float  # 0.0 to 1.0
    end_position: float  # 0.0 to 1.0
    purpose: str
    key_events: List[str] = field(default_factory=list)
    emotional_arc: str = ""
    percentage_of_book: float = 0.25
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "purpose": self.purpose,
            "key_events": self.key_events,
            "emotional_arc": self.emotional_arc,
            "percentage_of_book": self.percentage_of_book
        }


@dataclass
class TurningPoint:
    """A key turning point in the narrative."""
    name: str
    position: float  # 0.0 to 1.0
    description: str
    emotional_impact: str = ""
    plot_function: str = ""  # What this does for the plot
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "position": self.position,
            "description": self.description,
            "emotional_impact": self.emotional_impact,
            "plot_function": self.plot_function
        }


@dataclass
class ActStructure:
    """Narrative act structure definition."""
    name: str = "three_act"
    acts: List[Act] = field(default_factory=list)
    turning_points: List[TurningPoint] = field(default_factory=list)
    
    def get_act_at_position(self, position: float) -> Optional[Act]:
        """Get the act at a specific position."""
        for act in self.acts:
            if act.start_position <= position < act.end_position:
                return act
        return self.acts[-1] if self.acts else None
    
    def get_turning_points_in_range(
        self,
        start: float,
        end: float
    ) -> List[TurningPoint]:
        """Get turning points within a position range."""
        return [
            tp for tp in self.turning_points
            if start <= tp.position < end
        ]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "acts": [a.to_dict() for a in self.acts],
            "turning_points": [tp.to_dict() for tp in self.turning_points]
        }


@dataclass
class ChapterTemplate:
    """Template for a specific chapter type."""
    name: str
    chapter_type: str  # opening, rising_action, climax, falling_action, resolution
    typical_position: Tuple[float, float] = (0.0, 1.0)  # Range in book
    purpose: str = ""
    typical_length: Tuple[int, int] = (2000, 4000)  # Word range
    key_elements: List[str] = field(default_factory=list)
    avoid_elements: List[str] = field(default_factory=list)
    pov_guidance: str = ""
    pacing: str = "moderate"  # slow, moderate, fast
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "chapter_type": self.chapter_type,
            "typical_position": self.typical_position,
            "purpose": self.purpose,
            "typical_length": self.typical_length,
            "key_elements": self.key_elements,
            "avoid_elements": self.avoid_elements,
            "pov_guidance": self.pov_guidance,
            "pacing": self.pacing
        }


@dataclass
class CharacterArchetype:
    """A character archetype for the genre."""
    name: str
    role: str  # protagonist, antagonist, mentor, sidekick, etc.
    typical_traits: List[str] = field(default_factory=list)
    typical_arc: str = ""
    common_relationships: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "typical_traits": self.typical_traits,
            "typical_arc": self.typical_arc,
            "common_relationships": self.common_relationships,
            "examples": self.examples
        }


@dataclass
class PlotDeviceTemplate:
    """A plot device common to the genre."""
    name: str
    description: str
    typical_position: Tuple[float, float] = (0.0, 1.0)
    setup_required: List[str] = field(default_factory=list)
    payoff_type: str = ""  # twist, revelation, confrontation, etc.
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "typical_position": self.typical_position,
            "setup_required": self.setup_required,
            "payoff_type": self.payoff_type,
            "examples": self.examples
        }


@dataclass
class GenreTemplate:
    """
    Genre-specific configuration and templates.
    
    Defines all conventions, structures, and elements
    specific to a genre for consistent book generation.
    """
    # Identity
    genre_name: str
    category: GenreCategory = GenreCategory.FICTION
    subgenres: List[str] = field(default_factory=list)
    description: str = ""
    
    # Structure
    act_structure: Optional[ActStructure] = None
    chapter_templates: List[ChapterTemplate] = field(default_factory=list)
    
    # Requirements
    required_elements: List[str] = field(default_factory=list)
    forbidden_elements: List[str] = field(default_factory=list)
    
    # POV and tense
    pov_conventions: List[str] = field(default_factory=list)
    tense_conventions: List[str] = field(default_factory=list)
    
    # Length
    typical_length_ranges: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    # e.g., {"short_story": (1000, 7500), "novella": (20000, 50000), "novel": (70000, 100000)}
    
    # Style
    typical_tone: str = ""
    dialogue_style: str = ""
    description_density: float = 0.5  # 0.0 to 1.0
    action_to_reflection_ratio: float = 0.5
    
    # Genre elements
    plot_devices: List[PlotDeviceTemplate] = field(default_factory=list)
    character_archetypes: List[CharacterArchetype] = field(default_factory=list)
    setting_conventions: List[str] = field(default_factory=list)
    
    # Pacing
    typical_pacing: str = "moderate"
    tension_curve: List[float] = field(default_factory=list)
    climax_position: float = 0.85
    
    # Reader expectations
    reader_expectations: List[str] = field(default_factory=list)
    genre_promises: List[str] = field(default_factory=list)  # What the genre promises readers
    
    def get_chapter_template(
        self,
        chapter_position: float
    ) -> Optional[ChapterTemplate]:
        """Get appropriate chapter template for a position."""
        for template in self.chapter_templates:
            if (template.typical_position[0] <= chapter_position < 
                template.typical_position[1]):
                return template
        return self.chapter_templates[-1] if self.chapter_templates else None
    
    def get_plot_devices_for_position(
        self,
        position: float
    ) -> List[PlotDeviceTemplate]:
        """Get plot devices appropriate for a position."""
        return [
            pd for pd in self.plot_devices
            if pd.typical_position[0] <= position <= pd.typical_position[1]
        ]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "genre_name": self.genre_name,
            "category": self.category.value,
            "subgenres": self.subgenres,
            "description": self.description,
            "act_structure": self.act_structure.to_dict() if self.act_structure else None,
            "chapter_templates": [ct.to_dict() for ct in self.chapter_templates],
            "required_elements": self.required_elements,
            "forbidden_elements": self.forbidden_elements,
            "pov_conventions": self.pov_conventions,
            "tense_conventions": self.tense_conventions,
            "typical_length_ranges": self.typical_length_ranges,
            "typical_tone": self.typical_tone,
            "dialogue_style": self.dialogue_style,
            "description_density": self.description_density,
            "action_to_reflection_ratio": self.action_to_reflection_ratio,
            "plot_devices": [pd.to_dict() for pd in self.plot_devices],
            "character_archetypes": [ca.to_dict() for ca in self.character_archetypes],
            "setting_conventions": self.setting_conventions,
            "typical_pacing": self.typical_pacing,
            "tension_curve": self.tension_curve,
            "climax_position": self.climax_position,
            "reader_expectations": self.reader_expectations,
            "genre_promises": self.genre_promises
        }


# ============================================================================
# PREDEFINED GENRE TEMPLATES
# ============================================================================

THRILLER_TEMPLATE = GenreTemplate(
    genre_name="thriller",
    category=GenreCategory.FICTION,
    subgenres=["psychological", "action", "crime", "spy", "legal", "medical"],
    description="Fast-paced, tension-filled narratives with high stakes and danger",
    
    act_structure=ActStructure(
        name="three_act",
        acts=[
            Act(
                name="Setup",
                start_position=0.0,
                end_position=0.25,
                purpose="Establish protagonist, threat, and stakes",
                key_events=["Introduction of protagonist", "Inciting incident/threat emerges", "Stakes established"],
                emotional_arc="Curiosity to concern",
                percentage_of_book=0.25
            ),
            Act(
                name="Confrontation",
                start_position=0.25,
                end_position=0.75,
                purpose="Escalating danger and obstacles",
                key_events=["First confrontation", "Rising obstacles", "Midpoint twist", "All seems lost moment"],
                emotional_arc="Tension building",
                percentage_of_book=0.50
            ),
            Act(
                name="Resolution",
                start_position=0.75,
                end_position=1.0,
                purpose="Final confrontation and aftermath",
                key_events=["Final confrontation", "Climax", "Resolution", "Aftermath"],
                emotional_arc="Peak tension to relief",
                percentage_of_book=0.25
            )
        ],
        turning_points=[
            TurningPoint("Inciting Incident", 0.1, "Threat or crime that starts the story", "Shock/intrigue", "Sets plot in motion"),
            TurningPoint("First Plot Point", 0.25, "Protagonist fully committed", "Determination", "Locks protagonist into conflict"),
            TurningPoint("Midpoint", 0.5, "Major revelation or twist", "Surprise", "Changes direction/raises stakes"),
            TurningPoint("Dark Moment", 0.75, "All seems lost", "Despair", "Forces protagonist to dig deep"),
            TurningPoint("Climax", 0.9, "Final confrontation", "Peak tension", "Resolves main conflict")
        ]
    ),
    
    chapter_templates=[
        ChapterTemplate(
            name="Opening Chapter",
            chapter_type="opening",
            typical_position=(0.0, 0.05),
            purpose="Hook the reader, establish tone and threat",
            typical_length=(2500, 4000),
            key_elements=["Strong hook", "Immediate tension", "Protagonist introduction", "Hint of threat"],
            avoid_elements=["Slow exposition", "Backstory dumps"],
            pacing="fast"
        ),
        ChapterTemplate(
            name="Investigation Chapter",
            chapter_type="rising_action",
            typical_position=(0.1, 0.5),
            purpose="Build tension through discovery and obstacles",
            typical_length=(3000, 5000),
            key_elements=["New clues", "Rising danger", "Character development", "Red herrings"],
            pacing="moderate"
        ),
        ChapterTemplate(
            name="Action Chapter",
            chapter_type="rising_action",
            typical_position=(0.3, 0.8),
            purpose="High-energy confrontation or chase",
            typical_length=(2500, 4000),
            key_elements=["Physical action", "Immediate danger", "Stakes escalation", "Time pressure"],
            pacing="fast"
        ),
        ChapterTemplate(
            name="Climax Chapter",
            chapter_type="climax",
            typical_position=(0.85, 0.95),
            purpose="Final confrontation with antagonist",
            typical_length=(4000, 6000),
            key_elements=["Maximum tension", "Life-or-death stakes", "Resolution of main plot", "Character tested"],
            pacing="fast"
        )
    ],
    
    required_elements=["tension", "stakes", "antagonist", "time_pressure", "protagonist_in_danger"],
    forbidden_elements=["coincidental_solutions", "passive_protagonist", "slow_opening"],
    
    pov_conventions=["third_limited", "first_person"],
    tense_conventions=["past", "present"],
    
    typical_length_ranges={
        "novel": (70000, 100000),
        "novella": (25000, 50000)
    },
    
    typical_tone="suspenseful",
    dialogue_style="sharp and tense",
    description_density=0.3,
    action_to_reflection_ratio=0.7,
    
    plot_devices=[
        PlotDeviceTemplate(
            name="Ticking Clock",
            description="Time limit that creates urgency",
            typical_position=(0.3, 0.95),
            payoff_type="tension",
            examples=["Bomb countdown", "Kidnapped victim", "Approaching deadline"]
        ),
        PlotDeviceTemplate(
            name="Red Herring",
            description="False lead that misdirects",
            typical_position=(0.2, 0.7),
            payoff_type="twist",
            examples=["Wrong suspect", "False clue", "Misleading evidence"]
        ),
        PlotDeviceTemplate(
            name="Betrayal",
            description="Someone trusted is revealed as enemy",
            typical_position=(0.5, 0.8),
            payoff_type="revelation",
            examples=["Mole in organization", "Double agent", "Corrupt ally"]
        )
    ],
    
    character_archetypes=[
        CharacterArchetype(
            name="Determined Protagonist",
            role="protagonist",
            typical_traits=["resourceful", "persistent", "morally driven", "skilled"],
            typical_arc="tested and proven",
            common_relationships=["mentor", "partner", "antagonist"]
        ),
        CharacterArchetype(
            name="Brilliant Antagonist",
            role="antagonist",
            typical_traits=["intelligent", "ruthless", "hidden agenda", "formidable"],
            typical_arc="revealed and confronted",
            common_relationships=["minions", "protagonist"]
        )
    ],
    
    setting_conventions=["urban", "contemporary", "atmospheric", "dangerous"],
    
    typical_pacing="fast",
    tension_curve=[0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.85, 0.6],
    climax_position=0.9,
    
    reader_expectations=["Excitement", "Suspense", "Satisfying resolution", "Clever plot"],
    genre_promises=["The protagonist will face danger", "The stakes are real", "Tension will build", "Resolution will be earned"]
)


ROMANCE_TEMPLATE = GenreTemplate(
    genre_name="romance",
    category=GenreCategory.FICTION,
    subgenres=["contemporary", "historical", "paranormal", "romantic_comedy", "romantic_suspense"],
    description="Focus on romantic relationship development with emotional journey",
    
    act_structure=ActStructure(
        name="romance_structure",
        acts=[
            Act(
                name="Meet Cute & Attraction",
                start_position=0.0,
                end_position=0.25,
                purpose="Introduce leads and spark attraction",
                key_events=["First meeting", "Initial attraction", "Conflict established"],
                emotional_arc="Intrigue and attraction",
                percentage_of_book=0.25
            ),
            Act(
                name="Developing Relationship",
                start_position=0.25,
                end_position=0.6,
                purpose="Build relationship and deepen feelings",
                key_events=["Forced proximity", "Growing intimacy", "Vulnerability moments"],
                emotional_arc="Falling in love",
                percentage_of_book=0.35
            ),
            Act(
                name="Conflict & Separation",
                start_position=0.6,
                end_position=0.8,
                purpose="Test the relationship",
                key_events=["Major conflict", "Misunderstanding", "Separation"],
                emotional_arc="Heartbreak and doubt",
                percentage_of_book=0.20
            ),
            Act(
                name="Resolution & HEA",
                start_position=0.8,
                end_position=1.0,
                purpose="Resolve conflict and achieve happy ending",
                key_events=["Grand gesture", "Reconciliation", "Commitment"],
                emotional_arc="Joy and fulfillment",
                percentage_of_book=0.20
            )
        ],
        turning_points=[
            TurningPoint("Meet Cute", 0.05, "First encounter between leads", "Surprise/attraction", "Introduces romantic pair"),
            TurningPoint("First Kiss", 0.3, "Physical relationship begins", "Desire", "Escalates romance"),
            TurningPoint("Midpoint Intimacy", 0.5, "Deep emotional connection", "Love growing", "Commits to relationship"),
            TurningPoint("Black Moment", 0.7, "Relationship seems doomed", "Despair", "Tests love"),
            TurningPoint("Grand Gesture", 0.9, "Prove love and commitment", "Hope to joy", "Resolves conflict")
        ]
    ),
    
    required_elements=["romantic_leads", "emotional_journey", "conflict", "happy_ending"],
    forbidden_elements=["tragic_ending", "cheating_protagonist", "unresolved_romance"],
    
    pov_conventions=["third_limited", "dual_pov", "first_person"],
    tense_conventions=["past"],
    
    typical_length_ranges={
        "category_romance": (50000, 70000),
        "single_title": (80000, 100000)
    },
    
    typical_tone="emotional",
    dialogue_style="witty and heartfelt",
    description_density=0.4,
    action_to_reflection_ratio=0.3,
    
    typical_pacing="moderate",
    tension_curve=[0.3, 0.4, 0.5, 0.6, 0.7, 0.5, 0.3, 0.6, 0.4],
    climax_position=0.9,
    
    reader_expectations=["Emotional engagement", "Character chemistry", "Happy ending", "Believable romance"],
    genre_promises=["Love will triumph", "Characters will grow", "Happy Ever After guaranteed"]
)


FANTASY_TEMPLATE = GenreTemplate(
    genre_name="fantasy",
    category=GenreCategory.FICTION,
    subgenres=["epic", "urban", "high_fantasy", "low_fantasy", "dark_fantasy", "ya_fantasy"],
    description="Stories with magical elements in secondary or magical realist worlds",
    
    act_structure=ActStructure(
        name="heros_journey",
        acts=[
            Act(
                name="Ordinary World & Call",
                start_position=0.0,
                end_position=0.15,
                purpose="Establish normal world and call to adventure",
                key_events=["Normal world", "Call to adventure", "Refusal", "Meeting mentor"],
                emotional_arc="Comfort to disruption",
                percentage_of_book=0.15
            ),
            Act(
                name="Special World & Trials",
                start_position=0.15,
                end_position=0.5,
                purpose="Enter magical world and face challenges",
                key_events=["Crossing threshold", "Tests and allies", "Approach", "Ordeal"],
                emotional_arc="Wonder and challenge",
                percentage_of_book=0.35
            ),
            Act(
                name="Transformation & Climax",
                start_position=0.5,
                end_position=0.85,
                purpose="Face greatest challenge and transform",
                key_events=["Reward", "Road back", "Resurrection"],
                emotional_arc="Growth and triumph",
                percentage_of_book=0.35
            ),
            Act(
                name="Return",
                start_position=0.85,
                end_position=1.0,
                purpose="Return changed with elixir",
                key_events=["Return with elixir", "New normal"],
                emotional_arc="Resolution",
                percentage_of_book=0.15
            )
        ],
        turning_points=[
            TurningPoint("Call to Adventure", 0.08, "Hero is called to quest", "Disruption", "Starts journey"),
            TurningPoint("Crossing Threshold", 0.15, "Hero enters special world", "Commitment", "No turning back"),
            TurningPoint("Ordeal", 0.5, "Greatest test", "Fear to triumph", "Transformation"),
            TurningPoint("Resurrection", 0.85, "Final test", "Climax", "Proves transformation")
        ]
    ),
    
    required_elements=["magic_system", "world_building", "quest_or_journey", "clear_stakes"],
    forbidden_elements=["inconsistent_magic", "modern_technology_in_high_fantasy"],
    
    pov_conventions=["third_limited", "third_omniscient", "multiple_pov"],
    tense_conventions=["past"],
    
    typical_length_ranges={
        "novel": (90000, 150000),
        "epic": (120000, 200000)
    },
    
    typical_tone="wondrous",
    dialogue_style="varies by subgenre",
    description_density=0.6,
    action_to_reflection_ratio=0.5,
    
    typical_pacing="varied",
    tension_curve=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.7, 0.5],
    climax_position=0.85,
    
    reader_expectations=["World immersion", "Magic system", "Epic scope", "Character growth"],
    genre_promises=["Wonder and magic", "Epic journey", "Good vs evil", "Heroic transformation"]
)


MYSTERY_TEMPLATE = GenreTemplate(
    genre_name="mystery",
    category=GenreCategory.FICTION,
    subgenres=["cozy", "hardboiled", "police_procedural", "amateur_detective", "locked_room"],
    description="Puzzle-centered narratives focused on solving a crime or mystery",
    
    act_structure=ActStructure(
        name="mystery_structure",
        acts=[
            Act(
                name="Discovery & Setup",
                start_position=0.0,
                end_position=0.2,
                purpose="Present crime and begin investigation",
                key_events=["Crime discovered", "Detective introduced", "Initial investigation"],
                emotional_arc="Intrigue",
                percentage_of_book=0.20
            ),
            Act(
                name="Investigation",
                start_position=0.2,
                end_position=0.7,
                purpose="Gather clues and interview suspects",
                key_events=["Suspects introduced", "Clues found", "Red herrings", "Midpoint revelation"],
                emotional_arc="Puzzlement to clarity",
                percentage_of_book=0.50
            ),
            Act(
                name="Resolution",
                start_position=0.7,
                end_position=1.0,
                purpose="Reveal solution and explain",
                key_events=["Breakthrough", "Confrontation", "Explanation", "Resolution"],
                emotional_arc="Satisfaction",
                percentage_of_book=0.30
            )
        ],
        turning_points=[
            TurningPoint("Crime Discovery", 0.05, "The mystery is revealed", "Shock/intrigue", "Sets puzzle"),
            TurningPoint("First Clue", 0.15, "Investigation begins", "Curiosity", "Starts solving"),
            TurningPoint("Midpoint Clue", 0.5, "Major revelation", "Surprise", "Changes understanding"),
            TurningPoint("Breakthrough", 0.75, "Final piece falls into place", "Realization", "Leads to solution"),
            TurningPoint("Revelation", 0.9, "Killer revealed", "Satisfaction", "Resolves mystery")
        ]
    ),
    
    required_elements=["crime_or_puzzle", "detective", "clues", "suspects", "fair_play"],
    forbidden_elements=["unfair_solutions", "withheld_evidence", "supernatural_solutions_in_realistic"],
    
    pov_conventions=["third_limited", "first_person"],
    tense_conventions=["past"],
    
    typical_length_ranges={
        "novel": (70000, 90000),
        "cozy": (60000, 75000)
    },
    
    typical_tone="intriguing",
    dialogue_style="questioning and revealing",
    description_density=0.4,
    action_to_reflection_ratio=0.4,
    
    typical_pacing="moderate",
    tension_curve=[0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.6, 0.5],
    climax_position=0.9,
    
    reader_expectations=["Fair puzzle", "Clever detective", "Satisfying solution", "Red herrings"],
    genre_promises=["Puzzle can be solved", "Clues are fair", "Resolution makes sense"]
)


# Template registry
GENRE_TEMPLATES: Dict[str, GenreTemplate] = {
    "thriller": THRILLER_TEMPLATE,
    "romance": ROMANCE_TEMPLATE,
    "fantasy": FANTASY_TEMPLATE,
    "mystery": MYSTERY_TEMPLATE,
}


class GenreTemplateManager:
    """
    Manages genre templates and provides access to genre-specific
    configurations for book generation.
    """
    
    def __init__(self):
        """Initialize the genre template manager."""
        self.templates = GENRE_TEMPLATES.copy()
        self.custom_templates: Dict[str, GenreTemplate] = {}
    
    def get_template(
        self,
        genre: str,
        subgenre: Optional[str] = None
    ) -> Optional[GenreTemplate]:
        """
        Get a genre template.
        
        Args:
            genre: Primary genre name
            subgenre: Optional subgenre for specialization
        
        Returns:
            GenreTemplate or None if not found
        """
        # Check custom templates first
        if genre in self.custom_templates:
            return self.custom_templates[genre]
        
        # Check predefined templates
        if genre in self.templates:
            return self.templates[genre]
        
        return None
    
    def register_template(self, template: GenreTemplate) -> None:
        """Register a custom genre template."""
        self.custom_templates[template.genre_name] = template
    
    def create_custom_template(
        self,
        base_genre: str,
        customizations: Dict[str, Any]
    ) -> GenreTemplate:
        """
        Create a customized genre template based on an existing one.
        
        Args:
            base_genre: Base genre to customize
            customizations: Dictionary of customizations
        
        Returns:
            Customized GenreTemplate
        """
        base = self.get_template(base_genre)
        
        if not base:
            # Create new template from scratch
            return GenreTemplate(
                genre_name=customizations.get("genre_name", base_genre),
                **customizations
            )
        
        # Create copy and apply customizations
        base_dict = base.to_dict()
        
        for key, value in customizations.items():
            if key in base_dict:
                base_dict[key] = value
        
        return GenreTemplate(
            genre_name=base_dict.get("genre_name", base_genre),
            category=GenreCategory(base_dict.get("category", "fiction")),
            subgenres=base_dict.get("subgenres", []),
            description=base_dict.get("description", ""),
            required_elements=base_dict.get("required_elements", []),
            forbidden_elements=base_dict.get("forbidden_elements", []),
            pov_conventions=base_dict.get("pov_conventions", []),
            tense_conventions=base_dict.get("tense_conventions", []),
            typical_tone=base_dict.get("typical_tone", ""),
            dialogue_style=base_dict.get("dialogue_style", ""),
            description_density=base_dict.get("description_density", 0.5),
            action_to_reflection_ratio=base_dict.get("action_to_reflection_ratio", 0.5),
            typical_pacing=base_dict.get("typical_pacing", "moderate"),
            climax_position=base_dict.get("climax_position", 0.85),
            reader_expectations=base_dict.get("reader_expectations", []),
            genre_promises=base_dict.get("genre_promises", [])
        )
    
    def list_genres(self) -> List[str]:
        """List all available genre templates."""
        return list(self.templates.keys()) + list(self.custom_templates.keys())
    
    def get_genres_by_category(self, category: GenreCategory) -> List[str]:
        """Get all genres in a category."""
        return [
            name for name, template in self.templates.items()
            if template.category == category
        ]


__all__ = [
    "GenreCategory",
    "Act",
    "TurningPoint",
    "ActStructure",
    "ChapterTemplate",
    "CharacterArchetype",
    "PlotDeviceTemplate",
    "GenreTemplate",
    "GENRE_TEMPLATES",
    "GenreTemplateManager",
]