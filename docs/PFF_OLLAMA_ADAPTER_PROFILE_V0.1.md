# PFF Ollama Adapter Profile v0.1

**Status:** ACCEPTED  
**Scope:** pure injected-transport Ollama `/api/generate` adapter only  
**Repository baseline:** `f1fda2e4f6109975d2b0c6bc01321fceda903761`  
**Controlling capture profile:** `PFF_GENERATION_CAPTURE_PROFILE_V0.1.md`,
SHA-256 `bdda03645aec07681dd817244cfb7ab4981102090c0f3bf17cc70cbf1676bfa4`

## 1. Purpose, authority, and rule provenance

This candidate freezes one narrow adapter above the accepted generation
capture boundary:

```text
OllamaGenerateRequest
    -> exact code-owned JSON request bytes
    -> one injected transport call
    -> strict provider-response validation
    -> GenerationEnvelope
```

It does not add Ollama, HTTP, credential, extraction, PFF, compiler, or ground
dependencies. The adapter never calls `extract_draft`; callers may pass the
successful envelope to the existing extractor later.

The authority order is:

1. the accepted generation capture profile controls `AttemptRef`, lineage,
   capture metadata, captured bytes, and `GenerationEnvelope` construction;
2. this profile controls the adapter API, exact request bytes, transport seam,
   response classification, diagnostics, and envelope mapping; and
3. the dated Ollama documentation in section 12 is evidence about the provider,
   not semantic authority over this adapter.

Rule provenance is:

| Tag | Population |
|---|---|
| `[S]` | Exact capture-model types, constraints, byte retention, lineage, and factory use restated from the accepted profile. |
| `[N]` | Every endpoint, identifier, request byte, transport, response, limit, diagnostic, ordering, and fixture choice introduced here. Ollama does not document these client-policy details completely. |
| `[D]` | Concrete HTTP, environment/key loading, persistence and durable/session replay, automatic retry, extraction, binding, and live tests deferred by section 13. |

There are no `[C]` rules. This candidate is not authority until independently
reviewed, accepted, and published. Its profile identity is
`pff-ollama-adapter/0.1`.

## 2. Public API

The later implementation exposes these exact names from
`poietics.generation.ollama`. The package initializer remains inert.

```python
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

@dataclass(frozen=True, slots=True, repr=False)
class OllamaTransportRequest:
    method: str
    url: str
    content_type: str
    body: bytes

    __hash__ = None

@dataclass(frozen=True, slots=True, repr=False)
class OllamaTransportResponse:
    status: int
    body: bytes

    __hash__ = None

class OllamaTransport(Protocol):
    def __call__(
        self, request: OllamaTransportRequest, /
    ) -> OllamaTransportResponse: ...

class OllamaTransportError(RuntimeError):
    def __init__(self) -> None: ...

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

class OllamaAdapterError(ValueError):
    issues: tuple[OllamaAdapterIssue, ...]

def generate_ollama(
    request: OllamaGenerateRequest,
    *,
    transport: OllamaTransport,
) -> GenerationEnvelope:
    ...
```

The adapter-owned request and transport records are deeply immutable. Exact
bytes are retained, no mutable container is stored, field assignment fails,
and these records are unhashable. Their generated `repr` is disabled so prompt,
request-body, and response-body bytes are not displayed accidentally. Equality
still compares every declared field exactly. The accepted capture model is not
changed: inherited `GenerationEnvelope` and `CapturedContent` reprs may display
retained prompt or assistant bytes and therefore must not be logged.

## 3. Request construction and prevalidation

`OllamaGenerateRequest` ordinary construction and `generate_ollama` immediately
before transport both enforce the same rules. `generate_ollama` first requires
`type(request) is OllamaGenerateRequest`; a subclass, mapping, or duck type
raises `TypeError`. Rechecking closes low-level slot corruption and guarantees
that no invalid request is sent. Every such failure has zero sends and zero
capture calls; transport-request construction timing is not observable here.

- `endpoint`, `attempt`, and `relation` require their exact declared classes;
  subclasses and duck types raise `TypeError`.
- `parent` is `None` or an exact `AttemptRef`.
- An `INITIAL` request has no parent. Every other relation has an earlier parent
  in the same session. Violations raise `ValueError`.
- `model`, `prompt_template_id`, and `prompt_template_version` are exact,
  nonempty Unicode-scalar strings of at most 4,096 UTF-8 bytes. Wrong exact
  types raise `TypeError`; value violations raise `ValueError`.
- `prompt` is exact `bytes`. It must strictly decode as UTF-8 and every decoded
  character must be a Unicode scalar value. Empty prompt bytes and a leading
  UTF-8 BOM are retained as content and are allowed. Invalid UTF-8 raises
  `ValueError`; `bytearray`, subclasses, and other types raise `TypeError`.
- There is no adapter request-byte or prompt-byte limit. `[S]` Capture retains
  an oversized prompt; later extraction applies the accepted 1,048,576-byte
  prompt limit. The adapter never truncates it.
- `transport` must be callable. A non-callable raises `TypeError` with zero
  sends and zero capture calls; transport-request construction is not observed.

The caller supplies a fresh `AttemptRef` for every invocation, including a
retry. This single-call API cannot prove session-wide freshness; it never
rewrites the attempt, relation, or parent.

After prevalidation, the adapter creates exactly one
`OllamaTransportRequest` with:

```text
method       = "POST"
url          = request.endpoint.value
content_type = "application/json"
body         = exact bytes from section 4
```

The transport-request constructor accepts only exact strings and exact bytes,
requires those three fixed metadata values, permits only the two endpoint URLs,
and copies `body`. Any other direct construction raises `TypeError` or
`ValueError` as applicable.

`OllamaTransportResponse` accepts an exact integer status in `100..599` and
exact body bytes, copies the body, and applies no body-size check. `bool`, int
subclasses, bytes subclasses, and duck types raise `TypeError`; an out-of-range
status raises `ValueError`. Keeping the size check out of this constructor is
required for status-before-size precedence.

## 4. Exact request JSON bytes

The request body is exactly this object, with keys in this order and with no
other member:

```json
{"model":MODEL,"prompt":PROMPT,"stream":false}
```

There is no space, indentation, optional slash escape, BOM, or final LF.
`MODEL` is the JSON string encoding of `request.model`. `PROMPT` is the same
encoding of the strictly decoded prompt string. The encoder is defined over
Unicode scalar values as follows:

1. emit opening and closing ASCII double quotes;
2. encode `"` as `\"` and `\` as `\\`;
3. encode U+0008, U+0009, U+000A, U+000C, and U+000D respectively as
   `\b`, `\t`, `\n`, `\f`, and `\r`;
4. encode every other U+0000..U+001F scalar as `\u` plus four lowercase
   hexadecimal digits; and
5. encode every other scalar directly as its shortest UTF-8 byte sequence.

In particular `/`, U+2028, and U+2029 are not escaped; non-ASCII scalars are
not ASCII-escaped; astral scalars are not encoded as surrogate pairs; and no
Unicode normalization, case folding, or newline conversion occurs.

The fixed scalar vectors are:

| Input scalar sequence | Exact JSON token bytes |
|---|---|
| empty | `""` |
| `"` | `"\""` |
| `\` | `"\\"` |
| U+0000, U+001F | `"\u0000\u001f"` |
| LF | `"\n"` |
| `/` | `"/"` |
| U+00E9 | UTF-8 bytes `22 c3 a9 22` |
| U+2028 | UTF-8 bytes `22 e2 80 a8 22` |
| U+1F600 | UTF-8 bytes `22 f0 9f 98 80 22` |

No Ollama `options`, `format`, `system`, `think`, `raw`, `keep_alive`, image,
suffix, or log-probability field is sent. `[N]` This tranche always requests
the documented non-streaming form with exact JSON boolean `false`.

## 5. Transport authority and one-send rule

The adapter invokes the supplied transport exactly once with the one immutable
transport request. It never retries, follows a redirect, sleeps, changes an
endpoint, or calls a second transport. A conforming future concrete transport
must likewise perform one POST and must disable library-level retries and
automatic redirect following. Those concrete mechanics are deferred.

The injected transport has exactly three permitted outcomes:

1. return an exact `OllamaTransportResponse`;
2. raise an exact `OllamaTransportError`; or
3. violate its contract by returning another value or raising another
   exception.

`OllamaTransportError()` takes no arguments and has the fixed text
`Ollama transport failed`. The adapter propagates that exact exception object,
unchanged and without retry. Any other exception also propagates unchanged.
A non-exact return raises `TypeError`. After an exact return-type check, the
adapter revalidates the returned record before the HTTP gate: `status` must be
an exact `int` rather than `bool` and lie in `100..599`, and `body` must be exact
`bytes`. Wrong exact types raise `TypeError`; an out-of-range status raises
`ValueError`. This repeat validation closes low-level mutation after ordinary
construction. Every failure produces no envelope, and `capture_generation`
has not been called.

The adapter does not catch, inspect, log, wrap, or attach request/response bytes
to transport exceptions. An injected transport owns the safety of unexpected
exceptions it raises.

Call cardinality is observable and exact:

| Outcome | Transport sends | `capture_generation` calls |
|---|---:|---:|
| request exact-type/prevalidation failure or non-callable transport | 0 | 0 |
| typed or unexpected transport exception, non-exact return, or corrupted exact response | 1 | 0 |
| any response failure after an exact transport response | 1 | 0 |
| success | 1 | 1 |

No row permits retry, a second send, early capture, or a partial envelope.

## 6. Strict response document

The maximum transport response body is 4,194,304 bytes inclusive. A successful
status body must be one complete RFC 8259 JSON value with only JSON whitespace
outside it. UTF-8 is strict; a BOM, invalid sequence, trailing value, `NaN`,
`Infinity`, or `-Infinity` is invalid.

Every decoded JSON key and string value, including one below an unknown field,
must contain only Unicode scalar values. A literal or escaped lone surrogate is
invalid. Every object at every depth must have unique keys. Unknown fields and
their values are otherwise inert after whole-document syntax, scalar, and
duplicate validation; they create no shape issue and no typed output.

To make the standard-library implementation bounded, JSON nesting has an
inclusive maximum of 64 using the accepted capture profile's lexical depth
definition: the root object is depth 1, `{` and `[` outside strings increment,
and quoted brackets do not. Attempted depth 65 is
`RESPONSE_JSON_INVALID`. This is not a second public limit diagnostic.

Every JSON integer and finite float is initially retained as an opaque lexical
token rather than converted through an interpreter numeric type. Known fields
reject numeric tokens by shape; valid unknown fields are ignored without
numeric conversion. In particular, a valid 5,000-digit integer below an
unknown field is accepted and cannot depend on an ambient integer-digit limit.

After whole-document validity, the root must be an object. Field names are
case-sensitive. The exact `error` member selects the error branch:

- present as an exact nonempty scalar string: provider error, regardless of
  missing or malformed success fields;
- present as empty string, null, boolean, number, array, or object: one shape
  issue at `/body/error`; and
- absent: validate the success branch.

The success branch has these fields. Unknown siblings remain inert.

| Field | Requirement | Mapping |
|---|---|---|
| `model` | required, nonempty scalar string, at most 4,096 UTF-8 bytes | `reported_model` |
| `response` | required scalar string; empty allowed | strict UTF-8 bytes become captured `raw_response` |
| `done` | required exact JSON boolean | `false` is incomplete; `true` continues |
| `done_reason` | absent or null, otherwise nonempty scalar string at most 4,096 UTF-8 bytes | `finish_reason` or `None` |

All success-branch missing and malformed-field issues aggregate. If any exists,
incompleteness is not tested. When shape is valid, `done=false` yields only the
incomplete issue. There is no truthy coercion.

The reported model need not equal the requested model. A mismatch is retained
exactly in the envelope and is neither repaired nor rejected.

## 7. Diagnostic contract and precedence

Paths are RFC 6901 JSON Pointers over the transport response abstraction:
`/status`, `/body`, and `/body/<field>`. No submitted value or unknown member
name enters a path.

`OllamaAdapterIssue` requires the exact enum, an exact valid pointer string, and
an exact tuple of exact strings. Wrong types raise `TypeError`; invalid pointer
syntax raises `ValueError`. `OllamaAdapterError` accepts one exact nonempty tuple
of exact issues, exact-deduplicates it, and sorts it by
`(path, code.value, details)`. Its `issues` tuple is the sole normative payload;
human text is non-normative, fixed by the implementation, and contains no
submitted bytes or values.

The response gates are absolute:

1. HTTP status;
2. response-body byte limit;
3. strict UTF-8;
4. JSON syntax, finite-token validity, and depth;
5. Unicode-scalar validity;
6. duplicate keys;
7. root type;
8. `error` branch selection;
9. success shape; and
10. completion.

One gate's failure suppresses every later gate. Shape is the only aggregating
gate. Exact diagnostics are:

| Code | Gate and path | Exact details |
|---|---|---|
| `HTTP_STATUS` | status other than exact 200, `/status` | `("status=N",)` |
| `RESPONSE_BODY_LIMIT` | length 4,194,305 or greater, `/body` | `("resource=response_body_bytes", "actual=N", "limit=4194304")` |
| `RESPONSE_UTF8` | strict decode failure, `/body` | `()` |
| `RESPONSE_JSON_INVALID` | syntax, nonfinite token, depth 65, BOM, trailing data, or non-scalar string, `/body` | `()` |
| `RESPONSE_JSON_DUPLICATE_KEY` | one or more duplicate keys anywhere, `/body` | `()` |
| `RESPONSE_ROOT_TYPE` | valid non-object root, `/body` | `()` |
| `RESPONSE_FIELD_MISSING` | absent required success field, its field path | `()` |
| `RESPONSE_SHAPE` | malformed `error`, `model`, `response`, `done`, or `done_reason`, its field path | exact `expected=` tuple below |
| `PROVIDER_ERROR` | nonempty string `error`, `/body/error` | `()` |
| `RESPONSE_INCOMPLETE` | valid exact `done=false`, `/body/done` | `()` |

`N` is unsigned base-10 without separators. Shape details are exactly:

```text
/body/error:       ("expected=nonempty_scalar_string",)
/body/model:       ("expected=nonempty_scalar_string", "limit=4096")
/body/response:    ("expected=scalar_string",)
/body/done:        ("expected=boolean",)
/body/done_reason: ("expected=null_or_nonempty_scalar_string", "limit=4096")
```

Multiple duplicate objects or keys still yield the single duplicate-key issue.
Provider error text, model text, assistant content, malformed bytes, prompt
bytes, unknown names, and credentials never enter details or exception text.

## 8. GenerationEnvelope mapping

Only after all response gates pass with `done=true` does the adapter call the
accepted `capture_generation` factory, exactly once, with:

| Factory argument | Exact value |
|---|---|
| `attempt`, `relation`, `parent` | exact source-request values |
| `provider_id` | `ollama-local` for `LOCAL`; `ollama-cloud` for `CLOUD` |
| `adapter_id` | `ollama-generate` |
| `adapter_version` | `1` |
| `requested_model` | request `model` |
| `reported_model` | response `model`, including a mismatch |
| `prompt_template_id`, `prompt_template_version` | exact source-request values |
| `prompt` | exact pre-call prompt bytes |
| `public_parameters` | exact dict below |
| `raw_response` | UTF-8 encoding of only decoded response `response` |
| `finish_reason` | mapped `done_reason` or `None` |
| `provider_request_id` | always `None` |

The exact public-parameter dict is:

```python
{
    "stream": "false",
}
```

The endpoint is represented only by `provider_id`; it is not duplicated in
public parameters. No HTTP response body, request JSON wrapper, metrics,
thinking, provider error, status, header, or credential enters
`GenerationEnvelope`. Transport request/response records are ephemeral seam
values and are not returned. `generate_ollama` returns the envelope itself.

## 9. Secrets and side effects

No public input accepts a credential, token, header map, cookie,
environment-variable name, timeout, or arbitrary URL. The transport-request
URL is restricted to the two code-owned values. An eventual cloud transport
may hold a credential privately, but
it must add authorization outside `OllamaTransportRequest` and must never put
it in records, reprs, diagnostics, prompts, public parameters, repository
files, fixtures, or logs.

Prompt, assistant content, and complete provider-body bytes remain sensitive
even though they are not credentials. Adapter-owned request and transport
records use `repr=False`. Inherited capture records do not promise a redacted
repr and must not be logged. The adapter performs no logging, redaction, secret
guessing, filesystem access, environment lookup, process execution, dynamic
import, provider discovery, extraction, validation, compilation, or evaluation.

## 10. Dependency direction and implementation boundary

The dependency direction is exactly:

```text
caller-owned concrete transport -> OllamaTransport protocol
poietics.generation.ollama -> poietics.generation.model
caller -> returned GenerationEnvelope -> generation.extract

ollama --X--> generation.extract, pff, ground, binder, durable/session replay
```

The production import allowlist for `ollama.py` is exactly:

```text
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from .model import AttemptRef, AttemptRelation, GenerationEnvelope,
                   capture_generation
```

Aliases, star imports, extra symbols, absolute project imports, function-local
imports, and dynamic imports are forbidden. `json` is used only for strict
response decoding; request string serialization follows section 4. No third-
party package is added.

Production must not call `open`, `eval`, `exec`, `compile`, `__import__`,
environment/filesystem/process/shell/network APIs, sleep, extraction, provider
SDKs, checkers, binders, validation, compilation, or evaluation. The sole
effectful call is the one injected `transport(request)` call.

This authority tranche changes exactly:

```text
docs/PFF_OLLAMA_ADAPTER_PROFILE_V0.1.md
```

After acceptance, the complete implementation allowlist is exactly:

```text
src/poietics/generation/ollama.py
tests/test_generation_ollama.py
README.md
```

`src/poietics/generation/__init__.py`, packaging, existing generation files,
PFF, ground, and every other path remain byte-identical. Default tests use only
an injected fake transport and make no network, environment, key, or provider
call.

## 11. Literal fixtures, manifest, and mutation map

### 11.1 A01 literal success

A01 uses endpoint `LOCAL`, `AttemptRef("session:ollama", 1)`, relation
`INITIAL`, no parent, model `test-model`, prompt-template ID `pff-draft-prompt`,
version `1`, and exact prompt bytes for `Return "café".` followed by LF.

The prompt is 16 bytes with digest
`sha256:0eb8a0f9ca20a8f70668d89433b6d6bad1e5bad1ff5710f5dd149474472a5c6a`.
The exact 68 request-body bytes, with no final LF, are:

```text
{"model":"test-model","prompt":"Return \"café\".\n","stream":false}
```

Their digest is
`sha256:65b830219043a20ba744248c7f50f0159b76dd12d7a30385bc3c0ccc8487907f`.
The fake transport returns status 200 and these exact 105 UTF-8 body bytes,
again without final LF:

```text
{"model":"reported-model","response":"Draft ✓\n","done":true,"done_reason":"stop","thinking":"ignored"}
```

Their digest is
`sha256:d86ec9c69622d356a1928c852a94ed47d92a0fb09911dae66c7514748ac9d232`.
The captured assistant content is the exact 10 UTF-8 bytes for `Draft ✓`
followed by LF, digest
`sha256:db4f81d3aa274d3de4a249fa9d092b97d35ef6cb6b0d2fe786a5f7e2ba734d9f`.

A01 returns an exact `GenerationEnvelope` after one send and one capture. It
retains requested model `test-model`, reported model `reported-model`, finish
reason `stop`, no provider request ID, provider `ollama-local`, adapter
`ollama-generate` version `1`, and the sole public parameter `stream=false`.
The transport body and `thinking` are not returned or copied into the envelope.

### 11.2 Exact serializer variants

For every row, the `M` fixture sets the model to exactly the scalar sequence and
uses an empty prompt; the `P` fixture sets model `m` and prompt to the exact
UTF-8 encoding of the scalar sequence. The body otherwise follows section 4.
Both IDs are independently dispatched. Hex includes the JSON token's quotes.

| Model ID | Prompt ID | Scalar sequence | Exact JSON token bytes |
|---|---|---|---|
| A03M01 | A03P01 | `"` | `22 5c 22 22` |
| A03M02 | A03P02 | `\` | `22 5c 5c 22` |
| A03M03 | A03P03 | U+0008 | `22 5c 62 22` |
| A03M04 | A03P04 | U+0009 | `22 5c 74 22` |
| A03M05 | A03P05 | U+000A | `22 5c 6e 22` |
| A03M06 | A03P06 | U+000C | `22 5c 66 22` |
| A03M07 | A03P07 | U+000D | `22 5c 72 22` |
| A03M08 | A03P08 | U+0000 then U+001F | ASCII `"\u0000\u001f"` |
| A03M09 | A03P09 | `/` | `22 2f 22` |
| A03M10 | A03P10 | composed U+00E9 | `22 c3 a9 22` |
| A03M11 | A03P11 | U+2028 | `22 e2 80 a8 22` |
| A03M12 | A03P12 | U+2029 | `22 e2 80 a9 22` |
| A03M13 | A03P13 | U+1F600 | `22 f0 9f 98 80 22` |
| A03M14 | A03P14 | CR then LF | `22 5c 72 5c 6e 22` |
| A03M15 | A03P15 | decomposed `e` then U+0301 | `22 65 cc 81 22` |

Every fixture rejects key reorder, ASCII escaping of non-ASCII scalars,
optional slash escaping, uppercase `\u` hex, CRLF normalization, composed/
decomposed normalization, astral surrogate pairs, or a final LF.

### 11.3 Exact request and lineage fixtures

Every failure in this table has zero sends and zero captures. `S =
"session:ollama"`, `a1 = AttemptRef(S,1)`, and `a2 = AttemptRef(S,2)`.
`U = "é" * 2_048` is exactly 4,096 UTF-8 bytes; `U + "a"` is 4,097.
The fixture-local contrast classes are exactly empty subclasses named
`TextSubclass(str)`, `RequestSubclass(OllamaGenerateRequest)`,
`ResponseSubclass(OllamaTransportResponse)`, `AttemptSubclass(AttemptRef)`,
`BytesSubclass(bytes)`, `IntSubclass(int)`,
`IssueSubclass(OllamaAdapterIssue)`, and `TupleSubclass(tuple)`.
The duck request is a slots-only class declaring the eight request field names
and populated from A01; the mapping is an exact dict with those same pairs.

| ID | Exact input | Observable |
|---|---|---|
| A02 | A01 with `CLOUD` | cloud URL/provider; sole parameter remains `stream=false`; 1/1 |
| A04R01 | `RequestSubclass` with A01 values | `TypeError` |
| A04R02 | exact mapping containing A01 fields | `TypeError` |
| A04R03 | slots duck object containing A01 attributes | `TypeError` |
| A04R04 | A01 request, `transport=object()` | `TypeError` |
| A04T01 | endpoint exact string `LOCAL.value` | `TypeError` |
| A04T02 | attempt `object()` | `TypeError` |
| A04T03 | relation exact string `"initial"` | `TypeError` |
| A04T04 | parent `object()` | `TypeError` |
| A04T05 | attempt `AttemptSubclass(S,1)` | `TypeError` |
| A04T06 | parent `AttemptSubclass(S,1)` | `TypeError` |
| A04L01 | `INITIAL` with parent `a1` | `ValueError` |
| A04L02 | `RETRY` with no parent | `ValueError` |
| A04L03 | `a2`, parent `AttemptRef("other",1)` | `ValueError` |
| A04L04 | `a2`, parent `AttemptRef(S,2)` | `ValueError` |
| A04L05 | `RETRY`, `a2`, parent `a1` | succeeds 1/1; lineage retained exactly |
| A04L06 | `REPAIR`, `a2`, parent `a1` | succeeds 1/1; lineage retained exactly |
| A04L07 | `EXTRACT`, `a2`, parent `a1` | succeeds 1/1; lineage retained exactly |
| A04M01 | model `""` | `ValueError` |
| A04M02 | model `1` | `TypeError` |
| A04M03 | model `TextSubclass("m")` | `TypeError` |
| A04M04 | model lone surrogate | `ValueError` |
| A04M05 | model `U` | succeeds 1/1; exact model retained |
| A04M06 | model `U + "a"` | `ValueError` |
| A04I01 | template ID `""` | `ValueError` |
| A04I02 | template ID `1` | `TypeError` |
| A04I03 | template ID `TextSubclass("pff-draft-prompt")` | `TypeError` |
| A04I04 | template ID lone surrogate | `ValueError` |
| A04I05 | template ID `U` | succeeds 1/1; retained exactly |
| A04I06 | template ID `U + "a"` | `ValueError` |
| A04V01 | template version `""` | `ValueError` |
| A04V02 | template version `1` | `TypeError` |
| A04V03 | template version `TextSubclass("1")` | `TypeError` |
| A04V04 | template version lone surrogate | `ValueError` |
| A04V05 | template version `U` | succeeds 1/1; retained exactly |
| A04V06 | template version `U + "a"` | `ValueError` |
| A04P01 | prompt `bytearray()` | `TypeError` |
| A04P02 | prompt `b"\xff"` | `ValueError` |
| A04P03 | prompt `b""` | succeeds 1/1; exact empty prompt retained |
| A04P04 | prompt `ef bb bf` | succeeds 1/1; leading BOM scalar retained |
| A04P05 | prompt `b"p" * 1_048_577` | succeeds 1/1; envelope retains it and fake transport receives independently constructed `b'{"model":"test-model","prompt":"'+b"p"*1_048_577+b'","stream":false}'` exactly |
| A04P06 | prompt `BytesSubclass(b"p")` | `TypeError` |

### 11.4 Exact response and precedence fixtures

Let `R` be A01's exact 105-byte body and define:

```text
B(n) = b'{"model":"m","response":"","done":true,"x":' + b'['*n + b'0' + b']'*n + b'}'
J(t) = b'{"model":"m","response":"","done":true,"x":' + t + b'}'
Q = b'{"model":"m","response":"","done":true,"x":"' + b'['*65 + b'"}'
```

`B(63)` has depth 64; `B(64)` attempts 65. Unless successful, each row has
exactly 1 send/0 captures and only the listed issue.

| ID | Exact status/body | Observable |
|---|---|---|
| A05S201 | 201, `R` | `HTTP_STATUS`, `/status`, `("status=201",)` |
| A05S429 | 429, `R` | `HTTP_STATUS`, `/status`, `("status=429",)` |
| A05S500 | 500, `R+b" "*4_194_200` | only status 500 issue |
| A06MAX | 200, `R+b" "*4_194_199` (4,194,304) | succeeds 1/1 |
| A06PLUS | 200, `R+b" "*4_194_200` (4,194,305) | body-limit issue with actual 4194305/limit 4194304 |
| A06UTF | 200, `b"\xff"+b"x"*4_194_304` | only body-limit issue, not UTF-8 |
| A07 | 200, `b"\xff"` | `RESPONSE_UTF8`, `/body`, `()` |
| A07DUP | 200, `b'\xff{"model":"m","model":"n"}'` | only UTF-8, not duplicate |
| A08BOM | 200, `ef bb bf` + `R` | JSON-invalid |
| A08TRAIL | 200, `R+b"{}"` | JSON-invalid |
| A08NAN | 200, `J(b"NaN")` | JSON-invalid |
| A08PINF | 200, `J(b"Infinity")` | JSON-invalid |
| A08NINF | 200, `J(b"-Infinity")` | JSON-invalid |
| A08D64 | 200, `B(63)` | succeeds 1/1 |
| A08D65 | 200, `B(64)` | JSON-invalid |
| A08QBR | 200, `Q` | succeeds 1/1; quoted brackets do not affect depth |
| A08SUR | 200, response `"\ud800"` | JSON-invalid |
| A08UKVSUR | 200, unknown value `"\ud800"` | JSON-invalid |
| A08UNKKSUR | 200, unknown key `"\ud800"` with value 0 | JSON-invalid |
| A08DUP | 200, duplicate root `model` | one duplicate-key issue |
| A08NDUP | 200, unknown `x:{"k":1,"k":2}` only | one duplicate-key issue |
| A08RDUP | 200, duplicate root `model` and nested `x.k` | one duplicate-key issue total |
| A08DUAL | 200, duplicate root `model` plus response `"\ud800"` | only JSON-invalid |
| A08WS | 200, `b" \t\r\n"+R+b"\n\r\t "` | succeeds 1/1 |
| A08INT | 200, `J(b"7"*5_000)` | succeeds 1/1 without numeric conversion |
| A09NULL | 200, `b"null"` | root-type issue |
| A09FALSE | 200, `b"false"` | root-type issue |
| A09ZERO | 200, `b"0"` | root-type issue |
| A09STRING | 200, `b'""'` | root-type issue |
| A09ARRAY | 200, `b"[]"` | root-type issue |
| A09MULTI | 200, duplicate root `model` and `response` | one duplicate-key issue total |

For A08INT only, the harness saves `sys.get_int_max_str_digits()`, sets the
limit to exact decimal 4300 with `sys.set_int_max_str_digits(4300)`, dispatches
the fixture, and restores the saved value in a `finally` block (including saved
value 0). Setup and restoration are prerequisites, not target assertions.

The abbreviated exact bodies are, respectively:

```text
A08SUR:     b'{"model":"m","response":"\ud800","done":true}'
A08UKVSUR: b'{"model":"m","response":"","done":true,"x":"\ud800"}'
A08UNKKSUR: b'{"model":"m","response":"","done":true,"\ud800":0}'
A08DUP:     b'{"model":"m","model":"n","response":"","done":true}'
A08NDUP:    b'{"model":"m","response":"","done":true,"x":{"k":1,"k":2}}'
A08RDUP:    b'{"model":"m","model":"n","response":"","done":true,"x":{"k":1,"k":2}}'
A08DUAL:    b'{"model":"m","model":"n","response":"\ud800","done":true}'
A09MULTI:   b'{"model":"m","model":"n","response":"","response":"x","done":true}'
```

### 11.5 Error and success-shape fixtures

`A10PROVIDER` is exact `b'{"error":"provider failed","done":0}'` and yields
only `PROVIDER_ERROR` at `/body/error`. A10 malformed bodies are exact
`b'{"error":'+VALUE+b'}'`; success fields are not inspected.

| ID | VALUE | Observable |
|---|---|---|
| A10PROVIDER | exact provider body above | provider-error issue only |
| A10EEMPTY | `b'""'` | error shape issue |
| A10ENULL | `b"null"` | error shape issue |
| A10EBOOL | `b"false"` | error shape issue |
| A10ENUM | `b"0"` | error shape issue |
| A10EARRAY | `b"[]"` | error shape issue |
| A10EOBJECT | `b"{}"` | error shape issue |

A11AGG is exact `b'{"done":0,"done_reason":""}'`, SHA-256
`a14cc5a4f95859b97755c7486c909de56a592e92a09ac9976da47f2f514bc768`,
and yields these exact canonical issues:

```text
(RESPONSE_SHAPE,         "/body/done",        ("expected=boolean",))
(RESPONSE_SHAPE,         "/body/done_reason", ("expected=null_or_nonempty_scalar_string", "limit=4096"))
(RESPONSE_FIELD_MISSING, "/body/model",       ())
(RESPONSE_FIELD_MISSING, "/body/response",    ())
```

The next rows replace one field in
`{"model":"m","response":"x","done":true}`. All failures are 1/0; all
successes 1/1.

| ID | Exact variant | Observable |
|---|---|---|
| A11AGG | exact aggregate body and four issues above | exact canonical issue tuple |
| A11M00 | model `""` | model shape |
| A11M01 | model `null` | model shape |
| A11M02 | model `false` | model shape |
| A11M03 | model `0` | model shape |
| A11M04 | model `[]` | model shape |
| A11M05 | model `{}` | model shape |
| A11M06 | model `"m"*4_096` | succeeds |
| A11M07 | model `"m"*4_097` | model shape with limit detail |
| A11M08 | model `U` (4,096 UTF-8 bytes) | succeeds; exact model retained |
| A11M09 | model `U+"a"` (4,097 UTF-8 bytes) | model shape with limit detail |
| A11R01 | response `null` | response shape |
| A11R02 | response `false` | response shape |
| A11R03 | response `0` | response shape |
| A11R04 | response `[]` | response shape |
| A11R05 | response `{}` | response shape |
| A11R06 | response `""` | succeeds, empty assistant bytes |
| A11D00 | done absent | done missing |
| A11D01 | done `null` | done shape |
| A11D02 | done `0` | done shape |
| A11D03 | done `1` | done shape |
| A11D04 | done `"true"` | done shape |
| A11D05 | done `[]` | done shape |
| A11D06 | done `{}` | done shape |
| A11D07 | done `false` | only incomplete issue |
| A11F01 | done_reason absent | succeeds; `None` |
| A11F02 | done_reason `null` | succeeds; `None` |
| A11F03 | done_reason `""` | reason shape |
| A11F04 | done_reason `false` | reason shape |
| A11F05 | done_reason `0` | reason shape |
| A11F06 | done_reason `[]` | reason shape |
| A11F07 | done_reason `{}` | reason shape |
| A11F08 | done_reason `"r"*4_096` | succeeds; exact reason |
| A11F09 | done_reason `"r"*4_097` | reason shape with limit detail |
| A11F10 | done_reason `U` (4,096 UTF-8 bytes) | succeeds; exact reason retained |
| A11F11 | done_reason `U+"a"` (4,097 UTF-8 bytes) | reason shape with limit detail |
| A11SHAPEFALSE | exact `b'{"model":0,"response":"","done":false}'` | only model shape; no incomplete issue |

### 11.6 Transport, diagnostic, and record boundaries

| ID | Exact input | Observable |
|---|---|---|
| A12 | `b'{"model":"reported-model","response":"x","done":true,"z_scalar":7,"z_object":{"k":"v"},"z_array":[null,false]}'` | mismatch/unknowns retained or inert exactly |
| A13 | transport raises one exact `OllamaTransportError` object | same object/text; 1/0 |
| A14E | transport raises sentinel exception | same object; 1/0 |
| A14N | transport returns `None` | `TypeError`; 1/0 |
| A14S | transport returns `ResponseSubclass(200,R)` | `TypeError`; 1/0 |
| A15Q01 | transport request `("POST",LOCAL.value,"application/json",b"{}")` | constructs, immutable/repr-safe/unhashable |
| A15Q02 | method `1` | `TypeError` |
| A15Q03 | URL `1` | `TypeError` |
| A15Q04 | content type `1` | `TypeError` |
| A15Q05 | body `bytearray(b"{}")` | `TypeError` |
| A15Q06 | method `"GET"` | `ValueError` |
| A15Q07 | URL `"http://example.test/"` | `ValueError` |
| A15Q08 | content type `"text/plain"` | `ValueError` |
| A15Q09 | method `TextSubclass("POST")` | `TypeError` |
| A15Q10 | URL `TextSubclass(LOCAL.value)` | `TypeError` |
| A15Q11 | content type `TextSubclass("application/json")` | `TypeError` |
| A15Q12 | body `BytesSubclass(b"{}")` | `TypeError` |
| A15S01 | response `(100,b"")` | constructs |
| A15S02 | response `(599,b"")` | constructs |
| A15S03 | status 99 | `ValueError` |
| A15S04 | status 600 | `ValueError` |
| A15S05 | status `True` | `TypeError` |
| A15S06 | status `"200"` | `TypeError` |
| A15S07 | body `bytearray()` | `TypeError` |
| A15S08 | exact response mutated after construction to status `True` | adapter `TypeError`; 1/0 |
| A15S09 | exact response mutated after construction to status 99 | adapter `ValueError`; 1/0 |
| A15S10 | exact response mutated after construction to body `bytearray(R)` | adapter `TypeError`; 1/0 |
| A15S11 | response constructor status `IntSubclass(200)` | `TypeError` |
| A15S12 | response constructor body `BytesSubclass(R)` | `TypeError` |
| A15S13 | exact response mutated after construction to status `IntSubclass(200)` | adapter `TypeError`; 1/0 |
| A15S14 | exact response mutated after construction to body `BytesSubclass(R)` | adapter `TypeError`; 1/0 |
| A15I01 | issue `(HTTP_STATUS,"/a~1b/~0c",("status=201",))` | constructs exactly |
| A15I02 | code `"ollama_http_status"` | `TypeError` |
| A15I03 | path `1` | `TypeError` |
| A15I04 | details list | `TypeError` |
| A15I05 | details `TupleSubclass(("status=201",))` | `TypeError` |
| A15I06 | integer detail member | `TypeError` |
| A15I07 | path `"~"` | `ValueError` |
| A15I08 | path `"/a~2"` | `ValueError` |
| A15I09 | path `TextSubclass("/a")` | `TypeError` |
| A15I10 | detail member `TextSubclass("status=201")` | `TypeError` |
| A15E01 | exact tuple of `/z`,`/a`,duplicate `/z` issues | canonical `/a`,`/z`; input unchanged |
| A15E02 | empty tuple | `ValueError` |
| A15E03 | list | `TypeError` |
| A15E04 | `TupleSubclass((valid_issue,))` | `TypeError` |
| A15E05 | tuple containing nonissue | `TypeError` |
| A15E06 | tuple containing `IssueSubclass(HTTP_STATUS,"/status",("status=201",))` | `TypeError` |
| A15T01 | `OllamaTransportError()` | exact text `Ollama transport failed` |
| A15T02 | `OllamaTransportError("x")` | `TypeError` |
| A16 | credential only in transport state and provider-error text | absent from adapter records/diagnostics/envelope |
| A17 | runtime traps for extract/PFF/ground/filesystem/env/process/network/sleep/SDK/second send | A01 calls only transport once and capture once |
| A18C01 | mutate A01 request model to `""` via `object.__setattr__` | adapter `ValueError`; 0/0 |
| A18F01 | assign request field | frozen-assignment failure |
| A18F02 | assign transport-request field | frozen-assignment failure |
| A18F03 | assign transport-response field | frozen-assignment failure |
| A18H01 | hash request | `TypeError` |
| A18H02 | hash transport request | `TypeError` |
| A18H03 | hash transport response | `TypeError` |
| A18R01 | repr request containing sentinel prompt | sentinel absent |
| A18R02 | repr transport request containing sentinel body | sentinel absent |
| A18R03 | repr transport response containing sentinel body | sentinel absent |
| A20AST | AST-walk every scope/import/call in `ollama.py` | exact section-10 imports only; every forbidden call absent |

### 11.7 External composability fixture

A19 uses exact 115 assistant bytes (no final LF), SHA-256
`666e782bc2438cde8fb42d9594bb28e4ccefe81960d44ce7e8150f413f9f1d93`:

```text
<<<PFF-DRAFT/0.1>>>
{"schema":"pff-draft/0.1","atoms":[],"rules":[],"evidence_requests":[]}
<<<END-PFF-DRAFT/0.1>>>
```

The exact minified provider body is 200 bytes, SHA-256
`ecb68c6cd13c4e11a74ab77cadf4426d6447b51cfb25aa2109e215688db1242f`:

```text
{"model":"reported-model","response":"<<<PFF-DRAFT/0.1>>>\n{\"schema\":\"pff-draft/0.1\",\"atoms\":[],\"rules\":[],\"evidence_requests\":[]}\n<<<END-PFF-DRAFT/0.1>>>","done":true,"done_reason":"stop"}
```

Generate once, replace transport with a raising callable, then call public
`extract_draft(envelope)` twice. Both results are exactly equal empty valid
drafts; send count remains one. This is external evidence: `ollama.py` cannot
import or call the extractor.

### 11.8 Fixture and mutation closure

`D` is exactly this finite 211-member set; no family, wildcard, or range
denotes an ID:

```text
D = {
 A01,A02,
 A03M01,A03P01,A03M02,A03P02,A03M03,A03P03,A03M04,A03P04,
 A03M05,A03P05,A03M06,A03P06,A03M07,A03P07,A03M08,A03P08,
 A03M09,A03P09,A03M10,A03P10,A03M11,A03P11,A03M12,A03P12,
 A03M13,A03P13,A03M14,A03P14,A03M15,A03P15,
 A04R01,A04R02,A04R03,A04R04,A04T01,A04T02,A04T03,A04T04,A04T05,A04T06,
 A04L01,A04L02,A04L03,A04L04,A04L05,A04L06,A04L07,
 A04M01,A04M02,A04M03,A04M04,A04M05,A04M06,
 A04I01,A04I02,A04I03,A04I04,A04I05,A04I06,
 A04V01,A04V02,A04V03,A04V04,A04V05,A04V06,
 A04P01,A04P02,A04P03,A04P04,A04P05,A04P06,
 A05S201,A05S429,A05S500,A06MAX,A06PLUS,A06UTF,A07,A07DUP,
 A08BOM,A08TRAIL,A08NAN,A08PINF,A08NINF,A08D64,A08D65,A08QBR,
 A08SUR,A08UKVSUR,A08UNKKSUR,A08DUP,A08NDUP,A08RDUP,A08DUAL,A08WS,A08INT,
 A09NULL,A09FALSE,A09ZERO,A09STRING,A09ARRAY,A09MULTI,
 A10PROVIDER,A10EEMPTY,A10ENULL,A10EBOOL,A10ENUM,A10EARRAY,A10EOBJECT,
 A11AGG,A11M00,A11M01,A11M02,A11M03,A11M04,A11M05,A11M06,A11M07,A11M08,A11M09,
 A11R01,A11R02,A11R03,A11R04,A11R05,A11R06,
 A11D00,A11D01,A11D02,A11D03,A11D04,A11D05,A11D06,A11D07,
 A11F01,A11F02,A11F03,A11F04,A11F05,A11F06,A11F07,A11F08,A11F09,A11F10,A11F11,
 A11SHAPEFALSE,A12,A13,A14E,A14N,A14S,
 A15Q01,A15Q02,A15Q03,A15Q04,A15Q05,A15Q06,A15Q07,A15Q08,A15Q09,A15Q10,A15Q11,A15Q12,
 A15S01,A15S02,A15S03,A15S04,A15S05,A15S06,A15S07,A15S08,A15S09,A15S10,A15S11,A15S12,A15S13,A15S14,
 A15I01,A15I02,A15I03,A15I04,A15I05,A15I06,A15I07,A15I08,A15I09,A15I10,
 A15E01,A15E02,A15E03,A15E04,A15E05,A15E06,A15T01,A15T02,A16,A17,
 A18C01,A18F01,A18F02,A18F03,A18H01,A18H02,A18H03,A18R01,A18R02,A18R03,
 A19,A20AST
}
```

During later implementation qualification—not profile acceptance—the harness
must prove `D == D_dispatch == D_executed`, with no extra or skipped ID.

The exact mutation population has 56 members:

```text
M = {M01,M02,M03,M04,M05,M06,M07,M08,M09,M10,M11,M12,M13,M14,M15,
     M16,M17,M18,M19,M20,M21,M22,M23,M24,M25,M26,M27,M28,M29,M30,
     M31,M32,M33,M34,M35,M36,M37,M38,M39,M40,M41,M42,M43,M44,M45,
     M46,M47,M48,M49,M50,M51,M52,M53,M54,M55,M56}
```

| ID | Exact mutation/mechanism | Killing ID/assertion | Prediction |
|---|---|---|---|
| M01 | swap local/cloud provider ID mapping | A01 provider | KILL |
| M02 | add endpoint public parameter | A01 sole parameter | KILL |
| M03 | change adapter ID | A01 adapter ID | KILL |
| M04 | reorder request JSON keys | A01 exact body | KILL |
| M05 | ASCII-escape non-ASCII | A03M10 exact token | KILL |
| M06 | escape `/` | A03P09 exact token | KILL |
| M07 | Unicode-normalize prompt | A03P15 exact token | KILL |
| M08 | use `isinstance` for request | A04R01 TypeError/0 sends | KILL |
| M09 | skip invocation-time request validation | A18C01 ValueError/0 sends | KILL |
| M10 | send oversized prompt truncated | A04P05 exact prompt | KILL |
| M11 | lose noninitial lineage | A04L05 retained retry | KILL |
| M12 | retry transport after error | A13 send count 1 | KILL |
| M13 | capture before response validation | A05S201 capture count 0 | KILL |
| M14 | omit returned-status exact-type revalidation | A15S08 TypeError | KILL |
| M15 | check body before status | A05S500 status-only | KILL |
| M16 | replace rejection predicate with `len(body) > 4_194_305` | A06PLUS must reject length 4,194,305 | KILL |
| M17 | UTF-8 replacement decode | A07 UTF-8 issue | KILL |
| M18 | parse duplicate before UTF-8 | A07DUP UTF-8-only | KILL |
| M19 | permit exact `NaN` token | A08NAN JSON-invalid | KILL |
| M20 | count brackets inside strings | A08QBR success | KILL |
| M21 | replace opaque JSON `parse_int` with exact built-in `int` | A08INT must succeed under configured 4300-digit limit | KILL |
| M22 | skip scalar walk under unknown values | A08UKVSUR JSON-invalid | KILL |
| M23 | inspect only root duplicates | A08NDUP duplicate issue | KILL |
| M24 | emit one issue per duplicate object | A08RDUP exactly one issue | KILL |
| M25 | duplicate gate before scalar gate | A08DUAL JSON-invalid-only | KILL |
| M26 | coerce nonobject root | A09ZERO root-type | KILL |
| M27 | inspect success fields before provider error | A10PROVIDER provider-only | KILL |
| M28 | test incomplete before shape | A11SHAPEFALSE shape-only | KILL |
| M29 | use character count for request metadata | A04M06 ValueError | KILL |
| M30 | reject model mismatch | A12 success/models | KILL |
| M31 | capture full HTTP body | A01 assistant digest | KILL |
| M32 | catch/wrap unexpected transport exception | A14E identity | KILL |
| M33 | accept response subclass | A14S TypeError | KILL |
| M34 | omit diagnostic exact deduplication | A15E01 two issues only | KILL |
| M35 | remove `~0`/`~1` escape validation after retaining leading-slash validation | A15I08 must raise `ValueError` for `/a~2` | KILL |
| M36 | enable dataclass repr | A18R01 sentinel absent | KILL |
| M37 | add `from .extract import extract_draft` | A20AST exact imports | KILL |
| M38 | call `extract_draft` in adapter success | A17 extractor trap | KILL |
| M39 | return wrapper instead of envelope | A01 exact return type | KILL |
| M40 | omit returned-body exact-type revalidation | A15S10 TypeError | KILL |
| M41 | omit exact `stream` request member | A01 exact body | KILL |
| M42 | change adapter version from `1` | A01 adapter version | KILL |
| M43 | add any `poietics.pff` import | A20AST exact imports | KILL |
| M44 | add any `poietics.ground` import | A20AST exact imports | KILL |
| M45 | add `urllib.request` import | A20AST exact imports | KILL |
| M46 | call injected transport a second time | A17 transport count 1 | KILL |
| M47 | skip scalar validation of unknown object keys | A08UNKKSUR JSON-invalid | KILL |
| M48 | omit returned-status range revalidation | A15S09 ValueError | KILL |
| M49 | preserve submitted diagnostic order instead of canonical sort | A15E01 `/a`,`/z` order | KILL |
| M50 | decode UTF-8 before enforcing body limit | A06UTF body-limit-only | KILL |
| M51 | reject when `len(body) >= 4_194_304` | A06MAX must accept exact maximum | KILL |
| M52 | validate response model limit with character count | A11M09 must reject 4,097 UTF-8 bytes | KILL |
| M53 | validate response done_reason limit with character count | A11F11 must reject 4,097 UTF-8 bytes | KILL |
| M54 | invoke transport a second time after HTTP 429 | A05S429 transport count must equal 1 | KILL |
| M55 | accept every 2xx status instead of exact 200 | A05S201 must emit status issue | KILL |
| M56 | copy provider `error` text into issue details or exception text | A10PROVIDER requires `()` details and no provider text | KILL |

Later qualification requires `M == M_dispatch == M_executed`, zero survivors,
and zero wrong-reason kills. A kill counts only when its listed assertion fails.
Expected values are literal; tests may not call production encoders, sorters,
or constructors to compute expectations.

Each mutant is applied alone to an authenticated fresh implementation copy.
Before dispatch, all unmutated controls and the mutant's listed fixture setup
and prerequisite assertions must be green, and execution must reach the named
target gate. Classification is exact:

- a syntax, import, collection, or setup failure; an earlier-gate failure; or
  failure only of an unlisted assertion is `WRONG_REASON_KILL`;
- a green named target assertion is `SURVIVOR`; and
- only the intended named assertion failing, with all prerequisites and
  unlisted assertions green, is `PREDICTED_KILL`.

The qualification record stores that classification for every member of `M`;
it cannot infer a kill merely from a nonzero process status.

## 12. Dated official Ollama evidence

The following official pages were accessed on 2026-08-17:

- [API introduction](https://docs.ollama.com/api/introduction): default local
  base `http://localhost:11434/api` and cloud base `https://ollama.com/api`;
- [Generate](https://docs.ollama.com/api/generate): `POST /api/generate`, model,
  prompt, stream request fields, and response model/response/done fields;
- [Streaming](https://docs.ollama.com/api/streaming): `stream:false` selects one
  JSON response rather than newline-delimited streaming objects;
- [Errors](https://docs.ollama.com/api/errors): common HTTP statuses and JSON
  error object with an `error` member; and
- [Authentication](https://docs.ollama.com/api/authentication): local access
  needs no authentication; direct cloud access uses a bearer API key.

The pages do not freeze response requiredness, JSON byte serialization, UTF-8
failure handling, duplicate keys, unknown fields, response limits, redirects,
timeouts, retries, or exhaustive status behavior. All such decisions above are
therefore explicitly `[N]`, not claimed as Ollama documentation restatements.

## 13. Explicit deferrals

This profile does not authorize:

- a concrete HTTP client, Ollama SDK, redirect policy implementation, timeout,
  cancellation, proxy, TLS, DNS, socket, or connection-pool code;
- environment-variable access, API-key loading/storage/rotation, authorization
  header construction, logging, metrics, tracing, or persistence;
- automatic retry, backoff, `Retry-After`, failover, model fallback, repair, or
  append-only attempt-history validation;
- streaming or partial-response assembly;
- request options, structured output, tools, images, thinking, system prompts,
  arbitrary endpoints, or custom headers;
- live provider tests in the default or acceptance suite;
- automatic extraction, provider-output repair, binding, evidence/checker work,
  PFF validation/compilation/evaluation, or ground evaluation; and
- durable replay storage, deletion/tombstones, encryption, or provenance DAGs.

A later concrete transport profile must bind credential ingress and prove one
physical request with retries and redirects disabled. A later optional-live
profile may use deployment secrets, but no secret or live output becomes an
acceptance fixture.

## 14. Acceptance rule

Profile acceptance is documentation-only. It requires authentication of the
exact candidate bytes, repository baseline, and controlling capture-profile
hash; three independent `CLEAN` reviews; and a finding that every explicit
criterion and mutation is determinate and dispatchable. It does not require or
use an implementation, focused/full test result, dispatched criterion, mutation
result, or qualification review. No green run can substitute for review of the
candidate authority itself.

Later implementation qualification is a separate gate. It requires exact
`D == D_dispatch == D_executed`, exact
`M == M_dispatch == M_executed`, zero mutation survivors, zero wrong-reason
kills, the focused and full suites, import/call-boundary evidence, and
independent clean implementation reviews. None of that later evidence changes
the already accepted profile bytes.

Acceptance changes only the status line from `CANDIDATE — NOT ACCEPTED` to
`ACCEPTED` and appends exactly one LF plus this section, with one final LF:

````text
## 15. Acceptance record

```text
profile: pff-ollama-adapter/0.1
status: accepted
accepted_on: 2026-08-17
reviewed_candidate_sha256: sha256:<64 lowercase hexadecimal digits>
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
````

`reviewed_candidate_sha256` is SHA-256 over the complete candidate bytes,
including their existing final LF, before the two acceptance transformations.
No semantic text, identifier, diagnostic, fixture, whitespace, or other byte
may change during acceptance. Implementation begins only after the accepted
profile is published.

## 15. Acceptance record

```text
profile: pff-ollama-adapter/0.1
status: accepted
accepted_on: 2026-08-17
reviewed_candidate_sha256: sha256:1a7fe234e6a5ae4753177e38c676f8a7cd4d69c155efb0383df0e1af6616f220
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
