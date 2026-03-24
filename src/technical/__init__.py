"""
Scientific/Technical Content Support for BookWriterAI.

This package provides citation management, fact verification, and
technical accuracy checking for academic and technical content.

Usage:
    from src.technical import CitationManager, CitationStyle
    from src.technical import FactVerificationSystem, TechnicalAccuracyChecker
    from src.technical import AcademicStructureManager
    
    # Citation management
    manager = CitationManager(style="apa")
    manager.create_reference(
        reference_type="book",
        title="Example Book",
        authors=[{"first_name": "John", "last_name": "Smith"}],
        year=2024,
        publisher="Example Publisher"
    )
    
    # Fact verification
    verifier = FactVerificationSystem()
    report = verifier.verify_content(content)
    
    # Academic structure
    struct_manager = AcademicStructureManager()
    structure = struct_manager.create_structure("thesis", "My Thesis")
"""

from .citations import (
    CitationStyle,
    Author,
    Reference,
    CitationManager,
)

from .verification import (
    ClaimType,
    VerificationStatus,
    FactualClaim,
    VerificationResult,
    ContentVerificationReport,
    ClaimExtractor,
    KnowledgeBase,
    MockKnowledgeBase,
    FactVerificationSystem,
    TechnicalIssue,
    TechnicalAccuracyReport,
    TechnicalAccuracyChecker,
)

from .structure import (
    DocumentType,
    Section,
    AcademicStructure,
    AcademicStructureManager,
)


__all__ = [
    # Citations
    "CitationStyle",
    "Author",
    "Reference",
    "CitationManager",
    
    # Verification
    "ClaimType",
    "VerificationStatus",
    "FactualClaim",
    "VerificationResult",
    "ContentVerificationReport",
    "ClaimExtractor",
    "KnowledgeBase",
    "MockKnowledgeBase",
    "FactVerificationSystem",
    "TechnicalIssue",
    "TechnicalAccuracyReport",
    "TechnicalAccuracyChecker",
    
    # Structure
    "DocumentType",
    "Section",
    "AcademicStructure",
    "AcademicStructureManager",
]