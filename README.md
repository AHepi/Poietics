# Poietics

Poietics is beginning with the narrowest executable layer of the Poietic
Faceted Fixpoint: a deterministic well-founded evaluator over a finite ground
program.

This first tranche deliberately implements only opaque atom references,
immutable ground rules, initial live and excluded sets, a protected-open set,
and the fixed-point evaluation specified by PFF Core v0.1. Its statuses are
package-relative computational results. They are not truth, acceptance,
support, confidence, or probability judgements.

## Current seam

| Layer | Current responsibility | Explicitly outside the layer |
|---|---|---|
| `poietics.ground.model` | Immutable ground records and typed statuses | Packages, predicates, certificates, faces, and challenges |
| `poietics.ground.evaluate` | One authoritative fixed-point path | Domain interpretation, provenance, replay, and incremental evaluation |
| Future compiler | Lower typed PFF packages to `GroundProgram` | Changing evaluator semantics |
| Future explanation layer | Combine source maps and contraries with an `Evaluation` | Persisting or inventing verdicts |

The dependency direction is intentionally one-way: future registries and
predicate packs feed a compiler; the compiler creates a `GroundProgram`; the
ground evaluator derives an `Evaluation`. Rule indexes and statuses are always
recomputed and are never stored as authority.

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

The next bounded milestone is package validation and the code-owned predicate
registry. Compiler, challenge, explanation, replay, CLI, and empirical-pack
work remain separate later milestones.
