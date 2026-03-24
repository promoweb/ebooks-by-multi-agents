"""
Academic Structure Management for BookWriterAI.

This module provides structure management for academic documents
including theses, dissertations, research papers, and textbooks.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class DocumentType(Enum):
    """Types of academic documents."""
    THESIS = "thesis"
    DISSERTATION = "dissertation"
    RESEARCH_PAPER = "research_paper"
    TEXTBOOK = "textbook"
    MONOGRAPH = "monograph"
    REPORT = "report"
    WHITE_PAPER = "white_paper"


@dataclass
class Section:
    """Represents a section in an academic document."""
    section_id: str
    title: str
    level: int  # 1 = chapter, 2 = section, 3 = subsection
    required: bool = True
    word_count_range: tuple = (500, 5000)
    content_guidelines: str = ""
    subsections: List["Section"] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "required": self.required,
            "word_count_range": self.word_count_range,
            "content_guidelines": self.content_guidelines,
            "subsections": [s.to_dict() for s in self.subsections]
        }


@dataclass
class AcademicStructure:
    """Complete structure for an academic document."""
    document_type: DocumentType
    title: str
    sections: List[Section] = field(default_factory=list)
    front_matter: List[Section] = field(default_factory=list)
    back_matter: List[Section] = field(default_factory=list)
    total_word_count: int = 0
    style_guidelines: Dict[str, Any] = field(default_factory=dict)
    
    def get_section(self, section_id: str) -> Optional[Section]:
        """Get a section by ID."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
            for subsection in section.subsections:
                if subsection.section_id == section_id:
                    return subsection
        return None
    
    def get_all_sections(self) -> List[Section]:
        """Get all sections including subsections."""
        all_sections = []
        for section in self.sections:
            all_sections.append(section)
            all_sections.extend(section.subsections)
        return all_sections
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type.value,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "front_matter": [s.to_dict() for s in self.front_matter],
            "back_matter": [s.to_dict() for s in self.back_matter],
            "total_word_count": self.total_word_count,
            "style_guidelines": self.style_guidelines
        }


class AcademicStructureManager:
    """
    Manages academic document structures.
    
    Provides templates and structure management for various
    types of academic documents.
    """
    
    # Standard structures for different document types
    THESIS_STRUCTURE = [
        Section("title_page", "Title Page", 1, True, (100, 300)),
        Section("abstract", "Abstract", 1, True, (150, 350)),
        Section("acknowledgments", "Acknowledgments", 1, False, (100, 500)),
        Section("table_of_contents", "Table of Contents", 1, True, (0, 0)),
        Section("list_of_figures", "List of Figures", 1, False, (0, 0)),
        Section("list_of_tables", "List of Tables", 1, False, (0, 0)),
        Section("introduction", "Introduction", 1, True, (2000, 5000), 
                "Introduce the research problem, objectives, and significance",
                [
                    Section("background", "Background", 2, True, (500, 1500)),
                    Section("problem_statement", "Problem Statement", 2, True, (300, 800)),
                    Section("objectives", "Research Objectives", 2, True, (200, 500)),
                    Section("significance", "Significance of Study", 2, True, (200, 500)),
                    Section("scope", "Scope and Limitations", 2, True, (200, 500)),
                ]),
        Section("literature_review", "Literature Review", 1, True, (5000, 10000),
                "Review relevant literature and establish theoretical framework",
                [
                    Section("theoretical_framework", "Theoretical Framework", 2, True, (1500, 3000)),
                    Section("related_studies", "Related Studies", 2, True, (2000, 4000)),
                    Section("research_gap", "Research Gap", 2, True, (500, 1000)),
                ]),
        Section("methodology", "Methodology", 1, True, (3000, 6000),
                "Describe research methods and procedures",
                [
                    Section("research_design", "Research Design", 2, True, (500, 1500)),
                    Section("participants", "Participants", 2, True, (300, 800)),
                    Section("instruments", "Research Instruments", 2, True, (500, 1500)),
                    Section("procedures", "Data Collection Procedures", 2, True, (500, 1500)),
                    Section("analysis", "Data Analysis", 2, True, (500, 1500)),
                ]),
        Section("results", "Results", 1, True, (4000, 8000),
                "Present research findings",
                [
                    Section("descriptive", "Descriptive Statistics", 2, True, (1000, 2000)),
                    Section("inferential", "Inferential Statistics", 2, True, (1500, 3000)),
                    Section("summary", "Summary of Findings", 2, True, (500, 1000)),
                ]),
        Section("discussion", "Discussion", 1, True, (3000, 6000),
                "Interpret findings and discuss implications",
                [
                    Section("interpretation", "Interpretation of Results", 2, True, (1000, 2000)),
                    Section("implications", "Implications", 2, True, (500, 1500)),
                    Section("limitations", "Limitations", 2, True, (300, 800)),
                    Section("recommendations", "Recommendations", 2, True, (500, 1000)),
                ]),
        Section("conclusion", "Conclusion", 1, True, (1000, 2000)),
        Section("references", "References", 1, True, (0, 0)),
        Section("appendices", "Appendices", 1, False, (0, 0)),
    ]
    
    RESEARCH_PAPER_STRUCTURE = [
        Section("abstract", "Abstract", 1, True, (150, 300)),
        Section("introduction", "Introduction", 1, True, (500, 1500),
                "Introduce the research problem and objectives",
                [
                    Section("background", "Background", 2, False, (200, 500)),
                    Section("objectives", "Objectives", 2, True, (100, 300)),
                ]),
        Section("literature_review", "Literature Review", 1, True, (1000, 3000)),
        Section("methodology", "Methodology", 1, True, (500, 1500)),
        Section("results", "Results", 1, True, (1000, 3000)),
        Section("discussion", "Discussion", 1, True, (500, 2000)),
        Section("conclusion", "Conclusion", 1, True, (200, 500)),
        Section("references", "References", 1, True, (0, 0)),
    ]
    
    TEXTBOOK_STRUCTURE = [
        Section("preface", "Preface", 1, True, (500, 1500)),
        Section("about_author", "About the Author", 1, False, (200, 500)),
        Section("how_to_use", "How to Use This Book", 1, False, (300, 800)),
        Section("part_1", "Part I: Foundations", 1, True, (10000, 20000),
                "Foundational concepts and principles",
                [
                    Section("chapter_1", "Chapter 1: Introduction", 2, True, (3000, 6000)),
                    Section("chapter_2", "Chapter 2: Core Concepts", 2, True, (4000, 8000)),
                    Section("chapter_3", "Chapter 3: Fundamental Principles", 2, True, (4000, 8000)),
                ]),
        Section("part_2", "Part II: Core Content", 1, True, (20000, 40000),
                "Main subject matter",
                [
                    Section("chapter_4", "Chapter 4", 2, True, (5000, 10000)),
                    Section("chapter_5", "Chapter 5", 2, True, (5000, 10000)),
                    Section("chapter_6", "Chapter 6", 2, True, (5000, 10000)),
                ]),
        Section("part_3", "Part III: Advanced Topics", 1, True, (15000, 30000),
                "Advanced concepts and applications",
                [
                    Section("chapter_7", "Chapter 7", 2, True, (5000, 10000)),
                    Section("chapter_8", "Chapter 8", 2, True, (5000, 10000)),
                ]),
        Section("glossary", "Glossary", 1, True, (500, 2000)),
        Section("index", "Index", 1, True, (0, 0)),
        Section("references", "References", 1, True, (0, 0)),
    ]
    
    WHITE_PAPER_STRUCTURE = [
        Section("title_page", "Title Page", 1, True, (100, 200)),
        Section("executive_summary", "Executive Summary", 1, True, (300, 700)),
        Section("introduction", "Introduction", 1, True, (500, 1000)),
        Section("problem_statement", "Problem Statement", 1, True, (300, 800)),
        Section("analysis", "Analysis", 1, True, (1500, 3000)),
        Section("solution", "Proposed Solution", 1, True, (1000, 2500)),
        Section("implementation", "Implementation", 1, True, (500, 1500)),
        Section("conclusion", "Conclusion", 1, True, (200, 500)),
        Section("references", "References", 1, False, (0, 0)),
    ]
    
    def __init__(self):
        """Initialize the academic structure manager."""
        self.structures = {
            DocumentType.THESIS: self.THESIS_STRUCTURE,
            DocumentType.DISSERTATION: self.THESIS_STRUCTURE,  # Similar to thesis
            DocumentType.RESEARCH_PAPER: self.RESEARCH_PAPER_STRUCTURE,
            DocumentType.TEXTBOOK: self.TEXTBOOK_STRUCTURE,
            DocumentType.WHITE_PAPER: self.WHITE_PAPER_STRUCTURE,
        }
    
    def create_structure(
        self,
        document_type: str,
        title: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> AcademicStructure:
        """
        Create an academic document structure.
        
        Args:
            document_type: Type of document to create
            title: Document title
            requirements: Optional custom requirements
        
        Returns:
            AcademicStructure for the document
        """
        doc_type = DocumentType(document_type.lower())
        base_sections = self.structures.get(doc_type, self.RESEARCH_PAPER_STRUCTURE)
        
        # Create deep copy of sections
        sections = [self._copy_section(s) for s in base_sections]
        
        # Apply custom requirements
        if requirements:
            sections = self._apply_requirements(sections, requirements)
        
        # Separate front and back matter
        front_matter = []
        back_matter = []
        main_sections = []
        
        front_matter_ids = ["title_page", "abstract", "acknowledgments", 
                           "table_of_contents", "list_of_figures", "list_of_tables",
                           "preface", "about_author", "how_to_use", "executive_summary"]
        back_matter_ids = ["references", "appendices", "glossary", "index"]
        
        for section in sections:
            if section.section_id in front_matter_ids:
                front_matter.append(section)
            elif section.section_id in back_matter_ids:
                back_matter.append(section)
            else:
                main_sections.append(section)
        
        # Calculate total word count
        total_words = self._calculate_total_words(main_sections)
        
        return AcademicStructure(
            document_type=doc_type,
            title=title,
            sections=main_sections,
            front_matter=front_matter,
            back_matter=back_matter,
            total_word_count=total_words,
            style_guidelines=requirements.get("style_guidelines", {}) if requirements else {}
        )
    
    def _copy_section(self, section: Section) -> Section:
        """Create a deep copy of a section."""
        return Section(
            section_id=section.section_id,
            title=section.title,
            level=section.level,
            required=section.required,
            word_count_range=section.word_count_range,
            content_guidelines=section.content_guidelines,
            subsections=[self._copy_section(s) for s in section.subsections]
        )
    
    def _apply_requirements(
        self,
        sections: List[Section],
        requirements: Dict[str, Any]
    ) -> List[Section]:
        """Apply custom requirements to sections."""
        # Adjust word counts if specified
        if "target_word_count" in requirements:
            target = requirements["target_word_count"]
            current = self._calculate_total_words(sections)
            if current > 0:
                scale = target / current
                for section in sections:
                    self._scale_word_count(section, scale)
        
        # Add custom sections if specified
        if "additional_sections" in requirements:
            for custom_section in requirements["additional_sections"]:
                sections.append(Section(
                    section_id=custom_section.get("id", f"custom_{len(sections)}"),
                    title=custom_section.get("title", "Custom Section"),
                    level=custom_section.get("level", 1),
                    required=custom_section.get("required", True),
                    word_count_range=custom_section.get("word_count_range", (500, 2000)),
                    content_guidelines=custom_section.get("guidelines", "")
                ))
        
        return sections
    
    def _scale_word_count(self, section: Section, scale: float) -> None:
        """Scale word count range for a section."""
        section.word_count_range = (
            int(section.word_count_range[0] * scale),
            int(section.word_count_range[1] * scale)
        )
        for subsection in section.subsections:
            self._scale_word_count(subsection, scale)
    
    def _calculate_total_words(self, sections: List[Section]) -> int:
        """Calculate total word count for sections."""
        total = 0
        for section in sections:
            total += section.word_count_range[1]
            total += self._calculate_total_words(section.subsections)
        return total
    
    def get_section_template(
        self,
        section_type: str
    ) -> Optional[Section]:
        """Get a template for a specific section type."""
        templates = {
            "abstract": Section(
                "abstract", "Abstract", 1, True, (150, 350),
                "Concise summary of the research including objectives, methods, key findings, and conclusions"
            ),
            "introduction": Section(
                "introduction", "Introduction", 1, True, (500, 2000),
                "Introduce the topic, provide context, and state objectives"
            ),
            "literature_review": Section(
                "literature_review", "Literature Review", 1, True, (1000, 5000),
                "Review and synthesize relevant literature"
            ),
            "methodology": Section(
                "methodology", "Methodology", 1, True, (500, 2000),
                "Describe research methods and procedures"
            ),
            "results": Section(
                "results", "Results", 1, True, (1000, 3000),
                "Present findings objectively"
            ),
            "discussion": Section(
                "discussion", "Discussion", 1, True, (500, 2000),
                "Interpret findings and discuss implications"
            ),
            "conclusion": Section(
                "conclusion", "Conclusion", 1, True, (200, 1000),
                "Summarize key points and provide final thoughts"
            ),
        }
        return templates.get(section_type.lower())
    
    def validate_structure(
        self,
        structure: AcademicStructure
    ) -> Dict[str, Any]:
        """
        Validate an academic structure.
        
        Args:
            structure: Structure to validate
        
        Returns:
            Validation report with issues and suggestions
        """
        issues = []
        suggestions = []
        
        # Check for required sections
        all_sections = structure.get_all_sections()
        section_ids = [s.section_id for s in all_sections]
        
        required_sections = self._get_required_sections(structure.document_type)
        for req_id in required_sections:
            if req_id not in section_ids:
                issues.append(f"Missing required section: {req_id}")
        
        # Check section ordering
        expected_order = self._get_expected_order(structure.document_type)
        actual_order = [s.section_id for s in structure.sections]
        
        for i, section_id in enumerate(actual_order):
            if section_id in expected_order:
                expected_pos = expected_order.index(section_id)
                if expected_pos < i:
                    suggestions.append(
                        f"Consider moving '{section_id}' earlier in the document"
                    )
        
        # Check word counts
        total_words = structure.total_word_count
        expected_range = self._get_expected_word_range(structure.document_type)
        
        if total_words < expected_range[0]:
            suggestions.append(
                f"Document may be too short. Expected at least {expected_range[0]} words, "
                f"currently estimated at {total_words} words."
            )
        elif total_words > expected_range[1]:
            suggestions.append(
                f"Document may be too long. Expected at most {expected_range[1]} words, "
                f"currently estimated at {total_words} words."
            )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "section_count": len(all_sections),
            "estimated_word_count": total_words
        }
    
    def _get_required_sections(self, doc_type: DocumentType) -> List[str]:
        """Get required sections for a document type."""
        required = {
            DocumentType.THESIS: ["abstract", "introduction", "literature_review", 
                                  "methodology", "results", "discussion", "conclusion", "references"],
            DocumentType.DISSERTATION: ["abstract", "introduction", "literature_review",
                                        "methodology", "results", "discussion", "conclusion", "references"],
            DocumentType.RESEARCH_PAPER: ["abstract", "introduction", "methodology", 
                                           "results", "discussion", "conclusion", "references"],
            DocumentType.TEXTBOOK: ["preface", "references"],
            DocumentType.WHITE_PAPER: ["executive_summary", "introduction", "conclusion"],
        }
        return required.get(doc_type, [])
    
    def _get_expected_order(self, doc_type: DocumentType) -> List[str]:
        """Get expected section order for a document type."""
        return [s.section_id for s in self.structures.get(doc_type, [])]
    
    def _get_expected_word_range(self, doc_type: DocumentType) -> tuple:
        """Get expected word count range for a document type."""
        ranges = {
            DocumentType.THESIS: (30000, 80000),
            DocumentType.DISSERTATION: (50000, 100000),
            DocumentType.RESEARCH_PAPER: (3000, 10000),
            DocumentType.TEXTBOOK: (50000, 200000),
            DocumentType.WHITE_PAPER: (3000, 8000),
        }
        return ranges.get(doc_type, (5000, 20000))


__all__ = [
    "DocumentType",
    "Section",
    "AcademicStructure",
    "AcademicStructureManager",
]