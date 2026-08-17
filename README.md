# Poietics

Poietics is being built around the narrow waist of the Poietic Faceted
Fixpoint: a typed admission boundary followed by a deterministic well-founded
evaluator over a finite ground program.

The implemented core now includes immutable package candidates, an exact
code-owned predicate registry, deterministic validation, opaque ground atom
references, deterministic certificate and closure gate compilation,
deterministic face clearance and face-guarded rule compilation, immutable ground
rules, initial live and excluded sets, a protected-open set, and the fixed-point
evaluation specified by PFF Core v0.1. Its statuses are package-relative
computational results. They are not truth, acceptance, support, confidence, or
probability judgements.

## Current seam

| Layer | Current responsibility | Explicitly outside the layer |
|---|---|---|
| `poietics.pff.model` | Deeply immutable typed package candidates and exact references | Parsing, registry meaning, semantic status, and compilation |
| `poietics.pff.registry` | Exact immutable predicate, checker-shape, and policy contracts | Provider calls, checker execution, mutable registration, and manifest loading |
| `poietics.pff.local_checkers` | Pure recomputation of explicitly code-owned package-local checker contracts | External evidence, I/O, provider calls, compilation, and evaluation |
| `poietics.pff.validate` | Mint `ValidatedPackage` or raise deterministic typed issues | Repairing proposals, external checker execution, compilation, and evaluation |
| `poietics.pff.compile` | Lower a validated package through certificate, closure, and face gates into one `GroundProgram`, retaining contraries and an immutable source map | Checker/provider execution, evaluation, parsing, and pending challenge/discharge lowering |
| `poietics.ground.model` | Immutable ground records and typed statuses | Packages, predicates, certificates, faces, and challenges |
| `poietics.ground.evaluate` | One authoritative fixed-point path | Domain interpretation, provenance, replay, and incremental evaluation |
| Future explanation layer | Combine source maps and contraries with an `Evaluation` | Persisting or inventing verdicts |

The dependency direction is intentionally one-way: a generator or other
producer creates a `Package`; validation binds it to one exact registry and
mints a `ValidatedPackage`; the compiler creates a `Compilation` containing a
`GroundProgram`; the ground evaluator derives an `Evaluation`. Rule indexes
and statuses are always recomputed and are never stored as authority.

## Compiler boundary

Compilation reads only an exact `ValidatedPackage`. Every source atom keeps
its exact ID and version. Every certificate, closure, and rule case receives a
reserved, version-bearing generated identity that is independent of collection
order. The result carries an immutable source map for later explanation and a
separate normalized contrary relation; contraries are never converted into
blocking rules or explosion.

The current compiler milestone implements the complete pass/fail/open tables
for certificate and closure gates, exact source-base transfer, closure-guarded
default negation, face clearance, and independent face-guarded rule cases. In
particular, a failed closure protects `closure-ready` as open rather than
excluding it, so a failed closure cannot establish absence. A face is live
after validation, while its clearance depends on its blocker closure and the
absence of an open challenge in that closed domain.

Validated packages containing challenges or discharges receive deterministic
typed compilation issues and no partial result. That fail-closed boundary is
intentional: PFF Core v0.1 permits blocking challenges to target a rule but
does not define the closure-guarded rule-case effect, and it does not define
how a revoke selects exact dependent-version faces. Those semantics must be
frozen before challenge effects are lowered; the records are never silently
ignored or guessed.

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
v0.1 rule that blocking challenges target rules or faces. Validation does not
execute external checkers. It does recompute the code-owned
`materialised-selector/v1` contract from the immutable package, so exact
membership yields `pass`, a mismatch yields `fail`, and an unsupported selector
yields `open`. Other bound `fail` and `open` checker results remain supplied
semantic data.

Two underspecified source shapes are isolated rather than guessed. Contrary
records carry IDs and versions because the specification's universal semantic
record identity rule requires them, even though its contrary example omits
them. A face's `depends_on_version` is an optional opaque `VersionToken`, not a
package record reference, because the example points outside the declared
package record kinds.

## Generator placement

The conjecture generator for this system is an LLM. It sits above the semantic
core and proposes typed candidate records; it is not part of fixed-point
evaluation and cannot assign `LIVE`, `EXCLUDED`, or `SUSPENDED` itself.

| Stage | Contract |
|---|---|
| Future `poietics.generation` adapter | Ask an LLM for candidate atoms, rule cases, challenges, discharges, or revisions in a provider-neutral proposal envelope |
| Controller and event record | Capture the prompt, raw response, model identity, generation parameters, and proposal before any semantic use |
| Package validator | Reject malformed, unresolved, unknown, or type-invalid proposals without assigning semantic status |
| Compiler and ground evaluator | Lower valid candidates and derive the complete partition through the one deterministic engine path |
| Discernment loop | Return typed blockers and open dependencies to the controller as context for a later LLM generation turn |

Replay will consume the captured proposal. It will never silently call the LLM
again, because nondeterministic generation is an input to the semantics rather
than part of the semantics. External checkers remain separate: they supply
typed evidence results, while the LLM supplies conjectural variation.

## Verification

From a clean checkout, the focused milestone check is:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

The next bounded milestone is a semantic freeze for rule-target blockers and
revocation selection, followed by challenge and discharge compilation through
the existing compiler path. Generator/provider adapters, canonical package
bytes, explanation, replay, CLI, and empirical-pack work remain separate later
milestones.
