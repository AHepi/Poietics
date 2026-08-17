"""Typed failures at the trusted ground-program boundary."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum


class GroundProgramErrorCode(StrEnum):
    """Machine-readable reasons why no semantic evaluation can be returned."""

    UNKNOWN_ATOM_REFERENCE = "unknown_atom_reference"
    DUPLICATE_RULE_ID = "duplicate_rule_id"
    BASE_STATUS_COLLISION = "base_status_collision"
    PROTECTED_OPEN_COLLISION = "protected_open_collision"
    DERIVED_STATUS_COLLISION = "derived_status_collision"


class GroundProgramError(ValueError):
    """An invalid ground program or evaluation, with structured evidence."""

    code: GroundProgramErrorCode
    atom_refs: tuple[str, ...]
    rule_refs: tuple[str, ...]

    def __init__(
        self,
        code: GroundProgramErrorCode,
        *,
        atom_refs: Iterable[str] = (),
        rule_refs: Iterable[str] = (),
    ) -> None:
        self.code = code
        self.atom_refs = tuple(sorted({str(ref) for ref in atom_refs}))
        self.rule_refs = tuple(sorted({str(ref) for ref in rule_refs}))

        evidence = []
        if self.atom_refs:
            evidence.append(f"atoms={self.atom_refs!r}")
        if self.rule_refs:
            evidence.append(f"rules={self.rule_refs!r}")
        suffix = f": {', '.join(evidence)}" if evidence else ""
        super().__init__(f"{code.value}{suffix}")

