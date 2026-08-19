# PFF Draft-Binding Mutation Qualification Profile v0.2

Status: ACCEPTED CONFORMANCE PROFILE

This candidate supersedes only the execution-envelope persistence boundary of
the accepted PFF Draft-Binding Mutation Qualification Profile v0.1. It does
not change a binder value, gate, diagnostic, ordering rule, fixture outcome,
mutation recipe, classification, child protocol, command specification, final
evidence meaning, or public API. The accepted semantic authority remains
`docs/PFF_DRAFT_BINDING_PROFILE_V0.1.md`; the accepted v0.1 qualification
profile remains immutable authority until this candidate is independently
reviewed, explicitly accepted, and published.

## 1. Subject and authority

The repository and branch are discovery locators only. They are not immutable
authority and do not enter identity comparisons. The exact implementation
subject is the commit, tree, and profile blob:

```text
locator_repository: https://github.com/AHepi/Poietics
locator_branch: main
commit: 15e61728eec90c45ca644f804e14f4d54dc31e38
git_tree: de7d6e8810b3ae349887035248c5328fe624e020
subject_profile_path: docs/PFF_DRAFT_BINDING_PROFILE_V0.1.md
subject_profile_sha256: sha256:139fc92efb03bf1c72c20e4aec5e2556d2799bf77fdd6de165ac2da2b558ce41
subject_profile_reviewed_candidate_sha256: sha256:8c347531cb217d9a8b66b71db7a7906594b70f30e949e0f52ad4cf36507b9b7b
```

The exact companion recipe authority is
`docs/PFF_DRAFT_BINDING_MUTATION_MANIFEST_V0.1.json`. Its SHA-256 is inserted
in this section before candidate review and is part of the reviewed candidate
bytes:

```text
recipe_manifest_sha256: sha256:2e967a8a37e90ea63928239040d852225620a42d391951f75ee02f20dea325e2
```

### 1.1 Supersession record and authority boundary

The superseded accepted authority and its publication identity are exact:

```text
superseded_profile_path: docs/PFF_DRAFT_BINDING_MUTATION_QUALIFICATION_PROFILE_V0.1.md
superseded_profile_sha256: sha256:0e2ca55cb31ef815f2674723d152ff1856057f25c0fcbace88d0810569ab959d
superseded_authority_commit: 053855c45abd9130557515df725c14af0b43cf41
superseded_authority_tree: ca7ba5a43125cd04a3cbb57da7ca4416d0f6adf2
preserved_manifest_path: docs/PFF_DRAFT_BINDING_MUTATION_MANIFEST_V0.1.json
preserved_manifest_sha256: sha256:2e967a8a37e90ea63928239040d852225620a42d391951f75ee02f20dea325e2
```

The challenged boundary is only v0.1 section 9's requirement to atomically
rewrite the complete ACTIVE `<ENVELOPE>` after every newly retained direct
child observation. On the full qualification path, and only when
`constructed_M = M` and `dispatched_O = O`, the exact v0.1 publication
equation is one initial ACTIVE publication, plus 571 observation-triggered
complete-envelope rewrites, plus one terminal COMPLETE publication, for 573
complete-envelope publications. Under that condition, the 571 observations
are the pairwise-disjoint typed populations 181 archive/GIT construction
rows, 181 import-probe rows, 205 component-leaf rows, and four post-attempt
identity Git rows:

```text
571 = 181 + 181 + 205 + 4
573 = 1 + 571 + 1
```

The reported semantic-challenge measurements are stdout byte length
371,682,282 for clean F87 and 376,620,048 for clean F89. The three reported
heavy mutant rows, again only when `constructed_M = M` and `dispatched_O = O`,
have one-based positions 346 for M108/F87, 349 for M109/F87, and 396 for
M124/F89 among the 571 post-creation observation-triggered publications. Under
that same condition, a clean control is present in the initial publication,
every observation-triggered rewrite, and terminal publication, so each clean
row has multiplicity 573. A mutant row at position `p` is present in
publications `p` through 571 and in the terminal publication, so the three
mutant multiplicities are respectively:
`571 - 346 + 1 + 1 = 227`, `571 - 349 + 1 + 1 = 224`, and
`571 - 396 + 1 + 1 = 177`.

Because section 9's raw stdout representation uses two hexadecimal ASCII
bytes for every stdout byte, excluding every key, wrapper, delimiter, other
stream, and all fixed envelope bytes gives this exact conditional lower bound
over only the five reported heavy executions:

```text
2 * [371,682,282 * (573 + 227 + 224) + 376,620,048 * (573 + 177)]
= 1,326,135,385,536 bytes
```

The two stdout lengths, the qualification host's reported ext2/ext3 and
non-reflink characterization, and the reported history of zero controlled
attempts are semantic-challenge provenance that is **UNVERIFIED** by the
sealed normative inputs. They are not conformance criteria, and this candidate
does not promote them, a host measurement, or an attempt-history assertion to
authority. The supersession does not depend on doing so: v0.1 normatively
requires repeated publication of the entire growing prefix, and the equation
above states the resulting write amplification conditional on the reported
lengths. Replacing that repeated full-prefix rule with linear append and one
terminal projection is a normative realizability repair, not evidence of an
implementation defect.

The defect invalidates any claim that a v0.1 runner implementing repeated
whole-envelope rewrites is ready for controlled execution, any review or
qualification conclusion over that persistence mechanism, and any projected
v0.1 execution-envelope bytes. It preserves byte-for-byte the subject binding
profile, the companion manifest, every finite F/C/L/M/O population and
expected component vector, all mutation recipes and content roots, all clean
control and implementation evidence unrelated to envelope persistence, and
any independently authenticated attempt ledger without claiming that one is
present in this candidate package. The reported `0/181` history remains
unverified provenance. Implementation may resume only after this v0.2
candidate is independently reviewed, explicitly accepted, published without
altering v0.1 or the manifest, and all affected runner/tests/review criteria
are re-derived from its published bytes.

Rule provenance for this candidate is closed. `[S]` denotes byte-for-byte or
semantic restatement of the accepted v0.1 authority. `[N]` denotes the new
append-only ACTIVE log, its chain and recovery rules, COMPLETE-envelope
assembly, dependent joins/tests/lifecycle clauses, and v0.2 acceptance and
publication topology. There are no `[C]` clarifications and no `[D]`
deferrals. Every clause outside the expressly replaced persistence boundary is
`[S]`; every clause marked `[N]` below is confined to that boundary.

The subject profile freezes `F00-F105`, `C00-C82`, `M01-M181`, every
forbidden transformation, every required-killer cell, the exact aggregate result,
and the evidence fields. This profile supplies only the previously missing
code-specific recipes, leaf dispatch, execution controls, classification
precedence, and evidence serialization.

Authority precedence is exact: the accepted subject profile controls every
binder semantic and F/C/M row; this qualification profile controls only
execution and qualification interpretation; the companion manifest may only
instantiate the recipes and leaf identities frozen by those two profiles. A
conflict at either lower layer invalidates the pair before acceptance or stops
preflight after acceptance. No lower layer silently overrides a higher one.

The repository's active `HEAD` after acceptance and tool implementation is not
the subject. From cwd `<REPO>`, the runner authenticates with exact commands
`<GIT> cat-file -e <commit>^{commit}`, `<GIT> rev-parse <commit>^{tree}`, and
`<GIT> ls-tree -rz --full-tree <commit>`. Their exact successful outputs are,
respectively, empty bytes, the named tree plus LF, and the NUL-delimited tree
records consumed below; stderr is empty and exit is zero. The profile blob
extracted from the archive must have the named SHA-256. For each declared fresh
root it runs exact command `<GIT> -c tar.umask=0022 archive --format=tar
--output=<ARCHIVE> <commit>` from `<REPO>` and extracts
the authenticated tree, not the commit object. Every contextual `<ARCHIVE>`
actual path is `<TMP>/archives/archive-` plus 32 fresh lowercase hexadecimal
digits and `.tar`, and therefore discloses no control or mutation identity to
Git; the execution envelope binds that opaque actual path to its logical role
and context. Archive paths are pairwise distinct, their parent exists, and each
output is absent.
The `ls-tree` result must declare
exactly 41 blob paths, each Git mode `100644`; the tar must carry exactly those
41 regular paths at mode `0644` plus the eight derived parent directory entries
`docs/`, `src/`, `src/poietics/`, its four package directories, and `tests/`,
each at mode `0755`. Extraction rejects a duplicate path, absolute path, `..`
component, symlink, hard link, device, FIFO, socket, unexpected mode, missing
path, or extra path before writing a disposable marker. After extraction and
before use, the runner recomputes each regular member's exact SHA-1 Git blob ID
from its bytes and requires equality with the corresponding `ls-tree` object;
local export attributes can therefore only cause a deterministic pre-attempt
failure, never a silently changed subject.
If any subject identity differs, qualification stops before a disposable copy
or controlled attempt is created. A later binder implementation requires a new
version of this profile and manifest; recipes must never float across trees.

## 2. Closed populations and equations

The controlling populations are:

```text
F = {F00, ..., F105}                         |F| = 106
C = {C00, ..., C82}                          |C| = 83
M = {M01, ..., M181}                         |M| = 181
L70 = {
  (C70, "empty subcase", 1),
  (C70, "wrong-member subcase", 2)
}                                             |L70| = 2
L = {(f, null, null) for f in F union C} union L70  |L| = 191
```

One subject-profile `Required killer` cell defines one composite killer program
for its mutation. Slash-separated tokens are that program's ordered component
fixtures; they are not claims that every component must independently fail.
This distinction is observable: for M50, F59 remains `PASS` while F60 detects
the forbidden retained evidence order. `C70 empty subcase` and `C70
wrong-member subcase` are distinct qualified components and must not collapse
to the aggregate C70 fixture. The companion manifest retains every component
and freezes its a-priori expected disposition before execution.

Qualification proves exact typed equality: set equality for `L` and `M`, and
sequence equality for `O`; counts alone are insufficient:

```text
defined_L = manifest_L = implemented_L = controlled_L = executed_control_L
defined_M = recipe_M = planned_M = attempted_M = classified_M
defined_O = manifest_O = planned_O = classified_O
```

`O` is the ordered sequence of composite-killer component identities
`(mutant_id, killer_ordinal, fixture, qualifier)`, produced by taking `M` in
numeric order and each row's killers in displayed left-to-right order with
one-based `killer_ordinal`. Its exact cardinality is 205: 159 mutants have one
component, 20 have two, and 2 have three. Sequence equality preserves repeated
fixture references across mutants. Every component has an expected disposition
of `PASS` or `MISMATCH`; each mutant has at least one `MISMATCH`. A mismatch
also freezes its exact semantic observable and mismatch kind. These expected
vectors are criteria, not observations, and are independently reviewed before
any mutant runs. The runner recomputes all populations independently from the
subject profile and companion manifest. No unregistered supplemental mutant or
killer can contribute to the result.

`constructed_M` is the subset whose recipe construction completes and
`dispatched_O` is exactly the O projection whose mutant belongs to
`constructed_M`. Components of a construction-failed mutant are not dispatched
but receive synthetic `INFRASTRUCTURE` component classes, so classified O still
closes. A `QUALIFIED` bundle additionally requires `constructed_M = M` and
`dispatched_O = O`; a `NONQUALIFYING` bundle records the exact subsets, which
remain equal to the full populations unless construction failed.

## 3. Companion manifest contract

The companion file is UTF-8 JSON with one final LF, no byte-order mark,
duplicate object keys forbidden, and exact schema
`pff-draft-binding-mutation-manifest/0.1`. Every object key is an ASCII string
and keys are emitted in increasing unsigned ASCII-byte order. Arrays retain
their declared order. There is no whitespace outside strings except the final
LF. Names and string values use double quotes; exact `"`, `\\`, backspace, tab,
LF, form feed, and carriage return escape respectively as `\"`, `\\`, `\b`,
`\t`, `\n`, `\f`, and `\r`; other U+0000-U+001F scalars use lowercase
`\u00xx`; solidus and every scalar above U+001F remain unescaped UTF-8.
Integers are nonnegative minimal base-ten digits with no sign or leading zero,
except exact zero. The only other tokens are lowercase `true`, `false`, and
`null`. Floats are forbidden. These rules define canonical JSON for this
profile.

The top-level object has exactly:

```text
schema
subject
leaves
mutations
```

`subject` has exactly `commit`, `git_tree`, `profile_path`, and
`profile_sha256`, equal to section 1.

The subject-profile table extractor operates on exact UTF-8 lines within exact
section `### 11.4 Behavioural fixture population F` for F, exact section
`### 11.5 Constructor population C` for C, and exact section
`## 12. Atomic mutation manifest` for M; each range ends at the next Markdown
heading of equal or higher rank. A fixture ID matches exact ASCII
`F(?:0[0-9]|[1-9][0-9]|10[0-5])` or
`C(?:0[0-9]|[1-7][0-9]|8[0-2])`; a mutation ID matches exact ASCII
`M(?:0[1-9]|[1-9][0-9]|1[0-7][0-9]|18[01])`. A row is one LF-terminated line
with exact prefix `| <ID> | ` and suffix ` |\n`. The ID is the bytes between
the first `| ` and next ` | `. For fixtures, `authority_text` is the exact byte
substring after that separator through the bytes immediately before the final
` |\n`. For mutations, `transformation` and the killer cell are the analogous
second and third substrings. Extraction requires exactly 106 F, 83 C, and 181
M unique rows in numeric order. Backticks, backslashes, spaces, punctuation,
and Unicode are ordinary retained data; no Markdown decoding occurs. Slash
divides killer tokens only in the killer cell. A token matches exact ASCII
`([FC][0-9]+)( SPACE qualifier)?`; only the two displayed C70 qualifiers are
permitted.

`leaves` is an array in exact order `F00-F105`, `C00-C82`, then the two `L70`
members in section-2 order. Every object has exactly `fixture`, `qualifier`,
`subcase_ordinal`, `authority_text`, `authority_text_sha256`, `captures`, and
`selectors`.
The first 189 rows have null qualifier and ordinal. The final two have the exact
L70 values.
`authority_text_sha256` is exact `sha256:` plus lowercase SHA-256 over the UTF-8
bytes of `authority_text` with no LF.

`captures` is the complete accepted-operation capture registry for that leaf,
in exact displayed fixture order. A capture has exactly `capture`, `kind`,
`symbol`, `case_path`, and `occurrence`. `capture` is a unique leaf-local ASCII
identifier matching `[a-z][a-z0-9-]{0,63}`. `kind` is `CALL`, `TRACE`, or
`STATIC`. A CALL `symbol` is the exact fully qualified subject or fixture
callable named by `authority_text`, including its displayed built-in/operator
operation. A TRACE or STATIC `symbol` is one of the closed tokens and payload
schemas in section 5. Every symbol is ASCII and may not name the adapter or
mutation tool. `case_path` is a nonempty array
of positive one-based ordinals through every displayed batch nesting level;
an unbatched operation uses `[1]`. `occurrence` is the positive adapter-issued
occurrence for the same kind/symbol/case, excluding internal production calls.
The tuple `(kind,symbol,case_path,occurrence)` is unique. A capture records
`RETURN` plus the complete returned value, `RAISE` plus the complete exception,
`VALUE` plus the complete trace/static value, or `NOT_REACHED` plus no value.

`selectors` is a nonempty ordered array of objects with exactly `selector`,
`domain`, and `program`. `selector` is unique within the leaf and matches the
observable grammar below; `domain` is `VALUE`, `TRACE`, or `STATIC`; and
`program` is the closed projection bytecode below. For each leaf, take the
distinct nonnull `observable` strings from aligned `expected_components` with
that exact fixture/qualifier, after the semantic-alias rules below, retaining
first occurrence in numeric-M then killer-ordinal order. Its domain is the
component's exact `TRACE` or `STATIC` kind, otherwise `VALUE`; a repeated
selector with a conflicting domain or program is invalid. Append exact object
whose selector is `<fixture>/complete-outcome`, domain is `VALUE`, and program
is `[["load-complete"]]`. The last selector is present even when no mutation
references another selector. Across all leaves there are exactly 191 named
projection selectors plus 191 final complete-outcome selectors. This array is
the normative position registry for the leaf's complete observation
transcript; a free-form runtime label is never a selector.

A projection program is a nonempty array of instruction arrays. The closed
instructions and exact arities are:

```text
["load-termination", <capture>]
["load-return", <capture>]
["load-exception", <capture>]
["load-exception-class", <capture>]
["load-value", <capture>]
["field", <declared-name>]
["index", <nonnegative-integer>]
["key", <canonical-typed-key>]
["length"]
["contains", <canonical-typed-scalar>]
["not"]
["tuple", <positive-integer>]
["load-complete"]
```

The five `load-*` capture instructions select respectively the exact
termination tag, returned value, exception, exception-class string, or
trace/static value for the named capture. `load-exception-class` produces the
exact ASCII string `type(exception).__module__ + "." +
type(exception).__qualname__`, never a Python class object. Compatibility with
the actual capture termination is interpreted by section 5. `field` is structural access only to a declared dataclass or
named-tuple field, `BaseException.args`, or a declared public exception
attribute; it never invokes a descriptor or property. `index` and `key` access
an exact sequence or mapping member. `length`, `contains`, and `not` are the
only reducers. Each capture load pushes one value. `field`, `index`, `key`,
`length`, `contains`, and `not` each pop one and push one. `tuple` pops its
stated number of values and pushes one tuple in their original push order;
underflow, a wrong exact operand type, or a final stack depth other than one is
a projection error. Multiple capture loads are permitted and are evaluated
left-to-right; every loaded capture must have the selector's domain (`CALL`
maps to `VALUE`). `load-complete` is valid only as the sole
instruction of the final selector and produces the capture-order tuple of raw
`(capture-id string, termination string, raw payload or None)` values. Every other program
begins with a capture load, type-checks against the clean captures, and ends
with exactly one value. Branches, loops,
dynamic lookup, arbitrary calls, mutation identity, and expected-status input
are impossible.

`key` and `contains` literals are complete canonical typed-value objects under
section 5. `key` compares those canonical bytes with the encoded keys of an
exact `dict`, `mappingproxy`, or `_FrozenMapping` and requires exactly one match; it never invokes
hashing or `__getitem__`. `contains` compares the literal's canonical bytes
with encoded members of an exact tuple, list, set, or frozenset, or encoded keys
of an exact mapping, and never invokes `__contains__`. `length` accepts only
those exact containers plus exact `str` or `bytes`; `index` accepts only exact
tuple, list, `str`, or `bytes`; and `not` accepts exact `bool`. `field` reads a
declared dataclass field with `object.__getattribute__`, a named-tuple field by
its declared positional index, `BaseException.args`, or an explicitly declared
public exception attribute. No instruction invokes a user-defined protocol.

Two distinct selector IDs whose capture-resolved canonical programs are
byte-identical invalidate the manifest; they must use one canonical selector.
A nonfinal selector program may not be a structural ancestor of another
selector program in the same leaf: projections are atomic siblings, so a
detail-only change cannot trigger an earlier whole-container selector. The
three mandatory additional aliases are M71=M113 at C14 uppercase policy H slot
1, M87=M138 at C57 Cartesian position 2, and M49=M152 at F05's first
pre-planning reverse-policy canonical-tuple projection. Existing identical
labels remain aliases. F98 M169 and F102 M173 project `issues[0].code`; F98
M170 and F102 M174 project `issues[0].details`. M128 selects C78 case 1, and
M58/C29 selects its retained same-ID/wrong-version subcase. The complete
capture/program registry is criteria and passes independent review before any
leaf adapter exists or any controlled attempt runs.

`mutations` is an array of 181 objects in numeric `M01-M181` order. Each
mutation object has exactly:

```text
id
transformation
killers
expected_components
patches
mutant_content_root
```

`id` and `transformation` equal the literal subject-profile table substrings
defined above. `killers` is a nonempty array retaining displayed order. An
ordinary killer is exactly `{"fixture":"F01","qualifier":null}`. A qualified
subcase retains its qualifier separately, for example
`{"fixture":"C70","qualifier":"empty subcase"}`.

`expected_components` has the same nonempty length and exact
fixture/qualifier sequence as `killers`. Every object has exactly:

```text
fixture
qualifier
disposition
observable
mismatch_kind
exception_class
```

`disposition` is `PASS` or `MISMATCH`. A `PASS` component has null
`observable`, `mismatch_kind`, and `exception_class`. A `MISMATCH` component
has an ASCII observable matching
`[FC][0-9]{2,3}/[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)*`, a `mismatch_kind` from
`VALUE`, `NOT_RAISED`, `RAISED`, `TRACE`, or `STATIC`, and an
`exception_class` that is null except for `RAISED`. For `RAISED`, the class is
an exact ASCII subject or built-in `module.qualname`. The observable's prefix
before and including the first slash must equal the component's exact fixture
plus slash. Every mutation has at
least one `MISMATCH` component. The vector states the exact outcome predicted
from the accepted fixture and recipe before execution; observed output may
never rewrite it.

`patches` is a nonempty ordered array. Every patch has exactly:

```text
path
before_file_sha256
after_file_sha256
operation
old
new
occurrences
```

`operation` is exact string `replace_exact_utf8`. `path` must be one of:

```text
src/poietics/binding/__init__.py
src/poietics/binding/model.py
src/poietics/binding/plan.py
src/poietics/binding/finalize.py
```

`old` is a nonempty exact source substring, `new` is an exact replacement
substring and may be empty, and `occurrences` is a positive integer exactly
equal to the complete non-overlapping left-to-right count found immediately
before that ordered patch is applied. The interpreter rejects zero, fewer, or
extra occurrences and replaces every occurrence from left to right.
`before_file_sha256` and `after_file_sha256` use exact `sha256:` plus 64
lowercase hexadecimal digits and bind respectively the immediate whole-file
state before and after that one ordered patch. Multiple patches are permitted only when
they jointly implement the one displayed semantic mechanism. Applying every
patch to a fresh subject copy must reproduce every declared
`after_file_sha256`.

After all patches for one M row, static source compilation visits the four
allowed binding paths in raw UTF-8 path order, strictly decodes each complete
file as UTF-8, and calls
`compile(source_text, logical_repo_path, "exec", flags=0,
dont_inherit=True, optimize=0)`. It discards the code object, writes no
bytecode, and imports or executes nothing. A decode or compile exception fixes
the row's `RECIPE_INVALID` source location.

The manifest generation review proves for each row that the complete diff is a
faithful representative of the displayed forbidden transformation, no
unrelated product mechanism changes, and all non-target tracked bytes remain
equal to the subject tree.

`mutant_content_root` is `sha256:` plus the lowercase SHA-256 of the following
preimage. Enumerate the exact Git-tracked subject paths in raw UTF-8 lexical
order. For each path append `UTF8(path)`, one NUL byte, the lowercase hexadecimal
SHA-256 of that mutant file's exact bytes, and one LF. No disposable marker,
cache, evidence file, or untracked file enters this preimage.

## 4. Required code-specific recipe choices

The manifest resolves every prose choice against the exact subject. The
following high-risk choices are mandatory and independently reviewed:

| Mutant | Frozen interpretation |
|---|---|
| M01 | admit exact `DraftPackage` at the public boundary; C00's target is the exact boundary outcome, so any later result or exception is retained as the target observation rather than relabeled as setup |
| M20 | on exact lookup failure, select the last member of the catalog's existing canonical registry-ID order as the forbidden fallback |
| M32/M33 | synthesize one evidence outcome only after the missing-set check, using the already planned task and route; all unrelated attestation fields are fixed fixture constants |
| M39 | call the resolved `CheckerContract.accepts_details` on every submitted detail mapping before certificate or `BoundPackage` construction |
| M44 | insert every mapped draft atom, and no other record, into `base.live` |
| M45 | use exact header metadata key `question` and the first exact request question in the extracted draft's retained order |
| M48 | call `generate_ollama(source.source, transport=lambda _: None)` during planning; the wrong request type may fail inside that forbidden call, but argument evaluation must reach the call boundary |
| M49 | retain submitted policy tuples without adding planner compensation |
| M58/C29 | compile C29 as two retained subcases: `target_for(ATOM, DraftRef("absent",1))` and same-ID/wrong-version `target_for(ATOM, DraftRef("atom:generated",6))`; both controls raise `KeyError`, while M58 makes the latter `NOT_RAISED` |
| M60/M61 | C07/C09 call the exact zero-argument constructors; C08 calls `BindingPlan` with keyword values for every declared public and private dataclass field copied from one valid plan, and C10 calls `BoundPackage` with keyword values for all four declared fields copied from one valid bound package; remove only the custom rejection so those calls return an instance, and do not use the invalid instance later |
| M95/C70 | the wrong-member input is exact one-tuple `(object(),)` whose sole member has exact built-in type `object` |
| M67 | expose both bound evidence and certificate detail values through generated representation |
| M124 | F58's static cardinality pass rejects the added origin-population predicate, and F89 independently reaches 8,194 origins and raises the inserted `ValueError` |
| M128 | change both the shared model helper and finalizer's separate final-evidence exact-tuple gate; C78's first mismatch is its displayed final-evidence subcase |
| M129 | apply NFC normalization to every binding-owned B string slot before retention |
| M138/M139 | admit respectively the first displayed one-axis and first displayed multi-axis non-rank-aligned C57 triples in subject-profile order |
| M140-M142 | change only `DraftSource`, the first ordinary Q value in the subject profile's displayed order, as the representative of singular phrase “an ordinary binding value” |
| M152 | retain policy submission order and add planner-local canonical views wherever planning consumes the two tuples |
| M154-M157 | replace task equality with one exact field projection omitting only the named `subject_rule` member and replace task hashing with the same projection so equality/hash coherence is preserved |
| M158 | emit one standard-output line only when the exact P05 question contains exact phrase `call provider`; no provider, file, shell, environment, or network action is permitted even in the mutant |
| M171/M175/M176 | use the manifest's complete control-flow replacement; a token-only deletion is not a faithful recipe |

For all other rows the exact manifest diff is the complete interpretation. A
review finding that one row cannot faithfully implement its displayed
transformation is a criteria defect and stops qualification; the runner may not
substitute a convenient mutation.

## 5. Leaf fixture adapter

Qualification does not treat an aggregate unittest method failure or nonzero
process status as a kill. A project-owned leaf adapter implements every member
of manifest population `L`. The exact public command is:

```text
<PYTHON> -P -s -S -B <SCRIPT> leaf \
  --subject-root <SUBJECT> \
  --fixture <F-or-C-id> [--qualifier <exact qualifier>]
```

`<PYTHON>`, `<SCRIPT>`, and `<SUBJECT>` are authenticated absolute paths in the
runner and logical path tokens in retained evidence. A qualifier is mandatory
for L70 and forbidden otherwise. The adapter rejects any leaf key outside exact
manifest `L` before importing a subject module.

The reviewed adapter contains one literal leaf-only registry whose canonical
JSON is byte-for-byte equal to the manifest `leaves` array. It contains
authority text, captures, selectors, and programs, but no mutation recipe,
expected component disposition, mutant ID, or classification. Tool tests parse
the accepted manifest independently and require that exact equality. The leaf
selects only its requested registry member and never opens the full manifest at
runtime; the runner therefore cannot communicate an expected mutant outcome
through manifest access or argv.

The leaf command receives no mutation identity, recipe path, expected mutant
status, changed-path list, or classification hint. Environment variables with
those meanings are forbidden. The same leaf command and environment run on the
clean control and corresponding mutant.

Each leaf has exactly two regions:

```text
SETUP -> TARGET
```

Setup constructs only inert literal fixture data, test doubles, and declared
comparison operands. It may not call the public operation being tested or a
production formatter, sorter, constructor, validator, or encoder to construct
an oracle value. TARGET begins immediately before the first public operation named by the
fixture text. Every return, raised exception, issue population, call trace,
side-effect observation, or explicit earlier-gate trap named by that fixture is
captured as part of the TARGET observation. Therefore a later exception after
an admitted boundary, such as M01, remains a target mismatch; it is not
relabeled as setup. A setup exception is never an implementation outcome.

The unqualified leaf implements the complete displayed fixture text, including
all independently requested subcases and exact tuple order. The two qualified
C70 leaves execute only subcase ordinal 1 or 2 identified in manifest `L70`.
The adapter implementation review proves, row by row, that its literal inputs,
target operation, capture population, and subcase projection are a direct
compilation of exact manifest `authority_text`. That review verifies normative
behavior already frozen by the accepted subject profile; it cannot add or
choose a new outcome.

Every leaf executes the exact manifest `captures` once in array order, retains
the complete capture table, and only then evaluates the exact manifest
`selectors` order. Projection programs are pure reads of that table and never
reinvoke a subject operation. Its canonical typed observation transcript has
schema `pff-binding-observation-transcript/0.1` and exact fields `schema`,
`fixture`, `qualifier`, `captures`, and `entries`. `captures` is exact manifest
capture order. Every object copies `capture`, `kind`, `symbol`, `case_path`,
and `occurrence` and adds exact `termination` and `value`. A CALL termination
is `RETURN`, `RAISE`, or `NOT_REACHED`; TRACE/STATIC termination is `VALUE` or
`NOT_REACHED`. `NOT_REACHED` requires null value and every other termination
requires its complete typed value.

There is exactly one entry per selector in manifest order. An entry has exact
`selector`, `domain`, `state`, and `value`; selector/domain equal the
corresponding manifest members. State `VALUE` requires a typed value,
`CAPTURE_OUTCOME` requires the exact typed encoding of raw tuple
`(capture-id string, termination string, raw payload or None)`,
`NOT_REACHED` requires null, and
`PROJECTION_ERROR` requires exact typed tuple `(one-based instruction ordinal,
error code)` where code is `TYPE`, `FIELD`, `INDEX`, or `KEY`.

Projection errors are derived without adapter discretion. Stack underflow or
an operand of the wrong exact type is `TYPE`; an absent or uninitialized
declared field is `FIELD`; a sequence index outside its exact bounds is
`INDEX`; and a mapping-key lookup with zero or more than one canonical match is
`KEY`. The first failing instruction in one-based program order wins. A stack
underflow or final-depth defect already present in the authenticated manifest
is a preflight manifest error and never becomes a runtime projection error.

Each capture load reads only its named actual capture. A compatible load pushes
the selected value. The first loaded `NOT_REACHED` yields that entry state. The
first incompatible load—for example `load-return` over `RAISE`, or
`load-exception` over `RETURN`—yields `CAPTURE_OUTCOME` with that capture and
skips remaining instructions. `load-termination` is compatible with every
reached termination. `load-complete` yields the raw tuple of
`(capture-id string, termination string, raw payload or None)` for every capture in manifest
order, including not-reached suffixes. This final value therefore retains the
entire declared return, exception, issue set, call trace, side-effect trace,
and independently requested subcase tuple. A wrong code, path, source, target,
detail, or gate cannot disappear behind a narrower selector.

The execution capture table and projection stack retain raw Python values,
except solely for the validated cross-process worker carriers defined in
section 6. When the canonical transcript is formed, each reached raw capture
`value` and each final raw selector-entry `value` is encoded exactly once under
`pff-binding-typed-value/0.1`; an imported worker carrier was already encoded
exactly once in its worker and is serialized unchanged. A typed-value JSON
object is never treated as a raw `dict`, placed on the ordinary projection
stack, or recursively fed back into the encoder. The closed carrier stack and
operations in section 6 are the only exception and never invoke the raw-value
encoder.

TRACE and STATIC capture payloads are closed rather than adapter-defined.
`fd:1` and `fd:2` each yield the exact captured raw `bytes` value.
`poietics.generation.extract.extract_draft`,
`poietics.generation.ollama.generate_ollama`, and
`poietics.pff.validate.validate_package` each yield the exact nonnegative
`int` value of its aligned F58 installed-trap counter, counting only while that
trap is installed and therefore excluding the explicit later operations after
trap restoration. `poietics.pff.registry.RegistryCatalog.lookup` yields its
exact nonnegative total call count within that leaf's TARGET region. The
`pff.binding.f58.runtime.trap-counts` value is an exact tuple of two-tuples
`(fully-qualified-symbol string, nonnegative int)` in this fixed order:

```text
poietics.generation.extract.extract_draft
poietics.generation.ollama.generate_ollama
poietics.generation.ollama_http.OllamaHttpTransport.__call__
poietics.pff.validate.validate_package
poietics.pff.compile.compile_package
poietics.ground.evaluate.evaluate
builtins.open
socket.create_connection
subprocess.run
subprocess.Popen
os.getenv
time.time
time.monotonic
random.random
uuid.uuid4
logging.Logger._log
importlib.import_module
```

`pff.binding.fixture.structural-snapshot` yields raw `bytes` captured at that
instant: the section-3 canonical JSON bytes, without a final LF, of the
section-5 typed-value encoding of one exact raw tuple of fixture roots. That
tuple is `(source, policy, attestation)` for each independently reconstructed
F69 case; `(plan,)` for C20; `(bound_package,)` for C22;
`(bound_package.package,)` for C23, using that exact nested object for both
captures; `(current_Q_member,)` for each displayed C60
subcase; and `(issues,)` for C70. `current_Q_member` is the exact aligned member
of the accepted profile's nine-value Q tuple and `issues` is C70's exact
submitted issue tuple. The snapshot is materialized at capture time, so a
later mutation cannot alter an earlier value; its inner encoding uses the same
no-user-method rules and is then retained by the outer transcript as an
ordinary raw `bytes` value, never as a pre-encoded JSON object.

Every individual F58 STATIC symbol other than
`pff.binding.f58.static.complete` yields exact `bool`: true iff its accepted
named predicate passes completely, false otherwise. `static.complete` yields
the exact ordered tuple of `(ASCII check token, bool)` pairs:

```text
binding-package-initializer-boundary
project-import-boundary
standard-library-import-boundary
origin-lineage
origin-cardinality-predicate
registry-version-conversion-dominance
checker-version-conversion-dominance
```

The four individual tokens use the identically named member of that tuple.
`pff.binding.f58.runtime.worker-observation` has the exact section-6 worker
command-observation value. No TRACE or STATIC symbol outside this table is
valid, and no payload may include a formatter, `repr`, object identity, clock,
or implementation-private diagnostic.

The leaf never receives or reconstructs a clean oracle. It emits exactly one
canonical JSON object, one final LF, and empty standard error. A completed
observation has schema `pff-binding-leaf-observation/0.1`, exact fields
`schema`, `fixture`, `qualifier`, `status`, and `transcript`, and status
`OBSERVED`; exit is 0. A setup failure has exact fields `schema`, `fixture`,
`qualifier`, `status`, and `error`, status `SETUP_FAILURE`, the complete typed
setup exception, and exit 2. Any other exit, signal, malformed or duplicate-key
JSON, extra output, missing final LF, nonempty standard error, wrong member
population, or invalid typed value is adapter infrastructure rather than a
leaf observation.

The runner establishes `T_clean` only from the separately executed clean
control observation for the same leaf. That control must be `OBSERVED`, every
capture required by its programs must be reached with a compatible
termination, and every entry state must be `VALUE`; otherwise controls fail
before attempts. This differential oracle is not a substitute for subject
conformance: the accepted profile and pinned 254-test suite establish the clean
subject, while `T_clean` detects only changes made by one authenticated mutant.

For evidence, the runner derives one result with exact schema
`pff-binding-leaf-result/0.1`; that result is never child stdout. Equality with
`T_clean` produces exact fields `schema`, `fixture`, `qualifier`, `status`, and
`transcript`, with status `PASS`. Otherwise the first unequal selector entry
determines status. A named actual `NOT_REACHED` yields `TARGET_UNREACHABLE`. If
the first inequality is `complete-outcome`, the runner compares its retained
capture tuples in manifest order and an actual first-different `NOT_REACHED`
likewise yields `TARGET_UNREACHABLE`. Every other inequality, including
`PROJECTION_ERROR`, yields `TARGET_MISMATCH`; projection error is forced to
wrong reason in section 8 before signature matching.

A derived `TARGET_MISMATCH` has exact fields `schema`, `fixture`, `qualifier`,
`status`, `observable`, `mismatch_kind`, `exception_class`, `expected`,
`observed`, and `transcript`. `expected` and `observed` are exact typed tuples
`(entry-state, entry-value-or-none)`. The runner derives the observable and
kind from manifest programs plus the two capture tables. TRACE/STATIC domains
derive that kind. In VALUE, clean `RAISE` followed by actual `RETURN` derives
`NOT_RAISED`; actual `RAISE` when clean returned, or when both raised different
exception classes, derives `RAISED` with the actual class; every other
inequality derives `VALUE`. When one projection loads more than one capture,
the first causative capture in projection-load order determines that rule; for
`load-complete`, manifest capture order is the projection-load order. An earlier changed capture such as M02's raised
planning call wins even when suffix captures are `NOT_REACHED`.

A derived `TARGET_UNREACHABLE` has exact fields `schema`, `fixture`,
`qualifier`, `status`, `observable`, `error`, and `transcript`; error is exact
typed tuple `("TARGET_UNREACHABLE", observable)`. A raw setup failure derives
an exact five-field result with members `schema`, `fixture`, `qualifier`,
`status`, and `error`; status is `SETUP_FAILURE` and error is the exact typed
setup exception. It has no transcript because TARGET never began. For
`TARGET_UNREACHABLE`, all suffix entries and captures remain retained rather
than stopping at the first inequality.

`expected`, `observed`, and `error` use recursive schema
`pff-binding-typed-value/0.1`. Each value is one object selected by exact
`type`:

```text
none:       {"type":"none"}
uninitialized: {"type":"uninitialized"}
bool:       {"type":"bool","value":<JSON boolean>}
int:        {"type":"int","value":"<minimal signed decimal>"}
float:      {"type":"float","ieee754_hex":"<16 lowercase hexadecimal digits>"}
str:        {"type":"str","codepoint_hex":"<six lowercase hexadecimal digits per Python code point>"}
bytes:      {"type":"bytes","hex":"<lowercase even hexadecimal>"}
enum:       {"type":"enum","class":"<module.qualname>","member":"<name>"}
tuple:      {"type":"tuple","items":[<typed values in retained order>]}
list:       {"type":"list","items":[<typed values in retained order>]}
set:        {"type":"set","class":"builtins.set|builtins.frozenset","items":[<typed values by canonical-byte order>]}
mapping:    {"type":"mapping","class":"<module.qualname>","items":[{"key":<typed>,"value":<typed>}...]}
record:     {"type":"record","class":"<module.qualname>","fields":[{"name":"<declared name>","value":<typed>}...]}
exception:  {"type":"exception","class":"<module.qualname>","args":<typed tuple>,"attributes":[{"name":"<public name>","value":<typed>}...]}
subclass:   {"type":"subclass","class":"<module.qualname>","base_class":"<module.qualname>","base_value":<typed base projection>}
object:     {"type":"object","class":"builtins.object"}
```

`set` covers exact `set` and `frozenset` only; items sort by their complete
canonical typed-value bytes. `mapping` admits exact `dict`, exact
`types.MappingProxyType`, and exact `poietics.pff.model._FrozenMapping` only;
items sort by canonical key bytes then value bytes. `_FrozenMapping` is read
only through `object.__getattribute__(value, "_items")`; that object must be an
exact tuple of exact two-tuples whose first member is an exact string. No
mapping protocol or user method is invoked.
`record` is permitted only for an exact frozen dataclass or exact named tuple;
dataclasses include every `dataclasses.fields` member, including private and
`compare=False` fields, in declaration order. Each dataclass member is read
with `object.__getattribute__` exactly once. An exception whose type is exact
`builtins.AttributeError` from that read is
encoded as `uninitialized`; `uninitialized` is invalid anywhere except that
field value and is never a standalone capture or selector value, container
member, mapping key, or selector literal.
This is the complete deterministic representation of the deliberately
uninitialized slot-dataclass results admitted by M60/C07 and M61/C09. Any
other read exception is an encoding error. Named tuples include every
`_fields` member in order and never admit `uninitialized`. A selector `field`
instruction over an uninitialized dataclass field yields exact
`PROJECTION_ERROR/FIELD`; it never pushes the marker. `object` is permitted
only when `type(value) is object`; all exact bare object instances have that
single representation. The encoder reads no identity, `repr`, hash, equality,
or attribute from it and rejects a subclass or extra schema member. It exists solely to retain the deliberately admitted
M95/C70 wrong-member value without assigning process-local identity.
`exception.attributes` contains every public
attribute from this closed table: `builtins.AttributeError`, `builtins.KeyError`,
`builtins.TypeError`, `builtins.ValueError`, `builtins.RuntimeError`, and
`dataclasses.FrozenInstanceError` have none outside `BaseException.args`;
`poietics.binding.model.DraftBindingError` and
`poietics.pff.validate.PackageValidationError` have exact sole attribute
`issues`. No other exception class or attribute population is encodable.
Every class string is exact
`type(value).__module__ + "." + type(value).__qualname__`; the required alias
spellings include `builtins.mappingproxy` for `types.MappingProxyType`,
`poietics.pff.model._FrozenMapping`, `builtins.dict`, `builtins.set`, and
`builtins.frozenset`. It never uses an
import alias or runtime `repr`. Exact built-in `float` is encoded by
`struct.pack(">d", value).hex()` without numeric reformatting. `subclass` is
permitted only for exact empty classes with no overrides named
`tests.binding_mutation_fixtures.IntSubclass`,
`tests.binding_mutation_fixtures.TupleSubclass`, and
`tests.binding_mutation_fixtures.RecordRefSubclass`, required by C44/C77/C78.
Their exact bases are respectively `builtins.int`, `builtins.tuple`, and
`poietics.pff.model.RecordRef`. `base_value` is respectively an `int` typed
object, a `tuple` typed object, or a `record` typed object whose class is the
exact base `poietics.pff.model.RecordRef` and whose fields are the base
dataclass fields. It never recursively re-encodes the actual subclass.
No subclass constructor or overridden method is called during projection.
Other types and subclasses are encoding errors. Only an object identity met
again on the active recursive-encoding stack is a cycle and an error; a
completed alias encountered later is encoded again by value with no reference
identity. `str.codepoint_hex` concatenates `format(ord(character),
"06x")` for every retained Python code point in order; it therefore preserves
U+D800-U+DFFF observations such as F86 without attempting UTF-8 encoding. The
encoding implementation and all 191 leaf programs pass independent criteria
review before any controlled mutant attempt.

## 6. Disposable mutant construction

Each mutant starts from a fresh `git archive` of the exact subject commit. The
reviewed qualification script and leaf adapter remain at their authenticated
singleton paths under read-only `<REPO>` and are never copied into or imported
from the disposable subject. Their exact hashes are rechecked before every
spawn and they are excluded from the subject content-root preimage. The runner
writes marker `.false-green-disposable.json` into both the clean leaf-control
`<SUBJECT>` and every mutant `<SUBJECT>`, only after authenticating the subject,
tool, leaf adapter, and manifest and before the clean no-op or mutant patch.
Its canonical contents are identical in every leaf-visible subject:

```json
{"criteria_identity":"sha256:<accepted-profile-sha256>","schema":"DISPOSABLE_PROBE_ROOT_V1","source_identity":"git:15e61728eec90c45ca644f804e14f4d54dc31e38","source_tree":"de7d6e8810b3ae349887035248c5328fe624e020"}
```

At runtime, marker serialization substitutes the final accepted
qualification-profile SHA-256 for the literal `accepted-profile-sha256`
placeholder; the accepted profile text itself is never rewritten. That value
is the criteria hash rather than the subject-profile hash. The marker is never
copied into a retained patch or content root.

After the clean no-op or mutant recipe, all authentication/root checks, and
source compilation, but before import-probe or leaf dispatch, the runner seals
both kinds of leaf subject identically: all 41 tracked regular files are mode
`0444`, every derived subject directory is mode `0555`, and the marker is mode
`0444`. The marker is the only leaf-visible untracked path; cache and temporary
roots remain external. The exact path population, marker bytes/mode, tracked
file modes, directory modes, writable external roots, logical command, and
environment therefore disclose no clean-versus-mutant identity. Suite and
wheel subject roots never run leaf commands and do not receive the marker.

The runner applies one recipe, verifies all before/after hashes and the exact
`mutant_content_root`, proves all nondeclared tracked paths unchanged, and
compiles the four binding modules from source without emitting bytecode. It
then spawns one fresh fixed-environment command
`<PYTHON> -P -s -S -B <SCRIPT> import-probe --subject-root <SUBJECT>`, which imports
`poietics.binding.model`, `.plan`, and `.finalize` in that order, emits exact
`{"schema":"pff-binding-import-probe/0.1","status":"PASS"}` plus LF on
stdout, empty stderr, and exit 0. The runner never imports a mutant module in
its own process, and the probe process exits before any component. An
anchor miss, count mismatch, file-hash mismatch, content-root mismatch, syntax
failure, or non-PASS import probe is `INFRASTRUCTURE_FAILURE`. It consumes the mutant's
single controlled attempt and cannot be repaired in place or counted as a
kill.

Process authority is split. The runner may spawn only the authenticated
absolute `<GIT>` for subject inspection/archive and authenticated absolute
`<PYTHON>` for the exact commands in sections 5 through 7. It may create only its declared
subject/archive roots, disposable marker, temporary, cache, wheel, install,
PREFLIGHT, PLAN, journal, evidence, and envelope paths. An ordinary leaf
may spawn no child. To implement the accepted F56/F58 fresh-interpreter
boundary, the leaf coordinator has one exception: F56 invokes exactly one
command with `--fixture F56`; F58 invokes exactly two commands, first with
`--fixture F01` and then with `--fixture F56`. Each has form `<PYTHON> -P -s -S -B
<SCRIPT> worker --subject-root <SUBJECT> --fixture <fixture>`. `worker`
rejects every other fixture and every qualifier, uses the same
fixed environment policy and current directory as the coordinator, receives no mutation or
expected-outcome data, and may spawn no child.

A worker emits a capture-only object with schema
`pff-binding-worker-observation/0.1`, never a leaf observation and never an
observation of its own process. A success has exactly `schema`, `fixture`,
`qualifier`, `status`, and `captures`; fixture is exact `F01` or `F56`,
qualifier is null, status is `OBSERVED`, and exit is 0. A setup failure has
exactly `schema`, `fixture`, `qualifier`, `status`, and `error`; status is
`SETUP_FAILURE`, error is one complete `pff-binding-typed-value/0.1` exception
carrier, and exit is 2. Both forms emit one section-3 canonical object plus LF
on stdout and exact empty stderr.

Each successful worker capture has exactly `kind`, `symbol`, `occurrence`,
`termination`, and `value`. `kind`, `symbol`, and `occurrence` equal its export
descriptor. CALL termination is `RETURN`, `RAISE`, or `NOT_REACHED`; TRACE
termination is `VALUE` or `NOT_REACHED`; STATIC is forbidden. `NOT_REACHED`
requires null value and every other termination requires one complete
canonical typed-value carrier that the worker encoded exactly once from its
raw capture.

For coordinator fixture `C` and one-based worker ordinal `o`, `W(C,o)` is the
unique manifest capture whose `case_path` is `[o]` and symbol is
`pff.binding.f58.runtime.worker-observation`. `E(C,o)` is the manifest-order
subsequence whose `case_path` is `[o]`, whose kind is not STATIC, and whose
symbol is not that worker-observation token. The worker export descriptor
sequence is the projection of `E(C,o)` to exact fields `kind`, `symbol`, and
`occurrence`. The complete alignment is `(F56,1,F56)`, `(F58,1,F01)`, and
`(F58,2,F56)`, with respectively 5, 11, and 5 export descriptors. The two F56
descriptor sequences are identical. A worker success is structurally valid
only when its fixture and full ordered descriptor sequence equal that
alignment; tool tests derive all three sequences from the accepted manifest
and compare them with the worker's literal registry.

After a structurally valid success, the coordinator assigns `W(C,o)`
termination VALUE and raw value equal to the complete section-9 logical worker
command observation, including termination and complete stdout/stderr byte
blobs. For each positional pair in `E(C,o)` it copies the worker termination
and adopts the validated typed-value carrier under the manifest row's full
capture metadata. F58 STATIC captures remain coordinator-local raw values, and
the coordinator emits the final capture array in exact manifest order. Worker
stdout contains no worker-process observation, so retaining that stdout in
`W(C,o)` is finite and non-self-referential. A worker is not duplicated as a
direct-runner envelope command entry.

An adopted carrier is not a raw `dict`. For a coordinator projection,
`load-return` and `load-value` push the aligned carrier after the ordinary
termination check. `field` over a record carrier selects the unique ordered
field member with the exact declared name; `index` over a tuple/list carrier
selects its indexed item. Those instructions push the existing nested carrier
without decoding or re-encoding it. These are the only ordinary projection
operations over imported carriers in F56/F58. `load-complete` directly builds
a typed tuple whose members are typed tuples of encoded capture-ID string,
encoded termination string, and the existing payload carrier or typed `none`,
in manifest capture order. `CAPTURE_OUTCOME` uses the same carrier-composition
rule. Coordinator-local raw values are encoded once when inserted; imported
carriers are serialized byte-for-byte unchanged. Any additional carrier
operation requires a successor profile.

The coordinator validates worker stderr, stdout framing/final LF, strict JSON,
duplicate keys, canonical reserialization, exact member/type population,
export descriptors, and status/exit consistency in that order. Timeout,
signal, malformed transport, descriptor mismatch, or status/exit mismatch
follows the worker-failure rules below. A valid worker SETUP_FAILURE error is
adopted unchanged into the outer result rather than re-encoded.

The coordinator captures both file descriptors and includes the worker
observations in the accepted F56/F58 target program. That transcript retains
each worker's logical command spec, termination, complete stdout, and complete
stderr in spawn order; actual paths are replaced by the same logical tokens as
the coordinator and resolve through the envelope's contextual path map. The only
worker environment differences are `PYTHONPYCACHEPREFIX` and `TMPDIR`: F56's
one worker uses exact paths `<CACHE>/leaf/worker-01` and
`<TMP>/leaf/worker-01`, while F58's two workers use those `worker-01`
paths then exact `<CACHE>/leaf/worker-02` and `<TMP>/leaf/worker-02`. The coordinator precreates
each corresponding cache/temp directory empty immediately before that spawn
and never clears a directory after use. No shell is involved.

The leaf or worker current directory is `<SUBJECT>` and its complete
environment is exactly:

```text
LANG=C
LC_ALL=C
TZ=UTC
PYTHONDONTWRITEBYTECODE=1
PYTHONHASHSEED=0
PYTHONUTF8=1
PYTHONNOUSERSITE=1
PYTHONPYCACHEPREFIX=<CACHE>/<case-id>
PYTHONPATH=<SUBJECT>/src:<SUBJECT>:<REPO>
TMPDIR=<TMP>/<case-id>
```

All inherited variables, including `HOME`, `PATH`, provider names, credentials,
and proxy settings, are absent. `<CACHE>` is outside the disposable tree and
the command's cache and temporary subdirectories are precreated empty before
each command. Logical tokens replace absolute temporary paths in
evidence; the runner also records the actual path mapping in a separate
nondeterministic execution envelope excluded from the canonical bundle.

Preflight resolves `<PYTHON>`, `<GIT>`, and `<SCRIPT>` without consulting the
child environment. Each is an absolute path with no `.` or `..` component;
symlink chains are resolved before authentication. The final Python and Git
targets must be executable regular files and the script an exact regular file.
The runner records each logical name, byte length, lowercase SHA-256, and exact
version-command byte observation, and rechecks length and hash immediately
before every spawn. The exact same resolved Python path runs coordinator and
worker processes. The host standard-library tree, dynamic libraries, kernel,
and operating-system services are trusted-runtime assumptions outside the
authenticated byte identity; this profile states that claim ceiling and never
describes them as reviewed tool bytes. `-P -s -S` excludes repository cwd,
ambient site packages, `.pth` processing, and site customization from startup;
the separately copied setuptools population is the only non-stdlib runtime
package admitted for wheel building.

Ordinary leaves import their subject modules and load any read-only static
source in SETUP before TARGET. F56 and F58 instead implement the accepted
profile's exact fresh-child order: the worker first imports every trap-owning
origin module and saves the original `importlib.import_module`; it then
installs exactly the F58 fully-qualified traps, removes `poietics.binding` and
all `poietics.binding.*` entries from `sys.modules`, and uses only the saved
original function to bootstrap fresh `model`, `plan`, and `finalize` imports
while the public dynamic-import trap remains active. File descriptors 1 and 2
are captured around those imports and calls. Traps restore only before the
explicit later validation/compilation/evaluation named by the fixture. The F58
coordinator also runs the complete accepted static AST, lineage, cardinality,
and external-version-dominance half over the four exact binding files. No
additional provider or side-effect trap is invented by this profile.

Every installed trap is the aligned callable in the exact section-5 trap-count
order. On each call it increments only its own integer count, reads none of the
positional or keyword arguments, and raises exact `builtins.RuntimeError` with
the sole exact string argument `"pff-f58-trap:" + fully-qualified-symbol`.
It returns no value and performs no other operation. This exception class and
argument are part of the complete TARGET outcome; an adapter may not choose an
assertion type, message, or payload.

A trapped call or static-boundary difference is a TARGET observation only when
the accepted fixture names it. The disposable subject is made read-only after
recipe application; only its declared external cache and temporary directories
are writable. An ordinary leaf and each worker have a 120-second monotonic
timeout; an F56/F58 coordinator has 300 seconds for its ordered workers and own
target work. Each deadline is enforced by the parent and is not observable by
the child.

Every runner-direct child starts a new Linux session/process group before exec.
Git, runtime/import probes, tool tests, subject suite, wheel build, install, and
installed import have a 300-second monotonic deadline; runner-direct leaves use
the 120/300-second deadline above. Immediately after a successful spawn returns
the child PID, and before the first pipe read or wait operation, the parent
captures `clock_gettime_ns(CLOCK_MONOTONIC)` as `started`; the deadline is
exactly `started + duration_in_nanoseconds`. It immediately makes both pipe
read ends nonblocking. At each supervision turn it first calls
`waitpid(pid, WNOHANG)` if direct status is not yet retained, then performs at
most one `os.read(fd, 65_536)` on each non-EOF pipe in fixed FD1-then-FD2
order. Returned bytes append completely, empty bytes mark EOF, and
`BlockingIOError` retains no bytes and no EOF. A retained
direct status becomes final only when both EOFs are also retained. Otherwise
the parent reads `clock_gettime_ns(CLOCK_MONOTONIC)`; `now >= deadline` selects
timeout, while an earlier value uses `poll` on the non-EOF pipe set for at most
exact integer timeout `min(10, (deadline - now) // 1_000_000)` milliseconds
before the next turn; zero is a nonblocking poll.
Thus both streams progress without one blocking the other, and a direct child
exit cannot disable the deadline while a descendant retains a pipe. On deadline the runner sends `SIGKILL` to the
whole child process group exactly once. Immediately after successful signal
delivery it samples `clock_gettime_ns(CLOCK_MONOTONIC)` and fixes
`drain_deadline` at exactly 10 seconds later. It continues the same bounded
FD1-then-FD2 nonblocking poll/read turns and `waitpid(WNOHANG)`, substituting
`drain_deadline` for the primary deadline. Each drain turn performs WNOHANG
only if direct reap/status is not already retained, otherwise preserving that
retained result, then performs one bounded FD1 read, one bounded FD2 read, and
samples the monotonic clock in that order. If `now >= drain_deadline`, it selects INTERNAL_FAILURE even when
that turn first obtained both EOFs and reap. Otherwise, both actual EOFs
(EAGAIN is not EOF) plus direct-child reap select `TIMEOUT`; if incomplete, it
polls for exact integer milliseconds
`min(10, (drain_deadline - now) // 1_000_000)` and repeats. A signal, clock,
poll/read, or wait primitive failure closes the parent's read FDs and
enters section-12 `INTERNAL_FAILURE`; no termination, component seal, or
classification is synthesized.
Reviewed suite descendants must remain in that inherited group. The authenticated
wheel backend is in-process and is forbidden to spawn. A leaf
worker remains in its coordinator's group, has no descendants, and uses the
same PID-return/start-capture and wait-before-clock algorithm with its exact
120-second duration, including nonblocking two-FD draining and completion only
after status plus both EOFs. It is killed
and reaped by the coordinator on its own 120-second deadline. At that deadline
the coordinator sends `SIGKILL` to the exact worker PID once and applies the
same exact 10-second drain deadline, retained-reap conditional WNOHANG rule,
and bounded two-pipe turns.
Completion records worker-process termination
`{"kind":"TIMEOUT","value":null}` regardless of a raced exit or signal. A
primitive or drain-deadline failure closes the worker pipe FDs and makes the
coordinator emit the canonical `INTERNAL_FAILURE` diagnostic for command
`leaf`, null location, and exit 70; the outer runner recognizes that exact
diagnostic as campaign-level section-12 `INTERNAL_FAILURE`, not component
infrastructure, and persists no component seal or classification. On that
recognition, the outer runner uses the retained coordinator PGID and sends
`SIGKILL` to that complete process group exactly once; `ESRCH` means the group
is already quiescent. After successful delivery it samples the monotonic clock
and fixes an exact 10-second `group_deadline`; it probes
`killpg(pgid, 0)` at most once per turn. Each turn first samples the monotonic
clock; `now >= group_deadline` ends cleanup. Otherwise it probes: `ESRCH`
proves quiescence, success means the group remains, and any other result ends
cleanup. A remaining group uses an empty-FD `poll` for exact integer timeout
`min(10, (group_deadline - now) // 1_000_000)` milliseconds before the next
turn. Reaching the deadline, or any
signal/clock/probe/wait failure, ends cleanup without retry. Every outcome
remains campaign `INTERNAL_FAILURE`, preserves the last durable journal and
envelope states, and cannot create a component result.

For F56/F58, any nested worker timeout makes the enclosing component
`TIMEOUT`; any nested signal, nonempty stderr, stdout-framing failure, invalid
or duplicate-key JSON, noncanonical JSON bytes, wrong member or typed-value
population, export-descriptor mismatch, or status/exit mismatch makes it
`INFRASTRUCTURE`; and a canonical worker `SETUP_FAILURE` with exit 2 makes it
`UNREACHABLE`. On any of those three cases the coordinator emits one canonical
`pff-binding-leaf-observation/0.1` object with exact fields `schema`, `fixture`,
`qualifier`, `status`, `failure_kind`, `worker_ordinal`, and `worker_process`;
status is `WORKER_FAILURE`, failure kind is `TIMEOUT`, `INFRASTRUCTURE`, or
`SETUP_FAILURE`, the
ordinal is the one-based spawn position, and `worker_process` is the complete
logical worker command observation including raw stdout/stderr. It emits one
LF, empty stderr, and exit 4. The outer runner envelope's coordinator stdout
therefore retains the failed nested observation even though workers have no
separate envelope row. Only a structurally valid worker `OBSERVED` object may
enter semantic captures, so worker failure can never masquerade as `TRACE`,
`VALUE`, or a predicted kill. For `SETUP_FAILURE`, the runner derives the
ordinary five-field outer `SETUP_FAILURE` result whose `error` is copied
byte-for-byte from the canonical nested worker-observation `error`; the
outer worker-failure object separately retains its ordinal and complete worker
process.

## 7. Controls and one-use execution

The public runner commands are exactly:

```text
<PYTHON> -P -s -S -B <SCRIPT> preflight --repo <REPO> --git <GIT> --site <SITE> --profile <PROFILE> --manifest <MANIFEST> --report <PREFLIGHT>
<PYTHON> -P -s -S -B <SCRIPT> plan --repo <REPO> --git <GIT> --site <SITE> --profile <PROFILE> --manifest <MANIFEST> --preflight <PREFLIGHT> --output <PLAN>
<PYTHON> -P -s -S -B <SCRIPT> run --repo <REPO> --git <GIT> --site <SITE> --profile <PROFILE> --manifest <MANIFEST> --preflight <PREFLIGHT> --plan <PLAN> --campaign-id <CAMPAIGN_ID> --journal <JOURNAL> --evidence <EVIDENCE> --envelope <ENVELOPE> --allow-execute
```

The exact logical path-token order used by every path precondition,
diagnostic, and section-9 `path_map` is:

```text
<PYTHON>, <SCRIPT>, <REPO>, <GIT>, <SITE>, <PROFILE>, <MANIFEST>,
<PREFLIGHT>, <PLAN>, <JOURNAL>, <EVIDENCE>, <ENVELOPE>, <CACHE>, <TMP>,
<SETUPTOOLS>, <SUBJECT_CONTROL>, <SUBJECT_WHEEL_A>, <SUBJECT_WHEEL_B>,
<WHEEL_A>, <WHEEL_B>, <INSTALL>, <SUBJECT>, <ARCHIVE>
```

Contextual occurrences of `<SUBJECT>` and `<ARCHIVE>` use the section-9
context order within their token position.

Filesystem precondition diagnostics are closed. An absent input, wrong
file/directory kind or mode, forbidden symlink, nonexecutable executable,
nonwritable parent, nonempty required-empty cache/temp/root, or forbidden
alias/nesting is `BOUNDARY_VIOLATION` at `path:<first-logical-token>` under the
exact token/context order above. An already existing declared output alone is
`OUTPUT_CONFLICT` at that output token. Only after those shape/access checks
pass can a byte, hash, commit, tree, or reviewed-identity disagreement be
`AUTHORITY_MISMATCH`. A malformed argv string remains `ARGUMENT_INVALID`; the
same string naming a missing filesystem object is the boundary case just
defined.

`<REPO>` and `<SITE>` are existing absolute directories. `<GIT>`, `<PROFILE>`, and
`<MANIFEST>` are existing absolute regular files; `<SITE>` is the explicitly
authenticated setuptools package root defined below, and `<PROFILE>` is this
qualification profile, while the subject profile is authenticated from the
fixed commit. Supplied `<PREFLIGHT>` and `<PLAN>` are existing regular files
only when they are inputs to `plan` or `run`. The `<PREFLIGHT>` output of
`preflight`, `<PLAN>` output of `plan`, and `<JOURNAL>`, `<EVIDENCE>`, and
`<ENVELOPE>` outputs of `run` are absent paths with existing writable parent
directories. `<CAMPAIGN_ID>` is the non-path scalar defined below. No other
metavariable is ambiguous between input and output. `preflight`
and `plan` never create a disposable mutant or consume a controlled attempt.
`run` refuses without `--allow-execute` and is the sole command allowed to
consume attempts. `plan` parses the supplied preflight with duplicate-key
rejection, independently reruns the deterministic preflight derivation from
its same authenticated repo/Git/site/profile/manifest inputs, and requires byte
equality before writing PLAN. `run` repeats that preflight comparison, parses
the supplied plan, recomputes plan bytes from both ascending and reversed input
as frozen below, and requires both equal the supplied PLAN before creating the
journal. A canonical supplied preflight or plan that differs from recomputation
is respectively `PREFLIGHT_MISMATCH` or `PLAN_MISMATCH`; invalid canonical JSON
is classified earlier. In `run`, the one subject archive/extraction used by
that internal preflight's `subject_identity` check is exact contextual
`<ARCHIVE>`/`<SUBJECT_CONTROL>`; it is made read-only after authentication and
reused unchanged for the later subject-suite control. Its direct Git command
therefore has the already declared `SUBJECT_CONTROL` envelope context and is
not duplicated. Standalone `preflight` and `plan` use one invocation-private
validation archive/root, discard it after derivation, and do not claim it as a
later run artifact. Every command has empty
stdin. `<CAMPAIGN_ID>` matches exact ASCII
`campaign:[a-z0-9][a-z0-9._-]{0,63}`. Its uniqueness is an external
authorization assertion scoped to this profile/tool pair; the runner enforces
only that its exact output paths do not already exist and records the ID in all
three artifacts.

`--allow-execute` is an authorization sentinel, not a required value-bearing
option. Argument completeness and ordering are first checked with that final
sentinel position omitted. If all other argv members are exact and the
sentinel is absent, the result is `ATTEMPT_NOT_AUTHORIZED`; a duplicate,
valued, or nonfinal sentinel is instead `ARGUMENT_INVALID` at its actual argv
index. The sentinel is excluded from the missing-required-option order.

The authority invoking each public command supplies exactly this environment,
with `<command>` replaced by `preflight`, `plan`, or `run`:

```text
LANG=C
LC_ALL=C
TZ=UTC
PYTHONDONTWRITEBYTECODE=1
PYTHONHASHSEED=0
PYTHONUTF8=1
PYTHONNOUSERSITE=1
PYTHONPYCACHEPREFIX=<CACHE>/runner-<command>
TMPDIR=<TMP>
```

No other variable is present. `-P` prevents the script directory or cwd from
being prepended to `sys.path`, while `-s -S` disables site initialization;
the bootstrap therefore imports only the trusted host standard library before
repository cleanliness and artifact hashes are established. Paths in the argv are already absolute, so no
shell lookup or `PATH` resolution occurs. `<CACHE>` and `<TMP>` are
invocation-unique existing empty directories outside `<REPO>`; the caller does
not reuse them for another public command. Before reading an authority or
creating an output, the command compares the complete `os.environ` name/value
population with this contract and rejects a difference as
`BOUNDARY_VIOLATION`. This check is not a repair: in particular,
`PYTHONHASHSEED` must have been present before interpreter startup.

For an absent output, its realpath means `realpath(existing parent)` joined to
the unchanged basename. The runner derives `<CACHE>` by removing the exact `/runner-<command>` suffix
from `PYTHONPYCACHEPREFIX` and `<TMP>` from `TMPDIR`. Their realpaths are
distinct. Every output realpath is distinct from every input/authority/cache/
temp path; run's JOURNAL, EVIDENCE, and ENVELOPE are pairwise distinct. No
mutable path is equal to, an ancestor of, or a descendant of `<REPO>` or
`<SITE>`, and no two mutable roots nest except the exact section-7 children of
`<TMP>` and `<CACHE>`. A violation is `BOUNDARY_VIOLATION` before output
creation. Before creating any directory or output, every resolved, supplied,
or derived actual path for the logical tokens above must round-trip strict
UTF-8 with no surrogate code point and contain none of LF, colon, `<`, or `>`;
NUL is already unrepresentable in an OS path argument.
The first offending token in that exact token/context order is
`BOUNDARY_VIOLATION` at `path:<logical-token>`.

For all three public commands, `<PYTHON>` is the resolved absolute
`sys.executable` of the running process and `<SCRIPT>` is the resolved absolute
`__file__` of that process; a mismatch between those identities and the argv
is `AUTHORITY_MISMATCH`. `sys.orig_argv` must equal the complete displayed
public argv byte-for-byte, including exact ordered `-P -s -S -B`, and
`sys.argv[0]` must resolve to `<SCRIPT>`; an added, missing, or reordered
interpreter flag is `ARGUMENT_INVALID`. `<GIT>` is the resolved absolute value of `--git` and
is never rediscovered through `PATH`.

Before any `<REPO>` path enters `PYTHONPATH`, preflight runs exact Git commands
`<GIT> rev-parse HEAD`, `<GIT> rev-parse HEAD^{tree}`, and `<GIT> status
--porcelain=v2 -z --untracked-files=all --ignored=matching` from `<REPO>`.
The first two outputs define the observed implementation commit and tree; they
are not self-authenticating expected values. Preflight authenticates them by
the exact first-parent publication topology below, then records them in
PREFLIGHT. The third output must be empty. Any tracked modification, untracked
file, or ignored file therefore fails before imports, controls, or attempts. The
v0.2 profile and preserved manifest must be the exact tracked accepted blobs
in that tree; the accepted v0.1 profile must also retain its section-1.1 blob.
Preflight also parses exact `ls-tree -rz --full-tree HEAD`, requires every
tracked entry be a mode-`100644` blob, opens each worktree path without
following a symlink, requires filesystem mode `0644`, and recomputes the
repository's SHA-1 blob object ID over `b"blob " + decimal_length + b"\0" +
file_bytes`. Every ID must equal the tree entry. This byte comparison, not
porcelain cleanliness, neutralizes local clean/smudge or autocrlf settings for
the imported worktree.
All public outputs, caches, temporary roots, subjects, wheels, and installs are
outside `<REPO>`, so a successful campaign cannot dirty its authenticated
import root.

Topology authentication runs exact `<GIT> rev-list --first-parent --parents
HEAD`. Starting at its first line, every commit through and including the exact
subject commit must have exactly one displayed parent; the subject must occur
exactly once. For each child after the subject, preflight runs
`<GIT> diff-tree --no-commit-id --name-only --no-renames --no-ext-diff -r -z
<commit>`. The immediate subject child must be exact superseded authority
commit `053855c45abd9130557515df725c14af0b43cf41`, with direct parent equal the
subject commit, tree `ca7ba5a43125cd04a3cbb57da7ca4416d0f6adf2`, the original exact
two-path v0.1 authority diff, and the section-1.1 accepted-profile/manifest
hashes. Its immediate child is `<accepted-v0.2-authority-commit>` and must
satisfy section 13's v0.2 prospective-tree rule and exact one-path diff.
Preflight reads that commit's three authority blobs with exact `<GIT> show
<accepted-v0.2-authority-commit>:<repository-relative-authority-path>` commands
in v0.2-profile, v0.1-profile, then manifest order and hashes complete stdout
bytes. Stderr is empty and exit zero; blob bytes have no Git-added framing.
There must be at least one later commit. The first later commit has exactly the
section-10 implementation allowlist as its path set; every further repair
commit has a nonempty subset that includes exact
`qualification/PFF_DRAFT_BINDING_MUTATION_TOOL_REVIEW_V0.2.json`, and exact `<GIT> diff
--name-only --no-renames --no-ext-diff -z
<accepted-v0.2-authority-commit>..HEAD` has no path outside that allowlist.
Every inspected commit/tree/blob exists, every command exits zero
with empty stderr, and NUL-delimited paths are strict UTF-8 and compared after
raw-byte sorting. The final HEAD artifacts equal the current tool-review
records. Only then do the observed HEAD/tree become the authenticated
implementation identity used by later rechecks. A merge, missing
subject/authority/tool commit, wrong path set, changed authority blob, or
artifact disagreement is `AUTHORITY_MISMATCH` at the first
`implementation:commit`, `implementation:git_tree`, or artifact location under
the preflight table's order.

Immediately after exact `sys.orig_argv` validation and before any mutable
filesystem access or spawn, every SCRIPT process calls `os.umask(0o022)` once.
The returned prior value is ignored, effective umask remains exact `0022` for
the process lifetime, every direct child and nested worker inherits it, and no
child changes it. Every declared output path must be absent and have an existing writable parent.
Except for section-9 ACTIVE command wrappers, successful writes use an
adjacent exclusive temporary file, `fchmod` to exact `0644`, file `fsync`,
atomic replace, and parent-directory `fsync`. ACTIVE wrappers instead use the
closed append-and-file-`fsync` protocol and never replace their prefix; newly
created runner directories use exact `0755`, independent of ambient umask.
Before a valid leaf-observation object
exists, any public-command rejection emits empty stdout and one canonical JSON
diagnostic plus LF on stderr. The diagnostic has exactly `schema`, `command`,
`code`, and `location`, with schema
`pff-draft-binding-mutation-tool-diagnostic/0.1`, command one of `preflight`,
`plan`, `run`, `import-probe`, `leaf`, `worker`, `build-wheel`, or
`install-wheel`, nullable ASCII logical location, and code
one of `ARGUMENT_INVALID`, `AUTHORITY_MISMATCH`, `CANONICAL_JSON_INVALID`,
`POPULATION_MISMATCH`, `RECIPE_INVALID`, `BOUNDARY_VIOLATION`,
`CONTROL_FAILED`, `PREFLIGHT_MISMATCH`, `PLAN_MISMATCH`, `ATTEMPT_NOT_AUTHORIZED`,
`OUTPUT_CONFLICT`, or `INTERNAL_FAILURE`. Exit is respectively 64 for argument
or authorization (`ARGUMENT_INVALID` or `ATTEMPT_NOT_AUTHORIZED`), 73 for
`OUTPUT_CONFLICT`, 70 for `INTERNAL_FAILURE`, and 65 for
every other code. Every successful or completed public command emits empty
stdout and stderr. `preflight` and `plan` success exit 0. Completed `run` exits
0 for `QUALIFIED` and 1 for `NONQUALIFYING` after writing its complete
artifacts.

Every SCRIPT subcommand, including import-probe, leaf, worker, build-wheel, and
install-wheel, compares complete `sys.orig_argv` with its exact displayed
command before semantic work. Only the optional leaf qualifier branch and the
two exact worker fixture values vary as frozen; no unlisted interpreter flag,
option, or argument is accepted.

Co-occurring public-command defects outside the preflight check sequence use
this total code precedence:
`ARGUMENT_INVALID`, `ATTEMPT_NOT_AUTHORIZED`, `BOUNDARY_VIOLATION`,
`OUTPUT_CONFLICT`, `AUTHORITY_MISMATCH`, `CANONICAL_JSON_INVALID`,
`POPULATION_MISMATCH`, `RECIPE_INVALID`, `PREFLIGHT_MISMATCH`,
`PLAN_MISMATCH`, `CONTROL_FAILED`,
then `INTERNAL_FAILURE`. Preflight-check failures instead use the exact check
order and check-local order below. Within a code elsewhere, argv/options use left-to-right argv
position; environment uses the first name in ASCII order over the expected /
actual union; logical path/authority inputs use their displayed public-command
order; JSON inputs use MANIFEST, PREFLIGHT, PLAN; populations use L, M, O;
recipes use numeric M then patch ordinal; outputs use argv order; and controls
use tool-tests, subject-suite, wheel-a, wheel-b, install, installed-import,
then L order. The first defect under those orders alone is reported.

`ARGUMENT_INVALID` location is `argv:<zero-based-index>` for an existing
malformed/unexpected member, or `option:<exact-required-token>` for the first
missing member in displayed command order, excluding the authorization
sentinel;
`ATTEMPT_NOT_AUTHORIZED` is exact `--allow-execute`;
`BOUNDARY_VIOLATION` is `environment:<ASCII-name>`, `path:<logical-token>`,
`import:<exact frozen module>`, or `call:<exact frozen callable>`;
`OUTPUT_CONFLICT` is the logical output token; `AUTHORITY_MISMATCH` is the
logical authority token or exact identity field enumerated below; `CANONICAL_JSON_INVALID` is
`<MANIFEST>`, `<PREFLIGHT>`, or `<PLAN>`; `POPULATION_MISMATCH` is `L`, `M`,
or `O`; `RECIPE_INVALID` is `<M-id>:<one-based-patch-ordinal>`,
`<M-id>:changed-path:<repo-relative-path>`, `<M-id>:source:<repo-relative-path>`,
or `<M-id>:content-root`;
`PREFLIGHT_MISMATCH` is `<PREFLIGHT>`; `PLAN_MISMATCH` is `<PLAN>`; and
`CONTROL_FAILED` is one listed control token,
or `leaf:<fixture>:<qualifier-or-null>` for the first failed L member.
`INTERNAL_FAILURE` alone requires null location. No other code/location
combination is valid.

`PREFLIGHT` is canonical JSON schema
`pff-draft-binding-mutation-preflight/0.1` with exactly `schema`, `status`,
`subject`, `authorities`, `implementation`, `runtime`, `populations`, and
`checks`. `status` is exact `PASS`. `subject` repeats section-1 commit, tree,
profile path, and profile hash using the exact manifest-subject fields.
`authorities` has exactly `qualification_profile_path`,
`qualification_profile_sha256`, `manifest_path`, and `manifest_sha256`.
`implementation` has exactly `commit`, `git_tree`, `script`, `leaf_adapter`,
`tool_tests`, and `tool_review`; each of the last four is an object with exact
`path`, `byte_length`, and `sha256`. `runtime` has the exact section-9 runtime
shape. `populations` has exactly integer `leaves`, `mutations`, and
`components`, equal respectively to 191, 181, and 205. `checks` is an array in
this exact order, every member exactly
`{"name":<name>,"status":"PASS"}`:

```text
subject_identity
authority_identity
worktree_clean
runtime_identity
canonical_manifest
population_closure
recipe_application
content_roots
direct_syntax_boundaries
tool_tests
post_control_identity
```

The checks have these complete scopes and failure diagnostics. They are
evaluated in displayed order after public argv, authorization, environment,
path-precondition, and output-conflict gates. A row's first mismatch under its
listed local order fixes the one diagnostic; a tool may not choose another
code for the same failed check.

| Check | Complete predicate and local order | Exact failure code and location |
|---|---|---|
| `subject_identity` | Every section-1 commit-object, tree-ID, subject-profile path/hash, 41-path tree population, Git mode/blob, archive process/framing, archive population/mode, and extracted-byte/blob check. Fields precede archive-global checks, then paths; paths use the first member of the expected/actual raw-UTF-8-order union. | `AUTHORITY_MISMATCH`; respectively `subject:commit`, `subject:git_tree`, `subject:profile_path`, `subject:profile_sha256`, `subject:archive` for a process/global tar failure, or `subject:path:<repo-relative-path>` |
| `authority_identity` | The tracked accepted `<PROFILE>`, immutable v0.1 profile, and `<MANIFEST>` blobs; exact subject→v0.1-authority→v0.2-authority→tool first-parent topology and per-commit path rules; observed implementation `HEAD`/tree; then exact script, leaf-adapter, tool-test, and tool-review path/mode/length/hash records. | `AUTHORITY_MISMATCH`; first of `<PROFILE>`, the v0.1 profile path, `<MANIFEST>`, `implementation:commit`, `implementation:git_tree`, or the four repository-relative artifact paths in that order |
| `worktree_clean` | Exact section-7 status output is empty and every `HEAD` path in the expected/actual raw-UTF-8-order union has the declared `100644` tree mode, regular `0644` worktree mode, and matching blob bytes; any ignored, untracked, missing, extra, symlinked, or changed member fails. | `BOUNDARY_VIOLATION`, `path:<REPO>` |
| `runtime_identity` | Exact section-7 resolved Python/Git executable identity and recheck, 442-file `<SITE>` population/root, isolated `<SETUPTOOLS>` population/root, then the four complete probe observations and derived scalar values. | `AUTHORITY_MISMATCH`; first of `<PYTHON>`, `<GIT>`, `<SITE>`, `<SETUPTOOLS>`, `python_version_probe`, `git_version_probe`, `platform_probe`, `setuptools_probe` |
| `canonical_manifest` | The complete section-3 UTF-8, framing, canonical JSON, schema, authority-row, member, type, ordering, capture, selector, alias, and value contract. | `CANONICAL_JSON_INVALID`, `<MANIFEST>` |
| `population_closure` | Every section-2 typed equality and derivation, in `L`, `M`, `O` order. | `POPULATION_MISMATCH`, the first unequal population name |
| `recipe_application` | For numeric M order: every ordered patch's anchor/count/immediate preimage/immediate postimage, then exact declared changed-path set in raw UTF-8 order, then static compilation of the four binding sources in raw UTF-8 path order. | `RECIPE_INVALID`; respectively `<M-id>:<patch-ordinal>`, `<M-id>:changed-path:<path>`, or `<M-id>:source:<path>` |
| `content_roots` | Every independently recomputed section-3 mutant content root in numeric M order. | `RECIPE_INVALID`, `<M-id>:content-root` |
| `direct_syntax_boundaries` | The complete section-10 direct-syntax AST predicate over reviewed implementation artifacts, in raw UTF-8 artifact-path then source-node order. | `BOUNDARY_VIOLATION`, `path:<repository-relative-artifact-path>` |
| `tool_tests` | The exact section-7 tool-test process exits zero and its executed-method population equals the reviewed closed set. | `CONTROL_FAILED`, `tool-tests` |
| `post_control_identity` | Immediately after tool tests: implementation HEAD commit/tree, exact empty status, every expected/actual tracked path mode/blob, then `<PROFILE>`, `<MANIFEST>`, script, adapter, tests, and review hashes, using the same orders as the earlier rows. | Commit/tree or artifact disagreement uses the corresponding `AUTHORITY_MISMATCH` location; status/path disagreement uses `BOUNDARY_VIOLATION`, `path:<REPO>` |

The exact `AUTHORITY_MISMATCH` identity locations introduced by this table are
`subject:commit`, `subject:git_tree`, `subject:profile_path`, `subject:profile_sha256`,
`subject:archive`, `subject:path:<repo-relative-path>`, every displayed logical authority token,
`implementation:commit`, `implementation:git_tree`, the four runtime-probe
names, and the four repository-relative implementation
artifact paths. The exact `BOUNDARY_VIOLATION` path locations are those shown
in the table. These additions exhaust the check-failure vocabulary; in
particular a runtime-probe disagreement cannot be reported as
`CONTROL_FAILED`, and a source content-root disagreement cannot be reported as
`AUTHORITY_MISMATCH`.

A failed preflight writes no PASS report and exits nonzero with one canonical
diagnostic on stderr. There is no failed-report variant that `run` may accept.

`PLAN` is canonical JSON schema `pff-draft-binding-mutation-plan/0.1` with
exactly `schema`, `subject`, `authorities`, `implementation`,
`preflight_sha256`, `control_leaves`, and `mutations`.
`subject`, `authorities`, and `implementation` are byte-for-byte equal to the
corresponding supplied PREFLIGHT objects.
`control_leaves` is exact manifest L order. `mutations` is exact numeric M
order; every member has exactly `id`, `content_root`, `patches`, and
`components`; `id` equals the aligned manifest ID and `content_root` equals its
exact `mutant_content_root`. `patches` is the exact manifest array. Components are in
displayed order and have exactly `killer_ordinal`, `fixture`, `qualifier`,
`expected`, and `command`; `expected` is the complete aligned manifest object,
and `command` is the complete logical leaf command spec with the qualifier
option present only when nonnull. `preflight_sha256` authenticates the complete
supplied PASS bytes. Plan generation from numeric order and from a reversed
in-memory parsed mutation array must produce identical canonical bytes.

Every `control_leaves` member has exactly `fixture`, `qualifier`, and `command`;
command is the corresponding complete command spec. The only
logical path tokens permitted in a preflight report, plan, or canonical bundle are `<REPO>`,
`<GIT>`, `<PYTHON>`, `<SCRIPT>`, `<SITE>`, `<SETUPTOOLS>`, `<PROFILE>`, `<MANIFEST>`, `<PREFLIGHT>`,
`<PLAN>`, `<JOURNAL>`, `<EVIDENCE>`, `<ENVELOPE>`, `<SUBJECT>`,
`<SUBJECT_CONTROL>`, `<SUBJECT_WHEEL_A>`, `<SUBJECT_WHEEL_B>`, `<CACHE>`,
`<TMP>`, `<ARCHIVE>`, `<WHEEL_A>`, `<WHEEL_B>`, and `<INSTALL>`. An unqualified-control cache
and temporary suffix is exact `leaf` for every clean or mutant leaf, regardless
of fixture, qualifier, mutation, or killer ordinal. A mutant import probe uses
exact suffix `import-probe`, also independent of mutant identity. The runner
performs the same reset before the first direct leaf/import-probe command and
immediately before every later such command: it removes, if present, then
recreates empty at mode `0755`, in exact order, `<CACHE>/leaf`, `<TMP>/leaf`,
`<CACHE>/import-probe`, and `<TMP>/import-probe`. The active command uses only
its aligned suffix while the other pair remains present and empty. Workers use
the child suffixes frozen in section 6
without clearing their parent during one coordinator run. No child-visible
cache, temporary, subject-root, cwd, argv, or environment value contains an M
ID, killer ordinal, expected disposition, or classification. Each contextual
`<SUBJECT>` actual basename is exact `subject-` plus 32 fresh lowercase
hexadecimal digits and likewise carries no semantic label; the external
envelope alone binds it to a context.
Other Python-child cache suffixes are exactly `probe-python-version`,
`probe-platform`, `probe-setuptools`, `tool-tests`, `subject-suite`, `wheel-a`,
`wheel-b`, `install`, and `installed-import` for the correspondingly named
commands. The tool-test command uses `PYTHONPATH=<REPO>/src:<REPO>`; subject suite uses
`<SUBJECT_CONTROL>/src:<SUBJECT_CONTROL>`; each wheel build uses its own
isolated `PYTHONPATH=<SETUPTOOLS>`; installed import uses
`PYTHONPATH=<INSTALL>`; every mutant import probe, leaf, and worker uses
`<SUBJECT>/src:<SUBJECT>:<REPO>`. These are the complete command-specific
`PYTHONPATH` choices. Python version/platform probes and the wheel installer
have no `PYTHONPATH` member. None is inferred from a parent.
No actual absolute temporary path enters PLAN.

Direct-child current directories are exact. Git inspection/archive, all three
runtime probes, and tool tests use `<REPO>`; subject suite uses
`<SUBJECT_CONTROL>`; wheel A and B use `<SUBJECT_WHEEL_A>` and
`<SUBJECT_WHEEL_B>` respectively; the reviewed wheel installer uses the precreated-empty
`<INSTALL>` and installed import then uses that resulting populated directory;
import-probe, leaf, and worker use the contextual `<SUBJECT>`. `<WHEEL_A>`, `<WHEEL_B>`, and `<INSTALL>` are
precreated empty, and a corresponding command rejects a preexisting member or
any output beyond its exact declared wheel/install population.

Every Git child receives exactly `LANG=C`, `LC_ALL=C`, `TZ=UTC`,
`GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`,
`GIT_NO_REPLACE_OBJECTS=1`, `GIT_CONFIG_COUNT=1`,
`GIT_CONFIG_KEY_0=core.fsmonitor`, `GIT_CONFIG_VALUE_0=false`, and
`GIT_OPTIONAL_LOCKS=0`. Every non-leaf
Python child receives exactly `LANG=C`, `LC_ALL=C`, `TZ=UTC`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0`, `PYTHONUTF8=1`,
`PYTHONNOUSERSITE=1`, `PYTHONPYCACHEPREFIX=<CACHE>/<case-id>`, and
`TMPDIR=<TMP>/<case-id>`, plus only the command-specific `PYTHONPATH` stated
above. Every case-specific temporary
directory is precreated empty and is the only temporary directory writable by
that child. Wheel-build and install children additionally receive exact
`SOURCE_DATE_EPOCH=315532800`. The setuptools probe and wheel builds receive
exact `SETUPTOOLS_USE_DISTUTILS=local`; wheel builds additionally receive
`HOME=<TMP>/<case-id>/home`, `XDG_CONFIG_HOME=<TMP>/<case-id>/xdg`, and
`PYTHONUSERBASE=<TMP>/<case-id>/userbase`, each precreated empty. No child
inherits another variable.

`<SITE>` is authenticated without importing from it. Its accepted source
population is every regular non-symlink file below exact directories
`setuptools/`, `setuptools-83.0.0.dist-info/`, and `_distutils_hack/`, relative to `<SITE>`, except
any path with a `__pycache__` component or `.pyc` suffix. There are exactly 442
files, each mode `0644`. In raw UTF-8 path order, each row contributes
`UTF8(path)`, NUL, four-digit mode, NUL, minimal decimal byte length, NUL, the
64 lowercase file-digest digits, and LF after prefix
`PFF_SETUPOOLS_RUNTIME_ROOT_V1\0`. SHA-256 of that preimage is exact
`sha256:3d4007f60bb4dc9ae7acbe32d9a794cb0cddbe4641a5cc6cb7fd4658b4fb9b0b`.
An absent, extra, nonregular, symlinked, wrong-mode, or differently hashed
member fails preflight.

Before its package probe or wheel controls, the runner copies exactly that
authenticated population into a fresh empty `<SETUPTOOLS>` root under its
declared temporary root, creates only derived directories at mode `0755`, and
recomputes the same content root. It
rechecks all 442 member modes/lengths/hashes plus the content root immediately before
the setuptools probe and each of the two build spawns, and once after both
builds. Only this isolated copy, never the broader
`<SITE>`, enters a child `PYTHONPATH`. The build wrapper installs traps on
exact `subprocess.Popen`, `run`, `call`, `check_call`, `check_output`,
`getoutput`, and `getstatusoutput`; exact `os.system`, `fork`, `forkpty`,
`posix_spawn`, `posix_spawnp`, `spawnl`, `spawnle`, `spawnlp`, `spawnlpe`,
`spawnv`, `spawnve`, `spawnvp`, and `spawnvpe`, before importing
`setuptools.build_meta`; the reviewed exact setuptools bytes have no direct
`fork`, `_posixsubprocess`, or other bypass. It calls `build_wheel` once in the
exact source cwd and rejects any child process, second wheel, wrong filename,
or output outside its source/cache/temp/wheel roots. Thus wheel building has no
unrecorded PEP-517 helper descendant.

Those environment and envelope rules apply to processes spawned directly by
the runner. The authenticated subject and tool suites may themselves spawn
only the descendants already fixed by their exact reviewed test source; their
parent observation retains the suite's complete stdout/stderr, but descendants
are not misrepresented as direct-runner envelope rows. The special leaf-worker
boundary remains the separately frozen exception in section 6.

The accepted execution runtime for v0.2 is exact CPython `3.12.13` on
`sys.platform == "linux"` and `platform.machine() == "x86_64"`, with
setuptools `83.0.0` and Git `2.51.1`. Every Python command uses `-s -S` before
`-B`, so neither system/user site initialization nor
`sitecustomize`/`usercustomize` executes. Preflight runs these exact probe
argvs from `<REPO>` with the fixed child environments and records a complete
section-9 command observation for each:

```text
<PYTHON> -P -s -S -B --version
<GIT> --version
<PYTHON> -P -s -S -B -c "import platform,sys; print(sys.implementation.name); print(platform.python_version()); print(sys.platform); print(platform.machine())"
<PYTHON> -P -s -S -B -c "import setuptools; print(setuptools.__version__)"
```

The first, second, third, and fourth stdout byte strings are respectively
`Python 3.12.13\n`, `git version 2.51.1\n`,
`cpython\n3.12.13\nlinux\nx86_64\n`, and `83.0.0\n`. Every stderr is
empty and every termination is exact exit zero. The two Python `-c` probes and
the Python version probe use the exact environments above; the setuptools
probe alone has `PYTHONPATH=<SETUPTOOLS>`. The Git probe uses the exact
Git-child environment. The scalar runtime fields must equal the corresponding
parsed probe values. A later runtime requires a new
qualification-profile version rather than an unrecorded substitution.

The implementation gate and `run`'s zero-attempt controls each run this exact
command from clean tool commit root `<REPO>`, with
`PYTHONPATH=<REPO>/src:<REPO>` and the other fixed child values:

```text
<PYTHON> -P -s -S -B -m unittest -v tests.test_binding_mutation_qualification
```

The test module contains an exact closed expected-method set and fails if
unittest dispatch executes a different set. Preflight includes the exact
section-10 direct-syntax AST inspection; the independently reviewed
`full_boundary` result covers its explicitly deferred dataflow cases. There is
no informal third inspection.

Each public preflight derivation spawns this tool-test command exactly once.
For `run`, the observation produced by its one internal preflight recomputation
is also `controls.tool_tests`; `run` does not spawn a second duplicate tool-test
control. Runtime probes and the direct-syntax check are likewise the single
observations from that recomputation. `plan` and the standalone `preflight`
command perform their own zero-attempt derivations, but their raw child output
does not pretend to be part of a later run envelope.

Both unittest controls use one closed parser over the complete retained
CPython-3.12.13 process bytes; no implementation parses human output by
heuristic. Standard output must be empty. Standard error must be strict UTF-8
and equal this byte grammar, where `N` is positive:

```text
N progress lines
"\n"
"----------------------------------------------------------------------\n"
"Ran " + minimal-decimal-N + " tests in " + DIGIT+ + "." + DIGIT DIGIT DIGIT + "s\n"
"\n"
"OK\n"
```

Each progress line is exact ASCII
`<short> (<test-id>) ... ok\n`, where `short` matches
`[A-Za-z_][A-Za-z0-9_]*`, `test-id` matches
`[A-Za-z_][A-Za-z0-9_.]*`, and `short` equals the suffix of `test-id` after its
last dot. Every dispatched test must have null `shortDescription()`, so no
description continuation line is permitted. The separator has exactly 70
hyphen bytes. The runner extracts `executed` solely from those progress lines
in byte order, assigns each status `PASS`, requires the line count and summary
N agree, and derives counts as run N with the other four counts zero. Any other
byte, invalid UTF-8, repeated/missing test ID, non-`ok` outcome, singular
summary spelling, duration with other than three decimal digits, or trailing
data is the aligned `CONTROL_FAILED` before attempts. The tool control also
requires the extracted IDs equal its independently reviewed closed expected
set; the subject control additionally requires N equal 254. Thus the same raw
bytes have exactly one suite projection, while the nondeterministic three-digit
duration remains only in the envelope.

Before any mutant attempt, `run` creates a pristine subject archive
`<SUBJECT_CONTROL>` with no tool overlay and runs the README discovery command
there:

```text
<PYTHON> -P -s -S -B -m unittest discover -s tests -v
```

That command uses exact
`PYTHONPATH=<SUBJECT_CONTROL>/src:<SUBJECT_CONTROL>`. It must report exactly
254 executed tests and zero failures, errors, skips, or
unexpected successes. It then creates two other independently authenticated
fresh archives `<SUBJECT_WHEEL_A>` and `<SUBJECT_WHEEL_B>`. Each must equal the
subject tree immediately before its one build. It runs respectively:

```text
<PYTHON> -P -s -S -B <SCRIPT> build-wheel --source-root <SUBJECT_WHEEL_A> --setuptools-root <SETUPTOOLS> --wheel-dir <WHEEL_A>
<PYTHON> -P -s -S -B <SCRIPT> build-wheel --source-root <SUBJECT_WHEEL_B> --setuptools-root <SETUPTOOLS> --wheel-dir <WHEEL_B>
<PYTHON> -P -s -S -B <SCRIPT> install-wheel --wheel <WHEEL_A>/poietics-0.1.0.dev0-py3-none-any.whl --target <INSTALL>
<PYTHON> -P -s -S -B -c "import poietics; print(poietics.__file__)"
```

The import command runs with `PYTHONPATH=<INSTALL>` and must emit the one
actual install path corresponding to logical
`<INSTALL>/poietics/__init__.py` plus LF and empty stderr. The two wheel files
must be byte-identical and have identical member paths, modes, and uncompressed
member hashes. `install-wheel` uses only `zipfile` and ordinary filesystem
operations from the authenticated Python runtime and imports or executes no
wheel member. It requires every decoded member name be exact ASCII matching
`[A-Za-z0-9._/-]+` and rejects duplicates, backslashes, NUL,
absolute paths, empty/`.`/`..` components, symlinks, devices, a compression
method other than ZIP method 0 (`STORED`) or 8 (`DEFLATED`), encrypted
members, and any mode other than regular `0644`/`0664` or derived directory
`0755`. It extracts every and only wheel member, verifies
every resulting byte and mode, and creates no `INSTALLER`, `RECORD`, direct-URL,
bytecode, or other installer-authored file; a wheel-owned `.dist-info/RECORD`
is retained byte-for-byte and is not rewritten. The canonical installed-file
population is therefore exactly every regular wheel member at its path
relative to `<INSTALL>`, including the complete `.dist-info` population, and
its hashes equal the wheel member table. The build-mutated subject roots are never reused for a suite,
control, or mutant. Raw build/import output and actual paths are retained only
in the nondeterministic envelope; the canonical evidence retains exact exit
state, logical path projection, wheel hash, member projection, and installed
file hashes.

The reviewed singleton tool and leaf adapter then execute every member of `L`
once against the fresh clean control archive, and every result must be exact
`PASS`. Immediately after the last leaf control and before the first journal
event, `run` repeats implementation HEAD/tree, exact empty status, every
tracked path mode/blob, and `<PROFILE>`/`<MANIFEST>`/script/adapter/test/review
hash checks in the exact `post_control_identity` order. The result is retained
as `controls.pre_attempt_identity`; any difference uses that row's exact
authority/boundary diagnostic. A failed semantic control uses its ordered
`CONTROL_FAILED` diagnostic; an AST, preflight, plan, or identity defect uses
its already frozen diagnostic. Every such failure stops with zero mutant attempts,
exit 65, creates
no journal, evidence bundle, or final execution envelope, and leaves the three
declared output paths absent. Any invocation-private raw control log is not a
qualification artifact and may be discarded; because no attempt began, a new
public invocation with new empty cache/temp roots may repeat the controls.

`plan` parses the canonical manifest, derives numeric M order and sequence O,
and emits canonical JSON containing all recipes, content roots, leaf commands,
and logical environments. During `run`, two fresh parses build the plan once
from ascending input and once from an independently reversed in-memory mutation
array, never reversed manifest bytes; both canonical results must equal the
supplied PLAN bytes.

After all controls pass, mutants execute in numeric order. Every displayed
component for one composite killer executes in order against that same fresh
mutant copy. There are no retries within one campaign. A nonpassing mutant does
not stop enumeration: all remaining components and mutants execute so
`classified_M` and `classified_O` can close. Construction infrastructure
failure assigns infrastructure outcomes to every unrun component for that
mutant and continues with the next fresh mutant. A process interruption before
the last seal writes an ACTIVE journal; later terminal-window states are frozen
in section 9, and no interruption creates a final evidence bundle. v0.2 forbids resume: that
campaign is abandoned. A separately authorized new campaign must use a new
campaign ID, restarts from zero, and retains rather than overwrites the
abandoned files.

After M181's final ordinary `COMPONENT_SEALED` or final construction-failure
`COMPONENT_SYNTHETIC_SEALED`, with every aligned component classification
retained but before the M181 mutant seal, `run` repeats the exact
`post_control_identity` whole-tree,
authority, and artifact scan. A mismatch uses that check's frozen diagnostic,
leaves the journal and envelope ACTIVE, writes no bundle, does not persist the
final mutant seal, abandons the campaign ID, and cannot be classified as a
component outcome. A pass is retained as `controls.post_attempt_identity` and
alone authorizes the final mutant seal.

The journal is canonical JSON schema
`pff-draft-binding-mutation-journal/0.1` with exactly `schema`, `campaign_id`,
`status`, `subject`, `criteria`, `tool_subject`, `preflight_sha256`,
`plan_sha256`, and `events`. `subject` is the manifest subject; `criteria` has
exactly `qualification_profile_sha256` and `manifest_sha256`; `tool_subject`
has exactly `commit` and `git_tree`; and the two report hashes bind the supplied bytes.
These immutable headers are written before the first event. Status is `ACTIVE`
or `COMPLETE`. After all controls and the pre-attempt identity check pass, `run`
first atomically creates this ACTIVE journal with exact empty `events`, then
atomically creates the ACTIVE envelope log defined in section 9, and only then
atomically persists the M01 `MUTANT_ATTEMPT_STARTED` event. Events are in append order and have exactly `sequence`, `event`,
`mutant_id`, and `killer_ordinal`; sequence equals the consecutive zero-based
array position with no gap or duplicate. Event is
`MUTANT_ATTEMPT_STARTED`, `COMPONENT_DISPATCH_STARTED`, `COMPONENT_SEALED`,
`COMPONENT_SYNTHETIC_SEALED`, or `MUTANT_ATTEMPT_SEALED`. Mutant events require
null ordinal; component events require the positive aligned ordinal. The mutant
start is atomically persisted before archive/construction, and its final seal
follows construction, every component record, and classification. For a
constructed mutant, each dispatch start is persisted before spawn and its seal
immediately after the corresponding envelope row is durable and semantic
interpretation completes, with no intervening event for another
component. Construction failure emits one synthetic seal per component without
dispatch, then the mutant seal. Thus one M member, not one component, is the
one-use controlled attempt, and an interruption during construction leaves a
durable unsealed mutant start. The whole journal is
rewritten through an adjacent exclusive temporary file, file `fsync`, atomic
replace, and parent-directory `fsync`. `run` accepts no journal as input and
refuses if journal, evidence, or envelope output already exists.

Status is COMPLETE exactly when the event array contains, for every M in
numeric order, one start, then either every component's adjacent dispatch/seal
pair in killer order or every component's synthetic seal after construction
failure, then one mutant seal, with all 181 mutant seals present and no other
event. Every other retained prefix is ACTIVE. The final evidence may bind only
a COMPLETE journal.

## 8. Classification and precedence

Classification is first per component occurrence in O and then per mutant.
Component classes are exact `EXPECTED_PASS`, `EXPECTED_MISMATCH`,
`MISSING_MISMATCH`, `WRONG_REASON`, `UNREACHABLE`, `TIMEOUT`, and
`INFRASTRUCTURE`. They are assigned as follows:

```text
invalid construction, malformed output, exit/status mismatch, signal -> INFRASTRUCTURE
valid nested WORKER_INFRASTRUCTURE                             -> INFRASTRUCTURE
runner-enforced timeout                                             -> TIMEOUT
valid nested WORKER_TIMEOUT                                    -> TIMEOUT
valid nested WORKER_SETUP_FAILURE                          -> UNREACHABLE
valid SETUP_FAILURE or TARGET_UNREACHABLE                            -> UNREACHABLE
expected PASS, actual exact PASS                                    -> EXPECTED_PASS
expected MISMATCH, actual exact PASS                                -> MISSING_MISMATCH
valid TARGET_MISMATCH with first unequal PROJECTION_ERROR           -> WRONG_REASON
expected MISMATCH, exact TARGET_MISMATCH and exact frozen signature -> EXPECTED_MISMATCH
any other valid TARGET_MISMATCH                                     -> WRONG_REASON
```

The clean-control transcript is the accepted `T_clean` oracle for that exact
leaf. For an expected `PASS`, the mutant transcript must equal `T_clean`
completely. For an
expected `MISMATCH`, the runner independently compares entries in manifest
selector order: every entry before the named selector must equal `T_clean`; the named
selector must be the first inequality; and its derived mismatch kind and exact
exception class must equal the aligned manifest component. The result object's
`observable`, `expected`, and `observed` must equal that independently located
selector and its two entry values. All suffix entries remain retained, whether
VALUE or NOT_REACHED. The exact atomic patch and unchanged-tree proof establish
the forbidden mechanism; no golden mutant output is invented.

Each reviewed named selector is one atomic accepted assertion projection; its
program retains the complete operand needed for the fixture's exact code,
path, source, target, detail, or gate assertion. An earlier/different selector,
kind, or class is `WRONG_REASON`, including a wrong field whose first
inequality belongs to another selector. Once the frozen selector is the first
inequality, any unequal operand is the named assertion's failure; qualification
does not invent a golden value for the forbidden mutant. A result label that
disagrees with the transcript is likewise wrong reason. A wrong fixture, qualifier, JSON member
population, exit code for the emitted status, extra stdout, nonempty stderr,
signal, or invalid typed value is infrastructure, not a semantic kill. A
clean-control non-PASS stops before attempts and is not a mutant class.

Mutant precedence from highest to lowest is
`INFRASTRUCTURE_FAILURE`, `TIMEOUT`, `UNREACHABLE_PROBE`,
`WRONG_REASON_KILL`, `SURVIVOR`, then `PREDICTED_KILL`. A mutant receives the
first applicable class: any component in the corresponding infrastructure,
timeout, unreachable, or wrong-reason class; otherwise any
`MISSING_MISMATCH` yields `SURVIVOR`; otherwise `PREDICTED_KILL` only when its
entire component vector equals the frozen `EXPECTED_PASS`/`EXPECTED_MISMATCH`
vector. Every
manifest row has at least one expected mismatch, so an all-PASS vector can
never qualify. Additional unregistered tests are never run to rescue or
reclassify a mutant.

The sole passing aggregate is:

```text
PREDICTED_KILL = M
|PREDICTED_KILL| = 181
WRONG_REASON_KILL = SURVIVOR = UNREACHABLE_PROBE = TIMEOUT = INFRASTRUCTURE_FAILURE = {}
```

All class sets are pairwise disjoint and their union equals `M`.

## 9. Evidence bundle

The canonical bundle uses section-3 JSON and exact schema
`pff-draft-binding-mutation-evidence/0.2`. Its top-level object has exactly:

```text
schema
status
campaign_id
subject
criteria
tool_subject
runtime
controls
populations
mutants
aggregates
pre_run_reviews
journal_sha256
execution_envelope_sha256
```

`status` is `QUALIFIED` exactly when the aggregate gate passes, otherwise
`NONQUALIFYING`. `campaign_id` is section 7's exact value. `subject` is the
four-field manifest subject object. `criteria` has exactly
`qualification_profile_path`, `qualification_profile_sha256`, `manifest_path`,
`manifest_sha256`, `preflight_sha256`, and `plan_sha256`. `tool_subject` has
exactly `commit`, `git_tree`, and `artifacts`; artifacts are UTF-8-path-order
objects with exactly `path`, `byte_length`, and `sha256` for the script, leaf
adapter, tool tests, and pre-run tool-review record.
`qualification_profile_path` is exact
`docs/PFF_DRAFT_BINDING_MUTATION_QUALIFICATION_PROFILE_V0.2.md` and
`manifest_path` is exact
`docs/PFF_DRAFT_BINDING_MUTATION_MANIFEST_V0.1.json`; repository-owned artifact
paths are likewise repository-relative strict UTF-8, while runtime-created
paths use only the logical tokens below. `tool_subject` is exactly the
PREFLIGHT `implementation` projection: its commit/tree are equal and its four
artifacts are the corresponding script, leaf-adapter, tool-test, and
tool-review objects in raw UTF-8 path order.
`journal_sha256` binds the complete canonical COMPLETE journal at `<JOURNAL>`.
The journal `campaign_id` and `subject` equal the bundle members; its
`criteria.qualification_profile_sha256` and `criteria.manifest_sha256` equal
the same-named bundle-criteria members; its `tool_subject.commit` and
`tool_subject.git_tree` equal the same-named bundle-tool-subject members; and
its top-level `preflight_sha256` and `plan_sha256` equal the same-named
bundle-criteria members. Its sealed event population equals the bundle's
attempted/classified mutation and component populations. No larger journal
object is asserted byte-equal to a differently shaped bundle object.

Every field named `sha256` or ending `_sha256` is exact `sha256:` plus 64
lowercase hexadecimal digits. Every path string is strict UTF-8 with no NUL;
an array declared in path order uses increasing raw UTF-8 byte order. Every
mode is a four-digit ASCII octal string such as `0644`. Every byte length,
population count, sequence, ordinal, and executed-test count is a nonnegative
JSON integer, except an explicitly one-based ordinal is positive.

`runtime` has exactly `python`, `git`, `setuptools`,
`python_implementation`, `python_version`, `sys_platform`, `machine`,
`python_version_probe`, `git_version_probe`, `platform_probe`, and
`setuptools_probe`. `python` and `git` each have exactly
`logical_path`, `byte_length`, and `sha256`. Each probe is a complete command
observation for its corresponding section-7 argv. Runtime strings are strict
UTF-8 projections of the exact probe bytes and must have the section-7 values;
invalid UTF-8 or disagreement fails preflight. `python.logical_path` is exact
`<PYTHON>`, `git.logical_path` is exact `<GIT>`, and the whole runtime object is
byte-for-byte equal to PREFLIGHT `runtime`. `setuptools` has exactly
`source_logical_path`, `isolated_logical_path`, `version`, `content_root`, and
`files`; the paths are exact `<SITE>` and `<SETUPTOOLS>`, version is exact
`83.0.0`, content root is the section-7 value, and files are its exact 442
raw-UTF-8-path-order member objects with fields `path`, `mode`, `byte_length`,
and `sha256`.

A byte blob is exactly
`{"byte_length":<nonnegative integer>,"hex":"<lowercase even hex>","sha256":"sha256:<64 lowercase hex>"}`;
its three values must agree over the complete bytes. No output is assumed to be
UTF-8 and no byte stream is truncated. A termination is exactly
`{"kind":"EXIT","value":<0..255>}`,
`{"kind":"SIGNAL","value":<positive integer>}`, or
`{"kind":"TIMEOUT","value":null}`. A command spec has exactly `argv`, `cwd`,
`environment`, and `stdin`. `argv` is a nonempty string array and no member
contains NUL. Environment is an ASCII-name-sorted array of exact
`{"name":<string>,"value":<string>}` objects; names are unique, match
`[A-Z_][A-Z0-9_]*`, and contain neither NUL nor `=`, and values contain no NUL.
In a canonical logical spec, `cwd` is one exact logical-token path
frozen in section 7, while in an envelope actual spec it is that materialized
absolute path; stdin is the empty byte blob.
A command observation has exactly
`spec`, `termination`, `stdout`, and `stderr`, using those types. Leaf control
and mutant leaf logical specs come byte-for-byte from PLAN. Every other
canonical logical spec is constructed from the exact argv, cwd, and
environment frozen in sections 1, 6, and 7; none is invented by PLAN.

`controls` has exactly `tool_tests`, `preflight`, `plan_ascending`,
`plan_reversed`, `subject_suite`, `wheel_a`, `wheel_b`, `install_import`,
`leaf_controls`, `pre_attempt_identity`, and `post_attempt_identity`. `preflight` is an artifact record with exactly `path`,
`byte_length`, `sha256`, and `status`, where status is `PASS`.
`plan_ascending` and `plan_reversed` are derivation records with exactly
`mode`, `input_manifest_sha256`, `output_sha256`, and `byte_length`; mode is
respectively `ASCENDING` or `REVERSED`, and output hash/length must be equal.
They do not pretend that the in-process reversed derivation was a spawned
command. Both `input_manifest_sha256` values equal
`criteria.manifest_sha256`, and both `output_sha256` values equal
`criteria.plan_sha256`.

A non-leaf process projection has exactly `spec` and `termination`, omitting
raw streams that live in the envelope. A suite control has exactly `process`,
`executed`, and `counts`; `executed` is the exact dispatch-order array of
`{"test_id":<string>,"status":"PASS"}` and `counts` has exactly `run`,
`failures`, `errors`, `skips`, and `unexpected_successes`. A wheel control has
exactly `process`, `wheel_sha256`, and `members`; members are raw-UTF-8-path-order
objects with exact `path`, `mode`, `byte_length`, and `sha256`. `install_import`
has exactly `install_process`, `import_process`, `logical_module_path`, and
`installed_files`; both process members are non-leaf process projections and
installed files use the same raw-UTF-8-path-order member object shape.
`logical_module_path` is exact `<INSTALL>/poietics/__init__.py`. `leaf_controls`
is exact L order; each object has exactly
`fixture`, `qualifier`, and `observation`. A leaf observation has exactly
`process`, `parse_status`, `leaf_observation`, and `result`; `process` is a
complete command observation, parse status is `VALID`, `leaf_observation` is
the exact parsed child object, and `result` is the runner-derived exact PASS
object bound to that control's `T_clean`.
`tool_tests` and `subject_suite` are suite controls; `wheel_a` and `wheel_b` are
wheel controls. In each final suite control, `counts.run` equals
`len(executed)` and failures, errors, skips, and unexpected successes are exact
zero. Every tool-test, subject-suite, wheel-A, wheel-B, install, and
installed-import process termination is exact `{"kind":"EXIT","value":0}`;
any other termination is its ordered `CONTROL_FAILED` token before attempts.
The suite counts, wheel/member predicates, and installed-file predicates remain
additional mandatory gates rather than substitutes for process success.
Control-token ownership is exact: a tool or subject suite process/parser/set
failure is respectively `tool-tests` or `subject-suite`; a wheel's own process,
filename, member, or source-root check is `wheel-a` or `wheel-b`; cross-wheel
byte/member inequality and the final post-build `<SETUPTOOLS>` recheck are
`wheel-b`; install extraction, installed member projection, or
installed-files-versus-wheel inequality is `install`; and the installed module
path/output/import check is `installed-import`. Leaf failures use the aligned
leaf token. No postcondition may be assigned to the earlier successful member
of a pair.
`preflight.path` is exact `<PREFLIGHT>` and its hash/length equal the supplied
bytes and `criteria.preflight_sha256`. Tool-test, subject-suite, wheel,
install, and import process specs equal their corresponding exact section-7
logical specs. Each leaf-control process spec equals its aligned PLAN control
command. The two wheel member arrays and hashes are equal, and
`installed_files` equals that wheel's complete regular-member projection.

`pre_attempt_identity` has exactly `status`, `implementation`,
`qualification_profile_sha256`, and `manifest_sha256`. Status is `PASS`;
implementation is byte-for-byte `tool_subject`; and the two hashes equal the
corresponding `criteria` members. It is derived only from the final section-7
whole-tree/artifact recheck after all leaf controls and before the first
journal event.

`post_attempt_identity` has the identical four-field shape and values. It is
derived only from the final section-7 whole-tree/artifact recheck after the
last M181 ordinary or synthetic component seal and before the M181 mutant seal. A final bundle may
exist only when both identity records are exact PASS and byte-for-byte equal.

Unittest duration lines, build cache paths, actual install paths, and other
nondeterministic raw control output do not enter those projections. They are
retained in the execution envelope. Leaf stdout/stderr remain in the canonical
bundle because their exact bytes are asserted behavior.

`populations` has exactly `defined_leaves`, `executed_control_leaves`,
`defined_mutations`, `attempted_mutations`, `constructed_mutations`, `classified_mutations`,
`defined_components`, `dispatched_components`, and `classified_components`.
Leaf keys are exact `{"fixture":...,"qualifier":...}` objects; mutation arrays
contain numeric-order IDs; component arrays contain numeric/display-order
objects with exactly `mutant_id`, `killer_ordinal`, `fixture`, and `qualifier`.
The equalities in section 2 must hold byte-for-byte between aligned arrays.

`mutants` is exact numeric M order. Every object has exactly `id`,
`transformation`, `patches`, `construction`, `mutant_content_root`,
`components`, and `classification`. `patches` is copied from the authenticated
manifest; `id`, `transformation`, and `mutant_content_root` equal the same
aligned manifest members. `construction` has exactly `status`, `changed_paths`,
`computed_content_root`, `import_probe`, and `diagnostic`; status is `PASS` or
`FAIL`. `changed_paths` is always the complete raw-UTF-8-path-order array of
tracked paths whose current bytes differ from the subject when construction
seals; `ARCHIVE` has the exact empty array because no candidate tree exists.
PASS has exactly the distinct declared patch paths, the expected content
root, a complete successful import-probe command observation, and null
diagnostic. That probe's logical spec equals the exact section-6 import-probe
spec for the mutant context. On FAIL, `computed_content_root` is null if root calculation was not
reached and otherwise retains the observed root; `import_probe` is null unless
the probe was spawned and otherwise retains its complete observation; and
`diagnostic` is nonnull with exact fields `code`, `path`, and
`patch_ordinal`. Code is one of `ARCHIVE`, `ANCHOR`, `PREIMAGE`, `POSTIMAGE`,
`CONTENT_ROOT`, `UNDECLARED_CHANGE`, `SYNTAX`, or `IMPORT`. `ARCHIVE`,
`CONTENT_ROOT`, and `IMPORT` require null path and ordinal; `ANCHOR`,
`PREIMAGE`, and `POSTIMAGE` require the exact manifest path and positive patch
ordinal; `UNDECLARED_CHANGE` requires the first offending path in raw UTF-8
order and null ordinal; and `SYNTAX` requires the exact source path and null
ordinal. `ARCHIVE`, `ANCHOR`, `PREIMAGE`, `POSTIMAGE`, and
`UNDECLARED_CHANGE` require null computed root and import probe; `CONTENT_ROOT`
requires the observed nonnull root and null probe; `SYNTAX` requires the exact
expected root and null probe; and `IMPORT` requires the exact expected root and
nonnull probe observation. No other nullability combination is valid.

Every mutant component has exactly `killer_ordinal`, `fixture`, `qualifier`,
`expected`, `observation`, and `component_class`. `expected` is the aligned
manifest component. Its ordinal/fixture/qualifier and logical command equal the
aligned PLAN component. `observation` is null only when construction failed;
otherwise it has exact `process`, `parse_status`, `leaf_observation`, and
`result`. `process` is a complete command observation whose logical `spec`
equals that planned command byte-for-byte. `parse_status` is one of `VALID`, `NOT_PARSED`,
`STDERR_NONEMPTY`, `STDOUT_SHAPE`, `INVALID_JSON`, `DUPLICATE_KEY`,
`NONCANONICAL_JSON`,
`WRONG_MEMBERS`, `STATUS_EXIT_MISMATCH`, `WORKER_TIMEOUT`, or
`WORKER_INFRASTRUCTURE`, or `WORKER_SETUP_FAILURE`. `leaf_observation` and
`result` are both nonnull exactly for `VALID`; for `WORKER_SETUP_FAILURE` the
exact worker-failure object and the derived ordinary outer SETUP_FAILURE result
are both nonnull; for `WORKER_TIMEOUT` or `WORKER_INFRASTRUCTURE` the exact
worker-failure object is nonnull and result is null; otherwise both are null. A valid parsed raw
`OBSERVED`/`SETUP_FAILURE` object is interpreted against the aligned clean
control into the retained result; the child never supplies that result.
Timeout or signal fixes `NOT_PARSED` and both null without inspecting output. For an
exit, precedence is nonempty stderr, stdout
shape/final-LF, strict JSON decoding, duplicate-key scan, canonical reserialization,
member/type validation, then
raw status/exit consistency (`OBSERVED`/0, `SETUP_FAILURE`/2, or exact
`WORKER_FAILURE`/4). A valid worker failure derives the corresponding worker
parse status from `failure_kind` before component classification:
`TIMEOUT` maps to `WORKER_TIMEOUT`, `INFRASTRUCTURE` to
`WORKER_INFRASTRUCTURE`, and `SETUP_FAILURE` to `WORKER_SETUP_FAILURE`. For an `EXIT` termination, the
check order in the preceding sentence is the total precedence; the enum-list
order is not precedence. `STDOUT_SHAPE` is the exact byte predicate: stdout
has length at least two, its last byte is LF, the preceding payload is
nonempty, and that payload contains no raw LF byte. Failure of any clause is
`STDOUT_SHAPE`; no brace or top-level JSON type is inspected at this stage. The runner then strictly
decodes UTF-8 and the complete RFC 8259 JSON grammar into an ordered-pairs
representation, without yet collapsing object members. Invalid UTF-8,
incomplete or extra JSON syntax, or non-JSON `NaN`, `Infinity`, or `-Infinity`
syntax is `INVALID_JSON`. Only after that complete parse succeeds, it scans
every object depth-first in source member order; any repeated key in one object
is `DUPLICATE_KEY`. It then serializes the duplicate-free value with the exact
section-3 canonical JSON rules and appends one LF; byte inequality with stdout
is `NONCANONICAL_JSON`. A decoded negative integer, float, unpaired surrogate,
or value outside section 3's canonical domain is also
`NONCANONICAL_JSON`, because no canonical serialization exists. Only
byte-equal canonical JSON proceeds to exact member
and typed-value validation. These statuses are mutually exclusive and the
preceding `EXIT` check order is their total precedence. For every status other
than `VALID` and the three worker statuses, both `leaf_observation` and `result`
are null as already required above.
`component_class` is one section-8 component class.
`classification` is one section-8 mutant class.

`aggregates` has exactly the six mutant-class names, each mapping to a
numeric-order ID array. The arrays are pairwise disjoint and their concatenated
set equals M. `pre_run_reviews` has exactly `criteria_acceptance` and
`tool_implementation`. `criteria_acceptance` has exactly
`qualification_profile_sha256`, `architecture`, `determinacy`, and `criteria`,
with all three results exact `CLEAN`. `tool_implementation` has exactly `path`,
`byte_length`, `sha256`, and `status`, with status `CLEAN`. It never claims a
post-run review. The criteria-acceptance hash equals
`criteria.qualification_profile_sha256`; the tool-implementation artifact is
byte-for-byte the PREFLIGHT/tool-subject `tool_review` path, length, and hash.

[N] While a campaign is ACTIVE, `<ENVELOPE>` is not a JSON envelope object. It
is one append-only canonical JSON Lines log. Line 0 is a HEADER object with
schema `pff-draft-binding-mutation-execution-envelope-log/0.2` and exactly
`schema`, `status`, `campaign_id`, `subject`, `criteria`, `tool_subject`,
`preflight_sha256`, `plan_sha256`, `path_map`, and `started_at`. Status is exact
`ACTIVE`. The campaign, identity, and hash members equal the journal headers; `subject`
is the manifest subject; `criteria` has exactly
`qualification_profile_sha256` and `manifest_sha256`; and `tool_subject` has
exactly `commit` and `git_tree`. The path map has the complete population and
order below. The HEADER is one section-3 canonical JSON object followed by one
LF byte; the LF is part of the record and every digest preimage.

[S] Immediately before the first runner-direct control spawn, `run` samples
`clock_gettime_ns(CLOCK_REALTIME)`, floors to the containing microsecond, and
formats that UTC instant as `started_at`. It buffers the immutable identity
members, that time, the path map, and complete control observations in private
invocation storage while controls run. A control failure leaves `<JOURNAL>`,
`<ENVELOPE>`, and `<EVIDENCE>` absent. Only after all controls pass and the
empty ACTIVE journal is durable, and before M01's start event, it creates the
ACTIVE log with the buffered complete command population.

[N] To create the log, the runner serializes the HEADER line, writes it to one
adjacent exclusive temporary regular file, applies exact mode `0644`, writes
the complete line, file-`fsync`s it, renames it atomically to the still-absent
`<ENVELOPE>`, and `fsync`s its parent directory. Any collision at the
target is `OUTPUT_CONFLICT`; any primitive failure is `INTERNAL_FAILURE`. The
HEADER digest is `sha256:` plus lowercase SHA-256 over its complete canonical
line including LF. That digest initializes both the current chain tip and the
predecessor for command sequence zero. After directory `fsync`, the runner
`lstat`s the target and retains its device, inode, exact mode `0644`, and HEADER
line length as the append identity; disagreement is `INTERNAL_FAILURE`.

[N] Every subsequent log record is a wrapper object with schema
`pff-draft-binding-mutation-execution-envelope-command/0.2` and exactly
`schema`, `sequence`, `previous_record_sha256`, and `command`. `sequence` is
the consecutive zero-based wrapper position. `previous_record_sha256` is the
SHA-256 identity of the immediately preceding complete line including LF: the
HEADER digest for sequence zero and the preceding wrapper digest thereafter.
`command` is byte-for-byte the pre-existing COMPLETE-envelope command-row
object defined below, including its own `sequence`; wrapper `sequence` must
equal `command.sequence`. This wrapper choice preserves every existing command
observation and join without stripping or repurposing a command-row field.

[N] A wrapper is one section-3 canonical JSON object followed by one LF. For
each complete direct-child observation after log creation, the runner writes
the complete wrapper bytes through an append-only descriptor for the existing
regular non-symlink `<ENVELOPE>`, then file-`fsync`s that descriptor. It does
not seek, truncate, replace, or rewrite a previously durable log byte. Only
after that `fsync` succeeds does it advance the in-memory count/tip or persist
any dependent component seal, synthetic construction seal, mutant seal, or
classification. The wrapper digest becomes `sha256:` plus lowercase SHA-256
over that complete line including LF. A primitive failure before a complete
command observation, during append, or during `fsync` leaves the already
persisted journal dispatch/start unsealed and enters `INTERNAL_FAILURE`; there
is no append retry. An implementation may retain a partial current suffix but
may never synthesize a command or dependent seal.

[N] Immediately before any dependent seal or classification persistence,
`S0_DEPENDENT_WRAPPER_DURABILITY` identifies the chronologically last wrapper
required by that state transition and requires its zero-based sequence to be
less than the retained durable wrapper count and its LF-inclusive digest to
equal the digest retained for that wrapper. Because such state is persisted
immediately after its last required wrapper, that wrapper is also the retained
chain tip. Failure is `INTERNAL_FAILURE` and the dependent state is not
persisted. The section-9.1 seal-order projection is the complete conformance
input for this predicate; an implementation may not replace it with a
post-hoc file-existence or count-only assertion.

[N] Immediately before each append, the runner `lstat`s `<ENVELOPE>`, requires
one regular file at mode `0644`, and requires its device, inode, and byte length
equal the retained identity and expected complete-prefix length. It opens that
path without following a symlink for write-only append with close-on-exec,
then requires `fstat` device/inode/mode/length equality with the preceding
check. It repeatedly writes only the unwritten suffix of the one wrapper until
all bytes are accepted; a zero-length write is failure. It then file-`fsync`s
and closes. No parent-directory `fsync` or target rename occurs for a wrapper.
Any check, open, write, `fsync`, or close failure is the primitive-failure path
above; the expected length and chain tip advance only after all steps succeed.

[S] `run` has at most one runner-direct child live at a time. `path_map` uses the exact token order displayed in section 7 and every member has exactly `logical`,
`context`, and `actual`, with an absolute actual path. Every token except
`<SUBJECT>` and `<ARCHIVE>` occurs once with null context. `<SUBJECT>` occurs first with context
`CONTROL`, then once for each `M01-M181` in numeric order; these 182 actual
roots are pairwise distinct fresh directories. `<ARCHIVE>` occurs in context
order `SUBJECT_CONTROL`, `SUBJECT_WHEEL_A`, `SUBJECT_WHEEL_B`, `CONTROL`, then
`M01-M181`; those 185 paths are pairwise distinct and have the exact opaque
form in section 1. A command entry's exact `context` selects the corresponding
contextual row. `commands`
contains every durably retained complete direct-child observation, in chronological order, and every
member has exactly `sequence`, `role`, `context`, `mutant_id`, `killer_ordinal`, and
`observation`. Sequence is the consecutive integer position starting at zero,
with no gap or duplicate. Global controls have both nullable
mutation fields null. `context` is null unless the spec contains contextual
`<ARCHIVE>` or `<SUBJECT>`; it is then exact `SUBJECT_CONTROL`,
`SUBJECT_WHEEL_A`, `SUBJECT_WHEEL_B`, `CONTROL`, or the aligned M ID. A `GIT`
construction row and an `IMPORT_PROBE` row have
nonnull mutant ID and null ordinal; mutation `LEAF` rows have both nonnull and
context equal to mutant ID; clean leaf rows use context CONTROL.
Role is `GIT`,
`RUNTIME_PROBE`, `TOOL_TESTS`, `SUBJECT_SUITE`, `WHEEL`, `INSTALL`, `IMPORT`,
`IMPORT_PROBE`, or `LEAF`; observation is a complete
command observation using actual paths. It therefore retains every sanitized
environment and complete stdout/stderr byte stream, including nondeterministic
control output. A COMPLETE envelope contains every direct child spawned by the
completed run. Timestamps use exact UTC form
`YYYY-MM-DDTHH:MM:SS.ffffffZ`. No credentials or inherited environment enter
either representation.

[N] Immediately after durable HEADER creation, the runner appends wrapper
records for every buffered control command in their original chronological
order, using the same append-and-`fsync` rule. Only after the last buffered
wrapper is durable may M01's `MUTANT_ATTEMPT_STARTED` event be persisted. Every
later command wrapper is appended immediately after its observation completes
and before the dependent journal or evidence state named above. The ACTIVE log
therefore carries the longest durable prefix of complete observations. It may
omit only a currently in-flight child, a child whose primitive failed before a
complete observation existed, or a just-completed child whose current append
did not become durable. A durable complete record is never retracted or
changed.

[N] The recovery parser reads the file from byte zero without modifying it.
Its validation gates and their total order are exact. `A0_HEADER_FRAMING`
requires a nonempty first record terminated by LF. `A1_HEADER_JSON` requires
that record to be strict section-3 canonical JSON. `A2_HEADER_SCHEMA` requires
the exact HEADER schema, member population, types, and ACTIVE status.
`A3_HEADER_IDENTITY` requires every immutable HEADER member to equal the
journal, manifest, preflight, plan, tool-subject, path-map, and retained
invocation values. For each later LF-terminated record in byte order,
`A4_WRAPPER_JSON` requires strict canonical JSON, `A5_WRAPPER_SCHEMA` requires
the exact wrapper and command-row member/type populations, `A6_WRAPPER_SEQUENCE`
requires wrapper sequence equal its zero-based record position,
`A7_COMMAND_SEQUENCE` requires the embedded command sequence equal that
wrapper sequence, and `A8_WRAPPER_PREDECESSOR` requires the exact LF-inclusive
digest of the preceding complete record. A record is admitted only after all
of its applicable gates pass.

[N] The recoverable ACTIVE state consists of every LF-terminated record, all
of which must pass the preceding gates, followed optionally by exactly one
nonempty trailing suffix that contains no LF byte. That suffix is the only
excludable current torn append. Every invalid LF-terminated record, including
the final record, is corruption and `INTERNAL_FAILURE`; it is never excluded
as a suffix. Consequently every duplicate, reorder, nonfinal or otherwise
structurally detectable omission, bad-link splice, or structurally detectable
replacement rejects recovery at its first failing A gate. Removing the final
valid wrapper instead yields a valid shorter log that passes `A0` through `A8`
and is detected only by `T1_RETAINED_ACTIVE_STATE` against the retained
post-`fsync` byte length, record count, and chain tip. A valid final wrapper is
always part of the prefix, even when its dependent journal seal is absent.
Recovery never authorizes resume: every retained ACTIVE state abandons that
campaign ID.

[N] After the final mutant seal makes `<JOURNAL>` COMPLETE and its file and
parent directory are durable, the runner reopens `<ENVELOPE>` read-only and
strictly validates the complete ACTIVE log. Terminal gates are also exact and
ordered. `T0_COMPLETE_ACTIVE_LOG` requires no excluded suffix.
`T1_RETAINED_ACTIVE_STATE` requires target device, inode, mode, and byte length
to equal the retained post-`fsync` append identity and requires the validated
HEADER digest, wrapper count, and chain tip to equal the values retained after
the last successful wrapper `fsync`. `T2_CHILD_POPULATION` requires command
count/sequence equality with all complete direct children and every
journal/evidence dependency frozen by this profile. Failure at any gate is
`INTERNAL_FAILURE`. These retained comparisons detect a valid but substituted
final wrapper, which has no later wrapper link, without making a crashed ACTIVE
campaign resumable. Only after all three gates pass does the runner sample
`clock_gettime_ns(CLOCK_REALTIME)`, floor to the containing microsecond, and
format `finished_at` identically to `started_at`. A value earlier than
`started_at` is `INTERNAL_FAILURE`; otherwise `finished_at >= started_at`.

[N] The COMPLETE execution envelope has schema
`pff-draft-binding-mutation-execution-envelope/0.2` and exactly `schema`,
`status`, `campaign_id`, `subject`, `criteria`, `tool_subject`,
`preflight_sha256`, `plan_sha256`, `path_map`, `commands`, `started_at`,
`finished_at`, `command_log_header_sha256`, `command_log_tip_sha256`, and
`command_log_record_count`. Status is exact `COMPLETE`. The identity, hash,
map, start-time, and command members are the validated log projections.
`command_log_header_sha256` is the validated HEADER-line digest;
`command_log_tip_sha256` is the final wrapper-line digest, or the HEADER digest
only when the record count is zero; and `command_log_record_count` is the
nonnegative wrapper count and equals `len(commands)`. `commands` is the
ordered projection of wrapper `.command` values, unchanged in member
population or bytes from the pre-existing command-row schema.

[N] The final envelope must reconstruct the discarded log without discretion.
Project exactly `campaign_id`, `subject`, `criteria`, `tool_subject`,
`preflight_sha256`, `plan_sha256`, `path_map`, and `started_at`; add exact
HEADER `schema` and `status`; then
canonicalize that object plus LF, and require its digest equal
`command_log_header_sha256`. Starting with that digest, construct for every
command in array order the exact wrapper schema, zero-based array position,
current predecessor digest, and unchanged command; canonicalize each plus LF
and advance the digest. The final digest must equal
`command_log_tip_sha256`, the count must equal
`command_log_record_count`, and every wrapper position must equal the embedded
command sequence. These equations bind omission, duplication, replacement,
reordering, and splicing even though the ACTIVE log is replaced.

[N] A final-envelope validator applies this total gate order before semantic
joins. `F0_FINAL_FRAMING` requires exactly one strict canonical JSON object
followed by one LF and no other byte. `F1_FINAL_SCHEMA_STATUS` requires the
exact COMPLETE `/0.2` schema, status, member population, and member types.
`F2_FINAL_HEADER_DIGEST` performs the HEADER reconstruction and comparison.
`F3_FINAL_WRAPPER_RECONSTRUCTION` reconstructs every wrapper in array order
and enforces both sequence equalities. `F4_FINAL_TIP_DIGEST` compares the
resulting tip. `F5_FINAL_RECORD_COUNT` compares the declared count with the
reconstructed wrapper count and `len(commands)`. `F6_FINAL_JOINS` performs the
remaining journal, evidence, path, raw-observation, and logical-command joins.
The first failing gate terminates with `INTERNAL_FAILURE`; a later gate is not
evaluated and cannot compete.

[N] Final assembly is streaming and linear. The runner creates one adjacent
exclusive temporary regular file at mode `0644`, emits exactly one section-3
canonical COMPLETE object plus final LF while reading and validating wrappers
in order and projecting only `.command` into `commands`, file-`fsync`s the
temporary, atomically replaces `<ENVELOPE>`, and parent-directory-`fsync`s it.
It must not retain or serialize an implementation-defined map order, and it
must not rewrite `<ENVELOPE>` before this one terminal replacement. Failure at
any validation, write, `fsync`, replace, or directory-`fsync` step is
`INTERNAL_FAILURE` and writes no evidence bundle. After successful replacement
the target is a COMPLETE envelope object, never an ACTIVE log; its schema is
the unambiguous representation discriminator.

[N] The persistence write bound is linear in retained observation bytes: each
wrapper line is appended once, and each unchanged command object is emitted
once more during the sole terminal envelope assembly. No operation writes a
previous wrapper prefix again. Header/final fixed fields and JSON delimiters
add only their exact serialized byte lengths. An implementation that rewrites
a complete ACTIVE prefix, even if its output bytes later agree, is
nonconforming.

`execution_envelope_sha256` binds the complete final COMPLETE-envelope bytes,
including their final LF.

[S] For a COMPLETE envelope and final bundle, every canonical runtime probe, suite, wheel, install, import, construction
probe, clean leaf, and mutant leaf projection joins to exactly one envelope
command row by role, logical spec, mutant context, and killer ordinal. The
row's actual spec must equal path-map materialization of that logical spec;
termination is identical, and every retained canonical stream/result/count,
wheel member, or installed-file projection is derived from that row's complete
raw observation. No row satisfies two canonical observations and no such
canonical observation lacks a row. Git-only construction/identity rows remain
raw envelope evidence and are not falsely projected as another control.

[N] Before those joins, bundle construction and post-run review independently
perform the final-envelope reconstruction equations above. A row participates
in semantic joins only after the reconstructed HEADER digest, wrapper chain,
tip, count, embedded sequences, and final envelope hash all pass. The chain
fields do not replace any existing raw-observation or logical-to-actual join;
they authenticate the unchanged command array's ACTIVE persistence history.

`controls.pre_attempt_identity` derives from the final noncontextual GIT
`rev-parse HEAD`, `rev-parse HEAD^{tree}`, `status`, and `ls-tree` envelope rows
in that exact order before the first attempt, plus the same in-process
mode/blob/artifact hash scan frozen by `post_control_identity`. It is the sole
canonical control allowed to join that ordered four-row group rather than one
row; those rows join no other canonical control.

`controls.post_attempt_identity` derives by the same rule from the final four
noncontextual GIT rows after the last component seal. Those rows join no other
canonical control and are the chronologically last spawned command group
before final journal sealing.

Every actual mapped path is absolute and contains no NUL, LF, colon, `<`, or
`>`. The actual values for authority/input/output tokens equal their supplied
resolved paths; `<SETUPTOOLS>` equals the fresh isolated runtime root; and
cache, temp, subject, wheel, and install tokens equal their runner-created
roots. `<CACHE>` and `<TMP>` are distinct. JOURNAL/EVIDENCE/ENVELOPE are
pairwise realpath-distinct, and no mutable/output root aliases, contains, or is
contained by `<REPO>`, `<SITE>`, another subject root, or another independently
declared mutable root except the explicitly declared `<SETUPTOOLS>` and archive
children of `<TMP>`. To materialize a logical command spec, the runner scans each string
left-to-right and replaces every exact displayed token with its one mapped
actual path, using the command's context for `<SUBJECT>` and `<ARCHIVE>`; tokens are
syntactically distinct and replacements are not rescanned. Canonical specs are
constructed from PLAN only for leaf commands and otherwise from the profile's
exact logical specs, never inferred by reverse replacement from actual paths.
The envelope retains the separately constructed
actual spec, so the mapping and materialization are independently replayable.

[N] The crash-state topology is exhaustive. An interruption after the empty
ACTIVE journal is created but before HEADER publication leaves that journal
alone with zero events and zero consumed attempts. After HEADER publication
but before M01 start it leaves the ACTIVE journal plus a valid ACTIVE log and
still consumes zero attempts. During a later append it leaves the ACTIVE
journal plus a valid LF-terminated log prefix and at most one nonempty trailing
suffix containing no LF; the corresponding dispatch/start may be durable but
its dependent seal is absent. A complete LF-terminated invalid record is
corruption, not a crash suffix. After a complete wrapper `fsync` but before the
dependent seal it may leave that valid extra row with the seal absent. None
permits resume.

[N] After the last classified component and exact post-attempt identity pass,
the runner atomically persists the final mutant seal and thereby the COMPLETE
journal. Until terminal replacement, that COMPLETE journal coexists with the
valid ACTIVE log. A crash while the final temporary is being assembled leaves
the log at `<ENVELOPE>` plus an ignored incomplete adjacent temporary. A crash
at the atomic-replace/directory-`fsync` boundary recovers either the complete
old ACTIVE log or the complete new COMPLETE envelope according to filesystem
durability, never a hybrid target. After successful replacement and before
bundle publication it leaves the COMPLETE journal and COMPLETE envelope but no
bundle. Evidence is written atomically only after that state. None of these
states is silently called a final qualification bundle, and every no-bundle
state abandons the campaign ID.

[S] The bundle does not contain its own digest. Its external SHA-256 is computed
over complete canonical bytes and is later bound by the post-run review.
Re-running may change the envelope and raw-control timing text, but must
reproduce the plan, patches, roots, leaf outputs, component classes, aggregate
sets, and every other deterministic projection.

### 9.1 Canonical chain derivation vectors

[N] These vectors freeze byte encoding and chaining independently of one
runtime path population. The HEADER uses the exact production member schema
but an intentionally empty `path_map` so the vector remains compact; it is
not a runnable campaign header. Production validation additionally requires
the complete section-9 path-map population. Every displayed JSON line has
exactly one following LF byte; that LF is included in the stated byte length
and digest. No fence byte is part of a preimage.

`HEADER_LINE`:

```text
{"campaign_id":"campaign:vector","criteria":{"manifest_sha256":"sha256:1111111111111111111111111111111111111111111111111111111111111111","qualification_profile_sha256":"sha256:2222222222222222222222222222222222222222222222222222222222222222"},"path_map":[],"plan_sha256":"sha256:3333333333333333333333333333333333333333333333333333333333333333","preflight_sha256":"sha256:4444444444444444444444444444444444444444444444444444444444444444","schema":"pff-draft-binding-mutation-execution-envelope-log/0.2","started_at":"2026-08-19T00:00:00.000000Z","status":"ACTIVE","subject":{"commit":"0000000000000000000000000000000000000000","git_tree":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","profile_path":"docs/PFF_DRAFT_BINDING_PROFILE_V0.1.md","profile_sha256":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},"tool_subject":{"commit":"cccccccccccccccccccccccccccccccccccccccc","git_tree":"dddddddddddddddddddddddddddddddddddddddd"}}
```

`HEADER_LINE_BYTE_LENGTH = 953`

`HEADER_LINE_SHA256 = sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183`

`FIRST_WRAPPER_LINE`:

```text
{"command":{"context":null,"killer_ordinal":null,"mutant_id":null,"observation":{"spec":{"argv":["<PYTHON>","-P","-s","-S","-B","--version"],"cwd":"<REPO>","environment":[],"stdin":{"byte_length":0,"hex":"","sha256":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}},"stderr":{"byte_length":0,"hex":"","sha256":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},"stdout":{"byte_length":15,"hex":"507974686f6e20332e31322e31330a","sha256":"sha256:55ae85cf4bdb38743edbcd53ea68ff36511997ec6c21b1e83d8bebc939bf056b"},"termination":{"kind":"EXIT","value":0}},"role":"RUNTIME_PROBE","sequence":0},"previous_record_sha256":"sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183","schema":"pff-draft-binding-mutation-execution-envelope-command/0.2","sequence":0}
```

`FIRST_WRAPPER_LINE_BYTE_LENGTH = 821`

`FIRST_WRAPPER_LINE_SHA256 = sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e`

`FINAL_ENVELOPE_LINE`:

```text
{"campaign_id":"campaign:vector","command_log_header_sha256":"sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183","command_log_record_count":1,"command_log_tip_sha256":"sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e","commands":[{"context":null,"killer_ordinal":null,"mutant_id":null,"observation":{"spec":{"argv":["<PYTHON>","-P","-s","-S","-B","--version"],"cwd":"<REPO>","environment":[],"stdin":{"byte_length":0,"hex":"","sha256":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}},"stderr":{"byte_length":0,"hex":"","sha256":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},"stdout":{"byte_length":15,"hex":"507974686f6e20332e31322e31330a","sha256":"sha256:55ae85cf4bdb38743edbcd53ea68ff36511997ec6c21b1e83d8bebc939bf056b"},"termination":{"kind":"EXIT","value":0}},"role":"RUNTIME_PROBE","sequence":0}],"criteria":{"manifest_sha256":"sha256:1111111111111111111111111111111111111111111111111111111111111111","qualification_profile_sha256":"sha256:2222222222222222222222222222222222222222222222222222222222222222"},"finished_at":"2026-08-19T00:00:01.000000Z","path_map":[],"plan_sha256":"sha256:3333333333333333333333333333333333333333333333333333333333333333","preflight_sha256":"sha256:4444444444444444444444444444444444444444444444444444444444444444","schema":"pff-draft-binding-mutation-execution-envelope/0.2","started_at":"2026-08-19T00:00:00.000000Z","status":"COMPLETE","subject":{"commit":"0000000000000000000000000000000000000000","git_tree":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","profile_path":"docs/PFF_DRAFT_BINDING_PROFILE_V0.1.md","profile_sha256":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},"tool_subject":{"commit":"cccccccccccccccccccccccccccccccccccccccc","git_tree":"dddddddddddddddddddddddddddddddddddddddd"}}
```

`FINAL_ENVELOPE_LINE_BYTE_LENGTH = 1866`

`FINAL_ENVELOPE_LINE_SHA256 = sha256:2b15431b15e8efdec2b01a119d97ddf05ececabb36e48d6fbfe757537a31a584`

The exact positive second-wrapper derivation takes the displayed command
object, changes only embedded `command.sequence` to integer 1, wraps it with
wrapper `sequence` 1 and `previous_record_sha256` equal
`sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e`, then canonicalizes plus LF. Its byte length is
821 and its digest is `sha256:afc623d1871279a538c674ee393128e931b054bcd023177b2e4aa8a1314b04c1`.

[N] The vector byte algebra is exact. `||` means byte concatenation without an
inserted separator. `H`, `W0`, `W1`, and `E1` mean respectively the complete
`HEADER_LINE`, `FIRST_WRAPPER_LINE`, derived second-wrapper line, and
`FINAL_ENVELOPE_LINE`, each including its one final LF. `POSITIVE_LOG_0 = H`,
`POSITIVE_LOG_1 = H || W0`, and `POSITIVE_LOG_2 = H || W0 || W1`.
`POSITIVE_FINAL_1 = E1`. Byte offsets are zero-based half-open: in
`POSITIVE_LOG_2`, `H` occupies `[0,953)`, `W0` occupies `[953,1774)`, and `W1`
occupies `[1774,2595)`.

[N] Every replacement below operates on exactly one occurrence of the stated
ASCII byte string in the named source; a source with zero or multiple
occurrences is invalid criteria rather than an alternative construction. A
transformation changes no other byte and does not recompute a predecessor,
declared digest, declared count, or retained state unless it expressly says
so. `REPLACED_W0` replaces `"role":"RUNTIME_PROBE"` in `W0` with
`"role":"SUBJECT_SUITE"`. Both values are allowed role spellings and have
equal byte length. `SPLICED_W1` replaces
`"previous_record_sha256":"sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e"`
in `W1` with
`"previous_record_sha256":"sha256:0aeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e"`.
`MALFORMED_H` replaces `"status":"ACTIVE"` in `H` with
`"status":ACTIVE`, removing exactly the two quote bytes around `ACTIVE`.
`CHANGED_H` replaces `"campaign_id":"campaign:vector"` in `H` with
`"campaign_id":"campaign:vect0r"`.

[N] Three final-envelope transformations start independently from `E1`.
`WRONG_FINAL_HEADER` replaces
`"command_log_header_sha256":"sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183"`
with
`"command_log_header_sha256":"sha256:0b61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183"`.
`WRONG_FINAL_TIP` replaces
`"command_log_tip_sha256":"sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e"`
with
`"command_log_tip_sha256":"sha256:0aeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e"`.
`WRONG_FINAL_COUNT` replaces `"command_log_record_count":1` with
`"command_log_record_count":0`.

[N] The exact negative inputs are `TORN = H || W0[0:820]`, so its final 820
bytes contain no LF; `DUPLICATE = H || W0 || W0`; `REORDER = H || W1 || W0`;
`SPLICE = H || W0 || SPLICED_W1`; `OMISSION = H || W1`, obtained by removing
the exact `[953,1774)` `W0` record from `POSITIVE_LOG_2`;
`OMISSION_FINAL = POSITIVE_LOG_1 = H || W0`, obtained by removing the exact
`[1774,2595)` final `W1` record from `POSITIVE_LOG_2`;
`REPLACEMENT_NONFINAL = H || REPLACED_W0 || W1`;
`REPLACEMENT_FINAL = H || REPLACED_W0`; `MALFORMED_HEADER = MALFORMED_H`;
`CHANGED_HEADER = CHANGED_H`; and `ACTIVE_AS_COMPLETE = H`. For
`OMISSION_FINAL`, the terminal validator receives the retained append state
from unmodified `POSITIVE_LOG_2`:
`byte_length=2595`,
`header_sha256=sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183`,
`record_count=2`, and
`tip_sha256=sha256:afc623d1871279a538c674ee393128e931b054bcd023177b2e4aa8a1314b04c1`;
device, inode, and mode inputs are held equal. For
`REPLACEMENT_FINAL`, the terminal validator receives the retained append state
`byte_length=1774`, `header_sha256=sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183`,
`record_count=1`, and
`tip_sha256=sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e`;
device, inode, and mode inputs are held equal. The replacement line's actual
digest is intentionally not substituted into that retained state.

[N] The seal-order discriminator is this one canonical JSON line plus LF. It
is a conformance-validator input projection, not a production artifact and not
a new journal member. The `required_wrapper_record` is the last wrapper the
dependent transition needs; `durable_log` is the retained state presented to
`S0_DEPENDENT_WRAPPER_DURABILITY` immediately before persistence.

`PREMATURE_SEAL_PROJECTION_LINE`:

```text
{"dependent_seal":{"event":"COMPONENT_SEALED","required_wrapper_record":{"sequence":0,"sha256":"sha256:aaeb43b8e1740237ccdd245cabc8e72b189cfcaf308a253cf304cfae4335101e"}},"durable_log":{"record_count":0,"tip_sha256":"sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183"},"schema":"pff-draft-binding-mutation-seal-order-vector/0.2"}
```

`PREMATURE_SEAL_PROJECTION_LINE_BYTE_LENGTH = 352`

`PREMATURE_SEAL_PROJECTION_LINE_SHA256 = sha256:1a5f59b7952201a27b9bbb0aa56603454ee958a6d5431290f9cbde3489d1e881`

[N] The complete vector identities, including the final LF whenever the
construction has one, are exact:

```text
POSITIVE_LOG_0                 953  sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183
POSITIVE_LOG_1                1774  sha256:2a553b85c044e9ecf2f03f5c15a7aa317dfbb0a5737c88d04bbd7247926c4826
POSITIVE_LOG_2                2595  sha256:d90dc4e625eea8fffee18a98b791a672e2831b50d3b0cc04c98541a13c0e35c4
POSITIVE_FINAL_1              1866  sha256:2b15431b15e8efdec2b01a119d97ddf05ececabb36e48d6fbfe757537a31a584
W1                             821  sha256:afc623d1871279a538c674ee393128e931b054bcd023177b2e4aa8a1314b04c1
REPLACED_W0                    821  sha256:1653cb5c614fae912b0f1c4920ca62e0f5061b86e04946890a0c106125b3fd37
SPLICED_W1                     821  sha256:5b98258e6be0bfab44a24994f981dfed0d925a05f4c44ede349e1708254966af
TORN                          1773  sha256:e2007f4761e41d67e784fdfb42cddc3c1fe6fc1e31c435164b8dbc84f2c871a4
DUPLICATE                     2595  sha256:eba08565553e7681026a05b50455fa31257658042c33a98f24869f490c6f1e59
REORDER                       2595  sha256:b96844d8226bebcc152c54142b2d396c89840a51406fef10750bb295e44737fe
SPLICE                        2595  sha256:a9b91ebf9423f7151451afed19e9687deb26b19aefa444f57fac6d043fd76a1a
OMISSION                      1774  sha256:23fdbbfe86e99234fe7f44849fae83fdb59e8d09fb6bbf3d884f0e3cb1634e73
OMISSION_FINAL                1774  sha256:2a553b85c044e9ecf2f03f5c15a7aa317dfbb0a5737c88d04bbd7247926c4826
REPLACEMENT_NONFINAL          2595  sha256:5ec6283734f32fff1fc849e51708236ed6e69cecd581c4fbfa2d119bef9950e2
REPLACEMENT_FINAL             1774  sha256:1d6a804f5a3743b6e7bb090d5f7d035600faeecd383f3224f430426593e10853
MALFORMED_HEADER               951  sha256:14da95a023bade6d22ba98fac4a93a124f66b05abb7fe769cbebf3803e125bdd
CHANGED_HEADER                 953  sha256:3d515189ab47cfafcbebcbfeccd7ea4de372ad86ce4ae2bc85b3b216dc593951
WRONG_FINAL_HEADER            1866  sha256:95b1fa8d63dec76b2aff043a5d2948a1f660f271d2bcd201e2687dd9258cd21c
WRONG_FINAL_TIP               1866  sha256:a487a8c67e1db3278313fee4bd565e8b4363febb3757ce094cd539f87868a164
WRONG_FINAL_COUNT             1866  sha256:45eddd51b64df0cddd86a8347fea3f9f40304bad9f35c3d5315b2cc886f88d38
PREMATURE_DEPENDENT_SEAL       352  sha256:1a5f59b7952201a27b9bbb0aa56603454ee958a6d5431290f9cbde3489d1e881
ACTIVE_AS_COMPLETE             953  sha256:eb61d4c6dda7a9e1a8ce71d598e49ef8823e3a200725c3ca775c76ab331d1183
```

[N] Expected results and first rejecting gates are exact. The vector-mode
ACTIVE parser uses the immutable values displayed in `H` as its expected
`A3_HEADER_IDENTITY` input; production additionally requires the full path-map
and journal joins. `POSITIVE_LOG_0`, `POSITIVE_LOG_1`, and `POSITIVE_LOG_2`
pass all applicable `A0` through `A8` gates with respectively zero, one, and
two wrappers; their tips are the displayed `H`, `W0`, and `W1` digests.
`POSITIVE_FINAL_1` passes `F0` through `F5`; `F6` is intentionally outside this
compact vector because its empty path map is not a runnable campaign.

[N] `TORN` returns `POSITIVE_LOG_0` as its only valid prefix, count zero and
HEADER tip, and excludes exactly its non-LF 820-byte suffix; terminalization
rejects first at `T0_COMPLETE_ACTIVE_LOG`. `DUPLICATE` rejects recovery at
`A6_WRAPPER_SEQUENCE` on its third record. `REORDER` and `OMISSION` each reject
recovery at `A6_WRAPPER_SEQUENCE` on their first wrapper. `SPLICE` rejects
recovery at `A8_WRAPPER_PREDECESSOR` on `SPLICED_W1`.
`OMISSION_FINAL` is byte-identical to `POSITIVE_LOG_1`, passes `A0` through
`A8` with one wrapper, and then terminalization rejects first at
`T1_RETAINED_ACTIVE_STATE` against the exact two-wrapper retained state above.
`REPLACEMENT_NONFINAL` admits `REPLACED_W0` and then rejects recovery at
`A8_WRAPPER_PREDECESSOR` on unchanged `W1`. `REPLACEMENT_FINAL` passes the
structural recovery parser with count one and actual tip
`sha256:1653cb5c614fae912b0f1c4920ca62e0f5061b86e04946890a0c106125b3fd37`,
then terminalization rejects first at `T1_RETAINED_ACTIVE_STATE` against the
exact retained state above. No parser result authorizes resume.

[N] `MALFORMED_HEADER` rejects recovery at `A1_HEADER_JSON`.
`CHANGED_HEADER` passes canonical/schema checks and rejects at
`A3_HEADER_IDENTITY` because the campaign ID differs. `WRONG_FINAL_HEADER`
rejects the final-envelope validator first at `F2_FINAL_HEADER_DIGEST`.
`WRONG_FINAL_TIP` rejects first at `F4_FINAL_TIP_DIGEST`.
`WRONG_FINAL_COUNT` rejects first at `F5_FINAL_RECORD_COUNT`.
`PREMATURE_DEPENDENT_SEAL` rejects first at
`S0_DEPENDENT_WRAPPER_DURABILITY` because required sequence zero is not less
than durable count zero and the required wrapper digest is not the durable
tip; no journal seal write is attempted. `ACTIVE_AS_COMPLETE` passes final
framing and rejects first at `F1_FINAL_SCHEMA_STATUS` on the ACTIVE log schema
and status.

[N] Tool tests and both implementation and post-run reviews must construct
every named vector from these exact source bytes and transformations, require
the stated length and SHA-256 before dispatch, exercise the stated parser,
terminalizer, seal-order, or final-envelope boundary, and assert the exact
first gate and `INTERNAL_FAILURE` where rejection is required. An
implementation-selected substitute, a count-only assertion, a prose pin, or a
later-gate failure does not satisfy any vector.

## 10. Tooling and source boundaries

The v0.2 authority-only candidate and acceptance tranche changes exactly:

```text
docs/PFF_DRAFT_BINDING_MUTATION_QUALIFICATION_PROFILE_V0.2.md
```

The accepted v0.1 profile and preserved v0.1 manifest are immutable inputs,
not members of the v0.2 changed-path set.

After acceptance, the qualification-tool implementation allowlist is exactly:

```text
tools/qualify_binding_mutations.py
tests/binding_mutation_fixtures.py
tests/test_binding_mutation_qualification.py
qualification/PFF_DRAFT_BINDING_MUTATION_TOOL_REVIEW_V0.2.json
README.md
```

The tool may import the Python standard library, the leaf adapter, and public
test/production types required to construct frozen fixtures. The `build-wheel`
subcommand alone may additionally import the exact authenticated isolated
setuptools population after installing section-7 spawn traps. It must not modify
`src/poietics`, any existing test, any accepted authority file, the preserved
manifest, or package
metadata. Product modules must not import the tool or leaf adapter. The leaf
adapter is not an installed package surface.

The preflight `direct_syntax_boundaries` check is the following closed
CPython-3.12 AST predicate; it does not let tool code define its own inspection.
Its Python
artifact population is exactly the script, leaf adapter, and tool-test paths
above. The 20 `src/poietics/**/*.py` paths from the subject tree are separately
required byte-identical by `authority_identity`/`worktree_clean`, which proves
that no product module acquired a tool or adapter import. Each of the three new
files must parse with `ast.parse(..., mode="exec", feature_version=(3, 12))`.
Import and call nodes are inspected by artifact raw-UTF-8 path, then
`(lineno, col_offset, end_lineno, end_col_offset, type(node).__name__)` order.
A missing location, syntax failure, or first violation fails that artifact.

For `Import`, an alias with explicit `asname` binds that name and resolves to
the full imported module; without `asname`, it binds and resolves from only its
first dotted component (`import os.path` therefore binds `os` to `os`, while
`import os.path as p` binds `p` to `os.path`). For `ImportFrom`, `level` must be zero,
`module` nonnull, and no alias may be `*`; it binds the explicit `asname` or
imported member. Imported binding names are file-wide and unique; a second
import binding the same local name is a violation. Excluding the one originating
import alias, any `Name` with `Store` or `Del` context, `ast.arg`, function or
class definition name, exception-handler name, `global`/`nonlocal` member,
`MatchAs.name`, `MatchStar.name`, or `MatchMapping.rest` equal to an imported
binding is a violation. This conservative rule ignores lexical-scope escape
and therefore has one result without dataflow inference.
An import is module-executed when it has no `FunctionDef`, `AsyncFunctionDef`,
or `Lambda` ancestor. A top-level class body executes during import and uses
the module-executed set; a class nested under a function remains deferred. The
allowed module sets are exact:

| Artifact | Module-executed imports | Deferred imports (has a `FunctionDef`, `AsyncFunctionDef`, or `Lambda` ancestor) |
|---|---|---|
| `tools/qualify_binding_mutations.py` | roots in `sys.stdlib_module_names` | module-executed set, any `poietics` module, exact `tests.binding_mutation_fixtures`, and `setuptools` or `setuptools.build_meta` |
| `tests/binding_mutation_fixtures.py` | roots in `sys.stdlib_module_names` or any `poietics` module | same set |
| `tests/test_binding_mutation_qualification.py` | roots in `sys.stdlib_module_names`, any `poietics` module, exact `tests.binding_mutation_fixtures`, or exact `tools.qualify_binding_mutations` | same set |

For every row, the otherwise-standard-library roots `asyncio`, `ctypes`,
`ftplib`, `http`, `multiprocessing`, `smtplib`, `socket`, `ssl`, `telnetlib`,
`urllib`, `webbrowser`, and `xmlrpc` are excluded. `__future__` is admitted as a
standard-library root. Dotted modules match only the exact admitted prefix;
lookalike prefixes do not. The sole admitted third-party root is `setuptools`
at the tool's non-module scope described above.

For call resolution, a bare name in the forbidden built-in list resolves to
`builtins.<name>` regardless of any local binding;
an imported binding plus a static `Attribute` chain resolves to its absolute
module/member string. The exact forbidden resolved callees are
`builtins.__import__`, `builtins.breakpoint`, `builtins.eval`, `builtins.exec`,
`importlib.reload`, `os.system`, `os.popen`, `os.fork`, `os.forkpty`, every
one of `os.posix_spawn`, `os.posix_spawnp`, `os.spawnl`, `os.spawnle`,
`os.spawnlp`, `os.spawnlpe`, `os.spawnv`, `os.spawnve`, `os.spawnvp`, and
`os.spawnvpe`, and `subprocess.call`,
`subprocess.check_call`, `subprocess.check_output`, `subprocess.getoutput`, and
`subprocess.getstatusoutput`. A resolved `subprocess.Popen` or
`subprocess.run` call is allowed only when keyword `shell` is absent or is exact
constant `False`; duplicate `shell` keywords or `**kwargs` are violations.
Calls whose callee is a local function/class or otherwise has no imported or
built-in syntactic resolution are admitted. This check is deliberately named
for its direct-syntax scope: it does not claim to resolve local dataflow,
dynamic `importlib` arguments, or indirect callable aliases. The independent
tool-review `full_boundary` check over the exact hashed implementation proves
that only `build-wheel` reaches setuptools and that no indirect/dynamic route
reaches a disallowed import, call, provider, credential, shell, or network
action. References to
forbidden callables without a `Call` node remain permitted so the reviewed
spawn traps can capture them. This table and traversal are the complete
preflight direct-syntax inspection; the two scopes are not conflated.

The script's top-level bootstrap imports only the host standard library. It
does not insert `<REPO>` or import the leaf adapter, tests, or product modules
until the exact worktree/tree/artifact checks in section 7 pass; leaf/import
subcommands likewise recheck script and adapter hashes before adding their
authenticated subject/repository paths.

The implementation review is complete before controlled mutation attempts. It
includes strict manifest parsing, duplicate-key rejection, exact authority
table comparison, recipe population closure, anchor/preimage/postimage tests,
content-root recomputation, disposable-root enforcement, zero-attempt
preflight failures, leaf population and stage tests, output canonicalization,
timeout and classification precedence, no-retry enforcement, hostile order and
extra-row inputs, and proof that a nonzero aggregate unittest exit alone cannot
be classified as a kill.

[N] The implementation review additionally recomputes all section-9 vector
bytes and LF-inclusive digests; exercises HEADER creation, wrapper append and
`fsync` ordering, wrapper/command sequence equality, chain reconstruction,
streaming terminal assembly, schema discrimination, and exact final-envelope
member population; proves each frozen crash window; accepts only the permitted
nonempty no-LF torn suffix for ACTIVE forensics; rejects every invalid
LF-terminated record including a final duplicate or bad-link splice; and
instruments the runner to prove that no complete ACTIVE prefix is rewritten.
The test and review population is exactly every identity named in section
9.1: all four positive constructions, `W1`, `REPLACED_W0`, `SPLICED_W1`,
`TORN`, `DUPLICATE`, `REORDER`, `SPLICE`, `OMISSION`, `OMISSION_FINAL`,
`REPLACEMENT_NONFINAL`, `REPLACEMENT_FINAL`, `MALFORMED_HEADER`,
`CHANGED_HEADER`, `WRONG_FINAL_HEADER`, `WRONG_FINAL_TIP`,
`WRONG_FINAL_COUNT`, `PREMATURE_DEPENDENT_SEAL`, and
`ACTIVE_AS_COMPLETE`. Tests reconstruct each from the frozen source bytes,
authenticate its exact length and SHA-256, dispatch it to the exact boundary,
and require the first gate and result frozen in section 9.1. They additionally
exercise wrong final header/tip/count fields separately, the terminal retained
length/count/tip comparison for a final-wrapper omission, the terminal
retained tip comparison for a valid final-record replacement, and the
seal-order predicate before its journal write. An implementation-chosen vector,
permissive recovery of a complete invalid last record, wrong-reason later
failure, private-helper substitute, or assertion that does not reach the
production parser, terminalizer, seal write gate, or final-envelope validator
is a review failure.

[S] The review also proves executable reachability and closed dispatch for all
191 leaves and all 205 component occurrences; pre-acceptance
criteria review does not claim that post-acceptance code already exists.

The tool-review file is canonical JSON schema
`pff-draft-binding-mutation-tool-review/0.2` with exactly `schema`, `status`,
`criteria`, `reviewed_source_root`, `reviewed_files`, and `checks`. `status` is
`CLEAN`; criteria has exactly `subject_profile_sha256`,
`qualification_profile_sha256`, and `manifest_sha256`. `reviewed_files`
contains UTF-8-path-order objects with exact `path`, `byte_length`, and
`sha256` for the script, adapter, test, and README, excluding the review file
itself. `reviewed_source_root` is `sha256:` plus lowercase SHA-256 over, for
each object in that order, `UTF8(path)`, NUL, the 64 lowercase digest digits
without `sha256:`, and LF. `checks` is the exact ordered sequence
`architecture`, `determinacy`, `fixture_reachability`, `false_green`, and
`full_boundary`, each encoded exactly
`{"name":<name>,"status":"CLEAN"}`. The report does not
contain its own hash or predict its eventual commit/tree identity. Publication
review separately proves that the committed tree contains those exact four
reviewed files plus the exact review-report bytes and no other changed path.

After that review, the first qualification-tool implementation is published as
one ordinary non-force commit whose direct parent is the accepted authority
commit and whose changed paths equal the implementation allowlist. A repaired
tool is a later ordinary commit whose direct parent is the previously active
tool commit, whose own changed paths are a nonempty subset of the allowlist,
and whose cumulative diff from the accepted authority commit contains no path
outside that allowlist. Every successor carries a newly reviewed tool-review
record and repeats the full implementation gate. The reviewed tree, published
tree, and locally executed tree must be identical. Controlled mutant attempts
begin only from that clean published implementation commit. Any tool,
leaf-adapter, manifest, or profile byte change invalidates the run and requires
a new reviewed tool commit and new campaign before attempts restart from zero.

## 11. Post-run review and qualification publication

A `QUALIFIED` bundle does not by itself change repository status. One
independent read-only post-run review authenticates the exact tool commit, the
external evidence and envelope hashes, population closure, every construction
and component classification, the frozen right-reason vectors, raw-output
retention, and the deterministic replay projections. Its canonical JSON schema
is `pff-draft-binding-mutation-post-run-review/0.2` and has exactly `schema`,
`status`, `tool_subject`, `journal`, `evidence`, `execution_envelope`, and `checks`.
`status` is `CLEAN`; journal/evidence/envelope each have exact `path`, `byte_length`,
and `sha256`. Their paths are respectively exact
`qualification/PFF_DRAFT_BINDING_MUTATION_JOURNAL_V0.2.json`,
`qualification/PFF_DRAFT_BINDING_MUTATION_EVIDENCE_V0.2.json`, and
`qualification/PFF_DRAFT_BINDING_MUTATION_EXECUTION_ENVELOPE_V0.2.json`; the
review computes length and digest over the supplied run-output bytes that must
later be copied byte-for-byte to those publication paths. `tool_subject` has exact commit/tree; and checks is this ordered
sequence of exact `{"name":<name>,"status":"CLEAN"}` objects:

```text
identity
journal_integrity
command_log_integrity
population_closure
recipe_application
component_right_reason
aggregate_classification
raw_retention
deterministic_projection
```

[N] `command_log_integrity` independently verifies the final envelope schema,
exact member population, HEADER reconstruction, every wrapper reconstruction,
LF-inclusive header/tip digests, record count, embedded sequences, COMPLETE
journal ordering, complete command population, and all crash-state exclusions.
It fails if supplied envelope bytes are an ACTIVE log, if any chain equation
or join fails, or if the final object cannot be reproduced by the streaming
assembly rule.

Only after that review may one qualification-publication commit add or change
exactly:

```text
qualification/PFF_DRAFT_BINDING_MUTATION_EVIDENCE_V0.2.json
qualification/PFF_DRAFT_BINDING_MUTATION_EXECUTION_ENVELOPE_V0.2.json
qualification/PFF_DRAFT_BINDING_MUTATION_JOURNAL_V0.2.json
qualification/PFF_DRAFT_BINDING_MUTATION_POST_RUN_REVIEW_V0.2.json
README.md
```

Every one of those five prospective-tree entries has exact Git mode `100644`.
The journal, evidence, and envelope paths contain the exact reviewed bytes.
README may record only `QUALIFIED`, the subject/tool commit identities, and the
four artifact SHA-256 values; it does not change binder semantics. The
publication commit has the tool implementation commit as direct parent, its
prospective tree and exact five-path changed set are independently reviewed,
and it is pushed without force. After fetch, review authenticates the exact
publication commit, its direct tool parent, the prospective tree ID, the exact
changed-path set, and all five mode/blob pairs. Local, reviewed, committed,
pushed, and re-fetched artifact SHA-256 values must additionally be identical.
This publication, not the pre-run profile acceptance or green baseline suite,
closes draft-binding qualification.

## 12. Stopping and campaign rules

Qualification stops and reports without semantic repair when:

```text
the authenticated subject or authority differs;
the manifest is not byte-canonical or population-closed;
a recipe is ambiguous, non-atomic, inapplicable, or changes an unrelated mechanism;
a leaf cannot isolate its exact F/C member or qualified subcase;
a clean control is not exact PASS;
the implementation or independent review finds an authority defect.
```

Those pre-attempt failures consume zero attempts. After attempts begin, a
non-`PREDICTED_KILL` mutant does not stop enumeration; the campaign completes
all remaining M/O members but its aggregate is `NONQUALIFYING`. A construction
failure is classified as section 8 requires and likewise does not short-circuit
later mutants. External interruption, a newly discovered authority/tool
integrity defect, or a runner primitive `INTERNAL_FAILURE` may leave a partial
journal/ACTIVE-log or terminal envelope instead of a complete bundle. Primitive
failure includes spawn/exec, pipe, clock, process-group, signal, drain/wait,
file write, append, chain validation, streaming assembly, `fsync`, or
atomic-replace failure that the termination/component schemas cannot honestly
represent. The runner preserves the last durable journal and the last durable
ACTIVE-log or COMPLETE-envelope state and emits the canonical
`INTERNAL_FAILURE` diagnostic if it remains able, writes no new evidence
bundle before terminalization, and does not seal or classify an affected
component if one is active. If the failure occurs during the bundle's own
replace/fsync protocol, any visible candidate file is retained only as
unqualified forensic output and is never a final bundle. The runner never
synthesizes a termination. That campaign is abandoned and any retry requires a
new campaign ID.

A survivor or wrong-reason result is evidence about the current test design,
not permission to weaken a recipe, change a killer after observation, or add a
post hoc assertion. Repair requires a separately reviewed successor criteria
version or a bounded implementation/test repair under the still-accepted
binder semantics.

## 13. Acceptance protocol

Before acceptance, three independent read-only reviews report over the exact
candidate bytes and preserved authorities:

```text
architecture: qualification boundary and allowlists are clean
determinacy: unchanged manifest/leaf/classification rules remain complete and the ACTIVE-log, chain, recovery, terminal assembly, joins, and crash topology have one result
criteria: every preserved M recipe/expected component remains reachable and every new persistence vector discriminates the forbidden alternative
```

[N] The reviewed subject consists of the exact v0.2 candidate profile bytes,
the immutable accepted v0.1 profile bytes, and the immutable manifest bytes.
The v0.2 accepted profile is published as one ordinary non-force authority
commit whose direct parent is exact accepted v0.1 authority commit
`053855c45abd9130557515df725c14af0b43cf41`. Before commit, an independent
review derives the prospective accepted-profile bytes by the exact
transformation below. The prospective tree is exactly parent tree
`ca7ba5a43125cd04a3cbb57da7ca4416d0f6adf2` plus those v0.2 accepted-profile
bytes at Git mode `100644`. The accepted v0.1 profile and manifest remain at
mode `100644` with exact section-1.1 hashes; every other parent-tree entry is
byte-identical. The changed-path set against the parent is exactly the sole
section-10 v0.2 authority path. The committed tree equals that prospective
tree. After an ordinary non-force push, a re-fetch authenticates the same
commit, direct parent, tree, new accepted-profile blob, preserved v0.1 profile
blob, and preserved manifest blob.

Acceptance changes only the profile `Status` line from
`CANDIDATE CONFORMANCE PROFILE — NOT ACCEPTED` to
`ACCEPTED CONFORMANCE PROFILE` and appends exactly one LF byte followed by this
section, with one final LF after its closing fence:

````text
## 14. Acceptance record

```text
profile: pff-draft-binding-mutation-qualification/0.2
status: accepted
accepted_on: <YYYY-MM-DD>
reviewed_candidate_sha256: sha256:<64 lowercase hexadecimal digits>
recipe_manifest_sha256: sha256:<64 lowercase hexadecimal digits>
superseded_profile_sha256: sha256:<64 lowercase hexadecimal digits>
review_result: architecture=clean; determinacy=clean; criteria=clean
```
````

`reviewed_candidate_sha256` covers the complete candidate profile bytes,
including their existing final LF. `recipe_manifest_sha256` must equal
section 1's preserved manifest hash and `superseded_profile_sha256` must equal
section 1.1's accepted v0.1 profile hash. Neither accepted input is transformed
during acceptance. The record binds candidate and predecessor identities but
never its own accepted-profile hash or commit, so it is non-circular. No other
profile or manifest byte may change. This candidate itself grants no
implementation or execution authority: accepted v0.1 remains the governing
qualification authority until the transformed v0.2 profile is accepted and
published. Implementation repair may begin only from that published v0.2
authority, and controlled mutation execution remains forbidden until the
affected tool and tests have been re-derived, independently reviewed,
published, and preflight-authenticated against it.

## 14. Acceptance record

```text
profile: pff-draft-binding-mutation-qualification/0.2
status: accepted
accepted_on: 2026-08-19
reviewed_candidate_sha256: sha256:f48282a5873e7a8c6d87aad1afa1188a3c605757ebb2133029d2423d3a2a670c
recipe_manifest_sha256: sha256:2e967a8a37e90ea63928239040d852225620a42d391951f75ee02f20dea325e2
superseded_profile_sha256: sha256:0e2ca55cb31ef815f2674723d152ff1856057f25c0fcbace88d0810569ab959d
review_result: architecture=clean; determinacy=clean; criteria=clean
```
