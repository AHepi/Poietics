# PFF Generation Capture Profile v0.1

**Status:** ACCEPTED  
**Scope:** provider-neutral capture and deterministic extraction only  
**Core authority:** `poietic-pff-implementable-core-spec-v0.1.md`, SHA-256
`43f4c4cb50292feccf2b0fc45e517d1ec4bf60c908600b96169ce4702bc99aa9`  
**Implementation guidance:** `LESSONS_LEARNED_2026-08-17.md`, SHA-256
`9b4fe50618b53260e1d32533a2709da5a367c337adf35ced8c109e4fbaa25f7a`  
**Prior profile:** `PFF_CORE_V0.1_CHALLENGE_PROFILE.md`, SHA-256
`6e4bab9865db3c1cbdd160eaf80dcbf0d66716152e2a0be0b36deedddeafdf07`

## 1. Purpose and authority

The PFF core deliberately places natural-language extraction outside the
semantic engine. This profile freezes the first upstream landing zone for an
LLM or another nondeterministic producer.

The profile has one purpose:

```text
captured generation attempt
    -> strict extraction of one delimited JSON payload
    -> immutable, untrusted DraftPackage
```

It does not freeze or implement the later binding step:

```text
DraftPackage
    -> authenticated evidence and code-owned binding
    -> Package
    -> validate -> compile -> evaluate
```

The core specification is normative for the thin waist. The lessons document
is implementation guidance. Section 2 of the accepted challenge profile was
expressly provisional and is an informative input here; it did not freeze a
generation protocol. Core requirements restated here retain core authority.
Every capture, draft-schema, diagnostic, limit, and API choice introduced here
is new profile authority. The exclusions in section 13 are normative negative
scope for this tranche; only the deferred features' future positive semantics
remain unspecified and non-normative here.

The new choices in this document are normative only after this candidate is
accepted. They do not change PFF package or evaluation semantics.

The document/profile identity frozen by this file is
`pff-generation-capture/0.1`. The distinct `GenerationEnvelope.profile` value
`pff-generation/0.1` identifies captured envelope records; neither string is an
alias for the other.

## 2. Answer to the prose problem

An LLM may emit arbitrary prose before and after one exact machine-readable
block. The prose is retained byte-for-byte as part of the generation record,
but it has no typed effect. Words such as `LIVE`, `EXCLUDED`, `SUSPENDED`,
`pass`, `fail`, or `open` outside the block are ordinary text.

The extractor is not an NLP system. It never guesses a JSON object, repairs
syntax, chooses among alternatives, or invokes another model. Prose without the
exact block yields a typed extraction failure and no draft.

If a second LLM is later used to turn prose into a valid block, that is a new
captured attempt with relation `extract`. It is not a hidden parser action.

This rule is required for deterministic replay: identical captured bytes and
the same profile version always produce the same draft or the same typed
failure.

## 3. Authority boundary

The generator may propose only the fields present in `DraftPackage`. It cannot
author any of the following:

- a PFF `Package`, `PackageHeader`, or `ValidatedPackage`;
- registry selection or registry contracts;
- primitive atoms or base live, excluded, or protected-open membership;
- certificate or closure records, checker selection, or checker outcomes;
- semantic or evaluation status;
- compiler-generated `__pff__:` identities;
- validation, compilation, evaluation, or explanation output.

`DraftPackage` is neither a subclass nor a wrapper of `Package`. Passing it to
`validate_package` or `compile_package` must fail their existing exact-type
guards.

Only a future trusted, deterministic, provider-free binder may construct a
`Package`. The binder profile must be frozen separately before such code lands.

## 4. Public capture model

The first implementation exposes these exact concepts from
`poietics.generation.model`.

### 4.1 Attempt identity and lineage

```python
class AttemptRelation(StrEnum):
    INITIAL = "initial"
    RETRY = "retry"
    REPAIR = "repair"
    EXTRACT = "extract"

@dataclass(frozen=True, slots=True, order=True)
class AttemptRef:
    session_id: str
    sequence: int
```

`session_id` is a nonempty Unicode-scalar exact string of at most 256 UTF-8
bytes. `sequence` is an exact integer in `1..9223372036854775807`; Python
`bool` is rejected. `AttemptRef.__post_init__` enforces these rules on ordinary
construction. `AttemptRef` is generation history, not a package record
reference and not `parent_package_hash`.

For `AttemptRef`, `GenerationParameter`, and `DraftRef`, a wrong exact Python
type raises `TypeError`; an empty, non-scalar, oversized, reserved, or
out-of-range value raises `ValueError`, as applicable to that type. String and
integer subclasses are rejected.

An `INITIAL` attempt has no parent. Every other relation requires an exact
parent in the same session with a smaller sequence. As an adapter precondition,
the caller supplies a fresh `AttemptRef` for every invocation, even when its
request and response bytes match an earlier attempt. The single-envelope
factory cannot establish cross-call freshness. Within a future
generation-history log, duplicate `AttemptRef` values are invalid; that
collection-level check is outside this API.

This profile records lineage but does not yet validate a whole append-only
session log. Cross-attempt rules such as “retry has the same request” belong to
the later replay profile.

### 4.2 Captured bytes

```python
@dataclass(frozen=True, slots=True, init=False)
class CapturedContent:
    data: bytes
    sha256: str
```

`CapturedContent` is created only by the capture factory. It copies exact bytes
and computes:

```text
sha256 = "sha256:" + lowercase_hex(SHA-256(data))
```

The digest is integrity metadata, not authorship and not a PFF package hash.
No URL, filesystem path, media-type claim, or bare hash stands in for retained
content in this tranche.

`init=False` is not the factory guard by itself. Both factory-only classes have
a private custom `__init__` that requires an unexported module sentinel. Calling
`CapturedContent()` or `GenerationEnvelope()` without that sentinel raises
`TypeError` before any slot can be observed. The public factory is the only
caller holding the sentinel.

### 4.3 Generation envelope

```python
@dataclass(frozen=True, slots=True, order=True)
class GenerationParameter:
    name: str
    value: str

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
```

`profile` is exactly `pff-generation/0.1`. All required identifier/version
strings are nonempty Unicode-scalar exact strings. Nullable metadata, when
present, is also a nonempty Unicode-scalar exact string. Each such envelope
metadata string is at most 4,096 UTF-8 bytes.

Public parameters use one deliberately narrow representation:

`GenerationParameter.__post_init__` enforces its local type, scalar, nonempty
name, and size rules on ordinary construction.

The factory accepts an exact `dict[str, str]`; subclasses are rejected. Names
are nonempty exact strings, values are exact strings (including the empty
string), and the result is sorted by name. This preserves
absent-versus-explicit provider settings without
creating a second JSON-number identity problem: an adapter records, for
example, `temperature` as the exact public string it used. At most 256
parameters are accepted; a name is at most 256 UTF-8 bytes and a value at most
4,096 UTF-8 bytes, all limits inclusive. Every metadata and parameter string
must contain only Unicode scalar values. Invalid types raise `TypeError`; an
empty name, a non-scalar string, or an oversized name/value raises `ValueError`.
Duplicate-name detection is inapplicable after exact-dict construction, and
equal values under different names are permitted. Cyclic graphs and nested
resource attacks are structurally impossible. `GenerationEnvelope` is
deliberately unhashable: `hash(envelope)` raises `TypeError`. Transport
credentials and authorization headers are not public parameters.

Every string sort in this profile is ascending lexicographic Unicode scalar
value order, with the shorter equal-prefix string first. Integer tie-breakers
are ascending numeric order. No locale, normalization, or case folding applies.

The sole factory is:

```python
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
) -> GenerationEnvelope
```

The factory copies all caller-owned inputs. Callers cannot supply either
digest. Direct `GenerationEnvelope` or `CapturedContent` construction fails.
`attempt`, `relation`, and `parent` must have the exact declared types; prompt
and response must be exact `bytes`; parameter input must be an exact `dict`;
and all other values must have the exact declared type. Type mismatches raise
`TypeError`. Empty strings and invalid lineage raise `ValueError`. The factory
does not enforce raw prompt/response byte limits: it preserves the exact bytes,
and extraction reports limit diagnostics deterministically.

The prompt is the exact rendered prompt given to the adapter, not merely a
template name or hash. The raw response is the exact assistant content bytes
returned at the application boundary before stripping, newline normalization,
or extraction. Provider HTTP envelopes, adapter-injected authentication
headers, cookies, and hidden reasoning are outside the capture record. User
prompts and model output are untrusted, potentially sensitive bytes and may
themselves contain credential-like text; exact capture preserves that text
rather than silently redacting or normalizing it.

## 5. First draft schema

`pff-draft/0.1` is intentionally small. It proves the prose-to-typed-draft
path without guessing closure, checker, base, or challenge binding.

### 5.1 Exact draft types

```python
@dataclass(frozen=True, slots=True, order=True)
class DraftRef:
    id: str
    version: int

@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftAtom:
    id: str
    version: int
    predicate: str
    args: tuple[str, ...]
    frame: str
    grade: str | None

@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftRule:
    id: str
    version: int
    head: DraftRef
    positive: frozenset[DraftRef]
    evidence_request: DraftRef

@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftEvidenceRequest:
    id: str
    version: int
    kind: str
    subject: DraftRef
    question: str

@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DraftPackage:
    schema: str
    atoms: tuple[DraftAtom, ...]
    rules: tuple[DraftRule, ...]
    evidence_requests: tuple[DraftEvidenceRequest, ...]
```

`DraftRef` validates its local value invariants on ordinary construction. The
four owned draft classes use the same private-sentinel construction pattern as
the capture classes and are created only by successful extraction. This is an
unsupported-construction guard, not a Python sandbox or an authenticity claim.
The future binder must accept an exact successful extraction boundary, not
duck-typed or hand-populated records. A successful graph is deeply immutable:
its transitive values are frozen records, tuples, frozensets, strings, integers,
or null, never caller-owned dicts or lists.

All owned IDs and reference IDs are nonempty Unicode-scalar exact strings, at
most 262,144 UTF-8 bytes, and must not begin `__pff__:`. Versions are exact positive integers no greater than
`9_223_372_036_854_775_807`; Python `bool` is rejected. Predicate, frame, and
question are nonempty Unicode-scalar exact strings. Atom arguments are ordered
Unicode-scalar exact strings; grade is null or a Unicode-scalar exact string.
All recognized string values share the section-7 byte limit.
`DraftEvidenceRequest.kind` is exactly `certificate`.

There is deliberately no `primitive` field: every draft atom in this schema is
a nonprimitive proposal. There are no negative premises, faces, contraries,
challenges, discharges, certificate records, closure records, base partitions,
statuses, or checker fields. Later accepted draft-schema versions may add
further proposal vocabulary without changing capture or the PFF core.

Atom, rule, and evidence-request collections are canonicalized by exact
`(id, version)` using that sort. Atom argument order is retained. Rule positives have set
semantics but duplicate submitted members are rejected before freezing.

### 5.2 Structural linkage

The three identity namespaces are exactly `atom`, `rule`, and
`evidence_request`. Identity is `(namespace, id, version)`, so the same
`(id, version)` may coexist in different namespaces. References are
type-directed by their field.

Within one valid draft:

1. exact `(namespace, id, version)` identities are unique;
2. every rule head and positive reference resolves to exactly one draft atom;
3. every rule references exactly one evidence request;
4. every evidence request names exactly one draft rule as its subject;
5. the request subject equals the exact rule that references it;
6. an evidence request is referenced by one rule only; and
7. no evidence request is orphaned.

There is no ID-only or latest-version fallback. A reference to version 6 does
not resolve to version 5.

An evidence request is an untrusted request for later checking. It does not
select a checker, claim an output certificate ID, supply evidence details, or
state `pass`, `fail`, or `open`.

## 6. Exact wire grammar

The raw response may contain arbitrary UTF-8 prose around exactly one block:

```text
<<<PFF-DRAFT/0.1>>>
{one strict JSON object}
<<<END-PFF-DRAFT/0.1>>>
```

The opener production is the exact ASCII bytes
`<<<PFF-DRAFT/0.1>>>` immediately followed by LF (`0x0a`); either the start of
the response or LF must precede its first `<`. The closer production is LF immediately
followed by the exact ASCII bytes `<<<END-PFF-DRAFT/0.1>>>`, followed by either
LF or end of response. A marker followed by CRLF, leading/trailing spaces,
marker substrings, and alternate capitalization do not count as markers.
Markdown fence lines are ordinary surrounding prose: they are not markers and
do not prevent an enclosed exact marker line from counting. The LF that begins
the closer is structural and is not part of the payload.

The payload is the exact bytes after the opening LF and before the LF that
starts the closing line. It must contain one complete JSON object and nothing
else.

The JSON object has these exact required fields and no others:

```json
{
  "schema": "pff-draft/0.1",
  "atoms": [],
  "rules": [],
  "evidence_requests": []
}
```

References use objects with exactly `id` and `version`; `id@version` strings
are not reference syntax.

JSON is decoded as strict UTF-8 without BOM or Unicode normalization. Every
decoded string must contain only Unicode scalar values; an escaped or literal
lone surrogate is invalid. Duplicate keys at any depth, `NaN`, infinities,
trailing data, and non-object roots are invalid. Finite JSON float tokens are
retained as marked lexical tokens until field validation. JSON integer tokens
are also retained lexically, so interpreter integer-digit settings cannot alter
classification. A float, exponent, boolean, string, null, array, object,
out-of-range integer, or syntactically valid arbitrarily long integer in a
version field is `DRAFT_INVALID_VERSION`; exact in-range integer conversion
occurs only in phase 8. A numeric token in another known field is
`DRAFT_VALUE_TYPE`; an unknown or forbidden field suppresses value diagnostics
for its subtree. The current schema contains no valid float- or boolean-valued
field. No interpreter `RecursionError`, integer-conversion `ValueError`, or
implementation resource exception may escape the typed extraction boundary.

Unknown fields are errors. In the root and every object that occupies a
schema-declared record or reference position after its outer object category
has validated, a field receives `DRAFT_FIELD_FORBIDDEN` if and only if its exact
key is in this exhaustive set:

```text
accepted, base, certificate, certificate_result, certificates,
checker, closure, closure_result, closures, confidence, details,
excluded, header, live, open, parent_package_hash, payload_hash,
primitive, probability_true, protected_open, registry, registry_id,
result, status, support
```

Every non-allowed field outside that set receives `DRAFT_FIELD_UNKNOWN`.
Wrong-category value subtrees and the diagnosed unknown or forbidden field's
value are not traversed. Therefore
`{"typo":{"status":"LIVE"}}` at the root emits only the root unknown-field
issue; the nested `status` is inert data beneath the rejected field and does
not also emit a forbidden-field issue.

## 7. Extraction API, identity, and limits

```python
@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class ExtractedDraft:
    source: GenerationEnvelope
    payload_sha256: str
    draft: DraftPackage

    __hash__ = None

def extract_draft(envelope: GenerationEnvelope) -> ExtractedDraft:
    ...
```

`ExtractedDraft` is factory-only under the same private-sentinel pattern.
`extract_draft` accepts only an exact `GenerationEnvelope`; subclasses and
duck-typed values raise `TypeError` and no `DraftExtractionError` is created.
It first recomputes both captured digests and then uses one code-owned limits
profile. Every maximum is inclusive; the first disallowed value is maximum
plus one.

| Resource | Maximum in `pff-generation-limits/0.1` |
|---|---:|
| raw prompt bytes | 1,048,576 |
| raw response bytes | 4,194,304 |
| delimited payload bytes | 1,048,576 |
| JSON nesting depth | 64 |
| one recognized record/reference JSON string value, decoded UTF-8 bytes | 262,144 |
| each of `atoms`, `rules`, and `evidence_requests` | 4,096 members |
| each atom `args` and each rule `positive` | 4,096 members |

Capture itself never drops an oversized prompt or response. After digest
integrity succeeds, extraction reports `/prompt` and `/response` limit issues
together when both are oversized, then stops.

Nesting depth is checked before recursive JSON decoding by a bounded lexical
scan of the UTF-8 payload. The root object has depth 1; every `{` or `[` outside
a quoted JSON string increments depth; a scalar does not. Quote state uses the
JSON backslash-parity rule but this scan does not repair or otherwise validate
JSON. The counter begins at zero; `}` or `]` outside a string decrements a
positive counter and leaves zero unchanged. Other bytes do not change it. On
the first attempted depth 65 it reports actual depth 65 and stops;
this depth issue precedes later JSON syntax classification. Braces and brackets
inside a quoted string do not affect this scan.

String length is measured over the decoded Unicode scalar value encoded as
UTF-8, so literal and escaped spellings have the same length. The issue is
located at the recognized value path and suppresses that field's ID, enum,
nonempty, reserved-prefix, and other value diagnostics. Unknown and forbidden fields suppress
traversal of their names and values. If a collection exceeds its limit, its
one limit issue suppresses all member diagnostics for that collection.
Independent over-limit collections and recognized strings aggregate in phase
8.

`payload_sha256` uses the same `sha256:<lowercase hex>` spelling over the exact
payload bytes. It is extraction identity, not semantic package identity.

Two responses with different surrounding prose have different raw-response
digests but may yield equal `DraftPackage` values and equal payload digests.
JSON bytes with different whitespace or key order have different payload
digests even when their normalized `DraftPackage` values are equal. This
profile makes no claim of canonical package JSON.

Re-extraction for replay calls this same function. There is no second replay
parser and no provider call.

## 8. Typed diagnostics and precedence

```python
class DraftExtractionCode(StrEnum):
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

@dataclass(frozen=True, slots=True)
class DraftExtractionIssue:
    code: DraftExtractionCode
    path: str
    details: tuple[str, ...] = ()

class DraftExtractionError(ValueError):
    issues: tuple[DraftExtractionIssue, ...]
```

Paths use RFC 6901 JSON Pointer. `~` becomes `~0`; `/` becomes `~1`. Array
indices refer to submitted JSON order. The capture paths are `/prompt` and
`/response`; `/response/block` denotes the extracted payload as a whole. An
unknown submitted member name is not copied into a path: its issue is located
at the containing object and carries only a SHA-256 of the UTF-8 field name.

`DraftExtractionIssue` has no natural dataclass ordering. The error constructor
accepts only exact `DraftExtractionIssue` values. Each issue constructor
requires the exact enum type, an exact valid-pointer string, and an exact tuple
of exact strings; subclasses, lists, and duck types are rejected. A valid
pointer is empty or starts with `/`, and every `~` is followed by `0` or `1`.
Wrong exact types raise `TypeError`; an exact string with invalid pointer syntax
raises `ValueError`.
The error constructor deduplicates exact issues and sorts them by the explicit
key
`(issue.path, issue.code.value, issue.details)`. Details are code-specific,
fixed-order strings; they are never globally sorted and never contain a raw
prompt, response, payload fragment, submitted field value, transport
credential, or secret. All hashes use `sha256:<lowercase hex>`.
`DraftExtractionError.issues` is the sole normative diagnostic payload; human
exception text and `args` formatting are not part of this profile.

`DraftExtractionError.__init__` accepts one exact tuple; a list, subclass, or
non-issue member raises `TypeError`, and an empty tuple raises `ValueError`.
It exact-deduplicates and canonical-sorts the tuple before assigning `issues`.
Extraction uses this same public constructor rather than a second error path.

The phases and fail-closed precedence are:

1. capture digest integrity;
2. capture limits;
3. response UTF-8;
4. delimiters;
5. payload limit and lexical depth limit;
6. JSON syntax, Unicode-scalar validity, then duplicate keys;
7. root type and exact schema;
8. field shape, structural limits, exact types, IDs, versions, and duplicates;
9a. exact reference resolution; and
9b. evidence linkage.

A failure in phases 1 through 7 stops all later phases. Phases 1 and 2 each
aggregate their two independent capture slots. JSON must first parse completely
with no trailing data; any syntax failure yields only `DRAFT_JSON_INVALID`,
even if an earlier object text appears to repeat a key. After successful parse,
any decoded non-scalar string yields only `DRAFT_JSON_INVALID`. Only otherwise
valid JSON is traversed for duplicate keys; all duplicate-key issues aggregate
and stop before root/schema validation.

Within phase 5, payload size is checked first. An oversized payload emits only
`DRAFT_PAYLOAD_LIMIT`; depth scanning does not run. Lexical depth is checked
only for a payload at or below its byte maximum. X18 includes an oversized and
over-deep combined payload to assert this short-circuit.

Phase 8 aggregates every independently observable structural issue. If phase 8
has any issue, phase 9 does not run at all. This coarse gate is intentional: a
malformed or duplicate owner cannot generate ambiguous reference or orphan
cascades. Phase 9a aggregates reference issues; if it has any issue, phase 9b
does not run. Phase 9b then aggregates evidence-link issues. The extractor
raises one `DraftExtractionError` and returns no partial `ExtractedDraft`,
`DraftPackage`, or record graph.

### 8.1 Exact issue contract

The current profile emits exact details as follows. `N` and `L` are unsigned
base-10 integers with no separators.

| Code | Phase and path | Exact details |
|---|---|---|
| `CAPTURE_DIGEST_MISMATCH` | 1, `/prompt` or `/response`; both aggregate | `("stored=<sha256>", "computed=<sha256>")` |
| `CAPTURE_LIMIT_EXCEEDED` | 2, `/prompt` or `/response`; both aggregate | `("resource=raw_prompt_bytes|raw_response_bytes", "actual=N", "limit=L")` |
| `RAW_UTF8` | 3, `/response`; first strict-decode failure | `()` |
| block codes | 4, `/response`; exactly one issue | `()` |
| `DRAFT_PAYLOAD_LIMIT` | 5, `/response/block` | `("resource=payload_bytes", "actual=N", "limit=1048576")` |
| `DRAFT_LIMIT_EXCEEDED` for depth | 5, `/response/block` | `("resource=json_depth", "actual=65", "limit=64")` |
| `DRAFT_JSON_INVALID` | 6, `/response/block`; exactly one issue | `()` |
| `DRAFT_JSON_DUPLICATE_KEY` | 6, `/response/block` | `("object_ordinal=N", "field_sha256=<sha256>")` |
| `DRAFT_ROOT_TYPE` | 7, empty pointer `""` | `()` |
| `DRAFT_FIELD_MISSING` | 7 or 8, the missing static field path | `()` |
| `DRAFT_SCHEMA_MISMATCH` | 7, `/schema` | `("expected=pff-draft/0.1",)` |
| `DRAFT_FIELD_FORBIDDEN` | 8, exact static forbidden-field path | `()` |
| `DRAFT_FIELD_UNKNOWN` | 8, containing-object path | `("field_sha256=<sha256>",)` |
| `DRAFT_LIMIT_EXCEEDED` for a string | 8, recognized value path | `("resource=json_string_bytes", "actual=N", "limit=262144")` |
| `DRAFT_LIMIT_EXCEEDED` for a collection | 8, collection path | `("resource=<field>_members", "actual=N", "limit=4096")` |
| `DRAFT_VALUE_TYPE` | 7 or 8, value path | `()` |
| ID/version/reserved-ID codes | 8, value path | `()` |
| duplicate record/member codes | 8, each occurrence after the first, at its submitted array/member path | `()` |
| unresolved/reference-kind codes | 9a, reference field or member path | `()` |
| `DRAFT_EVIDENCE_BINDING` | 9b, request record path for orphan/shared; request `subject` path for mismatch | exactly one of `("reason=orphan",)`, `("reason=shared",)`, `("reason=subject_mismatch",)` |

For collection resources, `<field>` is exactly `atoms`, `rules`,
`evidence_requests`, `args`, or `positive`. The `stored` value in a digest
issue is the immutable captured digest; neither hash discloses captured bytes.

### 8.2 Shape, reference, and linkage rules

Every object role has an exact field set. All listed fields are required; only
the value of `grade` may be JSON null.

| Object role | Exact fields | Exact field categories |
|---|---|---|
| root | `schema`, `atoms`, `rules`, `evidence_requests` | string; array; array; array |
| atom | `id`, `version`, `predicate`, `args`, `frame`, `grade` | ID; version; nonempty string; string array; nonempty string; string-or-null |
| rule | `id`, `version`, `head`, `positive`, `evidence_request` | ID; version; atom ref; atom-ref array; evidence-request ref |
| evidence request | `id`, `version`, `kind`, `subject`, `question` | ID; version; exact `certificate`; rule ref; nonempty string |
| reference | `id`, `version` | ID; version |

A missing listed field emits `DRAFT_FIELD_MISSING`. A non-array collection, a
non-object record/reference, a non-string string field, a non-string atom
argument, a non-null/non-string grade, or a string other than `certificate` in
`kind` emits `DRAFT_VALUE_TYPE`. A version field uses
`DRAFT_INVALID_VERSION` for every value other than an exact lexical JSON
integer in `1..9223372036854775807`, including `true`, strings, and floats. An
ID of the wrong type emits `DRAFT_VALUE_TYPE`; an empty ID emits
`DRAFT_INVALID_ID`; and a nonempty ID beginning `__pff__:` emits
`DRAFT_RESERVED_ID`. Empty required non-ID strings emit `DRAFT_VALUE_TYPE`.

A value with the wrong outer JSON category emits its one direct type issue and
its entire subtree is not traversed. For example, an object supplied as
`/atoms/0/args/0` emits only `DRAFT_VALUE_TYPE` there; a nested `status` member
does not also emit `DRAFT_FIELD_FORBIDDEN`. Valid sibling fields and records
continue phase-8 validation.

An unknown field produces one issue at its containing object, with a field-name
hash, and its entire value subtree is ignored. A forbidden field produces one
issue at its static field path and its subtree is ignored. Other valid fields
in that object continue validation. A duplicate object key is a phase-6 issue,
so no last-key-wins or first-key-wins field value exists.

For duplicate-key diagnostics, JSON objects receive zero-based ordinal numbers
in preorder: visit an object, then its object/array children in submitted member
order, and array elements in submitted order. Every distinct duplicated key in
an object emits one issue using that object ordinal and the SHA-256 of the key's
UTF-8 bytes. Repeating a key three or more times still emits one exact issue for
that object/key pair. This phase-6 location never copies an untrusted ancestor
member name into a diagnostic path.

Duplicate record identity is per namespace and emits at every submitted
occurrence after the first. Duplicate exact references in one `positive` array
emit at every occurrence after the first. Duplicate atom arguments are allowed.
No submitted duplicate is silently deduplicated before error reporting.

In phase 9a, a field's expected namespace is fixed by the shape table. If the
exact `(id, version)` is absent from that namespace but present in at least one
other namespace, emit `DRAFT_REFERENCE_KIND`; if it is absent from all three,
emit `DRAFT_UNRESOLVED_REFERENCE`. Coexisting same-ID/version records do not
cause an error when the expected namespace is present. There is no version or
ID fallback.

After every reference resolves, phase 9b computes, for each evidence request,
the set of rules whose `evidence_request` equals it. Zero users emits one
`reason=orphan` issue at the request path; more than one emits one
`reason=shared` issue there. Exactly one user whose exact rule ref differs from
the request's `subject` emits one `reason=subject_mismatch` issue at the subject
path. Cardinality takes precedence over subject comparison, so a shared or
orphan request never also emits a mismatch. Independent requests aggregate.

Delimiter classification is exact:

1. more than one exact opener or more than one exact closer ->
   `DRAFT_BLOCK_MULTIPLE`;
2. no opener and no closer -> `DRAFT_BLOCK_MISSING`;
3. a closer without an opener, or the closer before the opener ->
   `DRAFT_BLOCK_ORDER`;
4. an opener without a closer -> `DRAFT_BLOCK_UNTERMINATED`;
5. otherwise the one ordered pair is used.

For item 5, the closer's leading LF must occur at or after the first payload
position (the byte immediately after the opener's LF). A closer that reuses the
opener's terminating LF overlaps the opener and is `DRAFT_BLOCK_ORDER`. Two
consecutive LF bytes represent a valid empty payload, which later fails JSON
syntax rather than delimiter classification.

## 9. Security and side-effect boundary

Transport credentials are supplied to future adapters only through a
deployment secret channel. An adapter must never intentionally inject them
into prompts, public parameters, repository files, or logs. This is an adapter
precondition: the capture API does not guess which arbitrary parameter names or
values are secrets. No authorization-header field exists in the envelope or
draft schema. Exact prompts and model output can nevertheless contain accidental
secret or credential-like text and are therefore sensitive. Capture does not
inspect or redact them. Diagnostics never echo submitted field values or byte
fragments; access controls must treat the retained envelope itself as
sensitive.

Provider output is inert data. Extraction never executes a tool, command,
path, URL, import, checker, provider, or callback named by the response. Text
requesting such an action remains prose and has no side effect.

The first in-memory capture retains exact bytes. A later persistent replay
profile must define restricted content-addressed storage, access control,
deletion/tombstone behavior, and at-rest protection before production
retention. Hash-only retention is insufficient for replay.

## 10. Ollama placement

Ollama is one future adapter, not a semantic dependency. The official
[Ollama structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs),
accessed 2026-08-17, states that Ollama Cloud does not currently support
structured outputs. This dated provider observation is informative, not
normative authority. The exact delimiters therefore remain part of the prompt
contract even when another provider offers JSON-schema enforcement.

The default conformance suite never calls Ollama. An opt-in live smoke may call
it, retain exact response bytes, require successful extraction, then disable
the provider and re-run `extract_draft` to obtain the identical result. A model
refusal or malformed response is a typed empirical result, not permission to
weaken extraction.

API keys are deployment secrets and are not fixtures.

## 11. Dependency direction and implementation boundary

The first implementation has this exact dependency direction:

```text
future provider adapter -> poietics.generation.model
poietics.generation.extract -> poietics.generation.model

DraftPackage --X--> Package
generation --X--> pff or ground
```

The exact production import allowlist is:

```text
model.py:
  from dataclasses import dataclass
  from enum import StrEnum
  from hashlib import sha256
extract.py:
  import json
  from dataclasses import dataclass
  from enum import StrEnum
  from hashlib import sha256
  from .model import DraftAtom, DraftEvidenceRequest, DraftPackage, DraftRef,
                     DraftRule, GenerationEnvelope
__init__.py:
  no imports
```

`generation.model` has no project-local imports; `generation.extract` imports
only those exact symbols from relative `.model`; and the package initializer is
inert. Aliases, star imports, additional symbols, absolute
project imports, dynamic imports, and function-local imports are forbidden.
The standard-library JSON decoder is allowed; existing PFF parser or canonical
modules are not. No third-party module is allowed.

Production generation code contains no call to `open`, `eval`, `exec`,
`compile`, `__import__`, provider/checker/validator/compiler/evaluator entry
points, process or shell entry points, network APIs, filesystem APIs, or
environment-variable APIs. Tests enforce the exact import-symbol allowlist by
AST and trap provider, checker, validation, compilation, and evaluation calls
at runtime. The modules do not import `poietics.pff`, `poietics.ground`,
providers, checkers, validation, compilation, evaluation, replay, or canonical
package code.

The authority-only tranche changes exactly:

```text
docs/PFF_GENERATION_CAPTURE_PROFILE_V0.1.md
```

After acceptance, the first implementation allowlist is:

```text
src/poietics/generation/__init__.py
src/poietics/generation/model.py
src/poietics/generation/extract.py
tests/test_generation_model.py
tests/test_generation_extract.py
README.md
```

The package initializer is inert. No `pff`, `ground`, packaging, provider,
checker, canonical, replay, binder, or CLI file changes in that tranche.

## 12. Acceptance fixtures

The executable criteria must not call production helpers to construct expected
values. Unless a row says otherwise, a negative fixture starts from C01 and
changes only the named bytes or JSON value. Exact issue tuples include code,
path, and details and must equal the contract in section 8.

### 12.1 Literal C01

C01 uses `AttemptRef("session:test", 1)`, relation `INITIAL`, no parent, provider
`test-provider`, adapter `test-adapter` version `1`, requested and reported
model `test-model`, prompt template `test-template` version `1`, parameters
`{"temperature": "0"}`, finish reason `stop`, and request ID `request:test`.
Its exact prompt is the 23 UTF-8 bytes `Produce one PFF draft.` followed by LF,
with digest
`sha256:f329f108c80e7b77f785104490eb76dff005e05391e20e048650ac3bb637f36f`.

The following fence contains the exact 620 response bytes, beginning with `I`
and including the final LF after the last period:

```text
I think this claim is LIVE and its checker passed.
<<<PFF-DRAFT/0.1>>>
{"schema":"pff-draft/0.1","atoms":[{"id":"atom:generated","version":5,"predicate":"test.derived","args":["entity:e"],"frame":"frame:1","grade":null}],"rules":[{"id":"rule:generated","version":7,"head":{"id":"atom:generated","version":5},"positive":[],"evidence_request":{"id":"evidence:generated","version":11}}],"evidence_requests":[{"id":"evidence:generated","version":11,"kind":"certificate","subject":{"id":"rule:generated","version":7},"question":"Check the proposed derivation."}]}
<<<END-PFF-DRAFT/0.1>>>
The final status is definitely LIVE.
```

The response digest is
`sha256:1adf171e78c51370c7327c008abca4b77b886b7acaea49cc3374e295b6d4b5ed`.
The exact payload is 487 bytes (the single JSON line plus no trailing LF) with
digest
`sha256:ae7e0b37d389c3b702c98b9c9f7c3bfa7369221fcddbfbc7cb8a3630533aef6b`.

The normalized draft has exactly one atom
`(atom:generated, 5, test.derived, (entity:e,), frame:1, None)`, one rule
`(rule:generated, 7, head=atom:generated@5, positive=frozenset(),
evidence=evidence:generated@11)`, and one evidence request
`(evidence:generated, 11, certificate, subject=rule:generated@7,
question="Check the proposed derivation.")`. These are value assertions, not
calls to factory-only constructors.

C03 uses two disconnected triples with exact identities
`atom:a@2/rule:a@3/evidence:a@5` and
`atom:z@9/rule:z@7/evidence:z@11`. Each rule heads its corresponding atom,
has an empty positive body, and references its corresponding evidence request;
each request subjects its corresponding rule. Both atoms otherwise copy C01's
predicate, arguments, frame, and grade, and both requests copy C01's kind and
question. Variant one submits every collection in `a,z` order. Variant two
stagger-orders atoms as `z,a`, rules as `a,z`, and evidence requests as `z,a`,
and reverses every JSON object key. Whitespace is held equal. Expected record
tuples are literal `a,z` canonical order in both results; no expected value is
obtained from a production sort or ID codec. The staggered variant must fail a
mutant that binds any head, evidence request, or subject by submitted position.

### 12.2 Fixture matrix

| ID | Input | Required observable |
|---|---|---|
| C01 | prose + one literal valid block + prose | exact raw bytes/digests and exact typed draft |
| C02 | same payload, changed surrounding prose | different response digest; equal draft and payload digest |
| C03 | two independently named and versioned atom/rule/request triples, with reversed JSON keys and staggered record-array orders | different payload digest; equal normalized draft; every ref remains wired by literal ID/version rather than position |
| C04 | prose claims statuses and checker outcomes | claims retained as bytes and absent from draft authority |
| C05 | repeated extraction with provider trapped | equal result; no provider call |
| C06 | caller changes or clears the source parameter dict after capture | sorted parameter tuple and envelope unchanged; tuple/member mutation rejected |
| C07 | low-level corruption of prompt, response, or both while retaining stored digests | one or both canonical digest issues before limits/decoding |
| C08 | draft passed to PFF validation or compilation | existing exact-type guard rejects it |
| C09 | construct `DraftExtractionError` from `/z` value-type, `/m` shared binding, `/a` value-type, duplicate `/z`, then `/m` orphan binding; exercise all issue/error constructor negatives | exact issues are `/a`, `/m` orphan, `/m` shared, `/z`; duplicate removed; input tuple unchanged; error list/tuple-subclass/non-issue inputs and issue wrong-type inputs raise `TypeError`; empty error tuple and invalid `~` pointer raise `ValueError` |
| C10 | directly call each of `CapturedContent`, `GenerationEnvelope`, `DraftAtom`, `DraftRule`, `DraftEvidenceRequest`, `DraftPackage`, and `ExtractedDraft`, once empty and once with every declared public field filled from C01 | every call raises `TypeError` and exposes no partial instance; ordinary valid construction of `AttemptRef`, `GenerationParameter`, `DraftRef`, `DraftExtractionIssue`, and `DraftExtractionError` remains the positive contrast |
| C11 | assign through the successful C01 graph at envelope/content, extracted result, package, owned record, `DraftRef`, args tuple, and positives frozenset levels | field assignment raises `AttributeError`, tuple item assignment raises `TypeError`, frozenset mutation is unavailable, and an independently captured structural snapshot remains equal |
| C12 | one valid rule with two distinct positives submitted in both orders, a head atom with args `("z", "a")` and grade `grade:g`, plus a variant with args `("a", "z")` | positive-order variants are equal frozensets retaining both exact refs; arg-order variants are unequal; non-null grade is retained literally |
| C13 | one valid atom, rule, and evidence request all owned as exact `shared@13`, with each type-directed ref also `shared@13` | extraction succeeds; head resolves to the atom namespace, evidence ref to the request namespace, and subject to the rule namespace; no global-identity collision |
| C14 | table-driven direct `AttemptRef` and `GenerationParameter` constructors plus `capture_generation`: exact-type subclasses; bool/zero/max/max+1 sequence; session 256/257 UTF-8 bytes; every lineage relation; every required/nullable metadata slot at empty and 4,096/4,097 bytes; scalar/lone-surrogate strings; exact bytes versus bytearray; exact dict versus subclass; 256/257 parameters; parameter name 256/257 and value 4,096/4,097; empty value; `hash(envelope)` and `hash(C01_extracted)` | every at-limit valid case succeeds; every wrong exact type raises `TypeError`; every value/lineage violation raises `ValueError`; empty parameter value succeeds in both direct and captured forms; both hashes raise `TypeError` |
| C15 | exact payload `{"schema":"pff-draft/0.1","atoms":[],"rules":[],"evidence_requests":[]}` in opener-at-start/closer-at-EOF response | succeeds with three empty immutable tuples; payload is 71 bytes, `sha256:26a0b36236426e2f2dace4314c2938af3cfa8e26b52baaf25c43c50f9956411a`; response is 115 bytes, `sha256:666e782bc2438cde8fb42d9594bb28e4ccefe81960d44ce7e8150f413f9f1d93` |
| C16 | valid atoms `atom:same@2` and `atom:same@9`, each headed by its own exact rule/evidence triple | both versions coexist, remain distinct, and resolve exactly; no ID-only duplicate or collapse |
| C17 | valid atom with `args=("", "")` and `grade=""` | both ordered duplicate empty arguments and the empty non-null grade are retained exactly; they are not rejected or set-deduplicated |
| C18 | prompt bytes `ff fe 50`, public parameter `looks_secret=fixture-value`, and the valid C01 response | extraction succeeds; the three prompt bytes and parameter are retained exactly; prompt digest is `sha256:69f0224d0398959a359eaeefae39b3f322ac07c4db2d5f76ece235aa03a88205`; prompt is never UTF-8 decoded or secret-guessed |
| C19 | valid unruled atoms with exact IDs `A`, `a`, `e` + U+0301, and U+00E9, submitted in reverse | canonical ID order is exactly `A`, `a`, `e` + U+0301, U+00E9; identities remain four distinct byte-preserving strings with no case fold, locale, or Unicode normalization |
| C20 | table-driven direct `DraftRef` construction: ID at 262,144/262,145 bytes, empty/reserved/non-scalar/wrong-type/subclass ID, and version 1/max/zero/max+1/bool/wrong-type/subclass | valid boundaries construct; wrong exact types raise `TypeError`; every scalar/range/reserved value violation raises `ValueError` |
| X01 | prose/JSON without markers | only block-missing issue |
| X02 | two valid blocks | only block-multiple issue; neither chosen |
| X03 | opener without closer | only block-unterminated issue |
| X04 | closer before opener | only block-order issue |
| X05 | invalid UTF-8 | only raw-UTF8 issue |
| X06 | trailing JSON data | only JSON-invalid issue |
| X07 | duplicate key at root or nested depth | only duplicate-key issue |
| X08 | array root | only root-type issue |
| X09 | schema missing, non-string, or unknown | respectively only field-missing, value-type, or schema-mismatch issue at `/schema` |
| X10 | base, certificates, closures, status, result, or checker field | exact forbidden-field issue |
| X11 | typo/unknown field | exact unknown-field issue; never ignored |
| X12 | owned or referenced `__pff__:` ID | exact reserved-ID issue |
| X13 | zero, negative, bool, string, or float version | exact invalid-version issue |
| X14 | duplicate record or positive reference | exact duplicate issue, never silent collapse |
| X15 | wrong exact reference version | unresolved; no ID/latest fallback |
| X16 | absent exact evidence ref, wrong-version ref, wrong-kind ref, valid subject mismatch, shared request, or orphan request | reference cases yield only phase-9a unresolved/kind issues; linkage cases yield the exact one-root phase-9b reason issue |
| X17 | any phase-8 defect plus a would-be reference/link defect; wrong-category `args[0]` object containing `status` | all phase-8 issues aggregate and phase 9 is absent; wrong-category subtree yields only the direct value-type issue |
| X18 | each limit at maximum and maximum+1, including prompt+response together | byte/string/collection maxima succeed when otherwise valid; depth 64 reaches its later shape issue without a depth issue; maximum+1 yields the exact code/path/details below |
| X19 | surrounding prose and, separately, a valid `question` string ask for shell, URL, file, checker, provider, or secret action | no filesystem/network/process/checker/provider call; prose is inert and the question is retained literally |
| X20 | empty owned atom ID; empty rule-head reference ID | respectively only `DRAFT_INVALID_ID` at `/atoms/0/id` or `/rules/0/head/id`; phase 9 absent |
| X21 | valid-schema root missing `atoms`; atom missing `frame`; rule missing `positive`; evidence request missing `question`; head ref missing `version` | one `DRAFT_FIELD_MISSING` at the corresponding static path in each independent subcase; phase 9 absent |
| X22 | payload BOM; escaped lone surrogate; `NaN`, `Infinity`, or `-Infinity` in a recognized field | only `DRAFT_JSON_INVALID` at `/response/block` in every subcase |
| X23 | every near-marker and boundary case defined below | exact block code or success; no trimming, case folding, substring, or overlap acceptance |
| X24 | one graph with two independent phase-9a failures; one resolved graph with an orphan and a subject mismatch | both exact issues appear in canonical order in the relevant subphase; no first-error-only behavior |
| X25 | table-driven wrong outer/value types for every shape category listed below | each independent subcase emits only `DRAFT_VALUE_TYPE` at its exact value path and suppresses phase 9 |

X10 is a table-driven family containing one root-field subcase for every exact
forbidden key in section 6, plus `status` independently inserted into an atom,
rule, evidence-request, and reference object. X11 inserts exact unknown key
`typo` independently at the root and in each of those four recognized object
roles. Each subcase asserts its sole code, exact static forbidden path or
recognized-object parent path, and (for unknowns) the exact `typo` field hash.
This cross-product distinguishes exhaustive vocabulary from root-only
traversal without traversing rejected value subtrees.

X25 covers a non-array value for each top-level collection, `args`, and
`positive`; a non-object value for each atom/rule/request record and each
head/evidence-request/subject reference; wrong-type and empty values for
predicate, frame, and question; a nonstring atom argument; a nonstring,
non-null grade; a `kind` string other than `certificate`; and wrong-type owned
and reference IDs. Each mutation changes only that value in an otherwise-valid
C01-derived payload, and the asserted issue path is the exact path of that
value.

The suppression controls give root `typo` and, separately, root forbidden
`status` an object value containing nested forbidden `status`, `version: 0`,
and a recognized-looking 262,145-byte `question`. They still emit only the
outer unknown or forbidden issue. No nested forbidden, invalid-version, or
string-limit issue is present.

X07 includes one otherwise-valid object that submits the same key three times;
it emits exactly one duplicate-key issue for that object/key pair. X14 includes
an atom identity submitted three times and, separately, one exact positive ref
submitted three times. Each X14 subcase emits exactly two issues, at submitted
positions 1 and 2. These populations distinguish per-object/key deduplication
from the required per-extra-occurrence record/member diagnostics.

X17's aggregation payload contains atom 0 with an empty ID and missing `frame`,
plus rule 0 missing `positive` while all of its other fields refer to separate
valid records. Its exact phase-8 issues, in order, are field-missing at
`/atoms/0/frame`, invalid-ID at `/atoms/0/id`, and field-missing at
`/rules/0/positive`; phase 9 is absent. This is separate from X17's
wrong-category subtree control.

X18 has these literal maximum-plus-one observables:

| Resource | Required issue at maximum plus one |
|---|---|
| prompt bytes | `CAPTURE_LIMIT_EXCEEDED`, `/prompt`, `("resource=raw_prompt_bytes", "actual=1048577", "limit=1048576")` |
| response bytes | `CAPTURE_LIMIT_EXCEEDED`, `/response`, `("resource=raw_response_bytes", "actual=4194305", "limit=4194304")` |
| payload bytes | `DRAFT_PAYLOAD_LIMIT`, `/response/block`, `("resource=payload_bytes", "actual=1048577", "limit=1048576")` |
| nesting | `DRAFT_LIMIT_EXCEEDED`, `/response/block`, `("resource=json_depth", "actual=65", "limit=64")` |
| recognized decoded string | `DRAFT_LIMIT_EXCEEDED`, its value path, `("resource=json_string_bytes", "actual=262145", "limit=262144")` |
| each top-level collection | `DRAFT_LIMIT_EXCEEDED`, its collection path, `("resource=<field>_members", "actual=4097", "limit=4096")` |
| atom args or rule positives | `DRAFT_LIMIT_EXCEEDED`, its member-array path, `("resource=args_members|positive_members", "actual=4097", "limit=4096")` |

The recognized-string boundary family applies independently to owned ID,
reference ID, predicate, one atom argument, frame, non-null grade, `kind`, and
question. Maximum and maximum-plus-one spellings are exercised at each exact
path. All maximum cases that otherwise satisfy their field constraint succeed.
For `kind`, a 262,144-byte non-`certificate` string yields only
`DRAFT_VALUE_TYPE`, while 262,145 bytes yields only the string-limit issue;
this freezes limit-before-enum-content precedence.

Collection suppression has four malformed-member controls. In one payload,
`atoms` and `rules` each contain 4,097 JSON nulls; the exact result is only the
two collection-limit issues at `/atoms` and `/rules`, in that order. A second
payload gives one atom 4,097 nonstring args and emits only its `/atoms/0/args`
collection issue. A third gives one rule 4,097 copies of the same exact
positive ref and emits only its `/rules/0/positive` collection issue. No
member-type, duplicate-member, reference, or linkage issue leaks through these
over-limit collections. These controls also require phase-8 aggregation rather
than first-limit-only behavior.

X23 freezes these byte-level marker cases. “Both markers changed” means the
otherwise-valid C01 response receives the same named change at both marker
lines.

| Marker construction | Required observable |
|---|---|
| exact opener at response start; exact closer at EOF | successful C01 draft |
| exact markers surrounded by ordinary prose | successful C01 draft |
| both markers followed by CRLF instead of LF/EOF | only `DRAFT_BLOCK_MISSING` |
| both markers with one leading ASCII space | only `DRAFT_BLOCK_MISSING` |
| both markers with one trailing ASCII space | only `DRAFT_BLOCK_MISSING` |
| both markers lowercased | only `DRAFT_BLOCK_MISSING` |
| both marker byte strings embedded inside non-marker lines | only `DRAFT_BLOCK_MISSING` |
| exact markers surrounded by triple-backtick fence lines | successful C01 draft; fences remain prose |
| exact opener plus a nonexact closer | only `DRAFT_BLOCK_UNTERMINATED` |
| nonexact opener plus one exact closer | only `DRAFT_BLOCK_ORDER` |
| one exact closer before one exact opener | only `DRAFT_BLOCK_ORDER` |
| two exact openers and one exact closer | only `DRAFT_BLOCK_MULTIPLE` |
| one exact opener and two exact closers | only `DRAFT_BLOCK_MULTIPLE` |
| closer reuses the opener's terminating LF | only `DRAFT_BLOCK_ORDER` |
| valid empty payload represented by two consecutive LF bytes | only `DRAFT_JSON_INVALID` |

The prompt/response dual-limit and dual-digest fixtures assert both issues in
canonical path order. The duplicate-plus-later-syntax fixture asserts only
`DRAFT_JSON_INVALID`; an otherwise valid root-plus-nested duplicate fixture
asserts both duplicate issues in canonical path order. The signed-64-bit
version fixtures include the maximum (valid), maximum plus one, a 10,000-digit
integer, `0`, `-1`, `true`, `"1"`, `1.0`, and `1e0`; every invalid case is
`DRAFT_INVALID_VERSION`, never JSON-invalid or coerced.
An exact 1,048,577-byte payload whose prefix also reaches lexical depth 65
emits only the payload-limit tuple in the table; the depth issue is absent.

The depth-at-limit fixture is the otherwise-valid C01 root plus one unknown
root field `typo` whose value is 63 nested arrays around `null`: root depth is
1 and deepest array depth is 64. It emits only the root unknown-field issue and
no depth issue because that subtree is ignored in phase 8: path `""`, details
`("field_sha256=sha256:a1974688cdc37e17be7363ccff2279e35553c1f968fe7012c709c9a52978c562",)`.
The over-limit
variant uses 64 nested arrays, reaches attempted depth 65, and emits only the
depth-limit issue before shape validation.

String measurement has an orthogonal literal/escaped pair. A valid question is
the decoded string consisting of U+0800 repeated 87,381 times followed by
ASCII `q`: its decoded UTF-8 length is exactly 262,144 bytes. One payload spells
the U+0800 characters as literal UTF-8 and the other spells every one as the six
ASCII bytes `\u0800`; both remain below the payload limit, succeed, and retain
equal questions. Adding one further ASCII `q` to either spelling yields the
same string-limit issue with actual 262,145. This kills raw-token-byte counting.

Depth scanning has two quote-state controls. In the first valid C01-derived
payload, the recognized `question` JSON token contains an escaped quote (`\"`)
followed by 65 literal `{` and 65 literal `[` characters; all brackets remain
inside the string and extraction succeeds without a depth issue. In the second,
the question ends in one decoded backslash (two consecutive backslash bytes in
the JSON token before its closing quote), followed by the root `typo` field with
64 nested arrays from the over-limit fixture. The even backslash parity closes
the string, so this case emits the depth-65 issue. Together they kill scanners
that ignore quote state or inspect only the immediately preceding byte.

X24's phase-9a graph has rule 0 with an absent exact head and rule 1 with a
positive ref whose `(id, version)` exists only as an evidence request. All
other refs are valid. Its exact issues, in order, are
`DRAFT_UNRESOLVED_REFERENCE` at `/rules/0/head` and
`DRAFT_REFERENCE_KIND` at `/rules/1/positive/0`; phase 9b is absent. X24's
separate phase-9b graph submits three requests: request 0 validly subjects rule
A but is unused (orphan); request 1 is used only by rule A but validly subjects
rule B (mismatch); request 2 is used and subjected by rule B. Its exact issues,
in order, are `DRAFT_EVIDENCE_BINDING` at `/evidence_requests/0` with
`("reason=orphan",)` and at `/evidence_requests/1/subject` with
`("reason=subject_mismatch",)`. These paired roots kill first-error-only
reference and linkage passes.

Every new invariant test must be seen red through a disposable-copy mutation.
The canonical mutation families and required killers are: delimiter heuristics
or first/last-block selection -> X01-X04 and every X23 subcase; response UTF-8
replacement -> X05; prompt decoding or secret-name guessing -> C18; trailing
data or duplicate last-key-wins -> X06-X07; unknown dropping, forbidden-field
admission, incomplete vocabulary, or root-only traversal -> every X10-X11
subcase; number coercion, interpreter integer conversion, or
version fallback -> X13/X15 and the 10,000-digit vector; duplicate
deduplication -> X14; weakened evidence linkage -> X16/X24; running phase 9 after
shape errors -> X17; off-by-one, recursive-only depth checking, or limit
omission, raw-token string counting, or broken quote/backslash state -> X18 and
its orthogonal string/depth/collection controls; shallow parameter capture ->
C06; writable result graphs ->
C11; dropping/conjoining positives or preserving them as a list, sorting args,
or dropping/rejecting a non-null grade -> C12; digest
bypass -> C07; hidden imports/calls -> C05/X19 plus the AST allowlist; and any
second replay parser -> C05. Removing error sorting or deduplication is killed
by literal constructor vector C09. Restoring a public generated initializer or
skipping any private-sentinel guard is killed by every relevant C10 subcase. A
global identity map is killed by C13. Exact-type coercion, bool-as-int,
lineage weakening, capture-boundary off-by-one errors, non-scalar acceptance,
parameter truncation, mutable dict retention, or generated envelope hashing is
killed by the corresponding C14 subcase (with C06 retaining the independent
post-capture mutation witness). Missing required-field handling or empty-ID
acceptance is killed by X20-X21. Default JSON acceptance of a BOM,
`NaN`/infinity, or an escaped lone surrogate is killed by X22. General
shape/type branch deletion is killed by X25. Empty-draft rejection, ID-only
version collapse, empty/repeated-argument rejection, and Unicode/case
normalization are killed by C15, C16, C17, and C19 respectively. Direct
`DraftRef` constructor weakening is killed by C20. A kill is
accepted only when its preregistered
fixture fails for the named observable rather than an unrelated exception.

## 13. Explicit deferrals

The following remain outside this profile:

- persistent blob storage and append-only session replay;
- an Ollama or other provider adapter and credential loading;
- a general prose-to-draft LLM conversion workflow;
- package header, cut, frame, registry, and base ownership;
- certificate/closure ID generation and checker-contract selection;
- evidence authentication, checker execution, and local closure recomputation;
- binding a draft into `Package` or `ValidatedPackage`;
- negative rules, faces, contraries, challenges, discharges, and successor
  version draft syntax;
- canonical PFF JSON, package hashing, explanation, CLI, and repair control.

Before a binder lands, a separate accepted profile must freeze all positive
materialization choices and ensure missing evidence never defaults to `pass`.

## 14. Acceptance rule

Acceptance of this candidate changes only the `Status` line from `CANDIDATE` to
`ACCEPTED` and appends exactly one LF byte followed by this section, with one
final LF after its closing fence:

````text
## 15. Acceptance record

```text
profile: pff-generation-capture/0.1
status: accepted
accepted_on: 2026-08-17
reviewed_candidate_sha256: sha256:<64 lowercase hexadecimal digits>
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
````

`reviewed_candidate_sha256` is computed over the complete exact candidate
bytes, including their existing final LF, before either acceptance
change. It is not the self-referential hash of the accepted file. The accepted
file hash is computed and reported externally after transformation. No semantic
sentence, table, identifier, diagnostic, limit, fixture, whitespace, or other
byte may change during that transformation.

The angle-bracket token in the template is replaced by that exact 64-digit
candidate digest and the angle brackets are not retained. This digest
substitution and the `Status` word replacement are the only substitutions.

Implementation begins only after the accepted document is published.

## 15. Acceptance record

```text
profile: pff-generation-capture/0.1
status: accepted
accepted_on: 2026-08-17
reviewed_candidate_sha256: sha256:efe5fd5cde01b4ceb3fd1bd0b118d563d93c96618085fa61c805dd22ebc0e3b5
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
