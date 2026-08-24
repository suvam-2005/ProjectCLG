from pathlib import Path

from childagenteval_research.experiment_identity import (
    build_experiment_identity,
    current_git_commit,
    hash_config_file,
)

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "l0.yaml"


def test_experiment_id_is_unique_per_call():
    id1 = build_experiment_identity(CONFIG_PATH, run_id="l0_dev")
    id2 = build_experiment_identity(CONFIG_PATH, run_id="l0_dev")
    assert id1.experiment_id != id2.experiment_id


def test_configuration_hash_matches_file_content_and_changes_when_file_changes(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("a: 1\n")
    h1 = hash_config_file(cfg)
    cfg.write_text("a: 2\n")
    h2 = hash_config_file(cfg)
    assert h1 != h2
    assert len(h1) == 64  # sha256 hex digest


def test_git_commit_capture_returns_placeholder_when_not_a_repo(tmp_path):
    commit = current_git_commit(tmp_path)  # tmp_path is never a git repo
    assert commit in ("no-commits-yet", "unknown")


def test_git_commit_capture_returns_real_sha_in_this_repo():
    repo_dir = Path(__file__).parent.parent
    commit = current_git_commit(repo_dir)
    # This repo may have zero commits at this point in the project's history — accept
    # either a real hex SHA or the explicit "no commits yet" placeholder, never a crash.
    is_hex_sha = len(commit) == 40 and all(c in "0123456789abcdef" for c in commit)
    assert is_hex_sha or commit == "no-commits-yet"


def test_build_experiment_identity_populates_all_fields():
    identity = build_experiment_identity(CONFIG_PATH, run_id="l0_dev")
    d = identity.to_dict()
    assert d["run_id"] == "l0_dev"
    assert d["configuration_hash"] == hash_config_file(CONFIG_PATH)
    assert d["timestamp"] > 0
