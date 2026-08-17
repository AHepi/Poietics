from __future__ import annotations

import ast
import importlib
import inspect
import unittest
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from poietics.ground.evaluate import evaluate
from poietics.ground.model import GroundProgram, GroundRule, Status
from poietics.pff.compile import (
    ArtifactOrigin,
    Compilation,
    CompilationCode,
    CompilationIssue,
    CompilationRole,
    CompiledContrary,
    GroundArtifactKind,
    PackageCompilationError,
    SourceRecord,
    compile_package,
)
import poietics.pff.compile as compile_module
import poietics.pff.local_checkers as local_checkers_module
from poietics.pff.model import (
    BasePartition,
    CheckResult,
    ClosedNegativeLiteral,
    ClosureRecord,
    ContraryRecord,
    Package,
    RecordKind,
    RuleRecord,
    Selector,
)
from poietics.pff.registry import (
    CheckerContract,
    CheckerUse,
    RegistryCatalog,
)
import poietics.pff.validate as validate_module
from poietics.pff.validate import ValidatedPackage, validate_package
from tests.test_pff_validate import (
    atom,
    catalog,
    certificate,
    linked_valid_package,
    minimal_valid_package,
    ref,
    registry,
)


SUPPLIED_CLOSURE_CHECKER = "supplied-closure/v1"


def literal_rule(
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


def compiler_catalog() -> RegistryCatalog:
    authority = registry()
    supplied_closure = CheckerContract(
        checker_id=SUPPLIED_CLOSURE_CHECKER,
        version=1,
        uses={CheckerUse.CLOSURE},
        closure_selector_kinds={RecordKind.ATOM},
        closure_frame_policy_id="frame:exact-package",
    )
    return RegistryCatalog(
        registries=(
            replace(
                authority,
                checker_contracts=(
                    *authority.checker_contracts,
                    supplied_closure,
                ),
            ),
        )
    )


def validated(candidate: Package) -> ValidatedPackage:
    return validate_package(candidate, compiler_catalog())


def empty_package() -> Package:
    return Package(header=minimal_valid_package().header)


def supplied_closure(
    record_id: str,
    result: CheckResult,
    *,
    version: int = 1,
) -> ClosureRecord:
    return ClosureRecord(
        id=record_id,
        version=version,
        checker=SUPPLIED_CLOSURE_CHECKER,
        result=result,
        cut_id="cut:1",
        frame="frame:1",
        selector=Selector(record_type=RecordKind.ATOM),
    )


def literal_origin(
    artifact_kind: GroundArtifactKind,
    artifact_ref: str,
    role: CompilationRole,
    source_kind: RecordKind,
    source_id: str,
    source_version: int = 1,
) -> ArtifactOrigin:
    return ArtifactOrigin(
        artifact_kind=artifact_kind,
        artifact_ref=artifact_ref,
        role=role,
        sources=(
            SourceRecord(
                kind=source_kind,
                ref=ref(source_id, source_version),
            ),
        ),
    )


def semantic_artifacts(
    compilation: Compilation,
) -> tuple[GroundProgram, tuple[CompiledContrary, ...], tuple[ArtifactOrigin, ...]]:
    """The deterministic compiler output, excluding its exact source evidence."""

    return (
        compilation.program,
        compilation.contraries,
        compilation.origins,
    )


def certificate_matrix_package() -> Package:
    source = atom("atom:source", "test.primitive", primitive=True)
    results = (
        ("pass", CheckResult.PASS),
        ("fail", CheckResult.FAIL),
        ("open", CheckResult.OPEN),
    )
    heads = tuple(atom(f"atom:{name}", "test.derived") for name, _ in results)
    rules = tuple(
        RuleRecord(
            id=f"rule:{name}",
            version=1,
            head=head.ref,
            positive=(source.ref,),
            certificate=ref(f"cert:{name}"),
        )
        for (name, _), head in zip(results, heads, strict=True)
    )
    certificates = tuple(
        certificate(
            f"cert:{name}",
            "rule-witness/v1",
            rule.ref,
            result=result,
        )
        for (name, result), rule in zip(results, rules, strict=True)
    )
    return Package(
        header=minimal_valid_package().header,
        atoms=(source, *heads),
        rules=rules,
        certificates=certificates,
        base=BasePartition(live=(source.ref,)),
    )


def guarded_negative_package() -> Package:
    seed = minimal_valid_package()
    second_source = atom(
        "atom:source-two",
        "test.primitive",
        primitive=True,
    )
    first_negative = atom("atom:negative-one", "test.derived")
    second_negative = atom("atom:negative-two", "test.derived")
    first_closure = supplied_closure("closure:first", CheckResult.PASS)
    second_closure = supplied_closure("closure:second", CheckResult.PASS)
    rule = replace(
        seed.rules[0],
        positive=(seed.atoms[0].ref, second_source.ref),
        negative=(
            ClosedNegativeLiteral(
                atom=first_negative.ref,
                closure=first_closure.ref,
            ),
            ClosedNegativeLiteral(
                atom=first_negative.ref,
                closure=second_closure.ref,
            ),
            ClosedNegativeLiteral(
                atom=second_negative.ref,
                closure=second_closure.ref,
            ),
        ),
    )
    return replace(
        seed,
        atoms=(
            seed.atoms[0],
            second_source,
            seed.atoms[1],
            first_negative,
            second_negative,
        ),
        rules=(rule,),
        closures=(first_closure, second_closure),
        base=BasePartition(live=(seed.atoms[0].ref, second_source.ref)),
    )


def alternative_package() -> Package:
    seed = minimal_valid_package()
    first_rule = replace(
        seed.rules[0],
        id="rule:a-alternative",
        certificate=ref("cert:a-alternative"),
    )
    second_rule = replace(
        seed.rules[0],
        id="rule:z-alternative",
        certificate=ref("cert:z-alternative"),
    )
    first_certificate = certificate(
        "cert:a-alternative",
        "rule-witness/v1",
        first_rule.ref,
    )
    second_certificate = certificate(
        "cert:z-alternative",
        "rule-witness/v1",
        second_rule.ref,
    )
    return replace(
        seed,
        rules=(second_rule, first_rule),
        certificates=(second_certificate, first_certificate),
    )


class ExactLoweringTests(unittest.TestCase):
    def test_empty_validated_package_compiles_to_an_empty_artifact(self) -> None:
        source = validated(empty_package())

        compiled = compile_package(source)

        self.assertIs(compiled.source, source)
        self.assertEqual(compiled.program, GroundProgram(atoms=()))
        self.assertEqual(compiled.contraries, ())
        self.assertEqual(compiled.origins, ())

    def test_minimal_program_and_source_map_match_an_independent_golden(self) -> None:
        source = validated(minimal_valid_package())

        compiled = compile_package(source)

        cert_valid = "__pff__:cert-valid(cert:derive@1)"
        cert_failed = "__pff__:cert-failed(cert:derive@1)"
        cert_open = "__pff__:cert-open(cert:derive@1)"
        live_case = "__pff__:live-case(rule:derive@1)"
        expected_program = GroundProgram(
            atoms={
                "atom:source@1",
                "atom:derived@1",
                cert_valid,
                cert_failed,
                cert_open,
                live_case,
            },
            rules=(
                literal_rule(
                    "__pff__:rule-case(rule:derive@1)",
                    live_case,
                    positive={cert_valid, "atom:source@1"},
                ),
                literal_rule(
                    "__pff__:head-bridge(rule:derive@1)",
                    "atom:derived@1",
                    positive={live_case},
                ),
            ),
            base_live={"atom:source@1", cert_valid},
        )
        expected_origins = (
            literal_origin(
                GroundArtifactKind.ATOM,
                cert_failed,
                CompilationRole.CERT_FAILED,
                RecordKind.CERTIFICATE,
                "cert:derive",
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                cert_open,
                CompilationRole.CERT_OPEN,
                RecordKind.CERTIFICATE,
                "cert:derive",
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                cert_valid,
                CompilationRole.CERT_VALID,
                RecordKind.CERTIFICATE,
                "cert:derive",
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                live_case,
                CompilationRole.LIVE_CASE,
                RecordKind.RULE,
                "rule:derive",
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                "atom:derived@1",
                CompilationRole.SOURCE_ATOM,
                RecordKind.ATOM,
                "atom:derived",
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                "atom:source@1",
                CompilationRole.SOURCE_ATOM,
                RecordKind.ATOM,
                "atom:source",
            ),
            literal_origin(
                GroundArtifactKind.RULE,
                "__pff__:head-bridge(rule:derive@1)",
                CompilationRole.HEAD_BRIDGE,
                RecordKind.RULE,
                "rule:derive",
            ),
            literal_origin(
                GroundArtifactKind.RULE,
                "__pff__:rule-case(rule:derive@1)",
                CompilationRole.RULE_CASE,
                RecordKind.RULE,
                "rule:derive",
            ),
        )

        self.assertIs(compiled.source, source)
        self.assertEqual(compiled.program, expected_program)
        self.assertEqual(compiled.contraries, ())
        self.assertEqual(compiled.origins, expected_origins)
        for origin in expected_origins:
            self.assertEqual(
                compiled.origin_for(origin.artifact_kind, origin.artifact_ref),
                origin,
            )

    def test_certificate_result_table_is_literal_and_complete(self) -> None:
        compiled = compile_package(validated(certificate_matrix_package()))

        expected_atoms = {
            "atom:source@1",
            "atom:pass@1",
            "atom:fail@1",
            "atom:open@1",
        }
        expected_rules: list[GroundRule] = []
        for name in ("pass", "fail", "open"):
            expected_atoms.update(
                {
                    f"__pff__:cert-valid(cert:{name}@1)",
                    f"__pff__:cert-failed(cert:{name}@1)",
                    f"__pff__:cert-open(cert:{name}@1)",
                    f"__pff__:live-case(rule:{name}@1)",
                }
            )
            expected_rules.extend(
                (
                    literal_rule(
                        f"__pff__:rule-case(rule:{name}@1)",
                        f"__pff__:live-case(rule:{name}@1)",
                        positive={
                            f"__pff__:cert-valid(cert:{name}@1)",
                            "atom:source@1",
                        },
                    ),
                    literal_rule(
                        f"__pff__:head-bridge(rule:{name}@1)",
                        f"atom:{name}@1",
                        positive={f"__pff__:live-case(rule:{name}@1)"},
                    ),
                )
            )
        expected = GroundProgram(
            atoms=expected_atoms,
            rules=tuple(expected_rules),
            base_live={
                "atom:source@1",
                "__pff__:cert-valid(cert:pass@1)",
                "__pff__:cert-failed(cert:fail@1)",
                "__pff__:cert-open(cert:open@1)",
            },
            base_excluded={"__pff__:cert-valid(cert:fail@1)"},
            protected_open={"__pff__:cert-valid(cert:open@1)"},
        )

        self.assertEqual(compiled.program, expected)
        self.assertEqual(len(compiled.origins), len(expected.atoms) + len(expected.rules))

    def test_closure_result_table_is_literal_complete_and_asymmetric(self) -> None:
        closures = (
            supplied_closure("closure:open", CheckResult.OPEN),
            supplied_closure("closure:pass", CheckResult.PASS),
            supplied_closure("closure:fail", CheckResult.FAIL),
        )
        candidate = replace(empty_package(), closures=closures)

        compiled = compile_package(validated(candidate))

        expected_atoms = {
            f"__pff__:closure-{role}(closure:{name}@1)"
            for role in ("ready", "failed", "open")
            for name in ("pass", "fail", "open")
        }
        expected = GroundProgram(
            atoms=expected_atoms,
            base_live={
                "__pff__:closure-ready(closure:pass@1)",
                "__pff__:closure-failed(closure:fail@1)",
                "__pff__:closure-open(closure:open@1)",
            },
            protected_open={
                "__pff__:closure-ready(closure:fail@1)",
                "__pff__:closure-ready(closure:open@1)",
            },
        )
        expected_roles = {
            "ready": CompilationRole.CLOSURE_READY,
            "failed": CompilationRole.CLOSURE_FAILED,
            "open": CompilationRole.CLOSURE_OPEN,
        }

        self.assertEqual(compiled.program, expected)
        self.assertEqual(compiled.program.base_excluded, frozenset())
        for role_name, role in expected_roles.items():
            for closure_name in ("pass", "fail", "open"):
                artifact = (
                    f"__pff__:closure-{role_name}(closure:{closure_name}@1)"
                )
                self.assertEqual(
                    compiled.origin_for(GroundArtifactKind.ATOM, artifact),
                    literal_origin(
                        GroundArtifactKind.ATOM,
                        artifact,
                        role,
                        RecordKind.CLOSURE,
                        f"closure:{closure_name}",
                    ),
                )

        reversed_compilation = compile_package(
            validated(replace(candidate, closures=tuple(reversed(closures))))
        )
        self.assertEqual(
            semantic_artifacts(reversed_compilation),
            semantic_artifacts(compiled),
        )

    def test_closed_negatives_keep_every_gate_and_one_default_target(self) -> None:
        compiled = compile_package(validated(guarded_negative_package()))

        expected_case = literal_rule(
            "__pff__:rule-case(rule:derive@1)",
            "__pff__:live-case(rule:derive@1)",
            positive={
                "__pff__:cert-valid(cert:derive@1)",
                "atom:source@1",
                "atom:source-two@1",
                "__pff__:closure-ready(closure:first@1)",
                "__pff__:closure-ready(closure:second@1)",
            },
            negative={"atom:negative-one@1", "atom:negative-two@1"},
        )
        expected_bridge = literal_rule(
            "__pff__:head-bridge(rule:derive@1)",
            "atom:derived@1",
            positive={"__pff__:live-case(rule:derive@1)"},
        )

        self.assertEqual(
            set(compiled.program.rules),
            {expected_case, expected_bridge},
        )
        self.assertEqual(
            expected_case.positive
            & {
                "__pff__:closure-ready(closure:first@1)",
                "__pff__:closure-ready(closure:second@1)",
            },
            {
                "__pff__:closure-ready(closure:first@1)",
                "__pff__:closure-ready(closure:second@1)",
            },
        )
        self.assertEqual(
            expected_case.negative,
            {"atom:negative-one@1", "atom:negative-two@1"},
        )

    def test_same_head_alternatives_have_independent_cases_and_bridges(self) -> None:
        compiled = compile_package(validated(alternative_package()))

        expected_rules = {
            literal_rule(
                "__pff__:rule-case(rule:a-alternative@1)",
                "__pff__:live-case(rule:a-alternative@1)",
                positive={
                    "__pff__:cert-valid(cert:a-alternative@1)",
                    "atom:source@1",
                },
            ),
            literal_rule(
                "__pff__:head-bridge(rule:a-alternative@1)",
                "atom:derived@1",
                positive={"__pff__:live-case(rule:a-alternative@1)"},
            ),
            literal_rule(
                "__pff__:rule-case(rule:z-alternative@1)",
                "__pff__:live-case(rule:z-alternative@1)",
                positive={
                    "__pff__:cert-valid(cert:z-alternative@1)",
                    "atom:source@1",
                },
            ),
            literal_rule(
                "__pff__:head-bridge(rule:z-alternative@1)",
                "atom:derived@1",
                positive={"__pff__:live-case(rule:z-alternative@1)"},
            ),
        }

        self.assertEqual(set(compiled.program.rules), expected_rules)
        self.assertIn(
            "__pff__:live-case(rule:a-alternative@1)",
            compiled.program.atoms,
        )
        self.assertIn(
            "__pff__:live-case(rule:z-alternative@1)",
            compiled.program.atoms,
        )

    def test_compiled_gate_outcomes_drive_the_expected_ground_statuses(self) -> None:
        certificate_evaluation = evaluate(
            compile_package(validated(certificate_matrix_package())).program
        )
        self.assertEqual(
            {
                name: certificate_evaluation.status_of(f"atom:{name}@1")
                for name in ("pass", "fail", "open")
            },
            {
                "pass": Status.LIVE,
                "fail": Status.EXCLUDED,
                "open": Status.SUSPENDED,
            },
        )

        seed = minimal_valid_package()
        negative_target = atom(
            "atom:closed-negative",
            "test.primitive",
            primitive=True,
        )
        for closure_result, expected in (
            (CheckResult.PASS, Status.LIVE),
            (CheckResult.FAIL, Status.SUSPENDED),
            (CheckResult.OPEN, Status.SUSPENDED),
        ):
            with self.subTest(closure_result=closure_result):
                closure = supplied_closure("closure:negative", closure_result)
                rule = replace(
                    seed.rules[0],
                    negative=(
                        ClosedNegativeLiteral(
                            atom=negative_target.ref,
                            closure=closure.ref,
                        ),
                    ),
                )
                candidate = replace(
                    seed,
                    atoms=(*seed.atoms, negative_target),
                    rules=(rule,),
                    closures=(closure,),
                    base=BasePartition(
                        live=(seed.atoms[0].ref,),
                        excluded=(negative_target.ref,),
                    ),
                )

                result = evaluate(compile_package(validated(candidate)).program)

                self.assertEqual(result.status_of("atom:derived@1"), expected)


class IdentityDeterminismAndContraryTests(unittest.TestCase):
    def test_base_versions_order_and_metadata_do_not_change_artifacts(self) -> None:
        source_v1 = atom(
            "atom:versioned",
            "test.primitive",
            version=1,
            primitive=True,
        )
        source_v2 = atom(
            "atom:versioned",
            "test.primitive",
            version=2,
            primitive=True,
        )
        excluded = atom(
            "atom:excluded",
            "test.primitive",
            primitive=True,
        )
        head = atom("atom:derived", "test.derived")
        first_rule = RuleRecord(
            id="rule:versioned",
            version=1,
            head=head.ref,
            positive=(source_v1.ref,),
            certificate=ref("cert:versioned", 1),
        )
        second_rule = RuleRecord(
            id="rule:versioned",
            version=2,
            head=head.ref,
            positive=(source_v2.ref,),
            certificate=ref("cert:versioned", 2),
        )
        first_certificate = certificate(
            "cert:versioned",
            "rule-witness/v1",
            first_rule.ref,
        )
        second_certificate = replace(
            certificate(
                "cert:versioned-v2-source",
                "rule-witness/v1",
                second_rule.ref,
            ),
            id="cert:versioned",
            version=2,
        )
        seed = minimal_valid_package()
        candidate = Package(
            header=seed.header,
            atoms=(head, source_v2, excluded, source_v1),
            rules=(second_rule, first_rule),
            certificates=(second_certificate, first_certificate),
            base=BasePartition(
                live=(source_v1.ref,),
                excluded=(excluded.ref,),
                open=(source_v2.ref,),
            ),
        )
        reordered = replace(
            candidate,
            atoms=tuple(reversed(candidate.atoms)),
            rules=tuple(reversed(candidate.rules)),
            certificates=tuple(reversed(candidate.certificates)),
            header=replace(
                candidate.header,
                parent_package_hash="sha256:different-lineage",
                metadata={"display": {"order": [3, 2, 1]}},
            ),
        )

        first = compile_package(validated(candidate))
        second = compile_package(validated(reordered))

        self.assertEqual(semantic_artifacts(first), semantic_artifacts(second))
        self.assertNotEqual(first, second)
        self.assertIsNot(first.source.package, second.source.package)
        self.assertEqual(
            first.program.base_live,
            {"atom:versioned@1", "__pff__:cert-valid(cert:versioned@1)", "__pff__:cert-valid(cert:versioned@2)"},
        )
        self.assertEqual(first.program.base_excluded, {"atom:excluded@1"})
        self.assertEqual(first.program.protected_open, {"atom:versioned@2"})
        for version in (1, 2):
            self.assertIn(f"atom:versioned@{version}", first.program.atoms)
            self.assertIn(
                f"__pff__:cert-valid(cert:versioned@{version})",
                first.program.atoms,
            )
            self.assertIn(
                f"__pff__:live-case(rule:versioned@{version})",
                first.program.atoms,
            )
            self.assertIn(
                f"__pff__:rule-case(rule:versioned@{version})",
                {str(rule.id) for rule in first.program.rules},
            )
            self.assertIn(
                f"__pff__:head-bridge(rule:versioned@{version})",
                {str(rule.id) for rule in first.program.rules},
            )

    def test_delimiter_heavy_and_unicode_ids_use_the_frozen_literal_grammar(self) -> None:
        source = atom(
            "atom:@:π",
            "test.primitive",
            version=7,
            primitive=True,
        )
        candidate = replace(
            empty_package(),
            atoms=(source,),
            base=BasePartition(live=(source.ref,)),
        )

        compiled = compile_package(validated(candidate))

        self.assertEqual(compiled.program.atoms, {"atom:@:π@7"})
        self.assertEqual(compiled.program.base_live, {"atom:@:π@7"})

    def test_contraries_normalize_endpoints_retain_sources_and_do_not_affect_program(self) -> None:
        seed = minimal_valid_package()
        left = atom("atom:left", "test.contrary-left")
        right = atom("atom:right", "test.contrary-right", version=2)
        forward = ContraryRecord(
            id="contrary:z-forward",
            version=2,
            left=left.ref,
            right=right.ref,
            boundary="comparison:entity-frame",
        )
        reversed_pair = ContraryRecord(
            id="contrary:a-reversed",
            version=1,
            left=right.ref,
            right=left.ref,
            boundary="comparison:entity-frame",
        )
        candidate = replace(
            seed,
            atoms=(*seed.atoms, right, left),
            contraries=(forward, reversed_pair),
        )
        without_contraries = replace(candidate, contraries=())

        compiled = compile_package(validated(candidate))
        plain = compile_package(validated(without_contraries))

        expected = (
            CompiledContrary(
                source=reversed_pair.ref,
                first="atom:left@1",
                second="atom:right@2",
                boundary="comparison:entity-frame",
            ),
            CompiledContrary(
                source=forward.ref,
                first="atom:left@1",
                second="atom:right@2",
                boundary="comparison:entity-frame",
            ),
        )
        self.assertEqual(compiled.contraries, expected)
        self.assertEqual(compiled.program, plain.program)
        self.assertEqual(compiled.origins, plain.origins)

        permuted = replace(candidate, contraries=tuple(reversed(candidate.contraries)))
        self.assertEqual(
            semantic_artifacts(compile_package(validated(permuted))),
            semantic_artifacts(compiled),
        )


class CapabilityAndBoundaryTests(unittest.TestCase):
    def test_compilation_is_factory_only_and_deeply_immutable(self) -> None:
        source = validated(minimal_valid_package())
        compiled = compile_package(source)

        with self.assertRaises(TypeError):
            Compilation(
                source=source,
                program=compiled.program,
                contraries=compiled.contraries,
                origins=compiled.origins,
            )
        with self.assertRaises(FrozenInstanceError):
            compiled.program = GroundProgram(atoms=())  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            compiled.origins[0].role = CompilationRole.SOURCE_ATOM  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            compiled.origins[0].sources[0].ref = ref("atom:other")  # type: ignore[misc]
        with self.assertRaises(TypeError):
            compiled._origin_index[  # type: ignore[index]
                (GroundArtifactKind.ATOM, "new")
            ] = compiled.origins[0]

        expected_order = tuple(
            sorted(
                compiled.origins,
                key=lambda item: (
                    item.artifact_kind.value,
                    item.artifact_ref,
                    item.role.value,
                    tuple(
                        (source.kind.value, source.ref.id, source.ref.version)
                        for source in item.sources
                    ),
                ),
            )
        )
        self.assertEqual(compiled.origins, expected_order)

    def test_wrapper_equality_binds_exact_validated_evidence(self) -> None:
        candidate = minimal_valid_package()
        first = compile_package(validated(candidate))
        changed_evidence = replace(
            candidate,
            certificates=(
                replace(
                    candidate.certificates[0],
                    payload_hash="sha256:different-evidence",
                ),
            ),
        )
        second = compile_package(validated(changed_evidence))

        self.assertEqual(semantic_artifacts(first), semantic_artifacts(second))
        self.assertNotEqual(first, second)
        with self.assertRaises(TypeError):
            hash(first)

    def test_compile_accepts_only_the_exact_validated_capability(self) -> None:
        signature = inspect.signature(compile_package)
        self.assertEqual(tuple(signature.parameters), ("source",))

        for candidate in (minimal_valid_package(), object()):
            with self.subTest(type=type(candidate).__name__):
                with self.assertRaises(TypeError):
                    compile_package(candidate)  # type: ignore[arg-type]

    def test_pending_records_fail_once_per_record_in_canonical_kind_order(self) -> None:
        candidate = linked_valid_package()
        original_face = candidate.faces[0]
        second_face = replace(
            original_face,
            id="face:second",
            blocker_closure=ref("closure:second-blockers"),
        )
        second_blocker_closure = ClosureRecord(
            id="closure:second-blockers",
            version=1,
            checker="materialised-selector/v1",
            result=CheckResult.PASS,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.CHALLENGE,
                where={"target": second_face.ref},
            ),
        )
        candidate = replace(
            candidate,
            rules=(
                replace(
                    candidate.rules[0],
                    faces={original_face.ref, second_face.ref},
                ),
            ),
            faces=(second_face, original_face),
            closures=(*candidate.closures, second_blocker_closure),
        )
        source = validate_package(candidate, catalog())

        with self.assertRaises(PackageCompilationError) as caught:
            compile_package(source)

        self.assertEqual(
            caught.exception.issues,
            (
                CompilationIssue(
                    code=CompilationCode.UNSUPPORTED_RECORD_KIND,
                    record_kind=RecordKind.FACE,
                    ref=original_face.ref,
                ),
                CompilationIssue(
                    code=CompilationCode.UNSUPPORTED_RECORD_KIND,
                    record_kind=RecordKind.FACE,
                    ref=second_face.ref,
                ),
                CompilationIssue(
                    code=CompilationCode.UNSUPPORTED_RECORD_KIND,
                    record_kind=RecordKind.CHALLENGE,
                    ref=candidate.challenges[0].ref,
                ),
                CompilationIssue(
                    code=CompilationCode.UNSUPPORTED_RECORD_KIND,
                    record_kind=RecordKind.DISCHARGE,
                    ref=candidate.discharges[0].ref,
                ),
            ),
        )

    def test_compiler_does_not_call_validation_checker_or_evaluator(self) -> None:
        source = validated(minimal_valid_package())
        ground_evaluate_module = importlib.import_module("poietics.ground.evaluate")

        with (
            patch.object(
                validate_module,
                "validate_package",
                side_effect=AssertionError("compiler called validation"),
            ) as validation_call,
            patch.object(
                local_checkers_module,
                "_evaluate_local_closure",
                side_effect=AssertionError("compiler called a checker"),
            ) as checker_call,
            patch.object(
                ground_evaluate_module,
                "evaluate",
                side_effect=AssertionError("compiler called evaluation"),
            ) as evaluator_call,
        ):
            compiled = compile_package(source)

        self.assertIs(compiled.source, source)
        validation_call.assert_not_called()
        checker_call.assert_not_called()
        evaluator_call.assert_not_called()

    def test_compiler_project_imports_are_direct_and_allowlisted(self) -> None:
        tree = ast.parse(inspect.getsource(compile_module))
        project_import_symbols = {
            (node.level, node.module, alias.name, alias.asname)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level > 0
            for alias in node.names
        }
        absolute_project_import_symbols = {
            (node.module, alias.name, alias.asname)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module is not None
            and (
                node.module == "poietics"
                or node.module.startswith("poietics.")
            )
            for alias in node.names
        }
        expected_project_import_symbols = {
            (2, "ground.model", name, None)
            for name in ("AtomRef", "GroundProgram", "GroundRule", "RuleRef")
        } | {
            (1, "model", name, None)
            for name in (
                "AtomRecord",
                "CertificateRecord",
                "CheckResult",
                "ClosureRecord",
                "ContraryRecord",
                "RecordKind",
                "RecordRef",
                "RuleRecord",
            )
        } | {(1, "validate", "ValidatedPackage", None)}
        plain_imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        dynamic_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "__import__")
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module"
                )
            )
        ]

        self.assertEqual(
            project_import_symbols,
            expected_project_import_symbols,
        )
        self.assertEqual(absolute_project_import_symbols, set())
        self.assertEqual(plain_imports, set())
        self.assertEqual(dynamic_imports, [])
        imported_parts = {
            part
            for _, module, _, _ in project_import_symbols
            if module is not None
            for part in module.split(".")
        }
        self.assertTrue(
            {
                "evaluate",
                "local_checkers",
                "provider",
                "providers",
                "generation",
                "parser",
                "canonical",
            }.isdisjoint(imported_parts)
        )


if __name__ == "__main__":
    unittest.main()
