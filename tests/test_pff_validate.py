from __future__ import annotations

import ast
import inspect
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from itertools import permutations

from poietics.pff.model import (
    AtomRecord,
    BasePartition,
    CertificateRecord,
    ChallengeRecord,
    CheckResult,
    ClosureRecord,
    ContraryRecord,
    DischargeRecord,
    FaceRecord,
    Package,
    PackageHeader,
    RecordKind,
    RecordRef,
    RuleRecord,
    Selector,
    VersionToken,
)
from poietics.pff.registry import (
    ArgumentTypeContract,
    CheckerContract,
    CheckerDetailField,
    CheckerDetailType,
    CheckerUse,
    ComputabilityClass,
    ContraryPolicy,
    ContraryPolicyMode,
    FramePolicy,
    FramePolicyMode,
    GradePolicy,
    LocalClosureSemantics,
    PredicateDefinition,
    PredicateRegistry,
    RegistryCatalog,
    SelectorFieldContract,
)
from poietics.pff.validate import (
    PackageValidationError,
    ValidatedPackage,
    ValidationCode,
    ValidationIssue,
    ValidationPhase,
    validate_package,
)
import poietics.pff.validate as validate_module
import poietics.pff.local_checkers as local_checkers_module


def ref(record_id: str, version: int = 1) -> RecordRef:
    return RecordRef(record_id, version)


def predicate(
    predicate_id: str,
    *,
    primitive_allowed: bool,
    grade_policy: GradePolicy = GradePolicy.FORBIDDEN,
    contrary_policy_id: str = "contrary:forbidden",
    allowed_face_kinds: frozenset[str] = frozenset(),
    allowed_challenge_kinds: frozenset[str] = frozenset(),
    checker_contract_ids: frozenset[str] = frozenset({"rule-witness/v1"}),
) -> PredicateDefinition:
    return PredicateDefinition(
        predicate_id=predicate_id,
        version=1,
        arg_type_ids=("entity_ref",),
        frame_policy_id="frame:exact-package",
        grade_policy=grade_policy,
        computability_class=ComputabilityClass.FIN,
        primitive_allowed=primitive_allowed,
        allowed_face_kinds=allowed_face_kinds,
        allowed_challenge_kinds=allowed_challenge_kinds,
        checker_contract_ids=checker_contract_ids,
        contrary_policy_id=contrary_policy_id,
    )


def registry() -> PredicateRegistry:
    return PredicateRegistry(
        registry_id="test-registry/1",
        version=1,
        argument_types=(
            ArgumentTypeContract(
                argument_type_id="entity_ref",
                version=1,
                required_prefix="entity:",
            ),
        ),
        frame_policies=(
            FramePolicy(
                frame_policy_id="frame:exact-package",
                version=1,
                mode=FramePolicyMode.EXACT_PACKAGE,
            ),
        ),
        contrary_policies=(
            ContraryPolicy(
                contrary_policy_id="contrary:forbidden",
                version=1,
                mode=ContraryPolicyMode.FORBIDDEN,
                include_frame=False,
            ),
            ContraryPolicy(
                contrary_policy_id="contrary:entity-frame",
                version=1,
                mode=ContraryPolicyMode.STABLE_COMPARISON_BOUNDARY,
                comparison_boundary="comparison:entity-frame",
                comparison_arg_positions=(0,),
                include_frame=True,
            ),
        ),
        checker_contracts=(
            CheckerContract(
                checker_id="rule-witness/v1",
                version=1,
                uses={CheckerUse.CERTIFICATE},
                certificate_subject_kinds={RecordKind.RULE},
                detail_fields=(
                    CheckerDetailField(
                        key="witness",
                        value_type=CheckerDetailType.NONEMPTY_STRING,
                    ),
                ),
            ),
            CheckerContract(
                checker_id="challenge-witness/v1",
                version=1,
                uses={CheckerUse.CERTIFICATE},
                certificate_subject_kinds={RecordKind.CHALLENGE},
                detail_fields=(
                    CheckerDetailField(
                        key="witness",
                        value_type=CheckerDetailType.NONEMPTY_STRING,
                    ),
                ),
            ),
            CheckerContract(
                checker_id="discharge-witness/v1",
                version=1,
                uses={CheckerUse.CERTIFICATE},
                certificate_subject_kinds={RecordKind.DISCHARGE},
                detail_fields=(
                    CheckerDetailField(
                        key="witness",
                        value_type=CheckerDetailType.NONEMPTY_STRING,
                    ),
                ),
            ),
            CheckerContract(
                checker_id="materialised-selector/v1",
                version=1,
                uses={CheckerUse.CLOSURE},
                local_closure_semantics=(
                    LocalClosureSemantics.MATERIALISED_SELECTOR_V1
                ),
                closure_selector_kinds={
                    RecordKind.CHALLENGE,
                    RecordKind.DISCHARGE,
                },
                selector_fields=(
                    SelectorFieldContract(
                        record_type=RecordKind.CHALLENGE,
                        field="target",
                        value_type=CheckerDetailType.RECORD_REF,
                        allowed_record_kinds={
                            RecordKind.ATOM,
                            RecordKind.RULE,
                            RecordKind.FACE,
                        },
                    ),
                    SelectorFieldContract(
                        record_type=RecordKind.DISCHARGE,
                        field="challenge",
                        value_type=CheckerDetailType.RECORD_REF,
                        allowed_record_kinds={RecordKind.CHALLENGE},
                    ),
                ),
                closure_frame_policy_id="frame:exact-package",
            ),
        ),
        predicates=(
            predicate("test.primitive", primitive_allowed=True),
            predicate(
                "test.derived",
                primitive_allowed=False,
                allowed_face_kinds=frozenset({"frame"}),
                allowed_challenge_kinds=frozenset(
                    {"rebut", "undercut", "defect"}
                ),
                checker_contract_ids=frozenset(
                    {
                        "rule-witness/v1",
                        "challenge-witness/v1",
                        "discharge-witness/v1",
                    }
                ),
            ),
            predicate(
                "test.contrary-left",
                primitive_allowed=False,
                contrary_policy_id="contrary:entity-frame",
            ),
            predicate(
                "test.contrary-right",
                primitive_allowed=False,
                contrary_policy_id="contrary:entity-frame",
            ),
            predicate(
                "test.graded-required",
                primitive_allowed=False,
                grade_policy=GradePolicy.REQUIRED,
            ),
            predicate(
                "test.graded-optional",
                primitive_allowed=False,
                grade_policy=GradePolicy.OPTIONAL,
            ),
        ),
    )


def catalog() -> RegistryCatalog:
    return RegistryCatalog(registries=(registry(),))


def atom(
    record_id: str,
    predicate_id: str,
    *,
    version: int = 1,
    arg: str = "entity:e",
    frame: str = "frame:1",
    grade: str | None = None,
    primitive: bool = False,
) -> AtomRecord:
    return AtomRecord(
        id=record_id,
        version=version,
        predicate=predicate_id,
        args=(arg,),
        frame=frame,
        grade=grade,
        primitive=primitive,
    )


def certificate(
    record_id: str,
    checker: str,
    subject: RecordRef,
    *,
    result: CheckResult = CheckResult.PASS,
    details: object | None = None,
) -> CertificateRecord:
    return CertificateRecord(
        id=record_id,
        version=1,
        checker=checker,
        subject=subject,
        result=result,
        payload_hash="sha256:test",
        details={"witness": "witness:1"} if details is None else details,  # type: ignore[arg-type]
    )


def minimal_valid_package() -> Package:
    source = atom(
        "atom:source",
        "test.primitive",
        primitive=True,
    )
    derived = atom("atom:derived", "test.derived")
    rule = RuleRecord(
        id="rule:derive",
        version=1,
        head=derived.ref,
        positive=(source.ref,),
        certificate=ref("cert:derive"),
    )
    cert = certificate("cert:derive", "rule-witness/v1", rule.ref)
    return Package(
        header=PackageHeader(
            schema="pff-core/0.1",
            package_id="package:test",
            cut_id="cut:1",
            frame_id="frame:1",
            registry_id="test-registry/1",
            metadata={"label": "test candidate"},
        ),
        atoms=(source, derived),
        rules=(rule,),
        certificates=(cert,),
        base=BasePartition(live=(source.ref,)),
    )


def linked_valid_package() -> Package:
    seed = minimal_valid_package()
    left = atom("atom:left", "test.contrary-left")
    right = atom("atom:right", "test.contrary-right")
    face = FaceRecord(
        id="face:frame",
        version=1,
        owner_rule=seed.rules[0].ref,
        kind="frame",
        boundary="frame:1",
        carrier="entity:e",
        depends_on_version=None,
        blocker_closure=ref("closure:blockers"),
    )
    rule = replace(seed.rules[0], faces=(face.ref,))
    challenge = ChallengeRecord(
        id="challenge:under",
        version=1,
        kind="undercut",
        target_kind=RecordKind.FACE,
        target=face.ref,
        certificate=ref("cert:challenge"),
        discharge_closure=ref("closure:discharges"),
    )
    discharge = DischargeRecord(
        id="discharge:repair",
        version=1,
        challenge=challenge.ref,
        kind="repair",
        certificate=ref("cert:discharge"),
    )
    blocker_closure = ClosureRecord(
        id="closure:blockers",
        version=1,
        checker="materialised-selector/v1",
        result=CheckResult.PASS,
        cut_id="cut:1",
        frame="frame:1",
        selector=Selector(
            record_type=RecordKind.CHALLENGE,
            where={"target": face.ref},
        ),
        members=(challenge.ref,),
    )
    discharge_closure = ClosureRecord(
        id="closure:discharges",
        version=1,
        checker="materialised-selector/v1",
        result=CheckResult.PASS,
        cut_id="cut:1",
        frame="frame:1",
        selector=Selector(
            record_type=RecordKind.DISCHARGE,
            where={"challenge": challenge.ref},
        ),
        members=(discharge.ref,),
    )
    contrary = ContraryRecord(
        id="contrary:pair",
        version=1,
        left=left.ref,
        right=right.ref,
        boundary="comparison:entity-frame",
    )
    challenge_cert = certificate(
        "cert:challenge",
        "challenge-witness/v1",
        challenge.ref,
    )
    discharge_cert = certificate(
        "cert:discharge",
        "discharge-witness/v1",
        discharge.ref,
    )
    return replace(
        seed,
        atoms=(*seed.atoms, left, right),
        rules=(rule,),
        faces=(face,),
        certificates=(*seed.certificates, challenge_cert, discharge_cert),
        closures=(blocker_closure, discharge_closure),
        contraries=(contrary,),
        challenges=(challenge,),
        discharges=(discharge,),
    )


def failure(candidate: Package) -> PackageValidationError:
    with unittest.TestCase().assertRaises(PackageValidationError) as caught:
        validate_package(candidate, catalog())
    return caught.exception


def codes(candidate: Package) -> tuple[ValidationCode, ...]:
    return tuple(issue.code for issue in failure(candidate).issues)


class SuccessfulBoundaryTests(unittest.TestCase):
    def test_minimal_and_linked_packages_mint_factory_only_capability(self) -> None:
        for candidate in (minimal_valid_package(), linked_valid_package()):
            with self.subTest(records=sum(1 for _ in candidate.iter_records())):
                validated = validate_package(candidate, catalog())
                self.assertIsInstance(validated, ValidatedPackage)
                self.assertIs(validated.package, candidate)
                self.assertEqual(validated.registry_id, "test-registry/1")
                source = validated.resolve(ref("atom:source"), RecordKind.ATOM)
                self.assertEqual(source, candidate.atoms[0])

        with self.assertRaises(TypeError):
            ValidatedPackage(  # type: ignore[call-arg]
                minimal_valid_package(),
                registry(),
                {},
            )

    def test_supplied_and_locally_recomputed_checker_results_are_distinct(self) -> None:
        seed = linked_valid_package()
        for result in (CheckResult.FAIL, CheckResult.OPEN):
            with self.subTest(result=result):
                certs = tuple(replace(item, result=result) for item in seed.certificates)
                validated = validate_package(
                    replace(seed, certificates=certs),
                    catalog(),
                )
                self.assertEqual(validated.package.certificates, certs)

        mismatch = replace(seed.closures[0], result=CheckResult.FAIL, members=())
        validated = validate_package(
            replace(seed, closures=(mismatch, seed.closures[1])),
            catalog(),
        )
        self.assertIs(validated.package.closures[0].result, CheckResult.FAIL)

        inconsistent = (
            replace(seed.closures[0], result=CheckResult.FAIL),
            replace(seed.closures[0], result=CheckResult.OPEN),
            replace(seed.closures[0], result=CheckResult.PASS, members=()),
        )
        for closure in inconsistent:
            with self.subTest(result=closure.result, members=closure.members):
                self.assertEqual(
                    codes(replace(seed, closures=(closure, seed.closures[1]))),
                    (ValidationCode.CLOSURE_RESULT_MISMATCH,),
                )

    def test_local_selector_uses_the_complete_order_independent_population(self) -> None:
        seed = linked_valid_package()
        second = ChallengeRecord(
            id="challenge:second",
            version=1,
            kind="undercut",
            target_kind=RecordKind.FACE,
            target=seed.faces[0].ref,
            certificate=ref("cert:second"),
            discharge_closure=ref("closure:second-open"),
        )
        second_certificate = certificate(
            "cert:second",
            "challenge-witness/v1",
            second.ref,
        )
        second_discharge_closure = ClosureRecord(
            id="closure:second-open",
            version=1,
            checker="materialised-selector/v1",
            result=CheckResult.OPEN,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.RULE,
                where={"future-selector": "opaque"},
            ),
        )
        blockers = replace(
            seed.closures[0],
            members={seed.challenges[0].ref, second.ref},
        )
        candidate = replace(
            seed,
            challenges=(seed.challenges[0], second),
            certificates=(*seed.certificates, second_certificate),
            closures=(blockers, seed.closures[1], second_discharge_closure),
        )

        for challenges in permutations(candidate.challenges):
            with self.subTest(order=tuple(item.id for item in challenges)):
                validate_package(replace(candidate, challenges=challenges), catalog())

        missing_second = replace(
            blockers,
            members={seed.challenges[0].ref},
        )
        self.assertIn(
            ValidationCode.CLOSURE_RESULT_MISMATCH,
            codes(
                replace(
                    candidate,
                    closures=(
                        missing_second,
                        seed.closures[1],
                        second_discharge_closure,
                    ),
                )
            ),
        )
        validate_package(
            replace(
                candidate,
                closures=(
                    replace(missing_second, result=CheckResult.FAIL),
                    seed.closures[1],
                    second_discharge_closure,
                ),
            ),
            catalog(),
        )

    def test_distinct_versions_coexist_without_latest_version_rewrite(self) -> None:
        seed = minimal_valid_package()
        source_v2 = replace(seed.atoms[0], version=2)
        candidate = replace(seed, atoms=(*seed.atoms, source_v2))

        validated = validate_package(candidate, catalog())

        self.assertEqual(
            validated.resolve(ref("atom:source", 1), RecordKind.ATOM).version,
            1,
        )
        self.assertEqual(
            validated.resolve(ref("atom:source", 2), RecordKind.ATOM).version,
            2,
        )

    def test_validated_graph_is_deeply_immutable(self) -> None:
        candidate = minimal_valid_package()
        validated = validate_package(candidate, catalog())

        with self.assertRaises(FrozenInstanceError):
            validated.package = linked_valid_package()  # type: ignore[misc]
        with self.assertRaises(TypeError):
            validated.package.header.metadata["new"] = "value"  # type: ignore[index]
        with self.assertRaises(TypeError):
            validated.package.header.metadata._items = ()  # type: ignore[attr-defined]


class HeaderIdentityReferenceTests(unittest.TestCase):
    def test_schema_and_exact_registry_lookup_fail_closed(self) -> None:
        seed = minimal_valid_package()
        wrong_schema = replace(
            seed,
            header=replace(seed.header, schema="pff-core/9.9"),
        )
        unknown_registry = replace(
            seed,
            header=replace(seed.header, registry_id="test-registry/2"),
        )

        self.assertEqual(codes(wrong_schema), (ValidationCode.SCHEMA_MISMATCH,))
        self.assertIn(ValidationCode.UNKNOWN_REGISTRY, codes(unknown_registry))

    def test_versions_duplicates_and_reserved_prefix_are_rejected(self) -> None:
        seed = minimal_valid_package()
        invalid_version = replace(
            seed,
            atoms=(replace(seed.atoms[1], version=0), seed.atoms[0]),
            rules=(replace(seed.rules[0], head=ref("atom:derived", 0)),),
        )
        duplicate = replace(seed, atoms=(*seed.atoms, seed.atoms[0]))
        reserved = replace(
            seed,
            rules=(replace(seed.rules[0], id="__pff__:rule:user"),),
            certificates=(
                replace(seed.certificates[0], subject=ref("__pff__:rule:user")),
            ),
        )

        self.assertIn(ValidationCode.INVALID_VERSION, codes(invalid_version))
        self.assertEqual(codes(duplicate), (ValidationCode.DUPLICATE_RECORD,))
        self.assertIn(ValidationCode.RESERVED_ID, codes(reserved))

    def test_exact_missing_version_and_wrong_kind_are_distinguished(self) -> None:
        seed = linked_valid_package()
        missing = replace(
            seed,
            rules=(replace(seed.rules[0], head=ref("atom:derived", 2)),),
        )
        wrong_kind = replace(
            seed,
            rules=(replace(seed.rules[0], certificate=seed.faces[0].ref),),
        )

        self.assertIn(ValidationCode.UNRESOLVED_REFERENCE, codes(missing))
        wrong_kind_codes = codes(wrong_kind)
        self.assertIn(ValidationCode.REFERENCE_KIND_MISMATCH, wrong_kind_codes)
        self.assertNotIn(
            ValidationCode.UNRESOLVED_REFERENCE,
            wrong_kind_codes,
        )

    def test_invalid_reference_and_external_version_token_are_diagnosed(self) -> None:
        seed = linked_valid_package()
        invalid_ref = replace(
            seed,
            rules=(replace(seed.rules[0], positive=(RecordRef("", 0),)),),
        )
        invalid_token = replace(
            seed,
            faces=(
                replace(
                    seed.faces[0],
                    depends_on_version=VersionToken("", 0),
                ),
            ),
        )

        ref_codes = codes(invalid_ref)
        self.assertIn(ValidationCode.INVALID_ID, ref_codes)
        self.assertIn(ValidationCode.INVALID_VERSION, ref_codes)
        self.assertNotIn(ValidationCode.UNRESOLVED_REFERENCE, ref_codes)
        token_codes = codes(invalid_token)
        self.assertIn(ValidationCode.INVALID_ID, token_codes)
        self.assertIn(ValidationCode.INVALID_VERSION, token_codes)


class PredicateAndBaseTests(unittest.TestCase):
    def test_predicate_arity_type_frame_and_grade_are_independent(self) -> None:
        seed = minimal_valid_package()
        derived = seed.atoms[1]
        cases = (
            (
                replace(seed, atoms=(seed.atoms[0], replace(derived, args=()))),
                ValidationCode.PREDICATE_ARITY,
            ),
            (
                replace(
                    seed,
                    atoms=(seed.atoms[0], replace(derived, args=("outcome:x",))),
                ),
                ValidationCode.PREDICATE_ARG_TYPE,
            ),
            (
                replace(
                    seed,
                    atoms=(seed.atoms[0], replace(derived, frame="frame:other")),
                ),
                ValidationCode.PREDICATE_FRAME,
            ),
            (
                replace(seed, atoms=(seed.atoms[0], replace(derived, grade="h"))),
                ValidationCode.PREDICATE_GRADE,
            ),
        )
        for candidate, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, codes(candidate))

    def test_unknown_predicate_and_primitive_constraints_are_rejected(self) -> None:
        seed = minimal_valid_package()
        unknown = replace(
            seed,
            atoms=(seed.atoms[0], replace(seed.atoms[1], predicate="unknown")),
        )
        forbidden = replace(
            seed,
            atoms=(seed.atoms[0], replace(seed.atoms[1], primitive=True)),
        )

        self.assertIn(ValidationCode.UNKNOWN_PREDICATE, codes(unknown))
        forbidden_codes = codes(forbidden)
        self.assertIn(ValidationCode.PRIMITIVE_FORBIDDEN, forbidden_codes)
        self.assertIn(ValidationCode.PRIMITIVE_HAS_DERIVATION, forbidden_codes)

    def test_grade_policy_accepts_only_the_frozen_vocabulary(self) -> None:
        seed = minimal_valid_package()
        for predicate_id, grades in (
            ("test.graded-required", ("h", "rho", "Phi")),
            ("test.graded-optional", (None, "h", "rho", "Phi")),
        ):
            for grade in grades:
                with self.subTest(predicate=predicate_id, grade=grade):
                    extra = atom("atom:graded", predicate_id, grade=grade)
                    validate_package(replace(seed, atoms=(*seed.atoms, extra)), catalog())

        missing = atom("atom:graded", "test.graded-required", grade=None)
        self.assertIn(
            ValidationCode.PREDICATE_GRADE,
            codes(replace(seed, atoms=(*seed.atoms, missing))),
        )

    def test_base_requires_primitive_atoms_and_all_pairwise_overlaps_fail(self) -> None:
        seed = minimal_valid_package()
        source = seed.atoms[0].ref
        for base in (
            BasePartition(live=(source,), excluded=(source,)),
            BasePartition(live=(source,), open=(source,)),
            BasePartition(excluded=(source,), open=(source,)),
            BasePartition(live=(source,), excluded=(source,), open=(source,)),
        ):
            with self.subTest(base=base):
                issues = failure(replace(seed, base=base)).issues
                overlaps = [
                    issue for issue in issues if issue.code is ValidationCode.BASE_OVERLAP
                ]
                self.assertEqual(len(overlaps), 1)

        nonprimitive = replace(seed, base=BasePartition(live=(seed.atoms[1].ref,)))
        self.assertIn(ValidationCode.BASE_NONPRIMITIVE, codes(nonprimitive))


class LinkedBindingTests(unittest.TestCase):
    def test_face_ownership_is_checked_in_both_directions(self) -> None:
        seed = linked_valid_package()
        omitted = replace(seed, rules=(replace(seed.rules[0], faces=()),))
        other_rule = replace(
            seed.rules[0],
            id="rule:other",
            certificate=ref("cert:other"),
            faces=(seed.faces[0].ref,),
        )
        wrong_owner = replace(
            seed,
            rules=(*seed.rules, other_rule),
            faces=(replace(seed.faces[0], owner_rule=other_rule.ref),),
            certificates=(
                *seed.certificates,
                certificate("cert:other", "rule-witness/v1", other_rule.ref),
            ),
        )
        omitted_issues = failure(omitted).issues
        wrong_owner_issues = failure(wrong_owner).issues
        self.assertEqual(
            [issue.code for issue in omitted_issues],
            [ValidationCode.FACE_OWNER_MISMATCH],
        )
        self.assertEqual(
            [issue.code for issue in wrong_owner_issues],
            [ValidationCode.FACE_OWNER_MISMATCH],
        )
        self.assertEqual(
            wrong_owner_issues[0].path,
            "rule[rule:derive@1].faces",
        )

    def test_face_vocabulary_and_predicate_permission_are_separate(self) -> None:
        seed = linked_valid_package()
        unknown = replace(seed, faces=(replace(seed.faces[0], kind="novel"),))
        forbidden = replace(seed, faces=(replace(seed.faces[0], kind="source"),))

        self.assertIn(ValidationCode.UNKNOWN_FACE_KIND, codes(unknown))
        self.assertIn(ValidationCode.FACE_KIND_FORBIDDEN, codes(forbidden))

    def test_dependent_policy_checks_do_not_duplicate_missing_reference_issues(self) -> None:
        seed = linked_valid_package()
        missing_head = replace(
            seed,
            rules=(replace(seed.rules[0], head=ref("atom:missing")),),
        )
        missing_role_target = replace(
            seed,
            closures=(
                replace(
                    seed.closures[0],
                    selector=Selector(
                        record_type=RecordKind.CHALLENGE,
                        where={"target": ref("face:missing")},
                    ),
                ),
                seed.closures[1],
            ),
        )

        for candidate, expected_path in (
            (missing_head, "rule[rule:derive@1].head"),
            (
                missing_role_target,
                "closure[closure:blockers@1].selector.where.target",
            ),
        ):
            with self.subTest(path=expected_path):
                unresolved = [
                    issue
                    for issue in failure(candidate).issues
                    if issue.code is ValidationCode.UNRESOLVED_REFERENCE
                ]
                self.assertEqual(len(unresolved), 1)
                self.assertEqual(unresolved[0].path, expected_path)

    def test_certificate_contract_subject_and_payload_are_bound_not_executed(self) -> None:
        seed = linked_valid_package()
        unknown = replace(
            seed,
            certificates=(
                replace(seed.certificates[0], checker="unknown/v1"),
                *seed.certificates[1:],
            ),
        )
        bad_payload = replace(
            seed,
            certificates=(
                replace(seed.certificates[0], details={"witness": 17}),
                *seed.certificates[1:],
            ),
        )
        wrong_subject = replace(
            seed,
            certificates=(
                replace(seed.certificates[0], subject=seed.challenges[0].ref),
                *seed.certificates[1:],
            ),
        )

        self.assertIn(ValidationCode.UNKNOWN_CHECKER, codes(unknown))
        self.assertIn(ValidationCode.CHECKER_PAYLOAD, codes(bad_payload))
        self.assertIn(
            ValidationCode.CERTIFICATE_SUBJECT_MISMATCH,
            codes(wrong_subject),
        )

    def test_challenge_and_discharge_certificates_require_forward_subject_binding(self) -> None:
        seed = linked_valid_package()
        authority = registry()
        mixed_checker = CheckerContract(
            checker_id="mixed-witness/v1",
            version=1,
            uses={CheckerUse.CERTIFICATE},
            certificate_subject_kinds={
                RecordKind.ATOM,
                RecordKind.CHALLENGE,
                RecordKind.DISCHARGE,
            },
            detail_fields=(
                CheckerDetailField(
                    key="witness",
                    value_type=CheckerDetailType.NONEMPTY_STRING,
                ),
            ),
        )
        predicates = tuple(
            replace(
                item,
                checker_contract_ids={*item.checker_contract_ids, mixed_checker.checker_id},
            )
            if item.predicate_id == "test.derived"
            else item
            for item in authority.predicates
        )
        mixed_catalog = RegistryCatalog(
            registries=(
                replace(
                    authority,
                    checker_contracts=(*authority.checker_contracts, mixed_checker),
                    predicates=predicates,
                ),
            )
        )

        for cert_index, owner_ref in (
            (1, seed.challenges[0].ref),
            (2, seed.discharges[0].ref),
        ):
            with self.subTest(owner=owner_ref):
                certificates = list(seed.certificates)
                certificates[cert_index] = replace(
                    certificates[cert_index],
                    checker=mixed_checker.checker_id,
                    subject=seed.atoms[1].ref,
                )
                with self.assertRaises(PackageValidationError) as caught:
                    validate_package(
                        replace(seed, certificates=tuple(certificates)),
                        mixed_catalog,
                    )
                ownership_issues = [
                    issue
                    for issue in caught.exception.issues
                    if issue.code is ValidationCode.CERTIFICATE_SUBJECT_MISMATCH
                ]
                self.assertEqual(len(ownership_issues), 1)
                self.assertIn(owner_ref, ownership_issues[0].refs)

    def test_typed_checker_detail_references_resolve_exact_kind_and_version(self) -> None:
        seed = linked_valid_package()
        authority = registry()
        ref_checker = CheckerContract(
            checker_id="rule-ref-witness/v1",
            version=1,
            uses={CheckerUse.CERTIFICATE},
            certificate_subject_kinds={RecordKind.RULE},
            detail_fields=(
                CheckerDetailField(
                    key="witness_atom",
                    value_type=CheckerDetailType.RECORD_REF,
                    allowed_record_kinds={RecordKind.ATOM},
                ),
            ),
        )
        predicates = tuple(
            replace(
                item,
                checker_contract_ids={*item.checker_contract_ids, ref_checker.checker_id},
            )
            if item.predicate_id == "test.derived"
            else item
            for item in authority.predicates
        )
        ref_catalog = RegistryCatalog(
            registries=(
                replace(
                    authority,
                    checker_contracts=(*authority.checker_contracts, ref_checker),
                    predicates=predicates,
                ),
            )
        )

        def candidate(detail_ref: RecordRef) -> Package:
            certificates = (
                replace(
                    seed.certificates[0],
                    checker=ref_checker.checker_id,
                    details={"witness_atom": detail_ref},
                ),
                *seed.certificates[1:],
            )
            return replace(seed, certificates=certificates)

        validate_package(candidate(seed.atoms[0].ref), ref_catalog)
        cases = (
            (ref("atom:missing"), ValidationCode.UNRESOLVED_REFERENCE),
            (ref("atom:source", 2), ValidationCode.UNRESOLVED_REFERENCE),
            (seed.faces[0].ref, ValidationCode.REFERENCE_KIND_MISMATCH),
            (RecordRef("", 0), ValidationCode.INVALID_ID),
        )
        for detail_ref, expected in cases:
            with self.subTest(detail_ref=detail_ref):
                with self.assertRaises(PackageValidationError) as caught:
                    validate_package(candidate(detail_ref), ref_catalog)
                self.assertIn(
                    expected,
                    [issue.code for issue in caught.exception.issues],
                )

    def test_predicate_checker_permission_follows_challenge_and_discharge_targets(self) -> None:
        seed = linked_valid_package()
        authority = registry()
        restricted = tuple(
            replace(item, checker_contract_ids={"rule-witness/v1"})
            if item.predicate_id == "test.derived"
            else item
            for item in authority.predicates
        )
        restricted_catalog = RegistryCatalog(
            registries=(replace(authority, predicates=restricted),)
        )

        with self.assertRaises(PackageValidationError) as caught:
            validate_package(seed, restricted_catalog)

        denied_subjects = {
            issue.refs[1]
            for issue in caught.exception.issues
            if issue.code is ValidationCode.CHECKER_NOT_PERMITTED
            and len(issue.refs) > 1
        }
        self.assertIn(seed.challenges[0].ref, denied_subjects)
        self.assertIn(seed.discharges[0].ref, denied_subjects)

    def test_closure_contract_cut_frame_and_member_kind_are_checked(self) -> None:
        seed = linked_valid_package()
        closure = seed.closures[1]
        cases = (
            (
                replace(
                    seed,
                    closures=(
                        seed.closures[0],
                        replace(
                            closure,
                            cut_id="cut:other",
                            result=CheckResult.FAIL,
                        ),
                    ),
                ),
                ValidationCode.CLOSURE_CUT_MISMATCH,
            ),
            (
                replace(
                    seed,
                    closures=(
                        seed.closures[0],
                        replace(
                            closure,
                            frame="frame:other",
                            result=CheckResult.FAIL,
                        ),
                    ),
                ),
                ValidationCode.CLOSURE_FRAME_MISMATCH,
            ),
            (
                replace(
                    seed,
                    closures=(
                        seed.closures[0],
                        replace(closure, members=(seed.challenges[0].ref,)),
                    ),
                ),
                ValidationCode.REFERENCE_KIND_MISMATCH,
            ),
        )
        for candidate, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(codes(candidate), (expected,))

    def test_closure_roles_and_nested_selector_references_are_bound(self) -> None:
        seed = linked_valid_package()
        swapped = replace(
            seed,
            faces=(
                replace(
                    seed.faces[0],
                    blocker_closure=seed.closures[1].ref,
                ),
            ),
            challenges=(
                replace(
                    seed.challenges[0],
                    discharge_closure=seed.closures[0].ref,
                ),
            ),
        )
        orphan = ClosureRecord(
            id="closure:orphan",
            version=1,
            checker="materialised-selector/v1",
            result=CheckResult.OPEN,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.CHALLENGE,
                where={"target": ref("face:missing")},
            ),
        )

        swapped_issues = [
            issue
            for issue in failure(swapped).issues
            if issue.code is ValidationCode.CLOSURE_ROLE_MISMATCH
        ]
        self.assertEqual(len(swapped_issues), 2)
        orphan_issues = failure(
            replace(seed, closures=(*seed.closures, orphan))
        ).issues
        self.assertEqual(
            [issue.code for issue in orphan_issues],
            [ValidationCode.UNRESOLVED_REFERENCE],
        )
        self.assertEqual(
            orphan_issues[0].path,
            "closure[closure:orphan@1].selector.where.target",
        )

    def test_role_binding_avoids_cascades_without_accepting_another_owner(self) -> None:
        seed = linked_valid_package()
        valid_other_target = replace(
            seed,
            closures=(
                replace(
                    seed.closures[0],
                    result=CheckResult.FAIL,
                    selector=Selector(
                        record_type=RecordKind.CHALLENGE,
                        where={"target": seed.rules[0].ref},
                    ),
                ),
                seed.closures[1],
            ),
        )
        wrong_blocker_kind = replace(
            seed,
            closures=(
                replace(
                    seed.closures[0],
                    selector=Selector(
                        record_type=RecordKind.CHALLENGE,
                        where={"target": seed.closures[1].ref},
                    ),
                ),
                seed.closures[1],
            ),
        )
        wrong_discharge_kind = replace(
            seed,
            closures=(
                seed.closures[0],
                replace(
                    seed.closures[1],
                    selector=Selector(
                        record_type=RecordKind.DISCHARGE,
                        where={"challenge": seed.faces[0].ref},
                    ),
                ),
            ),
        )

        self.assertEqual(
            tuple(issue.code for issue in failure(valid_other_target).issues),
            (ValidationCode.CLOSURE_ROLE_MISMATCH,),
        )
        for candidate in (wrong_blocker_kind, wrong_discharge_kind):
            with self.subTest(selector=candidate.closures):
                self.assertEqual(
                    tuple(issue.code for issue in failure(candidate).issues),
                    (ValidationCode.REFERENCE_KIND_MISMATCH,),
                )

    def test_role_binding_defers_to_direct_selector_shape_diagnostics(self) -> None:
        seed = linked_valid_package()
        malformed_candidates = (
            replace(
                seed,
                closures=(
                    replace(
                        seed.closures[0],
                        selector=Selector(
                            record_type=RecordKind.CHALLENGE,
                            where={"bogus": 17},
                        ),
                    ),
                    seed.closures[1],
                ),
            ),
            replace(
                seed,
                closures=(
                    seed.closures[0],
                    replace(
                        seed.closures[1],
                        selector=Selector(
                            record_type=RecordKind.DISCHARGE,
                            where={"challenge": 17},
                        ),
                    ),
                ),
            ),
        )
        for candidate in malformed_candidates:
            with self.subTest(selector=candidate.closures):
                self.assertEqual(
                    tuple(issue.code for issue in failure(candidate).issues),
                    (ValidationCode.CHECKER_PAYLOAD,),
                )

        open_unknown_scope = replace(
            seed,
            closures=(
                replace(
                    seed.closures[0],
                    result=CheckResult.OPEN,
                    selector=Selector(
                        record_type=RecordKind.RULE,
                        where={"future-selector": "opaque"},
                    ),
                    members=(),
                ),
                seed.closures[1],
            ),
        )
        validate_package(open_unknown_scope, catalog())

    def test_role_closures_cannot_narrow_their_exact_owner_scope(self) -> None:
        seed = linked_valid_package()
        authority = registry()
        extra_fields = (
            SelectorFieldContract(
                record_type=RecordKind.CHALLENGE,
                field="kind",
                value_type=CheckerDetailType.NONEMPTY_STRING,
            ),
            SelectorFieldContract(
                record_type=RecordKind.DISCHARGE,
                field="kind",
                value_type=CheckerDetailType.NONEMPTY_STRING,
            ),
        )
        checkers = tuple(
            replace(
                checker,
                selector_fields=(*checker.selector_fields, *extra_fields),
            )
            if checker.checker_id == "materialised-selector/v1"
            else checker
            for checker in authority.checker_contracts
        )
        narrowed_catalog = RegistryCatalog(
            registries=(replace(authority, checker_contracts=checkers),)
        )
        narrowed = replace(
            seed,
            closures=(
                replace(
                    seed.closures[0],
                    selector=Selector(
                        record_type=RecordKind.CHALLENGE,
                        where={"target": seed.faces[0].ref, "kind": "undercut"},
                    ),
                ),
                replace(
                    seed.closures[1],
                    selector=Selector(
                        record_type=RecordKind.DISCHARGE,
                        where={
                            "challenge": seed.challenges[0].ref,
                            "kind": "repair",
                        },
                    ),
                ),
            ),
        )

        with self.assertRaises(PackageValidationError) as caught:
            validate_package(narrowed, narrowed_catalog)

        role_issues = [
            issue
            for issue in caught.exception.issues
            if issue.code is ValidationCode.CLOSURE_ROLE_MISMATCH
        ]
        self.assertEqual(len(role_issues), 2)

    def test_selector_contract_rejects_unknown_fields_and_wrong_reference_kinds(self) -> None:
        seed = linked_valid_package()
        malformed = ClosureRecord(
            id="closure:malformed",
            version=1,
            checker="materialised-selector/v1",
            result=CheckResult.PASS,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.DISCHARGE,
                where={"bogus": 17},
            ),
        )
        wrong_kind = replace(
            malformed,
            id="closure:wrong-kind",
            selector=Selector(
                record_type=RecordKind.DISCHARGE,
                where={"challenge": seed.faces[0].ref},
            ),
        )
        wrong_union_kind = replace(
            malformed,
            id="closure:wrong-union-kind",
            selector=Selector(
                record_type=RecordKind.CHALLENGE,
                where={"target": seed.closures[0].ref},
            ),
        )

        self.assertIn(
            ValidationCode.CHECKER_PAYLOAD,
            codes(replace(seed, closures=(*seed.closures, malformed))),
        )
        self.assertIn(
            ValidationCode.REFERENCE_KIND_MISMATCH,
            codes(replace(seed, closures=(*seed.closures, wrong_kind))),
        )
        self.assertIn(
            ValidationCode.REFERENCE_KIND_MISMATCH,
            codes(replace(seed, closures=(*seed.closures, wrong_union_kind))),
        )

    def test_open_unsupported_selector_is_valid_but_nonopen_is_not(self) -> None:
        seed = linked_valid_package()
        unsupported = ClosureRecord(
            id="closure:unsupported",
            version=1,
            checker="materialised-selector/v1",
            result=CheckResult.OPEN,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.RULE,
                where={"future-selector": "opaque"},
            ),
        )

        validate_package(
            replace(seed, closures=(*seed.closures, unsupported)),
            catalog(),
        )
        nonopen = replace(unsupported, result=CheckResult.PASS)
        self.assertIn(
            ValidationCode.CHECKER_NOT_PERMITTED,
            codes(replace(seed, closures=(*seed.closures, nonopen))),
        )

        unsupported_shape = replace(
            unsupported,
            id="closure:unsupported-shape",
            selector=Selector(
                record_type=RecordKind.DISCHARGE,
                where={"future-selector": "opaque"},
            ),
        )
        validate_package(
            replace(seed, closures=(*seed.closures, unsupported_shape)),
            catalog(),
        )
        self.assertIn(
            ValidationCode.CHECKER_PAYLOAD,
            codes(
                replace(
                    seed,
                    closures=(
                        *seed.closures,
                        replace(unsupported_shape, result=CheckResult.PASS),
                    ),
                )
            ),
        )

    def test_closure_frame_uses_its_checker_policy_not_global_equality(self) -> None:
        seed = linked_valid_package()
        authority = registry()
        component_policy = FramePolicy(
            frame_policy_id="frame:component",
            version=1,
            mode=FramePolicyMode.NONEMPTY,
        )
        checkers = tuple(
            replace(
                checker,
                closure_frame_policy_id=component_policy.frame_policy_id,
            )
            if checker.checker_id == "materialised-selector/v1"
            else checker
            for checker in authority.checker_contracts
        )
        component_registry = replace(
            authority,
            frame_policies=(*authority.frame_policies, component_policy),
            checker_contracts=checkers,
        )
        closures = tuple(
            replace(closure, frame="frame:component:one")
            for closure in seed.closures
        )

        validated = validate_package(
            replace(seed, closures=closures),
            RegistryCatalog(registries=(component_registry,)),
        )

        self.assertEqual(validated.package.closures, closures)


class ContraryChallengeDischargeTests(unittest.TestCase):
    def test_contrary_pair_is_symmetric_and_policy_bound(self) -> None:
        seed = linked_valid_package()
        pair = seed.contraries[0]
        reversed_pair = replace(pair, left=pair.right, right=pair.left)
        validate_package(replace(seed, contraries=(reversed_pair,)), catalog())

        duplicate = replace(
            pair,
            id="contrary:duplicate",
            left=pair.right,
            right=pair.left,
        )
        mismatch = replace(pair, boundary="comparison:other")
        forbidden_atom = replace(seed.atoms[2], predicate="test.derived")
        forbidden = replace(seed, atoms=(*seed.atoms[:2], forbidden_atom, seed.atoms[3]))

        validate_package(replace(seed, contraries=(pair, duplicate)), catalog())
        validate_package(
            replace(seed, contraries=(replace(pair, left=pair.right),)),
            catalog(),
        )
        self.assertIn(ValidationCode.CONTRARY_BOUNDARY_MISMATCH, codes(replace(seed, contraries=(mismatch,))))
        self.assertIn(ValidationCode.CONTRARY_FORBIDDEN, codes(forbidden))

    def test_challenge_shape_and_target_permission_are_checked(self) -> None:
        seed = linked_valid_package()
        challenge = seed.challenges[0]
        unknown = replace(seed, challenges=(replace(challenge, kind="novel"),))
        forbidden = replace(seed, challenges=(replace(challenge, kind="recovery_gap"),))
        rebut = replace(
            seed,
            challenges=(replace(challenge, kind="rebut", contrary_atom=None),),
        )
        defect = replace(
            seed,
            challenges=(replace(challenge, kind="defect", problem_face_atom=None),),
        )

        self.assertIn(ValidationCode.UNKNOWN_CHALLENGE_KIND, codes(unknown))
        self.assertIn(ValidationCode.CHALLENGE_FORBIDDEN, codes(forbidden))
        self.assertIn(ValidationCode.REBUT_CONTRARY_REQUIRED, codes(rebut))
        self.assertIn(ValidationCode.DEFECT_PROBLEM_FACE_REQUIRED, codes(defect))

    def test_blocking_challenge_target_kind_is_registry_owned(self) -> None:
        seed = linked_valid_package()
        challenge = replace(
            seed.challenges[0],
            target_kind=RecordKind.ATOM,
            target=seed.atoms[1].ref,
        )

        issues = failure(replace(seed, challenges=(challenge,))).issues

        self.assertEqual(
            [issue.code for issue in issues],
            [
                ValidationCode.CHALLENGE_TARGET_KIND,
                ValidationCode.CLOSURE_RESULT_MISMATCH,
            ],
        )

    def test_missing_challenge_target_has_one_direct_reference_issue(self) -> None:
        seed = linked_valid_package()
        challenge = replace(seed.challenges[0], target=ref("face:missing"))

        issues = failure(replace(seed, challenges=(challenge,))).issues
        unresolved = [
            issue
            for issue in issues
            if issue.code is ValidationCode.UNRESOLVED_REFERENCE
        ]

        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].path, "challenge[challenge:under@1].target")

    def test_unknown_discharge_fails_but_known_incompatibility_remains_valid(self) -> None:
        seed = linked_valid_package()
        discharge = seed.discharges[0]
        unknown = replace(seed, discharges=(replace(discharge, kind="novel"),))
        incompatible = replace(
            seed,
            discharges=(replace(discharge, kind="recovery_witness"),),
        )

        self.assertIn(ValidationCode.UNKNOWN_DISCHARGE_KIND, codes(unknown))
        validated = validate_package(incompatible, catalog())
        self.assertEqual(validated.package.discharges[0].kind, "recovery_witness")


class DeterminismAndIsolationTests(unittest.TestCase):
    def test_aggregated_issues_equal_an_independent_golden_under_permutation(self) -> None:
        seed = minimal_valid_package()
        bad_a = atom("atom:a-bad", "unknown-a")
        bad_z = atom("atom:z-bad", "unknown-z")
        source = seed.atoms[0].ref
        faulty_header = replace(seed.header, schema="wrong")
        golden = (
            ValidationIssue(
                phase=ValidationPhase.HEADER,
                code=ValidationCode.SCHEMA_MISMATCH,
                path="header.schema",
                details=("expected:pff-core/0.1",),
            ),
            ValidationIssue(
                phase=ValidationPhase.POLICIES,
                code=ValidationCode.UNKNOWN_PREDICATE,
                path="atom[atom:a-bad@1].predicate",
                refs=(bad_a.ref,),
                details=("unknown-a",),
            ),
            ValidationIssue(
                phase=ValidationPhase.POLICIES,
                code=ValidationCode.UNKNOWN_PREDICATE,
                path="atom[atom:z-bad@1].predicate",
                refs=(bad_z.ref,),
                details=("unknown-z",),
            ),
            ValidationIssue(
                phase=ValidationPhase.BASE,
                code=ValidationCode.BASE_OVERLAP,
                path="base[atom:source@1]",
                refs=(source,),
                details=("live", "open"),
            ),
        )
        for atoms in permutations((*seed.atoms, bad_z, bad_a)):
            candidate = replace(
                seed,
                header=faulty_header,
                atoms=atoms,
                base=BasePartition(live=(source,), open=(source,)),
            )
            self.assertEqual(failure(candidate).issues, golden)

    def test_validation_module_has_no_ground_or_provider_import(self) -> None:
        script = (
            "import sys; "
            "from tests.test_pff_validate import catalog, minimal_valid_package; "
            "from poietics.pff.validate import validate_package; "
            "validate_package(minimal_valid_package(), catalog()); "
            "assert 'poietics.ground' not in sys.modules; "
            "assert 'poietics.ground.evaluate' not in sys.modules; "
            "assert 'poietics.pff.providers' not in sys.modules"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", script],
            check=False,
            env={"PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_validator_project_imports_are_statically_allowlisted(self) -> None:
        tree = ast.parse(inspect.getsource(validate_module))
        imports = {
            (node.level, node.module)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
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
            and isinstance(node.func, ast.Name)
            and node.func.id == "__import__"
        ]

        self.assertEqual(
            imports,
            {
                (0, "__future__"),
                (0, "dataclasses"),
                (0, "enum"),
                (0, "types"),
                (0, "typing"),
                (1, "model"),
                (1, "local_checkers"),
                (1, "registry"),
            },
        )
        self.assertEqual(plain_imports, set())
        self.assertEqual(dynamic_imports, [])

    def test_local_checker_module_is_provider_and_evaluator_free(self) -> None:
        tree = ast.parse(inspect.getsource(local_checkers_module))
        imports = {
            (node.level, node.module)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        plain_imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        self.assertEqual(
            imports,
            {
                (0, "__future__"),
                (0, "dataclasses"),
                (0, "typing"),
                (1, "model"),
                (1, "registry"),
            },
        )
        self.assertEqual(plain_imports, set())
        self.assertEqual(local_checkers_module.__all__, [])


if __name__ == "__main__":
    unittest.main()
