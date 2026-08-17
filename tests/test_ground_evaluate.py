from __future__ import annotations

import itertools
import unittest
from dataclasses import dataclass

from poietics.ground import (
    Evaluation,
    GroundProgram,
    GroundProgramError,
    GroundProgramErrorCode,
    GroundRule,
    Status,
    evaluate,
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


@dataclass(frozen=True, slots=True, kw_only=True)
class Case:
    name: str
    atoms: set[str]
    rules: tuple[GroundRule, ...] = ()
    live: set[str] = frozenset()  # type: ignore[assignment]
    excluded: set[str] = frozenset()  # type: ignore[assignment]
    open_: set[str] = frozenset()  # type: ignore[assignment]
    expected_live: set[str] = frozenset()  # type: ignore[assignment]
    expected_excluded: set[str] = frozenset()  # type: ignore[assignment]
    expected_suspended: set[str] = frozenset()  # type: ignore[assignment]


CASES = (
    Case(
        name="closed_unseeded_atom",
        atoms={"z"},
        expected_excluded={"z"},
    ),
    Case(
        name="positive_chain_reversed_rule_order",
        atoms={"a", "b", "c"},
        rules=(
            rule("r:c_from_b", "c", positive={"b"}),
            rule("r:b_from_a", "b", positive={"a"}),
        ),
        live={"a"},
        expected_live={"a", "b", "c"},
    ),
    Case(
        name="conjunction_all_live",
        atoms={"a", "b", "h"},
        rules=(rule("r:h_from_a_b", "h", positive={"a", "b"}),),
        live={"a", "b"},
        expected_live={"a", "b", "h"},
    ),
    Case(
        name="conjunction_one_excluded",
        atoms={"a", "b", "h"},
        rules=(rule("r:h_from_a_b", "h", positive={"a", "b"}),),
        live={"a"},
        excluded={"b"},
        expected_live={"a"},
        expected_excluded={"b", "h"},
    ),
    Case(
        name="conjunction_one_protected_open",
        atoms={"a", "b", "h"},
        rules=(rule("r:h_from_a_b", "h", positive={"a", "b"}),),
        live={"a"},
        open_={"b"},
        expected_live={"a"},
        expected_suspended={"b", "h"},
    ),
    Case(
        name="independent_alternative_survives",
        atoms={"p", "q", "h"},
        rules=(
            rule("r:h_from_q", "h", positive={"q"}),
            rule("r:h_from_p", "h", positive={"p"}),
        ),
        live={"p"},
        excluded={"q"},
        expected_live={"p", "h"},
        expected_excluded={"q"},
    ),
    Case(
        name="open_alternative_preserves_suspension",
        atoms={"o", "q", "h"},
        rules=(
            rule("r:h_from_q", "h", positive={"q"}),
            rule("r:h_from_o", "h", positive={"o"}),
        ),
        excluded={"q"},
        open_={"o"},
        expected_excluded={"q"},
        expected_suspended={"o", "h"},
    ),
    Case(
        name="unsupported_positive_cycle",
        atoms={"a", "b", "c"},
        rules=(
            rule("r:a_from_b", "a", positive={"b"}),
            rule("r:b_from_c", "b", positive={"c"}),
            rule("r:c_from_a", "c", positive={"a"}),
        ),
        expected_excluded={"a", "b", "c"},
    ),
    Case(
        name="externally_supported_positive_cycle",
        atoms={"seed", "a", "b"},
        rules=(
            rule("r:a_from_b", "a", positive={"b"}),
            rule("r:b_from_a", "b", positive={"a"}),
            rule("r:a_from_seed", "a", positive={"seed"}),
        ),
        live={"seed"},
        expected_live={"seed", "a", "b"},
    ),
    Case(
        name="protected_open_propagates",
        atoms={"o", "a", "b", "z"},
        rules=(
            rule("r:a_from_o", "a", positive={"o"}),
            rule("r:b_from_a", "b", positive={"a"}),
        ),
        open_={"o"},
        expected_excluded={"z"},
        expected_suspended={"o", "a", "b"},
    ),
    Case(
        name="negative_target_excluded",
        atoms={"n", "h"},
        rules=(rule("r:h_without_n", "h", negative={"n"}),),
        excluded={"n"},
        expected_live={"h"},
        expected_excluded={"n"},
    ),
    Case(
        name="derived_exclusion_enables_negative_rule_next_round",
        atoms={"n", "h"},
        rules=(rule("r:h_without_n", "h", negative={"n"}),),
        expected_live={"h"},
        expected_excluded={"n"},
    ),
    Case(
        name="negative_target_live",
        atoms={"n", "h"},
        rules=(rule("r:h_without_n", "h", negative={"n"}),),
        live={"n"},
        expected_live={"n"},
        expected_excluded={"h"},
    ),
    Case(
        name="negative_target_protected_open",
        atoms={"n", "h"},
        rules=(rule("r:h_without_n", "h", negative={"n"}),),
        open_={"n"},
        expected_suspended={"n", "h"},
    ),
    Case(
        name="even_negative_cycle",
        atoms={"a", "b"},
        rules=(
            rule("r:a_without_b", "a", negative={"b"}),
            rule("r:b_without_a", "b", negative={"a"}),
        ),
        expected_suspended={"a", "b"},
    ),
    Case(
        name="protected_open_can_be_derived",
        atoms={"o", "h"},
        rules=(
            rule("r:o_fact", "o"),
            rule("r:h_from_o", "h", positive={"o"}),
        ),
        open_={"o"},
        expected_live={"o", "h"},
    ),
)


class EvaluationFixtureTests(unittest.TestCase):
    def test_complete_partitions(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                program = GroundProgram(
                    atoms=case.atoms,
                    rules=case.rules,
                    base_live=case.live,
                    base_excluded=case.excluded,
                    protected_open=case.open_,
                )
                original_fields = (
                    program.atoms,
                    program.rules,
                    program.base_live,
                    program.base_excluded,
                    program.protected_open,
                )

                result = evaluate(program)

                self.assertEqual(result.live, frozenset(case.expected_live))
                self.assertEqual(
                    result.excluded, frozenset(case.expected_excluded)
                )
                self.assertEqual(
                    result.suspended, frozenset(case.expected_suspended)
                )
                self.assertTrue(result.live.isdisjoint(result.excluded))
                self.assertEqual(
                    result.live | result.excluded | result.suspended,
                    program.atoms,
                )
                self.assertTrue(program.protected_open.isdisjoint(result.excluded))
                self.assertEqual(evaluate(program), result)
                self.assertEqual(
                    (
                        program.atoms,
                        program.rules,
                        program.base_live,
                        program.base_excluded,
                        program.protected_open,
                    ),
                    original_fields,
                )

    def test_status_query_is_typed_and_total_only_over_the_partition(self) -> None:
        result = Evaluation(
            live={"live"},
            excluded={"excluded"},
            suspended={"suspended"},
        )

        self.assertEqual(result.status_of("live"), Status.LIVE)
        self.assertEqual(result.status_of("excluded"), Status.EXCLUDED)
        self.assertEqual(result.status_of("suspended"), Status.SUSPENDED)
        with self.assertRaises(KeyError):
            result.status_of("unknown")


class DeterminismTests(unittest.TestCase):
    def test_every_rule_permutation_has_the_same_exact_result(self) -> None:
        rules = (
            rule("r:p", "p", positive={"seed"}),
            rule("r:q", "q", positive={"p"}),
            rule("r:h", "h", positive={"q", "o"}),
            rule(
                "r:s",
                "s",
                positive={"seed", "q"},
                negative={"n", "m"},
            ),
            rule("r:x", "x", positive={"y"}),
            rule("r:y", "y", positive={"x"}),
        )
        expected = Evaluation(
            live={"seed", "p", "q", "s"},
            excluded={"n", "m", "x", "y"},
            suspended={"o", "h"},
        )

        for permutation in itertools.permutations(rules):
            program = GroundProgram(
                atoms={"seed", "p", "q", "h", "o", "s", "x", "y", "n", "m"},
                rules=permutation,
                base_live={"seed"},
                base_excluded={"n", "m"},
                protected_open={"o"},
            )
            self.assertEqual(evaluate(program), expected)

    def test_reverse_ordered_chain_terminates_at_the_full_fixed_point(self) -> None:
        atoms = {f"a{index:02}" for index in range(32)}
        rules = tuple(
            rule(
                f"r:{32 - index:02}:a{index:02}",
                f"a{index:02}",
                positive={f"a{index - 1:02}"},
            )
            for index in range(1, 32)
        )
        program = GroundProgram(atoms=atoms, rules=rules, base_live={"a00"})

        self.assertEqual(program.rules[0].head, "a31")
        self.assertEqual(program.rules[-1].head, "a01")
        self.assertEqual(evaluate(program).live, frozenset(atoms))


class CollisionTests(unittest.TestCase):
    def test_definitely_derived_excluded_head_is_invalid(self) -> None:
        program = GroundProgram(
            atoms={"p", "x"},
            rules=(rule("r:x_from_p", "x", positive={"p"}),),
            base_live={"p"},
            base_excluded={"x"},
        )

        with self.assertRaises(GroundProgramError) as caught:
            evaluate(program)

        self.assertEqual(
            caught.exception.code,
            GroundProgramErrorCode.DERIVED_STATUS_COLLISION,
        )
        self.assertEqual(caught.exception.atom_refs, ("x",))
        self.assertEqual(caught.exception.rule_refs, ("r:x_from_p",))

    def test_collision_check_repeats_after_each_fixed_point_round(self) -> None:
        program = GroundProgram(
            atoms={"seed", "p", "x"},
            rules=(
                rule("r:p_from_seed", "p", positive={"seed"}),
                rule("r:x_from_p", "x", positive={"p"}),
            ),
            base_live={"seed"},
            base_excluded={"x"},
        )

        with self.assertRaises(GroundProgramError) as caught:
            evaluate(program)

        self.assertEqual(
            caught.exception.code,
            GroundProgramErrorCode.DERIVED_STATUS_COLLISION,
        )
        self.assertEqual(caught.exception.atom_refs, ("x",))
        self.assertEqual(caught.exception.rule_refs, ("r:x_from_p",))

    def test_collision_reports_all_atoms_and_enabled_cases(self) -> None:
        program = GroundProgram(
            atoms={"p", "x", "y"},
            rules=(
                rule("r:x:2", "x", positive={"p"}),
                rule("r:y", "y", positive={"p"}),
                rule("r:x:1", "x", positive={"p"}),
            ),
            base_live={"p"},
            base_excluded={"x", "y"},
        )

        with self.assertRaises(GroundProgramError) as caught:
            evaluate(program)

        self.assertEqual(caught.exception.atom_refs, ("x", "y"))
        self.assertEqual(
            caught.exception.rule_refs,
            ("r:x:1", "r:x:2", "r:y"),
        )


if __name__ == "__main__":
    unittest.main()
