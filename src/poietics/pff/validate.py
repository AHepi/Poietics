"""Deterministic validation for immutable PFF package candidates.

Validation is an admission boundary, not an evaluator.  It binds one package
to one exact code-owned registry and either returns a sealed
``ValidatedPackage`` or raises ``PackageValidationError``.  It never assigns a
semantic status, executes an external checker, invokes a provider, or compiles
ground atoms.  It does authenticate explicitly code-owned package-local
checker semantics; external checker outcomes remain supplied evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from types import MappingProxyType
from typing import cast

from .local_checkers import _evaluate_local_closure
from .model import (
    AtomRecord,
    CertificateRecord,
    ChallengeRecord,
    CheckResult,
    ClosureRecord,
    ContraryRecord,
    DischargeRecord,
    FaceRecord,
    Package,
    Record,
    RecordKind,
    RecordRef,
    RuleRecord,
)
from .registry import (
    CheckerDetailType,
    CheckerUse,
    ContraryPolicyMode,
    PredicateDefinition,
    PredicateRegistry,
    RegistryCatalog,
)

PFF_CORE_SCHEMA = "pff-core/0.1"
RESERVED_ID_PREFIX = "__pff__:"


class ValidationPhase(IntEnum):
    """Stable ordering of validation phases for aggregate diagnostics."""

    HEADER = 10
    IDENTITY = 20
    REFERENCES = 30
    BINDINGS = 40
    POLICIES = 50
    BASE = 60


class ValidationCode(StrEnum):
    """Implementation-owned, machine-readable package issue vocabulary."""

    SCHEMA_MISMATCH = "schema_mismatch"
    INVALID_ID = "invalid_id"
    INVALID_VERSION = "invalid_version"
    RESERVED_ID = "reserved_id"
    UNKNOWN_REGISTRY = "unknown_registry"
    DUPLICATE_RECORD = "duplicate_record"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    REFERENCE_KIND_MISMATCH = "reference_kind_mismatch"
    UNKNOWN_PREDICATE = "unknown_predicate"
    PREDICATE_ARITY = "predicate_arity"
    PREDICATE_ARG_TYPE = "predicate_arg_type"
    PREDICATE_FRAME = "predicate_frame"
    PREDICATE_GRADE = "predicate_grade"
    PRIMITIVE_FORBIDDEN = "primitive_forbidden"
    PRIMITIVE_HAS_DERIVATION = "primitive_has_derivation"
    UNKNOWN_CHECKER = "unknown_checker"
    CHECKER_NOT_PERMITTED = "checker_not_permitted"
    CHECKER_PAYLOAD = "checker_payload"
    CERTIFICATE_SUBJECT_MISMATCH = "certificate_subject_mismatch"
    UNKNOWN_FACE_KIND = "unknown_face_kind"
    FACE_KIND_FORBIDDEN = "face_kind_forbidden"
    FACE_OWNER_MISMATCH = "face_owner_mismatch"
    CLOSURE_CUT_MISMATCH = "closure_cut_mismatch"
    CLOSURE_FRAME_MISMATCH = "closure_frame_mismatch"
    CLOSURE_RESULT_MISMATCH = "closure_result_mismatch"
    CONTRARY_FORBIDDEN = "contrary_forbidden"
    CONTRARY_BOUNDARY_MISMATCH = "contrary_boundary_mismatch"
    CLOSURE_ROLE_MISMATCH = "closure_role_mismatch"
    UNKNOWN_CHALLENGE_KIND = "unknown_challenge_kind"
    CHALLENGE_TARGET_KIND = "challenge_target_kind"
    CHALLENGE_TARGET_FACE_KIND = "challenge_target_face_kind"
    CHALLENGE_FORBIDDEN = "challenge_forbidden"
    REBUT_CONTRARY_REQUIRED = "rebut_contrary_required"
    PRIMITIVE_EFFECT_HEAD = "primitive_effect_head"
    DEFECT_PROBLEM_FACE_REQUIRED = "defect_problem_face_required"
    UNKNOWN_DISCHARGE_KIND = "unknown_discharge_kind"
    BASE_OVERLAP = "base_overlap"
    BASE_NONPRIMITIVE = "base_nonprimitive"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationIssue:
    """One deterministic issue; paths and references contain no payload text."""

    phase: ValidationPhase
    code: ValidationCode
    path: str
    refs: tuple[RecordRef, ...] = ()
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.phase) is not ValidationPhase:
            raise TypeError("phase must be an exact ValidationPhase")
        if type(self.code) is not ValidationCode:
            raise TypeError("code must be an exact ValidationCode")
        if type(self.path) is not str or not self.path:
            raise TypeError("path must be a non-empty string")
        refs = tuple(self.refs)
        if any(type(ref) is not RecordRef for ref in refs):
            raise TypeError("issue refs must be exact RecordRef values")
        details = tuple(self.details)
        if any(type(detail) is not str for detail in details):
            raise TypeError("issue details must be strings")
        object.__setattr__(self, "refs", tuple(sorted(refs)))
        object.__setattr__(self, "details", tuple(sorted(details)))


def _issue_key(issue: ValidationIssue) -> tuple[object, ...]:
    return (
        int(issue.phase),
        issue.path,
        issue.code.value,
        tuple((ref.id, ref.version) for ref in issue.refs),
        issue.details,
    )


class PackageValidationError(ValueError):
    """Aggregate validation failure; no partial validated package exists."""

    issues: tuple[ValidationIssue, ...]

    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        canonical = tuple(sorted(set(issues), key=_issue_key))
        if not canonical:
            raise ValueError("PackageValidationError requires at least one issue")
        self.issues = canonical
        codes = ", ".join(issue.code.value for issue in canonical)
        super().__init__(f"package validation failed: {codes}")


@dataclass(frozen=True, slots=True)
class _RecordEntry:
    kind: RecordKind
    record: Record


_VALIDATION_FACTORY = object()


@dataclass(frozen=True, slots=True, init=False)
class ValidatedPackage:
    """Factory-only capability proving package/registry validation succeeded."""

    package: Package
    registry: PredicateRegistry
    _index: MappingProxyType[RecordRef, _RecordEntry]

    def __init__(
        self,
        package: Package,
        registry: PredicateRegistry,
        index: dict[RecordRef, _RecordEntry],
        *,
        _factory: object | None = None,
    ) -> None:
        if _factory is not _VALIDATION_FACTORY:
            raise TypeError("ValidatedPackage is created only by validate_package")
        object.__setattr__(self, "package", package)
        object.__setattr__(self, "registry", registry)
        object.__setattr__(self, "_index", MappingProxyType(dict(index)))

    @property
    def registry_id(self) -> str:
        return self.registry.registry_id

    def resolve(self, ref: RecordRef, kind: RecordKind) -> Record:
        """Resolve an exact reference at an expected record kind."""

        if type(ref) is not RecordRef:
            raise TypeError("ref must be an exact RecordRef")
        if type(kind) is not RecordKind:
            raise TypeError("kind must be an exact RecordKind")
        entry = self._index[ref]
        if entry.kind is not kind:
            raise KeyError((ref, kind))
        return entry.record

    def records(self, kind: RecordKind) -> tuple[Record, ...]:
        """Return all validated records of one kind in exact-ref order."""

        if type(kind) is not RecordKind:
            raise TypeError("kind must be an exact RecordKind")
        return tuple(
            entry.record
            for _, entry in sorted(
                self._index.items(),
                key=lambda item: (item[0].id, item[0].version),
            )
            if entry.kind is kind
        )


class _Validator:
    def __init__(self, package: Package, catalog: RegistryCatalog) -> None:
        self.package = package
        self.catalog = catalog
        self.registry: PredicateRegistry | None = None
        self.issues: list[ValidationIssue] = []
        self.buckets: dict[RecordRef, list[_RecordEntry]] = {}

    @staticmethod
    def _ref_text(ref: RecordRef) -> str:
        return f"{ref.id}@{ref.version}"

    def _record_path(self, kind: RecordKind, record: Record) -> str:
        return f"{kind.value}[{self._ref_text(record.ref)}]"

    def _add(
        self,
        phase: ValidationPhase,
        code: ValidationCode,
        path: str,
        *,
        refs: tuple[RecordRef, ...] = (),
        details: tuple[str, ...] = (),
    ) -> None:
        self.issues.append(
            ValidationIssue(
                phase=phase,
                code=code,
                path=path,
                refs=refs,
                details=details,
            )
        )

    def _resolve_any(self, ref: RecordRef, *, path: str) -> _RecordEntry | None:
        invalid = False
        if not ref.id:
            self._add(
                ValidationPhase.IDENTITY,
                ValidationCode.INVALID_ID,
                path,
                refs=(ref,),
            )
            invalid = True
        if ref.version <= 0:
            self._add(
                ValidationPhase.IDENTITY,
                ValidationCode.INVALID_VERSION,
                path,
                refs=(ref,),
            )
            invalid = True
        if invalid:
            return None
        entries = self.buckets.get(ref, ())
        if not entries:
            self._add(
                ValidationPhase.REFERENCES,
                ValidationCode.UNRESOLVED_REFERENCE,
                path,
                refs=(ref,),
            )
            return None
        if len(entries) != 1:
            return None
        return entries[0]

    def _lookup_any(self, ref: RecordRef) -> _RecordEntry | None:
        """Non-emitting lookup for dependent policy checks after direct checks."""

        entries = self.buckets.get(ref, ())
        if len(entries) != 1:
            return None
        return entries[0]

    def _lookup(self, ref: RecordRef, expected: RecordKind) -> Record | None:
        entry = self._lookup_any(ref)
        if entry is None or entry.kind is not expected:
            return None
        return entry.record

    def _resolve(
        self,
        ref: RecordRef,
        expected: RecordKind,
        *,
        path: str,
    ) -> Record | None:
        entry = self._resolve_any(ref, path=path)
        if entry is None:
            return None
        if entry.kind is not expected:
            self._add(
                ValidationPhase.REFERENCES,
                ValidationCode.REFERENCE_KIND_MISMATCH,
                path,
                refs=(ref,),
                details=(f"expected:{expected.value}", f"actual:{entry.kind.value}"),
            )
            return None
        return entry.record

    def _resolve_allowed(
        self,
        ref: RecordRef,
        allowed: frozenset[RecordKind],
        *,
        path: str,
    ) -> Record | None:
        entry = self._resolve_any(ref, path=path)
        if entry is None:
            return None
        if entry.kind not in allowed:
            self._add(
                ValidationPhase.REFERENCES,
                ValidationCode.REFERENCE_KIND_MISMATCH,
                path,
                refs=(ref,),
                details=(
                    f"allowed:{','.join(sorted(kind.value for kind in allowed))}",
                    f"actual:{entry.kind.value}",
                ),
            )
            return None
        return entry.record

    def _selector_is_locally_supported(self, closure: ClosureRecord) -> bool:
        """Check selector shape and typed references without emitting issues.

        Role diagnostics are dependent checks.  A malformed, unsupported, or
        unresolved selector receives its direct checker/reference diagnostic
        elsewhere and must not also be reported as a different role binding.
        """

        if self.registry is None:
            return False
        try:
            contract = self.registry.checker_contract(closure.checker)
        except KeyError:
            return False
        if not contract.supports_closure_selector(closure.selector.record_type):
            return False
        if not contract.accepts_selector_shape(
            record_type=closure.selector.record_type,
            where=closure.selector.where,
        ):
            return False
        selector_fields = {
            field_contract.field: field_contract
            for field_contract in contract.selector_field_contracts(
                closure.selector.record_type
            )
        }
        for key, value in closure.selector.where.items():
            field_contract = selector_fields[key]
            if field_contract.value_type is not CheckerDetailType.RECORD_REF:
                continue
            entry = self._lookup_any(cast(RecordRef, value))
            if (
                entry is None
                or entry.kind not in field_contract.allowed_record_kinds
            ):
                return False
        local_evaluation = _evaluate_local_closure(
            contract.local_closure_semantics,
            self.package,
            closure,
        )
        return local_evaluation is None or local_evaluation.selector_supported

    def _predicate(self, atom: AtomRecord) -> PredicateDefinition | None:
        if self.registry is None:
            return None
        try:
            return self.registry.predicate(atom.predicate)
        except KeyError:
            return None

    def _predicate_for_target(
        self,
        entry: _RecordEntry,
        *,
        path: str,
    ) -> PredicateDefinition | None:
        atom: AtomRecord | None = None
        if entry.kind is RecordKind.ATOM:
            atom = cast(AtomRecord, entry.record)
        elif entry.kind is RecordKind.RULE:
            rule = cast(RuleRecord, entry.record)
            atom = cast(AtomRecord | None, self._lookup(rule.head, RecordKind.ATOM))
        elif entry.kind is RecordKind.FACE:
            face = cast(FaceRecord, entry.record)
            owner = self._lookup(face.owner_rule, RecordKind.RULE)
            if owner is not None:
                rule = cast(RuleRecord, owner)
                atom = cast(AtomRecord | None, self._lookup(rule.head, RecordKind.ATOM))
        return self._predicate(atom) if atom is not None else None

    def _predicate_for_certificate_subject(
        self,
        entry: _RecordEntry,
        *,
        path: str,
    ) -> PredicateDefinition | None:
        if entry.kind in {RecordKind.ATOM, RecordKind.RULE, RecordKind.FACE}:
            return self._predicate_for_target(entry, path=path)
        if entry.kind is RecordKind.CHALLENGE:
            challenge = cast(ChallengeRecord, entry.record)
            target = self._lookup(challenge.target, challenge.target_kind)
            if target is None:
                return None
            return self._predicate_for_target(
                _RecordEntry(challenge.target_kind, target),
                path=f"{path}.target",
            )
        if entry.kind is RecordKind.DISCHARGE:
            discharge = cast(DischargeRecord, entry.record)
            challenge = cast(
                ChallengeRecord | None,
                self._lookup(discharge.challenge, RecordKind.CHALLENGE),
            )
            if challenge is None:
                return None
            target = self._lookup(challenge.target, challenge.target_kind)
            if target is None:
                return None
            return self._predicate_for_target(
                _RecordEntry(challenge.target_kind, target),
                path=f"{path}.challenge.target",
            )
        return None

    def validate_header_and_identity(self) -> None:
        header = self.package.header
        if header.schema != PFF_CORE_SCHEMA:
            self._add(
                ValidationPhase.HEADER,
                ValidationCode.SCHEMA_MISMATCH,
                "header.schema",
                details=(f"expected:{PFF_CORE_SCHEMA}",),
            )
        for field_name in ("package_id", "cut_id", "frame_id", "registry_id"):
            if not getattr(header, field_name):
                self._add(
                    ValidationPhase.HEADER,
                    ValidationCode.INVALID_ID,
                    f"header.{field_name}",
                )
        try:
            self.registry = self.catalog.lookup(header.registry_id)
        except KeyError:
            self._add(
                ValidationPhase.HEADER,
                ValidationCode.UNKNOWN_REGISTRY,
                "header.registry_id",
                details=(header.registry_id,),
            )

        for kind, record in self.package.iter_records():
            path = self._record_path(kind, record)
            self.buckets.setdefault(record.ref, []).append(_RecordEntry(kind, record))
            if not record.id:
                self._add(ValidationPhase.IDENTITY, ValidationCode.INVALID_ID, f"{path}.id")
            if record.version <= 0:
                self._add(
                    ValidationPhase.IDENTITY,
                    ValidationCode.INVALID_VERSION,
                    f"{path}.version",
                    refs=(record.ref,),
                )
            if record.id.startswith(RESERVED_ID_PREFIX):
                self._add(
                    ValidationPhase.IDENTITY,
                    ValidationCode.RESERVED_ID,
                    f"{path}.id",
                    refs=(record.ref,),
                )

        for ref, entries in self.buckets.items():
            if len(entries) > 1:
                self._add(
                    ValidationPhase.IDENTITY,
                    ValidationCode.DUPLICATE_RECORD,
                    f"records[{self._ref_text(ref)}]",
                    refs=(ref,),
                    details=tuple(entry.kind.value for entry in entries),
                )

    def validate_atoms(self) -> None:
        if self.registry is None:
            return
        for atom in self.package.atoms:
            path = self._record_path(RecordKind.ATOM, atom)
            try:
                predicate = self.registry.predicate(atom.predicate)
            except KeyError:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.UNKNOWN_PREDICATE,
                    f"{path}.predicate",
                    refs=(atom.ref,),
                    details=(atom.predicate,),
                )
                continue

            if len(atom.args) != len(predicate.arg_type_ids):
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.PREDICATE_ARITY,
                    f"{path}.args",
                    refs=(atom.ref,),
                    details=(
                        f"expected:{len(predicate.arg_type_ids)}",
                        f"actual:{len(atom.args)}",
                    ),
                )
            else:
                for index, (value, argument_type_id) in enumerate(
                    zip(atom.args, predicate.arg_type_ids, strict=True)
                ):
                    contract = self.registry.argument_type(argument_type_id)
                    if not contract.accepts(value):
                        self._add(
                            ValidationPhase.POLICIES,
                            ValidationCode.PREDICATE_ARG_TYPE,
                            f"{path}.args[{index}]",
                            refs=(atom.ref,),
                            details=(argument_type_id,),
                        )

            frame_policy = self.registry.frame_policy(predicate.frame_policy_id)
            if not frame_policy.accepts(
                atom.frame,
                package_frame=self.package.header.frame_id,
            ):
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.PREDICATE_FRAME,
                    f"{path}.frame",
                    refs=(atom.ref,),
                )
            if not predicate.grade_policy.accepts(atom.grade):
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.PREDICATE_GRADE,
                    f"{path}.grade",
                    refs=(atom.ref,),
                )
            if atom.primitive and not predicate.primitive_allowed:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.PRIMITIVE_FORBIDDEN,
                    f"{path}.primitive",
                    refs=(atom.ref,),
                )

    def validate_rules_and_faces(self) -> None:
        for rule in self.package.rules:
            path = self._record_path(RecordKind.RULE, rule)
            head = cast(
                AtomRecord | None,
                self._resolve(rule.head, RecordKind.ATOM, path=f"{path}.head"),
            )
            if head is not None and head.primitive:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.PRIMITIVE_HAS_DERIVATION,
                    f"{path}.head",
                    refs=(head.ref, rule.ref),
                )
            for ref in sorted(rule.positive):
                self._resolve(ref, RecordKind.ATOM, path=f"{path}.positive")
            for literal in sorted(
                rule.negative,
                key=lambda item: (item.atom.id, item.atom.version, item.closure.id, item.closure.version),
            ):
                self._resolve(literal.atom, RecordKind.ATOM, path=f"{path}.negative.atom")
                self._resolve(
                    literal.closure,
                    RecordKind.CLOSURE,
                    path=f"{path}.negative.closure",
                )
            certificate = cast(
                CertificateRecord | None,
                self._resolve(
                    rule.certificate,
                    RecordKind.CERTIFICATE,
                    path=f"{path}.certificate",
                ),
            )
            if certificate is not None and certificate.subject != rule.ref:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CERTIFICATE_SUBJECT_MISMATCH,
                    f"{path}.certificate",
                    refs=(rule.ref, certificate.ref, certificate.subject),
                )
            for face_ref in sorted(rule.faces):
                face = cast(
                    FaceRecord | None,
                    self._resolve(face_ref, RecordKind.FACE, path=f"{path}.faces"),
                )
                if face is not None and face.owner_rule != rule.ref:
                    self._add(
                        ValidationPhase.BINDINGS,
                        ValidationCode.FACE_OWNER_MISMATCH,
                        f"{path}.faces",
                        refs=(rule.ref, face.ref, face.owner_rule),
                    )

        for face in self.package.faces:
            path = self._record_path(RecordKind.FACE, face)
            if face.depends_on_version is not None:
                if not face.depends_on_version.id:
                    self._add(
                        ValidationPhase.IDENTITY,
                        ValidationCode.INVALID_ID,
                        f"{path}.depends_on_version",
                    )
                if face.depends_on_version.version <= 0:
                    self._add(
                        ValidationPhase.IDENTITY,
                        ValidationCode.INVALID_VERSION,
                        f"{path}.depends_on_version",
                    )
            owner = cast(
                RuleRecord | None,
                self._resolve(
                    face.owner_rule,
                    RecordKind.RULE,
                    path=f"{path}.owner_rule",
                ),
            )
            blocker_closure = cast(
                ClosureRecord | None,
                self._resolve(
                    face.blocker_closure,
                    RecordKind.CLOSURE,
                    path=f"{path}.blocker_closure",
                ),
            )
            role_mismatch = False
            if (
                blocker_closure is not None
                and self._selector_is_locally_supported(blocker_closure)
            ):
                where = blocker_closure.selector.where
                selected_target = where.get("target")
                if (
                    blocker_closure.selector.record_type is not RecordKind.CHALLENGE
                    or set(where) != {"target"}
                ):
                    role_mismatch = True
                elif type(selected_target) is not RecordRef:
                    role_mismatch = True
                elif selected_target != face.ref:
                    selected_entry = self._lookup_any(selected_target)
                    role_mismatch = (
                        selected_entry is not None
                        and selected_entry.kind
                        in {RecordKind.ATOM, RecordKind.RULE, RecordKind.FACE}
                    )
            if blocker_closure is not None and role_mismatch:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CLOSURE_ROLE_MISMATCH,
                    f"{path}.blocker_closure",
                    refs=(face.ref, blocker_closure.ref),
                    details=("expected:challenge.target",),
                )
            if owner is not None and face.ref not in owner.faces:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.FACE_OWNER_MISMATCH,
                    f"{path}.owner_rule",
                    refs=(face.ref, owner.ref),
                )
            if self.registry is None:
                continue
            if face.kind not in self.registry.known_face_kinds:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.UNKNOWN_FACE_KIND,
                    f"{path}.kind",
                    refs=(face.ref,),
                    details=(face.kind,),
                )
                continue
            if owner is not None:
                head = cast(
                    AtomRecord | None,
                    self._lookup(owner.head, RecordKind.ATOM),
                )
                predicate = self._predicate(head) if head is not None else None
                if predicate is not None and face.kind not in predicate.allowed_face_kinds:
                    self._add(
                        ValidationPhase.POLICIES,
                        ValidationCode.FACE_KIND_FORBIDDEN,
                        f"{path}.kind",
                        refs=(face.ref, owner.ref),
                        details=(face.kind,),
                    )

    def validate_certificates_and_closures(self) -> None:
        for certificate in self.package.certificates:
            path = self._record_path(RecordKind.CERTIFICATE, certificate)
            subject = self._resolve_any(certificate.subject, path=f"{path}.subject")
            if self.registry is None:
                continue
            try:
                contract = self.registry.checker_contract(certificate.checker)
            except KeyError:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.UNKNOWN_CHECKER,
                    f"{path}.checker",
                    refs=(certificate.ref,),
                    details=(certificate.checker,),
                )
                continue
            if subject is not None and not contract.permits_certificate(subject.kind):
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.CHECKER_NOT_PERMITTED,
                    f"{path}.checker",
                    refs=(certificate.ref, subject.record.ref),
                    details=(subject.kind.value,),
                )
            details_valid = contract.accepts_details(certificate.details)
            if not certificate.payload_hash or not details_valid:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.CHECKER_PAYLOAD,
                    f"{path}.details",
                    refs=(certificate.ref,),
                )
            if details_valid:
                for detail_field in contract.detail_fields:
                    if detail_field.value_type is CheckerDetailType.RECORD_REF:
                        detail_ref = cast(
                            RecordRef,
                            certificate.details[detail_field.key],
                        )
                        self._resolve_allowed(
                            detail_ref,
                            detail_field.allowed_record_kinds,
                            path=f"{path}.details.{detail_field.key}",
                        )
            if subject is not None and subject.kind in {
                RecordKind.RULE,
                RecordKind.CHALLENGE,
                RecordKind.DISCHARGE,
            }:
                linked_certificate = cast(
                    RuleRecord | ChallengeRecord | DischargeRecord,
                    subject.record,
                ).certificate
                if linked_certificate != certificate.ref:
                    self._add(
                        ValidationPhase.BINDINGS,
                        ValidationCode.CERTIFICATE_SUBJECT_MISMATCH,
                        f"{path}.subject",
                        refs=(certificate.ref, subject.record.ref, linked_certificate),
                    )

            if subject is not None:
                predicate = self._predicate_for_certificate_subject(
                    subject,
                    path=f"{path}.subject",
                )
                if (
                    predicate is not None
                    and certificate.checker not in predicate.checker_contract_ids
                ):
                    self._add(
                        ValidationPhase.POLICIES,
                        ValidationCode.CHECKER_NOT_PERMITTED,
                        f"{path}.checker",
                        refs=(certificate.ref, subject.record.ref),
                        details=(predicate.predicate_id,),
                    )

        for closure in self.package.closures:
            path = self._record_path(RecordKind.CLOSURE, closure)
            contract = None
            selector_supported = False
            selector_refs_valid = False
            local_evaluation = None
            if self.registry is not None:
                try:
                    contract = self.registry.checker_contract(closure.checker)
                except KeyError:
                    self._add(
                        ValidationPhase.POLICIES,
                        ValidationCode.UNKNOWN_CHECKER,
                        f"{path}.checker",
                        refs=(closure.ref,),
                        details=(closure.checker,),
                    )
                else:
                    wrong_use = CheckerUse.CLOSURE not in contract.uses
                    kind_supported = contract.supports_closure_selector(
                        closure.selector.record_type
                    )
                    shape_supported = (
                        kind_supported
                        and contract.accepts_selector_shape(
                            record_type=closure.selector.record_type,
                            where=closure.selector.where,
                        )
                    )
                    if shape_supported:
                        local_evaluation = _evaluate_local_closure(
                            contract.local_closure_semantics,
                            self.package,
                            closure,
                        )
                    selector_supported = shape_supported and (
                        local_evaluation is None
                        or local_evaluation.selector_supported
                    )
                    if wrong_use:
                        self._add(
                            ValidationPhase.POLICIES,
                            ValidationCode.CHECKER_NOT_PERMITTED,
                            f"{path}.checker",
                            refs=(closure.ref,),
                            details=(closure.selector.record_type.value,),
                        )
                    elif not selector_supported:
                        if closure.result is not CheckResult.OPEN:
                            self._add(
                                ValidationPhase.POLICIES,
                                (
                                    ValidationCode.CHECKER_PAYLOAD
                                    if kind_supported
                                    else ValidationCode.CHECKER_NOT_PERMITTED
                                ),
                                (
                                    f"{path}.selector"
                                    if kind_supported
                                    else f"{path}.checker"
                                ),
                                refs=(closure.ref,),
                                details=(closure.selector.record_type.value,),
                            )
                    else:
                        selector_refs_valid = True
                        selector_fields = {
                            field_contract.field: field_contract
                            for field_contract in contract.selector_field_contracts(
                                closure.selector.record_type
                            )
                        }
                        for key, value in closure.selector.where.items():
                            field_contract = selector_fields[key]
                            if (
                                field_contract.value_type
                                is CheckerDetailType.RECORD_REF
                            ):
                                selector_ref = cast(RecordRef, value)
                                if self._resolve_allowed(
                                    selector_ref,
                                    field_contract.allowed_record_kinds,
                                    path=f"{path}.selector.where.{key}",
                                ) is None:
                                    selector_refs_valid = False
            cut_valid = closure.cut_id == self.package.header.cut_id
            if not cut_valid:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CLOSURE_CUT_MISMATCH,
                    f"{path}.cut_id",
                    refs=(closure.ref,),
                )
            frame_valid = not (
                self.registry is not None
                and contract is not None
                and CheckerUse.CLOSURE in contract.uses
                and contract.closure_frame_policy_id is not None
                and not self.registry.frame_policy(
                    contract.closure_frame_policy_id
                ).accepts(
                    closure.frame,
                    package_frame=self.package.header.frame_id,
                )
            )
            if not frame_valid:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CLOSURE_FRAME_MISMATCH,
                    f"{path}.frame",
                    refs=(closure.ref,),
                )
            members_valid = True
            for member in sorted(closure.members):
                if self._resolve(
                    member,
                    closure.selector.record_type,
                    path=f"{path}.members",
                ) is None:
                    members_valid = False
            if (
                local_evaluation is not None
                and selector_supported
                and selector_refs_valid
                and members_valid
                and cut_valid
                and frame_valid
                and all(len(entries) == 1 for entries in self.buckets.values())
                and closure.result is not local_evaluation.expected_result
            ):
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CLOSURE_RESULT_MISMATCH,
                    f"{path}.result",
                    refs=(closure.ref,),
                    details=(
                        f"expected:{local_evaluation.expected_result.value}",
                        f"actual:{closure.result.value}",
                    ),
                )

    def validate_contraries(self) -> None:
        for contrary in self.package.contraries:
            path = self._record_path(RecordKind.CONTRARY, contrary)
            left = cast(
                AtomRecord | None,
                self._resolve(
                    contrary.left,
                    RecordKind.ATOM,
                    path=f"{path}.left",
                ),
            )
            right = cast(
                AtomRecord | None,
                self._resolve(
                    contrary.right,
                    RecordKind.ATOM,
                    path=f"{path}.right",
                ),
            )
            if self.registry is None or left is None or right is None:
                continue
            left_definition = self._predicate(left)
            right_definition = self._predicate(right)
            if left_definition is None or right_definition is None:
                continue
            left_policy = self.registry.contrary_policy(
                left_definition.contrary_policy_id
            )
            right_policy = self.registry.contrary_policy(
                right_definition.contrary_policy_id
            )
            if (
                left_policy.mode is ContraryPolicyMode.FORBIDDEN
                or right_policy.mode is ContraryPolicyMode.FORBIDDEN
            ):
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.CONTRARY_FORBIDDEN,
                    path,
                    refs=(contrary.ref, left.ref, right.ref),
                )
                continue
            left_key = left_policy.comparison_key(args=left.args, frame=left.frame)
            right_key = right_policy.comparison_key(args=right.args, frame=right.frame)
            if (
                not left_policy.accepts_boundary(contrary.boundary)
                or not right_policy.accepts_boundary(contrary.boundary)
                or left_key != right_key
            ):
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.CONTRARY_BOUNDARY_MISMATCH,
                    f"{path}.boundary",
                    refs=(contrary.ref, left.ref, right.ref),
                )

    def validate_challenges_and_discharges(self) -> None:
        for challenge in self.package.challenges:
            path = self._record_path(RecordKind.CHALLENGE, challenge)
            known_kind = (
                self.registry is not None
                and challenge.kind in self.registry.known_challenge_kinds
            )
            if self.registry is not None and not known_kind:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.UNKNOWN_CHALLENGE_KIND,
                    f"{path}.kind",
                    refs=(challenge.ref,),
                    details=(challenge.kind,),
                )
            target_contract = (
                self.registry.challenge_target_contract(challenge.kind)
                if self.registry is not None and known_kind
                else None
            )
            allowed_targets = (
                target_contract.allowed_target_kinds
                if target_contract is not None
                else frozenset({RecordKind.ATOM, RecordKind.RULE, RecordKind.FACE})
            )
            if challenge.target_kind not in allowed_targets:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CHALLENGE_TARGET_KIND,
                    f"{path}.target_kind",
                    refs=(challenge.ref,),
                    details=(challenge.target_kind.value,),
                )
                target = None
            else:
                target = self._resolve_any(challenge.target, path=f"{path}.target")
                if target is not None and target.kind is not challenge.target_kind:
                    self._add(
                        ValidationPhase.REFERENCES,
                        ValidationCode.REFERENCE_KIND_MISMATCH,
                        f"{path}.target",
                        refs=(challenge.target,),
                        details=(
                            f"expected:{challenge.target_kind.value}",
                            f"actual:{target.kind.value}",
                        ),
                    )
                    target = None
                elif (
                    target_contract is not None
                    and target_contract.required_face_kind is not None
                    and target is not None
                    and target.kind is RecordKind.FACE
                ):
                    face = cast(FaceRecord, target.record)
                    if face.kind != target_contract.required_face_kind:
                        self._add(
                            ValidationPhase.BINDINGS,
                            ValidationCode.CHALLENGE_TARGET_FACE_KIND,
                            f"{path}.target",
                            refs=(challenge.ref, face.ref),
                            details=(
                                f"actual:{face.kind}",
                                f"expected:{target_contract.required_face_kind}",
                            ),
                        )
            challenge_certificate = cast(
                CertificateRecord | None,
                self._resolve(
                    challenge.certificate,
                    RecordKind.CERTIFICATE,
                    path=f"{path}.certificate",
                ),
            )
            if (
                challenge_certificate is not None
                and challenge_certificate.subject != challenge.ref
            ):
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CERTIFICATE_SUBJECT_MISMATCH,
                    f"{path}.certificate",
                    refs=(
                        challenge.ref,
                        challenge_certificate.ref,
                        challenge_certificate.subject,
                    ),
                )
            discharge_closure = cast(
                ClosureRecord | None,
                self._resolve(
                    challenge.discharge_closure,
                    RecordKind.CLOSURE,
                    path=f"{path}.discharge_closure",
                ),
            )
            role_mismatch = False
            if (
                discharge_closure is not None
                and self._selector_is_locally_supported(discharge_closure)
            ):
                where = discharge_closure.selector.where
                selected_challenge = where.get("challenge")
                if (
                    discharge_closure.selector.record_type
                    is not RecordKind.DISCHARGE
                    or set(where) != {"challenge"}
                ):
                    role_mismatch = True
                elif type(selected_challenge) is not RecordRef:
                    role_mismatch = True
                elif selected_challenge != challenge.ref:
                    selected_entry = self._lookup_any(selected_challenge)
                    role_mismatch = (
                        selected_entry is not None
                        and selected_entry.kind is RecordKind.CHALLENGE
                    )
            if discharge_closure is not None and role_mismatch:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CLOSURE_ROLE_MISMATCH,
                    f"{path}.discharge_closure",
                    refs=(challenge.ref, discharge_closure.ref),
                    details=("expected:discharge.challenge",),
                )
            contrary_atom = (
                cast(
                    AtomRecord | None,
                    self._resolve(
                        challenge.contrary_atom,
                        RecordKind.ATOM,
                        path=f"{path}.contrary_atom",
                    ),
                )
                if challenge.contrary_atom is not None
                else None
            )
            if (
                known_kind
                and challenge.kind == "rebut"
                and contrary_atom is not None
                and contrary_atom.primitive
            ):
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.PRIMITIVE_EFFECT_HEAD,
                    f"{path}.contrary_atom",
                    refs=(challenge.ref, contrary_atom.ref),
                )
            if challenge.problem_face_atom is not None:
                self._resolve(
                    challenge.problem_face_atom,
                    RecordKind.ATOM,
                    path=f"{path}.problem_face_atom",
                )
            if challenge.kind == "rebut" and challenge.contrary_atom is None:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.REBUT_CONTRARY_REQUIRED,
                    f"{path}.contrary_atom",
                    refs=(challenge.ref,),
                )
            if challenge.kind == "defect" and challenge.problem_face_atom is None:
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.DEFECT_PROBLEM_FACE_REQUIRED,
                    f"{path}.problem_face_atom",
                    refs=(challenge.ref,),
                )
            if self.registry is not None and target is not None:
                predicate = self._predicate_for_target(
                    target,
                    path=f"{path}.target",
                )
                if (
                    predicate is not None
                    and challenge.kind in self.registry.known_challenge_kinds
                    and challenge.kind not in predicate.allowed_challenge_kinds
                ):
                    self._add(
                        ValidationPhase.POLICIES,
                        ValidationCode.CHALLENGE_FORBIDDEN,
                        f"{path}.kind",
                        refs=(challenge.ref, target.record.ref),
                        details=(challenge.kind, predicate.predicate_id),
                    )

        for discharge in self.package.discharges:
            path = self._record_path(RecordKind.DISCHARGE, discharge)
            self._resolve(
                discharge.challenge,
                RecordKind.CHALLENGE,
                path=f"{path}.challenge",
            )
            discharge_certificate = cast(
                CertificateRecord | None,
                self._resolve(
                    discharge.certificate,
                    RecordKind.CERTIFICATE,
                    path=f"{path}.certificate",
                ),
            )
            if (
                discharge_certificate is not None
                and discharge_certificate.subject != discharge.ref
            ):
                self._add(
                    ValidationPhase.BINDINGS,
                    ValidationCode.CERTIFICATE_SUBJECT_MISMATCH,
                    f"{path}.certificate",
                    refs=(
                        discharge.ref,
                        discharge_certificate.ref,
                        discharge_certificate.subject,
                    ),
                )
            if self.registry is not None and discharge.kind not in self.registry.known_discharge_kinds:
                self._add(
                    ValidationPhase.POLICIES,
                    ValidationCode.UNKNOWN_DISCHARGE_KIND,
                    f"{path}.kind",
                    refs=(discharge.ref,),
                    details=(discharge.kind,),
                )
            # Known but incompatible pairs remain valid semantic data.  The
            # later compiler derives TypeMatch; validation must not pre-judge it.

    def validate_base(self) -> None:
        memberships: dict[RecordRef, list[str]] = {}
        for field_name in ("live", "excluded", "open"):
            refs = getattr(self.package.base, field_name)
            for ref in sorted(refs):
                memberships.setdefault(ref, []).append(field_name)
                atom = cast(
                    AtomRecord | None,
                    self._resolve(
                        ref,
                        RecordKind.ATOM,
                        path=f"base.{field_name}",
                    ),
                )
                if atom is not None and not atom.primitive:
                    self._add(
                        ValidationPhase.BASE,
                        ValidationCode.BASE_NONPRIMITIVE,
                        f"base.{field_name}",
                        refs=(atom.ref,),
                    )
        for ref, fields in memberships.items():
            if len(fields) > 1:
                self._add(
                    ValidationPhase.BASE,
                    ValidationCode.BASE_OVERLAP,
                    f"base[{self._ref_text(ref)}]",
                    refs=(ref,),
                    details=tuple(fields),
                )

    def run(self) -> ValidatedPackage:
        self.validate_header_and_identity()
        self.validate_atoms()
        self.validate_rules_and_faces()
        self.validate_certificates_and_closures()
        self.validate_contraries()
        self.validate_challenges_and_discharges()
        self.validate_base()
        if self.issues:
            raise PackageValidationError(tuple(self.issues))

        assert self.registry is not None
        index = {
            ref: entries[0]
            for ref, entries in self.buckets.items()
            if len(entries) == 1
        }
        return ValidatedPackage(
            self.package,
            self.registry,
            index,
            _factory=_VALIDATION_FACTORY,
        )


def validate_package(package: Package, catalog: RegistryCatalog) -> ValidatedPackage:
    """Validate one immutable package against its exact registry binding.

    The function aggregates deterministic independent issues, then raises one
    typed error.  No partial ``ValidatedPackage`` is returned on failure.
    """

    if type(package) is not Package:
        raise TypeError("package must be an exact Package candidate")
    if type(catalog) is not RegistryCatalog:
        raise TypeError("catalog must be an exact immutable RegistryCatalog")
    return _Validator(package, catalog).run()


__all__ = [
    "PFF_CORE_SCHEMA",
    "PackageValidationError",
    "ValidatedPackage",
    "ValidationCode",
    "ValidationIssue",
    "ValidationPhase",
    "validate_package",
]
