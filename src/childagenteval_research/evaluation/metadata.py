"""Model/provider/reproducibility metadata every result must carry."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..experiment_identity import build_experiment_identity


@dataclass
class RunMetadata:
    model: str
    model_version: str | None
    provider: str
    temperature: float
    max_output_tokens: int
    benchmark_version: str | None  # None until official access confirms one
    experiment_id: str
    run_id: str
    git_commit: str
    configuration_hash: str
    timestamp: float

    @classmethod
    def build(
        cls,
        *,
        model: str,
        provider: str,
        temperature: float,
        max_output_tokens: int,
        config_path: Path,
        run_id: str,
        model_version: str | None = None,
        benchmark_version: str | None = None,
    ) -> "RunMetadata":
        identity = build_experiment_identity(config_path, run_id=run_id)
        return cls(
            model=model,
            model_version=model_version,
            provider=provider,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            benchmark_version=benchmark_version,
            experiment_id=identity.experiment_id,
            run_id=run_id,
            git_commit=identity.git_commit,
            configuration_hash=identity.configuration_hash,
            timestamp=identity.timestamp,
        )
