from pathlib import Path

from childagenteval_research.telemetry.schema import TrajectoryRecord
from childagenteval_research.telemetry.writer import TrajectoryWriter


def make_record(step_number: int, **overrides) -> TrajectoryRecord:
    defaults = dict(
        experiment_id="test-experiment-id",
        run_id="l0_dev",
        task_id="t1",
        subtest="infra_test",
        target_age=10,
        model="qwen/qwen3.5-27b",
        provider="openrouter",
        condition="L0_none",
        timestamp=1000.0 + step_number,
        step_number=step_number,
        observation_metadata={},
        action={"action": "wait"},
        action_result={"success": True},
        latency_s=0.1,
        input_tokens=5,
        output_tokens=5,
        cost_usd=0.0,
        cumulative_cost_usd=0.0,
    )
    defaults.update(overrides)
    return TrajectoryRecord(**defaults)


def test_writer_appends_one_json_line_per_record(tmp_path: Path):
    path = tmp_path / "trajectories" / "t1.jsonl"
    writer = TrajectoryWriter(path=path)

    writer.write(make_record(0))
    writer.write(make_record(1))

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2

    records = writer.read_all()
    assert [r["step_number"] for r in records] == [0, 1]


def test_writer_creates_parent_directories(tmp_path: Path):
    path = tmp_path / "a" / "b" / "c.jsonl"
    writer = TrajectoryWriter(path=path)
    writer.write(make_record(0))
    assert path.exists()


def test_read_all_on_missing_file_returns_empty_list(tmp_path: Path):
    writer = TrajectoryWriter(path=tmp_path / "does_not_exist.jsonl")
    assert writer.read_all() == []
