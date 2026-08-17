"""Strict, deterministic extraction of one untrusted generation draft."""

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from .model import (
    DraftAtom,
    DraftEvidenceRequest,
    DraftPackage,
    DraftRef,
    DraftRule,
    GenerationEnvelope,
)


_RAW_PROMPT_BYTES = 1_048_576
_RAW_RESPONSE_BYTES = 4_194_304
_PAYLOAD_BYTES = 1_048_576
_JSON_DEPTH = 64
_STRING_BYTES = 262_144
_COLLECTION_MEMBERS = 4_096
_MAX_VERSION_TEXT = "9223372036854775807"
_DRAFT_SCHEMA = "pff-draft/0.1"
_OPEN_MARKER = b"<<<PFF-DRAFT/0.1>>>\n"
_CLOSE_MARKER = b"\n<<<END-PFF-DRAFT/0.1>>>"
_EXTRACTED_DRAFT_FACTORY = object()

_FORBIDDEN_FIELDS = frozenset(
    {
        "accepted",
        "base",
        "certificate",
        "certificate_result",
        "certificates",
        "checker",
        "closure",
        "closure_result",
        "closures",
        "confidence",
        "details",
        "excluded",
        "header",
        "live",
        "open",
        "parent_package_hash",
        "payload_hash",
        "primitive",
        "probability_true",
        "protected_open",
        "registry",
        "registry_id",
        "result",
        "status",
        "support",
    }
)


class DraftExtractionCode(StrEnum):
    """Stable machine-readable extraction issue vocabulary."""

    CAPTURE_DIGEST_MISMATCH = "capture_digest_mismatch"
    CAPTURE_LIMIT_EXCEEDED = "capture_limit_exceeded"
    RAW_UTF8 = "raw_utf8"
    DRAFT_BLOCK_MISSING = "draft_block_missing"
    DRAFT_BLOCK_MULTIPLE = "draft_block_multiple"
    DRAFT_BLOCK_UNTERMINATED = "draft_block_unterminated"
    DRAFT_BLOCK_ORDER = "draft_block_order"
    DRAFT_PAYLOAD_LIMIT = "draft_payload_limit"
    DRAFT_LIMIT_EXCEEDED = "draft_limit_exceeded"
    DRAFT_JSON_INVALID = "draft_json_invalid"
    DRAFT_JSON_DUPLICATE_KEY = "draft_json_duplicate_key"
    DRAFT_ROOT_TYPE = "draft_root_type"
    DRAFT_FIELD_MISSING = "draft_field_missing"
    DRAFT_SCHEMA_MISMATCH = "draft_schema_mismatch"
    DRAFT_FIELD_FORBIDDEN = "draft_field_forbidden"
    DRAFT_FIELD_UNKNOWN = "draft_field_unknown"
    DRAFT_VALUE_TYPE = "draft_value_type"
    DRAFT_INVALID_ID = "draft_invalid_id"
    DRAFT_INVALID_VERSION = "draft_invalid_version"
    DRAFT_RESERVED_ID = "draft_reserved_id"
    DRAFT_DUPLICATE_RECORD = "draft_duplicate_record"
    DRAFT_DUPLICATE_MEMBER = "draft_duplicate_member"
    DRAFT_UNRESOLVED_REFERENCE = "draft_unresolved_reference"
    DRAFT_REFERENCE_KIND = "draft_reference_kind"
    DRAFT_EVIDENCE_BINDING = "draft_evidence_binding"


def _valid_pointer(path: str) -> bool:
    if not path:
        return True
    if not path.startswith("/"):
        return False
    index = 0
    while index < len(path):
        if path[index] != "~":
            index += 1
            continue
        if index + 1 == len(path) or path[index + 1] not in {"0", "1"}:
            return False
        index += 2
    return True


@dataclass(frozen=True, slots=True)
class DraftExtractionIssue:
    """One deterministic, payload-free extraction diagnostic."""

    code: DraftExtractionCode
    path: str
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.code) is not DraftExtractionCode:
            raise TypeError("code must be an exact DraftExtractionCode")
        if type(self.path) is not str:
            raise TypeError("path must be an exact str")
        if not _valid_pointer(self.path):
            raise ValueError("path must be a valid RFC 6901 JSON Pointer")
        if type(self.details) is not tuple:
            raise TypeError("details must be an exact tuple")
        if any(type(detail) is not str for detail in self.details):
            raise TypeError("details must contain exact str values")


def _issue_key(issue: DraftExtractionIssue) -> tuple[object, ...]:
    return (issue.path, issue.code.value, issue.details)


class DraftExtractionError(ValueError):
    """Aggregate fail-closed extraction failure."""

    issues: tuple[DraftExtractionIssue, ...]

    def __init__(self, issues: tuple[DraftExtractionIssue, ...]) -> None:
        if type(issues) is not tuple:
            raise TypeError("issues must be an exact tuple")
        if any(type(issue) is not DraftExtractionIssue for issue in issues):
            raise TypeError("issues must contain exact DraftExtractionIssue values")
        if not issues:
            raise ValueError("DraftExtractionError requires at least one issue")
        canonical = tuple(sorted(set(issues), key=_issue_key))
        self.issues = canonical
        ValueError.__init__(self, "draft extraction failed")


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class ExtractedDraft:
    """Factory-only successful extraction boundary."""

    source: GenerationEnvelope
    payload_sha256: str
    draft: DraftPackage

    __hash__ = None

    def __init__(
        self,
        *,
        source: GenerationEnvelope,
        payload_sha256: str,
        draft: DraftPackage,
        _factory: object | None = None,
    ) -> None:
        if _factory is not _EXTRACTED_DRAFT_FACTORY:
            raise TypeError("ExtractedDraft is created only by extract_draft")
        if type(source) is not GenerationEnvelope:
            raise TypeError("source must be an exact GenerationEnvelope")
        if type(payload_sha256) is not str:
            raise TypeError("payload_sha256 must be an exact str")
        if type(draft) is not DraftPackage:
            raise TypeError("draft must be an exact DraftPackage")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "payload_sha256", payload_sha256)
        object.__setattr__(self, "draft", draft)


@dataclass(frozen=True, slots=True)
class _ObjectPairs:
    pairs: tuple[tuple[str, object], ...]


@dataclass(frozen=True, slots=True)
class _IntegerToken:
    text: str


@dataclass(frozen=True, slots=True)
class _FloatToken:
    text: str


@dataclass(frozen=True, slots=True)
class _RefData:
    id: str
    version: int
    path: str

    @property
    def identity(self) -> tuple[str, int]:
        return (self.id, self.version)


@dataclass(frozen=True, slots=True)
class _AtomData:
    id: str
    version: int
    predicate: str
    args: tuple[str, ...]
    frame: str
    grade: str | None
    path: str

    @property
    def identity(self) -> tuple[str, int]:
        return (self.id, self.version)


@dataclass(frozen=True, slots=True)
class _RuleData:
    id: str
    version: int
    head: _RefData
    positive: tuple[_RefData, ...]
    evidence_request: _RefData
    path: str

    @property
    def identity(self) -> tuple[str, int]:
        return (self.id, self.version)


@dataclass(frozen=True, slots=True)
class _EvidenceData:
    id: str
    version: int
    kind: str
    subject: _RefData
    question: str
    path: str

    @property
    def identity(self) -> tuple[str, int]:
        return (self.id, self.version)


def _issue(
    code: DraftExtractionCode,
    path: str,
    details: tuple[str, ...] = (),
) -> DraftExtractionIssue:
    return DraftExtractionIssue(code=code, path=path, details=details)


def _digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def _field_digest(field: str) -> str:
    return _digest(field.encode("utf-8"))


def _pointer(path: str, token: str) -> str:
    escaped = token.replace("~", "~0").replace("/", "~1")
    return path + "/" + escaped


def _marker_positions(data: bytes, marker: bytes, *, opening: bool) -> tuple[int, ...]:
    positions: list[int] = []
    start = 0
    while True:
        position = data.find(marker, start)
        if position < 0:
            return tuple(positions)
        if opening:
            boundary_ok = position == 0 or data[position - 1] == 0x0A
        else:
            after = position + len(marker)
            boundary_ok = after == len(data) or data[after] == 0x0A
        if boundary_ok:
            positions.append(position)
        start = position + 1


def _delimited_payload(data: bytes) -> tuple[bytes | None, DraftExtractionCode | None]:
    openers = _marker_positions(data, _OPEN_MARKER, opening=True)
    closers = _marker_positions(data, _CLOSE_MARKER, opening=False)
    if len(openers) > 1 or len(closers) > 1:
        return (None, DraftExtractionCode.DRAFT_BLOCK_MULTIPLE)
    if not openers and not closers:
        return (None, DraftExtractionCode.DRAFT_BLOCK_MISSING)
    if not openers:
        return (None, DraftExtractionCode.DRAFT_BLOCK_ORDER)
    if not closers:
        return (None, DraftExtractionCode.DRAFT_BLOCK_UNTERMINATED)
    payload_start = openers[0] + len(_OPEN_MARKER)
    payload_end = closers[0]
    if payload_end < payload_start:
        return (None, DraftExtractionCode.DRAFT_BLOCK_ORDER)
    return (data[payload_start:payload_end], None)


def _depth_exceeded(payload: bytes) -> bool:
    depth = 0
    in_string = False
    backslashes = 0
    for byte in payload:
        if in_string:
            if byte == 0x5C:
                backslashes += 1
                continue
            if byte == 0x22 and backslashes % 2 == 0:
                in_string = False
            backslashes = 0
            continue
        if byte == 0x22:
            in_string = True
        elif byte in {0x5B, 0x7B}:
            depth += 1
            if depth > _JSON_DEPTH:
                return True
        elif byte in {0x5D, 0x7D} and depth > 0:
            depth -= 1
    return False


def _object_pairs(pairs: list[tuple[str, object]]) -> _ObjectPairs:
    return _ObjectPairs(tuple(pairs))


def _integer_token(text: str) -> _IntegerToken:
    return _IntegerToken(text)


def _float_token(text: str) -> _FloatToken:
    return _FloatToken(text)


def _reject_constant(text: str) -> object:
    raise ValueError("non-finite JSON number")


def _contains_non_scalar_string(root: object) -> bool:
    stack = [root]
    while stack:
        value = stack.pop()
        if type(value) is str:
            if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
                return True
        elif type(value) is _ObjectPairs:
            for key, member in value.pairs:
                if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                    return True
                stack.append(member)
        elif type(value) is list:
            stack.extend(value)
    return False


def _duplicate_key_issues(root: object) -> tuple[DraftExtractionIssue, ...]:
    issues: list[DraftExtractionIssue] = []
    stack = [root]
    ordinal = 0
    while stack:
        value = stack.pop()
        if type(value) is _ObjectPairs:
            object_ordinal = ordinal
            ordinal += 1
            seen: set[str] = set()
            duplicated: set[str] = set()
            for key, _ in value.pairs:
                if key in seen and key not in duplicated:
                    issues.append(
                        _issue(
                            DraftExtractionCode.DRAFT_JSON_DUPLICATE_KEY,
                            "/response/block",
                            (
                                f"object_ordinal={object_ordinal}",
                                f"field_sha256={_field_digest(key)}",
                            ),
                        )
                    )
                    duplicated.add(key)
                seen.add(key)
            for _, member in reversed(value.pairs):
                stack.append(member)
        elif type(value) is list:
            for member in reversed(value):
                stack.append(member)
    return tuple(issues)


def _mapping(value: _ObjectPairs) -> dict[str, object]:
    return {key: member for key, member in value.pairs}


def _shape_fields(
    value: _ObjectPairs,
    path: str,
    fields: frozenset[str],
    issues: list[DraftExtractionIssue],
) -> dict[str, object]:
    members = _mapping(value)
    for field in fields:
        if field not in members:
            issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_FIELD_MISSING,
                    _pointer(path, field),
                )
            )
    for field, _ in value.pairs:
        if field in fields:
            continue
        if field in _FORBIDDEN_FIELDS:
            issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_FIELD_FORBIDDEN,
                    _pointer(path, field),
                )
            )
        else:
            issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_FIELD_UNKNOWN,
                    path,
                    (f"field_sha256={_field_digest(field)}",),
                )
            )
    return members


def _string_value(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
    *,
    allow_empty: bool,
    exact: str | None = None,
) -> str | None:
    if type(value) is not str:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return None
    byte_length = len(value.encode("utf-8"))
    if byte_length > _STRING_BYTES:
        issues.append(
            _issue(
                DraftExtractionCode.DRAFT_LIMIT_EXCEEDED,
                path,
                (
                    "resource=json_string_bytes",
                    f"actual={byte_length}",
                    f"limit={_STRING_BYTES}",
                ),
            )
        )
        return None
    if not allow_empty and not value:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return None
    if exact is not None and value != exact:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return None
    return value


def _identifier_value(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
) -> str | None:
    if type(value) is not str:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return None
    byte_length = len(value.encode("utf-8"))
    if byte_length > _STRING_BYTES:
        issues.append(
            _issue(
                DraftExtractionCode.DRAFT_LIMIT_EXCEEDED,
                path,
                (
                    "resource=json_string_bytes",
                    f"actual={byte_length}",
                    f"limit={_STRING_BYTES}",
                ),
            )
        )
        return None
    if not value:
        issues.append(_issue(DraftExtractionCode.DRAFT_INVALID_ID, path))
        return None
    if value.startswith("__pff__:"):
        issues.append(_issue(DraftExtractionCode.DRAFT_RESERVED_ID, path))
        return None
    return value


def _version_value(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
) -> int | None:
    if type(value) is not _IntegerToken:
        issues.append(_issue(DraftExtractionCode.DRAFT_INVALID_VERSION, path))
        return None
    text = value.text
    if (
        text.startswith("-")
        or text == "0"
        or len(text) > len(_MAX_VERSION_TEXT)
        or (len(text) == len(_MAX_VERSION_TEXT) and text > _MAX_VERSION_TEXT)
    ):
        issues.append(_issue(DraftExtractionCode.DRAFT_INVALID_VERSION, path))
        return None
    return int(text)


def _reference(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
) -> _RefData | None:
    if type(value) is not _ObjectPairs:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return None
    members = _shape_fields(
        value,
        path,
        frozenset({"id", "version"}),
        issues,
    )
    identifier = None
    version = None
    if "id" in members:
        identifier = _identifier_value(members["id"], _pointer(path, "id"), issues)
    if "version" in members:
        version = _version_value(
            members["version"],
            _pointer(path, "version"),
            issues,
        )
    if identifier is None or version is None:
        return None
    return _RefData(id=identifier, version=version, path=path)


def _atom_record(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
) -> tuple[tuple[str, int] | None, _AtomData | None]:
    if type(value) is not _ObjectPairs:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return (None, None)
    before = len(issues)
    members = _shape_fields(
        value,
        path,
        frozenset({"id", "version", "predicate", "args", "frame", "grade"}),
        issues,
    )
    identifier = None
    version = None
    predicate = None
    arguments: tuple[str, ...] | None = None
    frame = None
    grade: str | None = None
    grade_valid = False

    if "id" in members:
        identifier = _identifier_value(members["id"], _pointer(path, "id"), issues)
    if "version" in members:
        version = _version_value(
            members["version"],
            _pointer(path, "version"),
            issues,
        )
    if "predicate" in members:
        predicate = _string_value(
            members["predicate"],
            _pointer(path, "predicate"),
            issues,
            allow_empty=False,
        )
    if "args" in members:
        args_path = _pointer(path, "args")
        raw_args = members["args"]
        if type(raw_args) is not list:
            issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, args_path))
        elif len(raw_args) > _COLLECTION_MEMBERS:
            issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_LIMIT_EXCEEDED,
                    args_path,
                    (
                        "resource=args_members",
                        f"actual={len(raw_args)}",
                        f"limit={_COLLECTION_MEMBERS}",
                    ),
                )
            )
        else:
            parsed_arguments: list[str] = []
            valid_arguments = True
            for index, argument in enumerate(raw_args):
                parsed = _string_value(
                    argument,
                    _pointer(args_path, str(index)),
                    issues,
                    allow_empty=True,
                )
                if parsed is None:
                    valid_arguments = False
                else:
                    parsed_arguments.append(parsed)
            if valid_arguments:
                arguments = tuple(parsed_arguments)
    if "frame" in members:
        frame = _string_value(
            members["frame"],
            _pointer(path, "frame"),
            issues,
            allow_empty=False,
        )
    if "grade" in members:
        grade_path = _pointer(path, "grade")
        raw_grade = members["grade"]
        if raw_grade is None:
            grade_valid = True
        else:
            parsed_grade = _string_value(
                raw_grade,
                grade_path,
                issues,
                allow_empty=True,
            )
            if parsed_grade is not None:
                grade = parsed_grade
                grade_valid = True

    identity = None
    if identifier is not None and version is not None:
        identity = (identifier, version)
    if (
        len(issues) != before
        or identity is None
        or predicate is None
        or arguments is None
        or frame is None
        or not grade_valid
    ):
        return (identity, None)
    return (
        identity,
        _AtomData(
            id=identifier,
            version=version,
            predicate=predicate,
            args=arguments,
            frame=frame,
            grade=grade,
            path=path,
        ),
    )


def _rule_record(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
) -> tuple[tuple[str, int] | None, _RuleData | None]:
    if type(value) is not _ObjectPairs:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return (None, None)
    before = len(issues)
    members = _shape_fields(
        value,
        path,
        frozenset({"id", "version", "head", "positive", "evidence_request"}),
        issues,
    )
    identifier = None
    version = None
    head = None
    positives: tuple[_RefData, ...] | None = None
    evidence_request = None

    if "id" in members:
        identifier = _identifier_value(members["id"], _pointer(path, "id"), issues)
    if "version" in members:
        version = _version_value(
            members["version"],
            _pointer(path, "version"),
            issues,
        )
    if "head" in members:
        head = _reference(members["head"], _pointer(path, "head"), issues)
    if "positive" in members:
        positive_path = _pointer(path, "positive")
        raw_positive = members["positive"]
        if type(raw_positive) is not list:
            issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, positive_path))
        elif len(raw_positive) > _COLLECTION_MEMBERS:
            issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_LIMIT_EXCEEDED,
                    positive_path,
                    (
                        "resource=positive_members",
                        f"actual={len(raw_positive)}",
                        f"limit={_COLLECTION_MEMBERS}",
                    ),
                )
            )
        else:
            parsed_positive: list[_RefData] = []
            seen_positive: set[tuple[str, int]] = set()
            valid_positive = True
            for index, raw_reference in enumerate(raw_positive):
                member_path = _pointer(positive_path, str(index))
                reference = _reference(raw_reference, member_path, issues)
                if reference is None:
                    valid_positive = False
                    continue
                if reference.identity in seen_positive:
                    issues.append(
                        _issue(
                            DraftExtractionCode.DRAFT_DUPLICATE_MEMBER,
                            member_path,
                        )
                    )
                    valid_positive = False
                else:
                    seen_positive.add(reference.identity)
                    parsed_positive.append(reference)
            if valid_positive:
                positives = tuple(parsed_positive)
    if "evidence_request" in members:
        evidence_request = _reference(
            members["evidence_request"],
            _pointer(path, "evidence_request"),
            issues,
        )

    identity = None
    if identifier is not None and version is not None:
        identity = (identifier, version)
    if (
        len(issues) != before
        or identity is None
        or head is None
        or positives is None
        or evidence_request is None
    ):
        return (identity, None)
    return (
        identity,
        _RuleData(
            id=identifier,
            version=version,
            head=head,
            positive=positives,
            evidence_request=evidence_request,
            path=path,
        ),
    )


def _evidence_record(
    value: object,
    path: str,
    issues: list[DraftExtractionIssue],
) -> tuple[tuple[str, int] | None, _EvidenceData | None]:
    if type(value) is not _ObjectPairs:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return (None, None)
    before = len(issues)
    members = _shape_fields(
        value,
        path,
        frozenset({"id", "version", "kind", "subject", "question"}),
        issues,
    )
    identifier = None
    version = None
    kind = None
    subject = None
    question = None

    if "id" in members:
        identifier = _identifier_value(members["id"], _pointer(path, "id"), issues)
    if "version" in members:
        version = _version_value(
            members["version"],
            _pointer(path, "version"),
            issues,
        )
    if "kind" in members:
        kind = _string_value(
            members["kind"],
            _pointer(path, "kind"),
            issues,
            allow_empty=False,
            exact="certificate",
        )
    if "subject" in members:
        subject = _reference(
            members["subject"],
            _pointer(path, "subject"),
            issues,
        )
    if "question" in members:
        question = _string_value(
            members["question"],
            _pointer(path, "question"),
            issues,
            allow_empty=False,
        )

    identity = None
    if identifier is not None and version is not None:
        identity = (identifier, version)
    if (
        len(issues) != before
        or identity is None
        or kind is None
        or subject is None
        or question is None
    ):
        return (identity, None)
    return (
        identity,
        _EvidenceData(
            id=identifier,
            version=version,
            kind=kind,
            subject=subject,
            question=question,
            path=path,
        ),
    )


def _record_collection(
    value: object,
    path: str,
    field: str,
    validator: object,
    issues: list[DraftExtractionIssue],
) -> list[object] | None:
    if type(value) is not list:
        issues.append(_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, path))
        return None
    if len(value) > _COLLECTION_MEMBERS:
        issues.append(
            _issue(
                DraftExtractionCode.DRAFT_LIMIT_EXCEEDED,
                path,
                (
                    f"resource={field}_members",
                    f"actual={len(value)}",
                    f"limit={_COLLECTION_MEMBERS}",
                ),
            )
        )
        return None
    records: list[object] = []
    seen: set[tuple[str, int]] = set()
    for index, raw_record in enumerate(value):
        record_path = _pointer(path, str(index))
        identity, record = validator(raw_record, record_path, issues)
        if identity is not None:
            if identity in seen:
                issues.append(
                    _issue(
                        DraftExtractionCode.DRAFT_DUPLICATE_RECORD,
                        record_path,
                    )
                )
            else:
                seen.add(identity)
        if record is not None:
            records.append(record)
    return records


def _reference_issue(
    reference: _RefData,
    expected: set[tuple[str, int]],
    others: set[tuple[str, int]],
) -> DraftExtractionIssue | None:
    if reference.identity in expected:
        return None
    if reference.identity in others:
        code = DraftExtractionCode.DRAFT_REFERENCE_KIND
    else:
        code = DraftExtractionCode.DRAFT_UNRESOLVED_REFERENCE
    return _issue(code, reference.path)


def _materialise(
    atoms: list[_AtomData],
    rules: list[_RuleData],
    evidence: list[_EvidenceData],
) -> DraftPackage:
    atom_records = tuple(
        DraftAtom._from_extraction(
            id=atom.id,
            version=atom.version,
            predicate=atom.predicate,
            args=atom.args,
            frame=atom.frame,
            grade=atom.grade,
        )
        for atom in sorted(atoms, key=lambda item: item.identity)
    )
    rule_records = tuple(
        DraftRule._from_extraction(
            id=rule.id,
            version=rule.version,
            head=DraftRef(rule.head.id, rule.head.version),
            positive=frozenset(
                DraftRef(reference.id, reference.version)
                for reference in rule.positive
            ),
            evidence_request=DraftRef(
                rule.evidence_request.id,
                rule.evidence_request.version,
            ),
        )
        for rule in sorted(rules, key=lambda item: item.identity)
    )
    evidence_records = tuple(
        DraftEvidenceRequest._from_extraction(
            id=request.id,
            version=request.version,
            kind=request.kind,
            subject=DraftRef(request.subject.id, request.subject.version),
            question=request.question,
        )
        for request in sorted(evidence, key=lambda item: item.identity)
    )
    return DraftPackage._from_extraction(
        schema=_DRAFT_SCHEMA,
        atoms=atom_records,
        rules=rule_records,
        evidence_requests=evidence_records,
    )


def extract_draft(envelope: GenerationEnvelope) -> ExtractedDraft:
    """Extract exactly one strict draft block or raise canonical diagnostics."""

    if type(envelope) is not GenerationEnvelope:
        raise TypeError("envelope must be an exact GenerationEnvelope")

    issues: list[DraftExtractionIssue] = []
    computed_prompt_digest = _digest(envelope.prompt.data)
    computed_response_digest = _digest(envelope.raw_response.data)
    if envelope.prompt.sha256 != computed_prompt_digest:
        issues.append(
            _issue(
                DraftExtractionCode.CAPTURE_DIGEST_MISMATCH,
                "/prompt",
                (
                    f"stored={envelope.prompt.sha256}",
                    f"computed={computed_prompt_digest}",
                ),
            )
        )
    if envelope.raw_response.sha256 != computed_response_digest:
        issues.append(
            _issue(
                DraftExtractionCode.CAPTURE_DIGEST_MISMATCH,
                "/response",
                (
                    f"stored={envelope.raw_response.sha256}",
                    f"computed={computed_response_digest}",
                ),
            )
        )
    if issues:
        raise DraftExtractionError(tuple(issues))

    if len(envelope.prompt.data) > _RAW_PROMPT_BYTES:
        issues.append(
            _issue(
                DraftExtractionCode.CAPTURE_LIMIT_EXCEEDED,
                "/prompt",
                (
                    "resource=raw_prompt_bytes",
                    f"actual={len(envelope.prompt.data)}",
                    f"limit={_RAW_PROMPT_BYTES}",
                ),
            )
        )
    if len(envelope.raw_response.data) > _RAW_RESPONSE_BYTES:
        issues.append(
            _issue(
                DraftExtractionCode.CAPTURE_LIMIT_EXCEEDED,
                "/response",
                (
                    "resource=raw_response_bytes",
                    f"actual={len(envelope.raw_response.data)}",
                    f"limit={_RAW_RESPONSE_BYTES}",
                ),
            )
        )
    if issues:
        raise DraftExtractionError(tuple(issues))

    try:
        envelope.raw_response.data.decode("utf-8")
    except UnicodeDecodeError:
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.RAW_UTF8, "/response"),)
        ) from None

    payload, block_code = _delimited_payload(envelope.raw_response.data)
    if block_code is not None:
        raise DraftExtractionError((_issue(block_code, "/response"),))
    if payload is None:
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.DRAFT_BLOCK_MISSING, "/response"),)
        )

    if len(payload) > _PAYLOAD_BYTES:
        raise DraftExtractionError(
            (
                _issue(
                    DraftExtractionCode.DRAFT_PAYLOAD_LIMIT,
                    "/response/block",
                    (
                        "resource=payload_bytes",
                        f"actual={len(payload)}",
                        f"limit={_PAYLOAD_BYTES}",
                    ),
                ),
            )
        )
    if _depth_exceeded(payload):
        raise DraftExtractionError(
            (
                _issue(
                    DraftExtractionCode.DRAFT_LIMIT_EXCEEDED,
                    "/response/block",
                    (
                        "resource=json_depth",
                        "actual=65",
                        f"limit={_JSON_DEPTH}",
                    ),
                ),
            )
        )

    try:
        decoded = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_object_pairs,
            parse_int=_integer_token,
            parse_float=_float_token,
            parse_constant=_reject_constant,
        )
    except (ValueError, RecursionError, MemoryError):
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.DRAFT_JSON_INVALID, "/response/block"),)
        ) from None
    if _contains_non_scalar_string(decoded):
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.DRAFT_JSON_INVALID, "/response/block"),)
        )
    duplicate_issues = _duplicate_key_issues(decoded)
    if duplicate_issues:
        raise DraftExtractionError(duplicate_issues)

    if type(decoded) is not _ObjectPairs:
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.DRAFT_ROOT_TYPE, ""),)
        )
    root = _mapping(decoded)
    if "schema" not in root:
        raise DraftExtractionError(
            (
                _issue(
                    DraftExtractionCode.DRAFT_FIELD_MISSING,
                    "/schema",
                ),
            )
        )
    if type(root["schema"]) is not str:
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.DRAFT_VALUE_TYPE, "/schema"),)
        )
    if root["schema"] != _DRAFT_SCHEMA:
        raise DraftExtractionError(
            (
                _issue(
                    DraftExtractionCode.DRAFT_SCHEMA_MISMATCH,
                    "/schema",
                    (f"expected={_DRAFT_SCHEMA}",),
                ),
            )
        )

    issues = []
    root = _shape_fields(
        decoded,
        "",
        frozenset({"schema", "atoms", "rules", "evidence_requests"}),
        issues,
    )
    atoms: list[object] | None = None
    rules: list[object] | None = None
    evidence: list[object] | None = None
    if "atoms" in root:
        atoms = _record_collection(
            root["atoms"],
            "/atoms",
            "atoms",
            _atom_record,
            issues,
        )
    if "rules" in root:
        rules = _record_collection(
            root["rules"],
            "/rules",
            "rules",
            _rule_record,
            issues,
        )
    if "evidence_requests" in root:
        evidence = _record_collection(
            root["evidence_requests"],
            "/evidence_requests",
            "evidence_requests",
            _evidence_record,
            issues,
        )
    if issues:
        raise DraftExtractionError(tuple(issues))
    if atoms is None or rules is None or evidence is None:
        raise DraftExtractionError(
            (_issue(DraftExtractionCode.DRAFT_FIELD_MISSING, ""),)
        )

    atom_data = [item for item in atoms if type(item) is _AtomData]
    rule_data = [item for item in rules if type(item) is _RuleData]
    evidence_data = [item for item in evidence if type(item) is _EvidenceData]

    atom_ids = {atom.identity for atom in atom_data}
    rule_ids = {rule.identity for rule in rule_data}
    evidence_ids = {request.identity for request in evidence_data}
    reference_issues: list[DraftExtractionIssue] = []
    for rule in rule_data:
        head_issue = _reference_issue(
            rule.head,
            atom_ids,
            rule_ids | evidence_ids,
        )
        if head_issue is not None:
            reference_issues.append(head_issue)
        for reference in rule.positive:
            positive_issue = _reference_issue(
                reference,
                atom_ids,
                rule_ids | evidence_ids,
            )
            if positive_issue is not None:
                reference_issues.append(positive_issue)
        request_issue = _reference_issue(
            rule.evidence_request,
            evidence_ids,
            atom_ids | rule_ids,
        )
        if request_issue is not None:
            reference_issues.append(request_issue)
    for request in evidence_data:
        subject_issue = _reference_issue(
            request.subject,
            rule_ids,
            atom_ids | evidence_ids,
        )
        if subject_issue is not None:
            reference_issues.append(subject_issue)
    if reference_issues:
        raise DraftExtractionError(tuple(reference_issues))

    linkage_issues: list[DraftExtractionIssue] = []
    for request in evidence_data:
        users = [
            rule
            for rule in rule_data
            if rule.evidence_request.identity == request.identity
        ]
        if not users:
            linkage_issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_EVIDENCE_BINDING,
                    request.path,
                    ("reason=orphan",),
                )
            )
        elif len(users) > 1:
            linkage_issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_EVIDENCE_BINDING,
                    request.path,
                    ("reason=shared",),
                )
            )
        elif request.subject.identity != users[0].identity:
            linkage_issues.append(
                _issue(
                    DraftExtractionCode.DRAFT_EVIDENCE_BINDING,
                    request.subject.path,
                    ("reason=subject_mismatch",),
                )
            )
    if linkage_issues:
        raise DraftExtractionError(tuple(linkage_issues))

    draft = _materialise(atom_data, rule_data, evidence_data)
    return ExtractedDraft(
        source=envelope,
        payload_sha256=_digest(payload),
        draft=draft,
        _factory=_EXTRACTED_DRAFT_FACTORY,
    )


__all__ = (
    "DraftExtractionCode",
    "DraftExtractionError",
    "DraftExtractionIssue",
    "ExtractedDraft",
    "extract_draft",
)
