"""Immutable values shared by draft-binding planning and finalization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from types import MappingProxyType
from typing import TypeVar

from poietics.generation.extract import ExtractedDraft
from poietics.generation.model import DraftRef
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


_BINDING_POLICY_PROFILE = "pff-draft-binding-policy/0.1"
_EVIDENCE_TASK_PROFILE = "pff-evidence-task/0.1"
_EVIDENCE_ATTESTATION_PROFILE = "pff-evidence-attestation/0.1"
_BINDING_PLAN_PROFILE = "pff-draft-binding-plan/0.1"
_BOUND_PACKAGE_PROFILE = "pff-bound-package/0.1"
_REQUEST_KIND = "certificate"

_MAX_INTEGER = 9_223_372_036_854_775_807
_BINDING_STRING_BYTES = 262_144
_ISSUE_DETAIL_BYTES = 262_176
_MAX_RECORD_BINDINGS = 8_192
_MAX_EVIDENCE_BINDINGS = 4_096
_MAX_EVIDENCE_DETAILS = 4_096
_LOWER_HEXADECIMAL = frozenset("0123456789abcdef")


def _require_scalar_string(
    value: object,
    field_name: str,
    *,
    allow_empty: bool,
    maximum_bytes: int = _BINDING_STRING_BYTES,
) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{field_name} must contain only Unicode scalar values")
    if len(value.encode("utf-8")) > maximum_bytes:
        raise ValueError(f"{field_name} exceeds its UTF-8 byte limit")
    return value


def _require_identifier(value: object, field_name: str) -> str:
    return _require_scalar_string(value, field_name, allow_empty=False)


def _require_profile(value: object, expected: str, field_name: str) -> str:
    profile = _require_identifier(value, field_name)
    if profile != expected:
        raise ValueError(f"unsupported {field_name}")
    return profile


def _require_sha256(value: object, field_name: str) -> str:
    digest = _require_identifier(value, field_name)
    if (
        len(digest) != 71
        or not digest.startswith("sha256:")
        or any(character not in _LOWER_HEXADECIMAL for character in digest[7:])
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 value")
    return digest


def _require_positive_integer(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an exact int")
    if value < 1 or value > _MAX_INTEGER:
        raise ValueError(f"{field_name} is outside the supported range")
    return value


_MemberT = TypeVar("_MemberT")


def _require_exact_tuple(
    value: object,
    field_name: str,
    member_type: type[_MemberT],
) -> tuple[_MemberT, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple")
    if any(type(member) is not member_type for member in value):
        raise TypeError(
            f"{field_name} must contain exact {member_type.__name__} values"
        )
    return value


class DraftRecordKind(StrEnum):
    """Type-directed local identities admitted by the binder."""

    ATOM = "atom"
    RULE = "rule"
    EVIDENCE_REQUEST = "evidence_request"


def _draft_kind_rank(kind: DraftRecordKind) -> int:
    if kind is DraftRecordKind.ATOM:
        return 0
    if kind is DraftRecordKind.RULE:
        return 1
    return 2


@dataclass(frozen=True, slots=True)
class DraftSource:
    """One exact type-directed local draft reference."""

    kind: DraftRecordKind
    ref: DraftRef

    def __post_init__(self) -> None:
        if type(self.kind) is not DraftRecordKind:
            raise TypeError("kind must be an exact DraftRecordKind")
        if type(self.ref) is not DraftRef:
            raise TypeError("ref must be an exact DraftRef")


def _draft_source_key(source: DraftSource) -> tuple[object, ...]:
    return (_draft_kind_rank(source.kind), source.ref.id, source.ref.version)


@dataclass(frozen=True, slots=True)
class RecordIdentityBinding:
    """Map one local atom or rule identity to one authoritative record ref."""

    source_kind: DraftRecordKind
    source: DraftRef
    target: RecordRef

    def __post_init__(self) -> None:
        if type(self.source_kind) is not DraftRecordKind:
            raise TypeError("source_kind must be an exact DraftRecordKind")
        if self.source_kind is DraftRecordKind.EVIDENCE_REQUEST:
            raise ValueError("record identity bindings cannot bind evidence requests")
        if type(self.source) is not DraftRef:
            raise TypeError("source must be an exact DraftRef")
        if type(self.target) is not RecordRef:
            raise TypeError("target must be an exact RecordRef")


def _record_binding_key(binding: RecordIdentityBinding) -> tuple[object, ...]:
    return (
        _draft_kind_rank(binding.source_kind),
        binding.source.id,
        binding.source.version,
    )


@dataclass(frozen=True, slots=True)
class EvidenceBinding:
    """Code-owned certificate, checker, and authority route for one request."""

    request: DraftRef
    certificate: RecordRef
    checker_id: str
    checker_version: int
    authority_id: str
    authority_version: int

    def __post_init__(self) -> None:
        if type(self.request) is not DraftRef:
            raise TypeError("request must be an exact DraftRef")
        if type(self.certificate) is not RecordRef:
            raise TypeError("certificate must be an exact RecordRef")
        _require_identifier(self.checker_id, "checker_id")
        _require_positive_integer(self.checker_version, "checker_version")
        _require_identifier(self.authority_id, "authority_id")
        _require_positive_integer(self.authority_version, "authority_version")


def _evidence_binding_key(binding: EvidenceBinding) -> tuple[object, ...]:
    return (binding.request.id, binding.request.version)


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftBindingPolicy:
    """Complete code-owned authority input for one extracted draft."""

    profile: str
    policy_id: str
    version: int
    source_payload_sha256: str
    package_id: str
    cut_id: str
    frame_id: str
    registry_id: str
    registry_version: int
    record_bindings: tuple[RecordIdentityBinding, ...]
    evidence_bindings: tuple[EvidenceBinding, ...]

    def __post_init__(self) -> None:
        _require_profile(self.profile, _BINDING_POLICY_PROFILE, "profile")
        _require_identifier(self.policy_id, "policy_id")
        _require_positive_integer(self.version, "version")
        _require_sha256(self.source_payload_sha256, "source_payload_sha256")
        _require_identifier(self.package_id, "package_id")
        _require_identifier(self.cut_id, "cut_id")
        _require_identifier(self.frame_id, "frame_id")
        _require_identifier(self.registry_id, "registry_id")
        _require_positive_integer(self.registry_version, "registry_version")

        record_bindings = _require_exact_tuple(
            self.record_bindings,
            "record_bindings",
            RecordIdentityBinding,
        )
        evidence_bindings = _require_exact_tuple(
            self.evidence_bindings,
            "evidence_bindings",
            EvidenceBinding,
        )
        if len(record_bindings) > _MAX_RECORD_BINDINGS:
            raise ValueError("record_bindings exceeds its member limit")
        if len(evidence_bindings) > _MAX_EVIDENCE_BINDINGS:
            raise ValueError("evidence_bindings exceeds its member limit")

        record_keys = tuple(
            (binding.source_kind, binding.source)
            for binding in record_bindings
        )
        if len(set(record_keys)) != len(record_keys):
            raise ValueError("record_bindings contains a duplicate source key")
        evidence_keys = tuple(binding.request for binding in evidence_bindings)
        if len(set(evidence_keys)) != len(evidence_keys):
            raise ValueError("evidence_bindings contains a duplicate request key")

        object.__setattr__(
            self,
            "record_bindings",
            tuple(sorted(record_bindings, key=_record_binding_key)),
        )
        object.__setattr__(
            self,
            "evidence_bindings",
            tuple(sorted(evidence_bindings, key=_evidence_binding_key)),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceTask:
    """One fully bound request presented to an evidence authority."""

    profile: str
    source_payload_sha256: str
    policy_id: str
    policy_version: int
    subject_rule: RuleRecord
    request_kind: str
    request: DraftRef
    question: str = field(repr=False)
    checker_id: str
    checker_version: int
    expected_authority_id: str
    expected_authority_version: int
    package_id: str
    cut_id: str
    frame_id: str
    registry_id: str
    registry_version: int

    def __post_init__(self) -> None:
        _require_profile(self.profile, _EVIDENCE_TASK_PROFILE, "profile")
        _require_sha256(self.source_payload_sha256, "source_payload_sha256")
        _require_identifier(self.policy_id, "policy_id")
        _require_positive_integer(self.policy_version, "policy_version")
        if type(self.subject_rule) is not RuleRecord:
            raise TypeError("subject_rule must be an exact RuleRecord")
        request_kind = _require_identifier(self.request_kind, "request_kind")
        if request_kind != _REQUEST_KIND:
            raise ValueError("unsupported request_kind")
        if type(self.request) is not DraftRef:
            raise TypeError("request must be an exact DraftRef")
        _require_scalar_string(self.question, "question", allow_empty=True)
        _require_identifier(self.checker_id, "checker_id")
        _require_positive_integer(self.checker_version, "checker_version")
        _require_identifier(self.expected_authority_id, "expected_authority_id")
        _require_positive_integer(
            self.expected_authority_version,
            "expected_authority_version",
        )
        _require_identifier(self.package_id, "package_id")
        _require_identifier(self.cut_id, "cut_id")
        _require_identifier(self.frame_id, "frame_id")
        _require_identifier(self.registry_id, "registry_id")
        _require_positive_integer(self.registry_version, "registry_version")


EvidenceDetailValue = str | int | bool | RecordRef


@dataclass(frozen=True, slots=True, eq=False)
class EvidenceDetail:
    """One exact checker-detail key/value pair with a secret-safe repr."""

    key: str
    value: EvidenceDetailValue = field(repr=False)

    def __post_init__(self) -> None:
        _require_identifier(self.key, "key")
        if type(self.value) is str:
            _require_scalar_string(self.value, "value", allow_empty=True)
            return
        if type(self.value) is int:
            if self.value < -_MAX_INTEGER or self.value > _MAX_INTEGER:
                raise ValueError("integer detail value is outside the supported range")
            return
        if type(self.value) is bool or type(self.value) is RecordRef:
            return
        raise TypeError("value must be an exact evidence-detail scalar")

    def __eq__(self, other: object) -> bool:
        if type(other) is not EvidenceDetail:
            return NotImplemented
        return (
            self.key == other.key
            and type(self.value) is type(other.value)
            and self.value == other.value
        )

    def __hash__(self) -> int:
        return hash((self.key, type(self.value), self.value))


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceAttestation:
    """An ordinary, authority-asserted result for one exact evidence task."""

    profile: str
    task: EvidenceTask
    authority_id: str
    authority_version: int
    attestation_id: str
    attestation_version: int
    result: CheckResult
    payload_hash: str
    details: tuple[EvidenceDetail, ...] = field(repr=False)

    def __post_init__(self) -> None:
        _require_profile(self.profile, _EVIDENCE_ATTESTATION_PROFILE, "profile")
        if type(self.task) is not EvidenceTask:
            raise TypeError("task must be an exact EvidenceTask")
        _require_identifier(self.authority_id, "authority_id")
        _require_positive_integer(self.authority_version, "authority_version")
        _require_identifier(self.attestation_id, "attestation_id")
        _require_positive_integer(self.attestation_version, "attestation_version")
        if type(self.result) is not CheckResult:
            raise TypeError("result must be an exact CheckResult")
        _require_sha256(self.payload_hash, "payload_hash")
        details = _require_exact_tuple(self.details, "details", EvidenceDetail)
        if len(details) > _MAX_EVIDENCE_DETAILS:
            raise ValueError("details exceeds its member limit")
        keys = tuple(detail.key for detail in details)
        if len(set(keys)) != len(keys):
            raise ValueError("details contains a duplicate key")
        object.__setattr__(
            self,
            "details",
            tuple(sorted(details, key=lambda detail: detail.key)),
        )


class BindingRole(StrEnum):
    """How one authoritative package record originated."""

    DRAFT_ATOM = "draft-atom"
    DRAFT_RULE = "draft-rule"
    EVIDENCE_CERTIFICATE = "evidence-certificate"


@dataclass(frozen=True, slots=True)
class BindingOrigin:
    """One coherent package-record to local-source provenance edge."""

    target_kind: RecordKind
    target: RecordRef
    role: BindingRole
    source: DraftSource

    def __post_init__(self) -> None:
        if type(self.target_kind) is not RecordKind:
            raise TypeError("target_kind must be an exact RecordKind")
        if type(self.target) is not RecordRef:
            raise TypeError("target must be an exact RecordRef")
        if type(self.role) is not BindingRole:
            raise TypeError("role must be an exact BindingRole")
        if type(self.source) is not DraftSource:
            raise TypeError("source must be an exact DraftSource")
        coherent = (
            (
                RecordKind.ATOM,
                BindingRole.DRAFT_ATOM,
                DraftRecordKind.ATOM,
            ),
            (
                RecordKind.RULE,
                BindingRole.DRAFT_RULE,
                DraftRecordKind.RULE,
            ),
            (
                RecordKind.CERTIFICATE,
                BindingRole.EVIDENCE_CERTIFICATE,
                DraftRecordKind.EVIDENCE_REQUEST,
            ),
        )
        if (self.target_kind, self.role, self.source.kind) not in coherent:
            raise ValueError("incoherent binding origin")


class BindingPhase(IntEnum):
    """Fail-closed binder diagnostic gates."""

    SOURCE = 10
    COVERAGE = 20
    IDENTITY = 30
    REGISTRY = 40
    ROUTING = 50
    EVIDENCE_SET = 60
    ATTESTATION = 70


class BindingCode(StrEnum):
    """Stable machine-readable draft-binding issue vocabulary."""

    SOURCE_PAYLOAD_MISMATCH = "source_payload_mismatch"
    RECORD_BINDING_MISSING = "record_binding_missing"
    RECORD_BINDING_EXTRA = "record_binding_extra"
    EVIDENCE_BINDING_MISSING = "evidence_binding_missing"
    EVIDENCE_BINDING_EXTRA = "evidence_binding_extra"
    TARGET_INVALID_ID = "target_invalid_id"
    TARGET_INVALID_VERSION = "target_invalid_version"
    TARGET_RESERVED_ID = "target_reserved_id"
    TARGET_REF_COLLISION = "target_ref_collision"
    UNKNOWN_REGISTRY = "unknown_registry"
    REGISTRY_VERSION_UNSUPPORTED = "registry_version_unsupported"
    REGISTRY_VERSION_MISMATCH = "registry_version_mismatch"
    HEAD_PREDICATE_UNKNOWN = "head_predicate_unknown"
    CHECKER_UNKNOWN = "checker_unknown"
    CHECKER_VERSION_UNSUPPORTED = "checker_version_unsupported"
    CHECKER_VERSION_MISMATCH = "checker_version_mismatch"
    CHECKER_NOT_PERMITTED = "checker_not_permitted"
    EVIDENCE_MISSING = "evidence_missing"
    EVIDENCE_EXTRA = "evidence_extra"
    EVIDENCE_DUPLICATE = "evidence_duplicate"
    EVIDENCE_TASK_MISMATCH = "evidence_task_mismatch"
    EVIDENCE_AUTHORITY_MISMATCH = "evidence_authority_mismatch"
    ATTESTATION_REF_COLLISION = "attestation_ref_collision"


_ISSUE_SHAPES: Mapping[BindingCode, tuple[BindingPhase, str]] = MappingProxyType(
    {
        BindingCode.SOURCE_PAYLOAD_MISMATCH: (
            BindingPhase.SOURCE,
            "/source/payload_sha256",
        ),
        BindingCode.RECORD_BINDING_MISSING: (
            BindingPhase.COVERAGE,
            "/policy/record_bindings",
        ),
        BindingCode.RECORD_BINDING_EXTRA: (
            BindingPhase.COVERAGE,
            "/policy/record_bindings",
        ),
        BindingCode.EVIDENCE_BINDING_MISSING: (
            BindingPhase.COVERAGE,
            "/policy/evidence_bindings",
        ),
        BindingCode.EVIDENCE_BINDING_EXTRA: (
            BindingPhase.COVERAGE,
            "/policy/evidence_bindings",
        ),
        BindingCode.TARGET_INVALID_ID: (
            BindingPhase.IDENTITY,
            "/policy/targets/id",
        ),
        BindingCode.TARGET_INVALID_VERSION: (
            BindingPhase.IDENTITY,
            "/policy/targets/version",
        ),
        BindingCode.TARGET_RESERVED_ID: (
            BindingPhase.IDENTITY,
            "/policy/targets/id",
        ),
        BindingCode.TARGET_REF_COLLISION: (
            BindingPhase.IDENTITY,
            "/policy/targets",
        ),
        BindingCode.UNKNOWN_REGISTRY: (
            BindingPhase.REGISTRY,
            "/policy/registry_id",
        ),
        BindingCode.REGISTRY_VERSION_UNSUPPORTED: (
            BindingPhase.REGISTRY,
            "/catalog/registry/version",
        ),
        BindingCode.REGISTRY_VERSION_MISMATCH: (
            BindingPhase.REGISTRY,
            "/policy/registry_version",
        ),
        BindingCode.HEAD_PREDICATE_UNKNOWN: (
            BindingPhase.ROUTING,
            "/draft/rules/head/predicate",
        ),
        BindingCode.CHECKER_UNKNOWN: (
            BindingPhase.ROUTING,
            "/policy/evidence_bindings/checker_id",
        ),
        BindingCode.CHECKER_VERSION_UNSUPPORTED: (
            BindingPhase.ROUTING,
            "/catalog/registry/checker_contracts/version",
        ),
        BindingCode.CHECKER_VERSION_MISMATCH: (
            BindingPhase.ROUTING,
            "/policy/evidence_bindings/checker_version",
        ),
        BindingCode.CHECKER_NOT_PERMITTED: (
            BindingPhase.ROUTING,
            "/policy/evidence_bindings/checker_id",
        ),
        BindingCode.EVIDENCE_MISSING: (
            BindingPhase.EVIDENCE_SET,
            "/evidence",
        ),
        BindingCode.EVIDENCE_EXTRA: (
            BindingPhase.EVIDENCE_SET,
            "/evidence",
        ),
        BindingCode.EVIDENCE_DUPLICATE: (
            BindingPhase.EVIDENCE_SET,
            "/evidence",
        ),
        BindingCode.EVIDENCE_TASK_MISMATCH: (
            BindingPhase.EVIDENCE_SET,
            "/evidence/task",
        ),
        BindingCode.EVIDENCE_AUTHORITY_MISMATCH: (
            BindingPhase.ATTESTATION,
            "/evidence/authority",
        ),
        BindingCode.ATTESTATION_REF_COLLISION: (
            BindingPhase.ATTESTATION,
            "/evidence/attestation",
        ),
    }
)


def _record_ref_key(ref: RecordRef) -> tuple[object, ...]:
    return (ref.id, ref.version)


@dataclass(frozen=True, slots=True)
class BindingIssue:
    """One exact, canonical, payload-free binder diagnostic."""

    phase: BindingPhase
    code: BindingCode
    path: str
    sources: tuple[DraftSource, ...] = ()
    targets: tuple[RecordRef, ...] = ()
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.phase) is not BindingPhase:
            raise TypeError("phase must be an exact BindingPhase")
        if type(self.code) is not BindingCode:
            raise TypeError("code must be an exact BindingCode")
        if type(self.path) is not str:
            raise TypeError("path must be an exact str")
        expected_phase, expected_path = _ISSUE_SHAPES[self.code]
        if self.phase is not expected_phase:
            raise ValueError("binding issue code is in the wrong phase")
        if self.path != expected_path:
            raise ValueError("binding issue code has the wrong path")

        sources = _require_exact_tuple(self.sources, "sources", DraftSource)
        targets = _require_exact_tuple(self.targets, "targets", RecordRef)
        details = _require_exact_tuple(self.details, "details", str)
        for detail in details:
            _require_scalar_string(
                detail,
                "detail",
                allow_empty=True,
                maximum_bytes=_ISSUE_DETAIL_BYTES,
            )

        if len(set(sources)) != len(sources):
            raise ValueError("sources contains a duplicate member")
        if len(set(targets)) != len(targets):
            raise ValueError("targets contains a duplicate member")
        if len(set(details)) != len(details):
            raise ValueError("details contains a duplicate member")
        if sources != tuple(sorted(sources, key=_draft_source_key)):
            raise ValueError("sources is not in canonical order")
        if targets != tuple(sorted(targets, key=_record_ref_key)):
            raise ValueError("targets is not in canonical order")
        if details != tuple(sorted(details)):
            raise ValueError("details is not in canonical order")


def _issue_key(issue: BindingIssue) -> tuple[object, ...]:
    return (
        int(issue.phase),
        issue.path,
        issue.code.value,
        tuple(_draft_source_key(source) for source in issue.sources),
        tuple(_record_ref_key(target) for target in issue.targets),
        issue.details,
    )


class DraftBindingError(ValueError):
    """Canonical aggregate failure for one stopped binding gate."""

    __slots__ = ("issues",)

    issues: tuple[BindingIssue, ...]

    def __init__(self, issues: tuple[BindingIssue, ...]) -> None:
        members = _require_exact_tuple(issues, "issues", BindingIssue)
        if not members:
            raise ValueError("DraftBindingError requires at least one issue")
        self.issues = tuple(sorted(set(members), key=_issue_key))
        ValueError.__init__(self, "draft binding failed")


@dataclass(frozen=True, slots=True, init=False)
class BindingPlan:
    """Factory-only immutable result of successful draft-binding planning."""

    profile: str
    source: ExtractedDraft = field(repr=False)
    policy: DraftBindingPolicy
    catalog: RegistryCatalog
    registry: PredicateRegistry
    header: PackageHeader
    atoms: tuple[AtomRecord, ...]
    rules: tuple[RuleRecord, ...]
    tasks: tuple[EvidenceTask, ...]
    origins: tuple[BindingOrigin, ...]
    _target_index: Mapping[DraftSource, RecordRef] = field(
        repr=False,
        compare=False,
    )
    _task_index: Mapping[DraftRef, EvidenceTask] = field(
        repr=False,
        compare=False,
    )
    _origin_index: Mapping[tuple[RecordKind, RecordRef], BindingOrigin] = field(
        repr=False,
        compare=False,
    )

    __hash__ = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("BindingPlan is created only by plan_draft_binding")

    @classmethod
    def _from_planning(
        cls,
        *,
        source: ExtractedDraft,
        policy: DraftBindingPolicy,
        catalog: RegistryCatalog,
        registry: PredicateRegistry,
        header: PackageHeader,
        atoms: tuple[AtomRecord, ...],
        rules: tuple[RuleRecord, ...],
        tasks: tuple[EvidenceTask, ...],
        origins: tuple[BindingOrigin, ...],
    ) -> BindingPlan:
        if cls is not BindingPlan:
            raise TypeError("BindingPlan subclasses are not supported")
        self = object.__new__(cls)
        object.__setattr__(self, "profile", _BINDING_PLAN_PROFILE)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "policy", policy)
        object.__setattr__(self, "catalog", catalog)
        object.__setattr__(self, "registry", registry)
        object.__setattr__(self, "header", header)
        object.__setattr__(self, "atoms", atoms)
        object.__setattr__(self, "rules", rules)
        object.__setattr__(self, "tasks", tasks)
        object.__setattr__(self, "origins", origins)

        target_index = {
            DraftSource(binding.source_kind, binding.source): binding.target
            for binding in policy.record_bindings
        }
        target_index.update(
            {
                DraftSource(DraftRecordKind.EVIDENCE_REQUEST, binding.request): (
                    binding.certificate
                )
                for binding in policy.evidence_bindings
            }
        )
        object.__setattr__(
            self,
            "_target_index",
            MappingProxyType(target_index),
        )
        object.__setattr__(
            self,
            "_task_index",
            MappingProxyType({task.request: task for task in tasks}),
        )
        object.__setattr__(
            self,
            "_origin_index",
            MappingProxyType(
                {(o.target_kind, o.target): o for o in origins}
            ),
        )
        return self

    def target_for(self, kind: DraftRecordKind, ref: DraftRef) -> RecordRef:
        if type(kind) is not DraftRecordKind:
            raise TypeError("kind must be an exact DraftRecordKind")
        if type(ref) is not DraftRef:
            raise TypeError("ref must be an exact DraftRef")
        return self._target_index[DraftSource(kind, ref)]

    def task_for(self, request: DraftRef) -> EvidenceTask:
        if type(request) is not DraftRef:
            raise TypeError("request must be an exact DraftRef")
        return self._task_index[request]

    def origin_for(self, kind: RecordKind, ref: RecordRef) -> BindingOrigin:
        if type(kind) is not RecordKind:
            raise TypeError("kind must be an exact RecordKind")
        if type(ref) is not RecordRef:
            raise TypeError("ref must be an exact RecordRef")
        return self._origin_index[(kind, ref)]


@dataclass(frozen=True, slots=True, init=False)
class BoundPackage:
    """Factory-only candidate package plus its complete binding sidecar."""

    profile: str
    plan: BindingPlan
    evidence: tuple[EvidenceAttestation, ...] = field(repr=False)
    package: Package = field(repr=False)

    __hash__ = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("BoundPackage is created only by finalize_draft_binding")

    @classmethod
    def _from_finalization(
        cls,
        *,
        plan: BindingPlan,
        evidence: tuple[EvidenceAttestation, ...],
        package: Package,
    ) -> BoundPackage:
        if cls is not BoundPackage:
            raise TypeError("BoundPackage subclasses are not supported")
        self = object.__new__(cls)
        object.__setattr__(self, "profile", _BOUND_PACKAGE_PROFILE)
        object.__setattr__(self, "plan", plan)
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "package", package)
        return self

    def origin_for(self, kind: RecordKind, ref: RecordRef) -> BindingOrigin:
        return self.plan.origin_for(kind, ref)


__all__ = (
    "BindingCode",
    "BindingIssue",
    "BindingOrigin",
    "BindingPhase",
    "BindingPlan",
    "BindingRole",
    "BoundPackage",
    "DraftBindingError",
    "DraftBindingPolicy",
    "DraftRecordKind",
    "DraftSource",
    "EvidenceAttestation",
    "EvidenceBinding",
    "EvidenceDetail",
    "EvidenceDetailValue",
    "EvidenceTask",
    "RecordIdentityBinding",
)
