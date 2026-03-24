"""
Tests for the Genre Template System.

Tests cover GenreTemplate, GenreTemplateManager, and genre-specific
template implementations.
"""

import pytest

from src.genre import (
    GenreCategory,
    Act,
    TurningPoint,
    ActStructure,
    ChapterTemplate,
    CharacterArchetype,
    PlotDeviceTemplate,
    GenreTemplate,
    GenreTemplateManager,
    GENRE_TEMPLATES,
)


class TestAct:
    """Tests for Act dataclass."""
    
    def test_act_creation(self):
        """Test creating an act."""
        act = Act(
            name="Setup",
            start_position=0.0,
            end_position=0.25,
            purpose="Establish the world and characters",
            key_events=["Introduction", "Inciting incident"],
            emotional_arc="Curiosity",
            percentage_of_book=0.25
        )
        
        assert act.name == "Setup"
        assert act.start_position == 0.0
        assert act.end_position == 0.25
        assert len(act.key_events) == 2
    
    def test_act_to_dict(self):
        """Test converting act to dictionary."""
        act = Act(
            name="Test Act",
            start_position=0.0,
            end_position=0.5,
            purpose="Test purpose"
        )
        
        result = act.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == "Test Act"


class TestActStructure:
    """Tests for ActStructure."""
    
    @pytest.fixture
    def act_structure(self):
        """Create a test act structure."""
        return ActStructure(
            name="three_act",
            acts=[
                Act("Act 1", 0.0, 0.33, "Setup"),
                Act("Act 2", 0.33, 0.66, "Confrontation"),
                Act("Act 3", 0.66, 1.0, "Resolution")
            ],
            turning_points=[
                TurningPoint("Inciting Incident", 0.1, "The call to adventure"),
                TurningPoint("Climax", 0.9, "Final confrontation")
            ]
        )
    
    def test_get_act_at_position(self, act_structure):
        """Test getting act at a specific position."""
        act = act_structure.get_act_at_position(0.5)
        assert act is not None
        assert act.name == "Act 2"
    
    def test_get_act_at_boundary(self, act_structure):
        """Test getting act at boundary positions."""
        act = act_structure.get_act_at_position(0.0)
        assert act.name == "Act 1"
        
        act = act_structure.get_act_at_position(0.99)
        assert act.name == "Act 3"
    
    def test_get_turning_points_in_range(self, act_structure):
        """Test getting turning points in a range."""
        tps = act_structure.get_turning_points_in_range(0.0, 0.5)
        assert len(tps) == 1
        assert tps[0].name == "Inciting Incident"


class TestGenreTemplate:
    """Tests for GenreTemplate."""
    
    @pytest.fixture
    def genre_template(self):
        """Create a test genre template."""
        return GenreTemplate(
            genre_name="test_genre",
            category=GenreCategory.FICTION,
            subgenres=["sub1", "sub2"],
            description="A test genre",
            required_elements=["element1", "element2"],
            forbidden_elements=["bad_element"],
            typical_tone="dramatic",
            typical_pacing="moderate"
        )
    
    def test_template_creation(self, genre_template):
        """Test creating a genre template."""
        assert genre_template.genre_name == "test_genre"
        assert genre_template.category == GenreCategory.FICTION
        assert len(genre_template.required_elements) == 2
    
    def test_get_chapter_template(self, genre_template):
        """Test getting chapter template."""
        # Add chapter templates
        genre_template.chapter_templates = [
            ChapterTemplate(
                name="Opening",
                chapter_type="opening",
                typical_position=(0.0, 0.1)
            ),
            ChapterTemplate(
                name="Climax",
                chapter_type="climax",
                typical_position=(0.8, 0.95)
            )
        ]
        
        template = genre_template.get_chapter_template(0.05)
        assert template is not None
        assert template.name == "Opening"
        
        template = genre_template.get_chapter_template(0.85)
        assert template is not None
        assert template.name == "Climax"
    
    def test_to_dict(self, genre_template):
        """Test converting template to dictionary."""
        result = genre_template.to_dict()
        
        assert isinstance(result, dict)
        assert result["genre_name"] == "test_genre"
        assert result["category"] == "fiction"


class TestGenreTemplateManager:
    """Tests for GenreTemplateManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a GenreTemplateManager."""
        return GenreTemplateManager()
    
    def test_get_thriller_template(self, manager):
        """Test getting thriller template."""
        template = manager.get_template("thriller")
        
        assert template is not None
        assert template.genre_name == "thriller"
        assert "tension" in template.required_elements
    
    def test_get_romance_template(self, manager):
        """Test getting romance template."""
        template = manager.get_template("romance")
        
        assert template is not None
        assert template.genre_name == "romance"
        assert "happy_ending" in template.required_elements
    
    def test_get_fantasy_template(self, manager):
        """Test getting fantasy template."""
        template = manager.get_template("fantasy")
        
        assert template is not None
        assert template.genre_name == "fantasy"
        assert "magic_system" in template.required_elements
    
    def test_get_nonexistent_template(self, manager):
        """Test getting a non-existent template."""
        template = manager.get_template("nonexistent_genre")
        assert template is None
    
    def test_list_genres(self, manager):
        """Test listing all genres."""
        genres = manager.list_genres()
        
        assert "thriller" in genres
        assert "romance" in genres
        assert "fantasy" in genres
        assert "mystery" in genres
    
    def test_register_custom_template(self, manager):
        """Test registering a custom template."""
        custom = GenreTemplate(
            genre_name="custom_genre",
            category=GenreCategory.FICTION,
            description="A custom genre"
        )
        
        manager.register_template(custom)
        
        retrieved = manager.get_template("custom_genre")
        assert retrieved is not None
        assert retrieved.genre_name == "custom_genre"
    
    def test_create_custom_template(self, manager):
        """Test creating a customized template."""
        custom = manager.create_custom_template(
            base_genre="thriller",
            customizations={
                "genre_name": "psychological_thriller",
                "typical_tone": "unsettling"
            }
        )
        
        assert custom.genre_name == "psychological_thriller"
        assert custom.typical_tone == "unsettling"
        # Should inherit from thriller
        assert "tension" in custom.required_elements


class TestPredefinedTemplates:
    """Tests for predefined genre templates."""
    
    def test_thriller_template_structure(self):
        """Test thriller template has proper structure."""
        template = GENRE_TEMPLATES.get("thriller")
        
        assert template is not None
        assert template.act_structure is not None
        assert len(template.act_structure.acts) == 3
        assert len(template.act_structure.turning_points) == 5
    
    def test_romance_template_structure(self):
        """Test romance template has proper structure."""
        template = GENRE_TEMPLATES.get("romance")
        
        assert template is not None
        assert template.act_structure is not None
        # Romance typically has 4 acts
        assert len(template.act_structure.acts) == 4
    
    def test_fantasy_template_hero_journey(self):
        """Test fantasy template uses hero's journey structure."""
        template = GENRE_TEMPLATES.get("fantasy")
        
        assert template is not None
        assert template.act_structure is not None
        assert template.act_structure.name == "heros_journey"
    
    def test_all_templates_have_required_fields(self):
        """Test all templates have required fields."""
        for name, template in GENRE_TEMPLATES.items():
            assert template.genre_name, f"{name} missing genre_name"
            assert template.category, f"{name} missing category"
            assert isinstance(template.required_elements, list), f"{name} missing required_elements"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])