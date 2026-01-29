# Custom Analyzers

This guide covers writing custom analyzers for domain-specific detection.

## Analyzer Architecture

Analyzers in slopit follow a simple pattern:

1. Receive a `SlopitSession`
2. Process behavioral data
3. Compute metrics
4. Generate flags based on thresholds
5. Return an `AnalysisResult`

## Basic Structure

```python
from dataclasses import dataclass

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import SlopitSession
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


@dataclass
class MyAnalyzerConfig(AnalyzerConfig):
    """Configuration for my analyzer."""

    threshold: float = 0.5


class MyAnalyzer(Analyzer):
    """My custom analyzer."""

    def __init__(self, config: MyAnalyzerConfig | None = None) -> None:
        self.config = config or MyAnalyzerConfig()

    @property
    def name(self) -> str:
        return "my_analyzer"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze a session."""
        trial_results: list[dict[str, JsonValue]] = []
        all_flags: list[AnalysisFlag] = []

        for trial in session.trials:
            # Skip trials without needed data
            if not self._has_required_data(trial):
                continue

            # Compute metrics
            metrics = self._compute_metrics(trial)

            # Generate flags
            flags = self._compute_flags(trial.trial_id, metrics)

            # Store results
            trial_results.append({
                "trial_id": trial.trial_id,
                "metrics": metrics,
                "flags": [f.model_dump() for f in flags],
            })
            all_flags.extend(flags)

        return AnalysisResult(
            analyzer=self.name,
            session_id=session.session_id,
            trials=trial_results,
            flags=all_flags,
            session_summary=self._compute_summary(trial_results),
        )

    def _has_required_data(self, trial) -> bool:
        """Check if trial has required data."""
        return trial.behavioral is not None

    def _compute_metrics(self, trial) -> dict[str, JsonValue]:
        """Compute metrics from trial data."""
        return {"example_metric": 42.0}

    def _compute_flags(
        self, trial_id: str, metrics: dict[str, JsonValue]
    ) -> list[AnalysisFlag]:
        """Generate flags based on metrics."""
        flags: list[AnalysisFlag] = []

        value = metrics.get("example_metric", 0)
        if isinstance(value, (int, float)) and value > self.config.threshold:
            flags.append(
                AnalysisFlag(
                    type="example_flag",
                    analyzer=self.name,
                    severity="medium",
                    message=f"Example metric exceeded threshold ({value:.1f})",
                    confidence=0.7,
                    evidence={"example_metric": value},
                    trial_ids=[trial_id],
                )
            )

        return flags

    def _compute_summary(
        self, trial_results: list[dict[str, JsonValue]]
    ) -> dict[str, JsonValue]:
        """Compute session-level summary."""
        return {
            "trials_analyzed": len(trial_results),
            "total_flags": sum(
                len(r["flags"]) if isinstance(r["flags"], list) else 0
                for r in trial_results
            ),
        }
```

## Example: Response Length Analyzer

An analyzer that flags suspiciously long responses:

```python
from dataclasses import dataclass

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import SlopitSession, SlopitTrial
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


@dataclass
class ResponseLengthConfig(AnalyzerConfig):
    """Configuration for response length analysis."""

    max_chars_per_minute: float = 500.0
    min_response_length: int = 100


class ResponseLengthAnalyzer(Analyzer):
    """Analyzes response length relative to time spent."""

    def __init__(self, config: ResponseLengthConfig | None = None) -> None:
        self.config = config or ResponseLengthConfig()

    @property
    def name(self) -> str:
        return "response_length"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        trial_results: list[dict[str, JsonValue]] = []
        all_flags: list[AnalysisFlag] = []

        for trial in session.trials:
            if not self._is_analyzable(trial):
                continue

            metrics = self._compute_metrics(trial)
            flags = self._compute_flags(trial.trial_id, metrics)

            trial_results.append({
                "trial_id": trial.trial_id,
                "metrics": metrics,
                "flags": [f.model_dump() for f in flags],
            })
            all_flags.extend(flags)

        return AnalysisResult(
            analyzer=self.name,
            session_id=session.session_id,
            trials=trial_results,
            flags=all_flags,
            session_summary={"trials_analyzed": len(trial_results)},
        )

    def _is_analyzable(self, trial: SlopitTrial) -> bool:
        """Check if trial has response with sufficient length."""
        if trial.response is None:
            return False
        if trial.response.character_count is None:
            return False
        if trial.response.character_count < self.config.min_response_length:
            return False
        if trial.rt is None or trial.rt <= 0:
            return False
        return True

    def _compute_metrics(self, trial: SlopitTrial) -> dict[str, JsonValue]:
        """Compute characters per minute."""
        char_count = trial.response.character_count  # type: ignore
        rt_minutes = trial.rt / 60000  # type: ignore

        chars_per_minute = char_count / rt_minutes if rt_minutes > 0 else 0

        return {
            "character_count": char_count,
            "rt_ms": trial.rt,
            "chars_per_minute": chars_per_minute,
        }

    def _compute_flags(
        self, trial_id: str, metrics: dict[str, JsonValue]
    ) -> list[AnalysisFlag]:
        """Flag if typing speed is unrealistic."""
        flags: list[AnalysisFlag] = []

        cpm = metrics.get("chars_per_minute", 0)
        if isinstance(cpm, (int, float)) and cpm > self.config.max_chars_per_minute:
            confidence = min(1.0, cpm / (self.config.max_chars_per_minute * 2))
            flags.append(
                AnalysisFlag(
                    type="unrealistic_typing_speed",
                    analyzer=self.name,
                    severity="high",
                    message=f"Response produced at {cpm:.0f} chars/min (threshold: {self.config.max_chars_per_minute})",
                    confidence=confidence,
                    evidence={"chars_per_minute": cpm},
                    trial_ids=[trial_id],
                )
            )

        return flags
```

## Example: Cross-Trial Similarity Analyzer

An analyzer that detects similar responses across trials (possible template usage):

```python
from dataclasses import dataclass

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import SlopitSession
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


@dataclass
class SimilarityConfig(AnalyzerConfig):
    """Configuration for similarity analysis."""

    min_similarity_threshold: float = 0.8
    min_response_words: int = 20


class SimilarityAnalyzer(Analyzer):
    """Detects suspiciously similar responses across trials."""

    def __init__(self, config: SimilarityConfig | None = None) -> None:
        self.config = config or SimilarityConfig()

    @property
    def name(self) -> str:
        return "similarity"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        # Extract text responses
        responses: list[tuple[str, str]] = []  # (trial_id, text)

        for trial in session.trials:
            if trial.response is None:
                continue
            if trial.response.type != "text":
                continue
            if not isinstance(trial.response.value, str):
                continue

            text = trial.response.value
            words = text.lower().split()

            if len(words) >= self.config.min_response_words:
                responses.append((trial.trial_id, text))

        # Compute pairwise similarities
        flags: list[AnalysisFlag] = []
        similarities: list[dict[str, JsonValue]] = []

        for i, (trial_a, text_a) in enumerate(responses):
            words_a = set(text_a.lower().split())

            for trial_b, text_b in responses[i + 1:]:
                words_b = set(text_b.lower().split())
                sim = jaccard_similarity(words_a, words_b)

                if sim >= self.config.min_similarity_threshold:
                    similarities.append({
                        "trial_a": trial_a,
                        "trial_b": trial_b,
                        "similarity": sim,
                    })

                    flags.append(
                        AnalysisFlag(
                            type="high_response_similarity",
                            analyzer=self.name,
                            severity="medium",
                            message=f"Responses highly similar ({sim:.0%} word overlap)",
                            confidence=sim,
                            evidence={"similarity": sim},
                            trial_ids=[trial_a, trial_b],
                        )
                    )

        return AnalysisResult(
            analyzer=self.name,
            session_id=session.session_id,
            trials=[],
            flags=flags,
            session_summary={
                "responses_compared": len(responses),
                "high_similarity_pairs": len(similarities),
            },
        )
```

## Cross-Session Analysis

For analyzers that need to compare across sessions, override `analyze_sessions`:

```python
class HomogeneityAnalyzer(Analyzer):
    """Detects identical responses across different participants."""

    @property
    def name(self) -> str:
        return "homogeneity"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        # Single-session analysis (can be empty for cross-session analyzers)
        return AnalysisResult(
            analyzer=self.name,
            session_id=session.session_id,
            trials=[],
            flags=[],
            session_summary={},
        )

    def analyze_sessions(self, sessions: list[SlopitSession]) -> list[AnalysisResult]:
        """Compare responses across all sessions."""
        # Collect all responses
        response_to_sessions: dict[str, list[str]] = {}

        for session in sessions:
            for trial in session.trials:
                if trial.response and isinstance(trial.response.value, str):
                    text = trial.response.value.strip().lower()
                    if text:
                        if text not in response_to_sessions:
                            response_to_sessions[text] = []
                        response_to_sessions[text].append(session.session_id)

        # Find duplicate responses
        duplicates = {
            text: session_ids
            for text, session_ids in response_to_sessions.items()
            if len(session_ids) > 1
        }

        # Generate results
        results: list[AnalysisResult] = []
        flagged_sessions = set()

        for text, session_ids in duplicates.items():
            for session_id in session_ids:
                flagged_sessions.add(session_id)

        for session in sessions:
            flags: list[AnalysisFlag] = []

            if session.session_id in flagged_sessions:
                flags.append(
                    AnalysisFlag(
                        type="duplicate_response",
                        analyzer=self.name,
                        severity="high",
                        message="Response identical to another participant",
                        confidence=0.95,
                        evidence={},
                        trial_ids=None,
                    )
                )

            results.append(
                AnalysisResult(
                    analyzer=self.name,
                    session_id=session.session_id,
                    trials=[],
                    flags=flags,
                    session_summary={
                        "is_duplicate": session.session_id in flagged_sessions,
                    },
                )
            )

        return results
```

## Using Custom Analyzers

```python
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline

# Import your custom analyzers
from my_analyzers import ResponseLengthAnalyzer, SimilarityAnalyzer

sessions = load_sessions("data/")

pipeline = AnalysisPipeline([
    ResponseLengthAnalyzer(),
    SimilarityAnalyzer(),
])

result = pipeline.analyze(sessions)
```

## Best Practices

1. **Single responsibility**: Each analyzer should detect one type of pattern
2. **Clear flag types**: Use descriptive, unique flag type names
3. **Configurable thresholds**: Make detection parameters configurable
4. **Meaningful confidence**: Compute confidence based on how far the metric exceeds the threshold
5. **Rich evidence**: Include relevant metrics in the evidence field
6. **Trial IDs**: Always include trial_ids when the flag is trial-specific
7. **Session summary**: Provide useful aggregate statistics
8. **Type safety**: Use proper type annotations throughout
9. **Documentation**: Include docstrings with NumPy format

## Testing Analyzers

```python
import pytest
from slopit.schemas import SlopitSession, SlopitTrial, ResponseInfo

from my_analyzers import ResponseLengthAnalyzer, ResponseLengthConfig


@pytest.fixture
def fast_response_session() -> SlopitSession:
    """Session with unrealistically fast response."""
    return SlopitSession(
        schema_version="1.0",
        session_id="test",
        platform=...,
        environment=...,
        timing=...,
        trials=[
            SlopitTrial(
                trial_id="trial-0",
                trial_index=0,
                start_time=0,
                end_time=1000,
                rt=1000,  # 1 second
                response=ResponseInfo(
                    type="text",
                    value="x" * 1000,  # 1000 characters
                    character_count=1000,
                ),
            )
        ],
        global_events=...,
    )


class TestResponseLengthAnalyzer:
    def test_flags_fast_response(self, fast_response_session):
        """Should flag unrealistically fast typing."""
        analyzer = ResponseLengthAnalyzer()
        result = analyzer.analyze_session(fast_response_session)

        assert len(result.flags) == 1
        assert result.flags[0].type == "unrealistic_typing_speed"

    def test_custom_threshold(self, fast_response_session):
        """Should respect custom threshold."""
        config = ResponseLengthConfig(max_chars_per_minute=100000)
        analyzer = ResponseLengthAnalyzer(config)
        result = analyzer.analyze_session(fast_response_session)

        assert len(result.flags) == 0  # High threshold, no flag
```
