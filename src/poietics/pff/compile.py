"""Deterministic lowering from a validated PFF package to ground artifacts.

This module owns the single package-to-ground compilation path.  It consumes
only the capability minted by :func:`poietics.pff.validate.validate_package`,
reads already-bound checker outcomes, and constructs an immutable ground
program plus a deterministic source map.  It does not execute checkers,
providers, parsers, or the ground evaluator.

The current bounded slice also implements the admitted challenge/discharge
gates and effects.  Challenge semantics that remain underspecified fail closed
with challenge-rooted diagnostics before construction begins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, cast

from ..ground.model import AtomRef, GroundProgram, GroundRule, RuleRef
from .model import (
    AtomRecord,
    CertificateRecord,
    ChallengeRecord,
    CheckResult,
    ClosureRecord,
    ContraryRecord,
    DischargeRecord,
    FaceRecord,
    RecordKind,
    RecordRef,
    RuleRecord,
)
from .validate import ValidatedPackage


class GroundArtifactKind(StrEnum):
    """Kinds of ground artifact recorded in the compiler source map."""

    ATOM = "atom"
    RULE = "rule"


class CompilationRole(StrEnum):
    """Stable compiler roles used by generated identities and source maps."""

    SOURCE_ATOM = "source-atom"
    CERT_VALID = "cert-valid"
    CERT_FAILED = "cert-failed"
    CERT_OPEN = "cert-open"
    CLOSURE_READY = "closure-ready"
    CLOSURE_FAILED = "closure-failed"
    CLOSURE_OPEN = "closure-open"
    FACE = "face"
    HAS_OPEN_CHALLENGE = "has-open-challenge"
    CLEAR = "clear"
    LIVE_CASE = "live-case"
    CHALLENGE_CASE = "challenge-case"
    DISCHARGED = "discharged"
    OPEN_CHALLENGE = "open-challenge"
    TYPE_MATCH = "type-match"
    DISCHARGE_CASE = "discharge-case"
    RULE_CASE = "rule-case"
    HEAD_BRIDGE = "head-bridge"
    CLEAR_FACE = "clear-face"
    CHALLENGE_CASE_RULE = "challenge-case-rule"
    DISCHARGE_CASE_RULE = "discharge-case-rule"
    DISCHARGED_BRIDGE = "discharged-bridge"
    OPEN_CHALLENGE_RULE = "open-challenge-rule"
    REBUT_EFFECT = "rebut-effect"
    FACE_BLOCK_EFFECT = "face-block-effect"


class CompilationCode(StrEnum):
    """Typed compiler diagnostics that do not assign semantic status."""

    # Retained for callers that construct legacy issues.  The compiler no
    # longer emits this blanket diagnostic for challenge/discharge records.
    UNSUPPORTED_RECORD_KIND = "unsupported_record_kind"
    RULE_TARGET_BLOCKING_UNSUPPORTED = "rule_target_blocking_unsupported"
    REVOCATION_SELECTION_UNSUPPORTED = "revocation_selection_unsupported"
    CURRENTNESS_TARGET_UNSUPPORTED = "currentness_target_unsupported"
    PROBLEM_FACE_LIFECYCLE_UNSUPPORTED = "problem_face_lifecycle_unsupported"
    CHALLENGE_EFFECT_UNSUPPORTED = "challenge_effect_unsupported"


_CHALLENGE_CODE_RANK: Mapping[CompilationCode, int] = MappingProxyType(
    {
        CompilationCode.REVOCATION_SELECTION_UNSUPPORTED: 0,
        CompilationCode.CURRENTNESS_TARGET_UNSUPPORTED: 1,
        CompilationCode.PROBLEM_FACE_LIFECYCLE_UNSUPPORTED: 2,
        CompilationCode.RULE_TARGET_BLOCKING_UNSUPPORTED: 3,
        CompilationCode.CHALLENGE_EFFECT_UNSUPPORTED: 4,
    }
)
_DEFERRED_CHALLENGE_CODES: Mapping[str, CompilationCode] = MappingProxyType(
    {
        "revoke": CompilationCode.REVOCATION_SELECTION_UNSUPPORTED,
        "currentness_gap": CompilationCode.CURRENTNESS_TARGET_UNSUPPORTED,
        "defect": CompilationCode.PROBLEM_FACE_LIFECYCLE_UNSUPPORTED,
    }
)
_FACE_BLOCKING_CHALLENGE_KINDS = frozenset(
    {
        "undercut",
        "wound",
        "localisation_gap",
        "recovery_gap",
        "closure_gap",
    }
)
_RULE_TARGET_BLOCKING_KINDS = frozenset({"undercut", "wound"})
_COMPILER_MAPPED_CHALLENGE_KINDS = frozenset(
    {"rebut", *_FACE_BLOCKING_CHALLENGE_KINDS}
)


_ATOM_ROLES = frozenset(
    {
        CompilationRole.CERT_VALID,
        CompilationRole.CERT_FAILED,
        CompilationRole.CERT_OPEN,
        CompilationRole.CLOSURE_READY,
        CompilationRole.CLOSURE_FAILED,
        CompilationRole.CLOSURE_OPEN,
        CompilationRole.FACE,
        CompilationRole.HAS_OPEN_CHALLENGE,
        CompilationRole.CLEAR,
        CompilationRole.LIVE_CASE,
        CompilationRole.CHALLENGE_CASE,
        CompilationRole.DISCHARGED,
        CompilationRole.OPEN_CHALLENGE,
        CompilationRole.TYPE_MATCH,
        CompilationRole.DISCHARGE_CASE,
    }
)
_RULE_ROLES = frozenset(
    {
        CompilationRole.RULE_CASE,
        CompilationRole.HEAD_BRIDGE,
        CompilationRole.CLEAR_FACE,
        CompilationRole.CHALLENGE_CASE_RULE,
        CompilationRole.DISCHARGE_CASE_RULE,
        CompilationRole.DISCHARGED_BRIDGE,
        CompilationRole.OPEN_CHALLENGE_RULE,
        CompilationRole.REBUT_EFFECT,
        CompilationRole.FACE_BLOCK_EFFECT,
    }
)
# Kept only to preserve construction of the legacy public issue shape.
_PENDING_KINDS = (
    RecordKind.CHALLENGE,
    RecordKind.DISCHARGE,
)
_PENDING_KIND_ORDER = {
    kind: position for position, kind in enumerate(_PENDING_KINDS)
}


def _require_record_ref(ref: RecordRef) -> None:
    if type(ref) is not RecordRef:
        raise TypeError("source reference must be an exact RecordRef")
    if not ref.id or ref.version <= 0:
        raise ValueError(
            "source reference must have a non-empty ID and positive version"
        )


def _reference_token(ref: RecordRef) -> str:
    """Return the private, injective token used inside compiled identities.

    Consumers treat ground references as opaque.  The final ``@`` separates
    the canonical positive decimal version, so source IDs may themselves
    contain ``@`` or any other Unicode character without losing identity.
    """

    _require_record_ref(ref)
    return f"{ref.id}@{ref.version}"


def _source_atom(ref: RecordRef) -> AtomRef:
    return AtomRef(_reference_token(ref))


def _generated_atom(role: CompilationRole, ref: RecordRef) -> AtomRef:
    if type(role) is not CompilationRole or role not in _ATOM_ROLES:
        raise TypeError("generated atom role must be an atom CompilationRole")
    return AtomRef(f"__pff__:{role.value}({_reference_token(ref)})")


def _generated_rule(role: CompilationRole, ref: RecordRef) -> RuleRef:
    if type(role) is not CompilationRole or role not in _RULE_ROLES:
        raise TypeError("generated rule role must be a rule CompilationRole")
    return RuleRef(f"__pff__:{role.value}({_reference_token(ref)})")


@dataclass(frozen=True, slots=True, order=True)
class SourceRecord:
    """One exact package record responsible for a compiled artifact."""

    kind: RecordKind
    ref: RecordRef

    def __post_init__(self) -> None:
        if type(self.kind) is not RecordKind:
            raise TypeError("source kind must be an exact RecordKind")
        _require_record_ref(self.ref)


def _source_record_key(source: SourceRecord) -> tuple[str, str, int]:
    return (source.kind.value, source.ref.id, source.ref.version)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactOrigin:
    """Compiler source identity, not the post-evaluation provenance DAG."""

    artifact_kind: GroundArtifactKind
    artifact_ref: str
    role: CompilationRole
    sources: tuple[SourceRecord, ...]

    def __post_init__(self) -> None:
        if type(self.artifact_kind) is not GroundArtifactKind:
            raise TypeError("artifact kind must be an exact GroundArtifactKind")
        if type(self.artifact_ref) is not str or not self.artifact_ref:
            raise TypeError("artifact reference must be a non-empty string")
        if type(self.role) is not CompilationRole:
            raise TypeError("origin role must be an exact CompilationRole")
        allowed_roles = (
            _ATOM_ROLES | {CompilationRole.SOURCE_ATOM}
            if self.artifact_kind is GroundArtifactKind.ATOM
            else _RULE_ROLES
        )
        if self.role not in allowed_roles:
            raise ValueError("origin role is incompatible with its artifact kind")
        if isinstance(self.sources, (str, bytes)):
            raise TypeError("origin sources must be a collection")
        sources = tuple(self.sources)
        if not sources or any(type(source) is not SourceRecord for source in sources):
            raise TypeError("origin sources must contain exact SourceRecord values")
        if len(set(sources)) != len(sources):
            raise ValueError("origin sources must not contain duplicates")
        object.__setattr__(
            self,
            "sources",
            tuple(sorted(sources, key=_source_record_key)),
        )


def _origin_key(origin: ArtifactOrigin) -> tuple[object, ...]:
    return (
        origin.artifact_kind.value,
        origin.artifact_ref,
        origin.role.value,
        tuple(_source_record_key(source) for source in origin.sources),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CompiledContrary:
    """One explicit symmetric contrary relation kept outside ground rules."""

    source: RecordRef
    first: AtomRef
    second: AtomRef
    boundary: str

    def __post_init__(self) -> None:
        _require_record_ref(self.source)
        for field_name in ("first", "second", "boundary"):
            value = getattr(self, field_name)
            if type(value) is not str or not value:
                raise TypeError(f"compiled contrary {field_name} must be non-empty")


@dataclass(frozen=True, slots=True, order=True)
class CompilationIssue:
    """One deterministic reason a validated package is not yet lowerable."""

    code: CompilationCode
    record_kind: RecordKind
    ref: RecordRef

    def __post_init__(self) -> None:
        if type(self.code) is not CompilationCode:
            raise TypeError("compilation issue code must be exact")
        if type(self.record_kind) is not RecordKind:
            raise TypeError("compilation issue record kind must be exact")
        if self.code is CompilationCode.UNSUPPORTED_RECORD_KIND:
            if self.record_kind not in _PENDING_KINDS:
                raise ValueError(
                    "unsupported-record issue requires a pending record kind"
                )
        elif self.record_kind is not RecordKind.CHALLENGE:
            raise ValueError("challenge feature issue requires a challenge record")
        _require_record_ref(self.ref)


def _issue_key(issue: CompilationIssue) -> tuple[object, ...]:
    if issue.code is CompilationCode.UNSUPPORTED_RECORD_KIND:
        return (
            1,
            _PENDING_KIND_ORDER.get(
                issue.record_kind,
                len(_PENDING_KIND_ORDER),
            ),
            issue.ref.id,
            issue.ref.version,
            issue.code.value,
        )
    return (
        0,
        issue.ref.id,
        issue.ref.version,
        _CHALLENGE_CODE_RANK[issue.code],
    )


class PackageCompilationError(ValueError):
    """Aggregate feature-boundary failure with no partial compilation."""

    issues: tuple[CompilationIssue, ...]

    def __init__(self, issues: tuple[CompilationIssue, ...]) -> None:
        if isinstance(issues, (str, bytes)):
            raise TypeError("compilation issues must be a collection")
        frozen = tuple(issues)
        if not frozen or any(type(issue) is not CompilationIssue for issue in frozen):
            raise ValueError("PackageCompilationError requires typed issues")
        canonical = tuple(sorted(set(frozen), key=_issue_key))
        self.issues = canonical
        kinds = ", ".join(issue.record_kind.value for issue in canonical)
        super().__init__(f"package uses compiler features not yet implemented: {kinds}")


_COMPILATION_FACTORY = object()


@dataclass(frozen=True, slots=True, init=False)
class Compilation:
    """Factory-only compiled program, contrary relation, and source map."""

    # Exact validated evidence participates in wrapper equality.  Callers that
    # compare semantic compilation across source ordering or metadata changes
    # compare program, contraries, and origins explicitly.
    source: ValidatedPackage = field(repr=False)
    program: GroundProgram
    contraries: tuple[CompiledContrary, ...]
    origins: tuple[ArtifactOrigin, ...]
    _origin_index: Mapping[
        tuple[GroundArtifactKind, str], ArtifactOrigin
    ] = field(compare=False, repr=False)
    __hash__ = None

    def __init__(
        self,
        *,
        source: ValidatedPackage,
        program: GroundProgram,
        contraries: tuple[CompiledContrary, ...],
        origins: tuple[ArtifactOrigin, ...],
        _factory: object | None = None,
    ) -> None:
        if _factory is not _COMPILATION_FACTORY:
            raise TypeError("Compilation is created only by compile_package")
        if type(source) is not ValidatedPackage:
            raise TypeError("source must be an exact ValidatedPackage")
        if type(program) is not GroundProgram:
            raise TypeError("program must be an exact GroundProgram")

        contrary_values = tuple(contraries)
        if any(type(item) is not CompiledContrary for item in contrary_values):
            raise TypeError("contraries must contain exact CompiledContrary values")
        canonical_contraries = tuple(
            sorted(
                contrary_values,
                key=lambda item: (item.source.id, item.source.version),
            )
        )
        if len({item.source for item in canonical_contraries}) != len(
            canonical_contraries
        ):
            raise ValueError("compiled contrary sources must be unique")
        for contrary in canonical_contraries:
            source.resolve(contrary.source, RecordKind.CONTRARY)
            if (
                contrary.first not in program.atoms
                or contrary.second not in program.atoms
            ):
                raise ValueError("compiled contrary endpoints must be ground atoms")

        origin_values = tuple(origins)
        if any(type(item) is not ArtifactOrigin for item in origin_values):
            raise TypeError("origins must contain exact ArtifactOrigin values")
        canonical_origins = tuple(sorted(origin_values, key=_origin_key))
        origin_index: dict[
            tuple[GroundArtifactKind, str], ArtifactOrigin
        ] = {}
        for origin in canonical_origins:
            key = (origin.artifact_kind, origin.artifact_ref)
            if key in origin_index:
                raise ValueError("every ground artifact must have exactly one origin")
            for owner in origin.sources:
                source.resolve(owner.ref, owner.kind)
            origin_index[key] = origin

        expected_keys = {
            (GroundArtifactKind.ATOM, str(atom)) for atom in program.atoms
        } | {
            (GroundArtifactKind.RULE, str(rule.id)) for rule in program.rules
        }
        if set(origin_index) != expected_keys:
            raise ValueError(
                "compiler source map must cover every ground artifact exactly"
            )

        object.__setattr__(self, "source", source)
        object.__setattr__(self, "program", program)
        object.__setattr__(self, "contraries", canonical_contraries)
        object.__setattr__(self, "origins", canonical_origins)
        object.__setattr__(
            self,
            "_origin_index",
            MappingProxyType(origin_index),
        )

    def origin_for(
        self,
        artifact_kind: GroundArtifactKind,
        artifact_ref: str,
    ) -> ArtifactOrigin:
        """Return the exact source-map entry for one compiled artifact."""

        if type(artifact_kind) is not GroundArtifactKind:
            raise TypeError("artifact kind must be an exact GroundArtifactKind")
        if type(artifact_ref) is not str or not artifact_ref:
            raise TypeError("artifact reference must be a non-empty string")
        return self._origin_index[(artifact_kind, artifact_ref)]


class _CompilationBuilder:
    """Single mutation point used while constructing one immutable result."""

    def __init__(self, source: ValidatedPackage) -> None:
        self.source = source
        self.atoms: set[AtomRef] = set()
        self.rules: list[GroundRule] = []
        self.rule_ids: set[RuleRef] = set()
        self.base_live: set[AtomRef] = set()
        self.base_excluded: set[AtomRef] = set()
        self.protected_open: set[AtomRef] = set()
        self.origins: dict[
            tuple[GroundArtifactKind, str], ArtifactOrigin
        ] = {}
        self.contraries: list[CompiledContrary] = []

    @staticmethod
    def _source(kind: RecordKind, ref: RecordRef) -> SourceRecord:
        return SourceRecord(kind=kind, ref=ref)

    def add_atom(
        self,
        atom: AtomRef,
        *,
        role: CompilationRole,
        source_kind: RecordKind,
        source_ref: RecordRef,
    ) -> None:
        if type(atom) is not str or not atom:
            raise AssertionError("compiler created an invalid atom reference")
        key = (GroundArtifactKind.ATOM, str(atom))
        origin = ArtifactOrigin(
            artifact_kind=GroundArtifactKind.ATOM,
            artifact_ref=str(atom),
            role=role,
            sources=(self._source(source_kind, source_ref),),
        )
        previous = self.origins.get(key)
        if previous is not None and previous != origin:
            raise AssertionError("compiler-generated atom identity collision")
        self.atoms.add(atom)
        self.origins[key] = origin

    def add_rule(
        self,
        rule: GroundRule,
        *,
        role: CompilationRole,
        source_kind: RecordKind,
        source_ref: RecordRef,
    ) -> None:
        if rule.id in self.rule_ids:
            raise AssertionError("compiler-generated rule identity collision")
        self.rule_ids.add(rule.id)
        self.rules.append(rule)
        origin = ArtifactOrigin(
            artifact_kind=GroundArtifactKind.RULE,
            artifact_ref=str(rule.id),
            role=role,
            sources=(self._source(source_kind, source_ref),),
        )
        self.origins[(GroundArtifactKind.RULE, str(rule.id))] = origin

    def _place(self, atom: AtomRef, target: set[AtomRef]) -> None:
        if atom not in self.atoms:
            raise AssertionError("compiler placed an atom outside its universe")
        other_sets = (self.base_live, self.base_excluded, self.protected_open)
        if any(
            atom in candidate
            for candidate in other_sets
            if candidate is not target
        ):
            raise AssertionError("compiler created overlapping base partitions")
        target.add(atom)

    def mark_live(self, atom: AtomRef) -> None:
        self._place(atom, self.base_live)

    def mark_excluded(self, atom: AtomRef) -> None:
        self._place(atom, self.base_excluded)

    def mark_open(self, atom: AtomRef) -> None:
        self._place(atom, self.protected_open)

    def add_contrary(self, contrary: ContraryRecord) -> None:
        first_ref, second_ref = sorted((contrary.left, contrary.right))
        self.contraries.append(
            CompiledContrary(
                source=contrary.ref,
                first=_source_atom(first_ref),
                second=_source_atom(second_ref),
                boundary=contrary.boundary,
            )
        )

    def build(self) -> Compilation:
        program = GroundProgram(
            atoms=frozenset(self.atoms),
            rules=tuple(self.rules),
            base_live=frozenset(self.base_live),
            base_excluded=frozenset(self.base_excluded),
            protected_open=frozenset(self.protected_open),
        )
        return Compilation(
            source=self.source,
            program=program,
            contraries=tuple(self.contraries),
            origins=tuple(self.origins.values()),
            _factory=_COMPILATION_FACTORY,
        )


def _challenge_issues(source: ValidatedPackage) -> tuple[CompilationIssue, ...]:
    issues: list[CompilationIssue] = []
    for raw_record in source.records(RecordKind.CHALLENGE):
        record = cast(ChallengeRecord, raw_record)
        code = _DEFERRED_CHALLENGE_CODES.get(record.kind)
        if code is None and record.kind not in _COMPILER_MAPPED_CHALLENGE_KINDS:
            if record.kind not in source.registry.known_challenge_kinds:
                raise AssertionError(
                    "validated package contains an unknown challenge kind"
                )
            code = CompilationCode.CHALLENGE_EFFECT_UNSUPPORTED
        if (
            code is None
            and record.kind in _RULE_TARGET_BLOCKING_KINDS
            and record.target_kind is RecordKind.RULE
        ):
            code = CompilationCode.RULE_TARGET_BLOCKING_UNSUPPORTED
        if code is not None:
            issues.append(
                CompilationIssue(
                    code=code,
                    record_kind=RecordKind.CHALLENGE,
                    ref=record.ref,
                )
            )
    return tuple(sorted(issues, key=_issue_key))


def _compile_source_atoms(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.ATOM):
        record = cast(AtomRecord, raw_record)
        builder.add_atom(
            _source_atom(record.ref),
            role=CompilationRole.SOURCE_ATOM,
            source_kind=RecordKind.ATOM,
            source_ref=record.ref,
        )

    base = builder.source.package.base
    for ref in base.live:
        builder.mark_live(_source_atom(ref))
    for ref in base.excluded:
        builder.mark_excluded(_source_atom(ref))
    for ref in base.open:
        builder.mark_open(_source_atom(ref))


def _compile_certificates(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.CERTIFICATE):
        record = cast(CertificateRecord, raw_record)
        valid = _generated_atom(CompilationRole.CERT_VALID, record.ref)
        failed = _generated_atom(CompilationRole.CERT_FAILED, record.ref)
        opened = _generated_atom(CompilationRole.CERT_OPEN, record.ref)
        for atom, role in (
            (valid, CompilationRole.CERT_VALID),
            (failed, CompilationRole.CERT_FAILED),
            (opened, CompilationRole.CERT_OPEN),
        ):
            builder.add_atom(
                atom,
                role=role,
                source_kind=RecordKind.CERTIFICATE,
                source_ref=record.ref,
            )

        if record.result is CheckResult.PASS:
            builder.mark_live(valid)
        elif record.result is CheckResult.FAIL:
            builder.mark_excluded(valid)
            builder.mark_live(failed)
        elif record.result is CheckResult.OPEN:
            builder.mark_open(valid)
            builder.mark_live(opened)
        else:  # pragma: no cover - ValidatedPackage seals this enum.
            raise AssertionError(f"unhandled certificate result: {record.result!r}")


def _compile_closures(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.CLOSURE):
        record = cast(ClosureRecord, raw_record)
        ready = _generated_atom(CompilationRole.CLOSURE_READY, record.ref)
        failed = _generated_atom(CompilationRole.CLOSURE_FAILED, record.ref)
        opened = _generated_atom(CompilationRole.CLOSURE_OPEN, record.ref)
        for atom, role in (
            (ready, CompilationRole.CLOSURE_READY),
            (failed, CompilationRole.CLOSURE_FAILED),
            (opened, CompilationRole.CLOSURE_OPEN),
        ):
            builder.add_atom(
                atom,
                role=role,
                source_kind=RecordKind.CLOSURE,
                source_ref=record.ref,
            )

        if record.result is CheckResult.PASS:
            builder.mark_live(ready)
        elif record.result is CheckResult.FAIL:
            builder.mark_open(ready)
            builder.mark_live(failed)
        elif record.result is CheckResult.OPEN:
            builder.mark_open(ready)
            builder.mark_live(opened)
        else:  # pragma: no cover - ValidatedPackage seals this enum.
            raise AssertionError(f"unhandled closure result: {record.result!r}")


def _compile_contraries(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.CONTRARY):
        builder.add_contrary(cast(ContraryRecord, raw_record))


def _compile_faces(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.FACE):
        record = cast(FaceRecord, raw_record)
        face = _generated_atom(CompilationRole.FACE, record.ref)
        has_open_challenge = _generated_atom(
            CompilationRole.HAS_OPEN_CHALLENGE,
            record.ref,
        )
        clear = _generated_atom(CompilationRole.CLEAR, record.ref)
        for atom, role in (
            (face, CompilationRole.FACE),
            (has_open_challenge, CompilationRole.HAS_OPEN_CHALLENGE),
            (clear, CompilationRole.CLEAR),
        ):
            builder.add_atom(
                atom,
                role=role,
                source_kind=RecordKind.FACE,
                source_ref=record.ref,
            )
        builder.mark_live(face)

        clear_face = GroundRule(
            id=_generated_rule(CompilationRole.CLEAR_FACE, record.ref),
            head=clear,
            positive=frozenset(
                {
                    face,
                    _generated_atom(
                        CompilationRole.CLOSURE_READY,
                        record.blocker_closure,
                    ),
                }
            ),
            negative=frozenset({has_open_challenge}),
        )
        builder.add_rule(
            clear_face,
            role=CompilationRole.CLEAR_FACE,
            source_kind=RecordKind.FACE,
            source_ref=record.ref,
        )


def _compile_rules(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.RULE):
        record = cast(RuleRecord, raw_record)
        live_case = _generated_atom(CompilationRole.LIVE_CASE, record.ref)
        builder.add_atom(
            live_case,
            role=CompilationRole.LIVE_CASE,
            source_kind=RecordKind.RULE,
            source_ref=record.ref,
        )

        positive = {
            _generated_atom(CompilationRole.CERT_VALID, record.certificate),
            *(_source_atom(ref) for ref in record.positive),
            *(
                _generated_atom(CompilationRole.CLEAR, ref)
                for ref in record.faces
            ),
            *(
                _generated_atom(CompilationRole.CLOSURE_READY, literal.closure)
                for literal in record.negative
            ),
        }
        negative = {_source_atom(literal.atom) for literal in record.negative}

        case_rule = GroundRule(
            id=_generated_rule(CompilationRole.RULE_CASE, record.ref),
            head=live_case,
            positive=frozenset(positive),
            negative=frozenset(negative),
        )
        builder.add_rule(
            case_rule,
            role=CompilationRole.RULE_CASE,
            source_kind=RecordKind.RULE,
            source_ref=record.ref,
        )

        head_bridge = GroundRule(
            id=_generated_rule(CompilationRole.HEAD_BRIDGE, record.ref),
            head=_source_atom(record.head),
            positive=frozenset({live_case}),
        )
        builder.add_rule(
            head_bridge,
            role=CompilationRole.HEAD_BRIDGE,
            source_kind=RecordKind.RULE,
            source_ref=record.ref,
        )


def _compile_challenges(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.CHALLENGE):
        record = cast(ChallengeRecord, raw_record)
        challenge_case = _generated_atom(
            CompilationRole.CHALLENGE_CASE,
            record.ref,
        )
        discharged = _generated_atom(
            CompilationRole.DISCHARGED,
            record.ref,
        )
        open_challenge = _generated_atom(
            CompilationRole.OPEN_CHALLENGE,
            record.ref,
        )
        for atom, role in (
            (challenge_case, CompilationRole.CHALLENGE_CASE),
            (discharged, CompilationRole.DISCHARGED),
            (open_challenge, CompilationRole.OPEN_CHALLENGE),
        ):
            builder.add_atom(
                atom,
                role=role,
                source_kind=RecordKind.CHALLENGE,
                source_ref=record.ref,
            )

        builder.add_rule(
            GroundRule(
                id=_generated_rule(
                    CompilationRole.CHALLENGE_CASE_RULE,
                    record.ref,
                ),
                head=challenge_case,
                positive=frozenset(
                    {
                        _generated_atom(
                            CompilationRole.CERT_VALID,
                            record.certificate,
                        )
                    }
                ),
            ),
            role=CompilationRole.CHALLENGE_CASE_RULE,
            source_kind=RecordKind.CHALLENGE,
            source_ref=record.ref,
        )
        builder.add_rule(
            GroundRule(
                id=_generated_rule(
                    CompilationRole.OPEN_CHALLENGE_RULE,
                    record.ref,
                ),
                head=open_challenge,
                positive=frozenset(
                    {
                        challenge_case,
                        _generated_atom(
                            CompilationRole.CLOSURE_READY,
                            record.discharge_closure,
                        ),
                    }
                ),
                negative=frozenset({discharged}),
            ),
            role=CompilationRole.OPEN_CHALLENGE_RULE,
            source_kind=RecordKind.CHALLENGE,
            source_ref=record.ref,
        )

        if record.kind == "rebut":
            if record.contrary_atom is None:  # pragma: no cover - validated.
                raise AssertionError("validated rebut has no contrary atom")
            effect_head = _source_atom(record.contrary_atom)
            effect_role = CompilationRole.REBUT_EFFECT
        elif record.kind in _FACE_BLOCKING_CHALLENGE_KINDS:
            effect_head = _generated_atom(
                CompilationRole.HAS_OPEN_CHALLENGE,
                record.target,
            )
            effect_role = CompilationRole.FACE_BLOCK_EFFECT
        else:  # pragma: no cover - preflight rejects every other kind.
            raise AssertionError(f"unhandled challenge kind: {record.kind!r}")

        builder.add_rule(
            GroundRule(
                id=_generated_rule(effect_role, record.ref),
                head=effect_head,
                positive=frozenset({open_challenge}),
            ),
            role=effect_role,
            source_kind=RecordKind.CHALLENGE,
            source_ref=record.ref,
        )


def _compile_discharges(builder: _CompilationBuilder) -> None:
    for raw_record in builder.source.records(RecordKind.DISCHARGE):
        record = cast(DischargeRecord, raw_record)
        challenge = cast(
            ChallengeRecord,
            builder.source.resolve(record.challenge, RecordKind.CHALLENGE),
        )
        type_match = _generated_atom(
            CompilationRole.TYPE_MATCH,
            record.ref,
        )
        discharge_case = _generated_atom(
            CompilationRole.DISCHARGE_CASE,
            record.ref,
        )
        for atom, role in (
            (type_match, CompilationRole.TYPE_MATCH),
            (discharge_case, CompilationRole.DISCHARGE_CASE),
        ):
            builder.add_atom(
                atom,
                role=role,
                source_kind=RecordKind.DISCHARGE,
                source_ref=record.ref,
            )

        compatible = builder.source.registry.is_discharge_compatible(
            challenge_kind=challenge.kind,
            discharge_kind=record.kind,
        )
        if compatible:
            builder.mark_live(type_match)
        else:
            builder.mark_excluded(type_match)

        builder.add_rule(
            GroundRule(
                id=_generated_rule(
                    CompilationRole.DISCHARGE_CASE_RULE,
                    record.ref,
                ),
                head=discharge_case,
                positive=frozenset(
                    {
                        _generated_atom(
                            CompilationRole.CERT_VALID,
                            record.certificate,
                        ),
                        type_match,
                    }
                ),
            ),
            role=CompilationRole.DISCHARGE_CASE_RULE,
            source_kind=RecordKind.DISCHARGE,
            source_ref=record.ref,
        )
        builder.add_rule(
            GroundRule(
                id=_generated_rule(
                    CompilationRole.DISCHARGED_BRIDGE,
                    record.ref,
                ),
                head=_generated_atom(
                    CompilationRole.DISCHARGED,
                    challenge.ref,
                ),
                positive=frozenset({discharge_case}),
            ),
            role=CompilationRole.DISCHARGED_BRIDGE,
            source_kind=RecordKind.DISCHARGE,
            source_ref=record.ref,
        )


def compile_package(source: ValidatedPackage) -> Compilation:
    """Compile one validated package through the sole deterministic path.

    Unsupported challenge effects are reported before builder construction.
    A successful result is immutable and contains no evaluation.
    """

    if type(source) is not ValidatedPackage:
        raise TypeError("source must be an exact ValidatedPackage")

    issues = _challenge_issues(source)
    if issues:
        raise PackageCompilationError(issues)

    builder = _CompilationBuilder(source)
    _compile_source_atoms(builder)
    _compile_certificates(builder)
    _compile_closures(builder)
    _compile_faces(builder)
    _compile_contraries(builder)
    _compile_rules(builder)
    _compile_challenges(builder)
    _compile_discharges(builder)
    return builder.build()


__all__ = [
    "ArtifactOrigin",
    "Compilation",
    "CompilationCode",
    "CompilationIssue",
    "CompilationRole",
    "CompiledContrary",
    "GroundArtifactKind",
    "PackageCompilationError",
    "SourceRecord",
    "compile_package",
]
