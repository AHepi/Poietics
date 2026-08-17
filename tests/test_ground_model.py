from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from poietics.ground import (
    GroundProgram,
    GroundProgramError,
    GroundProgramErrorCode,
    GroundRule,
)


def rule(
    rule_id: str,
    head: str,
    *,
    positive: set[str] | frozenset[str] = frozenset(),
    negative: set[str] | frozenset[str] = frozenset(),
) -> GroundRule:
    return GroundRule(
        id=rule_id,
        head=head,
        positive=frozenset(positive),
        negative=frozenset(negative),
    )


class GroundRuleTests(unittest.TestCase):
    def test_bodies_are_immutable_sets(self) -> None:
        positive = {"a", "b"}
        candidate = rule("r:h", "h", positive=positive)
        positive.add("c")

        self.assertEqual(candidate.positive, frozenset({"a", "b"}))
        with self.assertRaises(FrozenInstanceError):
            candidate.head = "other"  # type: ignore[misc]

    def test_rejects_a_string_in_place_of_a_body_collection(self) -> None:
        with self.assertRaises(TypeError):
            GroundRule(
                id="r:h",
                head="h",
                positive="ab",  # type: ignore[arg-type]
            )


class GroundProgramTests(unittest.TestCase):
    def assert_program_error(
        self,
        code: GroundProgramErrorCode,
        *,
        atoms: set[str],
        rules: tuple[GroundRule, ...] = (),
        live: set[str] = set(),
        excluded: set[str] = set(),
        open_: set[str] = set(),
        expected_atoms: tuple[str, ...] = (),
        expected_rules: tuple[str, ...] = (),
    ) -> None:
        with self.assertRaises(GroundProgramError) as caught:
            GroundProgram(
                atoms=frozenset(atoms),
                rules=rules,
                base_live=frozenset(live),
                base_excluded=frozenset(excluded),
                protected_open=frozenset(open_),
            )

        self.assertEqual(caught.exception.code, code)
        self.assertEqual(caught.exception.atom_refs, expected_atoms)
        self.assertEqual(caught.exception.rule_refs, expected_rules)

    def test_normalises_rule_order_and_copies_inputs(self) -> None:
        atoms = {"a", "b", "c"}
        rules = [
            rule("r:z", "c", positive={"b"}),
            rule("r:a", "b", positive={"a"}),
        ]
        program = GroundProgram(atoms=atoms, rules=rules, base_live={"a"})

        atoms.add("later")
        rules.clear()

        self.assertEqual(program.atoms, frozenset({"a", "b", "c"}))
        self.assertEqual(tuple(item.id for item in program.rules), ("r:a", "r:z"))

    def test_rejects_duplicate_rule_ids_with_typed_evidence(self) -> None:
        self.assert_program_error(
            GroundProgramErrorCode.DUPLICATE_RULE_ID,
            atoms={"a", "b"},
            rules=(rule("r:dup", "a"), rule("r:dup", "b")),
            expected_rules=("r:dup",),
        )

    def test_rejects_every_out_of_universe_reference(self) -> None:
        cases = {
            "head": (rule("r:head", "missing"),),
            "positive": (rule("r:positive", "a", positive={"missing"}),),
            "negative": (rule("r:negative", "a", negative={"missing"}),),
        }
        for name, rules in cases.items():
            with self.subTest(name=name):
                self.assert_program_error(
                    GroundProgramErrorCode.UNKNOWN_ATOM_REFERENCE,
                    atoms={"a"},
                    rules=rules,
                    expected_atoms=("missing",),
                )

        for name, partition in {
            "live": {"live": {"missing"}},
            "excluded": {"excluded": {"missing"}},
            "open": {"open_": {"missing"}},
        }.items():
            with self.subTest(name=name):
                self.assert_program_error(
                    GroundProgramErrorCode.UNKNOWN_ATOM_REFERENCE,
                    atoms={"a"},
                    expected_atoms=("missing",),
                    **partition,
                )

    def test_rejects_all_initial_partition_overlaps(self) -> None:
        self.assert_program_error(
            GroundProgramErrorCode.BASE_STATUS_COLLISION,
            atoms={"x"},
            live={"x"},
            excluded={"x"},
            expected_atoms=("x",),
        )
        self.assert_program_error(
            GroundProgramErrorCode.PROTECTED_OPEN_COLLISION,
            atoms={"x"},
            live={"x"},
            open_={"x"},
            expected_atoms=("x",),
        )
        self.assert_program_error(
            GroundProgramErrorCode.PROTECTED_OPEN_COLLISION,
            atoms={"x"},
            excluded={"x"},
            open_={"x"},
            expected_atoms=("x",),
        )

    def test_atom_references_are_opaque_and_version_exact(self) -> None:
        program = GroundProgram(
            atoms={"atom:e@1", "atom:e@2"},
            base_live={"atom:e@1"},
        )

        self.assertIn("atom:e@1", program.base_live)
        self.assertNotIn("atom:e@2", program.base_live)

    def test_rejects_strings_in_place_of_reference_collections(self) -> None:
        with self.assertRaises(TypeError):
            GroundProgram(atoms="ab")  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            GroundProgram(
                atoms={"a", "b"},
                base_live="a",  # type: ignore[arg-type]
            )

    def test_rejects_mutable_duck_typed_rules(self) -> None:
        class MutableRule:
            id = "r:duck"
            head = "b"
            positive = {"a"}
            negative: set[str] = set()

        with self.assertRaises(TypeError):
            GroundProgram(
                atoms={"a", "b"},
                rules=(MutableRule(),),  # type: ignore[arg-type]
                base_live={"a"},
            )


if __name__ == "__main__":
    unittest.main()
