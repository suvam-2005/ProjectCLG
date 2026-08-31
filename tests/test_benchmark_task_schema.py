from pathlib import Path

import pytest

from childagenteval_research.benchmark.task_schema import TaskValidationError, load_all_tasks

TASKS_DIR = Path(__file__).parent.parent / "benchmark" / "tasks"


def test_all_real_tasks_load_and_validate():
    tasks = load_all_tasks(TASKS_DIR)
    assert len(tasks) == 32


def test_real_tasks_balanced_across_categories_and_ages():
    tasks = load_all_tasks(TASKS_DIR)
    categories = {t.category for t in tasks}
    ages = {t.target_age for t in tasks}
    assert len(categories) == 8
    assert ages == {7, 10, 13, 16}
    for category in categories:
        assert sum(1 for t in tasks if t.category == category) == 4
    for age in ages:
        assert sum(1 for t in tasks if t.target_age == age) == 8


def test_every_task_id_is_unique():
    tasks = load_all_tasks(TASKS_DIR)
    ids = [t.task_id for t in tasks]
    assert len(ids) == len(set(ids))


def test_every_task_includes_finish_action():
    tasks = load_all_tasks(TASKS_DIR)
    assert all("finish" in t.available_actions for t in tasks)


def test_duplicate_task_id_rejected(tmp_path):
    import shutil

    duplicate_dir = tmp_path / "tasks"
    duplicate_dir.mkdir()
    src = TASKS_DIR / "reasoning" / "reasoning_age7_v1.json"
    shutil.copy(src, duplicate_dir / "a.json")
    shutil.copy(src, duplicate_dir / "b.json")
    with pytest.raises(TaskValidationError, match="duplicate task_id"):
        load_all_tasks(duplicate_dir)
