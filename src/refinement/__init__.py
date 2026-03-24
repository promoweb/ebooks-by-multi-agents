"""
Refinement System for BookWriterAI.

This module provides iterative refinement capabilities for
improving generated content quality.

Components:
- Quality Assessment: Multi-dimensional quality evaluation
- Refinement Pipeline: Iterative improvement process
- Refiners: Specialized content improvement (structural, prose, consistency)

Example usage:
    from src.refinement import QualityAssessor, IterativeRefinementPipeline
    
    # Assess quality
    assessor = QualityAssessor()
    score = assessor.assess_chapter(content, chapter_info)
    
    # Refine content
    pipeline = IterativeRefinementPipeline(llm_client=client)
    result = pipeline.refine_chapter(content, chapter_info)
"""

# Quality Assessment
from src.refinement.quality import (
    QualityDimension,
    IssueSeverity,
    QualityIssue,
    QualityScore,
    BookQualityReport,
    QualityAssessor,
)

# Refinement Pipeline
from src.refinement.pipeline import (
    RefinementType,
    RefinementResult,
    PipelineConfig,
    StructuralRefiner,
    ProseRefiner,
    ConsistencyCorrector,
    IterativeRefinementPipeline,
)


__all__ = [
    # Quality Assessment
    "QualityDimension",
    "IssueSeverity",
    "QualityIssue",
    "QualityScore",
    "BookQualityReport",
    "QualityAssessor",
    
    # Refinement Pipeline
    "RefinementType",
    "RefinementResult",
    "PipelineConfig",
    "StructuralRefiner",
    "ProseRefiner",
    "ConsistencyCorrector",
    "IterativeRefinementPipeline",
]