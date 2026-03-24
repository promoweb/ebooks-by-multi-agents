"""
Custom exceptions for BookWriterAI.

This module defines a hierarchy of exceptions for handling various error
conditions throughout the book generation process.
"""

from typing import Optional, List, Any


class BookWriterError(Exception):
    """Base exception for all BookWriterAI errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(BookWriterError):
    """Raised when there's an issue with configuration."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is not found."""
    
    def __init__(self, provider: str, env_var: str):
        super().__init__(
            f"API key not found for provider '{provider}'. "
            f"Set the environment variable '{env_var}'.",
            {"provider": provider, "env_var": env_var}
        )


class InvalidProviderError(ConfigurationError):
    """Raised when an invalid provider is specified."""
    
    def __init__(self, provider: str, valid_providers: List[str]):
        super().__init__(
            f"Invalid provider '{provider}'. Valid providers: {valid_providers}",
            {"provider": provider, "valid_providers": valid_providers}
        )


# =============================================================================
# LLM Errors
# =============================================================================

class LLMError(BookWriterError):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM API fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, {"retry_after": retry_after})


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or unexpected."""
    pass


class TokenBudgetExceededError(LLMError):
    """Raised when token budget is exceeded during generation."""
    
    def __init__(self, used_tokens: int, max_tokens: int, context: str = ""):
        super().__init__(
            f"Token budget exceeded: {used_tokens} > {max_tokens}",
            {"used_tokens": used_tokens, "max_tokens": max_tokens, "context": context}
        )


# =============================================================================
# Content Errors
# =============================================================================

class ContentError(BookWriterError):
    """Base exception for content-related errors."""
    pass


class ContentValidationError(ContentError):
    """Raised when content validation fails."""
    
    def __init__(self, message: str, word_count: int, target_words: int, 
                 density_ratio: float):
        super().__init__(
            message,
            {
                "word_count": word_count,
                "target_words": target_words,
                "density_ratio": density_ratio
            }
        )


class ContentTooShortError(ContentValidationError):
    """Raised when generated content is below minimum threshold."""
    pass


class ContentTooLongError(ContentValidationError):
    """Raised when generated content exceeds maximum threshold."""
    pass


class QualityThresholdError(ContentError):
    """Raised when content quality is below acceptable threshold."""
    
    def __init__(self, quality_score: float, threshold: float, issues: List[str]):
        super().__init__(
            f"Quality score {quality_score:.2f} below threshold {threshold:.2f}",
            {"quality_score": quality_score, "threshold": threshold, "issues": issues}
        )


# =============================================================================
# Narrative Errors
# =============================================================================

class NarrativeError(BookWriterError):
    """Base exception for narrative-related errors."""
    pass


class NarrativeConsistencyError(NarrativeError):
    """Raised when narrative consistency check fails."""
    
    def __init__(self, entity_id: str, inconsistency_type: str, details: str):
        super().__init__(
            f"Narrative consistency error for entity '{entity_id}': {inconsistency_type}",
            {"entity_id": entity_id, "inconsistency_type": inconsistency_type, "details": details}
        )


class EntityNotFoundError(NarrativeError):
    """Raised when referenced entity is not found in registry."""
    
    def __init__(self, entity_id: str):
        super().__init__(
            f"Entity not found: '{entity_id}'",
            {"entity_id": entity_id}
        )


class EventConflictError(NarrativeError):
    """Raised when events have conflicting information."""
    
    def __init__(self, event_id_1: str, event_id_2: str, conflict_type: str):
        super().__init__(
            f"Event conflict between '{event_id_1}' and '{event_id_2}': {conflict_type}",
            {"event_id_1": event_id_1, "event_id_2": event_id_2, "conflict_type": conflict_type}
        )


# =============================================================================
# Character Errors
# =============================================================================

class CharacterError(BookWriterError):
    """Base exception for character-related errors."""
    pass


class CharacterConsistencyError(CharacterError):
    """Raised when character behavior is inconsistent with profile."""
    
    def __init__(self, character_id: str, action: str, reason: str):
        super().__init__(
            f"Character '{character_id}' action inconsistent: {reason}",
            {"character_id": character_id, "action": action, "reason": reason}
        )


class CharacterNotFoundError(CharacterError):
    """Raised when character is not found."""
    
    def __init__(self, character_id: str):
        super().__init__(
            f"Character not found: '{character_id}'",
            {"character_id": character_id}
        )


# =============================================================================
# Style Errors
# =============================================================================

class StyleError(BookWriterError):
    """Base exception for style-related errors."""
    pass


class StyleValidationError(StyleError):
    """Raised when style validation fails."""
    
    def __init__(self, metric: str, actual: float, expected: float, tolerance: float):
        super().__init__(
            f"Style validation failed for '{metric}': {actual} vs expected {expected} "
            f"(tolerance: {tolerance})",
            {"metric": metric, "actual": actual, "expected": expected, "tolerance": tolerance}
        )


# =============================================================================
# Knowledge Base Errors
# =============================================================================

class KnowledgeBaseError(BookWriterError):
    """Base exception for knowledge base errors."""
    pass


class DocumentLoadError(KnowledgeBaseError):
    """Raised when document loading fails."""
    
    def __init__(self, file_path: str, reason: str):
        super().__init__(
            f"Failed to load document '{file_path}': {reason}",
            {"file_path": file_path, "reason": reason}
        )


class DocumentParseError(KnowledgeBaseError):
    """Raised when document parsing fails."""
    
    def __init__(self, file_path: str, format: str, reason: str):
        super().__init__(
            f"Failed to parse {format} document '{file_path}': {reason}",
            {"file_path": file_path, "format": format, "reason": reason}
        )


class RetrievalError(KnowledgeBaseError):
    """Raised when context retrieval fails."""
    
    def __init__(self, query: str, reason: str):
        super().__init__(
            f"Retrieval failed for query: {reason}",
            {"query": query, "reason": reason}
        )


# =============================================================================
# Checkpoint Errors
# =============================================================================

class CheckpointError(BookWriterError):
    """Base exception for checkpoint errors."""
    pass


class CheckpointCorruptedError(CheckpointError):
    """Raised when checkpoint data is corrupted."""
    
    def __init__(self, checkpoint_path: str, reason: str):
        super().__init__(
            f"Checkpoint corrupted at '{checkpoint_path}': {reason}",
            {"checkpoint_path": checkpoint_path, "reason": reason}
        )


class CheckpointNotFoundError(CheckpointError):
    """Raised when checkpoint is not found."""
    
    def __init__(self, checkpoint_path: str):
        super().__init__(
            f"Checkpoint not found: '{checkpoint_path}'",
            {"checkpoint_path": checkpoint_path}
        )


# =============================================================================
# Generation Errors
# =============================================================================

class GenerationError(BookWriterError):
    """Base exception for generation errors."""
    pass


class OutlineGenerationError(GenerationError):
    """Raised when outline generation fails."""
    
    def __init__(self, reason: str, partial_outline: Optional[dict] = None):
        super().__init__(
            f"Outline generation failed: {reason}",
            {"reason": reason, "partial_outline": partial_outline}
        )


class ChapterGenerationError(GenerationError):
    """Raised when chapter generation fails."""
    
    def __init__(self, chapter_id: int, chapter_title: str, reason: str):
        super().__init__(
            f"Chapter {chapter_id} '{chapter_title}' generation failed: {reason}",
            {"chapter_id": chapter_id, "chapter_title": chapter_title, "reason": reason}
        )


class BookLengthError(GenerationError):
    """Raised when generated book doesn't meet length requirements."""
    
    def __init__(self, actual_pages: int, target_pages: int, min_pages: int):
        super().__init__(
            f"Book length {actual_pages} pages below minimum {min_pages} "
            f"(target: {target_pages})",
            {"actual_pages": actual_pages, "target_pages": target_pages, "min_pages": min_pages}
        )


# =============================================================================
# Genre Errors
# =============================================================================

class GenreError(BookWriterError):
    """Base exception for genre-related errors."""
    pass


class GenreNotFoundError(GenreError):
    """Raised when genre template is not found."""
    
    def __init__(self, genre: str, available_genres: List[str]):
        super().__init__(
            f"Genre '{genre}' not found. Available: {available_genres}",
            {"genre": genre, "available_genres": available_genres}
        )


class GenreConventionViolationError(GenreError):
    """Raised when content violates genre conventions."""
    
    def __init__(self, genre: str, violation: str, suggestion: str):
        super().__init__(
            f"Genre convention violation for '{genre}': {violation}",
            {"genre": genre, "violation": violation, "suggestion": suggestion}
        )


# =============================================================================
# Utility Functions
# =============================================================================

def wrap_exception(e: Exception, wrapper_class: type, message: str = None) -> BookWriterError:
    """
    Wrap a generic exception in a BookWriterError subclass.
    
    Args:
        e: Original exception
        wrapper_class: BookWriterError subclass to wrap in
        message: Optional custom message
        
    Returns:
        Wrapped exception
    """
    if isinstance(e, BookWriterError):
        return e
    
    error_message = message or str(e)
    return wrapper_class(error_message, {"original_exception": type(e).__name__, "original_message": str(e)})