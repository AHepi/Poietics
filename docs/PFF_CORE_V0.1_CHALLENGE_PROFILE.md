# PFF Core 0.1 Challenge/Discharge Profile

**Status:** ACCEPTED SEMANTIC PROFILE

**Date:** 2026-08-17

**Accepted:** 2026-08-17 by explicit user direction

**Implementation baseline:** `28a2df5bffa382b654b03e9fda468f2b2078e41c`

**Scope:** close only the semantic gaps required for the next validation and compiler slices

This document is the accepted conservative, executable profile for challenge
and discharge semantics. It supplements the core specification only within its
stated scope. At its implementation baseline, the published compiler still
rejects all challenge and discharge records.

## 1. Authority and notation

The authority order for this profile is:

1. `poietic-pff-implementable-core-spec-v0.1.md`, SHA-256
   `43f4c4cb50292feccf2b0fc45e517d1ec4bf60c908600b96169ce4702bc99aa9`.
2. This accepted document, identified by its published commit and file bytes.
3. The published implementation at the baseline commit above, as evidence of
   the existing API and dependency boundary, not as semantic authority.

`LESSONS_LEARNED_2026-08-17.md`, SHA-256
`9b4fe50618b53260e1d32533a2709da5a367c337adf35ced8c109e4fbaa25f7a`,
is implementation guidance only.

Rules are tagged as follows:

| Tag | Meaning |
|---|---|
| `[S]` | Direct restatement of the core specification |
| `[C]` | Clarification selecting one reading already required by the core |
| `[N]` | New normative choice needed to make the phase deterministic |
| `[D]` | Explicitly deferred; no implementation may guess the missing rule |

## 2. Thin waist and generator placement

This section answers the generator-placement question but is not part of the
challenge-profile acceptance request in section 13. `[D]` The names and exact
generation protocol remain provisional until a separate generator freeze.

The required architectural constraint is that a future generator remains
upstream of the package authority boundary:

```text
LLM or other generator
    -> captured GenerationEnvelope and untrusted DraftPackage
    -> deterministic extraction checks and trusted evidence binding
    -> immutable Package
    -> validate_package
    -> compile_package
    -> GroundProgram
    -> evaluate
    -> structured result and optional prose explanation
```

An LLM's prose is source material, not executable semantics. A prose-only
response must pass through a typed extraction step. The raw response is retained
unchanged beside the extracted draft so that extraction can be audited or
replayed. An LLM adapter must not call `validate_package` with an object it
materialized directly as an authoritative `Package`.

A later provider-neutral generation layer should define an immutable
`GenerationEnvelope` carrying at least the prompt or prompt hash, provider and
model identifiers, generation parameters, the raw response bytes or an immutable
content-addressed reference plus their hash, and the untrusted `DraftPackage`
produced by extraction. A hash without retrievable response content is
insufficient. The draft schema must be unable to carry authoritative certificate
results, closure results, base status, or compiler-generated IDs. It may carry
typed evidence requests. A separate trusted binder selects permitted checker
contracts, executes or imports their authenticated results, recomputes local
closures, and materializes the immutable `Package` consumed by
`validate_package`.

Provider adapters, including Ollama, belong outside `pff.model`, `pff.validate`,
`pff.compile`, and `ground`. They may import the generation draft model but not
the validator, compiler, or evaluator. Secrets are supplied through the process
environment and are never package data or repository content.

Replay never calls an LLM provider. It reuses the captured envelope,
extracted draft, and bound evidence. A diagnostic-driven repair or fresh model
call creates a new linked generation attempt; it does not mutate the captured
response or silently replace the prior draft.

A generator may propose user records: atoms, rule alternatives, faces,
contraries, challenges, discharges, exact successor versions, and evidence
requests. It may not author semantic status (`LIVE`, `EXCLUDED`, or `SUSPENDED`),
base membership, registry contracts, certificate or closure outcomes, or any
`__pff__:` record. Those remain code-owned or checker-bound inputs. A downstream
LLM may narrate a structured evaluation, but that narration cannot alter it.

## 3. Admitted and deferred challenge effects

`[N]` The next compiler profile admits only the following effects:

| Challenge kind | Admitted target | Effect while open |
|---|---|---|
| `rebut` | any target kind already admitted by validation | derive the exact `contrary_atom`; do not block the target |
| `undercut` | `FACE` | derive `has-open-challenge(target face)` |
| `wound` | `FACE` | derive `has-open-challenge(target face)`; retain the wound source identity in the effect-rule origin |
| `localisation_gap` | `FACE` of kind `localisation` | derive `has-open-challenge(target face)` |
| `recovery_gap` | `FACE` of kind `recovery` | derive `has-open-challenge(target face)` |
| `closure_gap` | `FACE` of kind `closure` | derive `has-open-challenge(target face)` |

`[D]` The following semantic effects remain unimplemented. `[N]` For this
profile, they fail compilation with the exact diagnostics below before any
ground artifact or status is produced:

| Input | Compilation diagnostic |
|---|---|
| any `revoke` | `REVOCATION_SELECTION_UNSUPPORTED` |
| any `currentness_gap` | `CURRENTNESS_TARGET_UNSUPPORTED` |
| any `defect` | `PROBLEM_FACE_LIFECYCLE_UNSUPPORTED` |
| `undercut` or `wound` targeting a `RULE` | `RULE_TARGET_BLOCKING_UNSUPPORTED` |
| any registry-known extension challenge kind without compiler semantics | `CHALLENGE_EFFECT_UNSUPPORTED` |

Specialised gaps with the wrong target kind or wrong face kind are invalid
packages and therefore never reach compilation.

## 4. Validation freeze

### 4.1 Specialised face binding

`[N]` `ChallengeTargetContract` gains this exact public field:

```python
required_face_kind: str | None = None
```

The constructor accepts only `None` or a nonempty exact `str`. An invalid value
raises `RegistryDefinitionError(INVALID_ID)` at
`challenge_target:<challenge-kind>.required_face_kind`. A non-`None` value
requires `allowed_target_kinds == frozenset({RecordKind.FACE})`; otherwise
construction raises `INCOHERENT_CONTRACT` at the same location.

`PredicateRegistry.challenge_target_contract(challenge_kind)` returns the exact
immutable contract or raises `KeyError`; the existing
`allowed_challenge_target_kinds` method delegates to it. A registry extension
may use `required_face_kind`, but every non-`None` value must occur in that
registry's `known_face_kinds`. An unknown value raises `UNKNOWN_FACE_KIND` at
`registry:<registry-id>.challenge_target_contracts`, with the unknown face kinds
as canonical identifiers.

For the core registry this dimension is not registry-relaxable:

| Challenge kind | Required target kind | Required `FaceRecord.kind` |
|---|---|---|
| `localisation_gap` | `FACE` | `localisation` |
| `recovery_gap` | `FACE` | `recovery` |
| `closure_gap` | `FACE` | `closure` |

A registry may narrow a core target contract but may not widen it, change its
required face kind, or remove the required-face-kind constraint.
Violating this core ceiling raises `INCOHERENT_CONTRACT` at
`registry:<registry-id>.challenge_target_contracts`, identifying the offending
challenge kinds. Registry construction checks unknown required face kinds before
the core-ceiling comparison, so a core contract naming an unknown face kind
raises only `UNKNOWN_FACE_KIND`; it does not also or instead raise
`INCOHERENT_CONTRACT`. A discriminator must change a core specialised contract's
required face kind to one absent from `known_face_kinds` and assert that single
code, location, and identifier tuple.

`[N]` A non-`FACE` specialised target uses the existing
diagnostic exactly as follows:

```text
phase   = BINDINGS
code    = CHALLENGE_TARGET_KIND
path    = challenge[<id>@<version>].target_kind
refs    = (challenge.ref,)
details = ("<challenge.target_kind.value>",)
```

The invalid target is not resolved after this diagnostic, suppressing dependent
reference and face-kind issues.

`[N]` A resolved `FACE` of the wrong face kind produces exactly:

```text
phase   = BINDINGS
code    = CHALLENGE_TARGET_FACE_KIND
path    = challenge[<id>@<version>].target
refs    = tuple(sorted((challenge.ref, face.ref)))
details = ("actual:<face.kind>", "expected:<required-kind>")
```

The issue is emitted only after the target resolves as a `FACE`; unresolved or
wrong-record-kind targets retain their direct reference diagnostic without this
dependent issue.

### 4.2 Effect heads must be derivable

`[C]` A `rebut` challenge's `contrary_atom` is an effect head and therefore must
resolve to a nonprimitive atom. `[N]` After a registry-known `rebut` has a
present `contrary_atom` that resolves to an exact `AtomRecord`, a primitive atom
produces exactly:

```text
phase   = BINDINGS
code    = PRIMITIVE_EFFECT_HEAD
path    = challenge[<id>@<version>].contrary_atom
refs    = tuple(sorted((challenge.ref, contrary_atom.ref)))
details = ()
```

A missing, unresolved, or wrong-record-kind `contrary_atom` retains its existing
direct diagnostic and suppresses this dependent primitive issue.

`[D]` A future `defect` lowering must impose the same requirement on
`problem_face_atom`. The current profile does not add that validation error,
because every otherwise-valid `defect` must instead reach the compiler and
produce its single root deferral diagnostic.

## 5. TypeMatch authority and placement

For each `DischargeRecord d`, let `c` be its exact resolved challenge.

`[S]` The exact registry selected by the validated package and its frozen
compatibility table are the sole compatibility authority:

```text
compatible(d) = source.registry.is_discharge_compatible(
    challenge_kind=c.kind,
    discharge_kind=d.kind,
)
```

`[S]` A known incompatible pair remains valid and its TypeMatch atom is
excluded. `[N]` The generated unary atom `type-match(d)` is placed in `T0` when
compatible and in `F0` when incompatible. It is never placed in protected-open,
omitted, derived by a fact rule, supplied by a provider, or rejected merely
because the known pair is incompatible.

## 6. Exact lowering

Let `cert-valid(x)` and `closure-ready(x)` denote the already-frozen gate atoms.
Let `c` be a challenge and `d` a discharge whose exact `challenge` is `c`.

`[S]` The generic gates are:

```text
challenge-case(c) <- cert-valid(c.certificate)

discharge-case(d) <- cert-valid(d.certificate), type-match(d)

discharged(c) <- discharge-case(d)

open-challenge(c) <- challenge-case(c),
                     closure-ready(c.discharge_closure),
                     not discharged(c)
```

There is one `discharged(c) <- discharge-case(d)` bridge for every discharge
that names `c`. Different discharges are alternatives, not conjuncts.

`[S]` Admitted effects are lowered as follows:

```text
# rebut
source-atom(c.contrary_atom) <- open-challenge(c)

# admitted FACE-target blocking kinds
has-open-challenge(c.target) <- open-challenge(c)
```

The existing face-clearance rule remains the only path from challenge effects
to rule applicability:

```text
clear(f) <- face(f), closure-ready(f.blocker_closure),
            not has-open-challenge(f)
```

No challenge effect writes a truth status directly. A rebut does not block its
target and does not create an explosion rule. If both endpoints of an explicit
contrary relation become live, that is conflict-view input, not a derived-status
collision.

## 7. Generated identities and compiler source map

`[N]` All generated IDs use the existing injective spelling:

```text
__pff__:<role>(<owner.id>@<owner.version>)
```

The exact new role vocabulary is:

| Artifact | Role / ID stem | Primary source owner |
|---|---|---|
| atom | `challenge-case` | challenge `c` |
| atom | `discharged` | challenge `c` |
| atom | `open-challenge` | challenge `c` |
| atom | `type-match` | discharge `d` |
| atom | `discharge-case` | discharge `d` |
| rule | `challenge-case-rule` | challenge `c` |
| rule | `discharge-case-rule` | discharge `d` |
| rule | `discharged-bridge` | discharge `d` |
| rule | `open-challenge-rule` | challenge `c` |
| rule | `rebut-effect` | challenge `c` |
| rule | `face-block-effect` | challenge `c` |

`[N]` Each new `ArtifactOrigin.sources` is exactly the singleton tuple
`(SourceRecord(<owner kind>, <owner ref>),)` shown above; no secondary source is
included.
The immutable discharge already binds its exact challenge, so `type-match(d)` is
unary and discharge-owned. Effect rules are challenge-owned. Existing source
atom origins and the face-owned origin of `has-open-challenge(f)` are not
overwritten or replaced by an effect-rule origin.

These origins are a compiler source map only. They do not replace the
post-evaluation provenance DAG required by the core specification.

## 8. Compiler diagnostics and ordering

`[N]` `CompilationCode` gains these exact public `StrEnum` members and values:

```text
RULE_TARGET_BLOCKING_UNSUPPORTED  = "rule_target_blocking_unsupported"
REVOCATION_SELECTION_UNSUPPORTED  = "revocation_selection_unsupported"
CURRENTNESS_TARGET_UNSUPPORTED    = "currentness_target_unsupported"
PROBLEM_FACE_LIFECYCLE_UNSUPPORTED = "problem_face_lifecycle_unsupported"
CHALLENGE_EFFECT_UNSUPPORTED       = "challenge_effect_unsupported"
```

Each unsupported root challenge produces exactly one `CompilationIssue`:

```text
record_kind = CHALLENGE
ref         = challenge.ref
code        = the first matching code below
```

Classification is kind-first, then target-specific:

1. `revoke` -> `REVOCATION_SELECTION_UNSUPPORTED`
2. `currentness_gap` -> `CURRENTNESS_TARGET_UNSUPPORTED`
3. `defect` -> `PROBLEM_FACE_LIFECYCLE_UNSUPPORTED`
4. registry-known but compiler-unmapped kind ->
   `CHALLENGE_EFFECT_UNSUPPORTED`
5. otherwise admitted blocking kind with a `RULE` target ->
   `RULE_TARGET_BLOCKING_UNSUPPORTED`

A discharge belonging to an unsupported challenge does not produce a second
issue. Issues are sorted by `(challenge.ref.id, challenge.ref.version)`, then by
the explicit code rank:

```text
REVOCATION_SELECTION_UNSUPPORTED
CURRENTNESS_TARGET_UNSUPPORTED
PROBLEM_FACE_LIFECYCLE_UNSUPPORTED
RULE_TARGET_BLOCKING_UNSUPPORTED
CHALLENGE_EFFECT_UNSUPPORTED
```

The code-rank tie is normally unreachable but is frozen for deterministic
aggregation. If any issue exists, `compile_package` raises one
`PackageCompilationError` before builder construction and returns no partial
`Compilation`, `GroundProgram`, origin set, or evaluation status.

A challenge kind absent from the exact selected registry remains an
`UNKNOWN_CHALLENGE_KIND` validation failure. It never becomes a compiler feature
diagnostic.

## 9. Discriminating semantic vectors

These vectors assume an otherwise valid minimal package, a live face, a passed
face blocker closure, a supported `FACE`-target blocking challenge (not a
`rebut`) whose own case is live unless stated, and a user rule guarded only by
that face. The user rule certificate passes, every other positive premise is
live, and this is the only rule case for its head. Unless a row says otherwise,
the challenge discharge closure passes and there are no discharge records naming
the challenge. Each row that names a discharge has exactly one. `L`, `E`, and
`S` mean `LIVE`, `EXCLUDED`, and `SUSPENDED` after ground evaluation.

| Case | challenge-case | discharged | open-challenge | face blocker | clear / guarded head |
|---|---:|---:|---:|---:|---:|
| challenge certificate `pass`, no discharge, discharge closure `pass` | L | E | L | L | E / E |
| challenge certificate `fail` | E | E | E | E | L / L |
| challenge certificate `open` | S | E | S | S | S / S |
| live challenge, discharge closure `fail` | L | E | S | S | S / S |
| live challenge, discharge closure `open` | L | E | S | S | S / S |
| compatible discharge certificate `pass` | L | L | E | E | L / L |
| compatible discharge certificate `fail` | L | E | L | L | E / E |
| compatible discharge certificate `open` | L | S | S | S | S / S |
| incompatible discharge certificate `pass` | L | E | L | L | E / E |
| incompatible discharge certificate `open` | L | E | L | L | E / E |
| challenge certificate `open`, compatible discharge certificate `pass` | S | L | E | E | L / L |

For multiple discharges naming one challenge:

- any live `discharge-case` makes `discharged` live;
- otherwise any suspended `discharge-case` makes `discharged` suspended;
- otherwise `discharged` is excluded.

An isolated nonprimitive rebut head with no other base membership or defining
rule mirrors `open-challenge`: live, excluded, or suspended. The rebut target is
unchanged.

## 10. Gap decisions and rejected readings

| Gap | Decision | Rejected reading | Minimum discriminator |
|---|---|---|---|
| rule-target blocking | `[D]` effect deferred; `[N]` exact failure | silently block every face of the rule, or create an unclosed rule blocker | a faceless rule-target undercut yields exactly one rule-target issue and no compilation |
| revoke selection | `[D]` effect deferred; `[N]` exact failure | guess latest version or scan every `depends_on_version` token | two candidate dependent versions still yield one revoke issue and no selected face |
| currentness target | `[D]` effect deferred; `[N]` exact failure | infer bearer/constructor/mark from strings | otherwise-valid currentness challenge with a registry-admitted `RULE` or `FACE` target yields one currentness issue |
| defect lifecycle | `[D]` effect deferred; `[N]` exact failure | equate `problem_face_atom` with the existing blocker lifecycle | otherwise-valid defect plus discharge yields one defect issue and no dependent discharge issue |
| TypeMatch placement | `[N]` exact T0/F0 | omit mismatch, reject it, or derive it through a provider/fact rule | one otherwise-valid package contains compatible and incompatible discharges; their exact generated TypeMatch atoms occur in T0 and F0 respectively |
| specialised gap face kind | `[N]` validate exact kind | accept any face under the same target kind | with all refs and policies otherwise valid, a registry-allowed resolved wrong-kind face yields only `CHALLENGE_TARGET_FACE_KIND` |
| primitive effect head | `[C]` nonprimitive rule; `[N]` exact diagnostic | allow compiler derivation of a primitive atom | predicate permits primitives, atom has no user derivation, and all other refs are valid; the primitive contrary yields only `PRIMITIVE_EFFECT_HEAD` |
| generated IDs and origins | `[N]` freeze table in section 7 | use iteration indices, omit versions, merge owners, or overwrite source origins | independent literal expected IDs plus collection reversal, unrelated-record insertion, and decorrelated owner/reference versions preserve exact body wiring and singleton origins |

## 11. Explicitly non-dispatchable semantics

Until a later accepted freeze supplies the missing model and laws:

- rule-target blocking cannot succeed without a closure-safe rule blocker
  domain or an explicit synthetic-face construction;
- revoke cannot lower positively without an exact dependent-version selection
  algorithm and its closure boundary;
- currentness cannot lower without typed bearer, constructor, and mark records;
- defect cannot lower without a retained problem diagnosis/open-obligation
  lifecycle tied to its discharge domain;
- the core's illustrative pure Dung cycle cannot be generated from the current
  `ChallengeRecord`, which has no attacker/support premise.

No compiler, registry pack, or LLM prompt may fill these gaps implicitly.

## 12. Bounded implementation plan after acceptance

Acceptance authorizes two separately reviewed tranches:

1. **Admission contracts:** modify only `src/poietics/pff/registry.py`,
   `src/poietics/pff/validate.py`, `tests/test_pff_registry.py`, and
   `tests/test_pff_validate.py`. Add the core face-kind ceiling and the two
   validation diagnostics. Do not compile or evaluate.
2. **Atomic compiler admission:** modify only `src/poietics/pff/compile.py`,
   `tests/test_pff_compile.py`, and `README.md`. Admit generic gates and the
   supported effect matrix as one preflight-safe lowering. Do not change the
   model, ground evaluator, checker execution, provider adapters, or parsers.

Every tranche requires focused tests, the full suite, deterministic
permutation/version fixtures, no-partial-result checks, dependency-boundary
tests, and independent false-green probes before publication.

The provider-neutral generation layer is a later tranche. It should follow the
challenge profile so the LLM's extraction target is stable, and it must depend
on the package model rather than the compiler or evaluator.

## 13. Acceptance record

The user explicitly accepted these three inseparable choice groups on
2026-08-17:

1. the admitted/deferred challenge-effect matrix, one-root diagnostics, and
   precedence;
2. exact specialised-face and primitive-effect validation plus TypeMatch
   placement in `T0`/`F0`;
3. the generated role/ID/origin table and lowering in sections 6–7.

All three groups are now semantic authority subordinate to the core
specification. Section 2 remains a deferred, provisional generator design note
and was not included in this acceptance. Acceptance authorizes the bounded
tranches in section 12; it does not represent those implementation changes as
already completed.
