"""Immutable, unvalidated records for a PFF Core package.

This module owns only the in-memory shape of a package.  It deliberately does
not resolve references, interpret registry vocabulary, enforce semantic ID or
version rules, or assign evaluation status.  Those are validation and compiler
responsibilities in later layers.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeVar, cast


class RecordKind(StrEnum):
    """Kinds of versioned records materialised directly in a package."""

    ATOM = "atom"
    RULE = "rule"
    FACE = "face"
    CERTIFICATE = "certificate"
    CLOSURE = "closure"
    CONTRARY = "contrary"
    CHALLENGE = "challenge"
    DISCHARGE = "discharge"


class CheckResult(StrEnum):
    """A supplied checker outcome, not an engine status or truth value."""

    PASS = "pass"
    FAIL = "fail"
    OPEN = "open"


def _require_string(value: object, *, field_name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")


def _require_integer(value: object, *, field_name: str) -> None:
    # bool is an int subclass but is not a structurally valid version.
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")


@dataclass(frozen=True, slots=True, order=True)
class RecordRef:
    """An exact reference to one package record ID and version."""

    id: str
    version: int

    def __post_init__(self) -> None:
        _require_string(self.id, field_name="record reference id")
        _require_integer(self.version, field_name="record reference version")


@dataclass(frozen=True, slots=True, order=True)
class VersionToken:
    """An opaque external version identity that is not a package reference."""

    id: str
    version: int

    def __post_init__(self) -> None:
        _require_string(self.id, field_name="version token id")
        _require_integer(self.version, field_name="version token version")


class _FrozenMapping(Mapping[str, object]):
    """A small, recursively immutable mapping preserving source key order."""

    __slots__ = ("_items",)

    def __init__(self, items: tuple[tuple[str, object], ...]) -> None:
        object.__setattr__(self, "_items", items)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("FrozenMapping is immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("FrozenMapping is immutable")

    def __getitem__(self, key: str) -> object:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __hash__(self) -> int:
        return hash(frozenset(self._items))

    def __repr__(self) -> str:
        body = ", ".join(f"{key!r}: {value!r}" for key, value in self._items)
        return f"FrozenMapping({{{body}}})"


def _freeze_value(value: object, *, field_name: str) -> object:
    """Copy supported nested container input into recursively immutable data."""

    if value is None or type(value) in {bool, int, float, str}:
        return value
    if type(value) in {RecordRef, VersionToken}:
        # Typed selectors bind exact package references and opaque external
        # version tokens without falling back to an id@version string grammar.
        return value

    if isinstance(value, Mapping):
        items: list[tuple[str, object]] = []
        for key, member in value.items():
            _require_string(key, field_name=f"{field_name} key")
            items.append(
                (
                    key,
                    _freeze_value(member, field_name=f"{field_name}.{key}"),
                )
            )
        return _FrozenMapping(tuple(items))

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_value(member, field_name=f"{field_name} member")
            for member in value
        )

    if isinstance(value, (set, frozenset)):
        frozen_members = tuple(
            _freeze_value(member, field_name=f"{field_name} member")
            for member in value
        )
        try:
            return frozenset(frozen_members)
        except TypeError as exc:  # pragma: no cover - defensive path detail
            raise TypeError(f"{field_name} contains an unhashable set member") from exc

    if isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"{field_name} contains unsupported byte or text data")

    raise TypeError(
        f"{field_name} contains unsupported value type {type(value).__name__}"
    )


def _freeze_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return cast(Mapping[str, object], _freeze_value(value, field_name=field_name))


_MemberT = TypeVar("_MemberT")


def _ordered_members(
    value: object,
    *,
    field_name: str,
    member_type: type[_MemberT],
) -> tuple[_MemberT, ...]:
    """Copy an ordered list/tuple while rejecting iterable lookalikes."""

    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, (list, tuple)
    ):
        raise TypeError(f"{field_name} must be a list or tuple")
    members = tuple(value)
    for member in members:
        if type(member) is not member_type:
            raise TypeError(
                f"{field_name} members must be exact {member_type.__name__} values"
            )
    return cast(tuple[_MemberT, ...], members)


def _set_members(
    value: object,
    *,
    field_name: str,
    member_type: type[_MemberT],
) -> frozenset[_MemberT]:
    """Copy a set-valued field without hiding duplicate raw members."""

    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, (list, tuple, set, frozenset)
    ):
        raise TypeError(f"{field_name} must be a list, tuple, set, or frozenset")
    members = tuple(value)
    for member in members:
        if type(member) is not member_type:
            raise TypeError(
                f"{field_name} members must be exact {member_type.__name__} values"
            )
    if len(frozenset(members)) != len(members):
        raise ValueError(f"{field_name} contains duplicate members")
    return frozenset(members)


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionedRecord:
    """Common structural identity for a package semantic record."""

    id: str
    version: int

    def __post_init__(self) -> None:
        _require_string(self.id, field_name="record id")
        _require_integer(self.version, field_name="record version")

    @property
    def ref(self) -> RecordRef:
        return RecordRef(self.id, self.version)


@dataclass(frozen=True, slots=True, kw_only=True)
class PackageHeader:
    schema: str
    package_id: str
    cut_id: str
    frame_id: str
    registry_id: str
    parent_package_hash: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "schema",
            "package_id",
            "cut_id",
            "frame_id",
            "registry_id",
        ):
            _require_string(getattr(self, field_name), field_name=field_name)
        if self.parent_package_hash is not None:
            _require_string(
                self.parent_package_hash,
                field_name="parent_package_hash",
            )
        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata, field_name="metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class AtomRecord(VersionedRecord):
    predicate: str
    args: tuple[str, ...]
    frame: str
    grade: str | None
    primitive: bool

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        _require_string(self.predicate, field_name="atom predicate")
        args = _ordered_members(
            self.args,
            field_name="atom args",
            member_type=str,
        )
        _require_string(self.frame, field_name="atom frame")
        if self.grade is not None:
            _require_string(self.grade, field_name="atom grade")
        if type(self.primitive) is not bool:
            raise TypeError("atom primitive must be a boolean")
        object.__setattr__(self, "args", args)


@dataclass(frozen=True, slots=True, kw_only=True)
class ClosedNegativeLiteral:
    atom: RecordRef
    closure: RecordRef

    def __post_init__(self) -> None:
        if type(self.atom) is not RecordRef:
            raise TypeError("closed-negative atom must be an exact RecordRef")
        if type(self.closure) is not RecordRef:
            raise TypeError("closed-negative closure must be an exact RecordRef")


@dataclass(frozen=True, slots=True, kw_only=True)
class RuleRecord(VersionedRecord):
    head: RecordRef
    positive: frozenset[RecordRef] = field(default_factory=frozenset)
    negative: frozenset[ClosedNegativeLiteral] = field(default_factory=frozenset)
    certificate: RecordRef
    faces: frozenset[RecordRef] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        if type(self.head) is not RecordRef:
            raise TypeError("rule head must be an exact RecordRef")
        if type(self.certificate) is not RecordRef:
            raise TypeError("rule certificate must be an exact RecordRef")
        object.__setattr__(
            self,
            "positive",
            _set_members(
                self.positive,
                field_name="rule positive",
                member_type=RecordRef,
            ),
        )
        object.__setattr__(
            self,
            "negative",
            _set_members(
                self.negative,
                field_name="rule negative",
                member_type=ClosedNegativeLiteral,
            ),
        )
        object.__setattr__(
            self,
            "faces",
            _set_members(
                self.faces,
                field_name="rule faces",
                member_type=RecordRef,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class FaceRecord(VersionedRecord):
    owner_rule: RecordRef
    kind: str
    boundary: str
    carrier: str
    blocker_closure: RecordRef
    depends_on_version: VersionToken | None = None

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        if type(self.owner_rule) is not RecordRef:
            raise TypeError("face owner_rule must be an exact RecordRef")
        for field_name in ("kind", "boundary", "carrier"):
            _require_string(getattr(self, field_name), field_name=f"face {field_name}")
        if type(self.blocker_closure) is not RecordRef:
            raise TypeError("face blocker_closure must be an exact RecordRef")
        if (
            self.depends_on_version is not None
            and type(self.depends_on_version) is not VersionToken
        ):
            raise TypeError(
                "face depends_on_version must be an exact VersionToken or None"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class CertificateRecord(VersionedRecord):
    checker: str
    subject: RecordRef
    result: CheckResult
    payload_hash: str
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        _require_string(self.checker, field_name="certificate checker")
        if type(self.subject) is not RecordRef:
            raise TypeError("certificate subject must be an exact RecordRef")
        if type(self.result) is not CheckResult:
            raise TypeError("certificate result must be an exact CheckResult")
        _require_string(self.payload_hash, field_name="certificate payload_hash")
        object.__setattr__(
            self,
            "details",
            _freeze_mapping(self.details, field_name="certificate details"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Selector:
    record_type: RecordKind
    where: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.record_type) is not RecordKind:
            raise TypeError("selector record_type must be an exact RecordKind")
        object.__setattr__(
            self,
            "where",
            _freeze_mapping(self.where, field_name="selector where"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ClosureRecord(VersionedRecord):
    checker: str
    result: CheckResult
    cut_id: str
    frame: str
    selector: Selector
    members: frozenset[RecordRef] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        _require_string(self.checker, field_name="closure checker")
        if type(self.result) is not CheckResult:
            raise TypeError("closure result must be an exact CheckResult")
        _require_string(self.cut_id, field_name="closure cut_id")
        _require_string(self.frame, field_name="closure frame")
        if type(self.selector) is not Selector:
            raise TypeError("closure selector must be an exact Selector")
        object.__setattr__(
            self,
            "members",
            _set_members(
                self.members,
                field_name="closure members",
                member_type=RecordRef,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ContraryRecord(VersionedRecord):
    """An explicit contrary pair; the global versioned-record rule applies."""

    left: RecordRef
    right: RecordRef
    boundary: str

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        if type(self.left) is not RecordRef or type(self.right) is not RecordRef:
            raise TypeError("contrary endpoints must be exact RecordRef values")
        _require_string(self.boundary, field_name="contrary boundary")


@dataclass(frozen=True, slots=True, kw_only=True)
class ChallengeRecord(VersionedRecord):
    kind: str
    target_kind: RecordKind
    target: RecordRef
    certificate: RecordRef
    discharge_closure: RecordRef
    contrary_atom: RecordRef | None = None
    problem_face_atom: RecordRef | None = None

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        _require_string(self.kind, field_name="challenge kind")
        if type(self.target_kind) is not RecordKind:
            raise TypeError("challenge target_kind must be an exact RecordKind")
        for field_name in ("target", "certificate", "discharge_closure"):
            if type(getattr(self, field_name)) is not RecordRef:
                raise TypeError(f"challenge {field_name} must be an exact RecordRef")
        for field_name in ("contrary_atom", "problem_face_atom"):
            value = getattr(self, field_name)
            if value is not None and type(value) is not RecordRef:
                raise TypeError(
                    f"challenge {field_name} must be an exact RecordRef or None"
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class DischargeRecord(VersionedRecord):
    challenge: RecordRef
    kind: str
    certificate: RecordRef

    def __post_init__(self) -> None:
        VersionedRecord.__post_init__(self)
        if type(self.challenge) is not RecordRef:
            raise TypeError("discharge challenge must be an exact RecordRef")
        _require_string(self.kind, field_name="discharge kind")
        if type(self.certificate) is not RecordRef:
            raise TypeError("discharge certificate must be an exact RecordRef")


@dataclass(frozen=True, slots=True, kw_only=True)
class BasePartition:
    live: frozenset[RecordRef] = field(default_factory=frozenset)
    excluded: frozenset[RecordRef] = field(default_factory=frozenset)
    open: frozenset[RecordRef] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        for field_name in ("live", "excluded", "open"):
            object.__setattr__(
                self,
                field_name,
                _set_members(
                    getattr(self, field_name),
                    field_name=f"base {field_name}",
                    member_type=RecordRef,
                ),
            )


Record = (
    AtomRecord
    | RuleRecord
    | FaceRecord
    | CertificateRecord
    | ClosureRecord
    | ContraryRecord
    | ChallengeRecord
    | DischargeRecord
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Package:
    """One immutable, not-yet-validated finite PFF package."""

    header: PackageHeader
    atoms: tuple[AtomRecord, ...] = ()
    rules: tuple[RuleRecord, ...] = ()
    faces: tuple[FaceRecord, ...] = ()
    certificates: tuple[CertificateRecord, ...] = ()
    closures: tuple[ClosureRecord, ...] = ()
    contraries: tuple[ContraryRecord, ...] = ()
    challenges: tuple[ChallengeRecord, ...] = ()
    discharges: tuple[DischargeRecord, ...] = ()
    base: BasePartition = field(default_factory=BasePartition)

    def __post_init__(self) -> None:
        if type(self.header) is not PackageHeader:
            raise TypeError("package header must be an exact PackageHeader")
        if type(self.base) is not BasePartition:
            raise TypeError("package base must be an exact BasePartition")

        collection_types: tuple[tuple[str, type[VersionedRecord]], ...] = (
            ("atoms", AtomRecord),
            ("rules", RuleRecord),
            ("faces", FaceRecord),
            ("certificates", CertificateRecord),
            ("closures", ClosureRecord),
            ("contraries", ContraryRecord),
            ("challenges", ChallengeRecord),
            ("discharges", DischargeRecord),
        )
        for field_name, member_type in collection_types:
            object.__setattr__(
                self,
                field_name,
                _ordered_members(
                    getattr(self, field_name),
                    field_name=f"package {field_name}",
                    member_type=member_type,
                ),
            )

    def record_groups(self) -> tuple[tuple[RecordKind, tuple[Record, ...]], ...]:
        """Return record groups in one stable schema order."""

        return (
            (RecordKind.ATOM, cast(tuple[Record, ...], self.atoms)),
            (RecordKind.RULE, cast(tuple[Record, ...], self.rules)),
            (RecordKind.FACE, cast(tuple[Record, ...], self.faces)),
            (
                RecordKind.CERTIFICATE,
                cast(tuple[Record, ...], self.certificates),
            ),
            (RecordKind.CLOSURE, cast(tuple[Record, ...], self.closures)),
            (RecordKind.CONTRARY, cast(tuple[Record, ...], self.contraries)),
            (RecordKind.CHALLENGE, cast(tuple[Record, ...], self.challenges)),
            (RecordKind.DISCHARGE, cast(tuple[Record, ...], self.discharges)),
        )

    def records(self, kind: RecordKind) -> tuple[Record, ...]:
        """Return the preserved tuple for one exact record kind."""

        if type(kind) is not RecordKind:
            raise TypeError("kind must be an exact RecordKind")
        for candidate, records in self.record_groups():
            if candidate is kind:
                return records
        raise AssertionError(f"unhandled record kind: {kind!r}")

    def iter_records(self) -> Iterator[tuple[RecordKind, Record]]:
        """Iterate records deterministically by schema group then tuple order."""

        for kind, records in self.record_groups():
            for record in records:
                yield kind, record


__all__ = [
    "AtomRecord",
    "BasePartition",
    "CertificateRecord",
    "ChallengeRecord",
    "CheckResult",
    "ClosedNegativeLiteral",
    "ClosureRecord",
    "ContraryRecord",
    "DischargeRecord",
    "FaceRecord",
    "Package",
    "PackageHeader",
    "Record",
    "RecordKind",
    "RecordRef",
    "RuleRecord",
    "Selector",
    "VersionToken",
    "VersionedRecord",
]
