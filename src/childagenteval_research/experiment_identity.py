"""Reproducibility metadata for a run: a unique experiment_id, the configured run_id,
the git commit of the code that produced it, and a hash of the exact config file used.
"""
from __future__ import annotations

import hashlib
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExperimentIdentity:
    experiment_id: str
    run_id: str
    git_commit: str
    configuration_hash: str
    timestamp: float

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def current_git_commit(repo_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if result.returncode != 0:
        return "no-commits-yet"
    return result.stdout.strip()


def hash_config_file(config_path: Path) -> str:
    return hashlib.sha256(config_path.read_bytes()).hexdigest()


def build_experiment_identity(config_path: Path, run_id: str, repo_dir: Path | None = None) -> ExperimentIdentity:
    return ExperimentIdentity(
        experiment_id=str(uuid.uuid4()),
        run_id=run_id,
        git_commit=current_git_commit(repo_dir or config_path.parent),
        configuration_hash=hash_config_file(config_path),
        timestamp=time.time(),
    )
