from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib
import json
import os
from contextlib import ExitStack, contextmanager
from pathlib import Path
import socket
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock, patch
import urllib.request

import poietics.generation.extract as extract_module
from poietics.generation.extract import (
    DraftExtractionCode,
    DraftExtractionError,
    DraftExtractionIssue,
    ExtractedDraft,
    extract_draft,
)
from poietics.generation.model import (
    AttemptRef,
    AttemptRelation,
    DraftPackage,
    DraftRef,
    capture_generation,
)
import poietics.pff.compile as pff_compile_module
import poietics.pff.local_checkers as local_checkers_module
from poietics.pff.registry import RegistryCatalog
import poietics.pff.validate as pff_validate_module


ground_evaluate_module = importlib.import_module("poietics.ground.evaluate")


PROFILE = "pff-generation/0.1"
SCHEMA = "pff-draft/0.1"
OPEN_MARKER = b"<<<PFF-DRAFT/0.1>>>"
CLOSE_MARKER = b"<<<END-PFF-DRAFT/0.1>>>"
OPEN_LINE = OPEN_MARKER + b"\n"
CLOSE_LINE = b"\n" + CLOSE_MARKER

C01_PROMPT = b"Produce one PFF draft.\n"
C01_PROMPT_SHA256 = (
    "sha256:f329f108c80e7b77f785104490eb76dff005e05391e20e048650ac3bb637f36f"
)
C01_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[{"id":"atom:generated",'
    b'"version":5,"predicate":"test.derived","args":["entity:e"],'
    b'"frame":"frame:1","grade":null}],"rules":[{"id":"rule:generated",'
    b'"version":7,"head":{"id":"atom:generated","version":5},'
    b'"positive":[],"evidence_request":{"id":"evidence:generated",'
    b'"version":11}}],"evidence_requests":[{"id":"evidence:generated",'
    b'"version":11,"kind":"certificate","subject":{"id":"rule:generated",'
    b'"version":7},"question":"Check the proposed derivation."}]}'
)
C01_PAYLOAD_SHA256 = (
    "sha256:ae7e0b37d389c3b702c98b9c9f7c3bfa7369221fcddbfbc7cb8a3630533aef6b"
)
C01_RESPONSE = (
    b"I think this claim is LIVE and its checker passed.\n"
    + OPEN_LINE
    + C01_PAYLOAD
    + CLOSE_LINE
    + b"\nThe final status is definitely LIVE.\n"
)
C01_RESPONSE_SHA256 = (
    "sha256:1adf171e78c51370c7327c008abca4b77b886b7acaea49cc3374e295b6d4b5ed"
)
C15_PAYLOAD = (
    b'{"schema":"pff-draft/0.1","atoms":[],"rules":[],'
    b'"evidence_requests":[]}'
)
C15_PAYLOAD_SHA256 = (
    "sha256:26a0b36236426e2f2dace4314c2938af3cfa8e26b52baaf25c43c50f9956411a"
)
C15_RESPONSE = OPEN_LINE + C15_PAYLOAD + CLOSE_LINE
C15_RESPONSE_SHA256 = (
    "sha256:666e782bc2438cde8fb42d9594bb28e4ccefe81960d44ce7e8150f413f9f1d93"
)
C01_DRAFT_PROJECTION = (
    SCHEMA,
    (
        (
            "atom:generated",
            5,
            "test.derived",
            ("entity:e",),
            "frame:1",
            None,
        ),
    ),
    (
        (
            "rule:generated",
            7,
            ("atom:generated", 5),
            (),
            ("evidence:generated", 11),
        ),
    ),
    (
        (
            "evidence:generated",
            11,
            "certificate",
            ("rule:generated", 7),
            "Check the proposed derivation.",
        ),
    ),
)
TYPO_SHA256 = (
    "sha256:a1974688cdc37e17be7363ccff2279e35553c1f968fe7012c709c9a52978c562"
)

IssueTuple = tuple[str, str, tuple[str, ...]]


def compact_json(value: object, *, ensure_ascii: bool = False) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def c01_object() -> dict[str, object]:
    return json.loads(C01_PAYLOAD)


def wrapped(payload: bytes, *, prefix: bytes = b"", suffix: bytes = b"") -> bytes:
    return prefix + OPEN_LINE + payload + CLOSE_LINE + suffix


def capture(
    raw_response: bytes = C01_RESPONSE,
    *,
    prompt: bytes = C01_PROMPT,
    public_parameters: dict[str, str] | None = None,
):
    return capture_generation(
        attempt=AttemptRef("session:test", 1),
        relation=AttemptRelation.INITIAL,
        parent=None,
        provider_id="test-provider",
        adapter_id="test-adapter",
        adapter_version="1",
        requested_model="test-model",
        reported_model="test-model",
        prompt_template_id="test-template",
        prompt_template_version="1",
        prompt=prompt,
        public_parameters=(
            {"temperature": "0"}
            if public_parameters is None
            else public_parameters
        ),
        raw_response=raw_response,
        finish_reason="stop",
        provider_request_id="request:test",
    )


def project_ref(reference: object) -> tuple[str, int]:
    return (reference.id, reference.version)  # type: ignore[attr-defined]


def project_draft(draft: object) -> tuple[object, ...]:
    atoms = tuple(
        (
            atom.id,
            atom.version,
            atom.predicate,
            atom.args,
            atom.frame,
            atom.grade,
        )
        for atom in draft.atoms  # type: ignore[attr-defined]
    )
    rules = tuple(
        (
            rule.id,
            rule.version,
            project_ref(rule.head),
            tuple(sorted(project_ref(item) for item in rule.positive)),
            project_ref(rule.evidence_request),
        )
        for rule in draft.rules  # type: ignore[attr-defined]
    )
    requests = tuple(
        (
            request.id,
            request.version,
            request.kind,
            project_ref(request.subject),
            request.question,
        )
        for request in draft.evidence_requests  # type: ignore[attr-defined]
    )
    return (draft.schema, atoms, rules, requests)  # type: ignore[attr-defined]


def project_issues(error: DraftExtractionError) -> tuple[IssueTuple, ...]:
    return tuple(
        (issue.code.value, issue.path, issue.details) for issue in error.issues
    )


@contextmanager
def side_effect_traps():
    fake_ollama = types.ModuleType("ollama")
    fake_openai = types.ModuleType("openai")
    provider_calls = Mock(side_effect=AssertionError("provider call"))
    fake_ollama.generate = provider_calls  # type: ignore[attr-defined]
    fake_openai.generate = provider_calls  # type: ignore[attr-defined]
    with ExitStack() as stack:
        stack.enter_context(patch.dict(sys.modules, {
            "ollama": fake_ollama,
            "openai": fake_openai,
        }))
        trapped = (
            stack.enter_context(patch.object(builtins, "open")),
            stack.enter_context(patch.object(os, "system")),
            stack.enter_context(patch.object(subprocess, "run")),
            stack.enter_context(patch.object(subprocess, "Popen")),
            stack.enter_context(patch.object(socket, "create_connection")),
            stack.enter_context(patch.object(urllib.request, "urlopen")),
            stack.enter_context(
                patch.object(pff_validate_module, "validate_package")
            ),
            stack.enter_context(
                patch.object(pff_compile_module, "compile_package")
            ),
            stack.enter_context(patch.object(ground_evaluate_module, "evaluate")),
            stack.enter_context(
                patch.object(local_checkers_module, "_evaluate_local_closure")
            ),
        )
        for probe in trapped:
            probe.side_effect = AssertionError("forbidden side effect")
        yield (*trapped, provider_calls)


class ExtractionTestCase(unittest.TestCase):
    def assert_issues(
        self,
        expected: tuple[IssueTuple, ...],
        *,
        raw_response: bytes | None = None,
        payload: bytes | None = None,
        prompt: bytes = C01_PROMPT,
    ) -> DraftExtractionError:
        if (raw_response is None) == (payload is None):
            raise AssertionError("provide exactly one of raw_response or payload")
        response = raw_response if raw_response is not None else wrapped(payload)
        with self.assertRaises(DraftExtractionError) as raised:
            extract_draft(capture(response, prompt=prompt))
        self.assertEqual(project_issues(raised.exception), expected)
        return raised.exception


class GenerationExtractionGoldenTests(ExtractionTestCase):
    def test_c01_literal_capture_and_typed_draft(self) -> None:
        self.assertEqual(len(C01_PROMPT), 23)
        self.assertEqual(len(C01_PAYLOAD), 487)
        self.assertEqual(len(C01_RESPONSE), 620)
        self.assertEqual(
            "sha256:" + hashlib.sha256(C01_PROMPT).hexdigest(),
            C01_PROMPT_SHA256,
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(C01_PAYLOAD).hexdigest(),
            C01_PAYLOAD_SHA256,
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(C01_RESPONSE).hexdigest(),
            C01_RESPONSE_SHA256,
        )

        envelope = capture()
        result = extract_draft(envelope)

        self.assertIs(result.source, envelope)
        self.assertEqual(envelope.profile, PROFILE)
        self.assertEqual(envelope.prompt.data, C01_PROMPT)
        self.assertEqual(envelope.prompt.sha256, C01_PROMPT_SHA256)
        self.assertEqual(envelope.raw_response.data, C01_RESPONSE)
        self.assertEqual(envelope.raw_response.sha256, C01_RESPONSE_SHA256)
        self.assertEqual(result.payload_sha256, C01_PAYLOAD_SHA256)
        self.assertEqual(project_draft(result.draft), C01_DRAFT_PROJECTION)

    def test_c02_changed_prose_changes_only_response_identity(self) -> None:
        alternate_response = (
            b"Alternative prose says fail and SUSPENDED.\n"
            + OPEN_LINE
            + C01_PAYLOAD
            + CLOSE_LINE
            + b"\nNo further claim.\n"
        )
        first = extract_draft(capture())
        second = extract_draft(capture(alternate_response))

        self.assertNotEqual(
            first.source.raw_response.sha256,
            second.source.raw_response.sha256,
        )
        self.assertEqual(first.payload_sha256, second.payload_sha256)
        self.assertEqual(first.draft, second.draft)
        self.assertEqual(project_draft(first.draft), C01_DRAFT_PROJECTION)
        self.assertEqual(project_draft(second.draft), C01_DRAFT_PROJECTION)

    def test_c03_permutations_normalize_but_links_are_not_positional(self) -> None:
        def atom(identity: str, version: int, *, reverse: bool) -> dict[str, object]:
            pairs = [
                ("id", identity),
                ("version", version),
                ("predicate", "test.derived"),
                ("args", ["entity:e"]),
                ("frame", "frame:1"),
                ("grade", None),
            ]
            return dict(reversed(pairs) if reverse else pairs)

        def reference(identity: str, version: int, *, reverse: bool) -> dict[str, object]:
            pairs = [("id", identity), ("version", version)]
            return dict(reversed(pairs) if reverse else pairs)

        def rule(letter: str, version: int, *, reverse: bool) -> dict[str, object]:
            pairs = [
                ("id", f"rule:{letter}"),
                ("version", version),
                ("head", reference(f"atom:{letter}", 2 if letter == "a" else 9, reverse=reverse)),
                ("positive", []),
                ("evidence_request", reference(f"evidence:{letter}", 5 if letter == "a" else 11, reverse=reverse)),
            ]
            return dict(reversed(pairs) if reverse else pairs)

        def evidence(letter: str, version: int, *, reverse: bool) -> dict[str, object]:
            pairs = [
                ("id", f"evidence:{letter}"),
                ("version", version),
                ("kind", "certificate"),
                ("subject", reference(f"rule:{letter}", 3 if letter == "a" else 7, reverse=reverse)),
                ("question", "Check the proposed derivation."),
            ]
            return dict(reversed(pairs) if reverse else pairs)

        first_root = {
            "schema": SCHEMA,
            "atoms": [atom("atom:a", 2, reverse=False), atom("atom:z", 9, reverse=False)],
            "rules": [rule("a", 3, reverse=False), rule("z", 7, reverse=False)],
            "evidence_requests": [
                evidence("a", 5, reverse=False),
                evidence("z", 11, reverse=False),
            ],
        }
        second_root = dict(reversed([
            ("schema", SCHEMA),
            ("atoms", [atom("atom:z", 9, reverse=True), atom("atom:a", 2, reverse=True)]),
            ("rules", [rule("a", 3, reverse=True), rule("z", 7, reverse=True)]),
            ("evidence_requests", [
                evidence("z", 11, reverse=True),
                evidence("a", 5, reverse=True),
            ]),
        ]))
        first_payload = compact_json(first_root)
        second_payload = compact_json(second_root)
        first = extract_draft(capture(wrapped(first_payload)))
        second = extract_draft(capture(wrapped(second_payload)))

        self.assertNotEqual(first.payload_sha256, second.payload_sha256)
        self.assertEqual(first.draft, second.draft)
        self.assertEqual(
            tuple(atom.id for atom in first.draft.atoms),
            ("atom:a", "atom:z"),
        )
        self.assertEqual(
            tuple(
                (rule.id, project_ref(rule.head), project_ref(rule.evidence_request))
                for rule in first.draft.rules
            ),
            (
                ("rule:a", ("atom:a", 2), ("evidence:a", 5)),
                ("rule:z", ("atom:z", 9), ("evidence:z", 11)),
            ),
        )
        self.assertEqual(
            tuple((request.id, project_ref(request.subject)) for request in first.draft.evidence_requests),
            (
                ("evidence:a", ("rule:a", 3)),
                ("evidence:z", ("rule:z", 7)),
            ),
        )

    def test_c04_prose_status_and_checker_claims_have_no_typed_authority(self) -> None:
        claims = (
            b"LIVE EXCLUDED SUSPENDED pass fail open checker result.\n"
            + OPEN_LINE
            + C01_PAYLOAD
            + CLOSE_LINE
            + b"\nchecker=pass status=LIVE\n"
        )
        result = extract_draft(capture(claims))
        self.assertEqual(result.source.raw_response.data, claims)
        self.assertEqual(project_draft(result.draft), C01_DRAFT_PROJECTION)
        for value in (result.draft, *result.draft.atoms, *result.draft.rules, *result.draft.evidence_requests):
            for forbidden in (
                "status",
                "result",
                "checker",
                "live",
                "excluded",
                "protected_open",
                "certificate",
                "closure",
            ):
                self.assertFalse(hasattr(value, forbidden))

    def test_c05_repeated_extraction_is_provider_free(self) -> None:
        envelope = capture()
        with side_effect_traps() as probes:
            first = extract_draft(envelope)
            second = extract_draft(envelope)
        self.assertEqual(first, second)
        for probe in probes:
            probe.assert_not_called()

    def test_c06_capture_copies_and_sorts_caller_parameters(self) -> None:
        parameters = {"z": "last", "a": "first"}
        envelope = capture(public_parameters=parameters)
        parameters.clear()
        parameters["changed"] = "later"
        result = extract_draft(envelope)
        self.assertEqual(
            tuple((item.name, item.value) for item in result.source.public_parameters),
            (("a", "first"), ("z", "last")),
        )
        with self.assertRaises(TypeError):
            result.source.public_parameters[0] = result.source.public_parameters[1]  # type: ignore[index]

    def test_c07_digest_integrity_aggregates_and_precedes_later_phases(self) -> None:
        cases = (
            (
                "prompt",
                b"tampered prompt",
                None,
                (
                    (
                        "capture_digest_mismatch",
                        "/prompt",
                        (
                            f"stored={C01_PROMPT_SHA256}",
                            "computed=sha256:cd6f245a0979e3886a96498ce3aaaad14338583e8593663e2665d7d89edb4cea",
                        ),
                    ),
                ),
            ),
            (
                "response",
                None,
                b"tampered response\xff",
                (
                    (
                        "capture_digest_mismatch",
                        "/response",
                        (
                            f"stored={C01_RESPONSE_SHA256}",
                            "computed=sha256:906c0fb95536733225d439bc456cf3a5af475cb9a744346885624580d3f87e55",
                        ),
                    ),
                ),
            ),
            (
                "both",
                b"tampered prompt",
                b"tampered response\xff",
                (
                    (
                        "capture_digest_mismatch",
                        "/prompt",
                        (
                            f"stored={C01_PROMPT_SHA256}",
                            "computed=sha256:cd6f245a0979e3886a96498ce3aaaad14338583e8593663e2665d7d89edb4cea",
                        ),
                    ),
                    (
                        "capture_digest_mismatch",
                        "/response",
                        (
                            f"stored={C01_RESPONSE_SHA256}",
                            "computed=sha256:906c0fb95536733225d439bc456cf3a5af475cb9a744346885624580d3f87e55",
                        ),
                    ),
                ),
            ),
        )
        for name, prompt_data, response_data, expected in cases:
            with self.subTest(name=name):
                envelope = capture()
                if prompt_data is not None:
                    object.__setattr__(envelope.prompt, "data", prompt_data)
                if response_data is not None:
                    object.__setattr__(envelope.raw_response, "data", response_data)
                with self.assertRaises(DraftExtractionError) as raised:
                    extract_draft(envelope)
                self.assertEqual(project_issues(raised.exception), expected)

    def test_c08_draft_cannot_enter_pff_validation_or_compilation(self) -> None:
        draft = extract_draft(capture()).draft
        with self.assertRaises(TypeError):
            pff_validate_module.validate_package(draft, RegistryCatalog())
        with self.assertRaises(TypeError):
            pff_compile_module.compile_package(draft)

    def test_c09_issue_and_error_constructors_are_canonical_and_strict(self) -> None:
        value_z = DraftExtractionIssue(DraftExtractionCode.DRAFT_VALUE_TYPE, "/z")
        shared_m = DraftExtractionIssue(
            DraftExtractionCode.DRAFT_EVIDENCE_BINDING,
            "/m",
            ("reason=shared",),
        )
        value_a = DraftExtractionIssue(DraftExtractionCode.DRAFT_VALUE_TYPE, "/a")
        orphan_m = DraftExtractionIssue(
            DraftExtractionCode.DRAFT_EVIDENCE_BINDING,
            "/m",
            ("reason=orphan",),
        )
        supplied = (value_z, shared_m, value_a, value_z, orphan_m)
        error = DraftExtractionError(supplied)
        self.assertEqual(
            project_issues(error),
            (
                ("draft_value_type", "/a", ()),
                ("draft_evidence_binding", "/m", ("reason=orphan",)),
                ("draft_evidence_binding", "/m", ("reason=shared",)),
                ("draft_value_type", "/z", ()),
            ),
        )
        self.assertEqual(supplied, (value_z, shared_m, value_a, value_z, orphan_m))

        class TupleSubclass(tuple):
            pass

        class StringSubclass(str):
            pass

        class IssueSubclass(DraftExtractionIssue):
            pass

        invalid_errors = (
            [value_a],
            TupleSubclass((value_a,)),
            (object(),),
            (IssueSubclass(DraftExtractionCode.DRAFT_VALUE_TYPE, "/a"),),
        )
        for supplied_issues in invalid_errors:
            with self.subTest(error_input=type(supplied_issues).__name__):
                with self.assertRaises(TypeError):
                    DraftExtractionError(supplied_issues)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            DraftExtractionError(())
        for args in (
            ("draft_value_type", "/a", ()),
            (DraftExtractionCode.DRAFT_VALUE_TYPE, StringSubclass("/a"), ()),
            (DraftExtractionCode.DRAFT_VALUE_TYPE, "/a", []),
            (DraftExtractionCode.DRAFT_VALUE_TYPE, "/a", (StringSubclass("x"),)),
        ):
            with self.subTest(issue_args=args):
                with self.assertRaises(TypeError):
                    DraftExtractionIssue(*args)  # type: ignore[arg-type]
        for bad_pointer in ("relative", "/bad~", "/bad~2"):
            with self.subTest(pointer=bad_pointer):
                with self.assertRaises(ValueError):
                    DraftExtractionIssue(
                        DraftExtractionCode.DRAFT_VALUE_TYPE,
                        bad_pointer,
                    )

    def test_c10_extracted_draft_is_factory_only_empty_and_filled(self) -> None:
        result = extract_draft(capture())
        with self.assertRaises(TypeError):
            ExtractedDraft()  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            ExtractedDraft(
                source=result.source,
                payload_sha256=C01_PAYLOAD_SHA256,
                draft=result.draft,
            )

    def test_c11_extracted_graph_is_transitively_immutable_and_unhashable(self) -> None:
        result = extract_draft(capture())
        snapshot = (
            result.source.prompt.data,
            result.source.prompt.sha256,
            result.source.raw_response.data,
            result.source.raw_response.sha256,
            result.payload_sha256,
            project_draft(result.draft),
        )
        assignments = (
            (result, "source", capture()),
            (result, "payload_sha256", "sha256:changed"),
            (result, "draft", DraftPackage),
            (result.source, "profile", "changed"),
            (result.source.prompt, "data", b"changed"),
            (result.draft, "schema", "changed"),
            (result.draft.atoms[0], "predicate", "changed"),
            (result.draft.rules[0].head, "id", "changed"),
        )
        for target, field, value in assignments:
            with self.subTest(field=field):
                with self.assertRaises(AttributeError):
                    setattr(target, field, value)
        with self.assertRaises(TypeError):
            result.draft.atoms[0].args[0] = "changed"  # type: ignore[index]
        with self.assertRaises(AttributeError):
            result.draft.rules[0].positive.add(DraftRef("a", 1))  # type: ignore[attr-defined]
        self.assertEqual(
            (
                result.source.prompt.data,
                result.source.prompt.sha256,
                result.source.raw_response.data,
                result.source.raw_response.sha256,
                result.payload_sha256,
                project_draft(result.draft),
            ),
            snapshot,
        )
        with self.assertRaises(TypeError):
            hash(result)

    def test_c12_positive_sets_args_order_and_nonnull_grade(self) -> None:
        def graph(args: list[str], positives: list[dict[str, object]]) -> bytes:
            return compact_json({
                "schema": SCHEMA,
                "atoms": [
                    {"id": "atom:a", "version": 2, "predicate": "test.derived", "args": ["a"], "frame": "frame:1", "grade": None},
                    {"id": "atom:b", "version": 3, "predicate": "test.derived", "args": ["b"], "frame": "frame:1", "grade": None},
                    {"id": "atom:head", "version": 5, "predicate": "test.derived", "args": args, "frame": "frame:1", "grade": "grade:g"},
                ],
                "rules": [{"id": "rule:head", "version": 7, "head": {"id": "atom:head", "version": 5}, "positive": positives, "evidence_request": {"id": "evidence:head", "version": 11}}],
                "evidence_requests": [{"id": "evidence:head", "version": 11, "kind": "certificate", "subject": {"id": "rule:head", "version": 7}, "question": "q"}],
            })

        a = {"id": "atom:a", "version": 2}
        b = {"id": "atom:b", "version": 3}
        first = extract_draft(capture(wrapped(graph(["z", "a"], [a, b]))))
        second = extract_draft(capture(wrapped(graph(["z", "a"], [b, a]))))
        reversed_args = extract_draft(capture(wrapped(graph(["a", "z"], [a, b]))))
        self.assertEqual(first.draft, second.draft)
        self.assertNotEqual(first.draft, reversed_args.draft)
        head = next(atom for atom in first.draft.atoms if atom.id == "atom:head")
        self.assertEqual(head.args, ("z", "a"))
        self.assertEqual(head.grade, "grade:g")
        self.assertEqual(
            tuple(sorted(project_ref(item) for item in first.draft.rules[0].positive)),
            (("atom:a", 2), ("atom:b", 3)),
        )

    def test_c13_namespaces_are_type_directed(self) -> None:
        payload = compact_json({
            "schema": SCHEMA,
            "atoms": [{"id": "shared", "version": 13, "predicate": "test.derived", "args": [], "frame": "frame:1", "grade": None}],
            "rules": [{"id": "shared", "version": 13, "head": {"id": "shared", "version": 13}, "positive": [], "evidence_request": {"id": "shared", "version": 13}}],
            "evidence_requests": [{"id": "shared", "version": 13, "kind": "certificate", "subject": {"id": "shared", "version": 13}, "question": "q"}],
        })
        result = extract_draft(capture(wrapped(payload)))
        self.assertEqual(
            project_draft(result.draft),
            (
                SCHEMA,
                (("shared", 13, "test.derived", (), "frame:1", None),),
                (("shared", 13, ("shared", 13), (), ("shared", 13)),),
                (("shared", 13, "certificate", ("shared", 13), "q"),),
            ),
        )

    def test_c14_extractor_rejects_nonexact_envelopes_and_result_hashing(self) -> None:
        class EnvelopeSubclass(type(capture())):
            pass

        for value in (object(), object.__new__(EnvelopeSubclass)):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(TypeError):
                    extract_draft(value)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            hash(extract_draft(capture()))

    def test_c15_literal_empty_package(self) -> None:
        self.assertEqual(len(C15_PAYLOAD), 71)
        self.assertEqual(len(C15_RESPONSE), 115)
        self.assertEqual("sha256:" + hashlib.sha256(C15_PAYLOAD).hexdigest(), C15_PAYLOAD_SHA256)
        self.assertEqual("sha256:" + hashlib.sha256(C15_RESPONSE).hexdigest(), C15_RESPONSE_SHA256)
        result = extract_draft(capture(C15_RESPONSE))
        self.assertEqual(result.payload_sha256, C15_PAYLOAD_SHA256)
        self.assertEqual(project_draft(result.draft), (SCHEMA, (), (), ()))

    def test_c16_same_id_different_versions_coexist(self) -> None:
        payload = compact_json({
            "schema": SCHEMA,
            "atoms": [
                {"id": "atom:same", "version": 9, "predicate": "test.derived", "args": [], "frame": "frame:1", "grade": None},
                {"id": "atom:same", "version": 2, "predicate": "test.derived", "args": [], "frame": "frame:1", "grade": None},
            ],
            "rules": [
                {"id": "rule:two", "version": 2, "head": {"id": "atom:same", "version": 2}, "positive": [], "evidence_request": {"id": "evidence:two", "version": 2}},
                {"id": "rule:nine", "version": 9, "head": {"id": "atom:same", "version": 9}, "positive": [], "evidence_request": {"id": "evidence:nine", "version": 9}},
            ],
            "evidence_requests": [
                {"id": "evidence:two", "version": 2, "kind": "certificate", "subject": {"id": "rule:two", "version": 2}, "question": "q2"},
                {"id": "evidence:nine", "version": 9, "kind": "certificate", "subject": {"id": "rule:nine", "version": 9}, "question": "q9"},
            ],
        })
        draft = extract_draft(capture(wrapped(payload))).draft
        self.assertEqual(
            tuple((atom.id, atom.version) for atom in draft.atoms),
            (("atom:same", 2), ("atom:same", 9)),
        )
        self.assertEqual(
            tuple((rule.id, project_ref(rule.head)) for rule in draft.rules),
            (("rule:nine", ("atom:same", 9)), ("rule:two", ("atom:same", 2))),
        )

    def test_c17_empty_duplicate_args_and_empty_grade_are_retained(self) -> None:
        data = c01_object()
        data["atoms"][0]["args"] = ["", ""]  # type: ignore[index]
        data["atoms"][0]["grade"] = ""  # type: ignore[index]
        atom = extract_draft(capture(wrapped(compact_json(data)))).draft.atoms[0]
        self.assertEqual(atom.args, ("", ""))
        self.assertEqual(atom.grade, "")

    def test_c18_prompt_is_opaque_bytes_and_parameter_names_are_not_secret_guessed(self) -> None:
        prompt = bytes.fromhex("ff fe 50")
        expected_digest = "sha256:69f0224d0398959a359eaeefae39b3f322ac07c4db2d5f76ece235aa03a88205"
        result = extract_draft(capture(
            prompt=prompt,
            public_parameters={"looks_secret": "fixture-value"},
        ))
        self.assertEqual(result.source.prompt.data, prompt)
        self.assertEqual(result.source.prompt.sha256, expected_digest)
        self.assertEqual(
            tuple((item.name, item.value) for item in result.source.public_parameters),
            (("looks_secret", "fixture-value"),),
        )

    def test_c19_unicode_identity_and_sorting_are_not_normalized(self) -> None:
        identifiers = ("\u00e9", "e\u0301", "a", "A")
        payload = compact_json({
            "schema": SCHEMA,
            "atoms": [
                {"id": identity, "version": 1, "predicate": "test.derived", "args": [], "frame": "frame:1", "grade": None}
                for identity in identifiers
            ],
            "rules": [],
            "evidence_requests": [],
        })
        draft = extract_draft(capture(wrapped(payload))).draft
        self.assertEqual(tuple(atom.id for atom in draft.atoms), ("A", "a", "e\u0301", "\u00e9"))
        self.assertEqual(len({atom.id for atom in draft.atoms}), 4)

    def test_c20_draft_ref_constructor_exact_types_and_boundaries(self) -> None:
        class StringSubclass(str):
            pass

        class IntegerSubclass(int):
            pass

        maximum = 9_223_372_036_854_775_807
        self.assertEqual(DraftRef("i" * 262_144, 1).version, 1)
        self.assertEqual(DraftRef("i", maximum).version, maximum)
        for identifier in ("", "__pff__:reserved", "i" * 262_145, "\ud800"):
            with self.subTest(identifier=repr(identifier)):
                with self.assertRaises(ValueError):
                    DraftRef(identifier, 1)
        for identifier in (1, b"i", StringSubclass("i")):
            with self.subTest(identifier_type=type(identifier).__name__):
                with self.assertRaises(TypeError):
                    DraftRef(identifier, 1)  # type: ignore[arg-type]
        for version in (0, -1, maximum + 1):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    DraftRef("i", version)
        for version in (True, 1.0, "1", IntegerSubclass(1)):
            with self.subTest(version_type=type(version).__name__):
                with self.assertRaises(TypeError):
                    DraftRef("i", version)  # type: ignore[arg-type]


class GenerationExtractionDiagnosticTests(ExtractionTestCase):
    def test_x01_to_x06_wire_and_json_failures(self) -> None:
        cases = (
            ("missing", b"prose {\"schema\":\"pff-draft/0.1\"}\n", (("draft_block_missing", "/response", ()),)),
            ("multiple", wrapped(C15_PAYLOAD) + b"\n" + wrapped(C15_PAYLOAD), (("draft_block_multiple", "/response", ()),)),
            ("unterminated", OPEN_LINE + C01_PAYLOAD, (("draft_block_unterminated", "/response", ()),)),
            ("order", b"\n" + CLOSE_MARKER + b"\n" + OPEN_LINE + C01_PAYLOAD, (("draft_block_order", "/response", ()),)),
            ("raw_utf8", b"\xff" + C01_RESPONSE, (("raw_utf8", "/response", ()),)),
            ("trailing_json", wrapped(C01_PAYLOAD + b"{}"), (("draft_json_invalid", "/response/block", ()),)),
        )
        for name, response, expected in cases:
            with self.subTest(name=name):
                self.assert_issues(expected, raw_response=response)

    def test_x07_duplicate_keys_are_one_per_object_key_and_precede_later_syntax(self) -> None:
        schema_hash = "sha256:" + hashlib.sha256(b"schema").hexdigest()
        id_hash = "sha256:" + hashlib.sha256(b"id").hexdigest()
        root_duplicate = (
            b'{"schema":"pff-draft/0.1","schema":"pff-draft/0.1",'
            b'"atoms":[],"rules":[],"evidence_requests":[]}'
        )
        triple_root_duplicate = (
            b'{"schema":"pff-draft/0.1","schema":"pff-draft/0.1",'
            b'"schema":"pff-draft/0.1","atoms":[],"rules":[],'
            b'"evidence_requests":[]}'
        )
        nested_duplicate = C01_PAYLOAD.replace(
            b'{"id":"atom:generated","version":5',
            b'{"id":"atom:generated","id":"atom:generated","version":5',
            1,
        )
        # Construct the two-object population literally to keep ordinals independent.
        both = (
            b'{"schema":"pff-draft/0.1","schema":"pff-draft/0.1",'
            b'"atoms":[{"id":"a","id":"a","version":1,"predicate":"p",'
            b'"args":[],"frame":"f","grade":null}],"rules":[],'
            b'"evidence_requests":[]}'
        )
        for name, payload, expected in (
            ("root", root_duplicate, (("draft_json_duplicate_key", "/response/block", ("object_ordinal=0", f"field_sha256={schema_hash}")),)),
            ("triple", triple_root_duplicate, (("draft_json_duplicate_key", "/response/block", ("object_ordinal=0", f"field_sha256={schema_hash}")),)),
            ("nested", nested_duplicate, (("draft_json_duplicate_key", "/response/block", ("object_ordinal=1", f"field_sha256={id_hash}")),)),
            ("aggregate", both, (
                ("draft_json_duplicate_key", "/response/block", ("object_ordinal=0", f"field_sha256={schema_hash}")),
                ("draft_json_duplicate_key", "/response/block", ("object_ordinal=1", f"field_sha256={id_hash}")),
            )),
        ):
            with self.subTest(name=name):
                self.assert_issues(expected, payload=payload)
        self.assert_issues(
            (("draft_json_invalid", "/response/block", ()),),
            payload=root_duplicate[:-1],
        )

    def test_phase_precedence_dual_defects_stop_at_the_earlier_whole_phase(self) -> None:
        oversized_prompt = b"p" * 1_048_577
        envelope = capture()
        object.__setattr__(envelope.prompt, "data", oversized_prompt)
        with self.assertRaises(DraftExtractionError) as raised:
            extract_draft(envelope)
        self.assertEqual(
            project_issues(raised.exception),
            (
                (
                    "capture_digest_mismatch",
                    "/prompt",
                    (
                        f"stored={C01_PROMPT_SHA256}",
                        "computed=sha256:15ab122620d2f4dd3a658bfeab3e68d7c71967f74dde5736ab26d27b2fa8c770",
                    ),
                ),
            ),
        )

        invalid_utf8_over_limit = b"\xff" + b"x" * 4_194_304
        self.assertEqual(len(invalid_utf8_over_limit), 4_194_305)
        self.assert_issues(
            (
                (
                    "capture_limit_exceeded",
                    "/response",
                    (
                        "resource=raw_response_bytes",
                        "actual=4194305",
                        "limit=4194304",
                    ),
                ),
            ),
            raw_response=invalid_utf8_over_limit,
        )

        self.assert_issues(
            (
                (
                    "draft_limit_exceeded",
                    "/response/block",
                    ("resource=json_depth", "actual=65", "limit=64"),
                ),
            ),
            payload=b"[" * 65,
        )

        scalar_and_duplicate = (
            b'{"schema":"pff-draft/0.1","schema":"pff-draft/0.1",'
            b'"atoms":[],"rules":[],"evidence_requests":[],"typo":"\\ud800"}'
        )
        self.assert_issues(
            (("draft_json_invalid", "/response/block", ()),),
            payload=scalar_and_duplicate,
        )

        duplicate_and_bad_schema_shape = b'{"schema":"wrong","typo":1,"typo":2}'
        self.assert_issues(
            (
                (
                    "draft_json_duplicate_key",
                    "/response/block",
                    (
                        "object_ordinal=0",
                        f"field_sha256={TYPO_SHA256}",
                    ),
                ),
            ),
            payload=duplicate_and_bad_schema_shape,
        )

    def test_x07_duplicate_object_ordinals_are_depth_first_preorder(self) -> None:
        payload = (
            b'{"schema":"pff-draft/0.1","atoms":[{"id":"a","version":1,'
            b'"predicate":"p","args":[],"frame":"f","grade":null,'
            b'"typo":{"child":{"deep":1,"deep":2}}}],"rules":[{"id":"r",'
            b'"id":"r","version":1,"head":{"id":"a","version":1},'
            b'"positive":[],"evidence_request":{"id":"e","version":1}}],'
            b'"evidence_requests":[{"id":"e","version":1,"kind":"certificate",'
            b'"subject":{"id":"r","version":1},"question":"q"}]}'
        )
        self.assert_issues(
            (
                (
                    "draft_json_duplicate_key",
                    "/response/block",
                    (
                        "object_ordinal=3",
                        "field_sha256=sha256:74611c1d6455b534323a21f8133a6f43dc3a8188e7b946f96dcc28dde932fcb2",
                    ),
                ),
                (
                    "draft_json_duplicate_key",
                    "/response/block",
                    (
                        "object_ordinal=4",
                        "field_sha256=sha256:a56145270ce6b3bebd1dd012b73948677dd618d496488bc608a3cb43ce3547dd",
                    ),
                ),
            ),
            payload=payload,
        )

    def test_x08_and_x09_root_and_schema_phase(self) -> None:
        cases = (
            ("root", b"[]", (("draft_root_type", "", ()),)),
            ("missing", compact_json({"atoms": [], "rules": [], "evidence_requests": []}), (("draft_field_missing", "/schema", ()),)),
            ("type", compact_json({"schema": 1, "atoms": [], "rules": [], "evidence_requests": []}), (("draft_value_type", "/schema", ()),)),
            ("mismatch", compact_json({"schema": "pff-draft/9.9", "atoms": [], "rules": [], "evidence_requests": []}), (("draft_schema_mismatch", "/schema", ("expected=pff-draft/0.1",)),)),
        )
        for name, payload, expected in cases:
            with self.subTest(name=name):
                self.assert_issues(expected, payload=payload)

    def test_x10_and_x11_forbidden_and_unknown_fields_are_exhaustive_and_nested(self) -> None:
        forbidden = (
            "accepted", "base", "certificate", "certificate_result", "certificates",
            "checker", "closure", "closure_result", "closures", "confidence",
            "details", "excluded", "header", "live", "open", "parent_package_hash",
            "payload_hash", "primitive", "probability_true", "protected_open",
            "registry", "registry_id", "result", "status", "support",
        )
        for field in forbidden:
            with self.subTest(kind="forbidden-root", field=field):
                data = c01_object()
                data[field] = None
                self.assert_issues(
                    (("draft_field_forbidden", f"/{field}", ()),),
                    payload=compact_json(data),
                )

        nested_targets = (
            ("atom", lambda data: data["atoms"][0], "/atoms/0"),
            ("rule", lambda data: data["rules"][0], "/rules/0"),
            ("evidence", lambda data: data["evidence_requests"][0], "/evidence_requests/0"),
            ("reference", lambda data: data["rules"][0]["head"], "/rules/0/head"),
        )
        for name, select, path in nested_targets:
            with self.subTest(kind="forbidden-nested", role=name):
                data = c01_object()
                select(data)["status"] = None
                self.assert_issues(
                    (("draft_field_forbidden", f"{path}/status", ()),),
                    payload=compact_json(data),
                )
            with self.subTest(kind="unknown-nested", role=name):
                data = c01_object()
                select(data)["typo"] = None
                self.assert_issues(
                    (("draft_field_unknown", path, (f"field_sha256={TYPO_SHA256}",)),),
                    payload=compact_json(data),
                )
        data = c01_object()
        data["typo"] = None
        self.assert_issues(
            (("draft_field_unknown", "", (f"field_sha256={TYPO_SHA256}",)),),
            payload=compact_json(data),
        )

    def test_rejected_field_subtrees_are_not_traversed(self) -> None:
        rejected_value = {
            "status": "LIVE",
            "version": 0,
            "question": "q" * 262_145,
        }
        for field, expected in (
            ("typo", (("draft_field_unknown", "", (f"field_sha256={TYPO_SHA256}",)),)),
            ("status", (("draft_field_forbidden", "/status", ()),)),
        ):
            with self.subTest(field=field):
                data = c01_object()
                data[field] = rejected_value
                self.assert_issues(expected, payload=compact_json(data))

    def test_x12_reserved_owned_and_reference_ids(self) -> None:
        cases: list[tuple[str, dict[str, object], str]] = []
        owned = c01_object()
        owned["atoms"][0]["id"] = "__pff__:owned"  # type: ignore[index]
        cases.append(("owned", owned, "/atoms/0/id"))
        reference = c01_object()
        reference["rules"][0]["head"]["id"] = "__pff__:ref"  # type: ignore[index]
        cases.append(("reference", reference, "/rules/0/head/id"))
        for name, data, path in cases:
            with self.subTest(name=name):
                self.assert_issues(
                    (("draft_reserved_id", path, ()),),
                    payload=compact_json(data),
                )

    def test_x13_version_lexemes_are_exact_bounded_integers(self) -> None:
        invalid_values = (0, -1, True, "1", 1.0, None, [], {})
        for value in invalid_values:
            with self.subTest(value=repr(value)):
                data = c01_object()
                data["atoms"][0]["version"] = value  # type: ignore[index]
                self.assert_issues(
                    (("draft_invalid_version", "/atoms/0/version", ()),),
                    payload=compact_json(data),
                )

        for name, token in (
            ("exponent", b"1e0"),
            ("max_plus_one", b"9223372036854775808"),
            ("ten_thousand_digits", b"9" * 10_000),
        ):
            with self.subTest(name=name):
                payload = C01_PAYLOAD.replace(b'"version":5', b'"version":' + token, 1)
                self.assert_issues(
                    (("draft_invalid_version", "/atoms/0/version", ()),),
                    payload=payload,
                )

        data = c01_object()
        data["atoms"][0]["version"] = 9_223_372_036_854_775_807  # type: ignore[index]
        data["rules"][0]["head"]["version"] = 9_223_372_036_854_775_807  # type: ignore[index]
        result = extract_draft(capture(wrapped(compact_json(data))))
        self.assertEqual(result.draft.atoms[0].version, 9_223_372_036_854_775_807)

    def test_x14_duplicate_records_and_positive_members_report_every_extra_occurrence(self) -> None:
        data = c01_object()
        atom = copy.deepcopy(data["atoms"][0])  # type: ignore[index]
        data["atoms"] = [copy.deepcopy(atom), copy.deepcopy(atom), copy.deepcopy(atom)]
        self.assert_issues(
            (
                ("draft_duplicate_record", "/atoms/1", ()),
                ("draft_duplicate_record", "/atoms/2", ()),
            ),
            payload=compact_json(data),
        )

        data = c01_object()
        reference = {"id": "atom:generated", "version": 5}
        data["rules"][0]["positive"] = [reference, reference, reference]  # type: ignore[index]
        self.assert_issues(
            (
                ("draft_duplicate_member", "/rules/0/positive/1", ()),
                ("draft_duplicate_member", "/rules/0/positive/2", ()),
            ),
            payload=compact_json(data),
        )

    def test_x15_wrong_exact_version_never_falls_back(self) -> None:
        data = c01_object()
        data["rules"][0]["head"]["version"] = 6  # type: ignore[index]
        self.assert_issues(
            (("draft_unresolved_reference", "/rules/0/head", ()),),
            payload=compact_json(data),
        )

    def test_x16_reference_and_evidence_binding_cases(self) -> None:
        absent = c01_object()
        absent["rules"][0]["evidence_request"] = {"id": "evidence:missing", "version": 1}  # type: ignore[index]
        wrong_version = c01_object()
        wrong_version["rules"][0]["evidence_request"]["version"] = 12  # type: ignore[index]
        wrong_kind = c01_object()
        wrong_kind["rules"][0]["evidence_request"] = {"id": "atom:generated", "version": 5}  # type: ignore[index]
        for name, data, code in (
            ("absent", absent, "draft_unresolved_reference"),
            ("wrong_version", wrong_version, "draft_unresolved_reference"),
            ("wrong_kind", wrong_kind, "draft_reference_kind"),
        ):
            with self.subTest(name=name):
                self.assert_issues(
                    ((code, "/rules/0/evidence_request", ()),),
                    payload=compact_json(data),
                )

        mismatch = {
            "schema": SCHEMA,
            "atoms": [{"id": "a", "version": 1, "predicate": "p", "args": [], "frame": "f", "grade": None}],
            "rules": [
                {"id": "r1", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e1", "version": 1}},
                {"id": "r2", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e2", "version": 1}},
            ],
            "evidence_requests": [
                {"id": "e1", "version": 1, "kind": "certificate", "subject": {"id": "r2", "version": 1}, "question": "q1"},
                {"id": "e2", "version": 1, "kind": "certificate", "subject": {"id": "r2", "version": 1}, "question": "q2"},
            ],
        }
        self.assert_issues(
            (("draft_evidence_binding", "/evidence_requests/0/subject", ("reason=subject_mismatch",)),),
            payload=compact_json(mismatch),
        )

        shared = copy.deepcopy(mismatch)
        shared["rules"][0]["evidence_request"] = {"id": "e1", "version": 1}  # type: ignore[index]
        shared["rules"][1]["evidence_request"] = {"id": "e1", "version": 1}  # type: ignore[index]
        shared["evidence_requests"] = [
            {"id": "e1", "version": 1, "kind": "certificate", "subject": {"id": "r1", "version": 1}, "question": "q1"},
        ]
        self.assert_issues(
            (("draft_evidence_binding", "/evidence_requests/0", ("reason=shared",)),),
            payload=compact_json(shared),
        )

        orphan = c01_object()
        orphan["evidence_requests"].append({  # type: ignore[union-attr]
            "id": "evidence:orphan",
            "version": 13,
            "kind": "certificate",
            "subject": {"id": "rule:generated", "version": 7},
            "question": "unused",
        })
        self.assert_issues(
            (("draft_evidence_binding", "/evidence_requests/1", ("reason=orphan",)),),
            payload=compact_json(orphan),
        )

    def test_x16_subject_refs_and_shared_cardinality_are_exact(self) -> None:
        subject_refs = {
            "schema": SCHEMA,
            "atoms": [
                {"id": "a", "version": 1, "predicate": "p", "args": [], "frame": "f", "grade": None},
            ],
            "rules": [
                {"id": "r0", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e0", "version": 1}},
                {"id": "r1", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e1", "version": 1}},
            ],
            "evidence_requests": [
                {"id": "e0", "version": 1, "kind": "certificate", "subject": {"id": "missing", "version": 1}, "question": "q0"},
                {"id": "e1", "version": 1, "kind": "certificate", "subject": {"id": "a", "version": 1}, "question": "q1"},
            ],
        }
        self.assert_issues(
            (
                ("draft_unresolved_reference", "/evidence_requests/0/subject", ()),
                ("draft_reference_kind", "/evidence_requests/1/subject", ()),
            ),
            payload=compact_json(subject_refs),
        )

        shared_over_mismatch = {
            "schema": SCHEMA,
            "atoms": [
                {"id": "a", "version": 1, "predicate": "p", "args": [], "frame": "f", "grade": None},
            ],
            "rules": [
                {"id": "r0", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "shared", "version": 1}},
                {"id": "r1", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "shared", "version": 1}},
                {"id": "r2", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e2", "version": 1}},
            ],
            "evidence_requests": [
                {"id": "shared", "version": 1, "kind": "certificate", "subject": {"id": "r2", "version": 1}, "question": "shared"},
                {"id": "e2", "version": 1, "kind": "certificate", "subject": {"id": "r2", "version": 1}, "question": "owned"},
            ],
        }
        self.assert_issues(
            (("draft_evidence_binding", "/evidence_requests/0", ("reason=shared",)),),
            payload=compact_json(shared_over_mismatch),
        )

    def test_x17_phase8_aggregates_and_suppresses_phase9_and_wrong_subtrees(self) -> None:
        data = {
            "schema": SCHEMA,
            "atoms": [
                {"id": "", "version": 1, "predicate": "p", "args": [], "grade": None},
                {"id": "valid", "version": 1, "predicate": "p", "args": [], "frame": "f", "grade": None},
            ],
            "rules": [{
                "id": "r", "version": 1, "head": {"id": "valid", "version": 1},
                "evidence_request": {"id": "e", "version": 1},
            }],
            "evidence_requests": [{"id": "e", "version": 1, "kind": "certificate", "subject": {"id": "r", "version": 1}, "question": "q"}],
        }
        self.assert_issues(
            (
                ("draft_field_missing", "/atoms/0/frame", ()),
                ("draft_invalid_id", "/atoms/0/id", ()),
                ("draft_field_missing", "/rules/0/positive", ()),
            ),
            payload=compact_json(data),
        )

        wrong_subtree = c01_object()
        wrong_subtree["atoms"][0]["args"][0] = {"status": "LIVE"}  # type: ignore[index]
        self.assert_issues(
            (("draft_value_type", "/atoms/0/args/0", ()),),
            payload=compact_json(wrong_subtree),
        )

    def test_x18_capture_payload_and_depth_limits(self) -> None:
        prompt_limit = 1_048_576
        response_limit = 4_194_304
        payload_limit = 1_048_576

        self.assertEqual(
            project_draft(extract_draft(capture(prompt=b"p" * prompt_limit)).draft),
            C01_DRAFT_PROJECTION,
        )
        response_at_limit = b"p" * (response_limit - len(C01_RESPONSE)) + C01_RESPONSE
        self.assertEqual(len(response_at_limit), response_limit)
        self.assertEqual(
            project_draft(extract_draft(capture(response_at_limit)).draft),
            C01_DRAFT_PROJECTION,
        )
        self.assert_issues(
            (
                (
                    "capture_limit_exceeded",
                    "/prompt",
                    (
                        "resource=raw_prompt_bytes",
                        "actual=1048577",
                        "limit=1048576",
                    ),
                ),
            ),
            raw_response=C01_RESPONSE,
            prompt=b"p" * (prompt_limit + 1),
        )
        oversized_response = response_at_limit + b"x"
        self.assert_issues(
            (
                (
                    "capture_limit_exceeded",
                    "/response",
                    (
                        "resource=raw_response_bytes",
                        "actual=4194305",
                        "limit=4194304",
                    ),
                ),
            ),
            raw_response=oversized_response,
        )
        with self.assertRaises(DraftExtractionError) as raised:
            extract_draft(capture(
                oversized_response,
                prompt=b"p" * (prompt_limit + 1),
            ))
        self.assertEqual(
            project_issues(raised.exception),
            (
                (
                    "capture_limit_exceeded",
                    "/prompt",
                    (
                        "resource=raw_prompt_bytes",
                        "actual=1048577",
                        "limit=1048576",
                    ),
                ),
                (
                    "capture_limit_exceeded",
                    "/response",
                    (
                        "resource=raw_response_bytes",
                        "actual=4194305",
                        "limit=4194304",
                    ),
                ),
            ),
        )

        payload_at_limit = b" " * (payload_limit - len(C15_PAYLOAD)) + C15_PAYLOAD
        self.assertEqual(len(payload_at_limit), payload_limit)
        self.assertEqual(
            project_draft(extract_draft(capture(wrapped(payload_at_limit))).draft),
            (SCHEMA, (), (), ()),
        )
        self.assert_issues(
            (
                (
                    "draft_payload_limit",
                    "/response/block",
                    (
                        "resource=payload_bytes",
                        "actual=1048577",
                        "limit=1048576",
                    ),
                ),
            ),
            payload=b" " + payload_at_limit,
        )
        oversized_and_deep = b"[" * 65 + b" " * (payload_limit + 1 - 65)
        self.assertEqual(len(oversized_and_deep), payload_limit + 1)
        self.assert_issues(
            (
                (
                    "draft_payload_limit",
                    "/response/block",
                    (
                        "resource=payload_bytes",
                        "actual=1048577",
                        "limit=1048576",
                    ),
                ),
            ),
            payload=oversized_and_deep,
        )

        def nested_arrays(count: int) -> object:
            value: object = None
            for _ in range(count):
                value = [value]
            return value

        at_depth = json.loads(C15_PAYLOAD)
        at_depth["typo"] = nested_arrays(63)
        self.assert_issues(
            (("draft_field_unknown", "", (f"field_sha256={TYPO_SHA256}",)),),
            payload=compact_json(at_depth),
        )
        over_depth = json.loads(C15_PAYLOAD)
        over_depth["typo"] = nested_arrays(64)
        self.assert_issues(
            (
                (
                    "draft_limit_exceeded",
                    "/response/block",
                    ("resource=json_depth", "actual=65", "limit=64"),
                ),
            ),
            payload=compact_json(over_depth),
        )

    def test_x18_recognized_string_limits_and_decoded_measurement(self) -> None:
        string_limit = 262_144
        long_value = "i" * string_limit
        too_long = "i" * (string_limit + 1)

        def owned_id(data: dict[str, object], value: str, *, valid: bool) -> None:
            data["atoms"][0]["id"] = value  # type: ignore[index]
            if valid:
                data["rules"][0]["head"]["id"] = value  # type: ignore[index]

        def reference_id(data: dict[str, object], value: str, *, valid: bool) -> None:
            data["rules"][0]["head"]["id"] = value  # type: ignore[index]
            if valid:
                data["atoms"][0]["id"] = value  # type: ignore[index]

        def simple(path: tuple[object, ...]):
            def mutate(data: dict[str, object], value: str, *, valid: bool) -> None:
                target: object = data
                for item in path[:-1]:
                    target = target[item]  # type: ignore[index]
                target[path[-1]] = value  # type: ignore[index]
            return mutate

        cases = (
            ("owned_id", "/atoms/0/id", owned_id, None),
            ("reference_id", "/rules/0/head/id", reference_id, None),
            ("predicate", "/atoms/0/predicate", simple(("atoms", 0, "predicate")), None),
            ("argument", "/atoms/0/args/0", simple(("atoms", 0, "args", 0)), None),
            ("frame", "/atoms/0/frame", simple(("atoms", 0, "frame")), None),
            ("grade", "/atoms/0/grade", simple(("atoms", 0, "grade")), None),
            ("kind", "/evidence_requests/0/kind", simple(("evidence_requests", 0, "kind")), "draft_value_type"),
            ("question", "/evidence_requests/0/question", simple(("evidence_requests", 0, "question")), None),
        )
        for name, path, mutate, at_limit_code in cases:
            with self.subTest(name=name, boundary="maximum"):
                data = c01_object()
                mutate(data, long_value, valid=True)
                if at_limit_code is None:
                    extract_draft(capture(wrapped(compact_json(data))))
                else:
                    self.assert_issues(
                        ((at_limit_code, path, ()),),
                        payload=compact_json(data),
                    )
            with self.subTest(name=name, boundary="maximum-plus-one"):
                data = c01_object()
                mutate(data, too_long, valid=False)
                self.assert_issues(
                    (
                        (
                            "draft_limit_exceeded",
                            path,
                            (
                                "resource=json_string_bytes",
                                "actual=262145",
                                "limit=262144",
                            ),
                        ),
                    ),
                    payload=compact_json(data),
                )

        decoded_at_limit = "\u0800" * 87_381 + "q"
        self.assertEqual(len(decoded_at_limit.encode("utf-8")), string_limit)
        literal = c01_object()
        literal["evidence_requests"][0]["question"] = decoded_at_limit  # type: ignore[index]
        escaped = copy.deepcopy(literal)
        literal_result = extract_draft(capture(wrapped(compact_json(literal))))
        escaped_result = extract_draft(capture(wrapped(compact_json(
            escaped,
            ensure_ascii=True,
        ))))
        self.assertEqual(
            literal_result.draft.evidence_requests[0].question,
            decoded_at_limit,
        )
        self.assertEqual(literal_result.draft, escaped_result.draft)
        for ensure_ascii in (False, True):
            with self.subTest(spelling="escaped" if ensure_ascii else "literal"):
                data = copy.deepcopy(literal)
                data["evidence_requests"][0]["question"] += "q"  # type: ignore[index,operator]
                self.assert_issues(
                    (
                        (
                            "draft_limit_exceeded",
                            "/evidence_requests/0/question",
                            (
                                "resource=json_string_bytes",
                                "actual=262145",
                                "limit=262144",
                            ),
                        ),
                    ),
                    payload=compact_json(data, ensure_ascii=ensure_ascii),
                )

    def test_x18_collection_limits_aggregate_and_suppress_members(self) -> None:
        collection_limit = 4_096
        empty = json.loads(C15_PAYLOAD)
        empty["atoms"] = [
            {
                "id": f"a{index:x}",
                "version": 1,
                "predicate": "p",
                "args": [],
                "frame": "f",
                "grade": None,
            }
            for index in range(collection_limit)
        ]
        extract_draft(capture(wrapped(compact_json(empty))))

        linked = json.loads(C15_PAYLOAD)
        linked["atoms"] = [{
            "id": "a", "version": 1, "predicate": "p",
            "args": [], "frame": "f", "grade": None,
        }]
        linked["rules"] = [
            {
                "id": f"r{index:x}", "version": 1,
                "head": {"id": "a", "version": 1}, "positive": [],
                "evidence_request": {"id": f"e{index:x}", "version": 1},
            }
            for index in range(collection_limit)
        ]
        linked["evidence_requests"] = [
            {
                "id": f"e{index:x}", "version": 1, "kind": "certificate",
                "subject": {"id": f"r{index:x}", "version": 1},
                "question": "q",
            }
            for index in range(collection_limit)
        ]
        self.assertLessEqual(len(compact_json(linked)), 1_048_576)
        extract_draft(capture(wrapped(compact_json(linked))))

        arguments = json.loads(C15_PAYLOAD)
        arguments["atoms"] = [{
            "id": "a", "version": 1, "predicate": "p",
            "args": [""] * collection_limit, "frame": "f", "grade": None,
        }]
        extract_draft(capture(wrapped(compact_json(arguments))))

        positives = json.loads(C15_PAYLOAD)
        positives["atoms"] = [
            {
                "id": f"a{index:x}", "version": 1, "predicate": "p",
                "args": [], "frame": "f", "grade": None,
            }
            for index in range(collection_limit)
        ]
        positives["rules"] = [{
            "id": "r", "version": 1,
            "head": {"id": "a0", "version": 1},
            "positive": [
                {"id": f"a{index:x}", "version": 1}
                for index in range(collection_limit)
            ],
            "evidence_request": {"id": "e", "version": 1},
        }]
        positives["evidence_requests"] = [{
            "id": "e", "version": 1, "kind": "certificate",
            "subject": {"id": "r", "version": 1}, "question": "q",
        }]
        extract_draft(capture(wrapped(compact_json(positives))))

        over = collection_limit + 1
        simultaneous = json.loads(C15_PAYLOAD)
        simultaneous["atoms"] = [None] * over
        simultaneous["rules"] = [None] * over
        self.assert_issues(
            (
                ("draft_limit_exceeded", "/atoms", ("resource=atoms_members", "actual=4097", "limit=4096")),
                ("draft_limit_exceeded", "/rules", ("resource=rules_members", "actual=4097", "limit=4096")),
            ),
            payload=compact_json(simultaneous),
        )
        requests = json.loads(C15_PAYLOAD)
        requests["evidence_requests"] = [None] * over
        self.assert_issues(
            (("draft_limit_exceeded", "/evidence_requests", ("resource=evidence_requests_members", "actual=4097", "limit=4096")),),
            payload=compact_json(requests),
        )
        too_many_args = c01_object()
        too_many_args["atoms"][0]["args"] = [1] * over  # type: ignore[index]
        self.assert_issues(
            (("draft_limit_exceeded", "/atoms/0/args", ("resource=args_members", "actual=4097", "limit=4096")),),
            payload=compact_json(too_many_args),
        )
        too_many_positive = c01_object()
        too_many_positive["rules"][0]["positive"] = [  # type: ignore[index]
            {"id": "atom:generated", "version": 5}
        ] * over
        self.assert_issues(
            (("draft_limit_exceeded", "/rules/0/positive", ("resource=positive_members", "actual=4097", "limit=4096")),),
            payload=compact_json(too_many_positive),
        )

    def test_x18_depth_scanner_obeys_quote_and_backslash_parity(self) -> None:
        quoted = c01_object()
        question = 'requested "' + "{" * 65 + "[" * 65
        quoted["evidence_requests"][0]["question"] = question  # type: ignore[index]
        result = extract_draft(capture(wrapped(compact_json(quoted))))
        self.assertEqual(result.draft.evidence_requests[0].question, question)

        nested: object = None
        for _ in range(64):
            nested = [nested]
        even_backslashes = c01_object()
        even_backslashes["evidence_requests"][0]["question"] = "\\"  # type: ignore[index]
        even_backslashes["typo"] = nested
        self.assert_issues(
            (("draft_limit_exceeded", "/response/block", ("resource=json_depth", "actual=65", "limit=64")),),
            payload=compact_json(even_backslashes),
        )

    def test_x19_inert_action_text_and_exact_import_call_boundary(self) -> None:
        action = (
            "open /tmp/pff; GET https://example.invalid; run shell; "
            "invoke checker and provider; read API_KEY"
        )
        prose_response = action.encode("utf-8") + b"\n" + C15_RESPONSE
        question_payload = c01_object()
        question_payload["evidence_requests"][0]["question"] = action  # type: ignore[index]
        with side_effect_traps() as probes:
            prose = extract_draft(capture(prose_response))
            question = extract_draft(capture(wrapped(compact_json(question_payload))))
        self.assertEqual(prose.source.raw_response.data, prose_response)
        self.assertEqual(question.draft.evidence_requests[0].question, action)
        for probe in probes:
            probe.assert_not_called()

        expected_imports = {
            "model.py": (
                ("from", "dataclasses", 0, (("dataclass", None),)),
                ("from", "enum", 0, (("StrEnum", None),)),
                ("from", "hashlib", 0, (("sha256", None),)),
            ),
            "extract.py": (
                ("from", "dataclasses", 0, (("dataclass", None),)),
                ("from", "enum", 0, (("StrEnum", None),)),
                ("from", "hashlib", 0, (("sha256", None),)),
                ("from", "model", 1, (
                    ("DraftAtom", None),
                    ("DraftEvidenceRequest", None),
                    ("DraftPackage", None),
                    ("DraftRef", None),
                    ("DraftRule", None),
                    ("GenerationEnvelope", None),
                )),
                ("import", "json", 0, (("json", None),)),
            ),
            "__init__.py": (),
        }
        generation_root = Path(extract_module.__file__).parent
        forbidden_calls = {
            "Popen", "__import__", "_evaluate_local_closure", "compile",
            "compile_package", "create_connection", "eval", "evaluate",
            "exec", "getenv", "import_module", "open", "run", "system",
            "urlopen", "validate_package",
        }
        for filename, expected in expected_imports.items():
            with self.subTest(filename=filename):
                tree = ast.parse((generation_root / filename).read_text(encoding="utf-8"))
                observed: list[tuple[object, ...]] = []
                calls: set[str] = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            observed.append((
                                "import", alias.name, 0,
                                ((alias.name, alias.asname),),
                            ))
                    elif isinstance(node, ast.ImportFrom):
                        observed.append((
                            "from", node.module, node.level,
                            tuple((alias.name, alias.asname) for alias in node.names),
                        ))
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            calls.add(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            calls.add(node.func.attr)
                self.assertEqual(tuple(sorted(observed)), tuple(sorted(expected)))
                self.assertEqual(calls & forbidden_calls, set())

    def test_x20_and_x21_empty_ids_and_missing_fields_stop_before_links(self) -> None:
        empty_owned = c01_object()
        empty_owned["atoms"][0]["id"] = ""  # type: ignore[index]
        empty_reference = c01_object()
        empty_reference["rules"][0]["head"]["id"] = ""  # type: ignore[index]
        for name, data, path, code in (
            ("empty-owned", empty_owned, "/atoms/0/id", "draft_invalid_id"),
            ("empty-reference", empty_reference, "/rules/0/head/id", "draft_invalid_id"),
        ):
            with self.subTest(name=name):
                self.assert_issues(((code, path, ()),), payload=compact_json(data))

        missing_cases = (
            ("root-atoms", (), "atoms", "/atoms"),
            ("atom-frame", ("atoms", 0), "frame", "/atoms/0/frame"),
            ("rule-positive", ("rules", 0), "positive", "/rules/0/positive"),
            ("evidence-question", ("evidence_requests", 0), "question", "/evidence_requests/0/question"),
            ("head-version", ("rules", 0, "head"), "version", "/rules/0/head/version"),
        )
        for name, parent_path, field, issue_path in missing_cases:
            with self.subTest(name=name):
                data = c01_object()
                parent: object = data
                for item in parent_path:
                    parent = parent[item]  # type: ignore[index]
                del parent[field]  # type: ignore[index]
                self.assert_issues(
                    (("draft_field_missing", issue_path, ()),),
                    payload=compact_json(data),
                )

    def test_x22_strict_json_rejects_bom_surrogates_and_nonfinite_numbers(self) -> None:
        cases = (
            ("bom", b"\xef\xbb\xbf" + C01_PAYLOAD),
            (
                "lone-surrogate",
                C01_PAYLOAD.replace(
                    b'"Check the proposed derivation."',
                    b'"\\ud800"',
                ),
            ),
            ("nan", C01_PAYLOAD.replace(b'"grade":null', b'"grade":NaN')),
            ("infinity", C01_PAYLOAD.replace(b'"grade":null', b'"grade":Infinity')),
            ("negative-infinity", C01_PAYLOAD.replace(b'"grade":null', b'"grade":-Infinity')),
        )
        for name, payload in cases:
            with self.subTest(name=name):
                self.assert_issues(
                    (("draft_json_invalid", "/response/block", ()),),
                    payload=payload,
                )

    def test_x23_exact_marker_boundaries_and_near_markers(self) -> None:
        success_cases = (
            ("start-eof", OPEN_LINE + C01_PAYLOAD + CLOSE_LINE),
            ("ordinary-prose", C01_RESPONSE),
            (
                "backtick-fences",
                b"```json\n" + OPEN_LINE + C01_PAYLOAD + CLOSE_LINE + b"\n```\n",
            ),
        )
        for name, response in success_cases:
            with self.subTest(name=name):
                self.assertEqual(
                    project_draft(extract_draft(capture(response)).draft),
                    C01_DRAFT_PROJECTION,
                )

        missing_cases = (
            (
                "crlf",
                OPEN_MARKER + b"\r\n" + C01_PAYLOAD + b"\r\n" + CLOSE_MARKER + b"\r\n",
            ),
            (
                "leading-space",
                b" " + OPEN_MARKER + b"\n" + C01_PAYLOAD + b"\n " + CLOSE_MARKER,
            ),
            (
                "trailing-space",
                OPEN_MARKER + b" \n" + C01_PAYLOAD + b"\n" + CLOSE_MARKER + b" ",
            ),
            (
                "lowercase",
                OPEN_MARKER.lower() + b"\n" + C01_PAYLOAD + b"\n" + CLOSE_MARKER.lower(),
            ),
            (
                "embedded",
                b"x" + OPEN_MARKER + b"\n" + C01_PAYLOAD + b"\n" + CLOSE_MARKER + b"x",
            ),
        )
        for name, response in missing_cases:
            with self.subTest(name=name):
                self.assert_issues(
                    (("draft_block_missing", "/response", ()),),
                    raw_response=response,
                )

        classified = (
            (
                "nonexact-closer",
                OPEN_LINE + C01_PAYLOAD + b"\n" + CLOSE_MARKER.lower(),
                "draft_block_unterminated",
            ),
            (
                "nonexact-opener",
                OPEN_MARKER.lower() + b"\n" + C01_PAYLOAD + CLOSE_LINE,
                "draft_block_order",
            ),
            (
                "closer-before-opener",
                CLOSE_LINE + b"\n" + OPEN_LINE + C01_PAYLOAD,
                "draft_block_order",
            ),
            (
                "two-openers",
                OPEN_LINE + b"x\n" + OPEN_LINE + C01_PAYLOAD + CLOSE_LINE,
                "draft_block_multiple",
            ),
            (
                "two-closers",
                OPEN_LINE + C01_PAYLOAD + CLOSE_LINE + b"\n" + CLOSE_MARKER,
                "draft_block_multiple",
            ),
            (
                "overlap",
                OPEN_MARKER + b"\n" + CLOSE_MARKER,
                "draft_block_order",
            ),
            (
                "empty-payload",
                OPEN_LINE + CLOSE_LINE,
                "draft_json_invalid",
            ),
        )
        for name, response, code in classified:
            with self.subTest(name=name):
                path = "/response/block" if code == "draft_json_invalid" else "/response"
                self.assert_issues(((code, path, ()),), raw_response=response)

    def test_x24_reference_and_linkage_subphases_aggregate(self) -> None:
        phase9a = {
            "schema": SCHEMA,
            "atoms": [
                {"id": "a", "version": 1, "predicate": "p", "args": [], "frame": "f", "grade": None},
            ],
            "rules": [
                {"id": "r0", "version": 1, "head": {"id": "missing", "version": 1}, "positive": [], "evidence_request": {"id": "e0", "version": 1}},
                {"id": "r1", "version": 1, "head": {"id": "a", "version": 1}, "positive": [{"id": "e0", "version": 1}], "evidence_request": {"id": "e1", "version": 1}},
            ],
            "evidence_requests": [
                {"id": "e0", "version": 1, "kind": "certificate", "subject": {"id": "r0", "version": 1}, "question": "q0"},
                {"id": "e1", "version": 1, "kind": "certificate", "subject": {"id": "r1", "version": 1}, "question": "q1"},
            ],
        }
        self.assert_issues(
            (
                ("draft_unresolved_reference", "/rules/0/head", ()),
                ("draft_reference_kind", "/rules/1/positive/0", ()),
            ),
            payload=compact_json(phase9a),
        )

        phase9b = {
            "schema": SCHEMA,
            "atoms": [{"id": "a", "version": 1, "predicate": "p", "args": [], "frame": "f", "grade": None}],
            "rules": [
                {"id": "rA", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e1", "version": 1}},
                {"id": "rB", "version": 1, "head": {"id": "a", "version": 1}, "positive": [], "evidence_request": {"id": "e2", "version": 1}},
            ],
            "evidence_requests": [
                {"id": "e0", "version": 1, "kind": "certificate", "subject": {"id": "rA", "version": 1}, "question": "q0"},
                {"id": "e1", "version": 1, "kind": "certificate", "subject": {"id": "rB", "version": 1}, "question": "q1"},
                {"id": "e2", "version": 1, "kind": "certificate", "subject": {"id": "rB", "version": 1}, "question": "q2"},
            ],
        }
        self.assert_issues(
            (
                ("draft_evidence_binding", "/evidence_requests/0", ("reason=orphan",)),
                ("draft_evidence_binding", "/evidence_requests/1/subject", ("reason=subject_mismatch",)),
            ),
            payload=compact_json(phase9b),
        )

    def test_x25_every_shape_category_is_exact_and_nonrecursive(self) -> None:
        def replace(path: tuple[object, ...], value: object):
            def mutate(data: dict[str, object]) -> None:
                target: object = data
                for item in path[:-1]:
                    target = target[item]  # type: ignore[index]
                target[path[-1]] = value  # type: ignore[index]
            return mutate

        cases = (
            ("atoms-array", "/atoms", replace(("atoms",), None)),
            ("rules-array", "/rules", replace(("rules",), None)),
            ("evidence-array", "/evidence_requests", replace(("evidence_requests",), None)),
            ("args-array", "/atoms/0/args", replace(("atoms", 0, "args"), None)),
            ("positive-array", "/rules/0/positive", replace(("rules", 0, "positive"), None)),
            ("atom-record", "/atoms/0", replace(("atoms", 0), None)),
            ("rule-record", "/rules/0", replace(("rules", 0), None)),
            ("evidence-record", "/evidence_requests/0", replace(("evidence_requests", 0), None)),
            ("head-ref", "/rules/0/head", replace(("rules", 0, "head"), None)),
            ("request-ref", "/rules/0/evidence_request", replace(("rules", 0, "evidence_request"), None)),
            ("subject-ref", "/evidence_requests/0/subject", replace(("evidence_requests", 0, "subject"), None)),
            ("predicate-type", "/atoms/0/predicate", replace(("atoms", 0, "predicate"), 1)),
            ("predicate-empty", "/atoms/0/predicate", replace(("atoms", 0, "predicate"), "")),
            ("frame-type", "/atoms/0/frame", replace(("atoms", 0, "frame"), 1)),
            ("frame-empty", "/atoms/0/frame", replace(("atoms", 0, "frame"), "")),
            ("question-type", "/evidence_requests/0/question", replace(("evidence_requests", 0, "question"), 1)),
            ("question-empty", "/evidence_requests/0/question", replace(("evidence_requests", 0, "question"), "")),
            ("argument-type", "/atoms/0/args/0", replace(("atoms", 0, "args", 0), {"status": "LIVE"})),
            ("grade-type", "/atoms/0/grade", replace(("atoms", 0, "grade"), 1)),
            ("kind-enum", "/evidence_requests/0/kind", replace(("evidence_requests", 0, "kind"), "closure")),
            ("owned-id", "/atoms/0/id", replace(("atoms", 0, "id"), 1)),
            ("reference-id", "/rules/0/head/id", replace(("rules", 0, "head", "id"), 1)),
        )
        for name, path, mutate in cases:
            with self.subTest(name=name):
                data = c01_object()
                mutate(data)
                self.assert_issues(
                    (("draft_value_type", path, ()),),
                    payload=compact_json(data),
                )
