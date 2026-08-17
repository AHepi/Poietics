# Poietics

Poietics is being built around the narrow waist of the Poietic Faceted
Fixpoint: a typed admission boundary followed by a deterministic well-founded
evaluator over a finite ground program.

The implemented core now includes immutable package candidates, an exact
code-owned predicate registry, deterministic validation, opaque ground atom
references, deterministic certificate and closure gate compilation,
deterministic face clearance and face-guarded rule compilation, generic
challenge and discharge case gates, registry-owned `type-match` placement,
admitted challenge effects, immutable ground rules, initial live and excluded
sets, a protected-open set, and the fixed-point evaluation specified by PFF Core
v0.1. Its statuses are package-relative computational results. They are not
truth, acceptance, support, confidence, or probability judgements.

## Current seam

| Layer | Current responsibility | Explicitly outside the layer |
|---|---|---|
| `poietics.pff.model` | Deeply immutable typed package candidates and exact references | Parsing, registry meaning, semantic status, and compilation |
| `poietics.pff.registry` | Exact immutable predicate, checker-shape, and policy contracts | Provider calls, checker execution, mutable registration, and manifest loading |
| `poietics.pff.local_checkers` | Pure recomputation of explicitly code-owned package-local checker contracts | External evidence, I/O, provider calls, compilation, and evaluation |
| `poietics.pff.validate` | Mint `ValidatedPackage` or raise deterministic typed issues | Repairing proposals, external checker execution, compilation, and evaluation |
| `poietics.pff.compile` | Lower a validated package through certificate, closure, face, and admitted challenge/discharge gates into one `GroundProgram`, retaining contraries and an immutable source map | Checker/provider execution, evaluation, parsing, and deferred challenge effects |
| `poietics.ground.model` | Immutable ground records and typed statuses | Packages, predicates, certificates, faces, and challenges |
| `poietics.ground.evaluate` | One authoritative fixed-point path | Domain interpretation, provenance, replay, and incremental evaluation |
| Future explanation layer | Combine source maps and contraries with an `Evaluation` | Persisting or inventing verdicts |

The dependency direction is intentionally one-way: an upstream producer may
supply untrusted candidate material; at the future generation boundary, a
trusted binder will create the immutable `Package`. Validation binds that
package to one exact registry and mints a `ValidatedPackage`; the compiler
creates a `Compilation` containing a `GroundProgram`; the ground evaluator
derives an `Evaluation`. Rule indexes and statuses are always recomputed and are
never stored as authority.

## Compiler boundary

Compilation reads only an exact `ValidatedPackage`. Every source atom keeps
its exact ID and version. Every certificate, closure, and rule case receives a
reserved, version-bearing generated identity that is independent of collection
order; challenge and discharge artifacts use the same owner-and-version identity
rule. The result carries an immutable source map for later explanation and a
separate normalized contrary relation; contraries are never converted into
blocking rules or explosion.

The current compiler implements the complete pass/fail/open tables for
certificate and closure gates, exact source-base transfer, closure-guarded
default negation, face clearance, independent face-guarded rule cases, and the
accepted generic challenge/discharge lifecycle. For every discharge,
compatibility comes only from the package's exact registry: `type-match` is
initially live for a compatible pair and excluded for a known incompatible
pair. Incompatible pairs remain valid package data, and separate discharges are
alternative bridges rather than conjunctive requirements.

An open `rebut` derives its exact nonprimitive contrary atom without blocking
its target. Face-target `undercut`, `wound`, `localisation_gap`, `recovery_gap`,
and `closure_gap` challenges derive the existing face-owned
`has-open-challenge` atom. These effects are ground rules, not direct status
assignments; face clearance remains the only path from a blocking challenge to
rule applicability.

Compilation still fails closed before constructing any ground artifact for an
unsupported root challenge. Any `revoke`, `currentness_gap`, or `defect` is
deferred, as are rule-target `undercut` and `wound` and registry-known extension
challenge kinds without compiler semantics. These produce one challenge-rooted
typed issue and no partial `Compilation`, `GroundProgram`, source map, or
evaluation status; the compiler never silently ignores or guesses an effect.

| Deferred challenge input | `CompilationCode` |
|---|---|
| `revoke` | `REVOCATION_SELECTION_UNSUPPORTED` |
| `currentness_gap` | `CURRENTNESS_TARGET_UNSUPPORTED` |
| `defect` | `PROBLEM_FACE_LIFECYCLE_UNSUPPORTED` |
| Rule-target `undercut` or `wound` | `RULE_TARGET_BLOCKING_UNSUPPORTED` |
| Registry-known kind without compiler semantics | `CHALLENGE_EFFECT_UNSUPPORTED` |

## Package-validation boundary

Validation aggregates issues in a stable order and returns no partial
capability on failure. Exact references are represented structurally as an ID
and positive version; textual `id@version` parsing and canonical bytes remain a
later boundary. Distinct versions may coexist, and validation never selects a
"latest" record.

Registry policies own argument, frame, grade, contrary, checker-shape, face,
and challenge vocabulary. They are immutable local data and deterministic
methods rather than callbacks. Validation checks declared checker bindings and
typed payload fields, resolves reference-valued evidence, and binds closure
selector fields and frames through those contracts. Blocker and discharge
closures retain their exact owner scope, and registries cannot redefine the
v0.1 target ceiling or the exact face kinds required by `localisation_gap`,
`recovery_gap`, and `closure_gap`. A registry-known `rebut` effect head must be
a resolved nonprimitive atom; the analogous `defect` lifecycle remains
deferred. Validation does not execute external checkers. It does recompute the
code-owned `materialised-selector/v1` contract from the immutable package, so
exact membership yields `pass`, a mismatch yields `fail`, and an unsupported
selector yields `open`. Other bound `fail` and `open` checker results remain
supplied semantic data.

Two underspecified source shapes are isolated rather than guessed. Contrary
records carry IDs and versions because the specification's universal semantic
record identity rule requires them, even though its contrary example omits
them. A face's `depends_on_version` is an optional opaque `VersionToken`, not a
package record reference, because the example points outside the declared
package record kinds.

## Generator placement

The intended conjecture generator for this system is an LLM, but the exact
provider-neutral generation protocol remains a future, provisional layer. It
sits above the semantic core and emits untrusted draft records and typed
evidence requests. A separate trusted binder materializes the immutable
`Package`; an LLM adapter cannot directly author an authoritative package or
call validation as though its output were trusted.

| Stage | Contract |
|---|---|
| Future provider-neutral adapter | Ask an LLM for candidate atoms, rule alternatives, faces, contraries, challenges, discharges, exact successor versions, or revisions in an untrusted draft |
| Capture and extraction boundary | Retain the prompt, model identity, parameters, raw response bytes or an immutable retrievable reference plus hash, and the extracted draft before semantic use |
| Trusted evidence binder | Select permitted checker contracts, import or execute authenticated evidence, recompute local closures, and materialize the immutable `Package` |
| Package validator | Reject malformed, unresolved, unknown, or type-invalid bound packages without assigning semantic status |
| Compiler and ground evaluator | Lower valid candidates and derive the complete partition through the one deterministic engine path |
| Discernment loop | Return typed blockers and open dependencies to the controller as context for a later LLM generation turn |

The draft cannot carry authoritative base membership, registry contracts,
certificate or closure outcomes, semantic status, or compiler-generated
`__pff__:` records. Replay consumes captured inputs and bound evidence without
calling an LLM. A repair or fresh model call creates a new linked generation
attempt rather than mutating the captured response or prior draft. External
checkers remain separate: they supply typed evidence results, while the LLM
supplies conjectural variation.

## Verification

From a clean checkout, the focused milestone check is:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Remaining semantic freezes include closure-safe rule-target blocking, exact
revocation selection, typed currentness targets, the retained defect/problem
lifecycle, and compiler semantics for registry extension kinds. The provisional
generator/provider protocol, canonical package bytes, explanation, replay, CLI,
and empirical-pack work remain separate later milestones.
