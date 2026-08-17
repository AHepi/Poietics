from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from poietics.binding.model import (
    BindingCode,
    BindingIssue,
    BindingOrigin,
    BindingPhase,
    BindingRole,
    DraftBindingError,
    DraftBindingPolicy,
    DraftRecordKind,
    DraftSource,
    EvidenceBinding,
    EvidenceTask,
    RecordIdentityBinding,
)
from poietics.binding.plan import plan_draft_binding
from poietics.generation.extract import ExtractedDraft, extract_draft
from poietics.generation.model import (
    AttemptRef,
    AttemptRelation,
    DraftRef,
    capture_generation,
)
from poietics.pff.model import AtomRecord, PackageHeader, RecordKind, RecordRef, RuleRecord
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
)


MAX_VERSION = 9_223_372_036_854_775_807
UNBOUNDED_EXTERNAL_VERSION = 10 ** 300_000
OPEN_LINE = b"<<<PFF-DRAFT/0.1>>>\n"
CLOSE_LINE = b"\n<<<END-PFF-DRAFT/0.1>>>"

S00_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[],"rules":[],'
    b'"evidence_requests":[]}'
)
S01_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"atom:generated",'
    b'"version":5,"predicate":"test.derived","args":["entity:e"],'
    b'"frame":"frame:1","grade":null}],"rules":[{"id":"rule:generated",'
    b'"version":7,"head":{"id":"atom:generated","version":5},'
    b'"positive":[],"evidence_request":{"id":"evidence:generated",'
    b'"version":11}}],"evidence_requests":[{"id":"evidence:generated",'
    b'"version":11,"kind":"certificate","subject":{"id":"rule:generated",'
    b'"version":7},"question":"Check the proposed derivation."}]}'
)
S02_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"local:b","version":1,'
    b'"predicate":"test.derived","args":["entity:b"],"frame":"frame:1",'
    b'"grade":null},{"id":"local:a","version":2,"predicate":"test.derived",'
    b'"args":["entity:a2"],"frame":"frame:1","grade":null},{"id":"local:a",'
    b'"version":1,"predicate":"test.derived","args":["entity:a1"],"frame":'
    b'"frame:1","grade":null}],"rules":[{"id":"local:r-b","version":1,'
    b'"head":{"id":"local:b","version":1},"positive":[],"evidence_request":'
    b'{"id":"local:e-b","version":1}},{"id":"local:r-a","version":2,'
    b'"head":{"id":"local:a","version":2},"positive":[],"evidence_request":'
    b'{"id":"local:e-a","version":2}},{"id":"local:r-a","version":1,'
    b'"head":{"id":"local:a","version":1},"positive":[{"id":"local:b",'
    b'"version":1}],"evidence_request":{"id":"local:e-a","version":1}}],'
    b'"evidence_requests":[{"id":"local:e-b","version":1,"kind":'
    b'"certificate","subject":{"id":"local:r-b","version":1},"question":'
    b'"Check."},{"id":"local:e-a","version":2,"kind":"certificate",'
    b'"subject":{"id":"local:r-a","version":2},"question":"Check."},{"id":'
    b'"local:e-a","version":1,"kind":"certificate","subject":{"id":'
    b'"local:r-a","version":1},"question":"Check."}]}'
)
S03_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"shared","version":13,'
    b'"predicate":"test.derived","args":["entity:shared"],"frame":"frame:1",'
    b'"grade":null}],"rules":[{"id":"shared","version":13,"head":'
    b'{"id":"shared","version":13},"positive":[{"id":"shared",'
    b'"version":13}],"evidence_request":{"id":"shared","version":13}}],'
    b'"evidence_requests":[{"id":"shared","version":13,"kind":'
    b'"certificate","subject":{"id":"shared","version":13},"question":'
    b'"Check shared."}]}'
)
S04H_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"atom:unknown",'
    b'"version":1,"predicate":"test.unknown","args":["entity:u"],'
    b'"frame":"frame:1","grade":null}],"rules":[{"id":'
    b'"rule:unknown-head","version":1,"head":{"id":"atom:unknown",'
    b'"version":1},"positive":[],"evidence_request":{"id":'
    b'"evidence:unknown-head","version":1}}],"evidence_requests":[{"id":'
    b'"evidence:unknown-head","version":1,"kind":"certificate","subject":'
    b'{"id":"rule:unknown-head","version":1},"question":'
    b'"Check unknown head."}]}'
)
S04P_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"atom:known","version":1,'
    b'"predicate":"test.derived","args":["entity:k"],"frame":"frame:1",'
    b'"grade":null},{"id":"atom:unknown-premise","version":1,"predicate":'
    b'"test.unknown","args":["entity:u"],"frame":"frame:1","grade":null}],'
    b'"rules":[{"id":"rule:known-head","version":1,"head":{"id":'
    b'"atom:known","version":1},"positive":[{"id":"atom:unknown-premise",'
    b'"version":1}],"evidence_request":{"id":"evidence:known-head",'
    b'"version":1}}],"evidence_requests":[{"id":"evidence:known-head",'
    b'"version":1,"kind":"certificate","subject":{"id":'
    b'"rule:known-head","version":1},"question":"Check known head."}]}'
)
S08_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"a","version":1,'
    b'"predicate":"test.derived","args":["entity:e"],"frame":"frame:1",'
    b'"grade":null}],"rules":[{"id":"r","version":10,"head":{"id":"a",'
    b'"version":1},"positive":[],"evidence_request":{"id":"e",'
    b'"version":10}},{"id":"r","version":2,"head":{"id":"a",'
    b'"version":1},"positive":[],"evidence_request":{"id":"e",'
    b'"version":2}}],"evidence_requests":[{"id":"e","version":10,'
    b'"kind":"certificate","subject":{"id":"r","version":10},'
    b'"question":"Q10."},{"id":"e","version":2,"kind":"certificate",'
    b'"subject":{"id":"r","version":2},"question":"Q2."}]}'
)

P01_ATOM_SOURCE = DraftRef("atom:generated", 5)
P01_RULE_SOURCE = DraftRef("rule:generated", 7)
P01_REQUEST_SOURCE = DraftRef("evidence:generated", 11)
P01_ATOM_TARGET = RecordRef("atom:authoritative", 2)
P01_RULE_TARGET = RecordRef("rule:authoritative", 4)
P01_CERTIFICATE_TARGET = RecordRef("certificate:authoritative", 6)

SUPPLEMENTAL_MUTATION_WITNESSES = {
    "IR-03": (
        "tests.test_binding_plan.BindingPlanTests."
        "test_ir03_identity_gate_aggregates_all_invalid_targets"
    ),
}


def make_extracted_source(
    payload: bytes,
    *,
    provider_id: str = "fixture-provider",
    requested_model: str = "fixture-model",
    provider_request_id: str = "fixture-request",
    raw_response: bytes | None = None,
) -> ExtractedDraft:
    envelope = capture_generation(
        attempt=AttemptRef("session:binding", 1),
        relation=AttemptRelation.INITIAL,
        parent=None,
        provider_id=provider_id,
        adapter_id="fixture-adapter",
        adapter_version="1",
        requested_model=requested_model,
        reported_model=requested_model,
        prompt_template_id="binding-fixture",
        prompt_template_version="1",
        prompt=b"Produce one PFF draft.\n",
        public_parameters={},
        raw_response=(
            OPEN_LINE + payload + CLOSE_LINE
            if raw_response is None
            else raw_response
        ),
        finish_reason="stop",
        provider_request_id=provider_request_id,
    )
    return extract_draft(envelope)


def make_s00_source() -> ExtractedDraft:
    return make_extracted_source(S00_PAYLOAD)


def make_s01_source() -> ExtractedDraft:
    return make_extracted_source(S01_PAYLOAD)


def make_s02_source() -> ExtractedDraft:
    return make_extracted_source(S02_PAYLOAD)


def make_population_source(*, extra_atom: bool) -> ExtractedDraft:
    atoms: list[dict[str, object]] = [
        {
            "id": "a",
            "version": 1,
            "predicate": "test.derived",
            "args": ["entity:e"],
            "frame": "frame:1",
            "grade": None,
        }
    ]
    if extra_atom:
        atoms.append(
            {
                "id": "b",
                "version": 1,
                "predicate": "test.derived",
                "args": ["entity:b"],
                "frame": "frame:1",
                "grade": None,
            }
        )
    rules = [
        {
            "id": f"r:{index:04d}",
            "version": 1,
            "head": {"id": "a", "version": 1},
            "positive": [],
            "evidence_request": {"id": f"e:{index:04d}", "version": 1},
        }
        for index in range(4_096)
    ]
    requests = [
        {
            "id": f"e:{index:04d}",
            "version": 1,
            "kind": "certificate",
            "subject": {"id": f"r:{index:04d}", "version": 1},
            "question": "Q.",
        }
        for index in range(4_096)
    ]
    payload = json.dumps(
        {
            "schema": "pff-draft/0.1",
            "atoms": atoms,
            "rules": rules,
            "evidence_requests": requests,
        },
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return make_extracted_source(payload)


def make_population_policy(
    source: ExtractedDraft,
    *,
    extra_atom: bool,
) -> DraftBindingPolicy:
    atom_bindings = (
        RecordIdentityBinding(
            DraftRecordKind.ATOM,
            DraftRef("a", 1),
            RecordRef("atom:max", 1),
        ),
    ) + (
        (
            RecordIdentityBinding(
                DraftRecordKind.ATOM,
                DraftRef("b", 1),
                RecordRef("atom:max:b", 1),
            ),
        )
        if extra_atom
        else ()
    )
    return DraftBindingPolicy(
        profile="pff-draft-binding-policy/0.1",
        policy_id="policy:max-plus-atom" if extra_atom else "policy:max",
        version=1,
        source_payload_sha256=source.payload_sha256,
        package_id="package:max-plus-atom" if extra_atom else "package:max",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
        record_bindings=atom_bindings
        + tuple(
            RecordIdentityBinding(
                DraftRecordKind.RULE,
                DraftRef(f"r:{index:04d}", 1),
                RecordRef(f"rule:max:{index:04d}", 1),
            )
            for index in range(4_096)
        ),
        evidence_bindings=tuple(
            EvidenceBinding(
                request=DraftRef(f"e:{index:04d}", 1),
                certificate=RecordRef(f"certificate:max:{index:04d}", 1),
                checker_id="rule-witness/v1",
                checker_version=1,
                authority_id="evidence-authority:test",
                authority_version=2,
            )
            for index in range(4_096)
        ),
    )


def _certificate_checker(
    checker_id: str,
    *,
    version: int,
    subject_kind: RecordKind,
) -> CheckerContract:
    return CheckerContract(
        checker_id=checker_id,
        version=version,
        uses=frozenset({CheckerUse.CERTIFICATE}),
        certificate_subject_kinds=frozenset({subject_kind}),
        detail_fields=(
            CheckerDetailField(
                key="witness",
                value_type=CheckerDetailType.NONEMPTY_STRING,
            ),
        ),
    )


def make_rc1(
    *,
    registry_version: int = 1,
    checker_versions: dict[str, int] | None = None,
) -> RegistryCatalog:
    versions = {} if checker_versions is None else checker_versions
    checkers = (
        _certificate_checker(
            "rule-witness/v1",
            version=versions.get("rule-witness/v1", 1),
            subject_kind=RecordKind.RULE,
        ),
        _certificate_checker(
            "rule-witness-alt/v1",
            version=versions.get("rule-witness-alt/v1", 1),
            subject_kind=RecordKind.RULE,
        ),
        CheckerContract(
            checker_id="two-detail/v1",
            version=versions.get("two-detail/v1", 1),
            uses=frozenset({CheckerUse.CERTIFICATE}),
            certificate_subject_kinds=frozenset({RecordKind.RULE}),
            detail_fields=(
                CheckerDetailField(
                    key="count",
                    value_type=CheckerDetailType.INTEGER,
                ),
                CheckerDetailField(
                    key="witness",
                    value_type=CheckerDetailType.NONEMPTY_STRING,
                ),
            ),
        ),
        _certificate_checker(
            "atom-only/v1",
            version=versions.get("atom-only/v1", 1),
            subject_kind=RecordKind.ATOM,
        ),
        _certificate_checker(
            "rule-forbidden/v1",
            version=versions.get("rule-forbidden/v1", 1),
            subject_kind=RecordKind.RULE,
        ),
        CheckerContract(
            checker_id="closure-only/v1",
            version=versions.get("closure-only/v1", 1),
            uses=frozenset({CheckerUse.CLOSURE}),
            local_closure_semantics=LocalClosureSemantics.NONE,
            closure_selector_kinds=frozenset({RecordKind.ATOM}),
            closure_frame_policy_id="frame:exact-package",
        ),
    )
    registry = PredicateRegistry(
        registry_id="test-registry/1",
        version=registry_version,
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
        ),
        checker_contracts=checkers,
        predicates=(
            PredicateDefinition(
                predicate_id="test.derived",
                version=1,
                arg_type_ids=("entity_ref",),
                frame_policy_id="frame:exact-package",
                grade_policy=GradePolicy.FORBIDDEN,
                computability_class=ComputabilityClass.FIN,
                primitive_allowed=False,
                checker_contract_ids=frozenset(
                    {
                        "atom-only/v1",
                        "rule-witness-alt/v1",
                        "rule-witness/v1",
                        "two-detail/v1",
                    }
                ),
                contrary_policy_id="contrary:forbidden",
            ),
        ),
    )
    return RegistryCatalog(registries=(registry,))


def make_p00_policy(source: ExtractedDraft | None = None) -> DraftBindingPolicy:
    actual_source = make_s00_source() if source is None else source
    return DraftBindingPolicy(
        profile="pff-draft-binding-policy/0.1",
        policy_id="policy:empty",
        version=1,
        source_payload_sha256=actual_source.payload_sha256,
        package_id="package:empty",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
        record_bindings=(),
        evidence_bindings=(),
    )


def make_p01_policy(source: ExtractedDraft | None = None) -> DraftBindingPolicy:
    actual_source = make_s01_source() if source is None else source
    return DraftBindingPolicy(
        profile="pff-draft-binding-policy/0.1",
        policy_id="policy:test",
        version=3,
        source_payload_sha256=actual_source.payload_sha256,
        package_id="package:bound-1",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
        record_bindings=(
            RecordIdentityBinding(
                DraftRecordKind.ATOM,
                P01_ATOM_SOURCE,
                P01_ATOM_TARGET,
            ),
            RecordIdentityBinding(
                DraftRecordKind.RULE,
                P01_RULE_SOURCE,
                P01_RULE_TARGET,
            ),
        ),
        evidence_bindings=(
            EvidenceBinding(
                request=P01_REQUEST_SOURCE,
                certificate=P01_CERTIFICATE_TARGET,
                checker_id="rule-witness/v1",
                checker_version=1,
                authority_id="evidence-authority:test",
                authority_version=2,
            ),
        ),
    )


def make_p02_policy(
    source: ExtractedDraft | None = None,
    *,
    reverse_submission: bool = False,
) -> DraftBindingPolicy:
    actual_source = make_s02_source() if source is None else source
    records = (
        RecordIdentityBinding(
            DraftRecordKind.ATOM,
            DraftRef("local:a", 1),
            RecordRef("atom:rich:a", 11),
        ),
        RecordIdentityBinding(
            DraftRecordKind.ATOM,
            DraftRef("local:a", 2),
            RecordRef("atom:rich:a", 12),
        ),
        RecordIdentityBinding(
            DraftRecordKind.ATOM,
            DraftRef("local:b", 1),
            RecordRef("atom:rich:b", 11),
        ),
        RecordIdentityBinding(
            DraftRecordKind.RULE,
            DraftRef("local:r-a", 1),
            RecordRef("rule:rich:a", 21),
        ),
        RecordIdentityBinding(
            DraftRecordKind.RULE,
            DraftRef("local:r-a", 2),
            RecordRef("rule:rich:a", 22),
        ),
        RecordIdentityBinding(
            DraftRecordKind.RULE,
            DraftRef("local:r-b", 1),
            RecordRef("rule:rich:b", 21),
        ),
    )
    evidence = tuple(
        EvidenceBinding(
            request=request,
            certificate=certificate,
            checker_id="rule-witness/v1",
            checker_version=1,
            authority_id="evidence-authority:test",
            authority_version=2,
        )
        for request, certificate in (
            (DraftRef("local:e-a", 1), RecordRef("certificate:rich:a", 31)),
            (DraftRef("local:e-a", 2), RecordRef("certificate:rich:a", 32)),
            (DraftRef("local:e-b", 1), RecordRef("certificate:rich:b", 31)),
        )
    )
    return DraftBindingPolicy(
        profile="pff-draft-binding-policy/0.1",
        policy_id="policy:rich",
        version=1,
        source_payload_sha256=actual_source.payload_sha256,
        package_id="package:rich",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
        record_bindings=tuple(reversed(records)) if reverse_submission else records,
        evidence_bindings=(
            tuple(reversed(evidence)) if reverse_submission else evidence
        ),
    )


def make_p01_plan():
    source = make_s01_source()
    return plan_draft_binding(source, make_p01_policy(source), make_rc1())


def replace_record_target(
    policy: DraftBindingPolicy,
    kind: DraftRecordKind,
    target: RecordRef,
) -> DraftBindingPolicy:
    return replace(
        policy,
        record_bindings=tuple(
            replace(binding, target=target)
            if binding.source_kind is kind
            else binding
            for binding in policy.record_bindings
        ),
    )


def replace_evidence_route(
    policy: DraftBindingPolicy,
    **changes: object,
) -> DraftBindingPolicy:
    return replace(
        policy,
        evidence_bindings=(
            replace(policy.evidence_bindings[0], **changes),
        ),
    )


def make_single_rule_policy(
    source: ExtractedDraft,
    *,
    policy_id: str,
    package_id: str,
    atom_routes: tuple[tuple[DraftRef, RecordRef], ...],
    rule_source: DraftRef,
    rule_target: RecordRef,
    request_source: DraftRef,
    certificate_target: RecordRef,
) -> DraftBindingPolicy:
    return DraftBindingPolicy(
        profile="pff-draft-binding-policy/0.1",
        policy_id=policy_id,
        version=1,
        source_payload_sha256=source.payload_sha256,
        package_id=package_id,
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="test-registry/1",
        registry_version=1,
        record_bindings=tuple(
            RecordIdentityBinding(DraftRecordKind.ATOM, local, target)
            for local, target in atom_routes
        )
        + (
            RecordIdentityBinding(
                DraftRecordKind.RULE,
                rule_source,
                rule_target,
            ),
        ),
        evidence_bindings=(
            EvidenceBinding(
                request=request_source,
                certificate=certificate_target,
                checker_id="rule-witness/v1",
                checker_version=1,
                authority_id="evidence-authority:test",
                authority_version=2,
            ),
        ),
    )


class BindingPlanTests(unittest.TestCase):
    def assert_binding_error(
        self,
        expected: tuple[BindingIssue, ...],
        source: ExtractedDraft,
        policy: DraftBindingPolicy,
        catalog: RegistryCatalog,
    ) -> None:
        with self.assertRaises(DraftBindingError) as caught:
            plan_draft_binding(source, policy, catalog)
        self.assertEqual(caught.exception.issues, expected)

    def test_f00_empty_plan_is_a_complete_success(self) -> None:
        source = make_s00_source()
        policy = make_p00_policy(source)
        catalog = make_rc1()

        plan = plan_draft_binding(source, policy, catalog)

        self.assertEqual(plan.profile, "pff-draft-binding-plan/0.1")
        self.assertIs(plan.source, source)
        self.assertIs(plan.policy, policy)
        self.assertIs(plan.catalog, catalog)
        self.assertIs(plan.registry, catalog.lookup("test-registry/1"))
        self.assertEqual(
            plan.header,
            PackageHeader(
                schema="pff-core/0.1",
                package_id="package:empty",
                cut_id="cut:1",
                frame_id="frame:1",
                registry_id="test-registry/1",
                parent_package_hash=None,
                metadata={},
            ),
        )
        self.assertEqual(plan.atoms, ())
        self.assertEqual(plan.rules, ())
        self.assertEqual(plan.tasks, ())
        self.assertEqual(plan.origins, ())

    def test_f01_f29_f61_exact_plan_projection_and_indexes(self) -> None:
        source = make_s01_source()
        policy = make_p01_policy(source)
        catalog = make_rc1()

        plan = plan_draft_binding(source, policy, catalog)

        atom = AtomRecord(
            id="atom:authoritative",
            version=2,
            predicate="test.derived",
            args=("entity:e",),
            frame="frame:1",
            grade=None,
            primitive=False,
        )
        rule = RuleRecord(
            id="rule:authoritative",
            version=4,
            head=P01_ATOM_TARGET,
            positive=frozenset(),
            certificate=P01_CERTIFICATE_TARGET,
            negative=frozenset(),
            faces=frozenset(),
        )
        task = EvidenceTask(
            profile="pff-evidence-task/0.1",
            source_payload_sha256=source.payload_sha256,
            policy_id="policy:test",
            policy_version=3,
            subject_rule=rule,
            request_kind="certificate",
            request=P01_REQUEST_SOURCE,
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
        origins = (
            BindingOrigin(
                RecordKind.ATOM,
                P01_ATOM_TARGET,
                BindingRole.DRAFT_ATOM,
                DraftSource(DraftRecordKind.ATOM, P01_ATOM_SOURCE),
            ),
            BindingOrigin(
                RecordKind.RULE,
                P01_RULE_TARGET,
                BindingRole.DRAFT_RULE,
                DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE),
            ),
            BindingOrigin(
                RecordKind.CERTIFICATE,
                P01_CERTIFICATE_TARGET,
                BindingRole.EVIDENCE_CERTIFICATE,
                DraftSource(DraftRecordKind.EVIDENCE_REQUEST, P01_REQUEST_SOURCE),
            ),
        )

        self.assertEqual(plan.atoms, (atom,))
        self.assertEqual(plan.rules, (rule,))
        self.assertEqual(plan.tasks, (task,))
        self.assertEqual(plan.origins, origins)
        self.assertEqual(
            plan.target_for(DraftRecordKind.ATOM, P01_ATOM_SOURCE),
            P01_ATOM_TARGET,
        )
        self.assertEqual(
            plan.target_for(DraftRecordKind.RULE, P01_RULE_SOURCE),
            P01_RULE_TARGET,
        )
        self.assertEqual(
            plan.target_for(DraftRecordKind.EVIDENCE_REQUEST, P01_REQUEST_SOURCE),
            P01_CERTIFICATE_TARGET,
        )
        self.assertEqual(plan.task_for(P01_REQUEST_SOURCE), task)
        for origin in origins:
            self.assertEqual(
                plan.origin_for(origin.target_kind, origin.target),
                origin,
            )

    def test_f04_f05_f06_p02_projection_order_and_versions(self) -> None:
        source = make_s02_source()
        self.assertEqual(
            source.payload_sha256,
            "sha256:5b6d12fefa5354a9b857fe19f5f9d73c5591ec2414c8c6894d79ed2c66d091ac",
        )
        forward = make_p02_policy(source)
        reverse = make_p02_policy(source, reverse_submission=True)

        self.assertEqual(forward, reverse)
        forward_plan = plan_draft_binding(source, forward, make_rc1())
        reverse_plan = plan_draft_binding(source, reverse, make_rc1())

        self.assertEqual(forward_plan, reverse_plan)
        self.assertEqual(
            tuple(atom.ref for atom in forward_plan.atoms),
            (
                RecordRef("atom:rich:a", 11),
                RecordRef("atom:rich:a", 12),
                RecordRef("atom:rich:b", 11),
            ),
        )
        self.assertEqual(
            tuple(rule.ref for rule in forward_plan.rules),
            (
                RecordRef("rule:rich:a", 21),
                RecordRef("rule:rich:a", 22),
                RecordRef("rule:rich:b", 21),
            ),
        )
        self.assertEqual(
            forward_plan.rules[0].positive,
            frozenset({RecordRef("atom:rich:b", 11)}),
        )
        self.assertEqual(
            tuple(task.request for task in forward_plan.tasks),
            (
                DraftRef("local:e-a", 1),
                DraftRef("local:e-a", 2),
                DraftRef("local:e-b", 1),
            ),
        )
        self.assertEqual(len(forward_plan.origins), 9)
        self.assertEqual(
            forward_plan.target_for(DraftRecordKind.ATOM, DraftRef("local:a", 1)),
            RecordRef("atom:rich:a", 11),
        )
        self.assertEqual(
            forward_plan.target_for(DraftRecordKind.ATOM, DraftRef("local:a", 2)),
            RecordRef("atom:rich:a", 12),
        )

    def test_f11_equal_target_ids_order_by_numeric_version(self) -> None:
        source = make_s02_source()
        ordinary = make_p02_policy(source)
        policy = replace(
            ordinary,
            record_bindings=tuple(
                (
                    replace(binding, target=RecordRef("target:same", 2))
                    if binding.source_kind is DraftRecordKind.ATOM
                    and binding.source == DraftRef("local:a", 1)
                    else (
                        replace(binding, target=RecordRef("target:same", 10))
                        if binding.source_kind is DraftRecordKind.ATOM
                        and binding.source == DraftRef("local:a", 2)
                        else binding
                    )
                )
                for binding in ordinary.record_bindings
            ),
        )

        plan = plan_draft_binding(source, policy, make_rc1())

        self.assertEqual(
            tuple(atom.ref for atom in plan.atoms if atom.id == "target:same"),
            (RecordRef("target:same", 2), RecordRef("target:same", 10)),
        )

    def test_c00_c03_planner_requires_exact_boundary_types(self) -> None:
        source = make_s01_source()
        policy = make_p01_policy(source)
        catalog = make_rc1()

        wrong_calls = (
            lambda: plan_draft_binding(source.draft, policy, catalog),  # type: ignore[arg-type]
            lambda: plan_draft_binding(object(), policy, catalog),  # type: ignore[arg-type]
            lambda: plan_draft_binding(source, object(), catalog),  # type: ignore[arg-type]
            lambda: plan_draft_binding(source, policy, object()),  # type: ignore[arg-type]
        )
        for call in wrong_calls:
            with self.subTest(call=call):
                with self.assertRaises(TypeError):
                    call()

    def test_f15_source_gate_precedes_catalog_lookup(self) -> None:
        source = make_s01_source()
        policy = replace(
            make_p01_policy(source),
            source_payload_sha256="sha256:" + "0" * 64,
        )
        expected = (
            BindingIssue(
                BindingPhase.SOURCE,
                BindingCode.SOURCE_PAYLOAD_MISMATCH,
                "/source/payload_sha256",
                details=(
                    "actual=" + source.payload_sha256,
                    "expected=sha256:" + "0" * 64,
                ),
            ),
        )

        def forbidden_lookup(self: RegistryCatalog, registry_id: str):
            del self, registry_id
            raise AssertionError("catalog lookup crossed the source gate")

        with patch.object(RegistryCatalog, "lookup", forbidden_lookup):
            self.assert_binding_error(expected, source, policy, make_rc1())

    def test_f16_f19_f81_f82_coverage_issues_are_complete(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        catalog = make_rc1()

        missing_atom = replace(
            ordinary,
            record_bindings=tuple(
                binding
                for binding in ordinary.record_bindings
                if binding.source_kind is not DraftRecordKind.ATOM
            ),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.RECORD_BINDING_MISSING,
                    "/policy/record_bindings",
                    sources=(DraftSource(DraftRecordKind.ATOM, P01_ATOM_SOURCE),),
                ),
            ),
            source,
            missing_atom,
            catalog,
        )

        one_extra_record = replace(
            ordinary,
            record_bindings=ordinary.record_bindings
            + (
                RecordIdentityBinding(
                    DraftRecordKind.ATOM,
                    DraftRef("absent", 1),
                    RecordRef("atom:absent", 1),
                ),
            ),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.RECORD_BINDING_EXTRA,
                    "/policy/record_bindings",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, DraftRef("absent", 1)),
                    ),
                    targets=(RecordRef("atom:absent", 1),),
                ),
            ),
            source,
            one_extra_record,
            catalog,
        )

        extra_record_rows = ordinary.record_bindings + (
            RecordIdentityBinding(
                DraftRecordKind.ATOM,
                DraftRef("absent:a", 1),
                RecordRef("extra:same", 1),
            ),
            RecordIdentityBinding(
                DraftRecordKind.RULE,
                DraftRef("absent:r", 1),
                RecordRef("extra:same", 1),
            ),
        )
        extra_records = replace(ordinary, record_bindings=extra_record_rows)
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.RECORD_BINDING_EXTRA,
                    "/policy/record_bindings",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, DraftRef("absent:a", 1)),
                        DraftSource(DraftRecordKind.RULE, DraftRef("absent:r", 1)),
                    ),
                    targets=(RecordRef("extra:same", 1),),
                ),
            ),
            source,
            extra_records,
            catalog,
        )

        missing_evidence = replace(ordinary, evidence_bindings=())
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.EVIDENCE_BINDING_MISSING,
                    "/policy/evidence_bindings",
                    sources=(
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            P01_REQUEST_SOURCE,
                        ),
                    ),
                ),
            ),
            source,
            missing_evidence,
            catalog,
        )

        one_extra_evidence = replace(
            ordinary,
            evidence_bindings=ordinary.evidence_bindings
            + (
                replace(
                    ordinary.evidence_bindings[0],
                    request=DraftRef("absent", 1),
                    certificate=RecordRef("certificate:absent", 1),
                ),
            ),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.EVIDENCE_BINDING_EXTRA,
                    "/policy/evidence_bindings",
                    sources=(
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            DraftRef("absent", 1),
                        ),
                    ),
                    targets=(RecordRef("certificate:absent", 1),),
                ),
            ),
            source,
            one_extra_evidence,
            catalog,
        )

        extra_evidence_rows = ordinary.evidence_bindings + (
            replace(
                ordinary.evidence_bindings[0],
                request=DraftRef("absent:a", 1),
                certificate=RecordRef("extra:certificate:same", 1),
            ),
            replace(
                ordinary.evidence_bindings[0],
                request=DraftRef("absent:b", 1),
                certificate=RecordRef("extra:certificate:same", 1),
            ),
        )
        extra_evidence = replace(ordinary, evidence_bindings=extra_evidence_rows)
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.EVIDENCE_BINDING_EXTRA,
                    "/policy/evidence_bindings",
                    sources=(
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            DraftRef("absent:a", 1),
                        ),
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            DraftRef("absent:b", 1),
                        ),
                    ),
                    targets=(RecordRef("extra:certificate:same", 1),),
                ),
            ),
            source,
            extra_evidence,
            catalog,
        )

    def test_f86_coverage_precedes_invalid_extra_target_encoding(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        policy = replace(
            ordinary,
            record_bindings=ordinary.record_bindings
            + (
                RecordIdentityBinding(
                    DraftRecordKind.ATOM,
                    DraftRef("absent:a", 1),
                    RecordRef("\ud801", 1),
                ),
                RecordIdentityBinding(
                    DraftRecordKind.RULE,
                    DraftRef("absent:b", 1),
                    RecordRef("\ud800", 1),
                ),
            ),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.RECORD_BINDING_EXTRA,
                    "/policy/record_bindings",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, DraftRef("absent:a", 1)),
                        DraftSource(DraftRecordKind.RULE, DraftRef("absent:b", 1)),
                    ),
                    targets=(RecordRef("\ud800", 1), RecordRef("\ud801", 1)),
                ),
            ),
            source,
            policy,
            make_rc1(),
        )

    def test_f62_f66_gate_precedence_uses_exact_single_controls(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        catalog = make_rc1()
        missing_atom_bindings = tuple(
            binding
            for binding in ordinary.record_bindings
            if binding.source_kind is not DraftRecordKind.ATOM
        )

        source_and_coverage = replace(
            ordinary,
            source_payload_sha256="sha256:" + "0" * 64,
            record_bindings=missing_atom_bindings,
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.SOURCE,
                    BindingCode.SOURCE_PAYLOAD_MISMATCH,
                    "/source/payload_sha256",
                    details=(
                        "actual=" + source.payload_sha256,
                        "expected=sha256:" + "0" * 64,
                    ),
                ),
            ),
            source,
            source_and_coverage,
            catalog,
        )

        registry_and_routing = replace_evidence_route(
            replace(ordinary, registry_version=2),
            checker_id="missing-checker",
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.REGISTRY,
                    BindingCode.REGISTRY_VERSION_MISMATCH,
                    "/policy/registry_version",
                    details=("actual=2", "expected=1"),
                ),
            ),
            source,
            registry_and_routing,
            catalog,
        )

        coverage_and_routing = replace_evidence_route(
            replace(ordinary, record_bindings=missing_atom_bindings),
            checker_id="missing-checker",
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.RECORD_BINDING_MISSING,
                    "/policy/record_bindings",
                    sources=(DraftSource(DraftRecordKind.ATOM, P01_ATOM_SOURCE),),
                ),
            ),
            source,
            coverage_and_routing,
            catalog,
        )

        shared_source = make_extracted_source(S03_PAYLOAD)
        shared = DraftRef("shared", 13)
        collision = RecordRef("collision:shared", 1)
        identity_and_routing = make_single_rule_policy(
            shared_source,
            policy_id="policy:shared",
            package_id="package:shared",
            atom_routes=((shared, collision),),
            rule_source=shared,
            rule_target=collision,
            request_source=shared,
            certificate_target=RecordRef("certificate:shared", 301),
        )
        identity_and_routing = replace_evidence_route(
            identity_and_routing,
            checker_id="missing-checker",
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.IDENTITY,
                    BindingCode.TARGET_REF_COLLISION,
                    "/policy/targets",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, shared),
                        DraftSource(DraftRecordKind.RULE, shared),
                    ),
                    targets=(collision,),
                ),
            ),
            shared_source,
            identity_and_routing,
            catalog,
        )

        request_source = DraftSource(
            DraftRecordKind.EVIDENCE_REQUEST,
            P01_REQUEST_SOURCE,
        )
        rule_source = DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE)
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_VERSION_MISMATCH,
                    "/policy/evidence_bindings/checker_version",
                    sources=(rule_source, request_source),
                    targets=(P01_CERTIFICATE_TARGET, P01_RULE_TARGET),
                    details=("actual=2", "expected=1"),
                ),
            ),
            source,
            replace_evidence_route(
                ordinary,
                checker_id="closure-only/v1",
                checker_version=2,
            ),
            catalog,
        )

    def test_f08_f09_f10_global_target_collisions_are_typed(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        atom_certificate_collision = replace_evidence_route(
            ordinary,
            certificate=P01_ATOM_TARGET,
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.IDENTITY,
                    BindingCode.TARGET_REF_COLLISION,
                    "/policy/targets",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, P01_ATOM_SOURCE),
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            P01_REQUEST_SOURCE,
                        ),
                    ),
                    targets=(P01_ATOM_TARGET,),
                ),
            ),
            source,
            atom_certificate_collision,
            make_rc1(),
        )

        rule_certificate_collision = replace_evidence_route(
            ordinary,
            certificate=P01_RULE_TARGET,
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.IDENTITY,
                    BindingCode.TARGET_REF_COLLISION,
                    "/policy/targets",
                    sources=(
                        DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE),
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            P01_REQUEST_SOURCE,
                        ),
                    ),
                    targets=(P01_RULE_TARGET,),
                ),
            ),
            source,
            rule_certificate_collision,
            make_rc1(),
        )

        shared_source = make_extracted_source(S03_PAYLOAD)
        local = DraftRef("shared", 13)
        collision = RecordRef("collision:shared", 1)
        shared_policy = make_single_rule_policy(
            shared_source,
            policy_id="policy:shared",
            package_id="package:shared",
            atom_routes=((local, collision),),
            rule_source=local,
            rule_target=collision,
            request_source=local,
            certificate_target=RecordRef("certificate:shared", 301),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.IDENTITY,
                    BindingCode.TARGET_REF_COLLISION,
                    "/policy/targets",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, local),
                        DraftSource(DraftRecordKind.RULE, local),
                    ),
                    targets=(collision,),
                ),
            ),
            shared_source,
            shared_policy,
            make_rc1(),
        )

    def test_f12_f14_f72_f76_f83_f84_target_boundaries(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        failures = (
            (
                RecordRef("", 2),
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
            ),
            (
                RecordRef("__pff__:bad", 1),
                BindingCode.TARGET_RESERVED_ID,
                "/policy/targets/id",
            ),
            (
                RecordRef("\ud800", 1),
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
            ),
            (
                RecordRef("x" * 262_145, 1),
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
            ),
            (
                RecordRef("é" * 131_072 + "a", 1),
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
            ),
            (
                RecordRef("atom:authoritative", 0),
                BindingCode.TARGET_INVALID_VERSION,
                "/policy/targets/version",
            ),
            (
                RecordRef("atom:authoritative", -1),
                BindingCode.TARGET_INVALID_VERSION,
                "/policy/targets/version",
            ),
            (
                RecordRef("atom:authoritative", MAX_VERSION + 1),
                BindingCode.TARGET_INVALID_VERSION,
                "/policy/targets/version",
            ),
        )
        for target, code, path in failures:
            with self.subTest(target=target, code=code):
                policy = replace_record_target(
                    ordinary,
                    DraftRecordKind.ATOM,
                    target,
                )
                self.assert_binding_error(
                    (
                        BindingIssue(
                            BindingPhase.IDENTITY,
                            code,
                            path,
                            sources=(
                                DraftSource(
                                    DraftRecordKind.ATOM,
                                    P01_ATOM_SOURCE,
                                ),
                            ),
                            targets=(target,),
                        ),
                    ),
                    source,
                    policy,
                    make_rc1(),
                )

        for target in (
            RecordRef("é" * 131_072, 1),
            RecordRef("atom:authoritative", MAX_VERSION),
        ):
            with self.subTest(valid_target=target):
                plan = plan_draft_binding(
                    source,
                    replace_record_target(
                        ordinary,
                        DraftRecordKind.ATOM,
                        target,
                    ),
                    make_rc1(),
                )
                self.assertEqual(plan.atoms[0].ref, target)

    def test_ir03_identity_gate_aggregates_all_invalid_targets(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        atom_target = RecordRef("", P01_ATOM_TARGET.version)
        rule_target = RecordRef("\ud800", P01_RULE_TARGET.version)
        policy = replace_record_target(
            replace_record_target(
                ordinary,
                DraftRecordKind.ATOM,
                atom_target,
            ),
            DraftRecordKind.RULE,
            rule_target,
        )
        expected = (
            BindingIssue(
                BindingPhase.IDENTITY,
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
                sources=(
                    DraftSource(DraftRecordKind.ATOM, P01_ATOM_SOURCE),
                ),
                targets=(atom_target,),
            ),
            BindingIssue(
                BindingPhase.IDENTITY,
                BindingCode.TARGET_INVALID_ID,
                "/policy/targets/id",
                sources=(
                    DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE),
                ),
                targets=(rule_target,),
            ),
        )

        self.assertEqual(
            SUPPLEMENTAL_MUTATION_WITNESSES,
            {
                "IR-03": (
                    "tests.test_binding_plan.BindingPlanTests."
                    "test_ir03_identity_gate_aggregates_all_invalid_targets"
                ),
            },
        )

        def forbidden_lookup(self: RegistryCatalog, registry_id: str):
            del self, registry_id
            raise AssertionError("registry lookup crossed the identity gate")

        with patch.object(RegistryCatalog, "lookup", forbidden_lookup):
            self.assert_binding_error(expected, source, policy, make_rc1())

    def test_f20_f21_f96_f97_f98_f99_registry_version_gate(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)

        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.REGISTRY,
                    BindingCode.UNKNOWN_REGISTRY,
                    "/policy/registry_id",
                    details=("missing-registry",),
                ),
            ),
            source,
            replace(ordinary, registry_id="missing-registry"),
            make_rc1(),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.REGISTRY,
                    BindingCode.REGISTRY_VERSION_MISMATCH,
                    "/policy/registry_version",
                    details=("actual=2", "expected=1"),
                ),
            ),
            source,
            replace(ordinary, registry_version=2),
            make_rc1(),
        )

        maximum_policy = replace(ordinary, registry_version=MAX_VERSION)
        maximum_plan = plan_draft_binding(
            source,
            maximum_policy,
            make_rc1(registry_version=MAX_VERSION),
        )
        self.assertEqual(maximum_plan.registry.version, MAX_VERSION)
        self.assertEqual(maximum_plan.tasks[0].registry_version, MAX_VERSION)

        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.REGISTRY,
                    BindingCode.REGISTRY_VERSION_MISMATCH,
                    "/policy/registry_version",
                    details=(
                        "actual=1",
                        "expected=9223372036854775807",
                    ),
                ),
            ),
            source,
            ordinary,
            make_rc1(registry_version=MAX_VERSION),
        )

        unsupported_issue = (
            BindingIssue(
                BindingPhase.REGISTRY,
                BindingCode.REGISTRY_VERSION_UNSUPPORTED,
                "/catalog/registry/version",
                details=(
                    "registry_id=test-registry/1",
                    "supported_max=9223372036854775807",
                ),
            ),
        )
        self.assert_binding_error(
            unsupported_issue,
            source,
            ordinary,
            make_rc1(registry_version=MAX_VERSION + 1),
        )
        missing_checker_policy = replace_evidence_route(
            ordinary,
            checker_id="missing-checker",
        )
        self.assert_binding_error(
            unsupported_issue,
            source,
            missing_checker_policy,
            make_rc1(registry_version=UNBOUNDED_EXTERNAL_VERSION),
        )

    def test_f22_f24_f25_f26_f27_f28_f66_f78_routing_diagnostics(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        request_source = DraftSource(
            DraftRecordKind.EVIDENCE_REQUEST,
            P01_REQUEST_SOURCE,
        )
        rule_source = DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE)
        route_targets = (P01_CERTIFICATE_TARGET, P01_RULE_TARGET)

        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_UNKNOWN,
                    "/policy/evidence_bindings/checker_id",
                    sources=(rule_source, request_source),
                    targets=route_targets,
                    details=("missing-checker",),
                ),
            ),
            source,
            replace_evidence_route(ordinary, checker_id="missing-checker"),
            make_rc1(),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_VERSION_MISMATCH,
                    "/policy/evidence_bindings/checker_version",
                    sources=(rule_source, request_source),
                    targets=route_targets,
                    details=("actual=2", "expected=1"),
                ),
            ),
            source,
            replace_evidence_route(ordinary, checker_version=2),
            make_rc1(),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_VERSION_MISMATCH,
                    "/policy/evidence_bindings/checker_version",
                    sources=(rule_source, request_source),
                    targets=route_targets,
                    details=("actual=2", "expected=1"),
                ),
            ),
            source,
            replace_evidence_route(
                ordinary,
                checker_id="closure-only/v1",
                checker_version=2,
            ),
            make_rc1(),
        )
        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_NOT_PERMITTED,
                    "/policy/evidence_bindings/checker_id",
                    sources=(rule_source, request_source),
                    targets=route_targets,
                    details=("reason=predicate",),
                ),
            ),
            source,
            replace_evidence_route(ordinary, checker_id="rule-forbidden/v1"),
            make_rc1(),
        )
        for checker_id, reasons in (
            (
                "closure-only/v1",
                ("reason=predicate", "reason=subject", "reason=use"),
            ),
            ("atom-only/v1", ("reason=subject",)),
        ):
            with self.subTest(checker_id=checker_id):
                self.assert_binding_error(
                    (
                        BindingIssue(
                            BindingPhase.ROUTING,
                            BindingCode.CHECKER_NOT_PERMITTED,
                            "/policy/evidence_bindings/checker_id",
                            sources=(rule_source, request_source),
                            targets=route_targets,
                            details=reasons,
                        ),
                    ),
                    source,
                    replace_evidence_route(ordinary, checker_id=checker_id),
                    make_rc1(),
                )

        unknown_source = make_extracted_source(S04H_PAYLOAD)
        unknown_policy = make_single_rule_policy(
            unknown_source,
            policy_id="policy:unknown-head",
            package_id="package:unknown-head",
            atom_routes=(
                (DraftRef("atom:unknown", 1), RecordRef("atom:authority:unknown", 1)),
            ),
            rule_source=DraftRef("rule:unknown-head", 1),
            rule_target=RecordRef("rule:authority:unknown-head", 1),
            request_source=DraftRef("evidence:unknown-head", 1),
            certificate_target=RecordRef("certificate:authority:unknown-head", 1),
        )
        unknown_head_issue = BindingIssue(
            BindingPhase.ROUTING,
            BindingCode.HEAD_PREDICATE_UNKNOWN,
            "/draft/rules/head/predicate",
            sources=(
                DraftSource(
                    DraftRecordKind.ATOM,
                    DraftRef("atom:unknown", 1),
                ),
                DraftSource(
                    DraftRecordKind.RULE,
                    DraftRef("rule:unknown-head", 1),
                ),
            ),
            targets=(
                RecordRef("atom:authority:unknown", 1),
                RecordRef("rule:authority:unknown-head", 1),
            ),
            details=("test.unknown",),
        )
        self.assert_binding_error(
            (unknown_head_issue,),
            unknown_source,
            unknown_policy,
            make_rc1(),
        )
        unknown_policy = replace_evidence_route(
            unknown_policy,
            checker_id="closure-only/v1",
        )
        self.assert_binding_error(
            (
                unknown_head_issue,
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_NOT_PERMITTED,
                    "/policy/evidence_bindings/checker_id",
                    sources=(
                        DraftSource(
                            DraftRecordKind.RULE,
                            DraftRef("rule:unknown-head", 1),
                        ),
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            DraftRef("evidence:unknown-head", 1),
                        ),
                    ),
                    targets=(
                        RecordRef("certificate:authority:unknown-head", 1),
                        RecordRef("rule:authority:unknown-head", 1),
                    ),
                    details=("reason=subject", "reason=use"),
                ),
            ),
            unknown_source,
            unknown_policy,
            make_rc1(),
        )

    def test_f23_unknown_premise_is_deferred_to_package_validation(self) -> None:
        source = make_extracted_source(S04P_PAYLOAD)
        policy = make_single_rule_policy(
            source,
            policy_id="policy:unknown-premise",
            package_id="package:unknown-premise",
            atom_routes=(
                (DraftRef("atom:known", 1), RecordRef("atom:authority:known", 1)),
                (
                    DraftRef("atom:unknown-premise", 1),
                    RecordRef("atom:authority:unknown-premise", 1),
                ),
            ),
            rule_source=DraftRef("rule:known-head", 1),
            rule_target=RecordRef("rule:authority:known-head", 1),
            request_source=DraftRef("evidence:known-head", 1),
            certificate_target=RecordRef("certificate:authority:known-head", 1),
        )

        plan = plan_draft_binding(source, policy, make_rc1())

        self.assertEqual(len(plan.atoms), 2)
        self.assertEqual(
            plan.rules[0].positive,
            frozenset({RecordRef("atom:authority:unknown-premise", 1)}),
        )

    def test_f100_f101_f102_f103_f104_f105_checker_external_version_gate(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        maximum_policy = replace_evidence_route(
            ordinary,
            checker_version=MAX_VERSION,
        )
        maximum_plan = plan_draft_binding(
            source,
            maximum_policy,
            make_rc1(checker_versions={"rule-witness/v1": MAX_VERSION}),
        )
        self.assertEqual(maximum_plan.tasks[0].checker_version, MAX_VERSION)

        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.ROUTING,
                    BindingCode.CHECKER_VERSION_MISMATCH,
                    "/policy/evidence_bindings/checker_version",
                    sources=(
                        DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE),
                        DraftSource(
                            DraftRecordKind.EVIDENCE_REQUEST,
                            P01_REQUEST_SOURCE,
                        ),
                    ),
                    targets=(P01_CERTIFICATE_TARGET, P01_RULE_TARGET),
                    details=(
                        "actual=1",
                        "expected=9223372036854775807",
                    ),
                ),
            ),
            source,
            ordinary,
            make_rc1(checker_versions={"rule-witness/v1": MAX_VERSION}),
        )

        unsupported = BindingIssue(
            BindingPhase.ROUTING,
            BindingCode.CHECKER_VERSION_UNSUPPORTED,
            "/catalog/registry/checker_contracts/version",
            sources=(
                DraftSource(DraftRecordKind.RULE, P01_RULE_SOURCE),
                DraftSource(
                    DraftRecordKind.EVIDENCE_REQUEST,
                    P01_REQUEST_SOURCE,
                ),
            ),
            targets=(P01_CERTIFICATE_TARGET, P01_RULE_TARGET),
            details=(
                "checker_id=rule-witness/v1",
                "supported_max=9223372036854775807",
            ),
        )
        self.assert_binding_error(
            (unsupported,),
            source,
            ordinary,
            make_rc1(
                checker_versions={
                    "rule-witness/v1": MAX_VERSION + 1,
                }
            ),
        )
        self.assert_binding_error(
            (unsupported,),
            source,
            ordinary,
            make_rc1(
                checker_versions={
                    "rule-witness/v1": UNBOUNDED_EXTERNAL_VERSION,
                }
            ),
        )

        closure_policy = replace_evidence_route(
            ordinary,
            checker_id="closure-only/v1",
        )
        closure_unsupported = replace(
            unsupported,
            details=(
                "checker_id=closure-only/v1",
                "supported_max=9223372036854775807",
            ),
        )
        self.assert_binding_error(
            (closure_unsupported,),
            source,
            closure_policy,
            make_rc1(
                checker_versions={
                    "closure-only/v1": UNBOUNDED_EXTERNAL_VERSION,
                }
            ),
        )

        unknown_source = make_extracted_source(S04H_PAYLOAD)
        unknown_policy = make_single_rule_policy(
            unknown_source,
            policy_id="policy:unknown-head",
            package_id="package:unknown-head",
            atom_routes=(
                (DraftRef("atom:unknown", 1), RecordRef("atom:authority:unknown", 1)),
            ),
            rule_source=DraftRef("rule:unknown-head", 1),
            rule_target=RecordRef("rule:authority:unknown-head", 1),
            request_source=DraftRef("evidence:unknown-head", 1),
            certificate_target=RecordRef("certificate:authority:unknown-head", 1),
        )
        with self.assertRaises(DraftBindingError) as caught:
            plan_draft_binding(
                unknown_source,
                unknown_policy,
                make_rc1(
                    checker_versions={
                        "rule-witness/v1": UNBOUNDED_EXTERNAL_VERSION,
                    }
                ),
            )
        self.assertEqual(
            tuple(issue.code for issue in caught.exception.issues),
            (
                BindingCode.CHECKER_VERSION_UNSUPPORTED,
                BindingCode.HEAD_PREDICATE_UNKNOWN,
            ),
        )

    def test_f07_f80_same_local_ref_keeps_three_typed_routes(self) -> None:
        source = make_extracted_source(S03_PAYLOAD)
        local = DraftRef("shared", 13)
        policy = make_single_rule_policy(
            source,
            policy_id="policy:shared",
            package_id="package:shared",
            atom_routes=((local, RecordRef("atom:shared", 101)),),
            rule_source=local,
            rule_target=RecordRef("rule:shared", 201),
            request_source=local,
            certificate_target=RecordRef("certificate:shared", 301),
        )

        plan = plan_draft_binding(source, policy, make_rc1())

        self.assertEqual(
            plan.target_for(DraftRecordKind.ATOM, local),
            RecordRef("atom:shared", 101),
        )
        self.assertEqual(
            plan.target_for(DraftRecordKind.RULE, local),
            RecordRef("rule:shared", 201),
        )
        self.assertEqual(
            plan.target_for(DraftRecordKind.EVIDENCE_REQUEST, local),
            RecordRef("certificate:shared", 301),
        )
        self.assertEqual(plan.rules[0].head, RecordRef("atom:shared", 101))
        self.assertEqual(
            plan.rules[0].positive,
            frozenset({RecordRef("atom:shared", 101)}),
        )

    def test_f90_numeric_versions_drive_every_planning_order(self) -> None:
        source = make_extracted_source(S08_PAYLOAD)
        policy = DraftBindingPolicy(
            profile="pff-draft-binding-policy/0.1",
            policy_id="policy:numeric",
            version=1,
            source_payload_sha256=source.payload_sha256,
            package_id="package:numeric",
            cut_id="cut:1",
            frame_id="frame:1",
            registry_id="test-registry/1",
            registry_version=1,
            record_bindings=(
                RecordIdentityBinding(
                    DraftRecordKind.RULE,
                    DraftRef("r", 10),
                    RecordRef("rule:numeric", 2),
                ),
                RecordIdentityBinding(
                    DraftRecordKind.ATOM,
                    DraftRef("a", 1),
                    RecordRef("atom:numeric", 1),
                ),
                RecordIdentityBinding(
                    DraftRecordKind.RULE,
                    DraftRef("r", 2),
                    RecordRef("rule:numeric", 10),
                ),
            ),
            evidence_bindings=(
                EvidenceBinding(
                    DraftRef("e", 10),
                    RecordRef("certificate:numeric", 2),
                    "rule-witness/v1",
                    1,
                    "evidence-authority:test",
                    2,
                ),
                EvidenceBinding(
                    DraftRef("e", 2),
                    RecordRef("certificate:numeric", 10),
                    "rule-witness/v1",
                    1,
                    "evidence-authority:test",
                    2,
                ),
            ),
        )

        plan = plan_draft_binding(source, policy, make_rc1())

        self.assertEqual(
            tuple(binding.source.version for binding in policy.record_bindings),
            (1, 2, 10),
        )
        self.assertEqual(
            tuple(binding.request.version for binding in policy.evidence_bindings),
            (2, 10),
        )
        self.assertEqual(tuple(rule.version for rule in plan.rules), (2, 10))
        self.assertEqual(tuple(task.request.version for task in plan.tasks), (2, 10))
        self.assertEqual(
            tuple(origin.target.version for origin in plan.origins),
            (1, 2, 10, 2, 10),
        )
        self.assertEqual(plan.rules[0].id, "rule:numeric")
        self.assertEqual(
            plan.target_for(DraftRecordKind.RULE, DraftRef("r", 10)),
            RecordRef("rule:numeric", 2),
        )
        self.assertEqual(
            plan.target_for(DraftRecordKind.RULE, DraftRef("r", 2)),
            RecordRef("rule:numeric", 10),
        )

    def test_f57_provider_and_surrounding_prose_do_not_enter_semantics(self) -> None:
        marker_source = make_s01_source()
        prose_response = (
            b"I think this claim is LIVE and its checker passed.\n"
            + OPEN_LINE
            + S01_PAYLOAD
            + CLOSE_LINE
            + b"\nThe final status is definitely LIVE.\n"
        )
        prose_source = make_extracted_source(
            S01_PAYLOAD,
            provider_id="other-provider",
            requested_model="other-model",
            provider_request_id="other-request",
            raw_response=prose_response,
        )

        marker_plan = plan_draft_binding(
            marker_source,
            make_p01_policy(marker_source),
            make_rc1(),
        )
        prose_plan = plan_draft_binding(
            prose_source,
            make_p01_policy(prose_source),
            make_rc1(),
        )

        self.assertNotEqual(marker_plan.source, prose_plan.source)
        self.assertEqual(marker_plan.header, prose_plan.header)
        self.assertEqual(marker_plan.atoms, prose_plan.atoms)
        self.assertEqual(marker_plan.rules, prose_plan.rules)
        self.assertEqual(marker_plan.tasks, prose_plan.tasks)
        self.assertEqual(marker_plan.origins, prose_plan.origins)

    def test_f91_diagnostic_targets_sort_versions_numerically(self) -> None:
        source = make_s01_source()
        ordinary = make_p01_policy(source)
        policy = replace(
            ordinary,
            record_bindings=ordinary.record_bindings
            + (
                RecordIdentityBinding(
                    DraftRecordKind.ATOM,
                    DraftRef("extra", 2),
                    RecordRef("extra:target", 10),
                ),
                RecordIdentityBinding(
                    DraftRecordKind.ATOM,
                    DraftRef("extra", 10),
                    RecordRef("extra:target", 2),
                ),
            ),
        )

        self.assert_binding_error(
            (
                BindingIssue(
                    BindingPhase.COVERAGE,
                    BindingCode.RECORD_BINDING_EXTRA,
                    "/policy/record_bindings",
                    sources=(
                        DraftSource(DraftRecordKind.ATOM, DraftRef("extra", 2)),
                        DraftSource(DraftRecordKind.ATOM, DraftRef("extra", 10)),
                    ),
                    targets=(
                        RecordRef("extra:target", 2),
                        RecordRef("extra:target", 10),
                    ),
                ),
            ),
            source,
            policy,
            make_rc1(),
        )

    def test_f87_f89_planning_is_total_at_maximum_populations(self) -> None:
        for extra_atom, expected_digest, expected_origin_count in (
            (
                False,
                "sha256:7ae1159951240bcbc3cc3f7de9ea4f887597cb86c91a52807a239a9df6594477",
                8_193,
            ),
            (
                True,
                "sha256:0822658a4ec0690b0684266931984607b8fcc428d3aaacc3aa0397932fb6a026",
                8_194,
            ),
        ):
            with self.subTest(extra_atom=extra_atom):
                source = make_population_source(extra_atom=extra_atom)
                self.assertEqual(source.payload_sha256, expected_digest)
                plan = plan_draft_binding(
                    source,
                    make_population_policy(source, extra_atom=extra_atom),
                    make_rc1(),
                )
                self.assertEqual(len(plan.atoms), 2 if extra_atom else 1)
                self.assertEqual(len(plan.rules), 4_096)
                self.assertEqual(len(plan.tasks), 4_096)
                self.assertEqual(len(plan.origins), expected_origin_count)
                self.assertEqual(
                    plan.origins[-1].target,
                    RecordRef("certificate:max:4095", 1),
                )


class PlanningStaticBoundaryTests(unittest.TestCase):
    @staticmethod
    def plan_tree() -> ast.Module:
        path = (
            Path(__file__).parents[1]
            / "src"
            / "poietics"
            / "binding"
            / "plan.py"
        )
        return ast.parse(path.read_text(encoding="utf-8"))

    def test_f58_plan_imports_stay_inside_the_exact_allowlist(self) -> None:
        tree = self.plan_tree()
        allowed_project = {
            "poietics.generation.extract": {"ExtractedDraft"},
            "poietics.generation.model": {"DraftRef"},
            "poietics.pff.model": {
                "AtomRecord",
                "PackageHeader",
                "RecordKind",
                "RecordRef",
                "RuleRecord",
            },
            "poietics.pff.registry": {
                "CheckerUse",
                "PredicateRegistry",
                "RegistryCatalog",
            },
            "poietics.binding.model": {
                "BindingCode",
                "BindingIssue",
                "BindingOrigin",
                "BindingPhase",
                "BindingPlan",
                "BindingRole",
                "DraftBindingError",
                "DraftBindingPolicy",
                "DraftRecordKind",
                "DraftSource",
                "EvidenceBinding",
                "EvidenceTask",
                "RecordIdentityBinding",
            },
        }
        allowed_standard = {
            "__future__",
            "collections.abc",
            "dataclasses",
            "enum",
            "types",
            "typing",
        }
        observed_project: dict[str, set[str]] = {}
        for node in ast.walk(tree):
            self.assertNotIsInstance(node, ast.Import)
            if not isinstance(node, ast.ImportFrom):
                continue
            self.assertTrue(all(alias.name != "*" for alias in node.names))
            if node.level == 1:
                self.assertEqual(node.module, "model")
                resolved = "poietics.binding.model"
            else:
                self.assertEqual(node.level, 0)
                self.assertIsNotNone(node.module)
                resolved = node.module
            names = {alias.name for alias in node.names}
            if resolved in allowed_standard:
                continue
            self.assertIn(resolved, allowed_project)
            self.assertLessEqual(names, allowed_project[resolved])
            observed_project.setdefault(resolved, set()).update(names)

        self.assertEqual(set(observed_project), set(allowed_project))
        forbidden_names = {
            "extract_draft",
            "generate_ollama",
            "validate_package",
            "compile_package",
            "evaluate",
            "open",
            "getenv",
            "import_module",
        }
        self.assertTrue(
            forbidden_names.isdisjoint(
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name)
            )
        )

    def test_f58_origin_builder_has_three_unfiltered_total_leaves(self) -> None:
        tree = self.plan_tree()
        planner = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "plan_draft_binding"
        )
        assignments = {
            target.id: node.value
            for node in planner.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance((target := node.targets[0]), ast.Name)
            and target.id
            in {"atom_origins", "rule_origins", "evidence_origins", "origins"}
        }
        self.assertEqual(
            set(assignments),
            {"atom_origins", "rule_origins", "evidence_origins", "origins"},
        )
        expected = {
            "atom_origins": (
                "atoms",
                "ATOM",
                "DRAFT_ATOM",
                "ATOM",
            ),
            "rule_origins": (
                "rules",
                "RULE",
                "DRAFT_RULE",
                "RULE",
            ),
            "evidence_origins": (
                "evidence_requests",
                "CERTIFICATE",
                "EVIDENCE_CERTIFICATE",
                "EVIDENCE_REQUEST",
            ),
        }
        for name, (collection, target_kind, role, source_kind) in expected.items():
            with self.subTest(leaf=name):
                wrapper = assignments[name]
                self.assertIsInstance(wrapper, ast.Call)
                self.assertIsInstance(wrapper.func, ast.Name)
                self.assertEqual(wrapper.func.id, "tuple")
                self.assertEqual(len(wrapper.args), 1)
                generator = wrapper.args[0]
                self.assertIsInstance(generator, ast.GeneratorExp)
                self.assertEqual(len(generator.generators), 1)
                clause = generator.generators[0]
                self.assertEqual(clause.is_async, 0)
                self.assertEqual(clause.ifs, [])
                self.assertEqual(
                    ast.unparse(clause.iter),
                    f"source.draft.{collection}",
                )
                self.assertIsInstance(generator.elt, ast.Call)
                self.assertIsInstance(generator.elt.func, ast.Name)
                self.assertEqual(generator.elt.func.id, "BindingOrigin")
                keywords = {keyword.arg: keyword.value for keyword in generator.elt.keywords}
                self.assertEqual(
                    ast.unparse(keywords["target_kind"]),
                    f"RecordKind.{target_kind}",
                )
                self.assertEqual(
                    ast.unparse(keywords["role"]),
                    f"BindingRole.{role}",
                )
                source_call = keywords["source"]
                self.assertIsInstance(source_call, ast.Call)
                self.assertEqual(
                    ast.unparse(
                        next(
                            keyword.value
                            for keyword in source_call.keywords
                            if keyword.arg == "kind"
                        )
                    ),
                    f"DraftRecordKind.{source_kind}",
                )
                target_lookup = keywords["target"]
                self.assertIsInstance(target_lookup, ast.Subscript)
                self.assertEqual(
                    ast.dump(target_lookup.slice, include_attributes=False),
                    ast.dump(source_call, include_attributes=False),
                )

        origins = assignments["origins"]
        self.assertEqual(
            ast.unparse(origins),
            "tuple(sorted(atom_origins + rule_origins + evidence_origins, key=_origin_key))",
        )
        factory_calls = [
            node
            for node in ast.walk(planner)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_from_planning"
        ]
        self.assertEqual(len(factory_calls), 1)
        origin_arguments = [
            keyword.value
            for keyword in factory_calls[0].keywords
            if keyword.arg == "origins"
        ]
        self.assertEqual(len(origin_arguments), 1)
        self.assertEqual(ast.unparse(origin_arguments[0]), "origins")

    def test_f58_external_versions_are_compared_before_conversion(self) -> None:
        tree = self.plan_tree()
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        for function_name, object_name in (
            ("_registry_gate", "registry"),
            ("_routing_gate", "checker"),
        ):
            with self.subTest(function=function_name):
                function = functions[function_name]
                unsupported = [
                    node
                    for node in ast.walk(function)
                    if isinstance(node, ast.If)
                    and isinstance(node.test, ast.Compare)
                    and len(node.test.ops) == 1
                    and isinstance(node.test.ops[0], ast.Gt)
                    and ast.unparse(node.test.left) == f"{object_name}.version"
                    and ast.unparse(node.test.comparators[0]) == "_MAX_VERSION"
                ]
                self.assertEqual(len(unsupported), 1)
                comparison = unsupported[0]
                calls_reading_version = [
                    node
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)
                    and any(
                        isinstance(member, ast.Attribute)
                        and ast.unparse(member) == f"{object_name}.version"
                        for member in ast.walk(node)
                    )
                ]
                self.assertTrue(calls_reading_version)
                self.assertTrue(
                    all(node.lineno > comparison.lineno for node in calls_reading_version)
                )
                self.assertFalse(
                    any(
                        isinstance(member, ast.Attribute)
                        and ast.unparse(member) == f"{object_name}.version"
                        for statement in comparison.body
                        for member in ast.walk(statement)
                    )
                )


if __name__ == "__main__":
    unittest.main()
