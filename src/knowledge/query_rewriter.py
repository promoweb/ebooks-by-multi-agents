"""
Query Rewriter for Knowledge Base System.

This module provides query rewriting capabilities to improve
retrieval effectiveness through query expansion and transformation.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


logger = logging.getLogger("BookWriterAI")


class RewriteStrategy(Enum):
    """Strategy for query rewriting."""
    EXPANSION = "expansion"  # Add related terms
    DECOMPOSITION = "decomposition"  # Break into sub-queries
    PARAPHRASE = "paraphrase"  # Rephrase query
    HYDE = "hyde"  # Hypothetical document embeddings


@dataclass
class RewrittenQuery:
    """Represents a rewritten query."""
    original: str
    rewritten: str
    strategy: RewriteStrategy
    variations: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class QueryRewriter:
    """
    Rewrites queries for better retrieval.
    
    Supports multiple strategies:
    - Expansion: Add synonyms and related terms
    - Decomposition: Break complex queries into sub-queries
    - Paraphrase: Rephrase for different perspectives
    - HyDE: Generate hypothetical document for embedding
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize query rewriter.
        
        Args:
            llm_client: LLM client for advanced rewriting (optional)
        """
        self.llm_client = llm_client
        
        # Common synonyms for book-related queries
        self.synonyms = {
            "character": ["person", "protagonist", "figure", "character"],
            "plot": ["storyline", "narrative", "events", "plot"],
            "setting": ["location", "place", "world", "setting"],
            "theme": ["topic", "subject", "message", "theme"],
            "conflict": ["problem", "struggle", "tension", "conflict"],
            "ending": ["conclusion", "finale", "resolution", "ending"],
            "beginning": ["start", "opening", "introduction", "beginning"],
        }
        
        # Query patterns for decomposition
        self.decomposition_patterns = [
            (r"how does (.+) (feel|think|react) about (.+)", 
             ["{1} emotions towards {2}", "{1} thoughts about {2}", "{1} reaction to {2}"]),
            (r"what happened (to|with) (.+) in (.+)",
             ["events involving {1} in {2}", "{1} story arc in {2}", "{1} experiences in {2}"]),
            (r"why did (.+) (.+)",
             ["reasons for {1} {2}", "{1} motivation to {2}", "causes of {1} {2}"]),
        ]
    
    def rewrite_for_retrieval(
        self,
        original_query: str,
        context: Optional[Dict[str, Any]] = None,
        strategies: Optional[List[RewriteStrategy]] = None
    ) -> RewrittenQuery:
        """
        Generate multiple query variations for better retrieval.
        
        Args:
            original_query: The original search query
            context: Optional narrative context
            strategies: Strategies to use (default: all)
        
        Returns:
            RewrittenQuery with variations
        
        Example:
            Original: "What happened to John?"
            Rewritten:
            - "John character arc events"
            - "John major plot points"
            - "John relationships changes"
            - "John emotional journey"
        """
        strategies = strategies or list(RewriteStrategy)
        context = context or {}
        
        variations = []
        
        for strategy in strategies:
            if strategy == RewriteStrategy.EXPANSION:
                expanded = self._expand_query(original_query, context)
                variations.extend(expanded)
            
            elif strategy == RewriteStrategy.DECOMPOSITION:
                decomposed = self._decompose_query(original_query)
                variations.extend(decomposed)
            
            elif strategy == RewriteStrategy.PARAPHRASE:
                paraphrased = self._paraphrase_query(original_query, context)
                variations.extend(paraphrased)
            
            elif strategy == RewriteStrategy.HYDE:
                hyde = self._generate_hyde(original_query, context)
                if hyde:
                    variations.append(hyde)
        
        # Remove duplicates while preserving order
        unique_variations = []
        seen = set()
        for v in variations:
            normalized = v.lower().strip()
            if normalized not in seen and normalized != original_query.lower().strip():
                seen.add(normalized)
                unique_variations.append(v)
        
        return RewrittenQuery(
            original=original_query,
            rewritten=original_query,  # Keep original as primary
            strategy=strategies[0] if strategies else RewriteStrategy.EXPANSION,
            variations=unique_variations,
            metadata={
                "strategies_used": [s.value for s in strategies],
                "variation_count": len(unique_variations)
            }
        )
    
    def _expand_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Expand query with synonyms and related terms."""
        expanded = []
        words = query.lower().split()
        
        # Add synonym expansions
        for word in words:
            if word in self.synonyms:
                for synonym in self.synonyms[word]:
                    if synonym != word:
                        expanded_query = query.lower().replace(word, synonym)
                        expanded.append(expanded_query)
        
        # Add context-based expansions
        if context:
            # Add character names if mentioned
            characters = context.get("characters", [])
            for char in characters:
                if char.lower() in query.lower():
                    expanded.append(f"{char} character arc")
                    expanded.append(f"{char} story development")
                    expanded.append(f"{char} relationships")
        
        return expanded
    
    def _decompose_query(
        self,
        query: str
    ) -> List[str]:
        """Decompose complex queries into sub-queries."""
        decomposed = []
        query_lower = query.lower()
        
        for pattern, templates in self.decomposition_patterns:
            match = re.match(pattern, query_lower)
            if match:
                groups = match.groups()
                for template in templates:
                    try:
                        sub_query = template.format(*groups)
                        decomposed.append(sub_query)
                    except (IndexError, KeyError):
                        continue
        
        # Generic decomposition for "what" questions
        if query_lower.startswith("what"):
            # Extract key terms
            terms = re.findall(r'\b[a-z]{3,}\b', query_lower)
            terms = [t for t in terms if t not in ['what', 'the', 'was', 'were', 'did', 'does']]
            
            if terms:
                decomposed.append(f"{' '.join(terms)} events")
                decomposed.append(f"{' '.join(terms)} details")
                decomposed.append(f"{' '.join(terms)} description")
        
        # Generic decomposition for "how" questions
        elif query_lower.startswith("how"):
            terms = re.findall(r'\b[a-z]{3,}\b', query_lower)
            terms = [t for t in terms if t not in ['how', 'the', 'was', 'were', 'did', 'does']]
            
            if terms:
                decomposed.append(f"{' '.join(terms)} process")
                decomposed.append(f"{' '.join(terms)} explanation")
        
        return decomposed
    
    def _paraphrase_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Paraphrase query for different perspectives."""
        paraphrased = []
        query_lower = query.lower()
        
        # Question transformations
        transformations = {
            r"^who is (.+)\?$": ["{0} character profile", "{0} description", "{0} introduction"],
            r"^what is (.+)\?$": ["{0} definition", "{0} explanation", "{0} overview"],
            r"^where (.+)\?$": ["{0} location", "{0} setting", "{0} place"],
            r"^when (.+)\?$": ["{0} timeline", "{0} chronology", "{0} timing"],
            r"^why (.+)\?$": ["{0} reasons", "{0} motivation", "{0} causes"],
        }
        
        for pattern, templates in transformations.items():
            match = re.match(pattern, query_lower)
            if match:
                groups = match.groups()
                for template in templates:
                    try:
                        paraphrased.append(template.format(*groups))
                    except (IndexError, KeyError):
                        continue
        
        # Add perspective variations
        if "character" in query_lower or "protagonist" in query_lower:
            paraphrased.append(query.replace("character", "person"))
            paraphrased.append(query.replace("character", "figure"))
        
        return paraphrased
    
    def _generate_hyde(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Generate hypothetical document for HyDE retrieval.
        
        HyDE (Hypothetical Document Embeddings) generates a
        hypothetical document that would answer the query,
        then uses that for retrieval.
        """
        if not self.llm_client:
            # Simple fallback without LLM
            return self._simple_hyde(query)
        
        try:
            prompt = f"""Generate a brief hypothetical document passage that would answer this question:

Question: {query}

Generate a 2-3 sentence passage that could be from a book and would answer this question:"""
            
            response = self.llm_client.generate(prompt, max_tokens=150)
            return response.strip()
        
        except Exception as e:
            logger.warning(f"HyDE generation failed: {e}")
            return self._simple_hyde(query)
    
    def _simple_hyde(self, query: str) -> str:
        """Simple HyDE fallback without LLM."""
        # Create a hypothetical document structure
        query_lower = query.lower()
        
        if "who" in query_lower:
            return f"The character in question plays a significant role in the narrative. Their actions and decisions drive the plot forward."
        elif "what" in query_lower:
            return f"This is an important element of the story. It contributes to the overall narrative arc and character development."
        elif "where" in query_lower:
            return f"The location serves as an important setting in the narrative. It provides context for the events that unfold."
        elif "when" in query_lower:
            return f"This timing is significant in the narrative timeline. It marks an important point in the story's progression."
        else:
            return f"This relates to key elements of the narrative. The details contribute to the overall story structure."
    
    def rewrite_for_chapter(
        self,
        chapter_info: Dict[str, Any],
        narrative_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate retrieval queries for chapter generation.
        
        Args:
            chapter_info: Information about the chapter
            narrative_context: Current narrative state
        
        Returns:
            List of queries for retrieving relevant context
        """
        queries = []
        
        # Query from chapter title/summary
        if "title" in chapter_info:
            queries.append(chapter_info["title"])
        
        if "summary" in chapter_info:
            queries.append(chapter_info["summary"])
        
        # Query from characters
        if "characters" in chapter_info:
            for char in chapter_info["characters"]:
                queries.append(f"{char} character state")
                queries.append(f"{char} recent actions")
        
        # Query from plot points
        if "plot_points" in chapter_info:
            for point in chapter_info["plot_points"]:
                queries.append(point)
        
        # Query from narrative context
        if narrative_context:
            # Unresolved threads
            unresolved = narrative_context.get("unresolved_threads", [])
            for thread in unresolved[:3]:
                queries.append(thread)
            
            # Recent events
            recent = narrative_context.get("recent_events", [])
            for event in recent[:3]:
                queries.append(event)
        
        return queries


__all__ = [
    "RewriteStrategy",
    "RewrittenQuery",
    "QueryRewriter",
]