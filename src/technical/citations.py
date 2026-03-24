"""
Citation Management System for BookWriterAI.

This module provides citation management, formatting, and bibliography
generation for academic and technical content.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


logger = logging.getLogger("BookWriterAI")


class CitationStyle(Enum):
    """Supported citation styles."""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    HARVARD = "harvard"
    VANCOUVER = "vancouver"
    TURABIAN = "turabian"


@dataclass
class Author:
    """Represents an author of a work."""
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    suffix: Optional[str] = None  # Jr., III, etc.
    
    def format_apa(self) -> str:
        """Format author name in APA style."""
        parts = [f"{self.last_name}, {self.first_name[0]}."]
        if self.middle_name:
            parts.append(f"{self.middle_name[0]}.")
        if self.suffix:
            parts.append(self.suffix)
        return "".join(parts)
    
    def format_mla(self) -> str:
        """Format author name in MLA style."""
        return f"{self.last_name}, {self.first_name}"
    
    def format_chicago(self) -> str:
        """Format author name in Chicago style."""
        parts = [f"{self.first_name} {self.last_name}"]
        if self.suffix:
            parts.append(f", {self.suffix}")
        return "".join(parts)
    
    def format_ieee(self) -> str:
        """Format author name in IEEE style."""
        return f"{self.first_name[0]}. {self.last_name}"
    
    def format_harvard(self) -> str:
        """Format author name in Harvard style."""
        return f"{self.last_name}, {self.first_name[0]}."
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "suffix": self.suffix
        }


@dataclass
class Reference:
    """Represents a bibliographic reference."""
    # Core fields
    reference_id: str
    reference_type: str  # book, article, journal, website, conference, thesis, etc.
    title: str
    authors: List[Author]
    year: int
    
    # Optional fields
    publisher: Optional[str] = None
    publisher_location: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    access_date: Optional[str] = None
    edition: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    editor: Optional[str] = None
    translator: Optional[str] = None
    chapter: Optional[str] = None
    institution: Optional[str] = None  # For theses
    conference: Optional[str] = None  # For conference papers
    
    # Additional metadata
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def format_authors(self, style: CitationStyle) -> str:
        """Format authors list according to style."""
        if not self.authors:
            return ""
        
        if style == CitationStyle.APA:
            if len(self.authors) == 1:
                return self.authors[0].format_apa()
            elif len(self.authors) == 2:
                return f"{self.authors[0].format_apa()} & {self.authors[1].format_apa()}"
            else:
                formatted = ", ".join(a.format_apa() for a in self.authors[:-1])
                return f"{formatted}, & {self.authors[-1].format_apa()}"
        
        elif style == CitationStyle.MLA:
            if len(self.authors) == 1:
                return self.authors[0].format_mla()
            elif len(self.authors) == 2:
                return f"{self.authors[0].format_mla()}, and {self.authors[1].first_name} {self.authors[1].last_name}"
            else:
                return f"{self.authors[0].format_mla()}, et al"
        
        elif style == CitationStyle.IEEE:
            if len(self.authors) <= 6:
                return ", ".join(a.format_ieee() for a in self.authors)
            else:
                return f"{self.authors[0].format_ieee()}, et al."
        
        elif style == CitationStyle.HARVARD:
            if len(self.authors) == 1:
                return self.authors[0].format_harvard()
            elif len(self.authors) == 2:
                return f"{self.authors[0].format_harvard()} and {self.authors[1].format_harvard()}"
            else:
                return f"{self.authors[0].format_harvard()} et al."
        
        else:  # Chicago and others
            if len(self.authors) == 1:
                return self.authors[0].format_chicago()
            elif len(self.authors) == 2:
                return f"{self.authors[0].format_chicago()} and {self.authors[1].format_chicago()}"
            else:
                return f"{self.authors[0].format_chicago()} et al."
    
    def format_bibliography_entry(self, style: CitationStyle) -> str:
        """Format full bibliography entry according to style."""
        authors = self.format_authors(style)
        year = str(self.year)
        
        if style == CitationStyle.APA:
            return self._format_apa_bibliography(authors, year)
        elif style == CitationStyle.MLA:
            return self._format_mla_bibliography(authors, year)
        elif style == CitationStyle.CHICAGO:
            return self._format_chicago_bibliography(authors, year)
        elif style == CitationStyle.IEEE:
            return self._format_ieee_bibliography(authors, year)
        elif style == CitationStyle.HARVARD:
            return self._format_harvard_bibliography(authors, year)
        else:
            return self._format_apa_bibliography(authors, year)
    
    def _format_apa_bibliography(self, authors: str, year: str) -> str:
        """Format APA bibliography entry."""
        parts = [f"{authors} ({year})."]
        
        if self.reference_type == "book":
            parts.append(f" *{self.title}*.")
            if self.edition:
                parts.append(f" ({self.edition} ed.).")
            if self.publisher:
                parts.append(f" {self.publisher}.")
        
        elif self.reference_type == "article":
            parts.append(f" {self.title}.")
            if self.journal:
                parts.append(f" *{self.journal}*,")
            if self.volume:
                parts.append(f" *{self.volume}*")
            if self.issue:
                parts.append(f"({self.issue})")
            if self.pages:
                parts.append(f", {self.pages}.")
            if self.doi:
                parts.append(f" https://doi.org/{self.doi}")
        
        elif self.reference_type == "website":
            parts.append(f" {self.title}.")
            if self.publisher:
                parts.append(f" {self.publisher}.")
            if self.url:
                parts.append(f" Retrieved from {self.url}")
            if self.access_date:
                parts.append(f" (accessed {self.access_date})")
        
        else:
            parts.append(f" *{self.title}*.")
            if self.publisher:
                parts.append(f" {self.publisher}.")
        
        return "".join(parts)
    
    def _format_mla_bibliography(self, authors: str, year: str) -> str:
        """Format MLA bibliography entry."""
        parts = [f"{authors}."]
        parts.append(f' "{self.title}."')
        
        if self.reference_type == "book":
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
        
        elif self.reference_type == "article":
            if self.journal:
                parts.append(f" *{self.journal}*,")
            if self.volume:
                parts.append(f" vol. {self.volume},")
            if self.issue:
                parts.append(f" no. {self.issue},")
            if self.year:
                parts.append(f" {year},")
            if self.pages:
                parts.append(f" pp. {self.pages}.")
        
        elif self.reference_type == "website":
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
            if self.url:
                parts.append(f" {self.url}.")
            if self.access_date:
                parts.append(f" Accessed {self.access_date}.")
        
        else:
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
        
        return "".join(parts)
    
    def _format_chicago_bibliography(self, authors: str, year: str) -> str:
        """Format Chicago bibliography entry."""
        parts = [f"{authors}."]
        parts.append(f" *{self.title}*.")
        
        if self.reference_type == "book":
            if self.publisher_location:
                parts.append(f" {self.publisherLocation}:")
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
        
        elif self.reference_type == "article":
            if self.journal:
                parts.append(f" *{self.journal}*")
            if self.volume:
                parts.append(f" {self.volume},")
            if self.issue:
                parts.append(f" no. {self.issue} ({year}):")
            if self.pages:
                parts.append(f" {self.pages}.")
        
        else:
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
        
        return "".join(parts)
    
    def _format_ieee_bibliography(self, authors: str, year: str) -> str:
        """Format IEEE bibliography entry."""
        parts = [f'{authors}, "{self.title},"']
        
        if self.reference_type == "book":
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
        
        elif self.reference_type == "article":
            if self.journal:
                parts.append(f" *{self.journal}*,")
            if self.volume:
                parts.append(f" vol. {self.volume},")
            if self.issue:
                parts.append(f" no. {self.issue},")
            if self.pages:
                parts.append(f" pp. {self.pages},")
            parts.append(f" {year}.")
        
        else:
            if self.publisher:
                parts.append(f" {self.publisher},")
            parts.append(f" {year}.")
        
        return "".join(parts)
    
    def _format_harvard_bibliography(self, authors: str, year: str) -> str:
        """Format Harvard bibliography entry."""
        parts = [f"{authors} ({year})"]
        parts.append(f" *{self.title}*.")
        
        if self.reference_type == "book":
            if self.edition:
                parts.append(f" {self.edition} edn.")
            if self.publisher:
                parts.append(f" {self.publisher}.")
        
        elif self.reference_type == "article":
            if self.journal:
                parts.append(f" *{self.journal}*,")
            if self.volume:
                parts.append(f" {self.volume}")
            if self.issue:
                parts.append(f"({self.issue})")
            if self.pages:
                parts.append(f", pp. {self.pages}.")
        
        else:
            if self.publisher:
                parts.append(f" {self.publisher}.")
        
        return "".join(parts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "title": self.title,
            "authors": [a.to_dict() for a in self.authors],
            "year": self.year,
            "publisher": self.publisher,
            "publisher_location": self.publisher_location,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "url": self.url,
            "access_date": self.access_date,
            "edition": self.edition,
            "isbn": self.isbn,
            "issn": self.issn,
            "editor": self.editor,
            "translator": self.translator,
            "chapter": self.chapter,
            "institution": self.institution,
            "conference": self.conference,
            "notes": self.notes,
            "tags": self.tags
        }


class CitationManager:
    """
    Manages citations and references for academic/technical content.
    
    Supports multiple citation styles and provides automatic formatting
    for in-text citations and bibliographies.
    """
    
    def __init__(self, style: str = "apa"):
        """
        Initialize the citation manager.
        
        Args:
            style: Default citation style to use
        """
        self.style = CitationStyle(style.lower())
        self.references: Dict[str, Reference] = {}
        self._citation_counter = 0
    
    def add_reference(self, reference: Reference) -> str:
        """
        Add a reference to the manager.
        
        Args:
            reference: Reference object to add
        
        Returns:
            The reference ID
        """
        self.references[reference.reference_id] = reference
        return reference.reference_id
    
    def create_reference(
        self,
        reference_type: str,
        title: str,
        authors: List[Dict[str, str]],
        year: int,
        **kwargs
    ) -> Reference:
        """
        Create and add a new reference.
        
        Args:
            reference_type: Type of reference (book, article, etc.)
            title: Title of the work
            authors: List of author dictionaries
            year: Publication year
            **kwargs: Additional reference fields
        
        Returns:
            The created Reference object
        """
        # Generate reference ID
        ref_id = kwargs.pop("reference_id", None)
        if not ref_id:
            ref_id = f"ref_{len(self.references) + 1}"
        
        # Parse authors
        author_objects = []
        for author_dict in authors:
            author_objects.append(Author(
                first_name=author_dict.get("first_name", ""),
                last_name=author_dict.get("last_name", ""),
                middle_name=author_dict.get("middle_name"),
                suffix=author_dict.get("suffix")
            ))
        
        reference = Reference(
            reference_id=ref_id,
            reference_type=reference_type,
            title=title,
            authors=author_objects,
            year=year,
            **kwargs
        )
        
        self.add_reference(reference)
        return reference
    
    def get_reference(self, reference_id: str) -> Optional[Reference]:
        """Get a reference by ID."""
        return self.references.get(reference_id)
    
    def format_citation(
        self,
        reference_id: str,
        citation_type: str = "parenthetical",
        page: Optional[str] = None
    ) -> str:
        """
        Format an in-text citation.
        
        Args:
            reference_id: ID of the reference to cite
            citation_type: Type of citation (parenthetical, narrative, footnote)
            page: Optional page number
        
        Returns:
            Formatted citation string
        """
        ref = self.references.get(reference_id)
        if not ref:
            return f"[Reference {reference_id} not found]"
        
        if self.style == CitationStyle.APA:
            return self._format_apa_citation(ref, citation_type, page)
        elif self.style == CitationStyle.MLA:
            return self._format_mla_citation(ref, citation_type, page)
        elif self.style == CitationStyle.CHICAGO:
            return self._format_chicago_citation(ref, citation_type, page)
        elif self.style == CitationStyle.IEEE:
            return self._format_ieee_citation(ref, citation_type, page)
        elif self.style == CitationStyle.HARVARD:
            return self._format_harvard_citation(ref, citation_type, page)
        else:
            return self._format_apa_citation(ref, citation_type, page)
    
    def _format_apa_citation(
        self,
        ref: Reference,
        citation_type: str,
        page: Optional[str]
    ) -> str:
        """Format APA in-text citation."""
        if len(ref.authors) <= 2:
            names = " & ".join(a.last_name for a in ref.authors)
        else:
            names = f"{ref.authors[0].last_name} et al."
        
        if citation_type == "narrative":
            if page:
                return f"{names} ({ref.year}, p. {page})"
            return f"{names} ({ref.year})"
        else:  # parenthetical
            if page:
                return f"({names}, {ref.year}, p. {page})"
            return f"({names}, {ref.year})"
    
    def _format_mla_citation(
        self,
        ref: Reference,
        citation_type: str,
        page: Optional[str]
    ) -> str:
        """Format MLA in-text citation."""
        name = ref.authors[0].last_name if ref.authors else "Unknown"
        
        if page:
            return f"({name} {page})"
        return f"({name})"
    
    def _format_chicago_citation(
        self,
        ref: Reference,
        citation_type: str,
        page: Optional[str]
    ) -> str:
        """Format Chicago in-text citation."""
        if citation_type == "footnote":
            # Footnote format
            name = ref.authors[0].format_chicago() if ref.authors else "Unknown"
            if page:
                return f"{name}, *{ref.title}* ({ref.year}), {page}."
            return f"{name}, *{ref.title}* ({ref.year})."
        
        # Author-date format
        name = ref.authors[0].last_name if ref.authors else "Unknown"
        if page:
            return f"({name} {ref.year}, {page})"
        return f"({name} {ref.year})"
    
    def _format_ieee_citation(
        self,
        ref: Reference,
        citation_type: str,
        page: Optional[str]
    ) -> str:
        """Format IEEE in-text citation."""
        # IEEE uses numbered citations
        ref_num = list(self.references.keys()).index(ref.reference_id) + 1
        if page:
            return f"[{ref_num}, p. {page}]"
        return f"[{ref_num}]"
    
    def _format_harvard_citation(
        self,
        ref: Reference,
        citation_type: str,
        page: Optional[str]
    ) -> str:
        """Format Harvard in-text citation."""
        if len(ref.authors) <= 3:
            names = " and ".join(a.last_name for a in ref.authors)
        else:
            names = f"{ref.authors[0].last_name} et al."
        
        if citation_type == "narrative":
            if page:
                return f"{names} ({ref.year}, p. {page})"
            return f"{names} ({ref.year})"
        else:
            if page:
                return f"({names} {ref.year}, p. {page})"
            return f"({names} {ref.year})"
    
    def format_bibliography(
        self,
        sort_by: str = "author"
    ) -> str:
        """
        Format the complete bibliography.
        
        Args:
            sort_by: How to sort entries (author, year, appearance)
        
        Returns:
            Formatted bibliography string
        """
        refs = list(self.references.values())
        
        if sort_by == "author":
            refs.sort(key=lambda r: r.authors[0].last_name if r.authors else "")
        elif sort_by == "year":
            refs.sort(key=lambda r: r.year)
        # appearance order is default (already sorted)
        
        entries = []
        for ref in refs:
            entries.append(ref.format_bibliography_entry(self.style))
        
        return "\n\n".join(entries)
    
    def format_reference_list(self) -> List[Dict[str, str]]:
        """
        Get formatted reference list as dictionaries.
        
        Returns:
            List of reference dictionaries with formatted entries
        """
        result = []
        for ref_id, ref in self.references.items():
            result.append({
                "id": ref_id,
                "formatted": ref.format_bibliography_entry(self.style),
                "type": ref.reference_type,
                "year": ref.year
            })
        return result
    
    def export_bibtex(self) -> str:
        """
        Export references in BibTeX format.
        
        Returns:
            BibTeX formatted string
        """
        entries = []
        for ref in self.references.values():
            entry_type = ref.reference_type
            if entry_type == "article":
                entry_type = "article"
            elif entry_type == "book":
                entry_type = "book"
            elif entry_type == "website":
                entry_type = "misc"
            else:
                entry_type = "misc"
            
            # Generate citation key
            key = f"{ref.authors[0].last_name if ref.authors else 'Unknown'}{ref.year}"
            
            fields = [f'  title = "{{{ref.title}}}"]
            fields.append(f'  year = "{{{ref.year}}}"')
            
            if ref.authors:
                author_str = " and ".join(
                    f"{a.first_name} {a.last_name}" for a in ref.authors
                )
                fields.append(f'  author = "{{{author_str}}}"')
            
            if ref.publisher:
                fields.append(f'  publisher = "{{{ref.publisher}}}"')
            if ref.journal:
                fields.append(f'  journal = "{{{ref.journal}}}"')
            if ref.volume:
                fields.append(f'  volume = "{{{ref.volume}}}"')
            if ref.pages:
                fields.append(f'  pages = "{{{ref.pages}}}"')
            if ref.doi:
                fields.append(f'  doi = "{{{ref.doi}}}"')
            if ref.url:
                fields.append(f'  url = "{{{ref.url}}}"')
            
            entries.append(f"@{entry_type}{{{key},\n" + ",\n".join(fields) + "\n}")
        
        return "\n\n".join(entries)
    
    def set_style(self, style: str) -> None:
        """Set the citation style."""
        self.style = CitationStyle(style.lower())
    
    def clear(self) -> None:
        """Clear all references."""
        self.references.clear()
    
    def to_dict(self) -> dict:
        """Convert manager state to dictionary."""
        return {
            "style": self.style.value,
            "references": {k: v.to_dict() for k, v in self.references.items()}
        }


__all__ = [
    "CitationStyle",
    "Author",
    "Reference",
    "CitationManager",
]