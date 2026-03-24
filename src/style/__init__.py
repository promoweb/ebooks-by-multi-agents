"""
Style System for BookWriterAI.

This module provides comprehensive style management capabilities
including style profiles, validation, and enforcement.

Components:
- Style Profiles: Define and manage writing styles
- Style Enforcement: Inject style into prompts
- Style Validation: Validate content against style profiles
- Style Correction: Apply corrections for style compliance

Example usage:
    from src.style import StyleProfile, StyleProfileManager, StyleValidator
    
    # Get a predefined profile
    manager = StyleProfileManager()
    profile = manager.get_profile("literary")
    
    # Validate content
    validator = StyleValidator()
    report = validator.validate(text, profile)
    
    # Check compliance
    if not report.is_compliant:
        print(f"Style violations: {len(report.violations)}")
"""

# Profile System
from src.style.profile import (
    NarrativeVoice,
    AuthorialVoice,
    VocabularyComplexity,
    Tone,
    SpeechPatterns,
    StyleProfile,
    STYLE_PROFILES,
    StyleProfileManager,
)

# Enforcement System
from src.style.enforcement import (
    ContentType,
    StyleViolation,
    StyleValidationReport,
    StylePromptInjector,
    StyleValidator,
    StyleCorrector,
)


__all__ = [
    # Profile System
    "NarrativeVoice",
    "AuthorialVoice",
    "VocabularyComplexity",
    "Tone",
    "SpeechPatterns",
    "StyleProfile",
    "STYLE_PROFILES",
    "StyleProfileManager",
    
    # Enforcement System
    "ContentType",
    "StyleViolation",
    "StyleValidationReport",
    "StylePromptInjector",
    "StyleValidator",
    "StyleCorrector",
]