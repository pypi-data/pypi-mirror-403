"""Analysis pipeline for slopit.

This module provides orchestration for running multiple analyzers
and aggregating their results.
"""

from slopit.pipeline.aggregation import AggregationStrategy, aggregate_flags
from slopit.pipeline.pipeline import AnalysisPipeline, PipelineConfig
from slopit.pipeline.reporting import CSVExporter, TextReporter

__all__ = [
    "AggregationStrategy",
    "AnalysisPipeline",
    "CSVExporter",
    "PipelineConfig",
    "TextReporter",
    "aggregate_flags",
]
