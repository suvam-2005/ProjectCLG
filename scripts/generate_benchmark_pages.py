"""Renders every validated task JSON in benchmark/tasks/ into a standalone HTML page
under benchmark/pages/. Re-run whenever a task JSON changes."""
from pathlib import Path

from childagenteval_research.benchmark.task_page import generate_page_file
from childagenteval_research.benchmark.task_schema import load_all_tasks

PROJECT_ROOT = Path(__file__).parent.parent

if __name__ == "__main__":
    tasks = load_all_tasks(PROJECT_ROOT / "benchmark" / "tasks")
    out_dir = PROJECT_ROOT / "benchmark" / "pages"
    for task in tasks:
        generate_page_file(task, out_dir)
    print(f"generated {len(tasks)} pages in {out_dir}")
