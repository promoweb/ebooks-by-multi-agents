"""
Genre-Specific Template System for BookWriterAI.

This package provides genre-specific templates, conventions, and
configurations for different types of book generation.

Usage:
    from src.genre import GenreTemplateManager, GenreTemplate
    
    manager = GenreTemplateManager()
    template = manager.get_template("thriller")
    
    # Access genre-specific structure
    act_structure = template.act_structure
    required_elements = template.required_elements
"""

from .templates import (
    GenreCategory,
    Act,
    TurningPoint,
    ActStructure,
    ChapterTemplate,
    CharacterArchetype,
    PlotDeviceTemplate,
    GenreTemplate,
    GENRE_TEMPLATES,
    GenreTemplateManager,
)

from .genres import (
    SCIFI_TEMPLATE,
    LITERARY_FICTION_TEMPLATE,
    HORROR_TEMPLATE,
    NONFICTION_TEMPLATE,
    TECHNICAL_TEMPLATE,
    ACADEMIC_TEMPLATE,
    ADDITIONAL_GENRE_TEMPLATES,
)

# Combine all templates into the registry
for name, template in ADDITIONAL_GENRE_TEMPLATES.items():
    GENRE_TEMPLATES[name] = template


__all__ = [
    # Core classes
    "GenreCategory",
    "Act",
    "TurningPoint",
    "ActStructure",
    "ChapterTemplate",
    "CharacterArchetype",
    "PlotDeviceTemplate",
    "GenreTemplate",
    
    # Manager
    "GenreTemplateManager",
    
    # Template registry
    "GENRE_TEMPLATES",
    
    # Individual templates
    "SCIFI_TEMPLATE",
    "LITERARY_FICTION_TEMPLATE",
    "HORROR_TEMPLATE",
    "NONFICTION_TEMPLATE",
    "TECHNICAL_TEMPLATE",
    "ACADEMIC_TEMPLATE",
]