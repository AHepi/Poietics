"""Pure materialisation of one accepted draft-binding plan."""

from __future__ import annotations

from poietics.pff.model import BasePartition, CertificateRecord, Package, RecordRef

from .model import (
    BindingCode,
    BindingIssue,
    BindingPhase,
    BindingPlan,
    BoundPackage,
    DraftBindingError,
    DraftRecordKind,
    DraftSource,
    EvidenceAttestation,
    EvidenceTask,
)


_MAX_FINAL_EVIDENCE = 4_096
_SOURCE_KIND_RANK = {
    DraftRecordKind.ATOM: 0,
    DraftRecordKind.RULE: 1,
    DraftRecordKind.EVIDENCE_REQUEST: 2,
}


def _record_ref_key(ref: RecordRef) -> tuple[str, int]:
    return (ref.id, ref.version)


def _draft_source_key(source: DraftSource) -> tuple[int, str, int]:
    return (
        _SOURCE_KIND_RANK[source.kind],
        source.ref.id,
        source.ref.version,
    )


def _request_source(attestation: EvidenceAttestation) -> DraftSource:
    return DraftSource(
        DraftRecordKind.EVIDENCE_REQUEST,
        attestation.task.request,
    )


def _expected_request_source(task: EvidenceTask) -> DraftSource:
    return DraftSource(
        DraftRecordKind.EVIDENCE_REQUEST,
        task.request,
    )


def _evidence_set_issues(
    plan: BindingPlan,
    groups: dict[object, list[EvidenceAttestation]],
) -> tuple[BindingIssue, ...]:
    issues: list[BindingIssue] = []
    expected_requests = {task.request for task in plan.tasks}

    for task in plan.tasks:
        submitted = groups.get(task.request, ())
        source = _expected_request_source(task)
        targets = (task.subject_rule.certificate,)
        if not submitted:
            issues.append(
                BindingIssue(
                    BindingPhase.EVIDENCE_SET,
                    BindingCode.EVIDENCE_MISSING,
                    "/evidence",
                    sources=(source,),
                    targets=targets,
                )
            )
        elif len(submitted) > 1:
            issues.append(
                BindingIssue(
                    BindingPhase.EVIDENCE_SET,
                    BindingCode.EVIDENCE_DUPLICATE,
                    "/evidence",
                    sources=(source,),
                    targets=targets,
                )
            )
        elif submitted[0].task != task:
            issues.append(
                BindingIssue(
                    BindingPhase.EVIDENCE_SET,
                    BindingCode.EVIDENCE_TASK_MISMATCH,
                    "/evidence/task",
                    sources=(source,),
                    targets=targets,
                )
            )

    unknown_requests = tuple(
        sorted(
            (request for request in groups if request not in expected_requests),
            key=lambda request: (request.id, request.version),
        )
    )
    for request in unknown_requests:
        submitted = groups[request]
        targets = tuple(
            sorted(
                {
                    attestation.task.subject_rule.certificate
                    for attestation in submitted
                },
                key=_record_ref_key,
            )
        )
        issues.append(
            BindingIssue(
                BindingPhase.EVIDENCE_SET,
                BindingCode.EVIDENCE_EXTRA,
                "/evidence",
                sources=(
                    DraftSource(DraftRecordKind.EVIDENCE_REQUEST, request),
                ),
                targets=targets,
            )
        )

    return tuple(issues)


def _attestation_issues(
    evidence: tuple[EvidenceAttestation, ...],
) -> tuple[BindingIssue, ...]:
    issues: list[BindingIssue] = []
    identity_groups: dict[
        tuple[str, int, str, int], list[EvidenceAttestation]
    ] = {}

    for attestation in evidence:
        task = attestation.task
        if (
            attestation.authority_id != task.expected_authority_id
            or attestation.authority_version != task.expected_authority_version
        ):
            details = tuple(
                sorted(
                    (
                        f"actual_authority_id={attestation.authority_id}",
                        f"actual_authority_version={attestation.authority_version}",
                        f"expected_authority_id={task.expected_authority_id}",
                        f"expected_authority_version={task.expected_authority_version}",
                    )
                )
            )
            issues.append(
                BindingIssue(
                    BindingPhase.ATTESTATION,
                    BindingCode.EVIDENCE_AUTHORITY_MISMATCH,
                    "/evidence/authority",
                    sources=(_request_source(attestation),),
                    targets=(task.subject_rule.certificate,),
                    details=details,
                )
            )

        identity = (
            attestation.authority_id,
            attestation.authority_version,
            attestation.attestation_id,
            attestation.attestation_version,
        )
        identity_groups.setdefault(identity, []).append(attestation)

    for identity in sorted(identity_groups):
        matching = identity_groups[identity]
        if len(matching) < 2:
            continue
        authority_id, authority_version, attestation_id, attestation_version = (
            identity
        )
        sources = tuple(
            sorted(
                {_request_source(attestation) for attestation in matching},
                key=_draft_source_key,
            )
        )
        targets = tuple(
            sorted(
                {
                    attestation.task.subject_rule.certificate
                    for attestation in matching
                },
                key=_record_ref_key,
            )
        )
        details = tuple(
            sorted(
                (
                    f"authority_id={authority_id}",
                    f"authority_version={authority_version}",
                    f"attestation_id={attestation_id}",
                    f"attestation_version={attestation_version}",
                )
            )
        )
        issues.append(
            BindingIssue(
                BindingPhase.ATTESTATION,
                BindingCode.ATTESTATION_REF_COLLISION,
                "/evidence/attestation",
                sources=sources,
                targets=targets,
                details=details,
            )
        )

    return tuple(issues)


def _certificate(
    attestation: EvidenceAttestation,
) -> CertificateRecord:
    task = attestation.task
    certificate = task.subject_rule.certificate
    return CertificateRecord(
        id=certificate.id,
        version=certificate.version,
        checker=task.checker_id,
        subject=task.subject_rule.ref,
        result=attestation.result,
        payload_hash=attestation.payload_hash,
        details={detail.key: detail.value for detail in attestation.details},
    )


def finalize_draft_binding(
    plan: BindingPlan,
    evidence: tuple[EvidenceAttestation, ...],
) -> BoundPackage:
    """Bind one complete authority-evidence population into a PFF candidate."""

    if type(plan) is not BindingPlan:
        raise TypeError("plan must be an exact BindingPlan")
    if type(evidence) is not tuple:
        raise TypeError("evidence must be an exact tuple")
    if any(type(attestation) is not EvidenceAttestation for attestation in evidence):
        raise TypeError("evidence must contain exact EvidenceAttestation values")
    if len(evidence) > _MAX_FINAL_EVIDENCE:
        raise ValueError("evidence exceeds the final-evidence limit")

    groups: dict[object, list[EvidenceAttestation]] = {}
    for attestation in evidence:
        groups.setdefault(attestation.task.request, []).append(attestation)

    issues = _evidence_set_issues(plan, groups)
    if issues:
        raise DraftBindingError(issues)

    canonical_evidence = tuple(
        groups[task.request][0]
        for task in plan.tasks
    )
    issues = _attestation_issues(canonical_evidence)
    if issues:
        raise DraftBindingError(issues)

    certificates = tuple(
        sorted(
            (_certificate(attestation) for attestation in canonical_evidence),
            key=lambda certificate: _record_ref_key(certificate.ref),
        )
    )
    package = Package(
        header=plan.header,
        atoms=plan.atoms,
        rules=plan.rules,
        faces=(),
        certificates=certificates,
        closures=(),
        contraries=(),
        challenges=(),
        discharges=(),
        base=BasePartition(),
    )
    return BoundPackage._from_finalization(
        plan=plan,
        evidence=canonical_evidence,
        package=package,
    )


__all__ = ["finalize_draft_binding"]
