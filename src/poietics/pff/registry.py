"""Immutable, code-owned vocabulary and policy for PFF package validation.

The registry is deliberately declarative.  It contains no manifest loader,
provider adapter, checker callback, compiler hook, or evaluator dependency.
Every policy decision exposed here is a deterministic operation over supplied
values and immutable registry data.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import TypeVar

from .model import RecordKind, RecordRef


class RegistryDefinitionErrorCode(StrEnum):
    """Machine-readable failures at the code-owned registry boundary."""

    INVALID_ID = "invalid_id"
    INVALID_VERSION = "invalid_version"
    INVALID_COLLECTION = "invalid_collection"
    INVALID_MEMBER = "invalid_member"
    DUPLICATE_ID = "duplicate_id"
    DUPLICATE_REGISTRY_ID = "duplicate_registry_id"
    UNKNOWN_ARGUMENT_TYPE = "unknown_argument_type"
    UNKNOWN_FRAME_POLICY = "unknown_frame_policy"
    UNKNOWN_CONTRARY_POLICY = "unknown_contrary_policy"
    UNKNOWN_CHECKER_CONTRACT = "unknown_checker_contract"
    UNKNOWN_FACE_KIND = "unknown_face_kind"
    UNKNOWN_CHALLENGE_KIND = "unknown_challenge_kind"
    UNKNOWN_DISCHARGE_KIND = "unknown_discharge_kind"
    UNKNOWN_RULE_SCHEMA = "unknown_rule_schema"
    INCOHERENT_CONTRACT = "incoherent_contract"


class RegistryDefinitionError(ValueError):
    """A deterministic registry-definition failure with typed evidence."""

    code: RegistryDefinitionErrorCode
    location: str
    identifiers: tuple[str, ...]

    def __init__(
        self,
        code: RegistryDefinitionErrorCode,
        *,
        location: str,
        identifiers: Iterable[object] = (),
    ) -> None:
        self.code = code
        self.location = location
        self.identifiers = tuple(sorted({str(value) for value in identifiers}))
        suffix = f" identifiers={self.identifiers!r}" if self.identifiers else ""
        super().__init__(f"{code.value} at {location}{suffix}")


def _fail(
    code: RegistryDefinitionErrorCode,
    *,
    location: str,
    identifiers: Iterable[object] = (),
) -> None:
    raise RegistryDefinitionError(
        code,
        location=location,
        identifiers=identifiers,
    )


def _require_id(value: object, *, location: str) -> str:
    if type(value) is not str or not value:
        _fail(RegistryDefinitionErrorCode.INVALID_ID, location=location)
    return value


def _require_version(value: object, *, location: str) -> int:
    if type(value) is not int or value <= 0:
        _fail(RegistryDefinitionErrorCode.INVALID_VERSION, location=location)
    return value


def _collection(value: object, *, location: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        _fail(RegistryDefinitionErrorCode.INVALID_COLLECTION, location=location)
    return tuple(value)


def _freeze_string_set(value: object, *, location: str) -> frozenset[str]:
    members = _collection(value, location=location)
    for member in members:
        _require_id(member, location=f"{location}.member")
    frozen = frozenset(members)
    if len(frozen) != len(members):
        _fail(
            RegistryDefinitionErrorCode.DUPLICATE_ID,
            location=location,
            identifiers=members,
        )
    return frozen


def _freeze_string_tuple(value: object, *, location: str) -> tuple[str, ...]:
    members = _collection(value, location=location)
    for member in members:
        _require_id(member, location=f"{location}.member")
    return tuple(members)  # type: ignore[return-value]


_EnumT = TypeVar("_EnumT", bound=StrEnum)


def _freeze_enum_set(
    value: object,
    *,
    location: str,
    member_type: type[_EnumT],
) -> frozenset[_EnumT]:
    members = _collection(value, location=location)
    if any(type(member) is not member_type for member in members):
        _fail(RegistryDefinitionErrorCode.INVALID_MEMBER, location=location)
    frozen = frozenset(members)
    if len(frozen) != len(members):
        _fail(
            RegistryDefinitionErrorCode.DUPLICATE_ID,
            location=location,
            identifiers=members,
        )
    return frozen  # type: ignore[return-value]


_DefinitionT = TypeVar("_DefinitionT")


def _freeze_definitions(
    value: object,
    *,
    location: str,
    member_type: type[_DefinitionT],
    id_attribute: str,
) -> tuple[_DefinitionT, ...]:
    members = _collection(value, location=location)
    if any(type(member) is not member_type for member in members):
        _fail(RegistryDefinitionErrorCode.INVALID_MEMBER, location=location)

    identifiers = tuple(str(getattr(member, id_attribute)) for member in members)
    if len(set(identifiers)) != len(identifiers):
        _fail(
            RegistryDefinitionErrorCode.DUPLICATE_ID,
            location=location,
            identifiers=identifiers,
        )
    paired = zip(identifiers, members, strict=True)
    return tuple(member for _, member in sorted(paired, key=lambda pair: pair[0]))


class ComputabilityClass(StrEnum):
    FIN = "FIN"
    CLOSE = "CLOSE"
    CERT = "CERT"
    SCHEMA = "SCHEMA"


class GradePolicy(StrEnum):
    FORBIDDEN = "forbidden"
    OPTIONAL = "optional"
    REQUIRED = "required"

    def accepts(self, grade: object) -> bool:
        valid_grade = type(grade) is str and grade in PFF_GRADES
        if self is GradePolicy.FORBIDDEN:
            return grade is None
        if self is GradePolicy.OPTIONAL:
            return grade is None or valid_grade
        return valid_grade


PFF_GRADES = frozenset({"h", "rho", "Phi"})


@dataclass(frozen=True, slots=True, kw_only=True)
class ArgumentTypeContract:
    """A local nominal string contract, optionally constrained by a prefix."""

    argument_type_id: str
    version: int
    required_prefix: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.argument_type_id, location="argument_type.argument_type_id")
        _require_version(self.version, location=f"argument_type:{self.argument_type_id}.version")
        if self.required_prefix is not None:
            _require_id(
                self.required_prefix,
                location=f"argument_type:{self.argument_type_id}.required_prefix",
            )

    def accepts(self, value: object) -> bool:
        if type(value) is not str or not value:
            return False
        return self.required_prefix is None or value.startswith(self.required_prefix)


class FramePolicyMode(StrEnum):
    EXACT_PACKAGE = "exact_package"
    NONEMPTY = "nonempty"


@dataclass(frozen=True, slots=True, kw_only=True)
class FramePolicy:
    frame_policy_id: str
    version: int
    mode: FramePolicyMode

    def __post_init__(self) -> None:
        _require_id(self.frame_policy_id, location="frame_policy.frame_policy_id")
        _require_version(self.version, location=f"frame_policy:{self.frame_policy_id}.version")
        if type(self.mode) is not FramePolicyMode:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"frame_policy:{self.frame_policy_id}.mode",
            )

    def accepts(self, frame: object, *, package_frame: object) -> bool:
        if type(frame) is not str or not frame:
            return False
        if self.mode is FramePolicyMode.NONEMPTY:
            return True
        return type(package_frame) is str and bool(package_frame) and frame == package_frame


class ContraryPolicyMode(StrEnum):
    FORBIDDEN = "forbidden"
    STABLE_COMPARISON_BOUNDARY = "stable_comparison_boundary"


@dataclass(frozen=True, slots=True, kw_only=True)
class ContraryPolicy:
    """A deterministic contrary comparison policy with no user callback."""

    contrary_policy_id: str
    version: int
    mode: ContraryPolicyMode
    comparison_boundary: str | None = None
    comparison_arg_positions: tuple[int, ...] = ()
    include_frame: bool = False

    def __post_init__(self) -> None:
        _require_id(self.contrary_policy_id, location="contrary_policy.contrary_policy_id")
        _require_version(
            self.version,
            location=f"contrary_policy:{self.contrary_policy_id}.version",
        )
        if type(self.mode) is not ContraryPolicyMode or type(self.include_frame) is not bool:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"contrary_policy:{self.contrary_policy_id}",
            )

        positions = _collection(
            self.comparison_arg_positions,
            location=f"contrary_policy:{self.contrary_policy_id}.comparison_arg_positions",
        )
        if any(type(position) is not int or position < 0 for position in positions):
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"contrary_policy:{self.contrary_policy_id}.comparison_arg_positions",
            )
        if len(set(positions)) != len(positions):
            _fail(
                RegistryDefinitionErrorCode.DUPLICATE_ID,
                location=f"contrary_policy:{self.contrary_policy_id}.comparison_arg_positions",
                identifiers=positions,
            )
        object.__setattr__(self, "comparison_arg_positions", tuple(positions))

        if self.mode is ContraryPolicyMode.FORBIDDEN:
            if self.comparison_boundary is not None or positions or self.include_frame:
                _fail(
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                    location=f"contrary_policy:{self.contrary_policy_id}",
                )
        elif self.comparison_boundary is None:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"contrary_policy:{self.contrary_policy_id}.comparison_boundary",
            )
        else:
            _require_id(
                self.comparison_boundary,
                location=f"contrary_policy:{self.contrary_policy_id}.comparison_boundary",
            )

    def accepts_boundary(self, boundary: object) -> bool:
        return (
            self.mode is ContraryPolicyMode.STABLE_COMPARISON_BOUNDARY
            and type(boundary) is str
            and boundary == self.comparison_boundary
        )

    def comparison_key(
        self,
        *,
        args: tuple[str, ...],
        frame: str,
    ) -> tuple[object, ...] | None:
        if self.mode is ContraryPolicyMode.FORBIDDEN:
            return None
        if any(position >= len(args) for position in self.comparison_arg_positions):
            return None
        selected = tuple(args[position] for position in self.comparison_arg_positions)
        frame_component: tuple[object, ...] = (frame,) if self.include_frame else ()
        return (self.comparison_boundary, *frame_component, *selected)


class CheckerUse(StrEnum):
    CERTIFICATE = "certificate"
    CLOSURE = "closure"


class LocalClosureSemantics(StrEnum):
    """Provider-free closure semantics implemented inside the admission core."""

    NONE = "none"
    MATERIALISED_SELECTOR_V1 = "materialised_selector_v1"


MATERIALISED_SELECTOR_V1_ID = "materialised-selector/v1"


class CheckerDetailType(StrEnum):
    """Small deterministic value vocabulary for certificate detail fields."""

    NONEMPTY_STRING = "nonempty_string"
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    RECORD_REF = "record_ref"

    def accepts(self, value: object) -> bool:
        if self is CheckerDetailType.NONEMPTY_STRING:
            return type(value) is str and bool(value)
        if self is CheckerDetailType.STRING:
            return type(value) is str
        if self is CheckerDetailType.INTEGER:
            return type(value) is int
        if self is CheckerDetailType.BOOLEAN:
            return type(value) is bool
        return type(value) is RecordRef


_STRING_FIELD_TYPES = frozenset(
    {CheckerDetailType.STRING, CheckerDetailType.NONEMPTY_STRING}
)
_ALL_RECORD_KINDS = frozenset(RecordKind)
_MaterialisedFieldSpec = tuple[
    frozenset[CheckerDetailType],
    frozenset[RecordKind] | None,
]


def _string_field() -> _MaterialisedFieldSpec:
    return (_STRING_FIELD_TYPES, None)


def _integer_field() -> _MaterialisedFieldSpec:
    return (frozenset({CheckerDetailType.INTEGER}), None)


def _boolean_field() -> _MaterialisedFieldSpec:
    return (frozenset({CheckerDetailType.BOOLEAN}), None)


def _reference_field(*kinds: RecordKind) -> _MaterialisedFieldSpec:
    return (frozenset({CheckerDetailType.RECORD_REF}), frozenset(kinds))


_COMMON_MATERIALISED_FIELDS: dict[str, _MaterialisedFieldSpec] = {
    "id": _string_field(),
    "version": _integer_field(),
}
_MATERIALISED_SELECTOR_FIELDS: Mapping[
    RecordKind,
    Mapping[str, _MaterialisedFieldSpec],
] = MappingProxyType(
    {
        RecordKind.ATOM: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "predicate": _string_field(),
                "frame": _string_field(),
                "grade": _string_field(),
                "primitive": _boolean_field(),
            }
        ),
        RecordKind.RULE: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "head": _reference_field(RecordKind.ATOM),
                "certificate": _reference_field(RecordKind.CERTIFICATE),
            }
        ),
        RecordKind.FACE: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "owner_rule": _reference_field(RecordKind.RULE),
                "kind": _string_field(),
                "boundary": _string_field(),
                "carrier": _string_field(),
                "blocker_closure": _reference_field(RecordKind.CLOSURE),
            }
        ),
        RecordKind.CERTIFICATE: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "checker": _string_field(),
                "subject": (
                    frozenset({CheckerDetailType.RECORD_REF}),
                    _ALL_RECORD_KINDS,
                ),
                "payload_hash": _string_field(),
            }
        ),
        RecordKind.CLOSURE: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "checker": _string_field(),
                "cut_id": _string_field(),
                "frame": _string_field(),
            }
        ),
        RecordKind.CONTRARY: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "left": _reference_field(RecordKind.ATOM),
                "right": _reference_field(RecordKind.ATOM),
                "boundary": _string_field(),
            }
        ),
        RecordKind.CHALLENGE: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "kind": _string_field(),
                "target": _reference_field(
                    RecordKind.ATOM,
                    RecordKind.RULE,
                    RecordKind.FACE,
                ),
                "certificate": _reference_field(RecordKind.CERTIFICATE),
                "discharge_closure": _reference_field(RecordKind.CLOSURE),
                "contrary_atom": _reference_field(RecordKind.ATOM),
                "problem_face_atom": _reference_field(RecordKind.ATOM),
            }
        ),
        RecordKind.DISCHARGE: MappingProxyType(
            {
                **_COMMON_MATERIALISED_FIELDS,
                "challenge": _reference_field(RecordKind.CHALLENGE),
                "kind": _string_field(),
                "certificate": _reference_field(RecordKind.CERTIFICATE),
            }
        ),
    }
)


def _materialised_selector_field_spec(
    record_type: RecordKind,
    field_name: str,
) -> _MaterialisedFieldSpec | None:
    return _MATERIALISED_SELECTOR_FIELDS[record_type].get(field_name)


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckerDetailField:
    """One required checker-detail key and its exact local value shape."""

    key: str
    value_type: CheckerDetailType
    allowed_record_kinds: frozenset[RecordKind] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _require_id(self.key, location="checker_detail.key")
        if type(self.value_type) is not CheckerDetailType:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_detail:{self.key}.value_type",
            )
        allowed_kinds = _freeze_enum_set(
            self.allowed_record_kinds,
            location=f"checker_detail:{self.key}.allowed_record_kinds",
            member_type=RecordKind,
        )
        object.__setattr__(self, "allowed_record_kinds", allowed_kinds)
        if self.value_type is CheckerDetailType.RECORD_REF and not allowed_kinds:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_detail:{self.key}.allowed_record_kinds",
            )
        if self.value_type is not CheckerDetailType.RECORD_REF and allowed_kinds:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_detail:{self.key}.allowed_record_kinds",
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class SelectorFieldContract:
    """One equality field accepted by a closure selector contract."""

    record_type: RecordKind
    field: str
    value_type: CheckerDetailType
    allowed_record_kinds: frozenset[RecordKind] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if type(self.record_type) is not RecordKind:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location="selector_field.record_type",
            )
        _require_id(self.field, location="selector_field.field")
        if type(self.value_type) is not CheckerDetailType:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"selector_field:{self.selector_field_id}.value_type",
            )
        allowed_kinds = _freeze_enum_set(
            self.allowed_record_kinds,
            location=f"selector_field:{self.selector_field_id}.allowed_record_kinds",
            member_type=RecordKind,
        )
        object.__setattr__(self, "allowed_record_kinds", allowed_kinds)
        if self.value_type is CheckerDetailType.RECORD_REF and not allowed_kinds:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"selector_field:{self.selector_field_id}.allowed_record_kinds",
            )
        if self.value_type is not CheckerDetailType.RECORD_REF and allowed_kinds:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"selector_field:{self.selector_field_id}.allowed_record_kinds",
            )

    @property
    def selector_field_id(self) -> str:
        return f"{self.record_type.value}.{self.field}"

    def accepts(self, value: object) -> bool:
        return self.value_type.accepts(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckerContract:
    """Local metadata describing permitted checker records and payload shape."""

    checker_id: str
    version: int
    uses: frozenset[CheckerUse]
    local_closure_semantics: LocalClosureSemantics = LocalClosureSemantics.NONE
    certificate_subject_kinds: frozenset[RecordKind] = field(default_factory=frozenset)
    closure_selector_kinds: frozenset[RecordKind] = field(default_factory=frozenset)
    detail_fields: tuple[CheckerDetailField, ...] = ()
    selector_fields: tuple[SelectorFieldContract, ...] = ()
    closure_frame_policy_id: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.checker_id, location="checker_contract.checker_id")
        _require_version(self.version, location=f"checker_contract:{self.checker_id}.version")
        uses = _freeze_enum_set(
            self.uses,
            location=f"checker_contract:{self.checker_id}.uses",
            member_type=CheckerUse,
        )
        if type(self.local_closure_semantics) is not LocalClosureSemantics:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=(
                    f"checker_contract:{self.checker_id}.local_closure_semantics"
                ),
            )
        declares_materialised_id = self.checker_id == MATERIALISED_SELECTOR_V1_ID
        declares_materialised_semantics = (
            self.local_closure_semantics
            is LocalClosureSemantics.MATERIALISED_SELECTOR_V1
        )
        if (
            declares_materialised_id != declares_materialised_semantics
            or (declares_materialised_semantics and self.version != 1)
        ):
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=(
                    f"checker_contract:{self.checker_id}.local_closure_semantics"
                ),
            )
        subject_kinds = _freeze_enum_set(
            self.certificate_subject_kinds,
            location=f"checker_contract:{self.checker_id}.certificate_subject_kinds",
            member_type=RecordKind,
        )
        selector_kinds = _freeze_enum_set(
            self.closure_selector_kinds,
            location=f"checker_contract:{self.checker_id}.closure_selector_kinds",
            member_type=RecordKind,
        )
        detail_fields = _freeze_definitions(
            self.detail_fields,
            location=f"checker_contract:{self.checker_id}.detail_fields",
            member_type=CheckerDetailField,
            id_attribute="key",
        )
        selector_fields = _freeze_definitions(
            self.selector_fields,
            location=f"checker_contract:{self.checker_id}.selector_fields",
            member_type=SelectorFieldContract,
            id_attribute="selector_field_id",
        )
        object.__setattr__(self, "uses", uses)
        object.__setattr__(self, "certificate_subject_kinds", subject_kinds)
        object.__setattr__(self, "closure_selector_kinds", selector_kinds)
        object.__setattr__(self, "detail_fields", detail_fields)
        object.__setattr__(self, "selector_fields", selector_fields)

        if not uses:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_contract:{self.checker_id}.uses",
            )
        if (
            self.local_closure_semantics is not LocalClosureSemantics.NONE
            and CheckerUse.CLOSURE not in uses
        ):
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=(
                    f"checker_contract:{self.checker_id}.local_closure_semantics"
                ),
            )
        if (
            self.local_closure_semantics
            is LocalClosureSemantics.MATERIALISED_SELECTOR_V1
            and uses != frozenset({CheckerUse.CLOSURE})
        ):
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=(
                    f"checker_contract:{self.checker_id}.local_closure_semantics"
                ),
            )
        if CheckerUse.CERTIFICATE in uses:
            if not subject_kinds:
                _fail(
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                    location=f"checker_contract:{self.checker_id}.certificate_subject_kinds",
                )
        elif subject_kinds or detail_fields:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_contract:{self.checker_id}",
            )
        if CheckerUse.CLOSURE not in uses and (selector_kinds or selector_fields):
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_contract:{self.checker_id}.closure_selector_kinds",
            )
        unsupported_selector_fields = {
            selector_field.record_type
            for selector_field in selector_fields
            if selector_field.record_type not in selector_kinds
        }
        if unsupported_selector_fields:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_contract:{self.checker_id}.selector_fields",
                identifiers=(
                    record_kind.value for record_kind in unsupported_selector_fields
                ),
            )
        if (
            self.local_closure_semantics
            is LocalClosureSemantics.MATERIALISED_SELECTOR_V1
        ):
            for selector_field in selector_fields:
                field_spec = _materialised_selector_field_spec(
                    selector_field.record_type,
                    selector_field.field,
                )
                if field_spec is None:
                    _fail(
                        RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                        location=(
                            f"checker_contract:{self.checker_id}.selector_fields"
                        ),
                        identifiers=(selector_field.selector_field_id,),
                    )
                accepted_types, reference_ceiling = field_spec
                if selector_field.value_type not in accepted_types or (
                    reference_ceiling is not None
                    and not selector_field.allowed_record_kinds
                    <= reference_ceiling
                ):
                    _fail(
                        RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                        location=(
                            f"checker_contract:{self.checker_id}.selector_fields"
                        ),
                        identifiers=(selector_field.selector_field_id,),
                    )
        if CheckerUse.CLOSURE in uses:
            if self.closure_frame_policy_id is None:
                _fail(
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                    location=f"checker_contract:{self.checker_id}.closure_frame_policy_id",
                )
            _require_id(
                self.closure_frame_policy_id,
                location=f"checker_contract:{self.checker_id}.closure_frame_policy_id",
            )
        elif self.closure_frame_policy_id is not None:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"checker_contract:{self.checker_id}.closure_frame_policy_id",
            )

    def permits_certificate(self, subject_kind: RecordKind) -> bool:
        return (
            type(subject_kind) is RecordKind
            and CheckerUse.CERTIFICATE in self.uses
            and subject_kind in self.certificate_subject_kinds
        )

    def supports_closure_selector(self, selector_kind: RecordKind) -> bool:
        return (
            type(selector_kind) is RecordKind
            and CheckerUse.CLOSURE in self.uses
            and selector_kind in self.closure_selector_kinds
        )

    def accepts_details(self, details: Mapping[str, object]) -> bool:
        if not isinstance(details, Mapping):
            return False
        required = {detail_field.key for detail_field in self.detail_fields}
        return required == set(details) and all(
            detail_field.value_type.accepts(details[detail_field.key])
            for detail_field in self.detail_fields
        )

    def selector_field_contracts(
        self,
        record_type: RecordKind,
    ) -> tuple[SelectorFieldContract, ...]:
        if type(record_type) is not RecordKind:
            raise TypeError("record_type must be an exact RecordKind")
        return tuple(
            field_contract
            for field_contract in self.selector_fields
            if field_contract.record_type is record_type
        )

    def accepts_selector_shape(
        self,
        *,
        record_type: RecordKind,
        where: Mapping[str, object],
    ) -> bool:
        fields = {
            field_contract.field: field_contract
            for field_contract in self.selector_field_contracts(record_type)
        }
        return set(where) <= set(fields) and all(
            fields[key].accepts(value) for key, value in where.items()
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PredicateDefinition:
    predicate_id: str
    version: int
    arg_type_ids: tuple[str, ...]
    frame_policy_id: str
    grade_policy: GradePolicy
    computability_class: ComputabilityClass
    primitive_allowed: bool
    allowed_face_kinds: frozenset[str] = field(default_factory=frozenset)
    allowed_challenge_kinds: frozenset[str] = field(default_factory=frozenset)
    checker_contract_ids: frozenset[str] = field(default_factory=frozenset)
    contrary_policy_id: str = "forbidden"
    rule_schema_ids: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _require_id(self.predicate_id, location="predicate.predicate_id")
        _require_version(self.version, location=f"predicate:{self.predicate_id}.version")
        object.__setattr__(
            self,
            "arg_type_ids",
            _freeze_string_tuple(
                self.arg_type_ids,
                location=f"predicate:{self.predicate_id}.arg_type_ids",
            ),
        )
        _require_id(
            self.frame_policy_id,
            location=f"predicate:{self.predicate_id}.frame_policy_id",
        )
        _require_id(
            self.contrary_policy_id,
            location=f"predicate:{self.predicate_id}.contrary_policy_id",
        )
        if type(self.grade_policy) is not GradePolicy:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"predicate:{self.predicate_id}.grade_policy",
            )
        if type(self.computability_class) is not ComputabilityClass:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"predicate:{self.predicate_id}.computability_class",
            )
        if type(self.primitive_allowed) is not bool:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"predicate:{self.predicate_id}.primitive_allowed",
            )
        for field_name in (
            "allowed_face_kinds",
            "allowed_challenge_kinds",
            "checker_contract_ids",
            "rule_schema_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _freeze_string_set(
                    getattr(self, field_name),
                    location=f"predicate:{self.predicate_id}.{field_name}",
                ),
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class DischargeCompatibility:
    challenge_kind: str
    admissible_discharge_kinds: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _require_id(self.challenge_kind, location="discharge_compatibility.challenge_kind")
        object.__setattr__(
            self,
            "admissible_discharge_kinds",
            _freeze_string_set(
                self.admissible_discharge_kinds,
                location=f"discharge_compatibility:{self.challenge_kind}",
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ChallengeTargetContract:
    """Registry-owned target-kind policy for one known challenge kind."""

    challenge_kind: str
    allowed_target_kinds: frozenset[RecordKind]

    def __post_init__(self) -> None:
        _require_id(self.challenge_kind, location="challenge_target.challenge_kind")
        allowed = _freeze_enum_set(
            self.allowed_target_kinds,
            location=f"challenge_target:{self.challenge_kind}.allowed_target_kinds",
            member_type=RecordKind,
        )
        if not allowed or not allowed <= {
            RecordKind.ATOM,
            RecordKind.RULE,
            RecordKind.FACE,
        }:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"challenge_target:{self.challenge_kind}.allowed_target_kinds",
            )
        object.__setattr__(self, "allowed_target_kinds", allowed)


PFF_V01_FACE_KINDS = frozenset(
    {
        "type",
        "version",
        "source",
        "witness",
        "frame",
        "transport",
        "grade",
        "coverage",
        "closure",
        "interpretation",
        "retention",
        "localisation",
        "recovery",
    }
)

PFF_V01_CHALLENGE_KINDS = frozenset(
    {
        "rebut",
        "undercut",
        "wound",
        "revoke",
        "defect",
        "localisation_gap",
        "recovery_gap",
        "currentness_gap",
        "closure_gap",
    }
)

_BLOCKING_TARGET_KINDS = frozenset({RecordKind.RULE, RecordKind.FACE})
_GENERAL_TARGET_KINDS = frozenset(
    {RecordKind.ATOM, RecordKind.RULE, RecordKind.FACE}
)

PFF_V01_CHALLENGE_TARGETS = tuple(
    ChallengeTargetContract(
        challenge_kind=challenge_kind,
        allowed_target_kinds=(
            _GENERAL_TARGET_KINDS
            if challenge_kind in {"rebut", "defect"}
            else _BLOCKING_TARGET_KINDS
        ),
    )
    for challenge_kind in sorted(PFF_V01_CHALLENGE_KINDS)
)

PFF_V01_DISCHARGE_KINDS = frozenset(
    {
        "repair",
        "malformed_or_inapplicable",
        "replacement_transport",
        "repaired_transport",
        "inapplicable_with_valid_domain",
        "successor_version_transport",
        "explicit_retraction",
        "good_face_discharge",
        "internal_defect",
        "good_localisation",
        "recovery_witness",
        "current_frontier_witness",
        "current_repertoire_witness",
        "passed_local_closure",
    }
)

PFF_V01_DISCHARGE_COMPATIBILITY = (
    DischargeCompatibility(challenge_kind="rebut"),
    DischargeCompatibility(
        challenge_kind="undercut",
        admissible_discharge_kinds={"repair", "malformed_or_inapplicable"},
    ),
    DischargeCompatibility(
        challenge_kind="wound",
        admissible_discharge_kinds={
            "replacement_transport",
            "repaired_transport",
            "inapplicable_with_valid_domain",
        },
    ),
    DischargeCompatibility(
        challenge_kind="revoke",
        admissible_discharge_kinds={
            "successor_version_transport",
            "explicit_retraction",
        },
    ),
    DischargeCompatibility(
        challenge_kind="defect",
        admissible_discharge_kinds={"good_face_discharge"},
    ),
    DischargeCompatibility(
        challenge_kind="localisation_gap",
        admissible_discharge_kinds={"internal_defect", "good_localisation"},
    ),
    DischargeCompatibility(
        challenge_kind="recovery_gap",
        admissible_discharge_kinds={"recovery_witness"},
    ),
    DischargeCompatibility(
        challenge_kind="currentness_gap",
        admissible_discharge_kinds={
            "current_frontier_witness",
            "current_repertoire_witness",
        },
    ),
    DischargeCompatibility(
        challenge_kind="closure_gap",
        admissible_discharge_kinds={"passed_local_closure"},
    ),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PredicateRegistry:
    """One exact immutable registry version selected by a package header."""

    registry_id: str
    version: int
    argument_types: tuple[ArgumentTypeContract, ...] = ()
    frame_policies: tuple[FramePolicy, ...] = ()
    contrary_policies: tuple[ContraryPolicy, ...] = ()
    checker_contracts: tuple[CheckerContract, ...] = ()
    predicates: tuple[PredicateDefinition, ...] = ()
    known_face_kinds: frozenset[str] = PFF_V01_FACE_KINDS
    known_challenge_kinds: frozenset[str] = PFF_V01_CHALLENGE_KINDS
    known_discharge_kinds: frozenset[str] = PFF_V01_DISCHARGE_KINDS
    rule_schema_ids: frozenset[str] = field(default_factory=frozenset)
    discharge_compatibility: tuple[DischargeCompatibility, ...] = (
        PFF_V01_DISCHARGE_COMPATIBILITY
    )
    challenge_target_contracts: tuple[ChallengeTargetContract, ...] = (
        PFF_V01_CHALLENGE_TARGETS
    )

    def __post_init__(self) -> None:
        _require_id(self.registry_id, location="registry.registry_id")
        _require_version(self.version, location=f"registry:{self.registry_id}.version")

        definition_fields: tuple[tuple[str, type[object], str], ...] = (
            ("argument_types", ArgumentTypeContract, "argument_type_id"),
            ("frame_policies", FramePolicy, "frame_policy_id"),
            ("contrary_policies", ContraryPolicy, "contrary_policy_id"),
            ("checker_contracts", CheckerContract, "checker_id"),
            ("predicates", PredicateDefinition, "predicate_id"),
            (
                "discharge_compatibility",
                DischargeCompatibility,
                "challenge_kind",
            ),
            (
                "challenge_target_contracts",
                ChallengeTargetContract,
                "challenge_kind",
            ),
        )
        for field_name, member_type, id_attribute in definition_fields:
            object.__setattr__(
                self,
                field_name,
                _freeze_definitions(
                    getattr(self, field_name),
                    location=f"registry:{self.registry_id}.{field_name}",
                    member_type=member_type,
                    id_attribute=id_attribute,
                ),
            )

        for field_name in (
            "known_face_kinds",
            "known_challenge_kinds",
            "known_discharge_kinds",
            "rule_schema_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _freeze_string_set(
                    getattr(self, field_name),
                    location=f"registry:{self.registry_id}.{field_name}",
                ),
            )

        argument_type_ids = {item.argument_type_id for item in self.argument_types}
        frame_policy_ids = {item.frame_policy_id for item in self.frame_policies}
        contrary_policy_ids = {item.contrary_policy_id for item in self.contrary_policies}
        checker_contracts = {item.checker_id: item for item in self.checker_contracts}

        for checker in self.checker_contracts:
            if (
                checker.closure_frame_policy_id is not None
                and checker.closure_frame_policy_id not in frame_policy_ids
            ):
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_FRAME_POLICY,
                    location=f"checker_contract:{checker.checker_id}.closure_frame_policy_id",
                    identifiers=(checker.closure_frame_policy_id,),
                )

        for predicate in self.predicates:
            missing_args = set(predicate.arg_type_ids) - argument_type_ids
            if missing_args:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_ARGUMENT_TYPE,
                    location=f"predicate:{predicate.predicate_id}.arg_type_ids",
                    identifiers=missing_args,
                )
            if predicate.frame_policy_id not in frame_policy_ids:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_FRAME_POLICY,
                    location=f"predicate:{predicate.predicate_id}.frame_policy_id",
                    identifiers=(predicate.frame_policy_id,),
                )
            if predicate.contrary_policy_id not in contrary_policy_ids:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_CONTRARY_POLICY,
                    location=f"predicate:{predicate.predicate_id}.contrary_policy_id",
                    identifiers=(predicate.contrary_policy_id,),
                )
            missing_checkers = predicate.checker_contract_ids - set(checker_contracts)
            if missing_checkers:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_CHECKER_CONTRACT,
                    location=f"predicate:{predicate.predicate_id}.checker_contract_ids",
                    identifiers=missing_checkers,
                )
            non_certificate_checkers = {
                checker_id
                for checker_id in predicate.checker_contract_ids
                if CheckerUse.CERTIFICATE not in checker_contracts[checker_id].uses
            }
            if non_certificate_checkers:
                _fail(
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                    location=f"predicate:{predicate.predicate_id}.checker_contract_ids",
                    identifiers=non_certificate_checkers,
                )
            unknown_faces = predicate.allowed_face_kinds - self.known_face_kinds
            if unknown_faces:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_FACE_KIND,
                    location=f"predicate:{predicate.predicate_id}.allowed_face_kinds",
                    identifiers=unknown_faces,
                )
            unknown_challenges = (
                predicate.allowed_challenge_kinds - self.known_challenge_kinds
            )
            if unknown_challenges:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_CHALLENGE_KIND,
                    location=f"predicate:{predicate.predicate_id}.allowed_challenge_kinds",
                    identifiers=unknown_challenges,
                )
            unknown_schemas = predicate.rule_schema_ids - self.rule_schema_ids
            if unknown_schemas:
                _fail(
                    RegistryDefinitionErrorCode.UNKNOWN_RULE_SCHEMA,
                    location=f"predicate:{predicate.predicate_id}.rule_schema_ids",
                    identifiers=unknown_schemas,
                )

            contrary_policy = self.contrary_policy(predicate.contrary_policy_id)
            if (
                contrary_policy.mode
                is ContraryPolicyMode.STABLE_COMPARISON_BOUNDARY
                and any(
                    position >= len(predicate.arg_type_ids)
                    for position in contrary_policy.comparison_arg_positions
                )
            ):
                _fail(
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                    location=f"predicate:{predicate.predicate_id}.contrary_policy_id",
                    identifiers=(predicate.contrary_policy_id,),
                )

        compatibility = {
            item.challenge_kind: item for item in self.discharge_compatibility
        }
        unknown_compatibility_challenges = set(compatibility) - self.known_challenge_kinds
        if unknown_compatibility_challenges:
            _fail(
                RegistryDefinitionErrorCode.UNKNOWN_CHALLENGE_KIND,
                location=f"registry:{self.registry_id}.discharge_compatibility",
                identifiers=unknown_compatibility_challenges,
            )
        missing_compatibility = self.known_challenge_kinds - set(compatibility)
        if missing_compatibility:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"registry:{self.registry_id}.discharge_compatibility",
                identifiers=missing_compatibility,
            )
        unknown_discharges = {
            discharge
            for item in self.discharge_compatibility
            for discharge in item.admissible_discharge_kinds
            if discharge not in self.known_discharge_kinds
        }
        if unknown_discharges:
            _fail(
                RegistryDefinitionErrorCode.UNKNOWN_DISCHARGE_KIND,
                location=f"registry:{self.registry_id}.discharge_compatibility",
                identifiers=unknown_discharges,
            )

        target_contracts = {
            item.challenge_kind: item for item in self.challenge_target_contracts
        }
        if set(target_contracts) != self.known_challenge_kinds:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"registry:{self.registry_id}.challenge_target_contracts",
                identifiers=set(target_contracts) ^ self.known_challenge_kinds,
            )
        core_targets = {
            item.challenge_kind: item for item in PFF_V01_CHALLENGE_TARGETS
        }
        redefined_core_targets = {
            challenge_kind
            for challenge_kind, contract in target_contracts.items()
            if challenge_kind in core_targets
            and not contract.allowed_target_kinds
            <= core_targets[challenge_kind].allowed_target_kinds
        }
        if redefined_core_targets:
            _fail(
                RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                location=f"registry:{self.registry_id}.challenge_target_contracts",
                identifiers=redefined_core_targets,
            )

    @staticmethod
    def _lookup(
        values: tuple[object, ...],
        *,
        id_attribute: str,
        identifier: str,
    ) -> object:
        if type(identifier) is not str:
            raise TypeError("registry lookup identifier must be a string")
        for value in values:
            if getattr(value, id_attribute) == identifier:
                return value
        raise KeyError(identifier)

    def predicate(self, predicate_id: str) -> PredicateDefinition:
        return self._lookup(
            self.predicates,
            id_attribute="predicate_id",
            identifier=predicate_id,
        )  # type: ignore[return-value]

    def argument_type(self, argument_type_id: str) -> ArgumentTypeContract:
        return self._lookup(
            self.argument_types,
            id_attribute="argument_type_id",
            identifier=argument_type_id,
        )  # type: ignore[return-value]

    def frame_policy(self, frame_policy_id: str) -> FramePolicy:
        return self._lookup(
            self.frame_policies,
            id_attribute="frame_policy_id",
            identifier=frame_policy_id,
        )  # type: ignore[return-value]

    def contrary_policy(self, contrary_policy_id: str) -> ContraryPolicy:
        return self._lookup(
            self.contrary_policies,
            id_attribute="contrary_policy_id",
            identifier=contrary_policy_id,
        )  # type: ignore[return-value]

    def checker_contract(self, checker_id: str) -> CheckerContract:
        return self._lookup(
            self.checker_contracts,
            id_attribute="checker_id",
            identifier=checker_id,
        )  # type: ignore[return-value]

    def admissible_discharge_kinds(self, challenge_kind: str) -> frozenset[str]:
        item = self._lookup(
            self.discharge_compatibility,
            id_attribute="challenge_kind",
            identifier=challenge_kind,
        )
        return item.admissible_discharge_kinds  # type: ignore[union-attr]

    def allowed_challenge_target_kinds(
        self,
        challenge_kind: str,
    ) -> frozenset[RecordKind]:
        item = self._lookup(
            self.challenge_target_contracts,
            id_attribute="challenge_kind",
            identifier=challenge_kind,
        )
        return item.allowed_target_kinds  # type: ignore[union-attr]

    def is_discharge_compatible(
        self,
        *,
        challenge_kind: str,
        discharge_kind: str,
    ) -> bool:
        if discharge_kind not in self.known_discharge_kinds:
            raise KeyError(discharge_kind)
        return discharge_kind in self.admissible_discharge_kinds(challenge_kind)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegistryCatalog:
    """An immutable exact registry lookup with no fallback or registration."""

    registries: tuple[PredicateRegistry, ...] = ()

    def __post_init__(self) -> None:
        registries = _collection(self.registries, location="registry_catalog.registries")
        if any(type(registry) is not PredicateRegistry for registry in registries):
            _fail(
                RegistryDefinitionErrorCode.INVALID_MEMBER,
                location="registry_catalog.registries",
            )
        registry_ids = tuple(registry.registry_id for registry in registries)
        if len(set(registry_ids)) != len(registry_ids):
            raise RegistryDefinitionError(
                RegistryDefinitionErrorCode.DUPLICATE_REGISTRY_ID,
                location="registry_catalog.registries",
                identifiers=registry_ids,
            )
        object.__setattr__(
            self,
            "registries",
            tuple(sorted(registries, key=lambda registry: registry.registry_id)),
        )

    def lookup(self, registry_id: str) -> PredicateRegistry:
        if type(registry_id) is not str:
            raise TypeError("registry_id must be a string")
        for registry in self.registries:
            if registry.registry_id == registry_id:
                return registry
        raise KeyError(registry_id)


__all__ = [
    "ArgumentTypeContract",
    "CheckerContract",
    "CheckerDetailField",
    "CheckerDetailType",
    "CheckerUse",
    "ChallengeTargetContract",
    "ComputabilityClass",
    "ContraryPolicy",
    "ContraryPolicyMode",
    "DischargeCompatibility",
    "FramePolicy",
    "FramePolicyMode",
    "GradePolicy",
    "LocalClosureSemantics",
    "MATERIALISED_SELECTOR_V1_ID",
    "PFF_GRADES",
    "PFF_V01_CHALLENGE_KINDS",
    "PFF_V01_CHALLENGE_TARGETS",
    "PFF_V01_DISCHARGE_COMPATIBILITY",
    "PFF_V01_DISCHARGE_KINDS",
    "PFF_V01_FACE_KINDS",
    "PredicateDefinition",
    "PredicateRegistry",
    "RegistryCatalog",
    "RegistryDefinitionError",
    "RegistryDefinitionErrorCode",
    "SelectorFieldContract",
]
