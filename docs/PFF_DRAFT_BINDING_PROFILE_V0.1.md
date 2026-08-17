# PFF Draft Binding Profile v0.1

**Status:** ACCEPTED SEMANTIC PROFILE

**Date:** 2026-08-18

**Implementation baseline:** `7bcf73c97df03a961cfba25fbeca68cf21146ded`

**Scope:** bind one exact extracted `pff-draft/0.1` graph, one code-owned
policy, and authority-asserted evidence into one provenance-bearing candidate
`Package`

## 1. Purpose, authority, and gap classification

This profile supplies semantics that the accepted generation-capture profile
deliberately deferred. The gap is an **absence**: existing authority requires a
trusted binder but does not determine final record identities, checker routing,
evidence-task binding, missing-evidence behaviour, or the provenance returned
with the candidate package.

The authority order is:

1. `poietic-pff-implementable-core-spec-v0.1.md`, SHA-256
   `43f4c4cb50292feccf2b0fc45e517d1ec4bf60c908600b96169ce4702bc99aa9`;
2. accepted `docs/PFF_CORE_V0.1_CHALLENGE_PROFILE.md`, SHA-256
   `6e4bab9865db3c1cbdd160eaf80dcbf0d66716152e2a0be0b36deedddeafdf07`;
3. accepted `docs/PFF_GENERATION_CAPTURE_PROFILE_V0.1.md`, SHA-256
   `bdda03645aec07681dd817244cfb7ab4981102090c0f3bf17cc70cbf1676bfa4`;
4. this document after separate review and explicit acceptance; and
5. the implementation baseline above, as evidence about existing public types
   and dependency direction, never as semantic authority.

`LESSONS_LEARNED_2026-08-17.md`, SHA-256
`9b4fe50618b53260e1d32533a2709da5a367c337adf35ced8c109e4fbaa25f7a`,
is implementation guidance only.

Rules use these provenance tags:

| Tag | Meaning |
|---|---|
| `[S]` | Direct restatement of controlling authority |
| `[C]` | Clarification selecting a reading already required by controlling authority |
| `[N]` | New normative choice required to close the binder absence |
| `[D]` | Explicit deferral to a later named boundary |

There are no new digest preimages or generated content-addressed identities in
this profile. All authoritative package `RecordRef` values are supplied
explicitly by policy. Existing extraction and evidence payload digests are
compared or retained as exact strings; the binder neither recomputes an
evidence payload hash nor claims what bytes it authenticates.

## 2. Thin waist and stopping answer

`[S]` The binder remains between untrusted generation and PFF admission:

```text
GenerationEnvelope -> extract_draft -> exact ExtractedDraft
                                      + code-owned DraftBindingPolicy
                                      -> plan_draft_binding -> BindingPlan
BindingPlan + authority EvidenceAttestation values
                                      -> finalize_draft_binding -> BoundPackage
BoundPackage.package -> validate_package -> ValidatedPackage
```

`[C]` The binder accepts an exact, factory-only `ExtractedDraft`, not a naked
`DraftPackage`, mapping, JSON object, model response, or duck-typed substitute.
It does not call `extract_draft`: the capture profile's successful factory
boundary is the input authority here. A private factory guard is not a hostile
Python sandbox and is not evidence authentication.

The challenge profile's section 2 explicitly marked its generation type names
and protocol provisional. This profile preserves that section's architectural
constraint but derives the concrete source boundary from the later accepted
generation-capture profile, not from the provisional sketches.

`[N]` Binding is two-phase. Planning must freeze every authoritative package
identity and evidence task before any evidence result is accepted. Finalization
must require the complete exact task population before it constructs a
candidate. A one-phase function that lets an evidence result choose its own
checker, subject, certificate identity, frame, cut, or registry is
nonconforming.

`[S]` LLM prose, claims of checker success, requested semantic status, and the
evidence-request question are never evidence. `[N]` The exact question is
retained in its evidence task so an authority can know what was requested, but
it is untrusted text: it cannot select a route, run an action, or override the
checker contract.

`[C]` Finalization returns a candidate `BoundPackage`. It does not call
`validate_package` and does not return a `ValidatedPackage`. The one existing
validator remains the only PFF admission path, and callers must invoke it
explicitly. The compiler continues to require its factory-only
`ValidatedPackage` capability.

## 3. Exact public model

The public profile identifiers are:

```text
pff-draft-binding-policy/0.1
pff-evidence-task/0.1
pff-evidence-attestation/0.1
pff-draft-binding-plan/0.1
pff-bound-package/0.1
```

All classes in this section are frozen and slotted. Unless a rule below says a
class is factory-only, it is an ordinary public value. Exact-type rules reject
subclasses as well as unrelated values.

The binding-owned limits are:

| Resource | Maximum |
|---|---:|
| one binding-owned UTF-8 string | 262,144 bytes |
| one `BindingIssue.details` member | 262,176 UTF-8 bytes |
| one version or positive authority ordinal | 9,223,372,036,854,775,807 |
| one signed evidence-detail integer magnitude | 9,223,372,036,854,775,807 |
| `record_bindings` | 8,192 members |
| `evidence_bindings`, planned tasks, final evidence | 4,096 members each |
| one attestation `details` tuple | 4,096 members |
| derived plan-origin upper bound (not an admission limit) | 12,288 members |

A binding-owned string is an exact `str` containing only Unicode scalar values
and no more than the table's UTF-8 limit. Profiles and identifiers are also
nonempty. `EvidenceTask.question` and an evidence-detail string value are not
identifiers and may be empty in their ordinary direct constructors; every task
actually produced from an accepted `ExtractedDraft` still inherits the
extractor's nonempty question invariant. A version is an exact
positive `int` within the table; `bool` is not an integer here. An evidence
detail integer is an exact `int`, not `bool`, in the inclusive signed range
`[-9_223_372_036_854_775_807, 9_223_372_036_854_775_807]`. A SHA-256 value is
exactly `sha256:` followed by 64 lowercase hexadecimal digits.

Wrong scalar, enum, member, or collection types raise `TypeError`. An invalid
profile literal, empty required string, surrogate, UTF-8 limit excess, numeric
range failure, collection maximum plus one, forbidden source kind, or duplicate
constructor key raises `ValueError`. An exact tuple is required wherever the
public shape says tuple; lists and tuple subclasses are rejected.

There is one deliberate embedded-value exception. `DraftRef` validates its own
accepted source values. An exact `RecordRef` embedded as a policy target is
accepted by the ordinary binding-value constructor even if its ID is empty,
non-scalar, oversized, reserved, or its version is nonpositive or above the
maximum. Phase 30 is the sole owner of those target diagnostics. Other embedded
`RecordRef` values, including evidence-detail references, remain PFF candidate
data for the later validator.

Every order called lexicographic in this profile compares the integer returned
by `ord()` for each Python string element, with a shorter sequence first when
it is an exact prefix. This comparator deliberately also orders surrogate code
points carried by an invalid embedded `RecordRef`, so phase-20 and phase-30
diagnostics remain deterministic before scalar validity is established. There
is no normalization, case folding, locale, collation library, UTF-8-byte
comparison, or platform order. Numeric versions compare as integers.

### 3.1 Local source identity and authoritative record mapping

```python
class DraftRecordKind(StrEnum):
    ATOM = "atom"
    RULE = "rule"
    EVIDENCE_REQUEST = "evidence_request"

@dataclass(frozen=True, slots=True)
class DraftSource:
    kind: DraftRecordKind
    ref: DraftRef

@dataclass(frozen=True, slots=True)
class RecordIdentityBinding:
    source_kind: DraftRecordKind
    source: DraftRef
    target: RecordRef

@dataclass(frozen=True, slots=True)
class EvidenceBinding:
    request: DraftRef
    certificate: RecordRef
    checker_id: str
    checker_version: int
    authority_id: str
    authority_version: int
```

`[N]` A `RecordIdentityBinding.source_kind` is only `ATOM` or `RULE`.
`EVIDENCE_REQUEST` is valid in `DraftSource` but invalid in this binding type.
This distinction prevents an evidence request from being silently materialised
as an atom or rule.

`[N]` Draft IDs and versions are local, untrusted, type-directed handles. They
are not PFF stable identities. A code-owned policy supplies every final atom,
rule, and certificate `RecordRef`. This permits a local atom and rule to share
the same `DraftRef` while mapping to distinct authoritative targets, and it
prevents changed model text from acquiring an old package identity merely by
repeating an ID and version.

### 3.2 Code-owned policy

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class DraftBindingPolicy:
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
```

`profile` is exactly `pff-draft-binding-policy/0.1`. The policy is ordinary
immutable code-owned data, like the current registry definitions; it is not a
callback and is not constructed from LLM output. `source_payload_sha256` binds
it to exactly one extracted payload.

The constructor requires exact tuples and exact members. It rejects duplicate
record-binding source keys `(source_kind, source.id, source.version)` and
duplicate evidence-binding request keys `(request.id, request.version)`.
It rejects more than 8,192 record bindings or 4,096 evidence bindings.
It canonicalizes `record_bindings` by the absolute kind order `ATOM`, `RULE`,
then source ID under the Unicode-scalar order and numeric version. It
canonicalizes `evidence_bindings` by request ID under that order and numeric
version. Submitted tuple order has no meaning.
Coverage, target validity, cross-binding target collisions, and registry
coherence are planning diagnostics rather than constructor failures.

### 3.3 Evidence task

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceTask:
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
```

`profile` is exactly `pff-evidence-task/0.1` and `request_kind` is exactly
`certificate`. `subject_rule` is the complete exact planned `RuleRecord`,
including its authoritative ref, mapped head, mapped positive body, mapped
certificate, and exact empty negative and face sets. `question` is the exact
extracted question string, with no
normalization, trimming, templating, execution, or reinterpretation. The
remaining fields are exact structural bindings to the source payload, policy,
mapped rule semantics, mapped certificate, checker contract, expected evidence
authority, and package context.

Evidence-task identity is structural equality over every public field,
including every `subject_rule` field. It is
never Python object identity and this profile defines no task digest. Tasks are
canonically ordered by request ID under the Unicode-scalar order and numeric
version.

### 3.4 Authority assertion and evidence details

```python
EvidenceDetailValue = str | int | bool | RecordRef

@dataclass(frozen=True, slots=True)
class EvidenceDetail:
    key: str
    value: EvidenceDetailValue = field(repr=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceAttestation:
    profile: str
    task: EvidenceTask
    authority_id: str
    authority_version: int
    attestation_id: str
    attestation_version: int
    result: CheckResult
    payload_hash: str
    details: tuple[EvidenceDetail, ...] = field(repr=False)
```

`profile` is exactly `pff-evidence-attestation/0.1`. An evidence-detail key is
an exact nonempty Unicode-scalar string. Its value is exactly one of `str`,
`int`, `bool`, or `RecordRef`; subclasses and every container, float, null, and
other object are rejected. This is precisely the value vocabulary that current
`CheckerDetailType` members can inspect. Detail strings may be empty because
the registry, not the binder, owns the distinction between `STRING` and
`NONEMPTY_STRING`.

`details` is an exact tuple, contains at most 4,096 exact `EvidenceDetail`
members, has unique keys, and is canonicalized by key. The `result` is an exact
`CheckResult`. `payload_hash` has the exact SHA-256 spelling defined above.

`[N]` `EvidenceAttestation` is intentionally an ordinary publicly
constructible immutable value, not a factory-only capability. It is a
structural assertion that a named authority made one result for one task. This
binder checks the asserted task and authority bindings; it does **not** prove
that the assertion is authentic. A private constructor token would not supply
authentication and must not be described as doing so.

Ordinary public binding dataclasses are frozen, slotted, structurally
hashable, and have no `__dict__`. Their generated
representations must not contain the evidence-task `question` or evidence
detail values; `EvidenceTask.question`, `EvidenceDetail.value`, and
`EvidenceAttestation.details` are `repr=False`. Factory-only `BindingPlan`
and `BoundPackage` reject ordinary construction with `TypeError`, are deeply
immutable and explicitly unhashable, and exclude their source and evidence
fields from generated representations.

`[N]` Attestation identity is
`(authority_id, authority_version, attestation_id, attestation_version)`. It
must be unique within one successful finalization. Cross-package uniqueness,
signatures, durable authority ledgers, and rehydration are deferred.

### 3.5 Origins, plan, and bound candidate

```python
class BindingRole(StrEnum):
    DRAFT_ATOM = "draft-atom"
    DRAFT_RULE = "draft-rule"
    EVIDENCE_CERTIFICATE = "evidence-certificate"

@dataclass(frozen=True, slots=True)
class BindingOrigin:
    target_kind: RecordKind
    target: RecordRef
    role: BindingRole
    source: DraftSource

@dataclass(frozen=True, slots=True, init=False)
class BindingPlan:
    profile: str
    source: ExtractedDraft
    policy: DraftBindingPolicy
    catalog: RegistryCatalog
    registry: PredicateRegistry
    header: PackageHeader
    atoms: tuple[AtomRecord, ...]
    rules: tuple[RuleRecord, ...]
    tasks: tuple[EvidenceTask, ...]
    origins: tuple[BindingOrigin, ...]

@dataclass(frozen=True, slots=True, init=False)
class BoundPackage:
    profile: str
    plan: BindingPlan
    evidence: tuple[EvidenceAttestation, ...]
    package: Package
```

`BindingPlan` and `BoundPackage` are factory-only, unhashable capabilities.
Their source and evidence fields are excluded from generated representations.
`BindingPlan.profile` is exactly `pff-draft-binding-plan/0.1`;
`BoundPackage.profile` is exactly `pff-bound-package/0.1`.

The plan owns immutable private indexes and these exact methods:

```python
def target_for(self, kind: DraftRecordKind, ref: DraftRef) -> RecordRef: ...
def task_for(self, request: DraftRef) -> EvidenceTask: ...
def origin_for(self, kind: RecordKind, ref: RecordRef) -> BindingOrigin: ...
```

All arguments require exact types. A missing key raises `KeyError`. The origin
index key is exactly `(RecordKind, RecordRef)`. Its value population contains
one `BindingOrigin` for every planned atom, rule, and certificate target:

| Target | Role | Source |
|---|---|---|
| mapped atom | `DRAFT_ATOM` | exact local atom `DraftSource` |
| mapped rule | `DRAFT_RULE` | exact local rule `DraftSource` |
| mapped certificate | `EVIDENCE_CERTIFICATE` | exact local evidence-request `DraftSource` |

The `target_for` index is total over the exact typed source population
`A union R union {DraftSource(EVIDENCE_REQUEST, e) for e in E}`. An `ATOM` or
`RULE` key returns its `RecordIdentityBinding.target`; an `EVIDENCE_REQUEST`
key returns its `EvidenceBinding.certificate`. A source kind is never erased,
so equal local atom, rule, and request refs remain three distinct lookup keys.

There are no header or base origin entries. A successful `BoundPackage` has
exactly the same origin-key set as
`{(kind, record.ref) for kind, record in package.iter_records()}`.
`BoundPackage.origin_for` delegates to its plan with identical behaviour.

`BindingOrigin` is an ordinary value but accepts only these three coherent
triples: `(ATOM, DRAFT_ATOM, source.kind=ATOM)`,
`(RULE, DRAFT_RULE, source.kind=RULE)`, and
`(CERTIFICATE, EVIDENCE_CERTIFICATE, source.kind=EVIDENCE_REQUEST)`.
Every other target-kind/role/source-kind combination raises `ValueError`.

The 12,288 origin upper bound is not an independently supplied collection
limit:
the accepted extractor caps atoms, rules, and evidence requests at 4,096 each,
and planning creates exactly one origin per mapped output. Thus 12,289 origins
are unreachable through the public binder APIs. Planning applies no independent
cardinality rejection to atoms, rules, tasks, certificates, or origins;
population totality is the executable proof of this derived ceiling.

## 4. Policy coverage and authority invariants

For one exact source, define these finite populations:

```text
A = { DraftSource(ATOM, DraftRef(a.id, a.version)) for a in draft.atoms }
R = { DraftSource(RULE, DraftRef(r.id, r.version)) for r in draft.rules }
E = { DraftRef(e.id, e.version) for e in draft.evidence_requests }
```

`[N]` The record-binding source-key set must equal the disjoint typed union
`A union R`. The evidence-binding request-key set must equal `E`. Missing and
extra coverage are distinct diagnostics. The extractor already proves every
rule/evidence-request relation, so the binder never performs ID-only or latest-
version fallback.

`[N]` Every mapped atom, mapped rule, and mapped certificate target must have a
nonempty ID, a positive version, and an ID that does not start `__pff__:`. Their
exact `RecordRef` values must be globally unique across all three kinds. No
target is silently renamed, versioned, deduplicated, or overwritten.

`[N]` The policy registry ID selects exactly one `PredicateRegistry` from the
exact `RegistryCatalog`; its integer version must equal
`policy.registry_version`. There is no fallback or latest-registry selection.
The selected registry's existing constructor guarantees an exact positive
integer but does not impose this profile's maximum. Planning therefore compares
the selected version numerically with `9_223_372_036_854_775_807` before any
string conversion. A larger selected version is the typed phase-40 diagnostic
defined in section 8, never an untyped conversion or formatting failure.

For each rule, planning follows its exact evidence request to one
`EvidenceBinding`. The selected checker must exist in the selected registry,
have the exact declared integer version, permit certificate use on
`RecordKind.RULE`, and occur in the mapped head atom predicate's
`checker_contract_ids`. These are routing prerequisites, not a second package
validator. Atom arity, argument types, frame, grade, certificate detail shape,
and other PFF admission rules remain exclusively with `validate_package`.
As with the selected registry, a resolved checker's existing constructor admits
arbitrarily large positive versions. Planning compares the resolved checker
version with the profile maximum before any string conversion and owns the
typed phase-50 unsupported-version diagnostic.

## 5. Planning API and deterministic construction

```python
def plan_draft_binding(
    source: ExtractedDraft,
    policy: DraftBindingPolicy,
    catalog: RegistryCatalog,
) -> BindingPlan:
    ...
```

The three arguments must be exact types. Any wrong type raises `TypeError`
before a diagnostic phase. The function is pure and provider-free. It never
calls an extractor, checker, binder callback, validator, compiler, evaluator,
network, filesystem, environment, process, clock, random source, or logger.

After the ordered diagnostic gates in section 8 succeed, planning constructs:

1. a `PackageHeader` with schema exactly `pff-core/0.1`, policy-owned
   `package_id`, `cut_id`, `frame_id`, and `registry_id`, and exactly
   `parent_package_hash=None`, `metadata={}`;
2. one `AtomRecord` per draft atom using its mapped target ID and version,
   exact predicate, ordered args, frame, and grade, and `primitive=False`;
3. one `RuleRecord` per draft rule using its mapped target ID and version,
   mapped head and positive refs, its evidence binding's certificate ref,
   `negative=frozenset()`, and `faces=frozenset()`;
4. one exact `EvidenceTask` per evidence request, carrying its complete planned
   rule as `subject_rule`, its exact question, and all fields in section 3.3;
   and
5. the complete origin population in section 3.5.

Atoms and rules are ordered by final target ID then numeric version. Positive
premises retain set semantics as `frozenset`. Tasks are ordered by local
request ID then numeric version. Origins use absolute target-kind order
`ATOM`, `RULE`, `CERTIFICATE`, then target ID and numeric version. No source or
policy tuple order affects these outputs.

## 6. Finalization API and deterministic materialization

```python
def finalize_draft_binding(
    plan: BindingPlan,
    evidence: tuple[EvidenceAttestation, ...],
) -> BoundPackage:
    ...
```

The plan must be an exact `BindingPlan`; evidence must be an exact tuple of
exact `EvidenceAttestation` values. Wrong types raise `TypeError` before a
diagnostic phase. Submitted order is not semantic.

Evidence is grouped by each attestation task's local request `DraftRef`.
Finalization requires exactly one attestation whose complete task is
structurally equal to each planned task, no attestation for an unknown request,
and no duplicate request. A known request with one non-equal task is a task
mismatch, not a missing-plus-extra pair. Missing evidence never becomes
`PASS`, `OPEN`, a placeholder certificate, or a partial result.

After the evidence-set gate succeeds, each attestation's actual authority ID
and version must equal its task's expected authority ID and version. All
attestation identities must be unique within the call. The question, result,
payload hash, details, and attestation identity cannot alter any planned route
or final record identity.

Finalization constructs one `CertificateRecord` per planned task:

| Certificate field | Sole source |
|---|---|
| `id`, `version` | planned task `subject_rule.certificate` |
| `checker` | planned task `checker_id` |
| `subject` | planned task `subject_rule.ref` |
| `result` | matching attestation `result` |
| `payload_hash` | matching attestation `payload_hash` |
| `details` | key-ordered mapping from matching attestation details |

Certificates are ordered by final ID then numeric version. Finalization then
constructs exactly:

```python
Package(
    header=plan.header,
    atoms=plan.atoms,
    rules=plan.rules,
    faces=(),
    certificates=certificates,
    closures=(),
    contraries=(),
    challenges=(),
    discharges=(),
    base=BasePartition(),
)
```

The returned `BoundPackage` retains the exact plan, the evidence tuple
canonicalized by planned task order, and that candidate package. No
`BoundPackage` exists on any finalization issue.

`[S]` A later explicit call may be:

```python
validated = validate_package(bound.package, bound.plan.catalog)
```

The binder does not catch, translate, wrap, or pre-empt
`PackageValidationError`. In particular, a checker-detail key/type mismatch is
allowed to reach `BoundPackage` and is rejected only by the explicit later
validator. This preserves one admission path and one diagnostic owner.

## 7. Replay and source retention

The complete in-memory replay input is retained transitively:

```text
BoundPackage
  -> BindingPlan
       -> ExtractedDraft -> GenerationEnvelope -> exact captured bytes
       -> DraftBindingPolicy
       -> RegistryCatalog and selected registry
       -> mapped records, tasks, and origins
  -> canonical EvidenceAttestation tuple
  -> candidate Package
```

Replaying `plan_draft_binding` and `finalize_draft_binding` over structurally
equal inputs produces equal public outputs without calling an LLM. Different
surrounding prose may produce the same extracted payload and package while the
retained source envelopes remain distinguishable. Provider identity, raw
prose, questions, evidence authority metadata, and attestation identity never
enter package metadata.

`[D]` This profile defines no persistent encoder, plan/task hash, signature,
deserializer, storage address, deletion rule, or cross-version replay promise.
Those require a separate canonical/replay and evidence-authentication profile.

## 8. Diagnostics, gates, and precedence

### 8.1 Exact types

```python
class BindingPhase(IntEnum):
    SOURCE = 10
    COVERAGE = 20
    IDENTITY = 30
    REGISTRY = 40
    ROUTING = 50
    EVIDENCE_SET = 60
    ATTESTATION = 70

class BindingCode(StrEnum):
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

@dataclass(frozen=True, slots=True)
class BindingIssue:
    phase: BindingPhase
    code: BindingCode
    path: str
    sources: tuple[DraftSource, ...] = ()
    targets: tuple[RecordRef, ...] = ()
    details: tuple[str, ...] = ()

class DraftBindingError(ValueError):
    issues: tuple[BindingIssue, ...]
```

Each code belongs only to the phase shown by the table order below; constructing
an incompatible code/phase issue raises `ValueError`. Sources and targets are
exact typed tuples, duplicate-free and canonically sorted. Binder-emitted
details contain only the table-defined labels, identifiers, versions, or
digests—never the question, raw prompt/response, evidence detail values,
provider key, or payload bytes. This payload-free guarantee is an algorithm
postcondition, not an authenticity claim about arbitrary caller-created issue
values.

Input-owned binding strings retain the 262,144-byte ceiling. Table-generated
diagnostic details may add one fixed ASCII label and therefore have the derived
maximum 262,176 UTF-8 bytes. No diagnostic joins two input values into one
detail string. In particular, a maximum-size `registry_id` yields a
262,156-byte `registry_id=` detail and a maximum-size `checker_id` yields a
262,155-byte `checker_id=` detail.

`BindingIssue.details` has no observable caller-versus-binder provenance, so
its ordinary public constructor always applies that same derived 262,176-byte
ceiling to every exact scalar detail string. The binder's algorithms remain
strictly narrower: they emit only the table-defined details and never use the
extra allowance for arbitrary payload. This is the sole arbitrary-string slot
excluded from the 262,144-byte input ceiling.

`DraftBindingError` requires a nonempty exact issue tuple, canonicalizes by
`(phase integer, path, code value, source kind rank/ref, target ref, details)`,
and removes exact duplicates. Its message is exactly `draft binding failed`.

### 8.2 Gates

Planning and finalization run separate gate sequences. A gate completes all its
independent checks and aggregates its issues. If it emits any issue, later
gates do not run and no partial capability is returned.

Use these projections in the exhaustive table:

```text
DS(k,r) = DraftSource(k, r)
RS      = exact source-key set of policy.record_bindings
ES      = exact request-key set of policy.evidence_bindings
T(x)    = the target RecordRef of binding x
route(e)= (the mapped rule ref, e.certificate), sorted as RecordRef values
```

For identity checks, a certificate binding's source is
`DS(EVIDENCE_REQUEST, request)`. `sources` sort by the absolute rank
`ATOM=0`, `RULE=1`, `EVIDENCE_REQUEST=2`, then source ID under the profile
string comparator, then numeric version. `targets` sort by target ID under the
same comparator then numeric version. `details` use that comparator.
Origin keys use the distinct target-kind rank `ATOM=0`, `RULE=1`,
`CERTIFICATE=2`.

| Code | Phase | Exact path | Exact `sources` | Exact `targets` | Exact `details` | Issue cardinality/formula |
|---|---:|---|---|---|---|---|
| `SOURCE_PAYLOAD_MISMATCH` | 10 | `/source/payload_sha256` | `()` | `()` | sorted `("actual=" + source.payload_sha256, "expected=" + policy.source_payload_sha256)` | exactly 1 iff the digests differ |
| `RECORD_BINDING_MISSING` | 20 | `/policy/record_bindings` | sorted `(A union R) - RS` | `()` | `()` | exactly 1 iff that set is nonempty |
| `RECORD_BINDING_EXTRA` | 20 | `/policy/record_bindings` | sorted `RS - (A union R)` | sorted distinct targets of those extra bindings | `()` | exactly 1 iff that set is nonempty |
| `EVIDENCE_BINDING_MISSING` | 20 | `/policy/evidence_bindings` | `DS(EVIDENCE_REQUEST,e)` for sorted `E - ES` | `()` | `()` | exactly 1 iff that set is nonempty |
| `EVIDENCE_BINDING_EXTRA` | 20 | `/policy/evidence_bindings` | `DS(EVIDENCE_REQUEST,e)` for sorted `ES - E` | sorted distinct certificate targets of those rows | `()` | exactly 1 iff that set is nonempty |
| `TARGET_INVALID_ID` | 30 | `/policy/targets/id` | the one binding source | `(T(x),)` | `()` | one per binding whose target ID is empty, non-scalar, or over 262,144 UTF-8 bytes |
| `TARGET_INVALID_VERSION` | 30 | `/policy/targets/version` | the one binding source | `(T(x),)` | `()` | one per binding whose exact-int target version is outside `1..MAX_VERSION` |
| `TARGET_RESERVED_ID` | 30 | `/policy/targets/id` | the one binding source | `(T(x),)` | `()` | one per otherwise-valid target ID beginning `__pff__:` |
| `TARGET_REF_COLLISION` | 30 | `/policy/targets` | every source mapped to the collided exact ref | the singleton collided ref | `()` | one per distinct exact target with multiplicity at least 2 |
| `UNKNOWN_REGISTRY` | 40 | `/policy/registry_id` | `()` | `()` | `(policy.registry_id,)` | exactly 1 iff catalog lookup fails |
| `REGISTRY_VERSION_UNSUPPORTED` | 40 | `/catalog/registry/version` | `()` | `()` | exact `("registry_id=" + policy.registry_id, "supported_max=9223372036854775807")` | exactly 1 iff lookup succeeds and selected `registry.version > 9_223_372_036_854_775_807` |
| `REGISTRY_VERSION_MISMATCH` | 40 | `/policy/registry_version` | `()` | `()` | sorted `("actual=" + decimal policy version, "expected=" + decimal registry version)` | exactly 1 iff lookup succeeds, `registry.version <= 9_223_372_036_854_775_807`, and versions differ |
| `HEAD_PREDICATE_UNKNOWN` | 50 | `/draft/rules/head/predicate` | exact local head atom and rule sources | exact mapped atom and rule refs | `(predicate_id,)` | one per routed rule whose head predicate lookup fails |
| `CHECKER_UNKNOWN` | 50 | `/policy/evidence_bindings/checker_id` | exact local rule and request sources | `route(e)` | `(checker_id,)` | one per request whose checker lookup fails |
| `CHECKER_VERSION_UNSUPPORTED` | 50 | `/catalog/registry/checker_contracts/version` | exact local rule and request sources | `route(e)` | exact `("checker_id=" + checker_id, "supported_max=9223372036854775807")` | one per request whose checker resolves and `contract.version > 9_223_372_036_854_775_807` |
| `CHECKER_VERSION_MISMATCH` | 50 | `/policy/evidence_bindings/checker_version` | exact local rule and request sources | `route(e)` | sorted exact `actual=N`, `expected=N` | one per known checker with `contract.version <= 9_223_372_036_854_775_807` and unequal version |
| `CHECKER_NOT_PERMITTED` | 50 | `/policy/evidence_bindings/checker_id` | exact local rule and request sources | `route(e)` | sorted nonempty subset of `reason=predicate`, `reason=subject`, `reason=use` | one per request after known/equal-version checks when any reason applies |
| `EVIDENCE_MISSING` | 60 | `/evidence` | the expected request source | `(expected subject_rule.certificate,)` | `()` | one per expected request with zero submitted attestations |
| `EVIDENCE_EXTRA` | 60 | `/evidence` | the unknown request source | sorted distinct certificate refs from every submitted task in that unknown-key group | `()` | one per submitted unknown request key, regardless of its multiplicity |
| `EVIDENCE_DUPLICATE` | 60 | `/evidence` | the expected request source | `(expected subject_rule.certificate,)` | `()` | one per expected request with two or more submitted attestations; none is selected |
| `EVIDENCE_TASK_MISMATCH` | 60 | `/evidence/task` | the expected request source | `(expected subject_rule.certificate,)` | `()` | one per expected request with exactly one submitted, structurally unequal task |
| `EVIDENCE_AUTHORITY_MISMATCH` | 70 | `/evidence/authority` | the matching request source | `(task.subject_rule.certificate,)` | always the four strings `actual_authority_id=<actual>`, `expected_authority_id=<expected>`, `actual_authority_version=<decimal actual>`, `expected_authority_version=<decimal expected>`, sorted by the profile comparator | one per exact-task attestation whose ID or version differs; unchanged dimensions are still included and both differences share one issue |
| `ATTESTATION_REF_COLLISION` | 70 | `/evidence/attestation` | every matching request source using the identity | their certificate refs | always the four strings `authority_id=<identity authority ID>`, `authority_version=<decimal identity authority version>`, `attestation_id=<identity attestation ID>`, `attestation_version=<decimal identity attestation version>`, sorted by the profile comparator | one per four-part identity with multiplicity at least 2 |

The phase-60 grouping key is exact local request `(id, version)`. A known key
with exactly one unequal task produces only `EVIDENCE_TASK_MISMATCH`, not
missing plus extra. An unknown key produces only `EVIDENCE_EXTRA`. Phase 70
runs only when phase 60 is empty.

For `CHECKER_NOT_PERMITTED`, `reason=use` is present exactly when
`CheckerUse.CERTIFICATE` is absent, `reason=subject` exactly when
`RecordKind.RULE` is absent from `certificate_subject_kinds`, and
`reason=predicate` exactly when the head predicate resolved and the checker ID
is absent from that predicate's `checker_contract_ids`. An unresolved head
predicate emits `HEAD_PREDICATE_UNKNOWN`; it suppresses only the dependent
predicate reason, not independently decidable use or subject reasons. Unknown
checker, unsupported checker version, and checker-version mismatch suppress
every permission reason for that request. An unsupported checker version does
not suppress an independently decidable `HEAD_PREDICATE_UNKNOWN`.

Phase 40 first performs registry lookup. A failed lookup emits only
`UNKNOWN_REGISTRY`; a resolved version above the profile maximum emits only
`REGISTRY_VERSION_UNSUPPORTED`; only a supported resolved version may reach
ordinary version comparison. An unsupported registry version suppresses the
ordinary mismatch and every later gate. Phase 50 applies the analogous order
per request: head-predicate lookup is independent, then checker lookup,
unsupported-version comparison, ordinary version comparison, and finally
permission checks. Both unsupported comparisons occur before `str`, `repr`,
formatting, or decimal conversion of the external version. The unsupported
value itself never appears in an issue.

`BindingIssue` construction requires exact phase/code/path and exact tuples.
It rejects a code in the wrong phase, a path unequal to the table, duplicate
sources/targets/details, wrong member types, or noncanonical submitted tuple
order with `ValueError`; it does not silently reorder caller-created issues.
The planning/finalization algorithms themselves create table-canonical issues.
`DraftBindingError` requires a nonempty exact tuple of exact issues, removes
exact duplicates, and sorts the retained issues by the key in section 8.1
without mutating the input tuple.

Within a successful gate, iteration order never determines issue order. Decimal
versions compare numerically, so version 2 sorts before version 10. Collection
positions are not public diagnostic ordinals.

## 9. Security and side-effect boundary

The LLM controls only values already inside the exact extracted draft. It does
not control package IDs, versions, primitive flags, base membership, header,
registry, checker, checker version, evidence authority, certificate identity,
certificate result, evidence details, or any deferred record collection.

The evidence question is inert text. Text asking for a shell command, URL,
filesystem read, provider call, secret, checker choice, or semantic status
does not cause such an action. The binder never reads an environment variable
or credential and never receives the Ollama API key.

The binder is not a hostile-Python sandbox. Code that directly constructs a
false `EvidenceAttestation` is asserting false authority at the trusted caller
boundary. Preventing or detecting that act requires the deferred authenticator.
The binding checks ensure that generation bytes alone cannot supply that
assertion and that an assertion for another task or authority cannot be used by
accident.

## 10. Dependency direction and implementation boundary

The exact dependency direction is:

```text
generation.model <- generation.extract ----\
                                          > poietics.binding -> pff.model
pff.model <- pff.registry ----------------/                     + pff.registry

future evidence authority adapter -> poietics.binding.model

poietics.binding --X--> ollama, ollama_http, checker execution,
                      pff.validate, pff.compile, ground,
                      canonical, replay, CLI
generation, pff, ground --X--> poietics.binding
```

The binder is a top-level convergence package. It must not be placed under
`poietics.generation`, because generation has a frozen no-import boundary to
PFF authority. `src/poietics/binding/__init__.py` is inert except for its module
docstring.

The authority-only tranche changes exactly:

```text
docs/PFF_DRAFT_BINDING_PROFILE_V0.1.md
```

After acceptance, the implementation allowlist is exactly:

```text
src/poietics/binding/__init__.py
src/poietics/binding/model.py
src/poietics/binding/plan.py
src/poietics/binding/finalize.py
tests/test_binding_model.py
tests/test_binding_plan.py
tests/test_binding_finalize.py
README.md
```

No existing production type requires modification. In particular, no
generation, PFF, ground, provider, packaging, canonical, replay, CLI, or pack
file changes in that tranche.

Production binding code may import only standard-library dataclass, enum,
mapping-proxy, and typing facilities plus exact public types from
`generation.extract`, `generation.model`, `pff.model`, and `pff.registry`, and
exact sibling binding types. It may not dynamically import. `plan.py` may
import the `ExtractedDraft` class but must not import or call `extract_draft`.
No binding module imports `pff.validate` or names `validate_package`.

## 11. Executable conformance authority

This section freezes four pairwise-disjoint typed populations:

```text
S = {S00, S01, S02, S03, S04H, S04P, S05, S06, S07, S08} # sources, |S| = 10
F = {F00, ..., F105}                         # behavioural fixtures, |F| = 106
C = {C00, ..., C82}                          # constructor cases, |C| = 83
M = {M01, ..., M181}                         # implementation mutants, |M| = 181
```

The displayed order is absolute. Numeric suffixes compare numerically; `S04H`
precedes `S04P`. These populations are not added into one unexplained total.
Qualification proves separately:

```text
defined_F = generated_F = dispatched_F = executed_F
defined_C = generated_C = dispatched_C = executed_C
defined_M = attempted_M = classified_M
```

Every fixture compares the complete declared outcome. An expected failure
admits only its exact issue set; a different exception, code, path, source,
target, detail, or gate is a wrong-reason result.

### 11.1 Exact source construction

Except for the accepted prose-bearing C01 response named below, an exact source
response is:

```text
UTF8("<<<PFF-DRAFT/0.1>>>\n")
+ exact payload bytes
+ UTF8("\n<<<END-PFF-DRAFT/0.1>>>")
```

There is no terminal LF after the closer. The common capture call uses prompt
bytes `Produce one PFF draft.\n`, `AttemptRef("session:binding", 1)`, relation
`INITIAL`, no parent, provider `fixture-provider`, adapter `fixture-adapter`
version exact string `"1"`, requested and reported model `fixture-model`, prompt
template `binding-fixture` version exact string `"1"`, empty public parameters,
finish reason `stop`,
and provider request ID `fixture-request`. Calling `extract_draft` once before
the binder produces the factory-only source. Planning and finalization never
call it.

S00 through S05 and S08 are one UTF-8 line exactly as displayed. S06 and S07
are the exact generated UTF-8 lines defined by their closed construction rules;
they are not elliptical examples.

**S00 — empty**

```json
{"schema":"pff-draft/0.1","atoms":[],"rules":[],"evidence_requests":[]}
```

Payload length is 71 and SHA-256 is
`sha256:26a0b36236426e2f2dace4314c2938af3cfa8e26b52baaf25c43c50f9956411a`.
The wrapped response length is 115 and SHA-256 is
`sha256:666e782bc2438cde8fb42d9594bb28e4ccefe81960d44ce7e8150f413f9f1d93`.

**S01 — accepted C01**

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"atom:generated","version":5,"predicate":"test.derived","args":["entity:e"],"frame":"frame:1","grade":null}],"rules":[{"id":"rule:generated","version":7,"head":{"id":"atom:generated","version":5},"positive":[],"evidence_request":{"id":"evidence:generated","version":11}}],"evidence_requests":[{"id":"evidence:generated","version":11,"kind":"certificate","subject":{"id":"rule:generated","version":7},"question":"Check the proposed derivation."}]}
```

Payload length is 487 and SHA-256 is
`sha256:ae7e0b37d389c3b702c98b9c9f7c3bfa7369221fcddbfbc7cb8a3630533aef6b`.
The marker-only response length is 531 and SHA-256 is
`sha256:e7999336513221c1911a1bf31cc21d5f15d45d83d8c957e7d1180d30b1b0ec3b`.
The accepted generation-capture C01 prose response remains the second exact
envelope form for this same payload.

**S02 — ordering, versions, positives, and ownership**

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"local:b","version":1,"predicate":"test.derived","args":["entity:b"],"frame":"frame:1","grade":null},{"id":"local:a","version":2,"predicate":"test.derived","args":["entity:a2"],"frame":"frame:1","grade":null},{"id":"local:a","version":1,"predicate":"test.derived","args":["entity:a1"],"frame":"frame:1","grade":null}],"rules":[{"id":"local:r-b","version":1,"head":{"id":"local:b","version":1},"positive":[],"evidence_request":{"id":"local:e-b","version":1}},{"id":"local:r-a","version":2,"head":{"id":"local:a","version":2},"positive":[],"evidence_request":{"id":"local:e-a","version":2}},{"id":"local:r-a","version":1,"head":{"id":"local:a","version":1},"positive":[{"id":"local:b","version":1}],"evidence_request":{"id":"local:e-a","version":1}}],"evidence_requests":[{"id":"local:e-b","version":1,"kind":"certificate","subject":{"id":"local:r-b","version":1},"question":"Check."},{"id":"local:e-a","version":2,"kind":"certificate","subject":{"id":"local:r-a","version":2},"question":"Check."},{"id":"local:e-a","version":1,"kind":"certificate","subject":{"id":"local:r-a","version":1},"question":"Check."}]}
```

Payload length is 1,151 and SHA-256 is
`sha256:5b6d12fefa5354a9b857fe19f5f9d73c5591ec2414c8c6894d79ed2c66d091ac`.
The wrapped response length is 1,195 and SHA-256 is
`sha256:7a0398f620b6cd4110185c879ed3b7e7a88838249a4d92c592b2eec74c00a13e`.

**S03 — shared local namespaces**

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"shared","version":13,"predicate":"test.derived","args":["entity:shared"],"frame":"frame:1","grade":null}],"rules":[{"id":"shared","version":13,"head":{"id":"shared","version":13},"positive":[{"id":"shared","version":13}],"evidence_request":{"id":"shared","version":13}}],"evidence_requests":[{"id":"shared","version":13,"kind":"certificate","subject":{"id":"shared","version":13},"question":"Check shared."}]}
```

Payload length is 451 and SHA-256 is
`sha256:f8351501d65672b01b49d164c074c6a14306d14c3ebaf5caf600ca8ca57b0115`.
The wrapped response length is 495 and SHA-256 is
`sha256:a5c866b7e20a8e9d38ad1b94c997d02c539ba05601ca555dd180496067d20587`.

**S04H — unknown head predicate**

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"atom:unknown","version":1,"predicate":"test.unknown","args":["entity:u"],"frame":"frame:1","grade":null}],"rules":[{"id":"rule:unknown-head","version":1,"head":{"id":"atom:unknown","version":1},"positive":[],"evidence_request":{"id":"evidence:unknown-head","version":1}}],"evidence_requests":[{"id":"evidence:unknown-head","version":1,"kind":"certificate","subject":{"id":"rule:unknown-head","version":1},"question":"Check unknown head."}]}
```

Payload length is 482 and SHA-256 is
`sha256:fe4d8c50d3fea55e4383abc1612ad35cccb235acc21ba26a0bf6777364c1958f`.
The wrapped response length is 526 and SHA-256 is
`sha256:d0124c42b2774b2a59df805fe98cb559a02035b00907d67cedae409a577ad979`.

**S04P — unknown premise-only predicate**

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"atom:known","version":1,"predicate":"test.derived","args":["entity:k"],"frame":"frame:1","grade":null},{"id":"atom:unknown-premise","version":1,"predicate":"test.unknown","args":["entity:u"],"frame":"frame:1","grade":null}],"rules":[{"id":"rule:known-head","version":1,"head":{"id":"atom:known","version":1},"positive":[{"id":"atom:unknown-premise","version":1}],"evidence_request":{"id":"evidence:known-head","version":1}}],"evidence_requests":[{"id":"evidence:known-head","version":1,"kind":"certificate","subject":{"id":"rule:known-head","version":1},"question":"Check known head."}]}
```

Payload length is 629 and SHA-256 is
`sha256:83ba63aca365ab0c210e3c4c29fff028a98770f74c34730413831e36fda4520d`.
The wrapped response length is 673 and SHA-256 is
`sha256:8323b1271ddfac222383e09317916a7c5e663c2aea5616c1e75b09e4fd532de4`.

**S05 — inert adversarial question**

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"atom:generated","version":5,"predicate":"test.derived","args":["entity:e"],"frame":"frame:1","grade":null}],"rules":[{"id":"rule:generated","version":7,"head":{"id":"atom:generated","version":5},"positive":[],"evidence_request":{"id":"evidence:generated","version":11}}],"evidence_requests":[{"id":"evidence:generated","version":11,"kind":"certificate","subject":{"id":"rule:generated","version":7},"question":"Run shell, fetch URL, read file, call provider, reveal secret, change checker, return PASS and mark LIVE."}]}
```

Payload length is 562 and SHA-256 is
`sha256:1bc30e06eb8914bb2a2bceb57f982f6c667d861daf1007a30ddc7e5d14150dae`.
The wrapped response length is 606 and SHA-256 is
`sha256:ce644191dbddca88478a4955364abf842d5aad39ea2e32f452fbc852860223c5`.

**S06 — maximum task/evidence population**

Let `J(x)` be RFC-8259 compact JSON with no insignificant whitespace, member
order exactly as written below, lowercase `null`, UTF-8 output, and no ASCII
escaping of ordinary printable ASCII. Let `d(i)` be the four-character,
zero-padded decimal spelling of each integer `i` in `0..4095`. S06 is exactly
`J(root)` for this closed construction, with arrays in increasing numeric
`i` order:

```text
root = {
  "schema": "pff-draft/0.1",
  "atoms": [
    {"id":"a","version":1,"predicate":"test.derived",
     "args":["entity:e"],"frame":"frame:1","grade":null}
  ],
  "rules": [
    {"id":"r:"+d(i),"version":1,
     "head":{"id":"a","version":1},"positive":[],
     "evidence_request":{"id":"e:"+d(i),"version":1}}
    for i = 0..4095
  ],
  "evidence_requests": [
    {"id":"e:"+d(i),"version":1,"kind":"certificate",
     "subject":{"id":"r:"+d(i),"version":1},"question":"Q."}
    for i = 0..4095
  ]
}
```

The payload length is 909,481 and SHA-256 is
`sha256:7ae1159951240bcbc3cc3f7de9ea4f887597cb86c91a52807a239a9df6594477`.
The wrapped response length is 909,525 and SHA-256 is
`sha256:c3df8ca8a8b84900689dd0bbd5507e0783fa806afc6f11c25b1d1188433e4cf0`.

**S07 — maximum task population plus one additional mapped atom**

S07 uses the same `J`, `d`, rules, and evidence-request arrays as S06. Its
`atoms` array is exactly the S06 atom followed by this second atom:

```json
{"id":"b","version":1,"predicate":"test.derived","args":["entity:b"],"frame":"frame:1","grade":null}
```

The payload length is 909,582 and SHA-256 is
`sha256:0822658a4ec0690b0684266931984607b8fcc428d3aaacc3aa0397932fb6a026`.
The wrapped response length is 909,626 and SHA-256 is
`sha256:cbda4d4e24457b75785f51d670ba025a21a26b9c8d88bcd85418ee6c3a00d0c2`.

**S08 — numeric source and output ordering**

The arrays are deliberately submitted in numeric-version order 10, then 2:

```json
{"schema":"pff-draft/0.1","atoms":[{"id":"a","version":1,"predicate":"test.derived","args":["entity:e"],"frame":"frame:1","grade":null}],"rules":[{"id":"r","version":10,"head":{"id":"a","version":1},"positive":[],"evidence_request":{"id":"e","version":10}},{"id":"r","version":2,"head":{"id":"a","version":1},"positive":[],"evidence_request":{"id":"e","version":2}}],"evidence_requests":[{"id":"e","version":10,"kind":"certificate","subject":{"id":"r","version":10},"question":"Q10."},{"id":"e","version":2,"kind":"certificate","subject":{"id":"r","version":2},"question":"Q2."}]}
```

The payload length is 580 and SHA-256 is
`sha256:4a88db38a97153ada5a35eb9a03fec03c6b8589f0c831a2993593ee0fa3315a0`.
The wrapped response length is 624 and SHA-256 is
`sha256:99a0604acb4d54ed27b07697233ac57b2d6e44f600806c134bec1f8e69217ed5`.

### 11.2 Exact catalog RC1

Every fixture uses the singleton `RegistryCatalog` RC1 unless its one named
mutation changes registry selection. RC1 is constructed from these exact
definitions; omitted optional sets and tuples are empty:

| Definition | Exact fields |
|---|---|
| registry | `registry_id=test-registry/1`, `version=1` |
| argument type | `entity_ref@1`, `required_prefix=entity:` |
| frame policy | `frame:exact-package@1`, `EXACT_PACKAGE` |
| contrary policy | `contrary:forbidden@1`, `FORBIDDEN`, `include_frame=False` |
| `rule-witness/v1@1` | `CERTIFICATE`, subject `RULE`, detail `witness: NONEMPTY_STRING` |
| `rule-witness-alt/v1@1` | `CERTIFICATE`, subject `RULE`, detail `witness: NONEMPTY_STRING` |
| `two-detail/v1@1` | `CERTIFICATE`, subject `RULE`, details `count: INTEGER`, `witness: NONEMPTY_STRING` |
| `atom-only/v1@1` | `CERTIFICATE`, subject `ATOM`, detail `witness: NONEMPTY_STRING` |
| `rule-forbidden/v1@1` | `CERTIFICATE`, subject `RULE`, detail `witness: NONEMPTY_STRING` |
| `closure-only/v1@1` | `CLOSURE`, selector kind `ATOM`, frame policy `frame:exact-package`, local semantics `NONE` |
| predicate | `test.derived@1`, args `(entity_ref,)`, exact-package frame, grade `FORBIDDEN`, computability `FIN`, nonprimitive, contrary `contrary:forbidden` |

The predicate's checker set is exactly
`{atom-only/v1, rule-witness-alt/v1, rule-witness/v1, two-detail/v1}`.
`rule-forbidden/v1` and `closure-only/v1` are known contracts but absent from
that set. RC1 uses the existing registry defaults for the unrelated known
face/challenge/discharge tables; no fixture reads them.

For the external-version fixtures, let
`MAX = 9_223_372_036_854_775_807` and `U = 10 ** 300_000`. The exact integer
`U` has 300,001 decimal digits, but no conforming binder converts it to decimal.
`RC1-R(v)` copies RC1 exactly except that its sole
`PredicateRegistry.version` is `v`. `RC1-C(id,v)` copies RC1 exactly except
that the one named `CheckerContract.version` is `v`. All other registry and
contract fields, tuple positions, and defaults remain RC1's exact values.

### 11.3 Exact policies and attestations

All policies use profile `pff-draft-binding-policy/0.1`, `cut:1`, `frame:1`,
RC1 ID/version, and the exact digest of their named source.

| Policy | Source; header | Exact record routes | Exact evidence routes |
|---|---|---|---|
| P00 | S00; `policy:empty@1`, `package:empty` | none | none |
| P01 | S01; `policy:test@3`, `package:bound-1` | ATOM `atom:generated@5 -> atom:authoritative@2`; RULE `rule:generated@7 -> rule:authoritative@4` | `evidence:generated@11 -> certificate:authoritative@6`; checker `rule-witness/v1@1`; authority `evidence-authority:test@2` |
| P02 | S02; `policy:rich@1`, `package:rich` | ATOM `local:a@1 -> atom:rich:a@11`, `local:a@2 -> atom:rich:a@12`, `local:b@1 -> atom:rich:b@11`; RULE `local:r-a@1 -> rule:rich:a@21`, `local:r-a@2 -> rule:rich:a@22`, `local:r-b@1 -> rule:rich:b@21` | requests `local:e-a@1 -> certificate:rich:a@31`, `local:e-a@2 -> certificate:rich:a@32`, `local:e-b@1 -> certificate:rich:b@31`; each uses `rule-witness/v1@1`, authority `evidence-authority:test@2` |
| P03 | S03; `policy:shared@1`, `package:shared` | ATOM `shared@13 -> atom:shared@101`; RULE `shared@13 -> rule:shared@201` | request `shared@13 -> certificate:shared@301`; `rule-witness/v1@1`; authority `evidence-authority:test@2` |
| P04H | S04H; `policy:unknown-head@1`, `package:unknown-head` | ATOM `atom:unknown@1 -> atom:authority:unknown@1`; RULE `rule:unknown-head@1 -> rule:authority:unknown-head@1` | `evidence:unknown-head@1 -> certificate:authority:unknown-head@1`; ordinary checker/authority |
| P04P | S04P; `policy:unknown-premise@1`, `package:unknown-premise` | ATOM `atom:known@1 -> atom:authority:known@1`, `atom:unknown-premise@1 -> atom:authority:unknown-premise@1`; RULE `rule:known-head@1 -> rule:authority:known-head@1` | `evidence:known-head@1 -> certificate:authority:known-head@1`; ordinary checker/authority |
| P05 | S05; `policy:inert@1`, `package:inert` | P01 record routes | P01 evidence route |
| P06 | S06; `policy:max@1`, `package:max` | ATOM `a@1 -> atom:max@1`; for every increasing `i=0..4095`, RULE `r:<d(i)>@1 -> rule:max:<d(i)>@1` | for every increasing `i=0..4095`, request `e:<d(i)>@1 -> certificate:max:<d(i)>@1`; each uses ordinary checker/authority |
| P07 | S07; `policy:max-plus-atom@1`, `package:max-plus-atom` | P06 record routes plus ATOM `b@1 -> atom:max:b@1` | exactly the P06 evidence routes |
| P08 | S08; `policy:numeric@1`, `package:numeric`; submitted in the displayed order | RULE `r@10 -> rule:numeric@2`; ATOM `a@1 -> atom:numeric@1`; RULE `r@2 -> rule:numeric@10` | `e@10 -> certificate:numeric@2`; `e@2 -> certificate:numeric@10`; ordinary checker/authority |

“Ordinary checker/authority” means `rule-witness/v1@1` and
`evidence-authority:test@2`. The ordinary P01 attestation has identity
`evidence-authority:test@2 / witness:attestation-1@9`, result `PASS`, payload
hash `sha256:` plus 64 `1` digits, and sole detail
`EvidenceDetail("witness", "witness:1")`. P01-F and P01-O change only the exact
result to `FAIL` and `OPEN`: their profile, complete P01 task, actual authority,
attestation ID/version, payload hash, and details are byte-for-byte/value-for-
value identical to the ordinary P01 attestation.

P02 attestations, in planned request order, are:

| Request | Attestation | Result | Payload hash | Detail |
|---|---|---|---|---|
| `local:e-a@1` | `attestation:rich:a1@1` | `PASS` | 64 `2` digits | `witness:a1` |
| `local:e-a@2` | `attestation:rich:a2@1` | `OPEN` | 64 `3` digits | `witness:a2` |
| `local:e-b@1` | `attestation:rich:b1@1` | `FAIL` | 64 `4` digits | `witness:b1` |

Each row uses authority `evidence-authority:test@2` and the mandatory
`sha256:` prefix. P03 uses `attestation:shared@1`, `PASS`, a hash of 64 `5`
digits, and `witness:shared`. P04P uses exact ID
`attestation:unknown-premise@1`; P05 uses exact ID
`attestation:inert@1`. Both otherwise use the ordinary attestation shape with
their own complete planned task.

P06 has exactly 4,096 attestations in increasing numeric `i` order. Row `i`
has the complete P06 task for request `e:<d(i)>@1`, actual authority
`evidence-authority:test@2`, identity `attestation:max:<d(i)>@1`, result
`PASS`, payload hash `sha256:` plus 64 `6` digits, and sole detail
`EvidenceDetail("witness", "witness:" + d(i))`.
P07 uses the same complete attestation construction with each task replaced by
the structurally equal corresponding P07 task (whose package and policy
context are P07's exact values).

P08 submits its two attestations in request order `e@10`, `e@2`. Both use
authority `evidence-authority:test@2`, result `PASS`, and payload hash
`sha256:` plus 64 lowercase `8` digits. Their exact identities are
`attestation:numeric@10` and `attestation:numeric@2`; their sole witness values
are respectively `witness:10` and `witness:2`.

### 11.4 Behavioural fixture population F

Each row is one leaf fixture. “Sole” means the complete issue tuple has
cardinality one and all issue fields equal section 8.2. A later validation or
evaluation call is test code outside the binder.

| ID | Exact input/change | Complete required observable |
|---:|---|---|
| F00 | P00, empty evidence | planning/finalization/validation succeed; zero records, tasks, evidence, origins, and base members |
| F01 | P01, ordinary PASS | exact candidate; validation succeeds; mapped atom `LIVE`; compiled `base_live` is only `__pff__:cert-valid(certificate:authoritative@6)` |
| F02 | P01-F | exact certificate `FAIL`; mapped atom `EXCLUDED`; compiled live only cert-failed, excluded only cert-valid, protected-open empty |
| F03 | P01-O | exact certificate `OPEN`; mapped atom `SUSPENDED`; compiled live only cert-open, protected-open only cert-valid, excluded empty |
| F04 | P02 with policy/evidence submitted in canonical order | exact three atoms, three rules, three tasks, nine origins; `rule:rich:a@21` positive is only `atom:rich:b@11`; resulting mapped statuses are excluded, suspended, excluded for a@11, a@12, b@11 |
| F05 | F04 with both policy tuples and evidence tuple submitted in reverse | forward- and reverse-submitted policies are equal and expose identical canonical binding tuples before planning; plan records/tasks/origins and bound projection equal F04 |
| F06 | P02 local `local:a@1` and `local:a@2` | exact distinct targets; no ID-only/latest collapse |
| F07 | P03 | success; head and positive map to atom target, task subject rule maps to rule target, certificate maps independently |
| F08 | P03 maps atom and rule to `collision:shared@1` | sole `TARGET_REF_COLLISION`, both typed sources |
| F09 | P01 certificate target equals `atom:authoritative@2` | sole collision, atom and request sources |
| F10 | P01 certificate target equals `rule:authoritative@4` | sole collision, rule and request sources |
| F11 | P02 changes exactly `local:a@1 -> target:same@2` and `local:a@2 -> target:same@10`; every other P02 route is unchanged | success; versions remain distinct and the two final atoms occur in numeric-version order `@2`, `@10` |
| F12 | P01 atom target ID empty | sole `TARGET_INVALID_ID` |
| F13 | P01 atom target version 0 | sole `TARGET_INVALID_VERSION` |
| F14 | P01 atom target `__pff__:bad@1` | sole `TARGET_RESERVED_ID` |
| F15 | P01 digest changed to valid SHA-256 of 64 `0` digits | sole `SOURCE_PAYLOAD_MISMATCH`; catalog lookup count zero |
| F16 | P01 omits atom map | sole `RECORD_BINDING_MISSING` |
| F17 | P01 adds ATOM `absent@1 -> atom:absent@1` | sole `RECORD_BINDING_EXTRA` |
| F18 | P01 omits its evidence row | sole `EVIDENCE_BINDING_MISSING` |
| F19 | P01 adds request `absent@1 -> certificate:absent@1` with ordinary checker/authority | sole `EVIDENCE_BINDING_EXTRA` |
| F20 | P01 registry ID `missing-registry` | sole `UNKNOWN_REGISTRY` |
| F21 | P01 registry version 2 | sole `REGISTRY_VERSION_MISMATCH`, details `actual=2`, `expected=1` |
| F22 | P04H | sole `HEAD_PREDICATE_UNKNOWN` |
| F23 | P04P plus `attestation:unknown-premise@1` | binder succeeds; later validator emits exactly one issue: phase `POLICIES`, code `UNKNOWN_PREDICATE`, path `atom[atom:authority:unknown-premise@1].predicate`, refs `(atom:authority:unknown-premise@1,)`, details `(test.unknown,)` |
| F24 | P01 checker `missing-checker@1` | sole `CHECKER_UNKNOWN` |
| F25 | P01 checker `rule-witness/v1@2` | sole version mismatch, `actual=2`, `expected=1` |
| F26 | P01 checker `closure-only/v1@1` | sole not-permitted issue; exact reasons predicate, subject, use |
| F27 | P01 checker `atom-only/v1@1` | sole not-permitted issue; exact reason subject |
| F28 | P01 checker `rule-forbidden/v1@1` | sole not-permitted issue; exact reason predicate |
| F29 | P01 task projection | every section-3.3 field equals its literal authority; `subject_rule` is the complete exact planned rule |
| F30 | finalize P01 with `()` | sole `EVIDENCE_MISSING` |
| F31 | one attestation copying the complete P01 task except request `absent@1` and `subject_rule=RuleRecord(rule:absent@1, head=atom:authoritative@2, positive={}, certificate=certificate:absent@1, negative={}, faces={})`; actual authority/attestation fields copy P01 | sole `EVIDENCE_EXTRA`, source `EVIDENCE_REQUEST absent@1`, target `certificate:absent@1` |
| F32 | two valid attestations for P01 task with distinct attestation IDs | sole `EVIDENCE_DUPLICATE`; neither selected |
| F33 | known-request task changes only source SHA to 64 `2` digits | sole `EVIDENCE_TASK_MISMATCH` |
| F34 | task changes only policy ID to `policy:other` | sole task mismatch |
| F35 | task changes only policy version to 4 | sole task mismatch |
| F36 | task changes only question to `Other question.` | sole task mismatch |
| F37 | task changes only `subject_rule` to a valid otherwise-equal rule with ID `rule:other@1` | sole task mismatch |
| F38 | task changes only `subject_rule.certificate` to `certificate:other@1` | sole task mismatch |
| F39 | task changes only checker ID to `rule-witness-alt/v1` | sole task mismatch |
| F40 | task changes only checker version to 2 | sole task mismatch |
| F41 | task changes only expected authority ID to `evidence-authority:other` | sole task mismatch |
| F42 | task changes only expected authority version to 3 | sole task mismatch |
| F43 | task changes only package ID to `package:other` | sole task mismatch |
| F44 | task changes only cut ID to `cut:2` | sole task mismatch |
| F45 | task changes only frame ID to `frame:2` | sole task mismatch |
| F46 | task changes only registry ID to `other-registry` | sole task mismatch |
| F47 | task changes only registry version to 2 | sole task mismatch |
| F48 | distinct, structurally equal reconstruction of P01 task and attestation | success; equal bound projection, proving no object-identity comparison |
| F49 | exact task, actual authority ID `evidence-authority:other` | sole authority mismatch |
| F50 | exact task, actual authority version 3 | sole authority mismatch |
| F51 | P02 requests `local:e-a@1` and `local:e-a@2` reuse exact identity `evidence-authority:test@2 / reused@1`; the third row is unchanged | sole `ATTESTATION_REF_COLLISION` with exactly those two request sources and certificate targets |
| F52 | those same two rows use distinct IDs `reused:a@1`, `reused:b@1`; the third row is unchanged | success |
| F53 | P01 details contain `extra="x"` and valid witness | binder succeeds; later validator emits sole `POLICIES/CHECKER_PAYLOAD` at `certificate[certificate:authoritative@6].details`, certificate ref, empty details |
| F54 | P01 witness detail is exact integer 1 | same exact later validator issue as F53 |
| F55 | P01 route uses permitted `two-detail/v1@1`; details are exactly `EvidenceDetail("witness", "witness:1")` and `EvidenceDetail("count", 7)`, submitted in each order | attestations, certificates, bound projections equal; later validation succeeds |
| F56 | P05 inside the complete F58 fresh-child traps and file-descriptor capture | adversarial question retained exactly in task; no semantic field, route, result, metadata, base, or side effect changes; every trap count is zero and exact FD1/FD2 bytes are empty |
| F57 | S01 accepted prose envelope versus marker-only envelope with provider/model/request set to `other-provider`, `other-model`, `other-request` | tasks and candidate packages equal; retained source sidecars distinguish the attempts |
| F58 | exact traps below around plan/finalize only | F01 succeeds and every trap count is zero; traps restore before explicit validation |
| F59 | P02 evidence in planned-task order | success; evidence canonicalized by planned task |
| F60 | F59 evidence reversed | bound projection equals F59 |
| F61 | F01 origin/index projection | exact package-record key set and exact three role/source rows; every positive lookup exact |
| F62 | source mismatch plus missing atom map | source mismatch only; F15/F16 prove both singles reach their gates |
| F63 | registry version mismatch plus unknown checker | registry mismatch only; F21/F24 are singles |
| F64 | missing atom map plus unknown checker | coverage issue only; F16/F24 are singles |
| F65 | target collision plus unknown checker | collision only; F08/F24 are singles |
| F66 | `closure-only/v1@2` | checker version mismatch only; F25/F26 are singles |
| F67 | omit the ordinary P01 attestation and submit exactly the F31 unknown-request attestation | exact `EVIDENCE_MISSING` plus `EVIDENCE_EXTRA` set, with the F31 certificate target; no task or authority issue |
| F68 | known request has task mismatch and wrong actual authority | task mismatch only; F36/F49 are singles |
| F69 | independently reconstruct equal S01 source, P01, and attestation twice | equal public outputs; all input structural snapshots unchanged |
| F70 | F01 population projections | draft typed sources = map sources = planned atom/rule records; requests = bindings = tasks = evidence; origin keys = package record keys |
| F71 | repeat F00 twice under F58 traps | equal empty successes; neither dispatch is skipped |
| F72 | P01 atom target ID is the lone surrogate `\ud800` | sole `TARGET_INVALID_ID` |
| F73 | P01 atom target ID is `"x" * 262_145` | sole `TARGET_INVALID_ID` |
| F74 | P01 atom target version is `9_223_372_036_854_775_808` | sole `TARGET_INVALID_VERSION` |
| F75 | P01 atom target ID is `"\u00e9" * 131_072` (exactly 262,144 UTF-8 bytes) | planning and finalization succeed |
| F76 | P01 atom target version is `9_223_372_036_854_775_807` | planning and finalization succeed |
| F77 | two unknown-request attestations copy F31's complete task and P01 authority/result/payload/details, share request `absent@1`, use subject-rule/certificate refs `rule:absent:b@2` / `certificate:absent:b@2` and `rule:absent:a@10` / `certificate:absent:a@10`, and have IDs `attestation:absent:b@2` and `attestation:absent:a@10` | one `EVIDENCE_EXTRA`; targets are both distinct certificate refs in profile order |
| F78 | P04H checker route changed to known `closure-only/v1@1` | same phase contains `HEAD_PREDICATE_UNKNOWN` plus `CHECKER_NOT_PERMITTED` with exactly `reason=subject`, `reason=use`; no predicate reason |
| F79 | exact P01 task with actual authority ID `evidence-authority:other` and version 3 | one authority mismatch with the exact four always-present detail strings from section 8.2 |
| F80 | P03 plan lookup for the same local ref `shared@13` under `ATOM`, `RULE`, and `EVIDENCE_REQUEST` | exact results `atom:shared@101`, `rule:shared@201`, and `certificate:shared@301` respectively |
| F81 | P01 adds record rows ATOM `absent:a@1 -> extra:same@1` and RULE `absent:r@1 -> extra:same@1` | sole `RECORD_BINDING_EXTRA`; both typed sources and the singleton distinct target `extra:same@1` |
| F82 | P01 adds evidence rows `absent:a@1 -> extra:certificate:same@1` and `absent:b@1 -> extra:certificate:same@1`, each with ordinary checker/authority | sole `EVIDENCE_BINDING_EXTRA`; both request sources and the singleton distinct certificate target |
| F83 | P01 atom target ID is `"\u00e9" * 131_072 + "a"` (262,145 UTF-8 bytes but only 131,073 Python characters) | sole `TARGET_INVALID_ID` |
| F84 | P01 atom target version is `-1` | sole `TARGET_INVALID_VERSION` |
| F85 | P01 expected authority ID is `"\u00e9" * 131_072` and its sole submitted exact-task attestation instead asserts actual authority ID `evidence-authority:other` | sole `EVIDENCE_AUTHORITY_MISMATCH`; its always-present `expected_authority_id=` detail is exactly 262,166 UTF-8 bytes and all four details remain constructible under the derived diagnostic limit |
| F86 | P01 adds record rows ATOM `absent:a@1 -> RecordRef("\ud801",1)` and RULE `absent:b@1 -> RecordRef("\ud800",1)` | sole phase-20 `RECORD_BINDING_EXTRA`; target tuple is exactly `RecordRef("\ud800",1)`, `RecordRef("\ud801",1)` in that order; no phase-30 issue |
| F87 | P06 and its complete 4,096-attestation tuple | planning and finalization succeed; plan has exactly 1 atom, 4,096 rules, 4,096 tasks, and 8,193 origins; bound evidence has 4,096 members; candidate has exactly 1 atom, 4,096 rules, 4,096 certificates, empty deferred collections, and empty base |
| F88 | P02 requests `local:e-a@1` and `local:e-a@2` reuse identity `evidence-authority:test@2 / ("\u00e9" * 131_072)@1`; the third row is unchanged | sole `ATTESTATION_REF_COLLISION` with F51's two sources/targets; its `attestation_id=` detail is exactly 262,159 UTF-8 bytes and all four details are retained |
| F89 | P07 and its complete 4,096-attestation tuple | planning and finalization succeed; plan has exactly 2 atoms, 4,096 rules, 4,096 tasks, and 8,194 origins; bound package has exactly 2 atoms, 4,096 rules, and 4,096 certificates; no 8,193-origin cap exists |
| F90 | P08 with both policy tuples and attestations submitted in order `@10,@2` | policy record sources are `ATOM a@1`, `RULE r@2`, `RULE r@10`; evidence request sources are `e@2`, `e@10`; plan rules by final ref are `rule:numeric@2` from `r@10`, then `rule:numeric@10` from `r@2`; tasks and bound evidence are request `e@2`, then `e@10`; certificates are `certificate:numeric@2` from `e@10`, then `certificate:numeric@10` from `e@2`; origins are the exact atom row followed by those two rule rows and those two certificate rows; all corresponding `target_for` lookups are exact; planning, finalization, and validation succeed |
| F91 | P01 adds ATOM extras `extra@2 -> extra:target@10` and `extra@10 -> extra:target@2` | sole `RECORD_BINDING_EXTRA`; sources are `extra@2`, `extra@10` and targets are `extra:target@2`, `extra:target@10`, proving numeric version sorting in diagnostics |
| F92 | the sole P01 submitted task changes only `subject_rule.head` to `atom:other@1` | sole `EVIDENCE_TASK_MISMATCH` |
| F93 | the sole P01 submitted task changes only `subject_rule.positive` to `{atom:other@1}` | sole `EVIDENCE_TASK_MISMATCH` |
| F94 | the sole P01 submitted task changes only `subject_rule.negative` to `{ClosedNegativeLiteral(atom=atom:other@1, closure=closure:other@1)}` | sole `EVIDENCE_TASK_MISMATCH` |
| F95 | the sole P01 submitted task changes only `subject_rule.faces` to `{face:other@1}` | sole `EVIDENCE_TASK_MISMATCH` |
| F96 | P01 policy and `RC1-R(MAX)` both use registry version `MAX`; exact matching attestation | planning, finalization, and validation succeed; plan registry and task registry version are exactly `MAX` |
| F97 | ordinary P01 with `RC1-R(MAX)` | sole ordinary `REGISTRY_VERSION_MISMATCH`, exact details `actual=1`, `expected=9223372036854775807` |
| F98 | ordinary P01 with `RC1-R(MAX+1)` | sole `REGISTRY_VERSION_UNSUPPORTED`, exact empty source/target tuples and details `registry_id=test-registry/1`, `supported_max=9223372036854775807` |
| F99 | P01 additionally routed to `missing-checker@1`, with `RC1-R(U)` | same sole `REGISTRY_VERSION_UNSUPPORTED` as F98; no routing issue, decimal conversion, or other exception |
| F100 | P01 binding and `RC1-C(rule-witness/v1,MAX)` both use checker version `MAX`; exact matching attestation | planning, finalization, and validation succeed; task checker version is exactly `MAX` |
| F101 | ordinary P01 with `RC1-C(rule-witness/v1,MAX)` | sole ordinary `CHECKER_VERSION_MISMATCH`, exact details `actual=1`, `expected=9223372036854775807` |
| F102 | ordinary P01 with `RC1-C(rule-witness/v1,MAX+1)` | sole `CHECKER_VERSION_UNSUPPORTED`, exact local rule/request sources, exact route targets, and details `checker_id=rule-witness/v1`, `supported_max=9223372036854775807` |
| F103 | ordinary P01 with `RC1-C(rule-witness/v1,U)` | same sole `CHECKER_VERSION_UNSUPPORTED` as F102; no decimal conversion or other exception |
| F104 | P01 routed to `closure-only/v1@1` with `RC1-C(closure-only/v1,U)` | sole `CHECKER_VERSION_UNSUPPORTED`, details use `checker_id=closure-only/v1`; no checker-version mismatch or permission reasons |
| F105 | P04H with `RC1-C(rule-witness/v1,U)` | exact phase-50 issue set contains `HEAD_PREDICATE_UNKNOWN` and `CHECKER_VERSION_UNSUPPORTED`; the unsupported checker does not suppress the independent head diagnostic |

F01-F03 additionally compare the complete external compiler/evaluator
projection, not only the mapped atom's headline status. Let:

```text
A = atom:authoritative@2
V = __pff__:cert-valid(certificate:authoritative@6)
F = __pff__:cert-failed(certificate:authoritative@6)
O = __pff__:cert-open(certificate:authoritative@6)
L = __pff__:live-case(rule:authoritative@4)
```

For all three rows the exact ground universe is `{A,V,F,O,L}` and the exact
rules are
`__pff__:rule-case(rule:authoritative@4): L <- V` and
`__pff__:head-bridge(rule:authoritative@4): A <- L`.

| Row | `base_live` | `base_excluded` | `protected_open` | Evaluation `live` | Evaluation `excluded` | Evaluation `suspended` |
|---|---|---|---|---|---|---|
| F01 PASS | `{V}` | `{}` | `{}` | `{V,L,A}` | `{F,O}` | `{}` |
| F02 FAIL | `{F}` | `{V}` | `{}` | `{F}` | `{V,O,L,A}` | `{}` |
| F03 OPEN | `{O}` | `{}` | `{V}` | `{O}` | `{F}` | `{V,L,A}` |

The candidate PFF `BasePartition` remains empty in every row; the displayed
sets are compiler-produced ground bases only.

F58's runtime half dispatches F01 and F56 in two dedicated fresh interpreter
processes. The parent harness starts each process before any child trap is
installed. Inside each child, the harness imports every trap-owning origin
module, saves the original
`importlib.import_module` object, installs the traps, removes
`poietics.binding` and every `poietics.binding.*` entry from `sys.modules`, and
uses only the saved original import function to bootstrap one fresh import of
`poietics.binding.model`, `.plan`, and `.finalize`. The installed
`importlib.import_module` trap remains active during production imports and
calls, so binding code cannot use that saved harness reference. The child then
invokes its one planning/finalization scenario and reports its exact result and trap counts over
an IPC byte channel. The harness captures file descriptor 1 and file descriptor
2 around both fresh binding imports and both calls; their complete exact byte
contents must each be empty. The process exits, so no imported binding class identity
or module cache can affect a later fixture. It patches these fully qualified
symbols to raise if called:
`poietics.generation.extract.extract_draft`,
`poietics.generation.ollama.generate_ollama`,
`poietics.generation.ollama_http.OllamaHttpTransport.__call__`,
`poietics.pff.validate.validate_package`,
`poietics.pff.compile.compile_package`,
`poietics.ground.evaluate.evaluate`, `builtins.open`,
`socket.create_connection`, `subprocess.run`, `subprocess.Popen`, `os.getenv`,
`time.time`, `time.monotonic`, `random.random`, `uuid.uuid4`,
`logging.Logger._log`, and `importlib.import_module`. The traps are restored
before the fixture's explicit later validation/compilation/evaluation.

The static half parses exactly `src/poietics/binding/__init__.py`, `model.py`,
`plan.py`, and `finalize.py`, including imports nested inside functions.
`__init__.py` has an AST body of exactly one expression whose value is an
exact string constant (its module docstring); zero imports, assignments,
exports, calls, or other statements are permitted. Every project import in the
other three files must be `ImportFrom` rather than `Import`, with no star, and
the resolved module/name pairs must be subsets of this exact map:

```text
poietics.generation.extract: ExtractedDraft
poietics.generation.model: DraftRef
poietics.pff.model: AtomRecord, BasePartition, CertificateRecord, CheckResult,
                    Package, PackageHeader, RecordKind, RecordRef, RuleRecord
poietics.pff.registry: CheckerUse, PredicateRegistry, RegistryCatalog
poietics.binding.model: BindingCode, BindingIssue, BindingOrigin, BindingPhase,
                        BindingPlan, BindingRole, BoundPackage,
                        DraftBindingError, DraftBindingPolicy, DraftRecordKind,
                        DraftSource, EvidenceAttestation, EvidenceBinding,
                        EvidenceDetail, EvidenceTask, RecordIdentityBinding
```

The static half also performs a fail-closed symbolic lineage pass over
`binding/plan.py` and the `BindingPlan` factory path in `binding/model.py`.
Starting at the unique expression passed as the internal factory's `origins=`
argument, it inlines only local names with one reaching assignment and
normalizes only transparent `tuple(x)`, `sorted(x, key=_origin_key)`, and tuple
concatenation. The resulting intermediate representation must be exactly
`Sort(Concat(LeafA, LeafR, LeafE), _origin_key)`.

Each leaf is one generator or comprehension with exactly one non-async `for`,
no filters, and one exact `BindingOrigin(...)` element. `LeafA` iterates
directly over `source.draft.atoms` and fixes target/role/source kinds to
`ATOM/DRAFT_ATOM/ATOM`; `LeafR` iterates directly over
`source.draft.rules` and fixes `RULE/DRAFT_RULE/RULE`; `LeafE` iterates
directly over `source.draft.evidence_requests` and fixes
`CERTIFICATE/EVIDENCE_CERTIFICATE/EVIDENCE_REQUEST`. Each target lookup uses
the same exact typed `DraftSource` constructed for that leaf, and each leaf
occurs exactly once. Symbolic interpretation must yield the lineage multiset
`A ⊎ R ⊎ E` and cardinality polynomial `|A| + |R| + |E|`.

The unique write to the public `origins` slot is exactly
`object.__setattr__(self, "origins", origins)`. Its private origin index is the
unfiltered comprehension `{(o.target_kind, o.target): o for o in origins}`
wrapped by `MappingProxyType`. Across this lineage, any unresolved alias or
node fails. The pass rejects slices, filters, `break`, `continue`, `IfExp`,
`islice`, `takewhile`, `dropwhile`, `min`, `max`, bounded `zip` or `range`, and
every comparison, branch, assertion, match guard, early return, or raise whose
dataflow contains an origin-tainted value. It also rejects a cardinality
predicate derived from source atom/rule/request or policy binding populations
in the origin-builder/factory path. This proves totality for every admitted
population rather than chasing successive maximum-plus-one examples.

The same static pass seeds the selected `PredicateRegistry.version` and every
resolved `CheckerContract.version` as external-version-tainted values. On every
path, the exact numeric comparison with the profile maximum must dominate any
`str`, `repr`, `format`, f-string, decimal conversion, interpolation, or
diagnostic construction that reads the tainted value. The unsupported branch
may use the value only in that numeric comparison; its issue construction must
use the bounded code-owned label and policy-owned ID from section 8. An
unresolved alias or a conversion before the dominating comparison fails F58.

Standard-library imports are limited to `__future__`, `collections.abc`,
`dataclasses`, `enum`, `types`, and `typing`. The sole permitted relative form
is `from .model import <mapped name>`, resolved as
`poietics.binding.model`; every other relative or unresolved import, dynamic
import call, or imported symbol outside the map is forbidden. Registry lookup
and immutable checker-contract policy
methods are not checker execution and remain callable. The child restores
traps before any explicit later validation/compilation/evaluation inside that
child; parent process state was never altered.

### 11.5 Constructor population C

The boundary batches below are exact finite operations, not hidden families.
The fixed-profile batch `P` is, in order,
`DraftBindingPolicy.profile`, `EvidenceTask.profile`, and
`EvidenceAttestation.profile`. The SHA-256 batch `H` is, in order,
`DraftBindingPolicy.source_payload_sha256`,
`EvidenceTask.source_payload_sha256`, and
`EvidenceAttestation.payload_hash`. C12, C14, and C15 compare all three results
in their displayed batch; no field-local omission is hidden by another slot.

For `C38` through `C40`, `B` is this displayed ordered list of every
caller-supplied arbitrary binding-string slot:

```text
B = (
  EvidenceBinding.checker_id,
  EvidenceBinding.authority_id,
  DraftBindingPolicy.policy_id,
  DraftBindingPolicy.package_id,
  DraftBindingPolicy.cut_id,
  DraftBindingPolicy.frame_id,
  DraftBindingPolicy.registry_id,
  EvidenceTask.policy_id,
  EvidenceTask.question,
  EvidenceTask.checker_id,
  EvidenceTask.expected_authority_id,
  EvidenceTask.package_id,
  EvidenceTask.cut_id,
  EvidenceTask.frame_id,
  EvidenceTask.registry_id,
  EvidenceDetail.key,
  EvidenceDetail.value when that value is a string,
  EvidenceAttestation.authority_id,
  EvidenceAttestation.attestation_id,
)
```

Fixed profile/request-kind literals and SHA-256 fields have their own exact
literal validators and cases C12-C15. `BindingIssue.details` has its separate
derived limit in C71-C72. Embedded source refs are upstream-owned, and policy
target refs are phase-30-owned. Each B operation starts from the exact P01
ordinary component containing that slot, changes only that slot, and records
one result in B order. The complete fixture observable is the entire 19-result
tuple, so omitting validation for any one field fails the row.

For `C41` through `C44`, `V` is this displayed ordered list of every
caller-supplied positive binding integer slot:

```text
V = (
  EvidenceBinding.checker_version,
  EvidenceBinding.authority_version,
  DraftBindingPolicy.version,
  DraftBindingPolicy.registry_version,
  EvidenceTask.policy_version,
  EvidenceTask.checker_version,
  EvidenceTask.expected_authority_version,
  EvidenceTask.registry_version,
  EvidenceAttestation.authority_version,
  EvidenceAttestation.attestation_version,
)
```

Each V operation likewise changes only that slot in its exact ordinary P01
component and compares the complete ordered ten-result tuple. Upstream
`DraftRef` integers and phase-30 policy-target `RecordRef` integers are not V.

The origin-coherence batch uses target `RecordRef("origin:target", 1)` and
source ref `DraftRef("origin:source", 1)`. It enumerates the Cartesian product
of target kinds `(ATOM, RULE, CERTIFICATE)`, roles
`(DRAFT_ATOM, DRAFT_RULE, EVIDENCE_CERTIFICATE)`, and source kinds
`(ATOM, RULE, EVIDENCE_REQUEST)`, target-kind outermost, role next, source-kind
innermost.

For C59-C62, `Q` is the displayed ordered tuple of exact ordinary P01 values:
`DraftSource`, `RecordIdentityBinding`, `EvidenceBinding`,
`DraftBindingPolicy`, `EvidenceTask`, `EvidenceDetail`,
`EvidenceAttestation`, the coherent P01 atom `BindingOrigin`, and the exact
table-compatible F15 `BindingIssue`. An independently reconstructed twin means
equal field values in a distinct instance.

For C68-C70, define `SX2 = DraftSource(ATOM, DraftRef("x",2))`,
`SX10 = DraftSource(ATOM, DraftRef("x",10))`, `TX2 = RecordRef("x",2)`,
and `TX10 = RecordRef("x",10)`. The source-order case is a phase-30
`TARGET_REF_COLLISION` at `/policy/targets` with sources `SX2,SX10` and target
`collision@1`. The target-order case is a phase-60 `EVIDENCE_EXTRA` at
`/evidence` with source `DraftSource(EVIDENCE_REQUEST,DraftRef("absent",1))`
and targets `TX2,TX10`. The detail-order case is the exact P01
`EVIDENCE_AUTHORITY_MISMATCH` shape with its four section-8 labels. Duplicate
cases repeat the first canonical member; reverse cases reverse the complete
canonical tuple. C70's two issues are exact phase-30 `TARGET_INVALID_ID`
issues at `/policy/targets/id`, respectively
`(SX2,(RecordRef("",2),),())` and `(SX10,(RecordRef("",10),),())` for sources,
targets, and details.

For C48-C53 and C81, let `q(i)` be the four-character zero-padded decimal
spelling of `i` for `0..8192`. Define exact members:

```text
RB(i) = RecordIdentityBinding(
          ATOM, DraftRef("r:"+q(i),1), RecordRef("target:r:"+q(i),1))
EB(i) = EvidenceBinding(
          request=DraftRef("e:"+q(i),1),
          certificate=RecordRef("target:e:"+q(i),1),
          checker_id="rule-witness/v1", checker_version=1,
          authority_id="evidence-authority:test", authority_version=2)
ED(i) = EvidenceDetail("k:"+q(i), "")
```

Each policy case copies P01's scalar fields exactly. A case that changes only
one policy tuple retains P01's other ordinary tuple.

C80's registry issue is exactly
`BindingIssue(REGISTRY, REGISTRY_VERSION_UNSUPPORTED,
"/catalog/registry/version", (), (),
("registry_id=test-registry/1",
"supported_max=9223372036854775807"))`. Its checker issue is exactly
`BindingIssue(ROUTING, CHECKER_VERSION_UNSUPPORTED,
"/catalog/registry/checker_contracts/version",
(DraftSource(RULE,DraftRef("rule:generated",7)),
DraftSource(EVIDENCE_REQUEST,DraftRef("evidence:generated",11))),
(RecordRef("certificate:authoritative",6),
RecordRef("rule:authoritative",4)),
("checker_id=rule-witness/v1",
"supported_max=9223372036854775807"))`. All displayed tuples are already in
their canonical order.

| ID | Exact operation | Required result |
|---:|---|---|
| C00 | pass naked successful `DraftPackage` to planner | `TypeError` before diagnostics |
| C01 | source duck object | `TypeError` |
| C02 | policy duck object | `TypeError` |
| C03 | catalog duck object | `TypeError` |
| C04 | finalize with plan duck | `TypeError` |
| C05 | evidence list instead of tuple | `TypeError` |
| C06 | evidence tuple containing duck attestation | `TypeError` |
| C07 | direct empty `BindingPlan()` | `TypeError`, no partial object |
| C08 | direct fully populated `BindingPlan(...)` | `TypeError`, no partial object |
| C09 | direct empty `BoundPackage()` | `TypeError`, no partial object |
| C10 | direct fully populated `BoundPackage(...)` | `TypeError`, no partial object |
| C11 | ordinary complete `EvidenceAttestation` construction | succeeds; positive honesty control |
| C12 | independently set each P slot to exact string `wrong-profile` | exact three-result tuple of constructor `ValueError` outcomes |
| C13 | independently set `EvidenceTask.request_kind="other"` and `RecordIdentityBinding.source_kind=EVIDENCE_REQUEST` | exact two-result tuple of constructor `ValueError` outcomes |
| C14 | independently set each H slot first to `sha256:` plus 64 uppercase `A` digits and then to `sha256:` plus 64 lowercase nonhex `g` digits | exact six-result tuple of constructor `ValueError` outcomes in H order within each bad spelling |
| C15 | independently set each H slot to `sha256:` plus 63 lowercase `1` digits, `sha256:` plus 65 lowercase `1` digits, and `sha257:` plus 64 lowercase `1` digits | exact nine-result tuple of constructor `ValueError` outcomes in H order within each bad spelling |
| C16 | exact detail integer 1 versus exact bool true | remain distinct accepted values |
| C17 | integer subclass detail | `TypeError` |
| C18 | string subclass detail | `TypeError` |
| C19 | duplicate detail key tuple | `ValueError`, no last-wins value |
| C20 | assign a plan public field | immutability error; snapshot unchanged |
| C21 | mutate a plan private index | `TypeError`; lookup projection unchanged |
| C22 | assign a bound-package field | immutability error; snapshot unchanged |
| C23 | mutate its nested candidate package | immutability error; snapshot unchanged |
| C24 | `hash(plan)` | `TypeError` |
| C25 | `hash(bound)` | `TypeError` |
| C26 | `repr(plan)` | contains no source/envelope/captured bytes/question |
| C27 | `repr(bound)` | contains no attestation or detail values |
| C28 | `target_for` wrong kind type | `TypeError` |
| C29 | `target_for` missing exact typed ref | `KeyError` |
| C30 | `task_for` wrong ref type | `TypeError` |
| C31 | `task_for` missing exact version | `KeyError` |
| C32 | `origin_for` wrong record-kind type | `TypeError` |
| C33 | `origin_for(RecordKind.RULE, atom:authoritative@2)` on P01 | `KeyError`, proving the existing ref is not looked up without kind |
| C34 | attestation details list rather than tuple | `TypeError` |
| C35 | policy bindings list rather than tuple | `TypeError` |
| C36 | subclass of `DraftBindingPolicy` passed to planner | `TypeError` |
| C37 | subclass of `EvidenceAttestation` in final tuple | `TypeError` |
| C38 | independently set each B slot to `"\u00e9" * 131_072` (262,144 UTF-8 bytes) | exact 19-result tuple of successful constructions |
| C39 | independently set each B slot to `"\u00e9" * 131_072 + "a"` (262,145 UTF-8 bytes) | exact 19-result tuple of constructor `ValueError` outcomes |
| C40 | independently set each B slot to the lone surrogate `"\ud800"` | exact 19-result tuple of constructor `ValueError` outcomes |
| C41 | independently set each V slot first to `1` and then to `9_223_372_036_854_775_807` | exact twenty-result tuple of successful constructions in V order within each value |
| C42 | independently set each V slot to zero | exact ten-result tuple of constructor `ValueError` outcomes |
| C43 | independently set each V slot to `9_223_372_036_854_775_808` | exact ten-result tuple of constructor `ValueError` outcomes |
| C44 | define exact `class IntSubclass(int): pass`; independently set each V slot to `True`, `IntSubclass(1)`, and exact string `"1"` | exact thirty-result tuple of constructor `TypeError` outcomes in V order within each value |
| C45 | one attestation has detail integers at both signed endpoints `-9_223_372_036_854_775_807` and `9_223_372_036_854_775_807` under distinct keys | construction succeeds and values remain exact |
| C46 | detail integer is `9_223_372_036_854_775_808` | constructor `ValueError` |
| C47 | detail integer is `-9_223_372_036_854_775_808` | constructor `ValueError` |
| C48 | policy record bindings are exact `RB(0)..RB(8191)` | construction succeeds |
| C49 | C48 plus exact `RB(8192)` | constructor `ValueError` |
| C50 | policy evidence bindings are exact `EB(0)..EB(4095)` | construction succeeds |
| C51 | C50 plus exact `EB(4096)` | constructor `ValueError` |
| C52 | attestation details are exact `ED(0)..ED(4095)` | construction succeeds |
| C53 | C52 plus exact `ED(4096)` | constructor `ValueError` |
| C54 | finalize P01 with an exact tuple containing 4,097 repetitions of the ordinary attestation | `ValueError` before evidence-population diagnostics |
| C55 | independently use `(P01 atom row, same exact row)` and `(P01 atom row, row with the same typed source but target atom:conflict@9)` as the complete policy record tuple | exact two-result tuple of constructor `ValueError` outcomes |
| C56 | independently use `(P01 evidence row, same exact row)` and `(P01 evidence row, row with the same request but certificate:conflict@9)` as the complete policy evidence tuple | exact two-result tuple of constructor `ValueError` outcomes |
| C57 | construct the complete 27-member origin Cartesian product defined above | only positions 1, 14, and 27, the three rank-aligned triples, succeed; every other position raises `ValueError` |
| C58 | independently replace a coherent origin's target kind with exact string `"atom"`, target with `DraftRef("origin:target",1)`, role with exact string `"draft-atom"`, and source with `RecordRef("origin:source",1)` | exact four-result tuple of constructor `TypeError` outcomes |
| C59 | construct every value in Q | exact nine-result tuple of successes |
| C60 | assign the first displayed public field of each Q value to its existing value using ordinary attribute assignment | exact nine-result tuple of `FrozenInstanceError`; every pre-call snapshot remains unchanged |
| C61 | hash every Q value and its independently reconstructed twin | all 18 calls succeed with exact integer results; each twin pair has equal hashes |
| C62 | evaluate `hasattr(value, "__dict__")` for every Q value | exact nine-result tuple of `False` values |
| C63 | `repr(EvidenceDetail("secret", "fixture-secret"))` | does not contain `fixture-secret` |
| C64 | compare `DraftSource(ATOM, a@1) < DraftSource(RULE, r@1)` | `TypeError`; canonical ranks are explicit sort keys, not a conflicting public generated order |
| C65 | `origin_for(RecordKind.ATOM, RecordRef("absent", 1))` | `KeyError` |
| C66 | construct `BindingIssue` with a valid code but wrong phase | `ValueError` |
| C67 | construct `BindingIssue` with the code's wrong path | `ValueError` |
| C68 | independently submit duplicate sources, duplicate targets, and duplicate details to otherwise-valid `BindingIssue` values | exact three-result tuple of constructor `ValueError` outcomes |
| C69 | independently submit reverse-canonical distinct two-source, two-target, and two-detail tuples to otherwise-valid `BindingIssue` values | exact three-result tuple of constructor `ValueError` outcomes |
| C70 | independently construct `DraftBindingError(())`, construct it with one non-issue, and construct it from the exact C70 issues in order source `x@10`, then `x@2`, then duplicate `x@2` | empty raises `ValueError`; wrong member raises `TypeError`; the third construction retains exactly the numeric order `(x@2 issue, x@10 issue)`, leaves its input tuple unchanged, and has exact message `draft binding failed` |
| C71 | construct a table-compatible `UNKNOWN_REGISTRY` `BindingIssue` whose sole detail is `"\u00e9" * 131_088` (262,176 UTF-8 bytes) | construction succeeds and retains the exact detail |
| C72 | C71 detail plus one ASCII `a` (262,177 UTF-8 bytes) | constructor `ValueError` |
| C73 | independently set each B identifier slot (all B slots except `EvidenceTask.question` and string `EvidenceDetail.value`) to the empty string | exact 17-result tuple of constructor `ValueError` outcomes |
| C74 | independently construct an otherwise-valid `EvidenceTask` with empty question and `EvidenceDetail("empty", "")` | exact two-result tuple of successful constructions retaining the empty strings |
| C75 | independently set each V slot to `-1` | exact ten-result tuple of constructor `ValueError` outcomes |
| C76 | for every B slot independently construct otherwise-equal components containing respectively `"\u00e9"` and `"e\u0301"` in that slot | exact 19 pairs retain their code points and compare unequal; no field-local NFC normalization |
| C77 | independently use exact `RecordRef("detail:ref",1)`, its exact subclass instance, float `1.0`, `None`, empty tuple, and empty list as an `EvidenceDetail.value` | the exact `RecordRef` construction succeeds and retains the ref; the other five constructions raise `TypeError` |
| C78 | define exact `class TupleSubclass(tuple): pass`; independently pass it as final evidence, attestation details, policy record bindings, policy evidence bindings, `BindingIssue.sources`, `BindingIssue.targets`, `BindingIssue.details`, and `DraftBindingError.issues` | exact eight-result tuple of `TypeError` outcomes before semantics |
| C79 | independently use a `str` subclass, exact integer `1`, and the lone surrogate `"\ud800"` as one `BindingIssue.details` member | exact outcomes `TypeError`, `TypeError`, `ValueError` |
| C80 | construct the complete exact F98 issue and complete exact F102 issue, then independently swap their phases and swap their exact paths | two successes followed by exact four-result tuple of `ValueError` outcomes |
| C81 | one P01-scalar policy has exact record tuple `RB(0)..RB(8191)` and exact evidence tuple `EB(0)..EB(4095)` simultaneously | construction succeeds with 8,192 record and 4,096 evidence bindings; there is no combined-population cap |
| C82 | independently construct an otherwise-valid P01 `EvidenceAttestation` with exact empty `details=()` and a valid `UNKNOWN_REGISTRY` `BindingIssue` whose sole detail member is the exact empty string | exact two-result tuple of successful constructions retaining the empty tuple/string |

## 12. Atomic mutation manifest

Every mutant below changes exactly one mechanism in binding code. Mutation is
performed only in an authenticated disposable copy. The exact required result
is `181 PREDICTED_KILL / 181`, zero wrong-reason kills, survivors, unreachable
probes, timeouts, or infrastructure failures.

| ID | One forbidden transformation | Required killer |
|---:|---|---|
| M01 | accept naked `DraftPackage` | C00 |
| M02 | compare policy digest to raw-response digest | F01 |
| M03 | omit source-digest comparison | F15 |
| M04 | admit missing record map | F16 |
| M05 | ignore extra record map | F17 |
| M06 | key record map without source kind | F07 |
| M07 | key record map without source version | F06 |
| M08 | use local atom ref as target | F01 |
| M09 | use local rule ref as target | F01 |
| M10 | leave rule head local | F01/F07 |
| M11 | leave positive premise local | F04/F07 |
| M12 | admit missing evidence binding | F18 |
| M13 | ignore extra evidence binding | F19 |
| M14 | derive certificate ref from request | F01 |
| M15 | omit global target uniqueness gate | F08 |
| M16 | treat equal target ID at distinct versions as collision | F11 |
| M17 | accept empty target ID | F12 |
| M18 | accept target version zero | F13 |
| M19 | accept reserved target ID | F14 |
| M20 | fallback/latest registry selection | F20 |
| M21 | ignore registry integer version | F21 |
| M22 | validate every atom predicate during planning | F23 |
| M23 | admit unknown head predicate | F22 |
| M24 | admit unknown checker | F24 |
| M25 | ignore checker integer version | F25 |
| M26 | ignore checker use | F26 |
| M27 | ignore RULE subject permission | F27 |
| M28 | ignore head-predicate checker allowlist | F28 |
| M29 | copy policy ID instead of exact question into task | F29/F56 |
| M30 | compare tasks by request only | F36 |
| M31 | compare tasks by Python identity | F48 |
| M32 | default missing evidence to PASS | F30 |
| M33 | default missing evidence to OPEN | F30 |
| M34 | accept unknown-request evidence | F31 |
| M35 | select one duplicate attestation | F32 |
| M36 | ignore actual authority ID | F49 |
| M37 | ignore actual authority version | F50 |
| M38 | omit attestation-identity uniqueness | F51 |
| M39 | validate checker details before producing BoundPackage | F53 |
| M40 | duplicate detail keys use last value | C19 |
| M41 | materialize FAIL as PASS | F02 |
| M42 | materialize OPEN as FAIL | F03 |
| M43 | materialize atom with `primitive=True` | F01 |
| M44 | insert mapped source atom into `base.live` | F01 |
| M45 | copy the exact evidence-request question into header metadata | F56 |
| M46 | call `extract_draft` from binder | F58 |
| M47 | call `validate_package` during finalization | F53/F58 |
| M48 | call `generation.ollama.generate_ollama` during planning | F58 |
| M49 | retain submitted policy tuple order semantically | F05 |
| M50 | retain submitted evidence tuple order | F59/F60 |
| M51 | append `source.envelope.provider_id` to the planned task package ID | F57 |
| M52 | omit atom origin | F61/F70 |
| M53 | omit rule origin | F61/F70 |
| M54 | omit certificate origin | F61/F70 |
| M55 | index origins by ref without record kind | C32/C33 |
| M56 | reject the zero-population draft | F00/F71 |
| M57 | `target_for` ignores source kind | C28/C29/F80 |
| M58 | `target_for` ignores source version | C29/F06 |
| M59 | `task_for` ignores request version | C31/F04 |
| M60 | make `BindingPlan` directly constructible | C07/C08 |
| M61 | make `BoundPackage` directly constructible | C09/C10 |
| M62 | remove frozen assignment protection from `BindingPlan` public fields | C20 |
| M63 | remove frozen assignment protection from `BoundPackage` public fields | C22 |
| M64 | make `BindingPlan` hashable | C24 |
| M65 | make `BoundPackage` hashable | C25 |
| M66 | expose source/captured bytes in plan repr | C26 |
| M67 | expose evidence/detail values in bound repr | C27 |
| M68 | retain submitted evidence-detail order | F55 |
| M69 | accept wrong evidence-task profile | C12 |
| M70 | accept wrong evidence-task request kind | C13 |
| M71 | accept uppercase hexadecimal in a SHA-256 value | C14 |
| M72 | treat bool as integer evidence detail | C16/C17 |
| M73 | count Unicode code points instead of UTF-8 bytes for binding-owned string limits | C38/C39 |
| M74 | accept a lone surrogate in a binding-owned string | C40 |
| M75 | omit the maximum-version check | C43/F74 |
| M76 | accept `bool` as a version | C44 |
| M77 | omit the positive signed detail-integer bound | C46 |
| M78 | omit the negative signed detail-integer bound | C47 |
| M79 | omit the 8,192 `record_bindings` maximum | C49 |
| M80 | omit the 4,096 `evidence_bindings` maximum | C51 |
| M81 | omit the 4,096 detail maximum | C53 |
| M82 | omit the 4,096 final-evidence maximum | C54 |
| M83 | accept duplicate record-binding source keys | C55 |
| M84 | accept duplicate evidence-binding request keys | C56 |
| M85 | ignore `BindingOrigin.target_kind` coherence | C57 |
| M86 | ignore `BindingOrigin.role` coherence | C57 |
| M87 | ignore `BindingOrigin.source.kind` coherence | C57 |
| M88 | expose `EvidenceDetail.value` in its generated representation | C63 |
| M89 | add generated dataclass ordering to `DraftSource` | C64 |
| M90 | accept a `BindingIssue` code in the wrong phase | C66 |
| M91 | accept a `BindingIssue` code at the wrong path | C67 |
| M92 | silently deduplicate caller-supplied issue sources | C68 |
| M93 | silently reorder a caller-supplied noncanonical issue tuple | C69 |
| M94 | permit an empty `DraftBindingError` | C70 empty subcase |
| M95 | permit a non-issue `DraftBindingError` member | C70 wrong-member subcase |
| M96 | report only the first certificate target for grouped unknown evidence | F77 |
| M97 | omit unchanged authority dimensions from authority-mismatch details | F49/F50/F79 |
| M98 | suppress independently decidable checker use/subject reasons when the head predicate is unknown | F78 |
| M99 | omit the target-ID UTF-8 length check | F73/F83 |
| M100 | accept a surrogate-containing target ID | F72 |
| M101 | omit `EVIDENCE_REQUEST` keys from the `target_for` index | F80 |
| M102 | aggregate extra record rows in a mapping keyed by target and therefore retain only the first source for a repeated target | F81 |
| M103 | aggregate extra evidence rows in a mapping keyed by certificate target and therefore retain only the first source for a repeated target | F82 |
| M104 | enforce target-ID length with Python character count instead of UTF-8 bytes | F83 |
| M105 | reject target versions only when equal to zero or above the maximum, thereby admitting `-1` | F84 |
| M106 | apply the 262,144-byte input-string ceiling to each binder-generated diagnostic detail after adding its fixed label | F85 |
| M107 | drop any phase-20 issue target whose ID cannot be encoded as strict UTF-8 before sorting | F86 |
| M108 | change the final-evidence length rejection from `> 4_096` to `>= 4_096` | F87 |
| M109 | construct tasks and certificate origins from `source.draft.evidence_requests[:-1]` | F87 |
| M110 | add `from .model import BindingPlan` to `binding/__init__.py` | F58 |
| M111 | accept a wrong `DraftBindingPolicy.profile` | C12 |
| M112 | accept a wrong `EvidenceAttestation.profile` | C12 |
| M113 | accept uppercase hexadecimal in `DraftBindingPolicy.source_payload_sha256` | C14 |
| M114 | accept uppercase hexadecimal in `EvidenceTask.source_payload_sha256` | C14 |
| M115 | accept a 63-digit `EvidenceAttestation.payload_hash` | C15 |
| M116 | accept an empty caller-supplied binding identifier | C73 |
| M117 | reject an empty direct-constructor `EvidenceTask.question` | C74 |
| M118 | reject an empty string `EvidenceDetail.value` | C74 |
| M119 | reject positive binding integers only when equal to zero, thereby admitting `-1` | C75 |
| M120 | apply the ordinary 262,144-byte ceiling to public `BindingIssue.details` | C71 |
| M121 | omit the 262,176-byte public `BindingIssue.details` ceiling | C72 |
| M122 | apply a 262,144-byte post-label cap specifically to `ATTESTATION_REF_COLLISION` details | F88 |
| M123 | sort equal-ID final record refs by decimal version strings | F11/F90 |
| M124 | reject a valid plan when its origin population exceeds 8,193 | F58/F89 |
| M125 | print each planned task question to standard output | F58 |
| M126 | permit `RecordIdentityBinding.source_kind=EVIDENCE_REQUEST` | C13 |
| M127 | accept exact float `EvidenceDetail.value` | C77 |
| M128 | accept tuple subclasses wherever an exact tuple is required | C78 |
| M129 | normalize binding-owned strings to NFC during construction | C76 |
| M130 | accept lowercase nonhex SHA-256 digits | C14 |
| M131 | accept a prefix other than exact `sha256:` | C15 |
| M132 | accept an integer subclass as a V value | C44 |
| M133 | require a caller-owned authority version to be at least 2 | C41 |
| M134 | reject an exact `RecordRef` evidence-detail value | C77 |
| M135 | accept a `RecordRef` subclass evidence-detail value | C77 |
| M136 | accept tuple subclasses in `BindingIssue` tuple fields | C78 |
| M137 | accept a tuple subclass for `DraftBindingError.issues` | C78 |
| M138 | admit a non-rank-aligned single-axis origin triple | C57 |
| M139 | admit a non-rank-aligned multi-axis origin triple | C57 |
| M140 | make an ordinary binding value mutable | C60 |
| M141 | make an ordinary binding value unhashable | C61 |
| M142 | remove slots from an ordinary binding value | C62 |
| M143 | accept duplicate issue targets | C68 |
| M144 | accept duplicate issue details | C68 |
| M145 | silently sort caller-supplied issue targets | C69 |
| M146 | silently sort caller-supplied issue details | C69 |
| M147 | accept a nonstring issue-detail member | C79 |
| M148 | accept a surrogate issue-detail string | C79 |
| M149 | retain duplicate `DraftBindingError` issues | C70 |
| M150 | order error issues by decimal version strings | C70 |
| M151 | retain the default exception message | C70 |
| M152 | retain policy submission order while the planner separately sorts | F05 |
| M153 | normalize only attestation IDs to NFC | C76 |
| M154 | ignore `subject_rule.head` in task equality | F92 |
| M155 | ignore `subject_rule.positive` in task equality | F93 |
| M156 | ignore `subject_rule.negative` in task equality | F94 |
| M157 | ignore `subject_rule.faces` in task equality | F95 |
| M158 | perform output or provider behaviour only for the P05 keywords | F56 |
| M159 | reject a policy when `len(record_bindings) + len(evidence_bindings) > 8_194` | C81 |
| M160 | order policy record bindings by decimal version strings | F90 |
| M161 | order policy evidence bindings by decimal version strings | F90 |
| M162 | order planned rules by decimal version strings | F90 |
| M163 | order tasks by decimal request-version strings | F90 |
| M164 | order origins by decimal version strings | F90 |
| M165 | order certificates by decimal version strings | F90 |
| M166 | order bound evidence by decimal request-version strings | F90 |
| M167 | order diagnostic targets by decimal version strings | F91 |
| M168 | classify a selected registry version equal to `MAX` as unsupported | F96 |
| M169 | feed an unsupported selected registry version into ordinary mismatch handling | F98 |
| M170 | append exact detail `actual_external=<decimal selected version>` to `REGISTRY_VERSION_UNSUPPORTED` | F98 |
| M171 | continue to routing after `REGISTRY_VERSION_UNSUPPORTED` | F99 |
| M172 | classify a resolved checker version equal to `MAX` as unsupported | F100 |
| M173 | feed an unsupported resolved checker version into ordinary mismatch handling | F102 |
| M174 | append exact detail `actual_external=<decimal resolved version>` to `CHECKER_VERSION_UNSUPPORTED` | F102 |
| M175 | run checker permission checks after `CHECKER_VERSION_UNSUPPORTED` | F104 |
| M176 | suppress an independent unknown-head diagnostic when checker version is unsupported | F105 |
| M177 | accept a SHA-256 spelling with 65 lowercase hexadecimal digits | C15 |
| M178 | call `str(registry.version)` before the dominating external-version range comparison | F58 |
| M179 | call `str(checker.version)` before the dominating external-version range comparison | F58 |
| M180 | reject exact empty `EvidenceAttestation.details` | C82 |
| M181 | reject an exact empty string `BindingIssue.details` member | C82 |

The mutation evidence bundle records the exact candidate tree, criteria hash,
mutant identity, changed mechanism, named killer, command, exit status, and
observed complete outcome. The classification sets are pairwise disjoint and
their union equals `M`.

## 13. Explicit deferrals

The following are outside this profile and must not be guessed:

- evidence authentication, signature verification, checker execution,
  credential/key loading, retries, timeouts, or authority discovery;
- automatic construction of policy, identity mappings, checker routes, or
  evidence attestations from LLM prose;
- primitive atoms, base membership, seed-package merging, or references to
  records outside the exact draft;
- negative rules, faces, closures, contraries, challenges, discharges, and
  successor/revocation syntax;
- package validation inside binding, compilation, evaluation, explanation,
  status narration, or repair control;
- canonical Package/plan/task/attestation bytes or hashes, durable storage,
  append-only replay, signatures, rehydration, and cross-package attestation
  identity enforcement;
- persistent provenance DAGs, canonical JSON, package hashing, CLI, provider
  orchestration, and empirical or later predicate packs.

A future naming-policy builder may generate an explicit
`DraftBindingPolicy`, but the accepted v0.1 binder continues to consume the
fully materialised immutable policy and does not accept callbacks. A future
draft-schema version may add proposal kinds only through a separately accepted
binder profile; v0.1 never fills absent fields implicitly.

## 14. Acceptance and implementation gate

This candidate is accepted only after all of the following are independently
clean:

1. architecture review proves the dependency direction, authority split,
   exact mappings, and stopping boundary;
2. semantic review derives every materialised field and diagnostic from the
   authority hierarchy and finds no unresolved identity, evidence, validation,
   or replay choice;
3. criteria review proves the exact `S`, `F00-F105`, and `C00-C82`
   populations discriminate the named alternatives and `M01-M181` closes the
   mutation population; and
4. the reviewed candidate bytes are recorded before the mechanical acceptance
   transformation.

Acceptance changes only the `Status` line from `CANDIDATE SEMANTIC PROFILE` to
`ACCEPTED SEMANTIC PROFILE` and appends exactly one LF byte followed by this
section, with one final LF after its closing fence:

````text
## 15. Acceptance record

```text
profile: pff-draft-binding/0.1
status: accepted
accepted_on: 2026-08-18
reviewed_candidate_sha256: sha256:<64 lowercase hexadecimal digits>
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
````

`reviewed_candidate_sha256` is computed over the complete candidate bytes,
including their existing final LF, before the status replacement or appended
record. The angle-bracket token is replaced by the exact lowercase candidate
digest and the angle brackets are not retained. No other semantic sentence,
table, identifier, diagnostic, fixture, mutant, whitespace, or byte may change
during acceptance.

Implementation begins only after the accepted document is published. The
implementation gate must include focused and full tests, exact import and
call-boundary inspection, the complete `F00-F105` and `C00-C82` fixture
populations, predicted kills for `M01-M181`, and independent clean
implementation reviews. Later
implementation evidence cannot silently amend this authority.

## 15. Acceptance record

```text
profile: pff-draft-binding/0.1
status: accepted
accepted_on: 2026-08-18
reviewed_candidate_sha256: sha256:8c347531cb217d9a8b66b71db7a7906594b70f30e949e0f52ad4cf36507b9b7b
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
