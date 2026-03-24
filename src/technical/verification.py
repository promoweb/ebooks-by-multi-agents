"""
Fact Verification and Technical Accuracy System for BookWriterAI.

This module provides fact verification, claim extraction, and technical
accuracy checking for academic and technical content.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod


logger = logging.getLogger("BookWriterAI")


class ClaimType(Enum):
    """Types of factual claims."""
    STATISTICAL = "statistical"
    HISTORICAL = "historical"
    SCIENTIFIC = "scientific"
    DEFINITION = "definition"
    QUOTE = "quote"
    DATE = "date"
    NAME = "name"
    LOCATION = "location"
    GENERAL = "general"


class VerificationStatus(Enum):
    """Status of claim verification."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass
class FactualClaim:
    """Represents a factual claim extracted from content."""
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    location: str  # Position in text
    context: str  # Surrounding text
    confidence: float = 1.0
    entities: List[str] = field(default_factory=list)
    numbers: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type.value,
            "location": self.location,
            "context": self.context,
            "confidence": self.confidence,
            "entities": self.entities,
            "numbers": self.numbers,
            "dates": self.dates
        }


@dataclass
class VerificationResult:
    """Result of verifying a claim."""
    claim_id: str
    status: VerificationStatus
    confidence: float
    supporting_sources: List[str] = field(default_factory=list)
    contradicting_sources: List[str] = field(default_factory=list)
    suggested_correction: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "claim_id": self.claim_id,
            "status": self.status.value,
            "confidence": self.confidence,
            "supporting_sources": self.supporting_sources,
            "contradicting_sources": self.contradicting_sources,
            "suggested_correction": self.suggested_correction,
            "notes": self.notes
        }


@dataclass
class ContentVerificationReport:
    """Report on verification of all claims in content."""
    total_claims: int
    verified_claims: int
    unverified_claims: int
    disputed_claims: int
    contradicted_claims: int
    overall_accuracy: float
    claims: List[VerificationResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_claims": self.total_claims,
            "verified_claims": self.verified_claims,
            "unverified_claims": self.unverified_claims,
            "disputed_claims": self.disputed_claims,
            "contradicted_claims": self.contradicted_claims,
            "overall_accuracy": self.overall_accuracy,
            "claims": [c.to_dict() for c in self.claims],
            "recommendations": self.recommendations
        }


class ClaimExtractor:
    """Extracts factual claims from text content."""
    
    # Patterns for claim detection
    STATISTICAL_PATTERNS = [
        r'\d+(?:\.\d+)?%',  # Percentages
        r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|trillion)',  # Large numbers
        r'(?:approximately|about|around|nearly|over)\s+\d+',  # Approximate numbers
    ]
    
    DATE_PATTERNS = [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b(?:in|during|since)\s+\d{4}\b',
    ]
    
    CLAIM_INDICATORS = [
        "according to",
        "research shows",
        "studies indicate",
        "data suggests",
        "experts say",
        "it is estimated",
        "statistics show",
        "evidence indicates",
        "scientists have found",
        "historians believe",
    ]
    
    def __init__(self):
        """Initialize the claim extractor."""
        self._claim_counter = 0
    
    def extract_claims(self, content: str) -> List[FactualClaim]:
        """
        Extract factual claims from content.
        
        Args:
            content: Text content to analyze
        
        Returns:
            List of extracted FactualClaim objects
        """
        claims = []
        sentences = self._split_into_sentences(content)
        
        for i, sentence in enumerate(sentences):
            claim_type = self._classify_claim(sentence)
            if claim_type:
                claim = self._create_claim(sentence, i, claim_type, content)
                if claim:
                    claims.append(claim)
        
        return claims
    
    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def _classify_claim(self, sentence: str) -> Optional[ClaimType]:
        """Determine if sentence contains a factual claim."""
        sentence_lower = sentence.lower()
        
        # Check for statistical claims
        for pattern in self.STATISTICAL_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                return ClaimType.STATISTICAL
        
        # Check for date claims
        for pattern in self.DATE_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                return ClaimType.DATE
        
        # Check for claim indicators
        for indicator in self.CLAIM_INDICATORS:
            if indicator in sentence_lower:
                if "histor" in sentence_lower:
                    return ClaimType.HISTORICAL
                elif "scient" in sentence_lower or "research" in sentence_lower:
                    return ClaimType.SCIENTIFIC
                return ClaimType.GENERAL
        
        return None
    
    def _create_claim(
        self,
        sentence: str,
        index: int,
        claim_type: ClaimType,
        full_content: str
    ) -> Optional[FactualClaim]:
        """Create a FactualClaim from a sentence."""
        self._claim_counter += 1
        
        # Extract entities (capitalized words)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence)
        
        # Extract numbers
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?(?:%)?', sentence)
        
        # Extract dates
        dates = []
        for pattern in self.DATE_PATTERNS:
            dates.extend(re.findall(pattern, sentence, re.IGNORECASE))
        
        return FactualClaim(
            claim_id=f"claim_{self._claim_counter}",
            claim_text=sentence,
            claim_type=claim_type,
            location=f"sentence_{index}",
            context=self._get_context(sentence, full_content),
            entities=entities,
            numbers=numbers,
            dates=dates
        )
    
    def _get_context(self, sentence: str, full_content: str) -> str:
        """Get surrounding context for a sentence."""
        # Find position and get surrounding text
        pos = full_content.find(sentence)
        if pos == -1:
            return sentence
        
        start = max(0, pos - 100)
        end = min(len(full_content), pos + len(sentence) + 100)
        return full_content[start:end]


class KnowledgeBase(ABC):
    """Abstract base class for knowledge bases."""
    
    @abstractmethod
    def verify_claim(self, claim: FactualClaim) -> VerificationResult:
        """Verify a claim against the knowledge base."""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        pass


class MockKnowledgeBase(KnowledgeBase):
    """
    Mock knowledge base for testing.
    In production, this would connect to actual knowledge sources.
    """
    
    def __init__(self):
        """Initialize mock knowledge base with sample data."""
        self.facts = {
            "earth_planets": "Earth is the third planet from the Sun.",
            "water_composition": "Water is composed of hydrogen and oxygen (H2O).",
            "pi_value": "Pi is approximately 3.14159.",
            "world_war_2_end": "World War II ended in 1945.",
            "moon_landing": "The first Moon landing was in 1969.",
        }
    
    def verify_claim(self, claim: FactualClaim) -> VerificationResult:
        """Verify a claim (mock implementation)."""
        # This is a mock - in production would use actual verification
        claim_lower = claim.claim_text.lower()
        
        # Simple keyword matching for demonstration
        for key, fact in self.facts.items():
            if any(word in claim_lower for word in fact.lower().split()[:3]):
                return VerificationResult(
                    claim_id=claim.claim_id,
                    status=VerificationStatus.VERIFIED,
                    confidence=0.8,
                    supporting_sources=[f"Knowledge base: {key}"],
                    notes="Matched known fact"
                )
        
        # Default to unverified
        return VerificationResult(
            claim_id=claim.claim_id,
            status=VerificationStatus.UNVERIFIED,
            confidence=0.5,
            notes="Could not verify against knowledge base"
        )
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        results = []
        query_lower = query.lower()
        
        for key, fact in self.facts.items():
            if query_lower in fact.lower():
                results.append({
                    "key": key,
                    "fact": fact,
                    "relevance": 0.8
                })
        
        return results


class FactVerificationSystem:
    """
    Verifies factual claims in content.
    
    Uses knowledge bases and external sources to verify
    the accuracy of claims made in generated content.
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        verification_threshold: float = 0.8
    ):
        """
        Initialize the fact verification system.
        
        Args:
            knowledge_base: Knowledge base to use for verification
            verification_threshold: Confidence threshold for verification
        """
        self.knowledge_base = knowledge_base or MockKnowledgeBase()
        self.verification_threshold = verification_threshold
        self.extractor = ClaimExtractor()
    
    def extract_claims(self, content: str) -> List[FactualClaim]:
        """
        Extract factual claims from content.
        
        Args:
            content: Text content to analyze
        
        Returns:
            List of extracted claims
        """
        return self.extractor.extract_claims(content)
    
    def verify_claim(self, claim: FactualClaim) -> VerificationResult:
        """
        Verify a single claim.
        
        Args:
            claim: Claim to verify
        
        Returns:
            VerificationResult with verification status
        """
        return self.knowledge_base.verify_claim(claim)
    
    def verify_content(self, content: str) -> ContentVerificationReport:
        """
        Verify all claims in content.
        
        Args:
            content: Text content to verify
        
        Returns:
            ContentVerificationReport with all verification results
        """
        claims = self.extract_claims(content)
        results = []
        
        verified = 0
        unverified = 0
        disputed = 0
        contradicted = 0
        
        for claim in claims:
            result = self.verify_claim(claim)
            results.append(result)
            
            if result.status == VerificationStatus.VERIFIED:
                verified += 1
            elif result.status == VerificationStatus.UNVERIFIED:
                unverified += 1
            elif result.status == VerificationStatus.DISPUTED:
                disputed += 1
            elif result.status == VerificationStatus.CONTRADICTED:
                contradicted += 1
        
        total = len(claims)
        accuracy = verified / total if total > 0 else 1.0
        
        recommendations = self._generate_recommendations(results)
        
        return ContentVerificationReport(
            total_claims=total,
            verified_claims=verified,
            unverified_claims=unverified,
            disputed_claims=disputed,
            contradicted_claims=contradicted,
            overall_accuracy=accuracy,
            claims=results,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        results: List[VerificationResult]
    ) -> List[str]:
        """Generate recommendations based on verification results."""
        recommendations = []
        
        contradicted = [r for r in results if r.status == VerificationStatus.CONTRADICTED]
        if contradicted:
            recommendations.append(
                f"Review {len(contradicted)} contradicted claim(s) for accuracy"
            )
        
        disputed = [r for r in results if r.status == VerificationStatus.DISPUTED]
        if disputed:
            recommendations.append(
                f"Verify {len(disputed)} disputed claim(s) with additional sources"
            )
        
        unverified = [r for r in results if r.status == VerificationStatus.UNVERIFIED]
        if len(unverified) > len(results) * 0.3:
            recommendations.append(
                "Consider adding more citations for unverified claims"
            )
        
        return recommendations


@dataclass
class TechnicalIssue:
    """Represents a technical accuracy issue."""
    issue_id: str
    issue_type: str
    severity: str  # low, medium, high, critical
    location: str
    description: str
    suggested_fix: Optional[str] = None
    reference: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "location": self.location,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "reference": self.reference
        }


@dataclass
class TechnicalAccuracyReport:
    """Report on technical accuracy of content."""
    overall_score: float
    issues: List[TechnicalIssue]
    domain: str
    technical_level: str
    checked_elements: List[str]
    passed_checks: int
    failed_checks: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "issues": [i.to_dict() for i in self.issues],
            "domain": self.domain,
            "technical_level": self.technical_level,
            "checked_elements": self.checked_elements,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks
        }


class TechnicalAccuracyChecker:
    """
    Checks technical accuracy of content.
    
    Validates terminology, concepts, and technical correctness
    for specific domains.
    """
    
    # Domain-specific terminology databases
    TERMINOLOGY = {
        "computer_science": {
            "algorithm": "A step-by-step procedure for solving a problem",
            "data_structure": "A way of organizing and storing data",
            "api": "Application Programming Interface",
            "database": "An organized collection of structured information",
            "machine_learning": "A subset of AI that enables systems to learn from data",
        },
        "physics": {
            "velocity": "Rate of change of position with respect to time",
            "acceleration": "Rate of change of velocity with respect to time",
            "force": "An interaction that changes the motion of an object",
            "energy": "The capacity to do work",
            "momentum": "Product of mass and velocity",
        },
        "biology": {
            "cell": "The basic structural and functional unit of life",
            "dna": "Deoxyribonucleic acid, the genetic material",
            "protein": "A biomolecule composed of amino acids",
            "enzyme": "A protein that catalyzes biochemical reactions",
            "genome": "The complete set of genetic material in an organism",
        }
    }
    
    # Common technical errors to check
    COMMON_ERRORS = {
        "computer_science": [
            ("Java and JavaScript are the same", "Java and JavaScript are different languages"),
            ("HTTP is secure", "HTTP is not secure; HTTPS is the secure version"),
            ("RAM stores data permanently", "RAM is volatile and loses data when powered off"),
        ],
        "physics": [
            ("Heavier objects fall faster", "In vacuum, all objects fall at the same rate"),
            ("Energy can be created", "Energy is conserved and cannot be created or destroyed"),
            ("Velocity and speed are the same", "Velocity is a vector; speed is a scalar"),
        ],
        "biology": [
            ("Humans evolved from monkeys", "Humans and monkeys share a common ancestor"),
            ("DNA is found only in the nucleus", "DNA is also found in mitochondria"),
            ("All bacteria are harmful", "Many bacteria are beneficial or neutral"),
        ]
    }
    
    def __init__(self):
        """Initialize the technical accuracy checker."""
        self._issue_counter = 0
    
    def check(
        self,
        content: str,
        domain: str,
        technical_level: str = "intermediate"
    ) -> TechnicalAccuracyReport:
        """
        Check technical accuracy of content.
        
        Args:
            content: Text content to check
            domain: Technical domain (computer_science, physics, biology, etc.)
            technical_level: Level of technical depth (introductory, intermediate, advanced, expert)
        
        Returns:
            TechnicalAccuracyReport with findings
        """
        issues = []
        checked_elements = []
        passed = 0
        failed = 0
        
        # Get domain-specific data
        terminology = self.TERMINOLOGY.get(domain, {})
        common_errors = self.COMMON_ERRORS.get(domain, [])
        
        # Check terminology usage
        term_issues, term_passed, term_failed = self._check_terminology(
            content, terminology, technical_level
        )
        issues.extend(term_issues)
        passed += term_passed
        failed += term_failed
        checked_elements.append("terminology")
        
        # Check for common errors
        error_issues, error_passed, error_failed = self._check_common_errors(
            content, common_errors
        )
        issues.extend(error_issues)
        passed += error_passed
        failed += error_failed
        checked_elements.append("common_errors")
        
        # Check code snippets if applicable
        if domain == "computer_science":
            code_issues, code_passed, code_failed = self._check_code_snippets(content)
            issues.extend(code_issues)
            passed += code_passed
            failed += code_failed
            checked_elements.append("code_snippets")
        
        # Calculate overall score
        total = passed + failed
        score = passed / total if total > 0 else 1.0
        
        return TechnicalAccuracyReport(
            overall_score=score,
            issues=issues,
            domain=domain,
            technical_level=technical_level,
            checked_elements=checked_elements,
            passed_checks=passed,
            failed_checks=failed
        )
    
    def _check_terminology(
        self,
        content: str,
        terminology: Dict[str, str],
        level: str
    ) -> Tuple[List[TechnicalIssue], int, int]:
        """Check terminology usage."""
        issues = []
        passed = 0
        failed = 0
        
        content_lower = content.lower()
        
        for term, definition in terminology.items():
            if term.lower() in content_lower:
                # Term is used - check if defined for introductory level
                if level == "introductory":
                    # Check if term is defined nearby
                    term_pos = content_lower.find(term.lower())
                    context = content[max(0, term_pos - 100):term_pos + 200]
                    
                    # Simple check for definition patterns
                    if not any(pattern in context.lower() for pattern in 
                              ["is a", "refers to", "means", "defined as", "known as"]):
                        self._issue_counter += 1
                        issues.append(TechnicalIssue(
                            issue_id=f"tech_{self._issue_counter}",
                            issue_type="undefined_term",
                            severity="low",
                            location=f"term: {term}",
                            description=f"Technical term '{term}' used without definition",
                            suggested_fix=f"Consider adding definition: '{term} is {definition}'",
                            reference=definition
                        ))
                        failed += 1
                    else:
                        passed += 1
                else:
                    passed += 1
        
        return issues, passed, failed
    
    def _check_common_errors(
        self,
        content: str,
        common_errors: List[Tuple[str, str]]
    ) -> Tuple[List[TechnicalIssue], int, int]:
        """Check for common technical errors."""
        issues = []
        passed = 0
        failed = 0
        
        content_lower = content.lower()
        
        for error, correction in common_errors:
            if error.lower() in content_lower:
                self._issue_counter += 1
                issues.append(TechnicalIssue(
                    issue_id=f"tech_{self._issue_counter}",
                    issue_type="common_error",
                    severity="high",
                    location=f"error: {error}",
                    description=f"Potential technical error: '{error}'",
                    suggested_fix=correction
                ))
                failed += 1
            else:
                passed += 1
        
        return issues, passed, failed
    
    def _check_code_snippets(
        self,
        content: str
    ) -> Tuple[List[TechnicalIssue], int, int]:
        """Check code snippets for basic validity."""
        issues = []
        passed = 0
        failed = 0
        
        # Find code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
        
        for i, code in enumerate(code_blocks):
            # Basic syntax checks
            if code.strip():
                # Check for balanced brackets
                open_brackets = code.count('{') + code.count('[') + code.count('(')
                close_brackets = code.count('}') + code.count(']') + code.count(')')
                
                if open_brackets != close_brackets:
                    self._issue_counter += 1
                    issues.append(TechnicalIssue(
                        issue_id=f"tech_{self._issue_counter}",
                        issue_type="code_syntax",
                        severity="medium",
                        location=f"code block {i + 1}",
                        description="Unbalanced brackets in code snippet",
                        suggested_fix="Check bracket matching"
                    ))
                    failed += 1
                else:
                    passed += 1
        
        return issues, passed, failed


__all__ = [
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
]