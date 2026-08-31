"""Renders a TaskDefinition into a standalone HTML page. The correct answer is never
embedded in the page — scoring.py determines correctness afterward, purely from the
agent's recorded click targets, so there is nothing for the agent to read off the DOM.
"""
from __future__ import annotations

import html
from pathlib import Path

from .task_schema import TaskDefinition

_PAGE_TEMPLATE = """<!--
INDEPENDENT_INTERACTIVE_COGNITIVE_AGE_BENCHMARK — task {task_id}
NOT ChildAgentEval. Original content authored for this project. No WISC-derived material.
-->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{task_id}</title>
<style>
  body {{ font-family: sans-serif; padding: 1.5em; }}
  .target, .choice {{ display: inline-block; margin: 0.4em; padding: 0.6em 1em;
                       border: 1px solid #888; cursor: pointer; }}
  #finish_button {{ margin-top: 1.5em; }}
  #status {{ margin-top: 1em; font-weight: bold; }}
</style>
</head>
<body>
  <p id="instructions">{instructions}</p>
  <div id="stimulus">{stimulus_html}</div>
  <div id="interactive_area">{interactive_html}</div>
  <button id="finish_button" type="button">Finish</button>
  <div id="status" data-state="not_started">not_started</div>
  <script>
    const status = document.getElementById("status");
    document.querySelectorAll(".target, .choice").forEach((el) => {{
      el.addEventListener("click", () => {{
        status.dataset.state = "in_progress";
        status.textContent = "in_progress";
      }});
    }});
    document.getElementById("finish_button").addEventListener("click", () => {{
      status.dataset.state = "completed";
      status.textContent = "completed";
    }});
  </script>
</body>
</html>
"""


def _render_multiple_choice(task: TaskDefinition) -> tuple[str, str]:
    prompt = html.escape(str(task.stimulus.get("prompt", "")))
    stimulus_html = f"<p>{prompt}</p>"
    buttons = "\n".join(
        f'<button class="choice" id="{html.escape(c["id"])}" type="button">{html.escape(c["label"])}</button>'
        for c in task.choices
    )
    return stimulus_html, buttons


def _render_sequence_click(task: TaskDefinition) -> tuple[str, str]:
    display = task.stimulus.get("sequence_display", [])
    stimulus_html = "<p>Sequence to remember: " + ", ".join(html.escape(str(x)) for x in display) + "</p>"
    targets = task.stimulus.get("targets", [])
    buttons = "\n".join(
        f'<button class="target" id="{html.escape(t["id"])}" type="button">{html.escape(t["label"])}</button>'
        for t in targets
    )
    return stimulus_html, buttons


_RENDERERS = {
    "multiple_choice": _render_multiple_choice,
    "sequence_click": _render_sequence_click,
}


def render_task_page(task: TaskDefinition) -> str:
    stimulus_html, interactive_html = _RENDERERS[task.interaction_kind](task)
    return _PAGE_TEMPLATE.format(
        task_id=html.escape(task.task_id),
        instructions=html.escape(task.instructions),
        stimulus_html=stimulus_html,
        interactive_html=interactive_html,
    )


def generate_page_file(task: TaskDefinition, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{task.task_id}.html"
    out_path.write_text(render_task_page(task), encoding="utf-8")
    return out_path
