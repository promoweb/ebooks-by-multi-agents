"""
Tests for the Technical Content Support System.

Tests cover CitationManager, FactVerificationSystem, and
AcademicStructureManager.
"""

import pytest

from src.technical import (
    CitationStyle,
    Author,
    Reference,
    CitationManager,
    ClaimType,
    VerificationStatus,
    FactualClaim,
    ClaimExtractor,
    FactVerificationSystem,
    MockKnowledgeBase,
    TechnicalAccuracyChecker,
    DocumentType,
    Section,
    AcademicStructure,
    AcademicStructureManager,
)


class TestAuthor:
    """Tests for Author dataclass."""
    
    def test_author_creation(self):
        """Test creating an author."""
        author = Author(
            first_name="John",
            last_name="Smith",
            middle_name="Robert",
            suffix="Jr."
        )
        
        assert author.first_name == "John"
        assert author.last_name == "Smith"
    
    def test_format_apa(self):
        """Test APA author formatting."""
        author = Author(first_name="John", last_name="Smith")
        formatted = author.format_apa()
        assert formatted == "Smith, J."
    
    def test_format_mla(self):
        """Test MLA author formatting."""
        author = Author(first_name="John", last_name="Smith")
        formatted = author.format_mla()
        assert formatted == "Smith, John"
    
    def test_format_ieee(self):
        """Test IEEE author formatting."""
        author = Author(first_name="John", last_name="Smith")
        formatted = author.format_ieee()
        assert formatted == "J. Smith"


class TestReference:
    """Tests for Reference dataclass."""
    
    @pytest.fixture
    def book_reference(self):
        """Create a book reference."""
        return Reference(
            reference_id="ref_1",
            reference_type="book",
            title="The Great Book",
            authors=[
                Author(first_name="John", last_name="Smith"),
                Author(first_name="Jane", last_name="Doe")
            ],
            year=2024,
            publisher="Test Publisher"
        )
    
    @pytest.fixture
    def article_reference(self):
        """Create an article reference."""
        return Reference(
            reference_id="ref_2",
            reference_type="article",
            title="Important Research",
            authors=[Author(first_name="Alice", last_name="Johnson")],
            year=2023,
            journal="Science Journal",
            volume="10",
            issue="2",
            pages="45-67",
            doi="10.1234/test"
        )
    
    def test_reference_creation(self, book_reference):
        """Test creating a reference."""
        assert book_reference.reference_id == "ref_1"
        assert book_reference.title == "The Great Book"
        assert len(book_reference.authors) == 2
    
    def test_format_authors_apa(self, book_reference):
        """Test formatting authors in APA style."""
        formatted = book_reference.format_authors(CitationStyle.APA)
        assert "Smith" in formatted
        assert "Doe" in formatted
    
    def test_format_bibliography_apa(self, book_reference):
        """Test formatting APA bibliography entry."""
        entry = book_reference.format_bibliography_entry(CitationStyle.APA)
        assert "Smith" in entry
        assert "2024" in entry
        assert "The Great Book" in entry
    
    def test_format_bibliography_mla(self, book_reference):
        """Test formatting MLA bibliography entry."""
        entry = book_reference.format_bibliography_entry(CitationStyle.MLA)
        assert "Smith" in entry
        assert "Test Publisher" in entry


class TestCitationManager:
    """Tests for CitationManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a CitationManager."""
        return CitationManager(style="apa")
    
    def test_add_reference(self, manager):
        """Test adding a reference."""
        ref = Reference(
            reference_id="test_1",
            reference_type="book",
            title="Test Book",
            authors=[Author(first_name="John", last_name="Smith")],
            year=2024
        )
        
        ref_id = manager.add_reference(ref)
        assert ref_id == "test_1"
    
    def test_create_reference(self, manager):
        """Test creating a reference through manager."""
        ref = manager.create_reference(
            reference_type="book",
            title="New Book",
            authors=[{"first_name": "Jane", "last_name": "Doe"}],
            year=2023
        )
        
        assert ref.title == "New Book"
        assert ref.year == 2023
    
    def test_format_citation_parenthetical(self, manager):
        """Test formatting parenthetical citation."""
        manager.create_reference(
            reference_type="book",
            title="Test Book",
            authors=[{"first_name": "John", "last_name": "Smith"}],
            year=2024
        )
        
        citation = manager.format_citation("ref_1", citation_type="parenthetical")
        assert "Smith" in citation
        assert "2024" in citation
    
    def test_format_citation_with_page(self, manager):
        """Test formatting citation with page number."""
        manager.create_reference(
            reference_type="book",
            title="Test Book",
            authors=[{"first_name": "John", "last_name": "Smith"}],
            year=2024
        )
        
        citation = manager.format_citation("ref_1", page="45")
        assert "45" in citation
    
    def test_format_bibliography(self, manager):
        """Test formatting bibliography."""
        manager.create_reference(
            reference_type="book",
            title="Book One",
            authors=[{"first_name": "John", "last_name": "Smith"}],
            year=2024
        )
        
        manager.create_reference(
            reference_type="book",
            title="Book Two",
            authors=[{"first_name": "Jane", "last_name": "Doe"}],
            year=2023
        )
        
        bibliography = manager.format_bibliography()
        assert "Book One" in bibliography
        assert "Book Two" in bibliography
    
    def test_change_style(self, manager):
        """Test changing citation style."""
        manager.create_reference(
            reference_type="book",
            title="Test Book",
            authors=[{"first_name": "John", "last_name": "Smith"}],
            year=2024
        )
        
        # APA style
        apa_citation = manager.format_citation("ref_1")
        
        # Change to MLA
        manager.set_style("mla")
        mla_citation = manager.format_citation("ref_1")
        
        # Both should contain author name
        assert "Smith" in apa_citation
        assert "Smith" in mla_citation


class TestClaimExtractor:
    """Tests for ClaimExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a ClaimExtractor."""
        return ClaimExtractor()
    
    def test_extract_statistical_claims(self, extractor):
        """Test extracting statistical claims."""
        content = "Research shows that 75% of users prefer option A."
        
        claims = extractor.extract_claims(content)
        
        assert len(claims) > 0
        assert any(c.claim_type == ClaimType.STATISTICAL for c in claims)
    
    def test_extract_date_claims(self, extractor):
        """Test extracting date claims."""
        content = "The treaty was signed on January 15, 2024."
        
        claims = extractor.extract_claims(content)
        
        # Should detect the date
        assert len(claims) > 0
    
    def test_extract_multiple_claims(self, extractor):
        """Test extracting multiple claims."""
        content = """
        Studies indicate that 60% of participants improved.
        According to research published in January 2024, the method is effective.
        Experts say this approach works.
        """
        
        claims = extractor.extract_claims(content)
        assert len(claims) >= 2


class TestFactVerificationSystem:
    """Tests for FactVerificationSystem."""
    
    @pytest.fixture
    def verifier(self):
        """Create a FactVerificationSystem with mock knowledge base."""
        return FactVerificationSystem(
            knowledge_base=MockKnowledgeBase()
        )
    
    def test_verify_content(self, verifier):
        """Test verifying content."""
        content = "Water is composed of hydrogen and oxygen. The Moon landing was in 1969."
        
        report = verifier.verify_content(content)
        
        assert report.total_claims > 0
        assert report.overall_accuracy >= 0
    
    def test_verify_claim(self, verifier):
        """Test verifying a single claim."""
        claim = FactualClaim(
            claim_id="test_1",
            claim_text="World War II ended in 1945.",
            claim_type=ClaimType.HISTORICAL,
            location="test",
            context="test context"
        )
        
        result = verifier.verify_claim(claim)
        
        assert result.status in [
            VerificationStatus.VERIFIED,
            VerificationStatus.UNVERIFIED,
            VerificationStatus.DISPUTED
        ]


class TestTechnicalAccuracyChecker:
    """Tests for TechnicalAccuracyChecker."""
    
    @pytest.fixture
    def checker(self):
        """Create a TechnicalAccuracyChecker."""
        return TechnicalAccuracyChecker()
    
    def test_check_computer_science_content(self, checker):
        """Test checking computer science content."""
        content = """
        An algorithm is a step-by-step procedure for solving a problem.
        A data structure organizes and stores data efficiently.
        """
        
        report = checker.check(
            content=content,
            domain="computer_science",
            technical_level="introductory"
        )
        
        assert report.overall_score >= 0
        assert "terminology" in report.checked_elements
    
    def test_detect_common_errors(self, checker):
        """Test detecting common technical errors."""
        content = "Java and JavaScript are the same language."
        
        report = checker.check(
            content=content,
            domain="computer_science",
            technical_level="introductory"
        )
        
        # Should detect the error
        assert len(report.issues) > 0
        assert any(i.issue_type == "common_error" for i in report.issues)


class TestAcademicStructureManager:
    """Tests for AcademicStructureManager."""
    
    @pytest.fixture
    def manager(self):
        """Create an AcademicStructureManager."""
        return AcademicStructureManager()
    
    def test_create_thesis_structure(self, manager):
        """Test creating thesis structure."""
        structure = manager.create_structure(
            document_type="thesis",
            title="Test Thesis"
        )
        
        assert structure.document_type == DocumentType.THESIS
        assert structure.title == "Test Thesis"
        assert len(structure.sections) > 0
    
    def test_create_research_paper_structure(self, manager):
        """Test creating research paper structure."""
        structure = manager.create_structure(
            document_type="research_paper",
            title="Test Paper"
        )
        
        assert structure.document_type == DocumentType.RESEARCH_PAPER
        # Should have standard sections
        section_ids = [s.section_id for s in structure.get_all_sections()]
        assert "abstract" in section_ids
        assert "introduction" in section_ids
    
    def test_validate_structure(self, manager):
        """Test validating structure."""
        structure = manager.create_structure(
            document_type="research_paper",
            title="Test Paper"
        )
        
        validation = manager.validate_structure(structure)
        
        assert "valid" in validation
        assert "issues" in validation
    
    def test_get_section_template(self, manager):
        """Test getting section template."""
        template = manager.get_section_template("abstract")
        
        assert template is not None
        assert template.section_id == "abstract"


class TestSection:
    """Tests for Section dataclass."""
    
    def test_section_creation(self):
        """Test creating a section."""
        section = Section(
            section_id="test_section",
            title="Test Section",
            level=1,
            required=True,
            word_count_range=(500, 1500),
            content_guidelines="Write about test topics"
        )
        
        assert section.section_id == "test_section"
        assert section.level == 1
    
    def test_section_with_subsections(self):
        """Test section with subsections."""
        section = Section(
            section_id="main",
            title="Main Section",
            level=1,
            subsections=[
                Section("sub1", "Subsection 1", 2),
                Section("sub2", "Subsection 2", 2)
            ]
        )
        
        assert len(section.subsections) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])