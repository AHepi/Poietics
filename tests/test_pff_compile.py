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
    ChallengeRecord,
    CheckResult,
    ClosedNegativeLiteral,
    ClosureRecord,
    ContraryRecord,
    DischargeRecord,
    FaceRecord,
    Package,
    RecordKind,
    RuleRecord,
    Selector,
)
from poietics.pff.registry import (
    ChallengeTargetContract,
    CheckerContract,
    CheckerDetailType,
    CheckerUse,
    DischargeCompatibility,
    RegistryCatalog,
    SelectorFieldContract,
)
import poietics.pff.validate as validate_module
from poietics.pff.validate import ValidatedPackage, validate_package
from tests.test_pff_validate import (
    atom,
    certificate,
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


def compiler_catalog(
    *,
    challenge_kinds: frozenset[str] = frozenset(),
    face_kinds: frozenset[str] = frozenset(),
    extension_targets: tuple[ChallengeTargetContract, ...] = (),
) -> RegistryCatalog:
    authority = registry()
    extension_kinds = frozenset(
        contract.challenge_kind for contract in extension_targets
    )
    supplied_closure = CheckerContract(
        checker_id=SUPPLIED_CLOSURE_CHECKER,
        version=1,
        uses={CheckerUse.CLOSURE},
        closure_selector_kinds={
            RecordKind.ATOM,
            RecordKind.CHALLENGE,
            RecordKind.DISCHARGE,
        },
        selector_fields=(
            SelectorFieldContract(
                record_type=RecordKind.CHALLENGE,
                field="target",
                value_type=CheckerDetailType.RECORD_REF,
                allowed_record_kinds={RecordKind.FACE},
            ),
            SelectorFieldContract(
                record_type=RecordKind.DISCHARGE,
                field="challenge",
                value_type=CheckerDetailType.RECORD_REF,
                allowed_record_kinds={RecordKind.CHALLENGE},
            ),
        ),
        closure_frame_policy_id="frame:exact-package",
    )
    predicates = tuple(
        replace(
            definition,
            allowed_challenge_kinds=(
                definition.allowed_challenge_kinds
                | challenge_kinds
                | extension_kinds
            ),
            allowed_face_kinds=definition.allowed_face_kinds | face_kinds,
        )
        if definition.predicate_id == "test.derived"
        else definition
        for definition in authority.predicates
    )
    return RegistryCatalog(
        registries=(
            replace(
                authority,
                known_challenge_kinds=(
                    authority.known_challenge_kinds | extension_kinds
                ),
                predicates=predicates,
                checker_contracts=(
                    *authority.checker_contracts,
                    supplied_closure,
                ),
                challenge_target_contracts=(
                    *authority.challenge_target_contracts,
                    *extension_targets,
                ),
                discharge_compatibility=(
                    *authority.discharge_compatibility,
                    *(
                        DischargeCompatibility(
                            challenge_kind=kind,
                            admissible_discharge_kinds={"repair"},
                        )
                        for kind in sorted(extension_kinds)
                    ),
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


def supplied_blocker_closure(
    record_id: str,
    result: CheckResult,
    target: object,
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
        selector=Selector(
            record_type=RecordKind.CHALLENGE,
            where={"target": target},
        ),
    )


def face_package(
    blocker_result: CheckResult = CheckResult.PASS,
) -> Package:
    return face_graph_package(
        (("face:frame", 1, "rule:derive", 1, "closure:blockers", 1, blocker_result),)
    )


def face_graph_package(
    cases: tuple[tuple[str, int, str, int, str, int, CheckResult], ...],
) -> Package:
    seed = minimal_valid_package()
    faces_by_rule: dict[tuple[str, int], list[object]] = {}
    for face_id, face_version, rule_id, rule_version, *_ in cases:
        faces_by_rule.setdefault((rule_id, rule_version), []).append(
            ref(face_id, face_version)
        )

    rules = tuple(
        replace(
            seed.rules[0],
            id=rule_id,
            version=rule_version,
            certificate=ref(rule_id.replace("rule:", "cert:", 1), rule_version),
            faces=tuple(face_refs),
        )
        for (rule_id, rule_version), face_refs in faces_by_rule.items()
    )
    rule_index = {(rule.id, rule.version): rule for rule in rules}
    faces = tuple(
        FaceRecord(
            id=face_id,
            version=face_version,
            owner_rule=rule_index[(rule_id, rule_version)].ref,
            kind="frame",
            boundary="frame:1",
            carrier=f"entity:{position}",
            blocker_closure=ref(closure_id, closure_version),
        )
        for position, (
            face_id,
            face_version,
            rule_id,
            rule_version,
            closure_id,
            closure_version,
            _,
        ) in enumerate(cases)
    )
    closures = tuple(
        supplied_blocker_closure(
            closure_id,
            result,
            face.ref,
            version=closure_version,
        )
        for face, (*_, closure_id, closure_version, result) in zip(
            faces, cases, strict=True
        )
    )
    certificates = tuple(
        replace(
            certificate(
                f"cert:temporary:{position}",
                "rule-witness/v1",
                rule.ref,
            ),
            id=rule.certificate.id,
            version=rule.certificate.version,
        )
        for position, rule in enumerate(rules)
    )
    return replace(
        seed,
        rules=rules,
        faces=faces,
        certificates=certificates,
        closures=closures,
    )


def conjunctive_face_package() -> Package:
    return face_graph_package(
        (
            ("face:first", 1, "rule:derive", 1, "closure:first-face", 1, CheckResult.PASS),
            ("face:second", 1, "rule:derive", 1, "closure:second-face", 1, CheckResult.FAIL),
        )
    )


def alternative_face_package() -> Package:
    return face_graph_package(
        (
            ("face:z", 1, "rule:z-face", 1, "closure:z-face", 1, CheckResult.FAIL),
            ("face:a", 1, "rule:a-face", 1, "closure:a-face", 1, CheckResult.PASS),
        )
    )


def versioned_face_package() -> Package:
    return face_graph_package(
        (
            (
                "face:versioned",
                7,
                "rule:versioned-face",
                3,
                "closure:versioned-face",
                11,
                CheckResult.PASS,
            ),
            (
                "face:versioned",
                5,
                "rule:versioned-face",
                2,
                "closure:versioned-face",
                9,
                CheckResult.PASS,
            ),
        )
    )


DischargeFixture = tuple[str, int, str, CheckResult, str, int]


def challenge_package(
    *,
    challenge_kind: str = "undercut",
    face_kind: str = "frame",
    challenge_result: CheckResult = CheckResult.PASS,
    discharge_closure_result: CheckResult = CheckResult.PASS,
    discharge_rows: tuple[DischargeFixture, ...] = (),
) -> tuple[Package, RegistryCatalog]:
    """Build one decorrelated, otherwise-valid challenge fixture."""

    seed = face_graph_package(
        (
            (
                "face:target",
                5,
                "rule:owner",
                2,
                "closure:blockers",
                9,
                CheckResult.PASS,
            ),
        )
    )
    face = replace(seed.faces[0], kind=face_kind)
    challenge = ChallengeRecord(
        id="challenge:block",
        version=7,
        kind=challenge_kind,
        target_kind=RecordKind.FACE,
        target=face.ref,
        certificate=ref("cert:block", 13),
        discharge_closure=ref("closure:discharges", 11),
        contrary_atom=(
            ref("atom:rebut-effect", 31)
            if challenge_kind == "rebut"
            else None
        ),
    )
    discharges = tuple(
        DischargeRecord(
            id=record_id,
            version=version,
            challenge=challenge.ref,
            kind=kind,
            certificate=ref(certificate_id, certificate_version),
        )
        for (
            record_id,
            version,
            kind,
            _,
            certificate_id,
            certificate_version,
        ) in discharge_rows
    )
    challenge_certificate = replace(
        certificate(
            "cert:block",
            "challenge-witness/v1",
            challenge.ref,
            result=challenge_result,
        ),
        version=13,
    )
    discharge_certificates = tuple(
        replace(
            certificate(
                certificate_id,
                "discharge-witness/v1",
                discharge.ref,
                result=result,
            ),
            version=certificate_version,
        )
        for discharge, (
            _,
            _,
            _,
            result,
            certificate_id,
            certificate_version,
        ) in zip(discharges, discharge_rows, strict=True)
    )
    discharge_closure = ClosureRecord(
        id="closure:discharges",
        version=11,
        checker=SUPPLIED_CLOSURE_CHECKER,
        result=discharge_closure_result,
        cut_id="cut:1",
        frame="frame:1",
        selector=Selector(
            record_type=RecordKind.DISCHARGE,
            where={"challenge": challenge.ref},
        ),
        members=tuple(discharge.ref for discharge in discharges),
    )
    atoms = seed.atoms
    if challenge_kind == "rebut":
        atoms = (
            *atoms,
            atom(
                "atom:rebut-effect",
                "test.derived",
                version=31,
            ),
        )
    candidate = replace(
        seed,
        atoms=atoms,
        faces=(face,),
        certificates=(
            *seed.certificates,
            challenge_certificate,
            *discharge_certificates,
        ),
        closures=(*seed.closures, discharge_closure),
        challenges=(challenge,),
        discharges=discharges,
    )
    return (
        candidate,
        compiler_catalog(
            challenge_kinds=frozenset({challenge_kind}),
            face_kinds=frozenset({face_kind}),
        ),
    )


def unsupported_challenge_package(
) -> tuple[Package, RegistryCatalog, tuple[CompilationIssue, ...]]:
    """Build every deferred root with discharges that must not cascade."""

    seed = minimal_valid_package()
    extension_kind = "extension_effect"
    rows = (
        (
            "challenge:a-shared",
            2,
            extension_kind,
            "repair",
            CompilationCode.CHALLENGE_EFFECT_UNSUPPORTED,
        ),
        (
            "challenge:a-shared",
            9,
            "revoke",
            "explicit_retraction",
            CompilationCode.REVOCATION_SELECTION_UNSUPPORTED,
        ),
        (
            "challenge:b-current",
            4,
            "currentness_gap",
            "current_frontier_witness",
            CompilationCode.CURRENTNESS_TARGET_UNSUPPORTED,
        ),
        (
            "challenge:c-defect",
            6,
            "defect",
            "good_face_discharge",
            CompilationCode.PROBLEM_FACE_LIFECYCLE_UNSUPPORTED,
        ),
        (
            "challenge:d-rule-target",
            8,
            "undercut",
            "repair",
            CompilationCode.RULE_TARGET_BLOCKING_UNSUPPORTED,
        ),
    )
    challenges: list[ChallengeRecord] = []
    discharges: list[DischargeRecord] = []
    certificates = list(seed.certificates)
    closures: list[ClosureRecord] = []
    expected: list[CompilationIssue] = []
    for position, (
        challenge_id,
        challenge_version,
        challenge_kind,
        discharge_kind,
        code,
    ) in enumerate(rows):
        challenge = ChallengeRecord(
            id=challenge_id,
            version=challenge_version,
            kind=challenge_kind,
            target_kind=RecordKind.RULE,
            target=seed.rules[0].ref,
            certificate=ref(f"cert:challenge:{position}", 13 + position),
            discharge_closure=ref(f"closure:challenge:{position}", 23 + position),
            problem_face_atom=(
                seed.atoms[1].ref if challenge_kind == "defect" else None
            ),
        )
        discharge = DischargeRecord(
            id=f"discharge:root:{position}",
            version=31 + position,
            challenge=challenge.ref,
            kind=discharge_kind,
            certificate=ref(f"cert:discharge:{position}", 41 + position),
        )
        challenges.append(challenge)
        discharges.append(discharge)
        certificates.extend(
            (
                replace(
                    certificate(
                        f"cert:challenge:{position}",
                        "challenge-witness/v1",
                        challenge.ref,
                    ),
                    version=13 + position,
                ),
                replace(
                    certificate(
                        f"cert:discharge:{position}",
                        "discharge-witness/v1",
                        discharge.ref,
                    ),
                    version=41 + position,
                ),
            )
        )
        closures.append(
            ClosureRecord(
                id=f"closure:challenge:{position}",
                version=23 + position,
                checker=SUPPLIED_CLOSURE_CHECKER,
                result=CheckResult.PASS,
                cut_id="cut:1",
                frame="frame:1",
                selector=Selector(
                    record_type=RecordKind.DISCHARGE,
                    where={"challenge": challenge.ref},
                ),
                members=(discharge.ref,),
            )
        )
        expected.append(
            CompilationIssue(
                code=code,
                record_kind=RecordKind.CHALLENGE,
                ref=challenge.ref,
            )
        )

    candidate = replace(
        seed,
        certificates=tuple(certificates),
        closures=tuple(closures),
        challenges=tuple(challenges),
        discharges=tuple(discharges),
    )
    extension = ChallengeTargetContract(
        challenge_kind=extension_kind,
        allowed_target_kinds={RecordKind.RULE},
    )
    authority = compiler_catalog(
        challenge_kinds=frozenset(row[2] for row in rows),
        extension_targets=(extension,),
    )
    return candidate, authority, tuple(expected)


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


CHALLENGE_COMPILATION_ROLES = frozenset(
    {
        CompilationRole.CHALLENGE_CASE,
        CompilationRole.DISCHARGED,
        CompilationRole.OPEN_CHALLENGE,
        CompilationRole.TYPE_MATCH,
        CompilationRole.DISCHARGE_CASE,
        CompilationRole.CHALLENGE_CASE_RULE,
        CompilationRole.DISCHARGE_CASE_RULE,
        CompilationRole.DISCHARGED_BRIDGE,
        CompilationRole.OPEN_CHALLENGE_RULE,
        CompilationRole.REBUT_EFFECT,
        CompilationRole.FACE_BLOCK_EFFECT,
    }
)


def owned_challenge_slice(
    compilation: Compilation,
    owner_refs: frozenset[object],
) -> tuple[
    frozenset[str],
    frozenset[GroundRule],
    frozenset[str],
    frozenset[str],
    frozenset[str],
    tuple[ArtifactOrigin, ...],
]:
    origins = tuple(
        origin
        for origin in compilation.origins
        if origin.role in CHALLENGE_COMPILATION_ROLES
        and any(source.ref in owner_refs for source in origin.sources)
    )
    atoms = frozenset(
        origin.artifact_ref
        for origin in origins
        if origin.artifact_kind is GroundArtifactKind.ATOM
    )
    rule_ids = frozenset(
        origin.artifact_ref
        for origin in origins
        if origin.artifact_kind is GroundArtifactKind.RULE
    )
    rules = frozenset(
        rule for rule in compilation.program.rules if rule.id in rule_ids
    )
    return (
        atoms,
        rules,
        atoms & compilation.program.base_live,
        atoms & compilation.program.base_excluded,
        atoms & compilation.program.protected_open,
        origins,
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

    def test_face_program_and_source_map_match_an_independent_golden(self) -> None:
        source = validated(face_package())

        compiled = compile_package(source)

        cert_valid = "__pff__:cert-valid(cert:derive@1)"
        cert_failed = "__pff__:cert-failed(cert:derive@1)"
        cert_open = "__pff__:cert-open(cert:derive@1)"
        closure_ready = "__pff__:closure-ready(closure:blockers@1)"
        closure_failed = "__pff__:closure-failed(closure:blockers@1)"
        closure_open = "__pff__:closure-open(closure:blockers@1)"
        face = "__pff__:face(face:frame@1)"
        has_open = "__pff__:has-open-challenge(face:frame@1)"
        clear = "__pff__:clear(face:frame@1)"
        live_case = "__pff__:live-case(rule:derive@1)"
        clear_rule = "__pff__:clear-face(face:frame@1)"
        expected_program = GroundProgram(
            atoms={
                "atom:source@1",
                "atom:derived@1",
                cert_valid,
                cert_failed,
                cert_open,
                closure_ready,
                closure_failed,
                closure_open,
                face,
                has_open,
                clear,
                live_case,
            },
            rules=(
                literal_rule(
                    clear_rule,
                    clear,
                    positive={face, closure_ready},
                    negative={has_open},
                ),
                literal_rule(
                    "__pff__:rule-case(rule:derive@1)",
                    live_case,
                    positive={cert_valid, "atom:source@1", clear},
                ),
                literal_rule(
                    "__pff__:head-bridge(rule:derive@1)",
                    "atom:derived@1",
                    positive={live_case},
                ),
            ),
            base_live={"atom:source@1", cert_valid, closure_ready, face},
        )
        origin_rows = (
            (GroundArtifactKind.ATOM, cert_failed, CompilationRole.CERT_FAILED, RecordKind.CERTIFICATE, "cert:derive"),
            (GroundArtifactKind.ATOM, cert_open, CompilationRole.CERT_OPEN, RecordKind.CERTIFICATE, "cert:derive"),
            (GroundArtifactKind.ATOM, cert_valid, CompilationRole.CERT_VALID, RecordKind.CERTIFICATE, "cert:derive"),
            (GroundArtifactKind.ATOM, clear, CompilationRole.CLEAR, RecordKind.FACE, "face:frame"),
            (GroundArtifactKind.ATOM, closure_failed, CompilationRole.CLOSURE_FAILED, RecordKind.CLOSURE, "closure:blockers"),
            (GroundArtifactKind.ATOM, closure_open, CompilationRole.CLOSURE_OPEN, RecordKind.CLOSURE, "closure:blockers"),
            (GroundArtifactKind.ATOM, closure_ready, CompilationRole.CLOSURE_READY, RecordKind.CLOSURE, "closure:blockers"),
            (GroundArtifactKind.ATOM, face, CompilationRole.FACE, RecordKind.FACE, "face:frame"),
            (GroundArtifactKind.ATOM, has_open, CompilationRole.HAS_OPEN_CHALLENGE, RecordKind.FACE, "face:frame"),
            (GroundArtifactKind.ATOM, live_case, CompilationRole.LIVE_CASE, RecordKind.RULE, "rule:derive"),
            (GroundArtifactKind.ATOM, "atom:derived@1", CompilationRole.SOURCE_ATOM, RecordKind.ATOM, "atom:derived"),
            (GroundArtifactKind.ATOM, "atom:source@1", CompilationRole.SOURCE_ATOM, RecordKind.ATOM, "atom:source"),
            (GroundArtifactKind.RULE, clear_rule, CompilationRole.CLEAR_FACE, RecordKind.FACE, "face:frame"),
            (GroundArtifactKind.RULE, "__pff__:head-bridge(rule:derive@1)", CompilationRole.HEAD_BRIDGE, RecordKind.RULE, "rule:derive"),
            (GroundArtifactKind.RULE, "__pff__:rule-case(rule:derive@1)", CompilationRole.RULE_CASE, RecordKind.RULE, "rule:derive"),
        )
        expected_origins = tuple(literal_origin(*row) for row in origin_rows)

        self.assertIs(compiled.source, source)
        self.assertEqual(compiled.program, expected_program)
        for origin in expected_origins:
            self.assertEqual(
                compiled.origin_for(origin.artifact_kind, origin.artifact_ref),
                origin,
                f"ORIGIN_MISMATCH:{origin.artifact_ref}",
            )
        self.assertEqual(compiled.origins, expected_origins)

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

    def test_face_blocker_closure_results_drive_clearance(self) -> None:
        expected = {
            CheckResult.PASS: (
                Status.LIVE,
                Status.EXCLUDED,
                Status.EXCLUDED,
            ),
            CheckResult.FAIL: (
                Status.SUSPENDED,
                Status.LIVE,
                Status.EXCLUDED,
            ),
            CheckResult.OPEN: (
                Status.SUSPENDED,
                Status.EXCLUDED,
                Status.LIVE,
            ),
        }
        ready = "__pff__:closure-ready(closure:blockers@1)"
        failed = "__pff__:closure-failed(closure:blockers@1)"
        opened = "__pff__:closure-open(closure:blockers@1)"
        face = "__pff__:face(face:frame@1)"
        blocker = "__pff__:has-open-challenge(face:frame@1)"
        clear = "__pff__:clear(face:frame@1)"
        live_case = "__pff__:live-case(rule:derive@1)"

        for closure_result, statuses in expected.items():
            with self.subTest(closure_result=closure_result):
                compiled = compile_package(
                    validated(face_package(closure_result))
                )
                result = evaluate(compiled.program)
                clear_status, failed_status, open_status = statuses

                self.assertEqual(result.status_of(face), Status.LIVE)
                self.assertEqual(result.status_of(blocker), Status.EXCLUDED)
                self.assertEqual(result.status_of(clear), clear_status)
                self.assertEqual(result.status_of(live_case), clear_status)
                self.assertEqual(result.status_of("atom:derived@1"), clear_status)
                self.assertEqual(result.status_of(failed), failed_status)
                self.assertEqual(result.status_of(opened), open_status)
                self.assertEqual(
                    ready in compiled.program.base_live,
                    closure_result is CheckResult.PASS,
                )
                self.assertEqual(
                    ready in compiled.program.protected_open,
                    closure_result in {CheckResult.FAIL, CheckResult.OPEN},
                )

    def test_multiple_faces_are_conjunctive_in_one_rule_case(self) -> None:
        compiled = compile_package(validated(conjunctive_face_package()))
        evaluation = evaluate(compiled.program)
        rule_case = next(
            rule
            for rule in compiled.program.rules
            if rule.id == "__pff__:rule-case(rule:derive@1)"
        )

        for expected_guard in (
            "__pff__:clear(face:first@1)",
            "__pff__:clear(face:second@1)",
        ):
            self.assertIn(
                expected_guard,
                rule_case.positive,
                f"MISSING_FACE_GUARD:{expected_guard}",
            )
        self.assertEqual(
            rule_case.positive,
            {
                "__pff__:cert-valid(cert:derive@1)",
                "atom:source@1",
                "__pff__:clear(face:first@1)",
                "__pff__:clear(face:second@1)",
            },
        )
        self.assertEqual(
            evaluation.status_of("__pff__:clear(face:first@1)"),
            Status.LIVE,
        )
        self.assertEqual(
            evaluation.status_of("__pff__:clear(face:second@1)"),
            Status.SUSPENDED,
        )
        self.assertEqual(
            evaluation.status_of("__pff__:live-case(rule:derive@1)"),
            Status.SUSPENDED,
        )
        self.assertEqual(
            evaluation.status_of("atom:derived@1"),
            Status.SUSPENDED,
        )

    def test_same_head_face_alternatives_remain_independent(self) -> None:
        compiled = compile_package(validated(alternative_face_package()))
        evaluation = evaluate(compiled.program)
        expected_cases = {
            literal_rule(
                "__pff__:rule-case(rule:a-face@1)",
                "__pff__:live-case(rule:a-face@1)",
                positive={
                    "__pff__:cert-valid(cert:a-face@1)",
                    "atom:source@1",
                    "__pff__:clear(face:a@1)",
                },
            ),
            literal_rule(
                "__pff__:rule-case(rule:z-face@1)",
                "__pff__:live-case(rule:z-face@1)",
                positive={
                    "__pff__:cert-valid(cert:z-face@1)",
                    "atom:source@1",
                    "__pff__:clear(face:z@1)",
                },
            ),
        }

        self.assertEqual(
            {
                rule
                for rule in compiled.program.rules
                if str(rule.id).startswith("__pff__:rule-case(")
            },
            expected_cases,
        )
        self.assertEqual(
            evaluation.status_of("__pff__:live-case(rule:a-face@1)"),
            Status.LIVE,
        )
        self.assertEqual(
            evaluation.status_of("__pff__:live-case(rule:z-face@1)"),
            Status.SUSPENDED,
        )
        self.assertEqual(evaluation.status_of("atom:derived@1"), Status.LIVE)

    def test_face_blocker_atom_composes_with_successor_rules(self) -> None:
        compiled = compile_package(validated(face_package()))
        original = evaluate(compiled.program)
        blocker = "__pff__:has-open-challenge(face:frame@1)"
        clear = "__pff__:clear(face:frame@1)"
        live_case = "__pff__:live-case(rule:derive@1)"
        successor_atom = "__pff__:open-challenge(challenge:future@1)"
        successor_rule = literal_rule(
            "__pff__:successor-face-blocker(challenge:future@1)",
            blocker,
            positive={successor_atom},
        )

        self.assertEqual(original.status_of(clear), Status.LIVE)
        self.assertEqual(original.status_of("atom:derived@1"), Status.LIVE)
        cases = (
            ("live", {successor_atom}, set(), Status.LIVE, Status.EXCLUDED),
            (
                "protected-open",
                set(),
                {successor_atom},
                Status.SUSPENDED,
                Status.SUSPENDED,
            ),
        )
        for label, extra_live, extra_open, blocker_status, clear_status in cases:
            with self.subTest(label=label):
                successor_program = GroundProgram(
                    atoms={*compiled.program.atoms, successor_atom},
                    rules=(*compiled.program.rules, successor_rule),
                    base_live={*compiled.program.base_live, *extra_live},
                    base_excluded=compiled.program.base_excluded,
                    protected_open={
                        *compiled.program.protected_open,
                        *extra_open,
                    },
                )
                result = evaluate(successor_program)

                self.assertEqual(result.status_of(blocker), blocker_status)
                self.assertEqual(result.status_of(clear), clear_status)
                self.assertEqual(result.status_of(live_case), clear_status)
                self.assertEqual(
                    result.status_of("atom:derived@1"),
                    clear_status,
                )


class ChallengeAndDischargeLoweringTests(unittest.TestCase):
    def test_public_roles_codes_and_generic_lowering_match_literal_goldens(
        self,
    ) -> None:
        expected_roles = {
            "CHALLENGE_CASE": "challenge-case",
            "DISCHARGED": "discharged",
            "OPEN_CHALLENGE": "open-challenge",
            "TYPE_MATCH": "type-match",
            "DISCHARGE_CASE": "discharge-case",
            "CHALLENGE_CASE_RULE": "challenge-case-rule",
            "DISCHARGE_CASE_RULE": "discharge-case-rule",
            "DISCHARGED_BRIDGE": "discharged-bridge",
            "OPEN_CHALLENGE_RULE": "open-challenge-rule",
            "REBUT_EFFECT": "rebut-effect",
            "FACE_BLOCK_EFFECT": "face-block-effect",
        }
        self.assertEqual(
            {
                name: CompilationRole[name].value
                for name in expected_roles
            },
            expected_roles,
        )
        self.assertEqual(
            {member.name: member.value for member in CompilationCode},
            {
                "UNSUPPORTED_RECORD_KIND": "unsupported_record_kind",
                "RULE_TARGET_BLOCKING_UNSUPPORTED": (
                    "rule_target_blocking_unsupported"
                ),
                "REVOCATION_SELECTION_UNSUPPORTED": (
                    "revocation_selection_unsupported"
                ),
                "CURRENTNESS_TARGET_UNSUPPORTED": (
                    "currentness_target_unsupported"
                ),
                "PROBLEM_FACE_LIFECYCLE_UNSUPPORTED": (
                    "problem_face_lifecycle_unsupported"
                ),
                "CHALLENGE_EFFECT_UNSUPPORTED": (
                    "challenge_effect_unsupported"
                ),
            },
        )

        candidate, authority = challenge_package(
            discharge_rows=(
                (
                    "discharge:repair",
                    17,
                    "repair",
                    CheckResult.PASS,
                    "cert:repair",
                    19,
                ),
                (
                    "discharge:mismatch",
                    23,
                    "recovery_witness",
                    CheckResult.PASS,
                    "cert:mismatch",
                    29,
                ),
            ),
        )
        compiled = compile_package(validate_package(candidate, authority))

        challenge_case = "__pff__:challenge-case(challenge:block@7)"
        discharged = "__pff__:discharged(challenge:block@7)"
        open_challenge = "__pff__:open-challenge(challenge:block@7)"
        repair_match = "__pff__:type-match(discharge:repair@17)"
        repair_case = "__pff__:discharge-case(discharge:repair@17)"
        mismatch_match = "__pff__:type-match(discharge:mismatch@23)"
        mismatch_case = "__pff__:discharge-case(discharge:mismatch@23)"
        expected_atoms = {
            challenge_case,
            discharged,
            open_challenge,
            repair_match,
            repair_case,
            mismatch_match,
            mismatch_case,
        }
        expected_rules = {
            literal_rule(
                "__pff__:challenge-case-rule(challenge:block@7)",
                challenge_case,
                positive={"__pff__:cert-valid(cert:block@13)"},
            ),
            literal_rule(
                "__pff__:open-challenge-rule(challenge:block@7)",
                open_challenge,
                positive={
                    challenge_case,
                    "__pff__:closure-ready(closure:discharges@11)",
                },
                negative={discharged},
            ),
            literal_rule(
                "__pff__:face-block-effect(challenge:block@7)",
                "__pff__:has-open-challenge(face:target@5)",
                positive={open_challenge},
            ),
            literal_rule(
                "__pff__:discharge-case-rule(discharge:repair@17)",
                repair_case,
                positive={
                    "__pff__:cert-valid(cert:repair@19)",
                    repair_match,
                },
            ),
            literal_rule(
                "__pff__:discharged-bridge(discharge:repair@17)",
                discharged,
                positive={repair_case},
            ),
            literal_rule(
                "__pff__:discharge-case-rule(discharge:mismatch@23)",
                mismatch_case,
                positive={
                    "__pff__:cert-valid(cert:mismatch@29)",
                    mismatch_match,
                },
            ),
            literal_rule(
                "__pff__:discharged-bridge(discharge:mismatch@23)",
                discharged,
                positive={mismatch_case},
            ),
        }
        challenge_owner_refs = frozenset(
            {
                candidate.challenges[0].ref,
                *(discharge.ref for discharge in candidate.discharges),
            }
        )
        actual_origins = tuple(
            origin
            for origin in compiled.origins
            if any(
                source.ref in challenge_owner_refs
                for source in origin.sources
            )
        )
        expected_origins = {
            literal_origin(
                GroundArtifactKind.ATOM,
                challenge_case,
                CompilationRole.CHALLENGE_CASE,
                RecordKind.CHALLENGE,
                "challenge:block",
                7,
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                discharged,
                CompilationRole.DISCHARGED,
                RecordKind.CHALLENGE,
                "challenge:block",
                7,
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                open_challenge,
                CompilationRole.OPEN_CHALLENGE,
                RecordKind.CHALLENGE,
                "challenge:block",
                7,
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                repair_match,
                CompilationRole.TYPE_MATCH,
                RecordKind.DISCHARGE,
                "discharge:repair",
                17,
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                repair_case,
                CompilationRole.DISCHARGE_CASE,
                RecordKind.DISCHARGE,
                "discharge:repair",
                17,
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                mismatch_match,
                CompilationRole.TYPE_MATCH,
                RecordKind.DISCHARGE,
                "discharge:mismatch",
                23,
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                mismatch_case,
                CompilationRole.DISCHARGE_CASE,
                RecordKind.DISCHARGE,
                "discharge:mismatch",
                23,
            ),
        }
        for artifact, role in (
            (
                "__pff__:challenge-case-rule(challenge:block@7)",
                CompilationRole.CHALLENGE_CASE_RULE,
            ),
            (
                "__pff__:open-challenge-rule(challenge:block@7)",
                CompilationRole.OPEN_CHALLENGE_RULE,
            ),
            (
                "__pff__:face-block-effect(challenge:block@7)",
                CompilationRole.FACE_BLOCK_EFFECT,
            ),
        ):
            expected_origins.add(
                literal_origin(
                    GroundArtifactKind.RULE,
                    artifact,
                    role,
                    RecordKind.CHALLENGE,
                    "challenge:block",
                    7,
                )
            )
        for record_id, version in (
            ("discharge:repair", 17),
            ("discharge:mismatch", 23),
        ):
            expected_origins.update(
                {
                    literal_origin(
                        GroundArtifactKind.RULE,
                        f"__pff__:discharge-case-rule({record_id}@{version})",
                        CompilationRole.DISCHARGE_CASE_RULE,
                        RecordKind.DISCHARGE,
                        record_id,
                        version,
                    ),
                    literal_origin(
                        GroundArtifactKind.RULE,
                        f"__pff__:discharged-bridge({record_id}@{version})",
                        CompilationRole.DISCHARGED_BRIDGE,
                        RecordKind.DISCHARGE,
                        record_id,
                        version,
                    ),
                }
            )

        self.assertEqual(
            {
                origin.artifact_ref
                for origin in actual_origins
                if origin.artifact_kind is GroundArtifactKind.ATOM
            },
            expected_atoms,
        )
        self.assertEqual(
            {
                rule
                for rule in compiled.program.rules
                if rule.id
                in {
                    origin.artifact_ref
                    for origin in actual_origins
                    if origin.artifact_kind is GroundArtifactKind.RULE
                }
            },
            expected_rules,
        )
        self.assertEqual(set(actual_origins), expected_origins)
        self.assertEqual(len(actual_origins), 14)
        self.assertTrue(all(len(origin.sources) == 1 for origin in actual_origins))
        self.assertEqual(
            expected_atoms & compiled.program.base_live,
            {repair_match},
        )
        self.assertEqual(
            expected_atoms & compiled.program.base_excluded,
            {mismatch_match},
        )
        self.assertEqual(
            expected_atoms & compiled.program.protected_open,
            set(),
        )
        self.assertEqual(
            compiled.origin_for(
                GroundArtifactKind.ATOM,
                "__pff__:has-open-challenge(face:target@5)",
            ),
            literal_origin(
                GroundArtifactKind.ATOM,
                "__pff__:has-open-challenge(face:target@5)",
                CompilationRole.HAS_OPEN_CHALLENGE,
                RecordKind.FACE,
                "face:target",
                5,
            ),
        )

    def test_every_admitted_blocking_kind_uses_the_same_face_effect_branch(
        self,
    ) -> None:
        expected_effect = literal_rule(
            "__pff__:face-block-effect(challenge:block@7)",
            "__pff__:has-open-challenge(face:target@5)",
            positive={"__pff__:open-challenge(challenge:block@7)"},
        )
        cases = (
            ("undercut", "frame"),
            ("wound", "frame"),
            ("localisation_gap", "localisation"),
            ("recovery_gap", "recovery"),
            ("closure_gap", "closure"),
        )
        for challenge_kind, face_kind in cases:
            with self.subTest(challenge_kind=challenge_kind):
                candidate, authority = challenge_package(
                    challenge_kind=challenge_kind,
                    face_kind=face_kind,
                )
                compiled = compile_package(
                    validate_package(candidate, authority)
                )

                self.assertIn(expected_effect, compiled.program.rules)
                self.assertEqual(
                    compiled.origin_for(
                        GroundArtifactKind.RULE,
                        "__pff__:face-block-effect(challenge:block@7)",
                    ),
                    literal_origin(
                        GroundArtifactKind.RULE,
                        "__pff__:face-block-effect(challenge:block@7)",
                        CompilationRole.FACE_BLOCK_EFFECT,
                        RecordKind.CHALLENGE,
                        "challenge:block",
                        7,
                    ),
                )
                self.assertNotIn(
                    "__pff__:rebut-effect(challenge:block@7)",
                    {str(rule.id) for rule in compiled.program.rules},
                )

    def test_rebut_effect_mirrors_open_challenge_without_blocking_target(
        self,
    ) -> None:
        expected_effect = literal_rule(
            "__pff__:rebut-effect(challenge:block@7)",
            "atom:rebut-effect@31",
            positive={"__pff__:open-challenge(challenge:block@7)"},
        )
        for certificate_result, expected_status in (
            (CheckResult.PASS, Status.LIVE),
            (CheckResult.FAIL, Status.EXCLUDED),
            (CheckResult.OPEN, Status.SUSPENDED),
        ):
            with self.subTest(certificate_result=certificate_result):
                candidate, authority = challenge_package(
                    challenge_kind="rebut",
                    challenge_result=certificate_result,
                )
                compiled = compile_package(
                    validate_package(candidate, authority)
                )
                result = evaluate(compiled.program)

                self.assertIn(expected_effect, compiled.program.rules)
                self.assertEqual(
                    result.status_of(
                        "__pff__:open-challenge(challenge:block@7)"
                    ),
                    expected_status,
                )
                self.assertEqual(
                    result.status_of("atom:rebut-effect@31"),
                    expected_status,
                )
                self.assertEqual(
                    result.status_of(
                        "__pff__:has-open-challenge(face:target@5)"
                    ),
                    Status.EXCLUDED,
                )
                self.assertEqual(
                    result.status_of("__pff__:clear(face:target@5)"),
                    Status.LIVE,
                )
                self.assertEqual(
                    result.status_of("atom:derived@1"),
                    Status.LIVE,
                )
                self.assertEqual(
                    compiled.origin_for(
                        GroundArtifactKind.RULE,
                        "__pff__:rebut-effect(challenge:block@7)",
                    ),
                    literal_origin(
                        GroundArtifactKind.RULE,
                        "__pff__:rebut-effect(challenge:block@7)",
                        CompilationRole.REBUT_EFFECT,
                        RecordKind.CHALLENGE,
                        "challenge:block",
                        7,
                    ),
                )

    def test_all_eleven_status_rows_match_the_accepted_table(self) -> None:
        rows = (
            (
                "challenge-pass-no-discharge",
                CheckResult.PASS,
                CheckResult.PASS,
                None,
                None,
                (Status.LIVE, Status.EXCLUDED, Status.LIVE, Status.LIVE, Status.EXCLUDED, Status.EXCLUDED),
            ),
            (
                "challenge-fail",
                CheckResult.FAIL,
                CheckResult.PASS,
                None,
                None,
                (Status.EXCLUDED, Status.EXCLUDED, Status.EXCLUDED, Status.EXCLUDED, Status.LIVE, Status.LIVE),
            ),
            (
                "challenge-open",
                CheckResult.OPEN,
                CheckResult.PASS,
                None,
                None,
                (Status.SUSPENDED, Status.EXCLUDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED),
            ),
            (
                "closure-fail",
                CheckResult.PASS,
                CheckResult.FAIL,
                None,
                None,
                (Status.LIVE, Status.EXCLUDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED),
            ),
            (
                "closure-open",
                CheckResult.PASS,
                CheckResult.OPEN,
                None,
                None,
                (Status.LIVE, Status.EXCLUDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED),
            ),
            (
                "compatible-pass",
                CheckResult.PASS,
                CheckResult.PASS,
                "repair",
                CheckResult.PASS,
                (Status.LIVE, Status.LIVE, Status.EXCLUDED, Status.EXCLUDED, Status.LIVE, Status.LIVE),
            ),
            (
                "compatible-fail",
                CheckResult.PASS,
                CheckResult.PASS,
                "repair",
                CheckResult.FAIL,
                (Status.LIVE, Status.EXCLUDED, Status.LIVE, Status.LIVE, Status.EXCLUDED, Status.EXCLUDED),
            ),
            (
                "compatible-open",
                CheckResult.PASS,
                CheckResult.PASS,
                "repair",
                CheckResult.OPEN,
                (Status.LIVE, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED, Status.SUSPENDED),
            ),
            (
                "incompatible-pass",
                CheckResult.PASS,
                CheckResult.PASS,
                "recovery_witness",
                CheckResult.PASS,
                (Status.LIVE, Status.EXCLUDED, Status.LIVE, Status.LIVE, Status.EXCLUDED, Status.EXCLUDED),
            ),
            (
                "incompatible-open",
                CheckResult.PASS,
                CheckResult.PASS,
                "recovery_witness",
                CheckResult.OPEN,
                (Status.LIVE, Status.EXCLUDED, Status.LIVE, Status.LIVE, Status.EXCLUDED, Status.EXCLUDED),
            ),
            (
                "challenge-open-compatible-pass",
                CheckResult.OPEN,
                CheckResult.PASS,
                "repair",
                CheckResult.PASS,
                (Status.SUSPENDED, Status.LIVE, Status.EXCLUDED, Status.EXCLUDED, Status.LIVE, Status.LIVE),
            ),
        )
        status_atoms = (
            "__pff__:challenge-case(challenge:block@7)",
            "__pff__:discharged(challenge:block@7)",
            "__pff__:open-challenge(challenge:block@7)",
            "__pff__:has-open-challenge(face:target@5)",
            "__pff__:clear(face:target@5)",
            "atom:derived@1",
        )
        for (
            label,
            challenge_result,
            closure_result,
            discharge_kind,
            discharge_result,
            expected,
        ) in rows:
            with self.subTest(label=label):
                discharge_rows: tuple[DischargeFixture, ...] = ()
                if discharge_kind is not None and discharge_result is not None:
                    discharge_rows = (
                        (
                            "discharge:row",
                            17,
                            discharge_kind,
                            discharge_result,
                            "cert:row",
                            19,
                        ),
                    )
                candidate, authority = challenge_package(
                    challenge_result=challenge_result,
                    discharge_closure_result=closure_result,
                    discharge_rows=discharge_rows,
                )

                evaluation = evaluate(
                    compile_package(
                        validate_package(candidate, authority)
                    ).program
                )

                self.assertEqual(
                    tuple(evaluation.status_of(atom_id) for atom_id in status_atoms),
                    expected,
                )

    def test_multiple_discharges_are_alternative_bridges_not_conjuncts(self) -> None:
        cases = (
            (
                "any-live",
                (
                    ("discharge:first", 17, "repair", CheckResult.PASS, "cert:first", 19),
                    ("discharge:second", 23, "malformed_or_inapplicable", CheckResult.FAIL, "cert:second", 29),
                ),
                Status.LIVE,
                Status.EXCLUDED,
                Status.LIVE,
            ),
            (
                "suspended-without-live",
                (
                    ("discharge:first", 17, "repair", CheckResult.OPEN, "cert:first", 19),
                    ("discharge:second", 23, "malformed_or_inapplicable", CheckResult.FAIL, "cert:second", 29),
                ),
                Status.SUSPENDED,
                Status.SUSPENDED,
                Status.SUSPENDED,
            ),
            (
                "all-excluded",
                (
                    ("discharge:first", 17, "repair", CheckResult.FAIL, "cert:first", 19),
                    ("discharge:second", 23, "recovery_witness", CheckResult.PASS, "cert:second", 29),
                ),
                Status.EXCLUDED,
                Status.LIVE,
                Status.EXCLUDED,
            ),
        )
        for label, discharge_rows, discharged_status, open_status, head_status in cases:
            with self.subTest(label=label):
                candidate, authority = challenge_package(
                    discharge_rows=discharge_rows,
                )
                compiled = compile_package(
                    validate_package(candidate, authority)
                )
                evaluation = evaluate(compiled.program)
                bridges = {
                    rule
                    for rule in compiled.program.rules
                    if str(rule.id).startswith("__pff__:discharged-bridge(")
                }

                self.assertEqual(
                    bridges,
                    {
                        literal_rule(
                            "__pff__:discharged-bridge(discharge:first@17)",
                            "__pff__:discharged(challenge:block@7)",
                            positive={
                                "__pff__:discharge-case(discharge:first@17)"
                            },
                        ),
                        literal_rule(
                            "__pff__:discharged-bridge(discharge:second@23)",
                            "__pff__:discharged(challenge:block@7)",
                            positive={
                                "__pff__:discharge-case(discharge:second@23)"
                            },
                        ),
                    },
                )
                self.assertEqual(
                    evaluation.status_of(
                        "__pff__:discharged(challenge:block@7)"
                    ),
                    discharged_status,
                )
                self.assertEqual(
                    evaluation.status_of(
                        "__pff__:open-challenge(challenge:block@7)"
                    ),
                    open_status,
                )
                self.assertEqual(
                    evaluation.status_of("atom:derived@1"),
                    head_status,
                )

    def test_versions_permutations_and_unrelated_insertion_preserve_owner_slice(
        self,
    ) -> None:
        candidate, authority = challenge_package(
            discharge_rows=(
                ("discharge:repair", 17, "repair", CheckResult.PASS, "cert:repair", 19),
                ("discharge:mismatch", 23, "recovery_witness", CheckResult.PASS, "cert:mismatch", 29),
            ),
        )
        original_owners = frozenset(
            {
                candidate.challenges[0].ref,
                *(discharge.ref for discharge in candidate.discharges),
            }
        )
        original = compile_package(validate_package(candidate, authority))
        permuted = replace(
            candidate,
            atoms=tuple(reversed(candidate.atoms)),
            rules=tuple(reversed(candidate.rules)),
            faces=tuple(reversed(candidate.faces)),
            certificates=tuple(reversed(candidate.certificates)),
            closures=tuple(reversed(candidate.closures)),
            challenges=tuple(reversed(candidate.challenges)),
            discharges=tuple(reversed(candidate.discharges)),
            header=replace(
                candidate.header,
                parent_package_hash="sha256:challenge-permutation",
                metadata={"order": [29, 5, 13, 7]},
            ),
        )
        reordered = compile_package(validate_package(permuted, authority))
        self.assertEqual(
            owned_challenge_slice(reordered, original_owners),
            owned_challenge_slice(original, original_owners),
        )

        unrelated = ChallengeRecord(
            id="challenge:aaa-unrelated",
            version=3,
            kind="undercut",
            target_kind=RecordKind.FACE,
            target=candidate.faces[0].ref,
            certificate=ref("cert:unrelated", 4),
            discharge_closure=ref("closure:unrelated", 6),
        )
        unrelated_certificate = replace(
            certificate(
                "cert:unrelated",
                "challenge-witness/v1",
                unrelated.ref,
            ),
            version=4,
        )
        unrelated_closure = ClosureRecord(
            id="closure:unrelated",
            version=6,
            checker=SUPPLIED_CLOSURE_CHECKER,
            result=CheckResult.PASS,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.DISCHARGE,
                where={"challenge": unrelated.ref},
            ),
        )
        inserted_candidate = replace(
            candidate,
            challenges=(unrelated, *candidate.challenges),
            certificates=(*candidate.certificates, unrelated_certificate),
            closures=(*candidate.closures, unrelated_closure),
        )
        inserted = compile_package(
            validate_package(inserted_candidate, authority)
        )

        self.assertEqual(
            owned_challenge_slice(inserted, original_owners),
            owned_challenge_slice(original, original_owners),
        )
        for literal in (
            "__pff__:challenge-case(challenge:block@7)",
            "__pff__:type-match(discharge:repair@17)",
            "__pff__:discharge-case(discharge:mismatch@23)",
            "__pff__:open-challenge-rule(challenge:block@7)",
        ):
            artifact_kind = (
                GroundArtifactKind.RULE
                if "-rule(" in literal
                else GroundArtifactKind.ATOM
            )
            self.assertEqual(
                inserted.origin_for(artifact_kind, literal),
                original.origin_for(artifact_kind, literal),
            )


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

    def test_face_versions_order_and_origins_are_exact(self) -> None:
        candidate = versioned_face_package()
        reordered = replace(
            candidate,
            rules=tuple(reversed(candidate.rules)),
            faces=tuple(reversed(candidate.faces)),
            certificates=tuple(reversed(candidate.certificates)),
            closures=tuple(reversed(candidate.closures)),
            header=replace(
                candidate.header,
                parent_package_hash="sha256:face-order",
                metadata={"display": {"faces": [2, 1]}},
            ),
        )

        first = compile_package(validated(candidate))
        second = compile_package(validated(reordered))

        self.assertEqual(semantic_artifacts(first), semantic_artifacts(second))
        self.assertNotEqual(first, second)
        cases = ((5, 2, 9, 7), (7, 3, 11, 5))
        for face_version, rule_version, closure_version, other_face_version in cases:
            face = f"__pff__:face(face:versioned@{face_version})"
            blocker = (
                "__pff__:has-open-challenge"
                f"(face:versioned@{face_version})"
            )
            clear = f"__pff__:clear(face:versioned@{face_version})"
            clear_rule = f"__pff__:clear-face(face:versioned@{face_version})"
            rule_case = f"__pff__:rule-case(rule:versioned-face@{rule_version})"
            live_case = f"__pff__:live-case(rule:versioned-face@{rule_version})"

            self.assertIn(face, first.program.base_live)
            self.assertIn(blocker, first.program.atoms)
            self.assertIn(clear, first.program.atoms)
            self.assertIn(clear_rule, {str(rule.id) for rule in first.program.rules})
            for kind, artifact, role in (
                (GroundArtifactKind.ATOM, face, CompilationRole.FACE),
                (GroundArtifactKind.ATOM, blocker, CompilationRole.HAS_OPEN_CHALLENGE),
                (GroundArtifactKind.ATOM, clear, CompilationRole.CLEAR),
                (GroundArtifactKind.RULE, clear_rule, CompilationRole.CLEAR_FACE),
            ):
                self.assertEqual(
                    first.origin_for(kind, artifact),
                    literal_origin(
                        kind,
                        artifact,
                        role,
                        RecordKind.FACE,
                        "face:versioned",
                        face_version,
                    ),
                )
            compiled_clear = next(
                rule for rule in first.program.rules if rule.id == clear_rule
            )
            self.assertIn(
                f"__pff__:closure-ready(closure:versioned-face@{closure_version})",
                compiled_clear.positive,
            )
            compiled_case = next(
                rule for rule in first.program.rules if rule.id == rule_case
            )
            self.assertEqual(compiled_case.head, live_case)
            self.assertIn(clear, compiled_case.positive)
            self.assertNotIn(
                f"__pff__:clear(face:versioned@{other_face_version})",
                compiled_case.positive,
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

    def test_deferred_challenges_preflight_once_per_root_without_cascades(
        self,
    ) -> None:
        candidate, authority, expected = unsupported_challenge_package()
        candidates = (
            candidate,
            replace(
                candidate,
                certificates=tuple(reversed(candidate.certificates)),
                closures=tuple(reversed(candidate.closures)),
                challenges=tuple(reversed(candidate.challenges)),
                discharges=tuple(reversed(candidate.discharges)),
            ),
        )
        for position, ordered in enumerate(candidates):
            with self.subTest(position=position):
                source = validate_package(ordered, authority)
                with (
                    patch.object(
                        compile_module,
                        "_CompilationBuilder",
                        side_effect=AssertionError("partial builder constructed"),
                    ) as builder,
                    self.assertRaises(PackageCompilationError) as caught,
                ):
                    compile_package(source)

                self.assertEqual(caught.exception.issues, expected)
                self.assertEqual(len(caught.exception.issues), 5)
                self.assertTrue(
                    all(
                        issue.record_kind is RecordKind.CHALLENGE
                        for issue in caught.exception.issues
                    )
                )
                self.assertNotIn(
                    CompilationCode.UNSUPPORTED_RECORD_KIND,
                    {issue.code for issue in caught.exception.issues},
                )
                builder.assert_not_called()

    def test_compiler_does_not_call_validation_checker_or_evaluator(self) -> None:
        candidate, authority = challenge_package(
            discharge_rows=(
                (
                    "discharge:repair",
                    17,
                    "repair",
                    CheckResult.PASS,
                    "cert:repair",
                    19,
                ),
            ),
        )
        source = validate_package(candidate, authority)
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
                "ChallengeRecord",
                "CheckResult",
                "ClosureRecord",
                "ContraryRecord",
                "DischargeRecord",
                "FaceRecord",
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
