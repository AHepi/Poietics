from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from poietics.binding.model import (
    BindingCode,
    BindingIssue,
    BindingOrigin,
    BindingPhase,
    BindingPlan,
    BindingRole,
    BoundPackage,
    DraftBindingError,
    DraftBindingPolicy,
    DraftRecordKind,
    DraftSource,
    EvidenceAttestation,
    EvidenceBinding,
    EvidenceDetail,
    EvidenceTask,
    RecordIdentityBinding,
)
from poietics.generation.extract import extract_draft
from poietics.generation.model import (
    AttemptRef,
    AttemptRelation,
    DraftRef,
    capture_generation,
)
from poietics.pff.model import (
    AtomRecord,
    CheckResult,
    Package,
    PackageHeader,
    RecordKind,
    RecordRef,
    RuleRecord,
)
from poietics.pff.registry import PredicateRegistry, RegistryCatalog


POLICY_PROFILE = "pff-draft-binding-policy/0.1"
TASK_PROFILE = "pff-evidence-task/0.1"
ATTESTATION_PROFILE = "pff-evidence-attestation/0.1"
MAX_INTEGER = 9_223_372_036_854_775_807
SHA_ONE = "sha256:" + "1" * 64
PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"atom:generated",'
    b'"version":5,"predicate":"test.derived","args":["entity:e"],'
    b'"frame":"frame:1","grade":null}],"rules":[{"id":"rule:generated",'
    b'"version":7,"head":{"id":"atom:generated","version":5},'
    b'"positive":[],"evidence_request":{"id":"evidence:generated",'
    b'"version":11}}],"evidence_requests":[{"id":"evidence:generated",'
    b'"version":11,"kind":"certificate","subject":{"id":"rule:generated",'
    b'"version":7},"question":"Check the proposed derivation."}]}'
)
RESPONSE = b"<<<PFF-DRAFT/0.1>>>\n" + PAYLOAD + b"\n<<<END-PFF-DRAFT/0.1>>>"
PAYLOAD_SHA = (
    "sha256:ae7e0b37d389c3b702c98b9c9f7c3bfa7369221fcddbfbc7cb8a3630533aef6b"
)


def source():
    envelope = capture_generation(
        attempt=AttemptRef("session:binding-model", 1),
        relation=AttemptRelation.INITIAL,
        parent=None,
        provider_id="test-provider",
        adapter_id="test-adapter",
        adapter_version="1",
        requested_model="test-model",
        reported_model="test-model",
        prompt_template_id="test-template",
        prompt_template_version="1",
        prompt=b"Produce one PFF draft.\n",
        public_parameters={},
        raw_response=RESPONSE,
        finish_reason="stop",
        provider_request_id="request:binding-model",
    )
    return extract_draft(envelope)


def atom_binding(
    *,
    source_ref: DraftRef | None = None,
    target: RecordRef | None = None,
) -> RecordIdentityBinding:
    return RecordIdentityBinding(
        DraftRecordKind.ATOM,
        DraftRef("atom:generated", 5) if source_ref is None else source_ref,
        RecordRef("atom:authoritative", 2) if target is None else target,
    )


def rule_binding(
    *,
    source_ref: DraftRef | None = None,
    target: RecordRef | None = None,
) -> RecordIdentityBinding:
    return RecordIdentityBinding(
        DraftRecordKind.RULE,
        DraftRef("rule:generated", 7) if source_ref is None else source_ref,
        RecordRef("rule:authoritative", 4) if target is None else target,
    )


def evidence_binding(
    *,
    request: DraftRef | None = None,
    certificate: RecordRef | None = None,
) -> EvidenceBinding:
    return EvidenceBinding(
        request=(
            DraftRef("evidence:generated", 11) if request is None else request
        ),
        certificate=(
            RecordRef("certificate:authoritative", 6)
            if certificate is None
            else certificate
        ),
        checker_id="rule-witness/v1",
        checker_version=1,
        authority_id="evidence-authority:test",
        authority_version=2,
    )


def policy(
    *,
    record_bindings: tuple[RecordIdentityBinding, ...] | None = None,
    evidence_bindings: tuple[EvidenceBinding, ...] | None = None,
) -> DraftBindingPolicy:
    return DraftBindingPolicy(
        profile=POLICY_PROFILE,
        policy_id="policy:test",
        version=3,
        source_payload_sha256=PAYLOAD_SHA,
        package_id="package:bound-1",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
        record_bindings=(
            (atom_binding(), rule_binding())
            if record_bindings is None
            else record_bindings
        ),
        evidence_bindings=(
            (evidence_binding(),)
            if evidence_bindings is None
            else evidence_bindings
        ),
    )


def header() -> PackageHeader:
    return PackageHeader(
        schema="pff-core/0.1",
        package_id="package:bound-1",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        parent_package_hash=None,
        metadata={},
    )


def planned_atom() -> AtomRecord:
    return AtomRecord(
        id="atom:authoritative",
        version=2,
        predicate="test.derived",
        args=("entity:e",),
        frame="frame:1",
        grade=None,
        primitive=False,
    )


def planned_rule() -> RuleRecord:
    return RuleRecord(
        id="rule:authoritative",
        version=4,
        head=RecordRef("atom:authoritative", 2),
        positive=frozenset(),
        negative=frozenset(),
        certificate=RecordRef("certificate:authoritative", 6),
        faces=frozenset(),
    )


def task() -> EvidenceTask:
    return EvidenceTask(
        profile=TASK_PROFILE,
        source_payload_sha256=PAYLOAD_SHA,
        policy_id="policy:test",
        policy_version=3,
        subject_rule=planned_rule(),
        request_kind="certificate",
        request=DraftRef("evidence:generated", 11),
        question="Check the proposed derivation.",
        checker_id="rule-witness/v1",
        checker_version=1,
        expected_authority_id="evidence-authority:test",
        expected_authority_version=2,
        package_id="package:bound-1",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
    )


def attestation(
    *,
    details: tuple[EvidenceDetail, ...] | None = None,
) -> EvidenceAttestation:
    return EvidenceAttestation(
        profile=ATTESTATION_PROFILE,
        task=task(),
        authority_id="evidence-authority:test",
        authority_version=2,
        attestation_id="attestation:one",
        attestation_version=9,
        result=CheckResult.PASS,
        payload_hash=SHA_ONE,
        details=(
            (EvidenceDetail("witness", "fixture-secret"),)
            if details is None
            else details
        ),
    )


def origins() -> tuple[BindingOrigin, ...]:
    return (
        BindingOrigin(
            RecordKind.ATOM,
            RecordRef("atom:authoritative", 2),
            BindingRole.DRAFT_ATOM,
            DraftSource(DraftRecordKind.ATOM, DraftRef("atom:generated", 5)),
        ),
        BindingOrigin(
            RecordKind.RULE,
            RecordRef("rule:authoritative", 4),
            BindingRole.DRAFT_RULE,
            DraftSource(DraftRecordKind.RULE, DraftRef("rule:generated", 7)),
        ),
        BindingOrigin(
            RecordKind.CERTIFICATE,
            RecordRef("certificate:authoritative", 6),
            BindingRole.EVIDENCE_CERTIFICATE,
            DraftSource(
                DraftRecordKind.EVIDENCE_REQUEST,
                DraftRef("evidence:generated", 11),
            ),
        ),
    )


def plan() -> BindingPlan:
    registry = PredicateRegistry(registry_id="test-registry/1", version=1)
    return BindingPlan._from_planning(
        source=source(),
        policy=policy(),
        catalog=RegistryCatalog(registries=(registry,)),
        registry=registry,
        header=header(),
        atoms=(planned_atom(),),
        rules=(planned_rule(),),
        tasks=(task(),),
        origins=origins(),
    )


def bound() -> BoundPackage:
    binding_plan = plan()
    candidate = Package(
        header=binding_plan.header,
        atoms=binding_plan.atoms,
        rules=binding_plan.rules,
    )
    return BoundPackage._from_finalization(
        plan=binding_plan,
        evidence=(attestation(),),
        package=candidate,
    )


class OrdinaryValueTests(unittest.TestCase):
    def test_policy_canonicalizes_by_kind_id_and_numeric_version(self) -> None:
        records = (
            rule_binding(source_ref=DraftRef("same", 10)),
            atom_binding(source_ref=DraftRef("z", 1)),
            rule_binding(source_ref=DraftRef("same", 2)),
            atom_binding(source_ref=DraftRef("a", 1)),
        )
        evidence = (
            evidence_binding(request=DraftRef("e", 10)),
            evidence_binding(request=DraftRef("e", 2)),
        )

        value = policy(record_bindings=records, evidence_bindings=evidence)

        self.assertEqual(
            tuple((item.source_kind, item.source) for item in value.record_bindings),
            (
                (DraftRecordKind.ATOM, DraftRef("a", 1)),
                (DraftRecordKind.ATOM, DraftRef("z", 1)),
                (DraftRecordKind.RULE, DraftRef("same", 2)),
                (DraftRecordKind.RULE, DraftRef("same", 10)),
            ),
        )
        self.assertEqual(
            tuple(item.request for item in value.evidence_bindings),
            (DraftRef("e", 2), DraftRef("e", 10)),
        )

    def test_policy_rejects_duplicate_typed_sources_and_requests(self) -> None:
        duplicate_atom = replace(
            atom_binding(),
            target=RecordRef("atom:other", 9),
        )
        duplicate_evidence = replace(
            evidence_binding(),
            certificate=RecordRef("certificate:other", 9),
        )
        with self.assertRaises(ValueError):
            policy(record_bindings=(atom_binding(), duplicate_atom))
        with self.assertRaises(ValueError):
            policy(evidence_bindings=(evidence_binding(), duplicate_evidence))

    def test_embedded_policy_target_validation_is_deferred(self) -> None:
        for target in (
            RecordRef("", 0),
            RecordRef("\ud800", -1),
            RecordRef("x" * 262_145, MAX_INTEGER + 1),
        ):
            with self.subTest(target=target):
                self.assertEqual(atom_binding(target=target).target, target)

    def test_evidence_details_are_exact_distinct_and_canonical(self) -> None:
        integer = EvidenceDetail("same", 1)
        boolean = EvidenceDetail("same", True)
        reference = RecordRef("detail:ref", 1)

        self.assertNotEqual(integer, boolean)
        self.assertNotEqual(hash(integer), hash(boolean))
        value = attestation(
            details=(
                EvidenceDetail("z", reference),
                EvidenceDetail("a", ""),
            )
        )
        self.assertEqual(tuple(detail.key for detail in value.details), ("a", "z"))
        self.assertEqual(value.details[1].value, reference)
        with self.assertRaises(ValueError):
            attestation(
                details=(EvidenceDetail("x", 1), EvidenceDetail("x", True))
            )

    def test_detail_type_and_signed_integer_boundaries(self) -> None:
        class IntSubclass(int):
            pass

        class StrSubclass(str):
            pass

        class RecordRefSubclass(RecordRef):
            pass

        for accepted in (
            -MAX_INTEGER,
            MAX_INTEGER,
            False,
            "",
            RecordRef("detail:ref", 1),
        ):
            self.assertEqual(EvidenceDetail("key", accepted).value, accepted)
        for rejected in (
            IntSubclass(1),
            StrSubclass("x"),
            RecordRefSubclass("detail:ref", 1),
            1.0,
            None,
            (),
            [],
        ):
            with self.subTest(rejected=type(rejected).__name__):
                with self.assertRaises(TypeError):
                    EvidenceDetail("key", rejected)  # type: ignore[arg-type]
        for rejected in (-MAX_INTEGER - 1, MAX_INTEGER + 1):
            with self.assertRaises(ValueError):
                EvidenceDetail("key", rejected)

    def test_profiles_hashes_and_request_kind_are_exact(self) -> None:
        constructors = (
            lambda bad: replace(policy(), profile=bad),
            lambda bad: replace(task(), profile=bad),
            lambda bad: replace(attestation(), profile=bad),
        )
        for constructor in constructors:
            with self.assertRaises(ValueError):
                constructor("wrong-profile")

        hash_constructors = (
            lambda bad: replace(policy(), source_payload_sha256=bad),
            lambda bad: replace(task(), source_payload_sha256=bad),
            lambda bad: replace(attestation(), payload_hash=bad),
        )
        for bad in (
            "sha256:" + "A" * 64,
            "sha256:" + "g" * 64,
            "sha256:" + "1" * 63,
            "sha256:" + "1" * 65,
            "sha257:" + "1" * 64,
        ):
            for constructor in hash_constructors:
                with self.assertRaises(ValueError):
                    constructor(bad)
        with self.assertRaises(ValueError):
            replace(task(), request_kind="other")
        with self.assertRaises(ValueError):
            RecordIdentityBinding(
                DraftRecordKind.EVIDENCE_REQUEST,
                DraftRef("evidence:generated", 11),
                RecordRef("certificate:authoritative", 6),
            )

    def test_empty_question_detail_and_detail_tuple_are_accepted(self) -> None:
        self.assertEqual(replace(task(), question="").question, "")
        self.assertEqual(EvidenceDetail("empty", "").value, "")
        self.assertEqual(attestation(details=()).details, ())
        issue = BindingIssue(
            BindingPhase.REGISTRY,
            BindingCode.UNKNOWN_REGISTRY,
            "/policy/registry_id",
            details=("",),
        )
        self.assertEqual(issue.details, ("",))

    def test_repr_hides_questions_and_detail_values(self) -> None:
        self.assertNotIn("Check the proposed derivation.", repr(task()))
        self.assertNotIn("fixture-secret", repr(EvidenceDetail("secret", "fixture-secret")))
        self.assertNotIn("fixture-secret", repr(attestation()))

    def test_ordinary_values_are_frozen_slotted_and_structurally_hashable(self) -> None:
        issue = BindingIssue(
            BindingPhase.REGISTRY,
            BindingCode.UNKNOWN_REGISTRY,
            "/policy/registry_id",
            details=("missing-registry",),
        )
        values = (
            DraftSource(DraftRecordKind.ATOM, DraftRef("atom:generated", 5)),
            atom_binding(),
            evidence_binding(),
            policy(),
            task(),
            EvidenceDetail("witness", "fixture-secret"),
            attestation(),
            origins()[0],
            issue,
        )
        for value in values:
            with self.subTest(value=type(value).__name__):
                self.assertFalse(hasattr(value, "__dict__"))
                self.assertEqual(hash(value), hash(replace(value)))
                with self.assertRaises(FrozenInstanceError):
                    setattr(value, next(iter(value.__dataclass_fields__)), getattr(value, next(iter(value.__dataclass_fields__))))


class ConstructorLimitTests(unittest.TestCase):
    def _string_mutators(self):
        base_evidence = evidence_binding()
        base_policy = policy()
        base_task = task()
        base_detail = EvidenceDetail("key", "value")
        base_attestation = attestation()
        return (
            lambda value: replace(base_evidence, checker_id=value),
            lambda value: replace(base_evidence, authority_id=value),
            lambda value: replace(base_policy, policy_id=value),
            lambda value: replace(base_policy, package_id=value),
            lambda value: replace(base_policy, cut_id=value),
            lambda value: replace(base_policy, frame_id=value),
            lambda value: replace(base_policy, registry_id=value),
            lambda value: replace(base_task, policy_id=value),
            lambda value: replace(base_task, question=value),
            lambda value: replace(base_task, checker_id=value),
            lambda value: replace(base_task, expected_authority_id=value),
            lambda value: replace(base_task, package_id=value),
            lambda value: replace(base_task, cut_id=value),
            lambda value: replace(base_task, frame_id=value),
            lambda value: replace(base_task, registry_id=value),
            lambda value: replace(base_detail, key=value),
            lambda value: replace(base_detail, value=value),
            lambda value: replace(base_attestation, authority_id=value),
            lambda value: replace(base_attestation, attestation_id=value),
        )

    def test_all_binding_strings_use_unicode_scalar_utf8_limits(self) -> None:
        maximum = "\u00e9" * 131_072
        over = maximum + "a"
        mutators = self._string_mutators()
        self.assertEqual(len(mutators), 19)
        for index, mutate in enumerate(mutators):
            with self.subTest(index=index, case="maximum"):
                mutate(maximum)
            with self.subTest(index=index, case="over"):
                with self.assertRaises(ValueError):
                    mutate(over)
            with self.subTest(index=index, case="surrogate"):
                with self.assertRaises(ValueError):
                    mutate("\ud800")

    def test_identifier_slots_reject_empty_but_free_text_slots_do_not(self) -> None:
        mutators = self._string_mutators()
        for index, mutate in enumerate(mutators):
            if index in {8, 16}:
                mutate("")
            else:
                with self.subTest(index=index):
                    with self.assertRaises(ValueError):
                        mutate("")

    def test_all_positive_integer_slots_enforce_exact_type_and_range(self) -> None:
        class IntSubclass(int):
            pass

        base_evidence = evidence_binding()
        base_policy = policy()
        base_task = task()
        base_attestation = attestation()
        mutators = (
            lambda value: replace(base_evidence, checker_version=value),
            lambda value: replace(base_evidence, authority_version=value),
            lambda value: replace(base_policy, version=value),
            lambda value: replace(base_policy, registry_version=value),
            lambda value: replace(base_task, policy_version=value),
            lambda value: replace(base_task, checker_version=value),
            lambda value: replace(base_task, expected_authority_version=value),
            lambda value: replace(base_task, registry_version=value),
            lambda value: replace(base_attestation, authority_version=value),
            lambda value: replace(base_attestation, attestation_version=value),
        )
        for mutate in mutators:
            mutate(1)
            mutate(MAX_INTEGER)
            for bad in (0, -1, MAX_INTEGER + 1):
                with self.assertRaises(ValueError):
                    mutate(bad)
            for bad in (True, IntSubclass(1), "1"):
                with self.assertRaises(TypeError):
                    mutate(bad)  # type: ignore[arg-type]

    def test_collection_caps_are_independent_and_exact(self) -> None:
        def q(index: int) -> str:
            return f"{index:04d}"

        records = tuple(
            RecordIdentityBinding(
                DraftRecordKind.ATOM,
                DraftRef("r:" + q(index), 1),
                RecordRef("target:r:" + q(index), 1),
            )
            for index in range(8_193)
        )
        evidence = tuple(
            EvidenceBinding(
                request=DraftRef("e:" + q(index), 1),
                certificate=RecordRef("target:e:" + q(index), 1),
                checker_id="rule-witness/v1",
                checker_version=1,
                authority_id="evidence-authority:test",
                authority_version=2,
            )
            for index in range(4_097)
        )
        details = tuple(
            EvidenceDetail("k:" + q(index), "") for index in range(4_097)
        )

        self.assertEqual(
            len(
                policy(
                    record_bindings=records[:8_192],
                    evidence_bindings=evidence[:4_096],
                ).record_bindings
            ),
            8_192,
        )
        with self.assertRaises(ValueError):
            policy(record_bindings=records)
        with self.assertRaises(ValueError):
            policy(evidence_bindings=evidence)
        self.assertEqual(len(attestation(details=details[:4_096]).details), 4_096)
        with self.assertRaises(ValueError):
            attestation(details=details)

    def test_exact_tuple_types_are_required(self) -> None:
        class TupleSubclass(tuple):
            pass

        for bad_records in ([], TupleSubclass((atom_binding(),))):
            with self.assertRaises(TypeError):
                replace(policy(), record_bindings=bad_records)  # type: ignore[arg-type]
        for bad_evidence in ([], TupleSubclass((evidence_binding(),))):
            with self.assertRaises(TypeError):
                replace(policy(), evidence_bindings=bad_evidence)  # type: ignore[arg-type]
        for bad_details in ([], TupleSubclass((EvidenceDetail("x", 1),))):
            with self.assertRaises(TypeError):
                replace(attestation(), details=bad_details)  # type: ignore[arg-type]


class OriginAndDiagnosticTests(unittest.TestCase):
    def test_only_three_rank_aligned_origin_triples_are_coherent(self) -> None:
        target_kinds = (RecordKind.ATOM, RecordKind.RULE, RecordKind.CERTIFICATE)
        roles = (
            BindingRole.DRAFT_ATOM,
            BindingRole.DRAFT_RULE,
            BindingRole.EVIDENCE_CERTIFICATE,
        )
        source_kinds = (
            DraftRecordKind.ATOM,
            DraftRecordKind.RULE,
            DraftRecordKind.EVIDENCE_REQUEST,
        )
        successes: list[tuple[RecordKind, BindingRole, DraftRecordKind]] = []
        for target_kind in target_kinds:
            for role in roles:
                for source_kind in source_kinds:
                    try:
                        BindingOrigin(
                            target_kind,
                            RecordRef("origin:target", 1),
                            role,
                            DraftSource(source_kind, DraftRef("origin:source", 1)),
                        )
                    except ValueError:
                        continue
                    successes.append((target_kind, role, source_kind))
        self.assertEqual(
            successes,
            [
                (RecordKind.ATOM, BindingRole.DRAFT_ATOM, DraftRecordKind.ATOM),
                (RecordKind.RULE, BindingRole.DRAFT_RULE, DraftRecordKind.RULE),
                (
                    RecordKind.CERTIFICATE,
                    BindingRole.EVIDENCE_CERTIFICATE,
                    DraftRecordKind.EVIDENCE_REQUEST,
                ),
            ],
        )

    def test_binding_issue_enforces_shape_uniqueness_and_canonical_order(self) -> None:
        sx2 = DraftSource(DraftRecordKind.ATOM, DraftRef("x", 2))
        sx10 = DraftSource(DraftRecordKind.ATOM, DraftRef("x", 10))
        tx2 = RecordRef("x", 2)
        tx10 = RecordRef("x", 10)
        valid = BindingIssue(
            BindingPhase.IDENTITY,
            BindingCode.TARGET_REF_COLLISION,
            "/policy/targets",
            sources=(sx2, sx10),
            targets=(RecordRef("collision", 1),),
        )
        self.assertEqual(valid.sources, (sx2, sx10))
        with self.assertRaises(ValueError):
            replace(valid, phase=BindingPhase.COVERAGE)
        with self.assertRaises(ValueError):
            replace(valid, path="/wrong")
        with self.assertRaises(ValueError):
            replace(valid, sources=(sx2, sx2))
        with self.assertRaises(ValueError):
            replace(valid, sources=(sx10, sx2))

        evidence_issue = BindingIssue(
            BindingPhase.EVIDENCE_SET,
            BindingCode.EVIDENCE_EXTRA,
            "/evidence",
            targets=(tx2, tx10),
        )
        with self.assertRaises(ValueError):
            replace(evidence_issue, targets=(tx10, tx2))
        with self.assertRaises(ValueError):
            replace(evidence_issue, details=("x", "x"))
        with self.assertRaises(ValueError):
            replace(evidence_issue, details=("z", "a"))

    def test_issue_detail_has_derived_utf8_limit_and_accepts_empty(self) -> None:
        maximum = "\u00e9" * 131_088
        issue = BindingIssue(
            BindingPhase.REGISTRY,
            BindingCode.UNKNOWN_REGISTRY,
            "/policy/registry_id",
            details=(maximum,),
        )
        self.assertEqual(issue.details, (maximum,))
        self.assertEqual(replace(issue, details=("",)).details, ("",))
        with self.assertRaises(ValueError):
            replace(issue, details=(maximum + "a",))
        with self.assertRaises(ValueError):
            replace(issue, details=("\ud800",))

    def test_draft_binding_error_deduplicates_and_orders_versions_numerically(self) -> None:
        def invalid_id_issue(version: int) -> BindingIssue:
            return BindingIssue(
                BindingPhase.IDENTITY,
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
                sources=(
                    DraftSource(DraftRecordKind.ATOM, DraftRef("x", version)),
                ),
                targets=(RecordRef("", version),),
            )

        x2 = invalid_id_issue(2)
        x10 = invalid_id_issue(10)
        submitted = (x10, x2, x2)
        error = DraftBindingError(submitted)
        self.assertEqual(error.issues, (x2, x10))
        self.assertEqual(submitted, (x10, x2, x2))
        self.assertEqual(str(error), "draft binding failed")
        with self.assertRaises(ValueError):
            DraftBindingError(())
        with self.assertRaises(TypeError):
            DraftBindingError((object(),))  # type: ignore[arg-type]


class CapabilityTests(unittest.TestCase):
    def test_capabilities_reject_direct_construction_and_are_unhashable(self) -> None:
        for constructor in (BindingPlan, BoundPackage):
            with self.assertRaises(TypeError):
                constructor()
            with self.assertRaises(TypeError):
                constructor(profile="anything")
        with self.assertRaises(TypeError):
            hash(plan())
        with self.assertRaises(TypeError):
            hash(bound())

    def test_plan_indexes_preserve_kind_and_version(self) -> None:
        value = plan()
        self.assertEqual(
            value.target_for(
                DraftRecordKind.ATOM,
                DraftRef("atom:generated", 5),
            ),
            RecordRef("atom:authoritative", 2),
        )
        self.assertEqual(
            value.target_for(
                DraftRecordKind.RULE,
                DraftRef("rule:generated", 7),
            ),
            RecordRef("rule:authoritative", 4),
        )
        self.assertEqual(
            value.target_for(
                DraftRecordKind.EVIDENCE_REQUEST,
                DraftRef("evidence:generated", 11),
            ),
            RecordRef("certificate:authoritative", 6),
        )
        self.assertEqual(value.task_for(DraftRef("evidence:generated", 11)), task())
        self.assertEqual(
            value.origin_for(RecordKind.ATOM, RecordRef("atom:authoritative", 2)),
            origins()[0],
        )
        with self.assertRaises(TypeError):
            value.target_for("atom", DraftRef("atom:generated", 5))  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            value.task_for(RecordRef("evidence:generated", 11))  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            value.origin_for("atom", RecordRef("atom:authoritative", 2))  # type: ignore[arg-type]
        with self.assertRaises(KeyError):
            value.target_for(DraftRecordKind.ATOM, DraftRef("absent", 1))
        with self.assertRaises(KeyError):
            value.target_for(
                DraftRecordKind.ATOM,
                DraftRef("atom:generated", 6),
            )
        with self.assertRaises(KeyError):
            value.task_for(DraftRef("evidence:generated", 10))
        with self.assertRaises(KeyError):
            value.origin_for(RecordKind.RULE, RecordRef("atom:authoritative", 2))

    def test_plan_and_bound_package_are_deeply_immutable_and_secret_safe(self) -> None:
        binding_plan = plan()
        candidate = bound()
        with self.assertRaises(FrozenInstanceError):
            binding_plan.profile = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            binding_plan._target_index[  # type: ignore[index]
                DraftSource(DraftRecordKind.ATOM, DraftRef("atom:generated", 5))
            ] = RecordRef("changed", 1)
        with self.assertRaises(FrozenInstanceError):
            candidate.profile = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            candidate.package.header = header()  # type: ignore[misc]
        self.assertNotIn("Check the proposed derivation.", repr(binding_plan))
        self.assertNotIn("fixture-secret", repr(candidate))
        self.assertEqual(
            candidate.origin_for(
                RecordKind.CERTIFICATE,
                RecordRef("certificate:authoritative", 6),
            ),
            origins()[2],
        )

    def test_origin_index_is_an_unfiltered_typed_projection(self) -> None:
        tree = ast.parse(Path("src/poietics/binding/model.py").read_text())
        source_text = ast.unparse(tree)
        self.assertIn(
            "MappingProxyType({(o.target_kind, o.target): o for o in origins})",
            source_text,
        )
        self.assertIn("object.__setattr__(self, 'origins', origins)", source_text)

    def test_package_initializer_is_docstring_only(self) -> None:
        tree = ast.parse(Path("src/poietics/binding/__init__.py").read_text())
        self.assertEqual(len(tree.body), 1)
        self.assertIsInstance(tree.body[0], ast.Expr)
        self.assertIsInstance(tree.body[0].value, ast.Constant)
        self.assertIsInstance(tree.body[0].value.value, str)


if __name__ == "__main__":
    unittest.main()
