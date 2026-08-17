"""Pure package-local checker semantics used by the admission boundary.

External checker results remain supplied evidence.  This module implements
only explicitly code-owned deterministic contracts whose outcome can be
recomputed from one immutable package without I/O, providers, or evaluation.
Dispatch remains private; ``validate_package`` is the public admission entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .model import CheckResult, ClosureRecord, Package, Record
from .registry import LocalClosureSemantics, _materialised_selector_field_spec


@dataclass(frozen=True, slots=True, kw_only=True)
class _LocalClosureEvaluation:
    """The expected outcome of one code-owned local closure contract."""

    selector_supported: bool
    expected_result: CheckResult


def _exact_field_equal(actual: object, expected: object) -> bool:
    return type(actual) is type(expected) and actual == expected


def _matches(record: Record, *, where: Mapping[str, object]) -> bool:
    return all(
        _exact_field_equal(getattr(record, field_name), expected)
        for field_name, expected in where.items()
    )


def _materialised_selector_v1(
    package: Package,
    closure: ClosureRecord,
) -> _LocalClosureEvaluation:
    selector = closure.selector
    for field_name, value in selector.where.items():
        field_spec = _materialised_selector_field_spec(
            selector.record_type,
            field_name,
        )
        if field_spec is None or not any(
            value_type.accepts(value) for value_type in field_spec[0]
        ):
            return _LocalClosureEvaluation(
                selector_supported=False,
                expected_result=CheckResult.OPEN,
            )

    selected = frozenset(
        record.ref
        for record in package.records(selector.record_type)
        if _matches(record, where=selector.where)
    )
    return _LocalClosureEvaluation(
        selector_supported=True,
        expected_result=(
            CheckResult.PASS if selected == closure.members else CheckResult.FAIL
        ),
    )


def _evaluate_local_closure(
    semantics: LocalClosureSemantics,
    package: Package,
    closure: ClosureRecord,
) -> _LocalClosureEvaluation | None:
    """Dispatch one declared local contract, or return ``None`` for supplied data."""

    if type(semantics) is not LocalClosureSemantics:
        raise TypeError("semantics must be an exact LocalClosureSemantics")
    if type(package) is not Package:
        raise TypeError("package must be an exact Package")
    if type(closure) is not ClosureRecord:
        raise TypeError("closure must be an exact ClosureRecord")
    if semantics is LocalClosureSemantics.NONE:
        return None
    if semantics is LocalClosureSemantics.MATERIALISED_SELECTOR_V1:
        return _materialised_selector_v1(package, closure)
    raise AssertionError(f"unhandled local closure semantics: {semantics!r}")


__all__: list[str] = []
