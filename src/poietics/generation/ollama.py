"""Pure, injected-transport adapter for Ollama's non-streaming generate API."""

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .model import (
    AttemptRef,
    AttemptRelation,
    GenerationEnvelope,
    capture_generation,
)


_METADATA_BYTE_LIMIT = 4_096
_RESPONSE_BODY_BYTE_LIMIT = 4_194_304
_JSON_DEPTH_LIMIT = 64
_ATTEMPT_SESSION_BYTE_LIMIT = 256
_ATTEMPT_SEQUENCE_LIMIT = 9_223_372_036_854_775_807


class OllamaEndpoint(StrEnum):
    LOCAL = "http://localhost:11434/api/generate"
    CLOUD = "https://ollama.com/api/generate"


@dataclass(frozen=True, slots=True, repr=False)
class OllamaGenerateRequest:
    endpoint: OllamaEndpoint
    attempt: AttemptRef
    relation: AttemptRelation
    parent: AttemptRef | None
    model: str
    prompt_template_id: str
    prompt_template_version: str
    prompt: bytes

    __hash__ = None

    def __post_init__(self) -> None:
        _validate_generate_request(self)
        object.__setattr__(self, "prompt", bytes(self.prompt))


@dataclass(frozen=True, slots=True, repr=False)
class OllamaTransportRequest:
    method: str
    url: str
    content_type: str
    body: bytes

    __hash__ = None

    def __post_init__(self) -> None:
        _validate_transport_request(self)
        object.__setattr__(self, "body", bytes(self.body))


@dataclass(frozen=True, slots=True, repr=False)
class OllamaTransportResponse:
    status: int
    body: bytes

    __hash__ = None

    def __post_init__(self) -> None:
        _validate_transport_response(self)
        object.__setattr__(self, "body", bytes(self.body))


class OllamaTransport(Protocol):
    def __call__(
        self, request: OllamaTransportRequest, /
    ) -> OllamaTransportResponse: ...


class OllamaTransportError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Ollama transport failed")


class OllamaAdapterCode(StrEnum):
    HTTP_STATUS = "ollama_http_status"
    RESPONSE_BODY_LIMIT = "ollama_response_body_limit"
    RESPONSE_UTF8 = "ollama_response_utf8"
    RESPONSE_JSON_INVALID = "ollama_response_json_invalid"
    RESPONSE_JSON_DUPLICATE_KEY = "ollama_response_json_duplicate_key"
    RESPONSE_ROOT_TYPE = "ollama_response_root_type"
    RESPONSE_FIELD_MISSING = "ollama_response_field_missing"
    RESPONSE_SHAPE = "ollama_response_shape"
    PROVIDER_ERROR = "ollama_provider_error"
    RESPONSE_INCOMPLETE = "ollama_response_incomplete"


@dataclass(frozen=True, slots=True)
class OllamaAdapterIssue:
    code: OllamaAdapterCode
    path: str
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.code) is not OllamaAdapterCode:
            raise TypeError("code must be an OllamaAdapterCode")
        if type(self.path) is not str:
            raise TypeError("path must be a string")
        if type(self.details) is not tuple:
            raise TypeError("details must be a tuple")
        for detail in self.details:
            if type(detail) is not str:
                raise TypeError("detail members must be strings")
        if not _is_json_pointer(self.path):
            raise ValueError("path must be a valid JSON pointer")


class OllamaAdapterError(ValueError):
    issues: tuple[OllamaAdapterIssue, ...]

    def __init__(self, issues: tuple[OllamaAdapterIssue, ...]) -> None:
        if type(issues) is not tuple:
            raise TypeError("issues must be a tuple")
        if not issues:
            raise ValueError("issues must not be empty")
        for issue in issues:
            if type(issue) is not OllamaAdapterIssue:
                raise TypeError("issue members must be OllamaAdapterIssue values")
        self.issues = tuple(
            sorted(
                set(issues),
                key=lambda issue: (issue.path, issue.code.value, issue.details),
            )
        )
        super().__init__("Ollama adapter failed")


@dataclass(frozen=True, slots=True)
class _JsonNumber:
    text: str


class _JsonObject(list):
    pass


def _is_scalar_string(value: str) -> bool:
    return all(not 0xD800 <= ord(character) <= 0xDFFF for character in value)


def _validate_text(
    value: object,
    *,
    name: str,
    byte_limit: int,
    allow_empty: bool = False,
) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if (not allow_empty and not value) or not _is_scalar_string(value):
        raise ValueError(f"{name} must be a valid scalar string")
    if len(value.encode("utf-8")) > byte_limit:
        raise ValueError(f"{name} exceeds its UTF-8 byte limit")
    return value


def _validate_attempt_ref(value: AttemptRef, *, name: str) -> None:
    if type(value) is not AttemptRef:
        raise TypeError(f"{name} must be an AttemptRef")
    _validate_text(
        value.session_id,
        name=f"{name}.session_id",
        byte_limit=_ATTEMPT_SESSION_BYTE_LIMIT,
    )
    if type(value.sequence) is not int:
        raise TypeError(f"{name}.sequence must be an integer")
    if not 1 <= value.sequence <= _ATTEMPT_SEQUENCE_LIMIT:
        raise ValueError(f"{name}.sequence is out of range")


def _validate_generate_request(request: OllamaGenerateRequest) -> str:
    if type(request.endpoint) is not OllamaEndpoint:
        raise TypeError("endpoint must be an OllamaEndpoint")
    _validate_attempt_ref(request.attempt, name="attempt")
    if type(request.relation) is not AttemptRelation:
        raise TypeError("relation must be an AttemptRelation")
    if request.parent is not None:
        _validate_attempt_ref(request.parent, name="parent")

    if request.relation is AttemptRelation.INITIAL:
        if request.parent is not None:
            raise ValueError("an initial request must not have a parent")
    else:
        if request.parent is None:
            raise ValueError("a noninitial request must have a parent")
        if request.parent.session_id != request.attempt.session_id:
            raise ValueError("attempt and parent must use the same session")
        if request.parent.sequence >= request.attempt.sequence:
            raise ValueError("parent must precede attempt")

    _validate_text(
        request.model,
        name="model",
        byte_limit=_METADATA_BYTE_LIMIT,
    )
    _validate_text(
        request.prompt_template_id,
        name="prompt_template_id",
        byte_limit=_METADATA_BYTE_LIMIT,
    )
    _validate_text(
        request.prompt_template_version,
        name="prompt_template_version",
        byte_limit=_METADATA_BYTE_LIMIT,
    )
    if type(request.prompt) is not bytes:
        raise TypeError("prompt must be bytes")
    try:
        prompt_text = request.prompt.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("prompt must be strict UTF-8") from None
    if not _is_scalar_string(prompt_text):
        raise ValueError("prompt must contain only Unicode scalar values")
    return prompt_text


def _validate_transport_request(request: OllamaTransportRequest) -> None:
    if type(request.method) is not str:
        raise TypeError("method must be a string")
    if type(request.url) is not str:
        raise TypeError("url must be a string")
    if type(request.content_type) is not str:
        raise TypeError("content_type must be a string")
    if type(request.body) is not bytes:
        raise TypeError("body must be bytes")
    if request.method != "POST":
        raise ValueError("method must be POST")
    if request.url not in (OllamaEndpoint.LOCAL.value, OllamaEndpoint.CLOUD.value):
        raise ValueError("url must be a supported Ollama endpoint")
    if request.content_type != "application/json":
        raise ValueError("content_type must be application/json")


def _validate_transport_response(response: OllamaTransportResponse) -> None:
    if type(response.status) is not int:
        raise TypeError("status must be an integer")
    if not 100 <= response.status <= 599:
        raise ValueError("status must be in 100..599")
    if type(response.body) is not bytes:
        raise TypeError("body must be bytes")


def _is_json_pointer(path: str) -> bool:
    if path and not path.startswith("/"):
        return False
    position = 0
    while position < len(path):
        if path[position] != "~":
            position += 1
            continue
        if position + 1 >= len(path) or path[position + 1] not in "01":
            return False
        position += 2
    return True


def _encode_json_string(value: str) -> bytes:
    encoded = bytearray(b'"')
    for character in value:
        codepoint = ord(character)
        if character == '"':
            encoded.extend(b'\\"')
        elif character == "\\":
            encoded.extend(b"\\\\")
        elif codepoint == 0x08:
            encoded.extend(b"\\b")
        elif codepoint == 0x09:
            encoded.extend(b"\\t")
        elif codepoint == 0x0A:
            encoded.extend(b"\\n")
        elif codepoint == 0x0C:
            encoded.extend(b"\\f")
        elif codepoint == 0x0D:
            encoded.extend(b"\\r")
        elif codepoint <= 0x1F:
            encoded.extend(b"\\u")
            encoded.extend(f"{codepoint:04x}".encode("ascii"))
        else:
            encoded.extend(character.encode("utf-8"))
    encoded.extend(b'"')
    return bytes(encoded)


def _snapshot_generate_request(
    request: OllamaGenerateRequest,
) -> OllamaGenerateRequest:
    attempt = AttemptRef(
        request.attempt.session_id,
        request.attempt.sequence,
    )
    parent = (
        None
        if request.parent is None
        else AttemptRef(
            request.parent.session_id,
            request.parent.sequence,
        )
    )
    return OllamaGenerateRequest(
        endpoint=request.endpoint,
        attempt=attempt,
        relation=request.relation,
        parent=parent,
        model=request.model,
        prompt_template_id=request.prompt_template_id,
        prompt_template_version=request.prompt_template_version,
        prompt=request.prompt,
    )


def _request_body(request: OllamaGenerateRequest, prompt_text: str) -> bytes:
    return (
        b'{"model":'
        + _encode_json_string(request.model)
        + b',"prompt":'
        + _encode_json_string(prompt_text)
        + b',"stream":false}'
    )


def _raise_issue(
    code: OllamaAdapterCode,
    path: str,
    details: tuple[str, ...] = (),
) -> None:
    raise OllamaAdapterError((OllamaAdapterIssue(code, path, details),)) from None


def _reject_nonfinite(token: str) -> object:
    raise ValueError("nonfinite JSON number")


def _exceeds_json_depth(text: str) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _JSON_DEPTH_LIMIT:
                return True
        elif character in "]}" and depth:
            depth -= 1
    return False


def _decode_json(text: str) -> object:
    if text.startswith("\ufeff") or _exceeds_json_depth(text):
        _raise_issue(OllamaAdapterCode.RESPONSE_JSON_INVALID, "/body")
    try:
        return json.loads(
            text,
            object_pairs_hook=_JsonObject,
            parse_int=_JsonNumber,
            parse_float=_JsonNumber,
            parse_constant=_reject_nonfinite,
        )
    except (ValueError, RecursionError):
        _raise_issue(OllamaAdapterCode.RESPONSE_JSON_INVALID, "/body")
    raise AssertionError("unreachable JSON decoder state")


def _json_scalars_are_valid(root: object) -> bool:
    pending = [root]
    while pending:
        value = pending.pop()
        if type(value) is str:
            if not _is_scalar_string(value):
                return False
        elif type(value) is _JsonObject:
            for key, member in value:
                if type(key) is not str or not _is_scalar_string(key):
                    return False
                pending.append(member)
        elif type(value) is list:
            pending.extend(value)
    return True


def _json_has_duplicate_key(root: object) -> bool:
    pending = [root]
    duplicate = False
    while pending:
        value = pending.pop()
        if type(value) is _JsonObject:
            seen: set[str] = set()
            for key, member in value:
                if key in seen:
                    duplicate = True
                else:
                    seen.add(key)
                pending.append(member)
        elif type(value) is list:
            pending.extend(value)
    return duplicate


def _response_object(body: bytes) -> _JsonObject:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _raise_issue(OllamaAdapterCode.RESPONSE_UTF8, "/body")
    root = _decode_json(text)
    if not _json_scalars_are_valid(root):
        _raise_issue(OllamaAdapterCode.RESPONSE_JSON_INVALID, "/body")
    if _json_has_duplicate_key(root):
        _raise_issue(OllamaAdapterCode.RESPONSE_JSON_DUPLICATE_KEY, "/body")
    if type(root) is not _JsonObject:
        _raise_issue(OllamaAdapterCode.RESPONSE_ROOT_TYPE, "/body")
    return root


def _shape_issues(values: dict[str, object]) -> tuple[OllamaAdapterIssue, ...]:
    issues: list[OllamaAdapterIssue] = []
    expected = {
        "model": (
            "expected=nonempty_scalar_string",
            "limit=4096",
        ),
        "response": ("expected=scalar_string",),
        "done": ("expected=boolean",),
    }
    for field in ("model", "response", "done"):
        if field not in values:
            issues.append(
                OllamaAdapterIssue(
                    OllamaAdapterCode.RESPONSE_FIELD_MISSING,
                    f"/body/{field}",
                )
            )
            continue
        value = values[field]
        valid = False
        if field == "model":
            valid = (
                type(value) is str
                and bool(value)
                and len(value.encode("utf-8")) <= _METADATA_BYTE_LIMIT
            )
        elif field == "response":
            valid = type(value) is str
        else:
            valid = type(value) is bool
        if not valid:
            issues.append(
                OllamaAdapterIssue(
                    OllamaAdapterCode.RESPONSE_SHAPE,
                    f"/body/{field}",
                    expected[field],
                )
            )

    if "done_reason" in values and values["done_reason"] is not None:
        reason = values["done_reason"]
        if not (
            type(reason) is str
            and bool(reason)
            and len(reason.encode("utf-8")) <= _METADATA_BYTE_LIMIT
        ):
            issues.append(
                OllamaAdapterIssue(
                    OllamaAdapterCode.RESPONSE_SHAPE,
                    "/body/done_reason",
                    (
                        "expected=null_or_nonempty_scalar_string",
                        "limit=4096",
                    ),
                )
            )
    return tuple(issues)


def generate_ollama(
    request: OllamaGenerateRequest,
    *,
    transport: OllamaTransport,
) -> GenerationEnvelope:
    if type(request) is not OllamaGenerateRequest:
        raise TypeError("request must be an OllamaGenerateRequest")
    _validate_generate_request(request)
    if not callable(transport):
        raise TypeError("transport must be callable")
    source = _snapshot_generate_request(request)
    prompt_text = _validate_generate_request(source)

    transport_request = OllamaTransportRequest(
        method="POST",
        url=source.endpoint.value,
        content_type="application/json",
        body=_request_body(source, prompt_text),
    )
    response = transport(transport_request)
    if type(response) is not OllamaTransportResponse:
        raise TypeError("transport must return an OllamaTransportResponse")
    _validate_transport_response(response)

    if response.status != 200:
        _raise_issue(
            OllamaAdapterCode.HTTP_STATUS,
            "/status",
            (f"status={response.status}",),
        )
    if len(response.body) > _RESPONSE_BODY_BYTE_LIMIT:
        _raise_issue(
            OllamaAdapterCode.RESPONSE_BODY_LIMIT,
            "/body",
            (
                "resource=response_body_bytes",
                f"actual={len(response.body)}",
                "limit=4194304",
            ),
        )

    root = _response_object(response.body)
    values = dict(root)
    if "error" in values:
        error = values["error"]
        if type(error) is str and bool(error):
            _raise_issue(OllamaAdapterCode.PROVIDER_ERROR, "/body/error")
        _raise_issue(
            OllamaAdapterCode.RESPONSE_SHAPE,
            "/body/error",
            ("expected=nonempty_scalar_string",),
        )

    issues = _shape_issues(values)
    if issues:
        raise OllamaAdapterError(issues)
    if values["done"] is False:
        _raise_issue(OllamaAdapterCode.RESPONSE_INCOMPLETE, "/body/done")

    provider_id = (
        "ollama-local"
        if source.endpoint is OllamaEndpoint.LOCAL
        else "ollama-cloud"
    )
    return capture_generation(
        attempt=source.attempt,
        relation=source.relation,
        parent=source.parent,
        provider_id=provider_id,
        adapter_id="ollama-generate",
        adapter_version="1",
        requested_model=source.model,
        reported_model=values["model"],
        prompt_template_id=source.prompt_template_id,
        prompt_template_version=source.prompt_template_version,
        prompt=source.prompt,
        public_parameters={"stream": "false"},
        raw_response=values["response"].encode("utf-8"),
        finish_reason=values.get("done_reason"),
        provider_request_id=None,
    )
