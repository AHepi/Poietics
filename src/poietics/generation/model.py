"""Immutable, provider-neutral generation capture and draft records."""

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256


_MAX_INTEGER = 9_223_372_036_854_775_807
_SESSION_ID_BYTES = 256
_PARAMETER_NAME_BYTES = 256
_METADATA_BYTES = 4_096
_DRAFT_STRING_BYTES = 262_144
_MAX_PUBLIC_PARAMETERS = 256
_ENVELOPE_PROFILE = "pff-generation/0.1"
_DRAFT_SCHEMA = "pff-draft/0.1"
_FACTORY_TOKEN = object()


def _require_exact_string(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    return value


def _require_scalar_string(
    value: object,
    field: str,
    *,
    maximum_bytes: int,
    allow_empty: bool,
) -> str:
    text = _require_exact_string(value, field)
    if not allow_empty and not text:
        raise ValueError(f"{field} must not be empty")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in text):
        raise ValueError(f"{field} must contain only Unicode scalar values")
    if len(text.encode("utf-8")) > maximum_bytes:
        raise ValueError(f"{field} exceeds its UTF-8 byte limit")
    return text


def _require_optional_scalar_string(
    value: object,
    field: str,
    *,
    maximum_bytes: int,
) -> str | None:
    if value is None:
        return None
    return _require_scalar_string(
        value,
        field,
        maximum_bytes=maximum_bytes,
        allow_empty=False,
    )


def _require_positive_integer(value: object, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an exact int")
    if value < 1 or value > _MAX_INTEGER:
        raise ValueError(f"{field} is outside the supported range")
    return value


def _require_draft_identifier(value: object, field: str) -> str:
    identifier = _require_scalar_string(
        value,
        field,
        maximum_bytes=_DRAFT_STRING_BYTES,
        allow_empty=False,
    )
    if identifier.startswith("__pff__:"):
        raise ValueError(f"{field} uses the reserved compiler prefix")
    return identifier


def _content_digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


class AttemptRelation(StrEnum):
    INITIAL = "initial"
    RETRY = "retry"
    REPAIR = "repair"
    EXTRACT = "extract"


@dataclass(frozen=True, slots=True, order=True)
class AttemptRef:
    session_id: str
    sequence: int

    def __post_init__(self) -> None:
        _require_scalar_string(
            self.session_id,
            "session_id",
            maximum_bytes=_SESSION_ID_BYTES,
            allow_empty=False,
        )
        _require_positive_integer(self.sequence, "sequence")


@dataclass(frozen=True, slots=True, init=False)
class CapturedContent:
    data: bytes
    sha256: str

    def __init__(
        self,
        data: bytes,
        sha256: str,
        *,
        _token: object | None = None,
    ) -> None:
        if _token is not _FACTORY_TOKEN:
            raise TypeError("CapturedContent is factory-only")
        if type(data) is not bytes:
            raise TypeError("data must be exact bytes")
        if type(sha256) is not str:
            raise TypeError("sha256 must be an exact str")
        if sha256 != _content_digest(data):
            raise ValueError("sha256 does not match data")
        object.__setattr__(self, "data", bytes(data))
        object.__setattr__(self, "sha256", sha256)


@dataclass(frozen=True, slots=True, order=True)
class GenerationParameter:
    name: str
    value: str

    def __post_init__(self) -> None:
        _require_scalar_string(
            self.name,
            "name",
            maximum_bytes=_PARAMETER_NAME_BYTES,
            allow_empty=False,
        )
        _require_scalar_string(
            self.value,
            "value",
            maximum_bytes=_METADATA_BYTES,
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True, init=False)
class GenerationEnvelope:
    profile: str
    attempt: AttemptRef
    relation: AttemptRelation
    parent: AttemptRef | None
    provider_id: str
    adapter_id: str
    adapter_version: str
    requested_model: str
    reported_model: str | None
    prompt_template_id: str
    prompt_template_version: str
    prompt: CapturedContent
    public_parameters: tuple[GenerationParameter, ...]
    raw_response: CapturedContent
    finish_reason: str | None
    provider_request_id: str | None

    __hash__ = None

    def __init__(
        self,
        *,
        profile: str,
        attempt: AttemptRef,
        relation: AttemptRelation,
        parent: AttemptRef | None,
        provider_id: str,
        adapter_id: str,
        adapter_version: str,
        requested_model: str,
        reported_model: str | None,
        prompt_template_id: str,
        prompt_template_version: str,
        prompt: CapturedContent,
        public_parameters: tuple[GenerationParameter, ...],
        raw_response: CapturedContent,
        finish_reason: str | None,
        provider_request_id: str | None,
        _token: object | None = None,
    ) -> None:
        if _token is not _FACTORY_TOKEN:
            raise TypeError("GenerationEnvelope is factory-only")
        if type(profile) is not str:
            raise TypeError("profile must be an exact str")
        if profile != _ENVELOPE_PROFILE:
            raise ValueError("unsupported generation profile")
        if type(attempt) is not AttemptRef:
            raise TypeError("attempt must be an exact AttemptRef")
        if type(relation) is not AttemptRelation:
            raise TypeError("relation must be an exact AttemptRelation")
        if parent is not None and type(parent) is not AttemptRef:
            raise TypeError("parent must be None or an exact AttemptRef")
        if relation is AttemptRelation.INITIAL:
            if parent is not None:
                raise ValueError("an initial attempt must not have a parent")
        elif parent is None:
            raise ValueError("a non-initial attempt requires a parent")
        elif (
            parent.session_id != attempt.session_id
            or parent.sequence >= attempt.sequence
        ):
            raise ValueError("parent must be an earlier attempt in the same session")

        required_metadata = (
            ("provider_id", provider_id),
            ("adapter_id", adapter_id),
            ("adapter_version", adapter_version),
            ("requested_model", requested_model),
            ("prompt_template_id", prompt_template_id),
            ("prompt_template_version", prompt_template_version),
        )
        for field, value in required_metadata:
            _require_scalar_string(
                value,
                field,
                maximum_bytes=_METADATA_BYTES,
                allow_empty=False,
            )
        _require_optional_scalar_string(
            reported_model,
            "reported_model",
            maximum_bytes=_METADATA_BYTES,
        )
        _require_optional_scalar_string(
            finish_reason,
            "finish_reason",
            maximum_bytes=_METADATA_BYTES,
        )
        _require_optional_scalar_string(
            provider_request_id,
            "provider_request_id",
            maximum_bytes=_METADATA_BYTES,
        )
        if type(prompt) is not CapturedContent:
            raise TypeError("prompt must be an exact CapturedContent")
        if type(raw_response) is not CapturedContent:
            raise TypeError("raw_response must be an exact CapturedContent")
        if type(public_parameters) is not tuple:
            raise TypeError("public_parameters must be an exact tuple")
        if len(public_parameters) > _MAX_PUBLIC_PARAMETERS:
            raise ValueError("too many public parameters")
        if any(type(parameter) is not GenerationParameter for parameter in public_parameters):
            raise TypeError("public_parameters must contain exact GenerationParameter values")
        if tuple(sorted(public_parameters, key=lambda item: item.name)) != public_parameters:
            raise ValueError("public_parameters must be sorted by name")
        if len({parameter.name for parameter in public_parameters}) != len(public_parameters):
            raise ValueError("public parameter names must be unique")

        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "attempt", attempt)
        object.__setattr__(self, "relation", relation)
        object.__setattr__(self, "parent", parent)
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "adapter_id", adapter_id)
        object.__setattr__(self, "adapter_version", adapter_version)
        object.__setattr__(self, "requested_model", requested_model)
        object.__setattr__(self, "reported_model", reported_model)
        object.__setattr__(self, "prompt_template_id", prompt_template_id)
        object.__setattr__(self, "prompt_template_version", prompt_template_version)
        object.__setattr__(self, "prompt", prompt)
        object.__setattr__(self, "public_parameters", tuple(public_parameters))
        object.__setattr__(self, "raw_response", raw_response)
        object.__setattr__(self, "finish_reason", finish_reason)
        object.__setattr__(self, "provider_request_id", provider_request_id)


def capture_generation(
    *,
    attempt: AttemptRef,
    relation: AttemptRelation,
    parent: AttemptRef | None,
    provider_id: str,
    adapter_id: str,
    adapter_version: str,
    requested_model: str,
    reported_model: str | None,
    prompt_template_id: str,
    prompt_template_version: str,
    prompt: bytes,
    public_parameters: dict[str, str],
    raw_response: bytes,
    finish_reason: str | None = None,
    provider_request_id: str | None = None,
) -> GenerationEnvelope:
    """Capture one immutable generation attempt without interpreting its bytes."""

    if type(attempt) is not AttemptRef:
        raise TypeError("attempt must be an exact AttemptRef")
    if type(relation) is not AttemptRelation:
        raise TypeError("relation must be an exact AttemptRelation")
    if parent is not None and type(parent) is not AttemptRef:
        raise TypeError("parent must be None or an exact AttemptRef")
    if type(prompt) is not bytes:
        raise TypeError("prompt must be exact bytes")
    if type(raw_response) is not bytes:
        raise TypeError("raw_response must be exact bytes")
    if type(public_parameters) is not dict:
        raise TypeError("public_parameters must be an exact dict")
    if len(public_parameters) > _MAX_PUBLIC_PARAMETERS:
        raise ValueError("too many public parameters")

    parameters = tuple(
        sorted(
            (
                GenerationParameter(name=name, value=value)
                for name, value in public_parameters.items()
            ),
            key=lambda item: item.name,
        )
    )
    prompt_content = CapturedContent(
        bytes(prompt),
        _content_digest(prompt),
        _token=_FACTORY_TOKEN,
    )
    response_content = CapturedContent(
        bytes(raw_response),
        _content_digest(raw_response),
        _token=_FACTORY_TOKEN,
    )
    return GenerationEnvelope(
        profile=_ENVELOPE_PROFILE,
        attempt=attempt,
        relation=relation,
        parent=parent,
        provider_id=provider_id,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        requested_model=requested_model,
        reported_model=reported_model,
        prompt_template_id=prompt_template_id,
        prompt_template_version=prompt_template_version,
        prompt=prompt_content,
        public_parameters=parameters,
        raw_response=response_content,
        finish_reason=finish_reason,
        provider_request_id=provider_request_id,
        _token=_FACTORY_TOKEN,
    )


@dataclass(frozen=True, slots=True, order=True)
class DraftRef:
    id: str
    version: int

    def __post_init__(self) -> None:
        _require_draft_identifier(self.id, "id")
        _require_positive_integer(self.version, "version")


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftAtom:
    id: str
    version: int
    predicate: str
    args: tuple[str, ...]
    frame: str
    grade: str | None

    def __init__(
        self,
        *,
        id: str,
        version: int,
        predicate: str,
        args: tuple[str, ...],
        frame: str,
        grade: str | None,
        _token: object | None = None,
    ) -> None:
        if _token is not _FACTORY_TOKEN:
            raise TypeError("DraftAtom is extraction-only")
        _require_draft_identifier(id, "id")
        _require_positive_integer(version, "version")
        _require_scalar_string(
            predicate,
            "predicate",
            maximum_bytes=_DRAFT_STRING_BYTES,
            allow_empty=False,
        )
        if type(args) is not tuple:
            raise TypeError("args must be an exact tuple")
        for argument in args:
            _require_scalar_string(
                argument,
                "argument",
                maximum_bytes=_DRAFT_STRING_BYTES,
                allow_empty=True,
            )
        _require_scalar_string(
            frame,
            "frame",
            maximum_bytes=_DRAFT_STRING_BYTES,
            allow_empty=False,
        )
        if grade is not None:
            _require_scalar_string(
                grade,
                "grade",
                maximum_bytes=_DRAFT_STRING_BYTES,
                allow_empty=True,
            )
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "predicate", predicate)
        object.__setattr__(self, "args", tuple(args))
        object.__setattr__(self, "frame", frame)
        object.__setattr__(self, "grade", grade)

    @classmethod
    def _from_extraction(
        cls,
        *,
        id: str,
        version: int,
        predicate: str,
        args: tuple[str, ...],
        frame: str,
        grade: str | None,
    ) -> "DraftAtom":
        if cls is not DraftAtom:
            raise TypeError("DraftAtom subclasses are not supported")
        return cls(
            id=id,
            version=version,
            predicate=predicate,
            args=args,
            frame=frame,
            grade=grade,
            _token=_FACTORY_TOKEN,
        )


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftRule:
    id: str
    version: int
    head: DraftRef
    positive: frozenset[DraftRef]
    evidence_request: DraftRef

    def __init__(
        self,
        *,
        id: str,
        version: int,
        head: DraftRef,
        positive: frozenset[DraftRef],
        evidence_request: DraftRef,
        _token: object | None = None,
    ) -> None:
        if _token is not _FACTORY_TOKEN:
            raise TypeError("DraftRule is extraction-only")
        _require_draft_identifier(id, "id")
        _require_positive_integer(version, "version")
        if type(head) is not DraftRef:
            raise TypeError("head must be an exact DraftRef")
        if type(positive) is not frozenset:
            raise TypeError("positive must be an exact frozenset")
        if any(type(reference) is not DraftRef for reference in positive):
            raise TypeError("positive must contain exact DraftRef values")
        if type(evidence_request) is not DraftRef:
            raise TypeError("evidence_request must be an exact DraftRef")
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "head", head)
        object.__setattr__(self, "positive", frozenset(positive))
        object.__setattr__(self, "evidence_request", evidence_request)

    @classmethod
    def _from_extraction(
        cls,
        *,
        id: str,
        version: int,
        head: DraftRef,
        positive: frozenset[DraftRef],
        evidence_request: DraftRef,
    ) -> "DraftRule":
        if cls is not DraftRule:
            raise TypeError("DraftRule subclasses are not supported")
        return cls(
            id=id,
            version=version,
            head=head,
            positive=positive,
            evidence_request=evidence_request,
            _token=_FACTORY_TOKEN,
        )


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftEvidenceRequest:
    id: str
    version: int
    kind: str
    subject: DraftRef
    question: str

    def __init__(
        self,
        *,
        id: str,
        version: int,
        kind: str,
        subject: DraftRef,
        question: str,
        _token: object | None = None,
    ) -> None:
        if _token is not _FACTORY_TOKEN:
            raise TypeError("DraftEvidenceRequest is extraction-only")
        _require_draft_identifier(id, "id")
        _require_positive_integer(version, "version")
        _require_scalar_string(
            kind,
            "kind",
            maximum_bytes=_DRAFT_STRING_BYTES,
            allow_empty=False,
        )
        if kind != "certificate":
            raise ValueError("unsupported evidence request kind")
        if type(subject) is not DraftRef:
            raise TypeError("subject must be an exact DraftRef")
        _require_scalar_string(
            question,
            "question",
            maximum_bytes=_DRAFT_STRING_BYTES,
            allow_empty=False,
        )
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "question", question)

    @classmethod
    def _from_extraction(
        cls,
        *,
        id: str,
        version: int,
        kind: str,
        subject: DraftRef,
        question: str,
    ) -> "DraftEvidenceRequest":
        if cls is not DraftEvidenceRequest:
            raise TypeError("DraftEvidenceRequest subclasses are not supported")
        return cls(
            id=id,
            version=version,
            kind=kind,
            subject=subject,
            question=question,
            _token=_FACTORY_TOKEN,
        )


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftPackage:
    schema: str
    atoms: tuple[DraftAtom, ...]
    rules: tuple[DraftRule, ...]
    evidence_requests: tuple[DraftEvidenceRequest, ...]

    def __init__(
        self,
        *,
        schema: str,
        atoms: tuple[DraftAtom, ...],
        rules: tuple[DraftRule, ...],
        evidence_requests: tuple[DraftEvidenceRequest, ...],
        _token: object | None = None,
    ) -> None:
        if _token is not _FACTORY_TOKEN:
            raise TypeError("DraftPackage is extraction-only")
        if type(schema) is not str:
            raise TypeError("schema must be an exact str")
        if schema != _DRAFT_SCHEMA:
            raise ValueError("unsupported draft schema")
        if type(atoms) is not tuple:
            raise TypeError("atoms must be an exact tuple")
        if any(type(atom) is not DraftAtom for atom in atoms):
            raise TypeError("atoms must contain exact DraftAtom values")
        if type(rules) is not tuple:
            raise TypeError("rules must be an exact tuple")
        if any(type(rule) is not DraftRule for rule in rules):
            raise TypeError("rules must contain exact DraftRule values")
        if type(evidence_requests) is not tuple:
            raise TypeError("evidence_requests must be an exact tuple")
        if any(
            type(request) is not DraftEvidenceRequest
            for request in evidence_requests
        ):
            raise TypeError(
                "evidence_requests must contain exact DraftEvidenceRequest values"
            )
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "atoms", tuple(atoms))
        object.__setattr__(self, "rules", tuple(rules))
        object.__setattr__(
            self,
            "evidence_requests",
            tuple(evidence_requests),
        )

    @classmethod
    def _from_extraction(
        cls,
        *,
        schema: str,
        atoms: tuple[DraftAtom, ...],
        rules: tuple[DraftRule, ...],
        evidence_requests: tuple[DraftEvidenceRequest, ...],
    ) -> "DraftPackage":
        if cls is not DraftPackage:
            raise TypeError("DraftPackage subclasses are not supported")
        return cls(
            schema=schema,
            atoms=atoms,
            rules=rules,
            evidence_requests=evidence_requests,
            _token=_FACTORY_TOKEN,
        )


__all__ = (
    "AttemptRef",
    "AttemptRelation",
    "CapturedContent",
    "DraftAtom",
    "DraftEvidenceRequest",
    "DraftPackage",
    "DraftRef",
    "DraftRule",
    "GenerationEnvelope",
    "GenerationParameter",
    "capture_generation",
)
