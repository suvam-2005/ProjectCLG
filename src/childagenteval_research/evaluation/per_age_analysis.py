"""Groups results by target age x condition without collapsing ages into one number."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping, Sequence, TypeVar

T = TypeVar("T")


def group_by_age_and_condition(
    results: Sequence[T],
    age_getter: Callable[[T], int],
    condition_getter: Callable[[T], str],
) -> dict[int, dict[str, list[T]]]:
    grouped: dict[int, dict[str, list[T]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        grouped[age_getter(r)][condition_getter(r)].append(r)
    return {age: dict(by_condition) for age, by_condition in grouped.items()}


def summarize_grouped(
    grouped: Mapping[int, Mapping[str, Sequence[T]]],
    summarize_fn: Callable[[Sequence[T]], Any],
) -> dict[int, dict[str, Any]]:
    """Applies summarize_fn (e.g. statistics_utils.describe on extracted scores) to each
    (age, condition) cell independently — ages are never averaged together here."""
    return {
        age: {condition: summarize_fn(items) for condition, items in by_condition.items()}
        for age, by_condition in grouped.items()
    }
