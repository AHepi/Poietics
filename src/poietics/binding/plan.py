"""Deterministic planning from one extracted draft and binding policy."""

from __future__ import annotations

from collections.abc import Iterable

from poietics.generation.extract import ExtractedDraft
from poietics.generation.model import DraftRef
from poietics.pff.model import (
    AtomRecord,
    PackageHeader,
    RecordKind,
    RecordRef,
    RuleRecord,
)
from poietics.pff.registry import CheckerUse, PredicateRegistry, RegistryCatalog

from .model import (
    BindingCode,
    BindingIssue,
    BindingOrigin,
    BindingPhase,
    BindingPlan,
    BindingRole,
    DraftBindingError,
    DraftBindingPolicy,
    DraftRecordKind,
    DraftSource,
    EvidenceBinding,
    EvidenceTask,
    RecordIdentityBinding,
)


_MAX_VERSION = 9_223_372_036_854_775_807
_MAX_TARGET_ID_BYTES = 262_144
_SUPPORTED_MAX_DETAIL = "supported_max=9223372036854775807"
_SOURCE_KIND_RANK = {
    DraftRecordKind.ATOM: 0,
    DraftRecordKind.RULE: 1,
    DraftRecordKind.EVIDENCE_REQUEST: 2,
}
_ORIGIN_KIND_RANK = {
    RecordKind.ATOM: 0,
    RecordKind.RULE: 1,
    RecordKind.CERTIFICATE: 2,
}


def _record_ref_key(reference: RecordRef) -> tuple[object, ...]:
    return (reference.id, reference.version)


def _draft_ref_key(reference: DraftRef) -> tuple[object, ...]:
    return (reference.id, reference.version)


def _source_key(source: DraftSource) -> tuple[object, ...]:
    return (
        _SOURCE_KIND_RANK[source.kind],
        source.ref.id,
        source.ref.version,
    )


def _origin_key(origin: BindingOrigin) -> tuple[object, ...]:
    return (
        _ORIGIN_KIND_RANK[origin.target_kind],
        origin.target.id,
        origin.target.version,
    )


def _sorted_sources(sources: Iterable[DraftSource]) -> tuple[DraftSource, ...]:
    return tuple(sorted(sources, key=_source_key))


def _sorted_targets(targets: Iterable[RecordRef]) -> tuple[RecordRef, ...]:
    return tuple(sorted(targets, key=_record_ref_key))


def _sorted_details(*details: str) -> tuple[str, ...]:
    return tuple(sorted(details))


def _raise_gate(issues: list[BindingIssue]) -> None:
    if issues:
        raise DraftBindingError(tuple(issues))


def _record_source(binding: RecordIdentityBinding) -> DraftSource:
    return DraftSource(kind=binding.source_kind, ref=binding.source)


def _evidence_source(binding: EvidenceBinding) -> DraftSource:
    return DraftSource(
        kind=DraftRecordKind.EVIDENCE_REQUEST,
        ref=binding.request,
    )


def _target_id_is_valid(identifier: str) -> bool:
    if not identifier:
        return False
    if any(0xD800 <= ord(character) <= 0xDFFF for character in identifier):
        return False
    return len(identifier.encode("utf-8")) <= _MAX_TARGET_ID_BYTES


def _coverage_gate(
    *,
    source: ExtractedDraft,
    policy: DraftBindingPolicy,
) -> tuple[
    dict[DraftSource, RecordIdentityBinding],
    dict[DraftRef, EvidenceBinding],
    dict[DraftSource, RecordRef],
]:
    atom_sources = {
        DraftSource(
            kind=DraftRecordKind.ATOM,
            ref=DraftRef(atom.id, atom.version),
        )
        for atom in source.draft.atoms
    }
    rule_sources = {
        DraftSource(
            kind=DraftRecordKind.RULE,
            ref=DraftRef(rule.id, rule.version),
        )
        for rule in source.draft.rules
    }
    request_refs = {
        DraftRef(request.id, request.version)
        for request in source.draft.evidence_requests
    }
    expected_record_sources = atom_sources | rule_sources

    record_bindings = {
        _record_source(binding): binding
        for binding in policy.record_bindings
    }
    evidence_bindings = {
        binding.request: binding
        for binding in policy.evidence_bindings
    }
    supplied_record_sources = set(record_bindings)
    supplied_request_refs = set(evidence_bindings)

    issues: list[BindingIssue] = []
    missing_records = expected_record_sources - supplied_record_sources
    if missing_records:
        issues.append(
            BindingIssue(
                phase=BindingPhase.COVERAGE,
                code=BindingCode.RECORD_BINDING_MISSING,
                path="/policy/record_bindings",
                sources=_sorted_sources(missing_records),
            )
        )

    extra_records = supplied_record_sources - expected_record_sources
    if extra_records:
        issues.append(
            BindingIssue(
                phase=BindingPhase.COVERAGE,
                code=BindingCode.RECORD_BINDING_EXTRA,
                path="/policy/record_bindings",
                sources=_sorted_sources(extra_records),
                targets=_sorted_targets(
                    {
                        record_bindings[record_source].target
                        for record_source in extra_records
                    }
                ),
            )
        )

    missing_requests = request_refs - supplied_request_refs
    if missing_requests:
        issues.append(
            BindingIssue(
                phase=BindingPhase.COVERAGE,
                code=BindingCode.EVIDENCE_BINDING_MISSING,
                path="/policy/evidence_bindings",
                sources=_sorted_sources(
                    {
                        DraftSource(
                            kind=DraftRecordKind.EVIDENCE_REQUEST,
                            ref=request,
                        )
                        for request in missing_requests
                    }
                ),
            )
        )

    extra_requests = supplied_request_refs - request_refs
    if extra_requests:
        issues.append(
            BindingIssue(
                phase=BindingPhase.COVERAGE,
                code=BindingCode.EVIDENCE_BINDING_EXTRA,
                path="/policy/evidence_bindings",
                sources=_sorted_sources(
                    {
                        DraftSource(
                            kind=DraftRecordKind.EVIDENCE_REQUEST,
                            ref=request,
                        )
                        for request in extra_requests
                    }
                ),
                targets=_sorted_targets(
                    {
                        evidence_bindings[request].certificate
                        for request in extra_requests
                    }
                ),
            )
        )

    _raise_gate(issues)

    target_by_source = {
        record_source: binding.target
        for record_source, binding in record_bindings.items()
    }
    target_by_source.update(
        {
            _evidence_source(binding): binding.certificate
            for binding in evidence_bindings.values()
        }
    )
    return record_bindings, evidence_bindings, target_by_source


def _identity_gate(
    *,
    record_bindings: dict[DraftSource, RecordIdentityBinding],
    evidence_bindings: dict[DraftRef, EvidenceBinding],
) -> None:
    routed_targets = tuple(
        (source, binding.target)
        for source, binding in record_bindings.items()
    ) + tuple(
        (_evidence_source(binding), binding.certificate)
        for binding in evidence_bindings.values()
    )

    issues: list[BindingIssue] = []
    by_target: dict[RecordRef, list[DraftSource]] = {}
    for source, target in routed_targets:
        valid_id = _target_id_is_valid(target.id)
        if not valid_id:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.IDENTITY,
                    code=BindingCode.TARGET_INVALID_ID,
                    path="/policy/targets/id",
                    sources=(source,),
                    targets=(target,),
                )
            )
        elif target.id.startswith("__pff__:"):
            issues.append(
                BindingIssue(
                    phase=BindingPhase.IDENTITY,
                    code=BindingCode.TARGET_RESERVED_ID,
                    path="/policy/targets/id",
                    sources=(source,),
                    targets=(target,),
                )
            )

        if target.version < 1 or target.version > _MAX_VERSION:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.IDENTITY,
                    code=BindingCode.TARGET_INVALID_VERSION,
                    path="/policy/targets/version",
                    sources=(source,),
                    targets=(target,),
                )
            )
        by_target.setdefault(target, []).append(source)

    for target, sources in by_target.items():
        if len(sources) >= 2:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.IDENTITY,
                    code=BindingCode.TARGET_REF_COLLISION,
                    path="/policy/targets",
                    sources=_sorted_sources(sources),
                    targets=(target,),
                )
            )

    _raise_gate(issues)


def _registry_gate(
    *,
    policy: DraftBindingPolicy,
    catalog: RegistryCatalog,
) -> PredicateRegistry:
    try:
        registry = catalog.lookup(policy.registry_id)
    except KeyError:
        raise DraftBindingError(
            (
                BindingIssue(
                    phase=BindingPhase.REGISTRY,
                    code=BindingCode.UNKNOWN_REGISTRY,
                    path="/policy/registry_id",
                    details=(policy.registry_id,),
                ),
            )
        ) from None

    if registry.version > _MAX_VERSION:
        raise DraftBindingError(
            (
                BindingIssue(
                    phase=BindingPhase.REGISTRY,
                    code=BindingCode.REGISTRY_VERSION_UNSUPPORTED,
                    path="/catalog/registry/version",
                    details=(
                        "registry_id=" + policy.registry_id,
                        _SUPPORTED_MAX_DETAIL,
                    ),
                ),
            )
        )

    if policy.registry_version != registry.version:
        raise DraftBindingError(
            (
                BindingIssue(
                    phase=BindingPhase.REGISTRY,
                    code=BindingCode.REGISTRY_VERSION_MISMATCH,
                    path="/policy/registry_version",
                    details=_sorted_details(
                        "actual=" + str(policy.registry_version),
                        "expected=" + str(registry.version),
                    ),
                ),
            )
        )
    return registry


def _routing_gate(
    *,
    source: ExtractedDraft,
    registry: PredicateRegistry,
    record_bindings: dict[DraftSource, RecordIdentityBinding],
    evidence_bindings: dict[DraftRef, EvidenceBinding],
) -> None:
    draft_atoms = {
        DraftRef(atom.id, atom.version): atom
        for atom in source.draft.atoms
    }
    draft_rules = {
        DraftRef(rule.id, rule.version): rule
        for rule in source.draft.rules
    }
    issues: list[BindingIssue] = []

    for request in source.draft.evidence_requests:
        request_ref = DraftRef(request.id, request.version)
        request_source = DraftSource(
            kind=DraftRecordKind.EVIDENCE_REQUEST,
            ref=request_ref,
        )
        rule = draft_rules[request.subject]
        rule_ref = DraftRef(rule.id, rule.version)
        rule_source = DraftSource(kind=DraftRecordKind.RULE, ref=rule_ref)
        head_atom = draft_atoms[rule.head]
        head_source = DraftSource(kind=DraftRecordKind.ATOM, ref=rule.head)
        evidence_binding = evidence_bindings[request_ref]
        mapped_rule = record_bindings[rule_source].target
        mapped_head = record_bindings[head_source].target
        route_targets = _sorted_targets(
            (mapped_rule, evidence_binding.certificate)
        )

        try:
            predicate = registry.predicate(head_atom.predicate)
        except KeyError:
            predicate = None
            issues.append(
                BindingIssue(
                    phase=BindingPhase.ROUTING,
                    code=BindingCode.HEAD_PREDICATE_UNKNOWN,
                    path="/draft/rules/head/predicate",
                    sources=_sorted_sources((head_source, rule_source)),
                    targets=_sorted_targets((mapped_head, mapped_rule)),
                    details=(head_atom.predicate,),
                )
            )

        try:
            checker = registry.checker_contract(evidence_binding.checker_id)
        except KeyError:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.ROUTING,
                    code=BindingCode.CHECKER_UNKNOWN,
                    path="/policy/evidence_bindings/checker_id",
                    sources=_sorted_sources((rule_source, request_source)),
                    targets=route_targets,
                    details=(evidence_binding.checker_id,),
                )
            )
            continue

        if checker.version > _MAX_VERSION:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.ROUTING,
                    code=BindingCode.CHECKER_VERSION_UNSUPPORTED,
                    path="/catalog/registry/checker_contracts/version",
                    sources=_sorted_sources((rule_source, request_source)),
                    targets=route_targets,
                    details=(
                        "checker_id=" + evidence_binding.checker_id,
                        _SUPPORTED_MAX_DETAIL,
                    ),
                )
            )
            continue

        if evidence_binding.checker_version != checker.version:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.ROUTING,
                    code=BindingCode.CHECKER_VERSION_MISMATCH,
                    path="/policy/evidence_bindings/checker_version",
                    sources=_sorted_sources((rule_source, request_source)),
                    targets=route_targets,
                    details=_sorted_details(
                        "actual=" + str(evidence_binding.checker_version),
                        "expected=" + str(checker.version),
                    ),
                )
            )
            continue

        reasons: list[str] = []
        if (
            predicate is not None
            and evidence_binding.checker_id not in predicate.checker_contract_ids
        ):
            reasons.append("reason=predicate")
        if RecordKind.RULE not in checker.certificate_subject_kinds:
            reasons.append("reason=subject")
        if CheckerUse.CERTIFICATE not in checker.uses:
            reasons.append("reason=use")
        if reasons:
            issues.append(
                BindingIssue(
                    phase=BindingPhase.ROUTING,
                    code=BindingCode.CHECKER_NOT_PERMITTED,
                    path="/policy/evidence_bindings/checker_id",
                    sources=_sorted_sources((rule_source, request_source)),
                    targets=route_targets,
                    details=_sorted_details(*reasons),
                )
            )

    _raise_gate(issues)


def plan_draft_binding(
    source: ExtractedDraft,
    policy: DraftBindingPolicy,
    catalog: RegistryCatalog,
) -> BindingPlan:
    """Bind one extracted draft to policy-owned identities and evidence tasks."""

    if type(source) is not ExtractedDraft:
        raise TypeError("source must be an exact ExtractedDraft")
    if type(policy) is not DraftBindingPolicy:
        raise TypeError("policy must be an exact DraftBindingPolicy")
    if type(catalog) is not RegistryCatalog:
        raise TypeError("catalog must be an exact RegistryCatalog")

    if source.payload_sha256 != policy.source_payload_sha256:
        raise DraftBindingError(
            (
                BindingIssue(
                    phase=BindingPhase.SOURCE,
                    code=BindingCode.SOURCE_PAYLOAD_MISMATCH,
                    path="/source/payload_sha256",
                    details=_sorted_details(
                        "actual=" + source.payload_sha256,
                        "expected=" + policy.source_payload_sha256,
                    ),
                ),
            )
        )

    record_bindings, evidence_bindings, target_by_source = _coverage_gate(
        source=source,
        policy=policy,
    )
    _identity_gate(
        record_bindings=record_bindings,
        evidence_bindings=evidence_bindings,
    )
    registry = _registry_gate(policy=policy, catalog=catalog)
    _routing_gate(
        source=source,
        registry=registry,
        record_bindings=record_bindings,
        evidence_bindings=evidence_bindings,
    )

    header = PackageHeader(
        schema="pff-core/0.1",
        package_id=policy.package_id,
        cut_id=policy.cut_id,
        frame_id=policy.frame_id,
        registry_id=policy.registry_id,
        parent_package_hash=None,
        metadata={},
    )

    atom_pairs = tuple(
        (
            DraftRef(atom.id, atom.version),
            AtomRecord(
                id=target_by_source[
                    DraftSource(
                        kind=DraftRecordKind.ATOM,
                        ref=DraftRef(atom.id, atom.version),
                    )
                ].id,
                version=target_by_source[
                    DraftSource(
                        kind=DraftRecordKind.ATOM,
                        ref=DraftRef(atom.id, atom.version),
                    )
                ].version,
                predicate=atom.predicate,
                args=atom.args,
                frame=atom.frame,
                grade=atom.grade,
                primitive=False,
            ),
        )
        for atom in source.draft.atoms
    )
    atoms = tuple(
        sorted(
            (record for _, record in atom_pairs),
            key=lambda record: (record.id, record.version),
        )
    )

    rule_pairs = tuple(
        (
            DraftRef(rule.id, rule.version),
            RuleRecord(
                id=target_by_source[
                    DraftSource(
                        kind=DraftRecordKind.RULE,
                        ref=DraftRef(rule.id, rule.version),
                    )
                ].id,
                version=target_by_source[
                    DraftSource(
                        kind=DraftRecordKind.RULE,
                        ref=DraftRef(rule.id, rule.version),
                    )
                ].version,
                head=target_by_source[
                    DraftSource(kind=DraftRecordKind.ATOM, ref=rule.head)
                ],
                positive=frozenset(
                    target_by_source[
                        DraftSource(kind=DraftRecordKind.ATOM, ref=premise)
                    ]
                    for premise in rule.positive
                ),
                certificate=evidence_bindings[rule.evidence_request].certificate,
                negative=frozenset(),
                faces=frozenset(),
            ),
        )
        for rule in source.draft.rules
    )
    rules_by_source = dict(rule_pairs)
    rules = tuple(
        sorted(
            (record for _, record in rule_pairs),
            key=lambda record: (record.id, record.version),
        )
    )

    tasks = tuple(
        sorted(
            (
                EvidenceTask(
                    profile="pff-evidence-task/0.1",
                    source_payload_sha256=source.payload_sha256,
                    policy_id=policy.policy_id,
                    policy_version=policy.version,
                    subject_rule=rules_by_source[request.subject],
                    request_kind=request.kind,
                    request=DraftRef(request.id, request.version),
                    question=request.question,
                    checker_id=evidence_bindings[
                        DraftRef(request.id, request.version)
                    ].checker_id,
                    checker_version=evidence_bindings[
                        DraftRef(request.id, request.version)
                    ].checker_version,
                    expected_authority_id=evidence_bindings[
                        DraftRef(request.id, request.version)
                    ].authority_id,
                    expected_authority_version=evidence_bindings[
                        DraftRef(request.id, request.version)
                    ].authority_version,
                    package_id=policy.package_id,
                    cut_id=policy.cut_id,
                    frame_id=policy.frame_id,
                    registry_id=policy.registry_id,
                    registry_version=policy.registry_version,
                )
                for request in source.draft.evidence_requests
            ),
            key=lambda task: _draft_ref_key(task.request),
        )
    )

    atom_origins = tuple(
        BindingOrigin(
            target_kind=RecordKind.ATOM,
            target=target_by_source[
                DraftSource(
                    kind=DraftRecordKind.ATOM,
                    ref=DraftRef(atom.id, atom.version),
                )
            ],
            role=BindingRole.DRAFT_ATOM,
            source=DraftSource(
                kind=DraftRecordKind.ATOM,
                ref=DraftRef(atom.id, atom.version),
            ),
        )
        for atom in source.draft.atoms
    )
    rule_origins = tuple(
        BindingOrigin(
            target_kind=RecordKind.RULE,
            target=target_by_source[
                DraftSource(
                    kind=DraftRecordKind.RULE,
                    ref=DraftRef(rule.id, rule.version),
                )
            ],
            role=BindingRole.DRAFT_RULE,
            source=DraftSource(
                kind=DraftRecordKind.RULE,
                ref=DraftRef(rule.id, rule.version),
            ),
        )
        for rule in source.draft.rules
    )
    evidence_origins = tuple(
        BindingOrigin(
            target_kind=RecordKind.CERTIFICATE,
            target=target_by_source[
                DraftSource(
                    kind=DraftRecordKind.EVIDENCE_REQUEST,
                    ref=DraftRef(request.id, request.version),
                )
            ],
            role=BindingRole.EVIDENCE_CERTIFICATE,
            source=DraftSource(
                kind=DraftRecordKind.EVIDENCE_REQUEST,
                ref=DraftRef(request.id, request.version),
            ),
        )
        for request in source.draft.evidence_requests
    )
    origins = tuple(
        sorted(
            atom_origins + rule_origins + evidence_origins,
            key=_origin_key,
        )
    )

    return BindingPlan._from_planning(
        source=source,
        policy=policy,
        catalog=catalog,
        registry=registry,
        header=header,
        atoms=atoms,
        rules=rules,
        tasks=tasks,
        origins=origins,
    )


__all__ = ("plan_draft_binding",)
