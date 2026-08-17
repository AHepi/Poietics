"""Deterministic well-founded evaluation for finite ground programs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import AbstractSet

from .errors import GroundProgramError, GroundProgramErrorCode
from .model import AtomRef, Evaluation, GroundProgram, GroundRule


def definitely_enabled(
    rule: GroundRule,
    live: AbstractSet[AtomRef],
    excluded: AbstractSet[AtomRef],
) -> bool:
    """Whether every positive is live and every negative target excluded."""

    return rule.positive <= live and rule.negative <= excluded


def greatest_unfounded(
    atoms: AbstractSet[AtomRef],
    rules_by_head: Mapping[AtomRef, Sequence[GroundRule]],
    live: AbstractSet[AtomRef],
    excluded: AbstractSet[AtomRef],
    protected_open: AbstractSet[AtomRef],
) -> frozenset[AtomRef]:
    """Compute the normative finite greatest-unfounded set.

    A protected-open atom is never placed in the set. A suspended premise or
    negative target counts as possible external support, so uncertainty is
    preserved rather than collapsed into exclusion.
    """

    unfounded = set(atoms) - set(protected_open) - set(live)

    while True:
        externally_supported: set[AtomRef] = set()

        for atom in unfounded:
            for rule in rules_by_head.get(atom, ()):
                if rule.positive & excluded:
                    continue
                if rule.negative & live:
                    continue
                if rule.positive & unfounded:
                    continue

                externally_supported.add(atom)
                break

        next_unfounded = unfounded - externally_supported
        if next_unfounded == unfounded:
            return frozenset(unfounded)
        unfounded = next_unfounded


def _rules_by_head(
    rules: Sequence[GroundRule],
) -> dict[AtomRef, tuple[GroundRule, ...]]:
    indexed: defaultdict[AtomRef, list[GroundRule]] = defaultdict(list)
    for rule in rules:
        indexed[rule.head].append(rule)
    return {head: tuple(cases) for head, cases in indexed.items()}


def evaluate(program: GroundProgram) -> Evaluation:
    """Fully recompute the unique live, excluded, and suspended partition."""

    live = set(program.base_live)
    excluded = set(program.base_excluded)
    rules_by_head = _rules_by_head(program.rules)

    while True:
        enabled_rules = tuple(
            rule
            for rule in program.rules
            if definitely_enabled(rule, live, excluded)
        )
        enabled_heads = {rule.head for rule in enabled_rules}

        collision = enabled_heads & excluded
        if collision:
            raise GroundProgramError(
                GroundProgramErrorCode.DERIVED_STATUS_COLLISION,
                atom_refs=collision,
                rule_refs=(
                    rule.id for rule in enabled_rules if rule.head in collision
                ),
            )

        next_live = live | enabled_heads
        unfounded = greatest_unfounded(
            program.atoms,
            rules_by_head,
            next_live,
            excluded,
            program.protected_open,
        )
        next_excluded = excluded | set(unfounded)

        if next_live == live and next_excluded == excluded:
            break

        live = next_live
        excluded = next_excluded

    suspended = set(program.atoms) - live - excluded
    return Evaluation(
        live=frozenset(live),
        excluded=frozenset(excluded),
        suspended=frozenset(suspended),
    )
