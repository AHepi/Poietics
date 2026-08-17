from dataclasses import FrozenInstanceError
import unittest

from poietics.generation.model import (
    AttemptRef,
    AttemptRelation,
    CapturedContent,
    DraftAtom,
    DraftEvidenceRequest,
    DraftPackage,
    DraftRef,
    DraftRule,
    GenerationEnvelope,
    GenerationParameter,
    capture_generation,
)


MAX_INTEGER = 9_223_372_036_854_775_807


class StringSubclass(str):
    pass


class IntegerSubclass(int):
    pass


class BytesSubclass(bytes):
    pass


class DictSubclass(dict):
    pass


class AttemptRefSubclass(AttemptRef):
    pass


def capture_fixture(**changes: object) -> GenerationEnvelope:
    values: dict[str, object] = {
        "attempt": AttemptRef("session:test", 1),
        "relation": AttemptRelation.INITIAL,
        "parent": None,
        "provider_id": "test-provider",
        "adapter_id": "test-adapter",
        "adapter_version": "1",
        "requested_model": "test-model",
        "reported_model": "test-model",
        "prompt_template_id": "test-template",
        "prompt_template_version": "1",
        "prompt": b"Produce one PFF draft.\n",
        "public_parameters": {"temperature": "0"},
        "raw_response": b"model response\n",
        "finish_reason": "stop",
        "provider_request_id": "request:test",
    }
    values.update(changes)
    return capture_generation(**values)  # type: ignore[arg-type]


def draft_fixture() -> DraftPackage:
    atom_ref = DraftRef("atom:generated", 5)
    rule_ref = DraftRef("rule:generated", 7)
    evidence_ref = DraftRef("evidence:generated", 11)
    atom = DraftAtom._from_extraction(
        id=atom_ref.id,
        version=atom_ref.version,
        predicate="test.derived",
        args=("entity:e",),
        frame="frame:1",
        grade=None,
    )
    rule = DraftRule._from_extraction(
        id=rule_ref.id,
        version=rule_ref.version,
        head=atom_ref,
        positive=frozenset(),
        evidence_request=evidence_ref,
    )
    request = DraftEvidenceRequest._from_extraction(
        id=evidence_ref.id,
        version=evidence_ref.version,
        kind="certificate",
        subject=rule_ref,
        question="Check the proposed derivation.",
    )
    return DraftPackage._from_extraction(
        schema="pff-draft/0.1",
        atoms=(atom,),
        rules=(rule,),
        evidence_requests=(request,),
    )


class AttemptRefTests(unittest.TestCase):
    def test_exact_boundaries(self) -> None:
        self.assertEqual(AttemptRef("s", 1).sequence, 1)
        self.assertEqual(AttemptRef("s", MAX_INTEGER).sequence, MAX_INTEGER)
        self.assertEqual(AttemptRef("s" * 256, 1).session_id, "s" * 256)
        multibyte_at_limit = "é" * 128
        self.assertEqual(
            AttemptRef(multibyte_at_limit, 1).session_id,
            multibyte_at_limit,
        )

        for sequence in (0, -1, MAX_INTEGER + 1):
            with self.subTest(sequence=sequence):
                with self.assertRaises(ValueError):
                    AttemptRef("s", sequence)
        for sequence in (True, 1.0, "1", IntegerSubclass(1)):
            with self.subTest(sequence=sequence):
                with self.assertRaises(TypeError):
                    AttemptRef("s", sequence)  # type: ignore[arg-type]

        for session_id in ("", "s" * 257, "é" * 128 + "a", "\ud800"):
            with self.subTest(session_id=repr(session_id)):
                with self.assertRaises(ValueError):
                    AttemptRef(session_id, 1)
        for session_id in (b"s", StringSubclass("s")):
            with self.subTest(session_id=repr(session_id)):
                with self.assertRaises(TypeError):
                    AttemptRef(session_id, 1)  # type: ignore[arg-type]


class GenerationParameterTests(unittest.TestCase):
    def test_exact_boundaries_and_empty_value(self) -> None:
        self.assertEqual(GenerationParameter("n" * 256, ""), GenerationParameter("n" * 256, ""))
        self.assertEqual(len(GenerationParameter("n", "v" * 4096).value), 4096)
        multibyte_name = "é" * 128
        multibyte_value = "é" * 2048
        self.assertEqual(
            GenerationParameter(multibyte_name, multibyte_value),
            GenerationParameter(multibyte_name, multibyte_value),
        )

        for name, value in (
            ("", "v"),
            ("n" * 257, "v"),
            ("é" * 128 + "a", "v"),
            ("\ud800", "v"),
            ("n", "v" * 4097),
            ("n", "é" * 2048 + "a"),
            ("n", "\udfff"),
        ):
            with self.subTest(name=repr(name), value_length=len(value)):
                with self.assertRaises(ValueError):
                    GenerationParameter(name, value)

        for name, value in (
            (StringSubclass("n"), "v"),
            (b"n", "v"),
            ("n", StringSubclass("v")),
            ("n", b"v"),
        ):
            with self.subTest(name=repr(name), value=repr(value)):
                with self.assertRaises(TypeError):
                    GenerationParameter(name, value)  # type: ignore[arg-type]


class CaptureGenerationTests(unittest.TestCase):
    def test_capture_retains_exact_bytes_and_computes_digests(self) -> None:
        envelope = capture_fixture()
        self.assertEqual(envelope.profile, "pff-generation/0.1")
        self.assertEqual(envelope.prompt.data, b"Produce one PFF draft.\n")
        self.assertEqual(
            envelope.prompt.sha256,
            "sha256:f329f108c80e7b77f785104490eb76dff005e05391e20e048650ac3bb637f36f",
        )
        self.assertEqual(envelope.raw_response.data, b"model response\n")
        self.assertEqual(
            envelope.raw_response.sha256,
            "sha256:c30214c91aa727bdc9648ada105a291fd644f3d8a81041b7332bbfda57d8d6cf",
        )

    def test_source_parameter_mutation_cannot_change_envelope(self) -> None:
        source = {"z": "last", "a": "first"}
        envelope = capture_fixture(public_parameters=source)
        source.clear()
        source["changed"] = "later"

        self.assertEqual(
            tuple((item.name, item.value) for item in envelope.public_parameters),
            (("a", "first"), ("z", "last")),
        )
        with self.assertRaises(TypeError):
            envelope.public_parameters[0] = GenerationParameter("x", "y")  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            envelope.public_parameters[0].value = "changed"  # type: ignore[misc]

    def test_all_lineage_relations_and_invalid_lineage(self) -> None:
        initial = capture_fixture()
        self.assertIsNone(initial.parent)
        parent = AttemptRef("session:test", 2)
        for relation in (
            AttemptRelation.RETRY,
            AttemptRelation.REPAIR,
            AttemptRelation.EXTRACT,
        ):
            with self.subTest(relation=relation):
                envelope = capture_fixture(
                    attempt=AttemptRef("session:test", 3),
                    relation=relation,
                    parent=parent,
                )
                self.assertEqual(envelope.parent, parent)

        invalid = (
            {
                "attempt": AttemptRef("session:test", 2),
                "relation": AttemptRelation.INITIAL,
                "parent": AttemptRef("session:test", 1),
            },
            {
                "attempt": AttemptRef("session:test", 2),
                "relation": AttemptRelation.RETRY,
                "parent": None,
            },
            {
                "attempt": AttemptRef("session:test", 2),
                "relation": AttemptRelation.REPAIR,
                "parent": AttemptRef("different", 1),
            },
            {
                "attempt": AttemptRef("session:test", 2),
                "relation": AttemptRelation.EXTRACT,
                "parent": AttemptRef("session:test", 2),
            },
            {
                "attempt": AttemptRef("session:test", 2),
                "relation": AttemptRelation.RETRY,
                "parent": AttemptRef("session:test", 3),
            },
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    capture_fixture(**changes)

    def test_metadata_boundaries_for_every_slot(self) -> None:
        required = (
            "provider_id",
            "adapter_id",
            "adapter_version",
            "requested_model",
            "prompt_template_id",
            "prompt_template_version",
        )
        nullable = ("reported_model", "finish_reason", "provider_request_id")
        multibyte_at_limit = "é" * 2048
        multibyte_over_limit = multibyte_at_limit + "a"

        for field in required + nullable:
            with self.subTest(field=field, boundary="maximum"):
                self.assertEqual(getattr(capture_fixture(**{field: "x" * 4096}), field), "x" * 4096)
            with self.subTest(field=field, boundary="empty"):
                with self.assertRaises(ValueError):
                    capture_fixture(**{field: ""})
            with self.subTest(field=field, boundary="oversized"):
                with self.assertRaises(ValueError):
                    capture_fixture(**{field: "x" * 4097})
            with self.subTest(field=field, boundary="multibyte_maximum"):
                self.assertEqual(
                    getattr(capture_fixture(**{field: multibyte_at_limit}), field),
                    multibyte_at_limit,
                )
            with self.subTest(field=field, boundary="multibyte_oversized"):
                with self.assertRaises(ValueError):
                    capture_fixture(**{field: multibyte_over_limit})
            with self.subTest(field=field, boundary="non_scalar"):
                with self.assertRaises(ValueError):
                    capture_fixture(**{field: "\ud800"})
            with self.subTest(field=field, boundary="subclass"):
                with self.assertRaises(TypeError):
                    capture_fixture(**{field: StringSubclass("x")})

        for field in nullable:
            with self.subTest(field=field, boundary="none"):
                self.assertIsNone(getattr(capture_fixture(**{field: None}), field))

    def test_exact_factory_input_types(self) -> None:
        invalid_cases = (
            {"attempt": object()},
            {"attempt": AttemptRefSubclass("session:test", 1)},
            {"relation": "initial"},
            {"parent": object()},
            {
                "attempt": AttemptRef("session:test", 2),
                "relation": AttemptRelation.RETRY,
                "parent": AttemptRefSubclass("session:test", 1),
            },
            {"prompt": bytearray(b"prompt")},
            {"prompt": BytesSubclass(b"prompt")},
            {"raw_response": bytearray(b"response")},
            {"raw_response": BytesSubclass(b"response")},
            {"public_parameters": DictSubclass()},
        )
        for changes in invalid_cases:
            with self.subTest(changes=changes):
                with self.assertRaises(TypeError):
                    capture_fixture(**changes)

        self.assertEqual(capture_fixture(prompt=b"", raw_response=b"").prompt.data, b"")

    def test_parameter_count_and_value_boundaries(self) -> None:
        boundary = capture_fixture(
            public_parameters={"n" * 256: "v" * 4096}
        ).public_parameters[0]
        self.assertEqual(len(boundary.name), 256)
        self.assertEqual(len(boundary.value), 4096)

        parameters_256 = {f"p{index:03d}": "" for index in range(256)}
        envelope = capture_fixture(public_parameters=parameters_256)
        self.assertEqual(len(envelope.public_parameters), 256)
        self.assertTrue(all(item.value == "" for item in envelope.public_parameters))

        parameters_257 = {f"p{index:03d}": "v" for index in range(257)}
        with self.assertRaises(ValueError):
            capture_fixture(public_parameters=parameters_257)
        with self.assertRaises(ValueError):
            capture_fixture(public_parameters={"n" * 257: "v"})
        with self.assertRaises(ValueError):
            capture_fixture(public_parameters={"n": "v" * 4097})
        with self.assertRaises(ValueError):
            capture_fixture(public_parameters={"\ud800": "v"})
        with self.assertRaises(ValueError):
            capture_fixture(public_parameters={"n": "\ud800"})
        with self.assertRaises(TypeError):
            capture_fixture(public_parameters={StringSubclass("n"): "v"})
        with self.assertRaises(TypeError):
            capture_fixture(public_parameters={"n": StringSubclass("v")})

    def test_sensitive_looking_non_utf8_prompt_is_inert_and_retained(self) -> None:
        envelope = capture_fixture(
            prompt=bytes.fromhex("ff fe 50"),
            public_parameters={"looks_secret": "fixture-value"},
        )
        self.assertEqual(envelope.prompt.data, bytes.fromhex("ff fe 50"))
        self.assertEqual(
            envelope.prompt.sha256,
            "sha256:69f0224d0398959a359eaeefae39b3f322ac07c4db2d5f76ece235aa03a88205",
        )
        self.assertEqual(
            tuple((item.name, item.value) for item in envelope.public_parameters),
            (("looks_secret", "fixture-value"),),
        )

    def test_envelope_is_unhashable(self) -> None:
        with self.assertRaises(TypeError):
            hash(capture_fixture())


class FactoryBoundaryTests(unittest.TestCase):
    def test_public_construction_of_owned_types_is_rejected(self) -> None:
        envelope = capture_fixture()
        atom_ref = DraftRef("atom:generated", 5)
        rule_ref = DraftRef("rule:generated", 7)
        evidence_ref = DraftRef("evidence:generated", 11)

        calls = (
            lambda: CapturedContent(),
            lambda: CapturedContent(data=b"x", sha256="sha256:bad"),
            lambda: GenerationEnvelope(),
            lambda: GenerationEnvelope(
                profile=envelope.profile,
                attempt=envelope.attempt,
                relation=envelope.relation,
                parent=envelope.parent,
                provider_id=envelope.provider_id,
                adapter_id=envelope.adapter_id,
                adapter_version=envelope.adapter_version,
                requested_model=envelope.requested_model,
                reported_model=envelope.reported_model,
                prompt_template_id=envelope.prompt_template_id,
                prompt_template_version=envelope.prompt_template_version,
                prompt=envelope.prompt,
                public_parameters=envelope.public_parameters,
                raw_response=envelope.raw_response,
                finish_reason=envelope.finish_reason,
                provider_request_id=envelope.provider_request_id,
            ),
            lambda: DraftAtom(),
            lambda: DraftAtom(
                id=atom_ref.id,
                version=atom_ref.version,
                predicate="test.derived",
                args=("entity:e",),
                frame="frame:1",
                grade=None,
            ),
            lambda: DraftRule(),
            lambda: DraftRule(
                id=rule_ref.id,
                version=rule_ref.version,
                head=atom_ref,
                positive=frozenset(),
                evidence_request=evidence_ref,
            ),
            lambda: DraftEvidenceRequest(),
            lambda: DraftEvidenceRequest(
                id=evidence_ref.id,
                version=evidence_ref.version,
                kind="certificate",
                subject=rule_ref,
                question="Check the proposed derivation.",
            ),
            lambda: DraftPackage(),
            lambda: DraftPackage(
                schema="pff-draft/0.1",
                atoms=(),
                rules=(),
                evidence_requests=(),
            ),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises(TypeError):
                    call()

        self.assertEqual(AttemptRef("s", 1), AttemptRef("s", 1))
        self.assertEqual(GenerationParameter("n", ""), GenerationParameter("n", ""))
        self.assertEqual(DraftRef("id", 1), DraftRef("id", 1))

    def test_successful_graph_is_deeply_immutable(self) -> None:
        envelope = capture_fixture()
        package = draft_fixture()
        atom = package.atoms[0]
        rule = package.rules[0]
        request = package.evidence_requests[0]
        snapshot = (
            envelope.profile,
            envelope.prompt.data,
            envelope.prompt.sha256,
            tuple((item.name, item.value) for item in envelope.public_parameters),
            package.schema,
            tuple((item.id, item.version, item.args) for item in package.atoms),
            tuple(
                (
                    item.id,
                    item.version,
                    item.head,
                    item.positive,
                    item.evidence_request,
                )
                for item in package.rules
            ),
            tuple(
                (item.id, item.version, item.kind, item.subject, item.question)
                for item in package.evidence_requests
            ),
        )

        for target, field, value in (
            (envelope, "provider_id", "changed"),
            (envelope.prompt, "data", b"changed"),
            (envelope.public_parameters[0], "value", "changed"),
            (package, "schema", "changed"),
            (atom, "predicate", "changed"),
            (rule, "head", DraftRef("other", 1)),
            (request, "question", "changed"),
            (rule.head, "id", "changed"),
        ):
            with self.subTest(target=type(target).__name__, field=field):
                with self.assertRaises(AttributeError):
                    setattr(target, field, value)
        with self.assertRaises(TypeError):
            atom.args[0] = "changed"  # type: ignore[index]
        with self.assertRaises(TypeError):
            package.atoms[0] = atom  # type: ignore[index]
        with self.assertRaises(AttributeError):
            rule.positive.add(DraftRef("other", 1))  # type: ignore[attr-defined]

        self.assertEqual(
            (
                envelope.profile,
                envelope.prompt.data,
                envelope.prompt.sha256,
                tuple((item.name, item.value) for item in envelope.public_parameters),
                package.schema,
                tuple((item.id, item.version, item.args) for item in package.atoms),
                tuple(
                    (
                        item.id,
                        item.version,
                        item.head,
                        item.positive,
                        item.evidence_request,
                    )
                    for item in package.rules
                ),
                tuple(
                    (item.id, item.version, item.kind, item.subject, item.question)
                    for item in package.evidence_requests
                ),
            ),
            snapshot,
        )

    def test_private_owned_factories_enforce_frozen_member_shapes(self) -> None:
        ref = DraftRef("atom:a", 1)
        with self.assertRaises(TypeError):
            DraftAtom._from_extraction(
                id="atom:a",
                version=1,
                predicate="p",
                args=["x"],  # type: ignore[arg-type]
                frame="f",
                grade=None,
            )
        with self.assertRaises(TypeError):
            DraftRule._from_extraction(
                id="rule:r",
                version=1,
                head=ref,
                positive={ref},  # type: ignore[arg-type]
                evidence_request=DraftRef("evidence:e", 1),
            )
        with self.assertRaises(TypeError):
            DraftPackage._from_extraction(
                schema="pff-draft/0.1",
                atoms=[],  # type: ignore[arg-type]
                rules=(),
                evidence_requests=(),
            )


class DraftRefTests(unittest.TestCase):
    def test_exact_boundaries(self) -> None:
        self.assertEqual(DraftRef("i" * 262_144, 1).version, 1)
        self.assertEqual(DraftRef("id", MAX_INTEGER).version, MAX_INTEGER)
        multibyte_at_limit = "é" * 131_072
        self.assertEqual(
            DraftRef(multibyte_at_limit, 1).id,
            multibyte_at_limit,
        )

        for identifier in (
            "",
            "i" * 262_145,
            "é" * 131_072 + "a",
            "__pff__:generated",
            "\ud800",
        ):
            with self.subTest(identifier=repr(identifier[:20])):
                with self.assertRaises(ValueError):
                    DraftRef(identifier, 1)
        for identifier in (b"id", StringSubclass("id")):
            with self.subTest(identifier=repr(identifier)):
                with self.assertRaises(TypeError):
                    DraftRef(identifier, 1)  # type: ignore[arg-type]

        for version in (0, -1, MAX_INTEGER + 1):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    DraftRef("id", version)
        for version in (True, "1", 1.0, IntegerSubclass(1)):
            with self.subTest(version=version):
                with self.assertRaises(TypeError):
                    DraftRef("id", version)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
