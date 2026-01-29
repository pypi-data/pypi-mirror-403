"""Flag aggregation strategies.

This module provides different strategies for combining flags
from multiple analyzers into a final verdict.
"""

from typing import Literal

from slopit.schemas.flags import AnalysisFlag

AggregationStrategy = Literal["any", "majority", "weighted"]
VerdictStatus = Literal["clean", "suspicious", "flagged"]


def aggregate_flags(
    flags: list[AnalysisFlag],
    strategy: AggregationStrategy,
    total_analyzers: int,
) -> tuple[VerdictStatus, float]:
    """Aggregate flags using the specified strategy.

    Parameters
    ----------
    flags
        List of flags to aggregate.
    strategy
        Aggregation strategy to use.
    total_analyzers
        Total number of analyzers in the pipeline.

    Returns
    -------
    tuple[VerdictStatus, float]
        The verdict status and confidence score.
    """
    if not flags:
        return ("clean", 1.0)

    if strategy == "any":
        return _aggregate_any(flags)
    elif strategy == "majority":
        return _aggregate_majority(flags, total_analyzers)
    else:  # weighted
        return _aggregate_weighted(flags)


def _aggregate_any(flags: list[AnalysisFlag]) -> tuple[VerdictStatus, float]:
    """Flag if any analyzer produces a flag.

    Most sensitive but highest false positive rate.
    """
    max_confidence = max((f.confidence or 0.5) for f in flags)
    return ("flagged", max_confidence)


def _aggregate_majority(
    flags: list[AnalysisFlag],
    total_analyzers: int,
) -> tuple[VerdictStatus, float]:
    """Flag if majority of analyzers produce flags.

    Balances sensitivity and specificity.
    """
    flagging_analyzers = len({f.analyzer for f in flags})
    ratio = flagging_analyzers / total_analyzers if total_analyzers > 0 else 0

    # With 0 analyzers, we cannot determine majority, so return suspicious if flags exist
    if total_analyzers == 0:
        if flagging_analyzers > 0:
            return ("suspicious", ratio)
        return ("clean", 1.0)

    if flagging_analyzers > total_analyzers / 2:
        return ("flagged", ratio)
    elif flagging_analyzers > 0:
        return ("suspicious", ratio)
    else:
        return ("clean", 1.0 - ratio)


def _aggregate_weighted(flags: list[AnalysisFlag]) -> tuple[VerdictStatus, float]:
    """Use confidence-weighted voting.

    Recommended for most use cases.
    """
    total_weight = sum((f.confidence or 0.5) for f in flags)
    avg_confidence = total_weight / len(flags) if flags else 0

    if avg_confidence >= 0.7:
        return ("flagged", avg_confidence)
    elif avg_confidence >= 0.4:
        return ("suspicious", avg_confidence)
    else:
        return ("clean", 1.0 - avg_confidence)
