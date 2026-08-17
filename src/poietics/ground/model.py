"""Immutable records for a finite ground normal program."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import NewType

from .errors import GroundProgramError, GroundProgramErrorCode

AtomRef = NewType("AtomRef", str)
RuleRef = NewType("RuleRef", str)


def _require_ref(value: str, *, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} must be a non-empty string")


def _freeze_refs(
    values: Iterable[AtomRef],
    *,
    label: str,
) -> frozenset[AtomRef]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{label} must be a collection of atom references")
    frozen = frozenset(values)
    for ref in frozen:
        _require_ref(ref, label=f"{label} member")
    return frozen


def _freeze_rules(values: Iterable[GroundRule]) -> tuple[GroundRule, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("rules must be a collection of GroundRule records")
    frozen = tuple(values)
    if any(type(rule) is not GroundRule for rule in frozen):
        raise TypeError("rules must contain only immutable GroundRule records")
    return tuple(sorted(frozen, key=lambda rule: str(rule.id)))


@dataclass(frozen=True, slots=True, kw_only=True)
class GroundRule:
    """One conjunctive rule case in a finite ground normal program.

    Atom references are opaque to this layer. A future compiler owns their
    construction and version binding; the evaluator compares the complete
    references exactly.
    """

    id: RuleRef
    head: AtomRef
    positive: frozenset[AtomRef] = field(default_factory=frozenset)
    negative: frozenset[AtomRef] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _require_ref(self.id, label="rule id")
        _require_ref(self.head, label="rule head")

        positive = _freeze_refs(self.positive, label="positive body")
        negative = _freeze_refs(self.negative, label="negative body")

        object.__setattr__(self, "positive", positive)
        object.__setattr__(self, "negative", negative)


@dataclass(frozen=True, slots=True, kw_only=True)
class GroundProgram:
    """A validated, immutable finite input to the ground evaluator."""

    atoms: frozenset[AtomRef]
    rules: tuple[GroundRule, ...] = ()
    base_live: frozenset[AtomRef] = field(default_factory=frozenset)
    base_excluded: frozenset[AtomRef] = field(default_factory=frozenset)
    protected_open: frozenset[AtomRef] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        atoms = _freeze_refs(self.atoms, label="atoms")
        rules = _freeze_rules(self.rules)
        base_live = _freeze_refs(self.base_live, label="base_live")
        base_excluded = _freeze_refs(self.base_excluded, label="base_excluded")
        protected_open = _freeze_refs(
            self.protected_open,
            label="protected_open",
        )

        object.__setattr__(self, "atoms", atoms)
        object.__setattr__(self, "rules", rules)
        object.__setattr__(self, "base_live", base_live)
        object.__setattr__(self, "base_excluded", base_excluded)
        object.__setattr__(self, "protected_open", protected_open)

        duplicate_ids = {
            rule_id
            for rule_id, count in Counter(str(rule.id) for rule in rules).items()
            if count > 1
        }
        if duplicate_ids:
            raise GroundProgramError(
                GroundProgramErrorCode.DUPLICATE_RULE_ID,
                rule_refs=duplicate_ids,
            )

        referenced = set(base_live | base_excluded | protected_open)
        for rule in rules:
            referenced.add(rule.head)
            referenced.update(rule.positive)
            referenced.update(rule.negative)

        unknown = referenced - atoms
        if unknown:
            raise GroundProgramError(
                GroundProgramErrorCode.UNKNOWN_ATOM_REFERENCE,
                atom_refs=unknown,
            )

        base_collision = base_live & base_excluded
        if base_collision:
            raise GroundProgramError(
                GroundProgramErrorCode.BASE_STATUS_COLLISION,
                atom_refs=base_collision,
            )

        open_collision = protected_open & (base_live | base_excluded)
        if open_collision:
            raise GroundProgramError(
                GroundProgramErrorCode.PROTECTED_OPEN_COLLISION,
                atom_refs=open_collision,
            )


class Status(StrEnum):
    """Package-relative computational status; never a truth value."""

    LIVE = "LIVE"
    EXCLUDED = "EXCLUDED"
    SUSPENDED = "SUSPENDED"


@dataclass(frozen=True, slots=True, kw_only=True)
class Evaluation:
    """The complete partition derived for one ground program."""

    live: frozenset[AtomRef]
    excluded: frozenset[AtomRef]
    suspended: frozenset[AtomRef]

    def __post_init__(self) -> None:
        live = frozenset(self.live)
        excluded = frozenset(self.excluded)
        suspended = frozenset(self.suspended)
        if live & excluded or live & suspended or excluded & suspended:
            raise ValueError("evaluation partitions must be pairwise disjoint")
        object.__setattr__(self, "live", live)
        object.__setattr__(self, "excluded", excluded)
        object.__setattr__(self, "suspended", suspended)

    def status_of(self, atom: AtomRef) -> Status:
        """Return the derived status of an atom in this evaluation."""

        if atom in self.live:
            return Status.LIVE
        if atom in self.excluded:
            return Status.EXCLUDED
        if atom in self.suspended:
            return Status.SUSPENDED
        raise KeyError(atom)
