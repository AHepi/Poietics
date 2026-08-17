from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError

from poietics.pff.model import (
    AtomRecord,
    BasePartition,
    CertificateRecord,
    ChallengeRecord,
    CheckResult,
    ClosedNegativeLiteral,
    ClosureRecord,
    ContraryRecord,
    DischargeRecord,
    FaceRecord,
    Package,
    PackageHeader,
    RecordKind,
    RecordRef,
    RuleRecord,
    Selector,
    VersionToken,
)


def ref(record_id: str, version: int = 1) -> RecordRef:
    return RecordRef(record_id, version)


def header(*, metadata: object | None = None) -> PackageHeader:
    return PackageHeader(
        schema="pff-core/0.1",
        package_id="package:test",
        cut_id="cut:1",
        frame_id="frame:1",
        registry_id="registry:test/1",
        metadata={} if metadata is None else metadata,  # type: ignore[arg-type]
    )


def atom(record_id: str, *, args: object = ()) -> AtomRecord:
    return AtomRecord(
        id=record_id,
        version=1,
        predicate="test.predicate",
        args=args,  # type: ignore[arg-type]
        frame="frame:1",
        grade=None,
        primitive=False,
    )


def certificate(record_id: str, subject: RecordRef) -> CertificateRecord:
    return CertificateRecord(
        id=record_id,
        version=1,
        checker="checker/test-v1",
        subject=subject,
        result=CheckResult.PASS,
        payload_hash="sha256:test",
        details={},
    )


class ExactIdentityTests(unittest.TestCase):
    def test_record_refs_and_external_version_tokens_are_structurally_distinct(self) -> None:
        record_ref = RecordRef("atom:a", 0)
        token = VersionToken("atom:a", 0)

        self.assertEqual(record_ref, RecordRef("atom:a", 0))
        self.assertNotEqual(record_ref, token)
        self.assertEqual({record_ref}, {RecordRef("atom:a", 0)})

    def test_semantically_bad_identity_values_remain_representable(self) -> None:
        candidate = atom("")
        package = Package(
            header=header(),
            atoms=(candidate,),
            base=BasePartition(
                live=[candidate.ref],
                excluded=[candidate.ref],
            ),
        )

        self.assertEqual(candidate.version, 1)
        self.assertEqual(candidate.id, "")
        self.assertEqual(package.base.live & package.base.excluded, {candidate.ref})

    def test_structurally_invalid_identity_types_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            RecordRef("atom:a", True)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            VersionToken(17, 1)  # type: ignore[arg-type]


class DependencyBoundaryTests(unittest.TestCase):
    def test_importing_model_does_not_eager_load_policy_or_evaluation(self) -> None:
        script = (
            "import sys; "
            "import poietics.pff.model; "
            "assert 'poietics.pff.registry' not in sys.modules; "
            "assert 'poietics.pff.validate' not in sys.modules; "
            "assert 'poietics.ground' not in sys.modules"
        )
        subprocess.run(
            [sys.executable, "-B", "-c", script],
            check=True,
            capture_output=True,
            text=True,
        )


class DeepImmutabilityTests(unittest.TestCase):
    def test_nested_objects_are_copied_and_recursively_frozen(self) -> None:
        metadata = {
            "nested": {
                "items": ["one", {"leaf": "before"}],
                "labels": {"alpha", "beta"},
            }
        }
        details = {"witness": {"steps": [1, 2]}}
        where = {"challenge": {"refs": [ref("challenge:c")]}}

        package_header = header(metadata=metadata)
        cert = CertificateRecord(
            id="cert:1",
            version=1,
            checker="checker/test-v1",
            subject=ref("atom:a"),
            result=CheckResult.OPEN,
            payload_hash="sha256:test",
            details=details,
        )
        selector = Selector(record_type=RecordKind.CHALLENGE, where=where)

        metadata["nested"]["items"][1]["leaf"] = "after"  # type: ignore[index]
        metadata["nested"]["labels"].add("gamma")  # type: ignore[index,union-attr]
        details["witness"]["steps"].append(3)  # type: ignore[index,union-attr]
        where["challenge"]["refs"].append(ref("challenge:d"))  # type: ignore[index,union-attr]

        frozen_nested = package_header.metadata["nested"]
        self.assertEqual(frozen_nested["items"][1]["leaf"], "before")  # type: ignore[index]
        self.assertEqual(frozen_nested["labels"], frozenset({"alpha", "beta"}))  # type: ignore[index]
        self.assertEqual(cert.details["witness"]["steps"], (1, 2))  # type: ignore[index]
        self.assertEqual(
            selector.where["challenge"]["refs"],  # type: ignore[index]
            (ref("challenge:c"),),
        )

        with self.assertRaises(TypeError):
            package_header.metadata["new"] = "value"  # type: ignore[index]
        with self.assertRaises(TypeError):
            frozen_nested["new"] = "value"  # type: ignore[index]
        with self.assertRaises(TypeError):
            package_header.metadata._items = ()  # type: ignore[attr-defined]
        with self.assertRaises(TypeError):
            del package_header.metadata._items  # type: ignore[attr-defined]

    def test_ordered_inputs_are_copied_without_reordering_or_deduplication(self) -> None:
        args = ["second", "first", "second"]
        atoms = [atom("atom:z"), atom("atom:a")]

        candidate = atom("atom:ordered", args=args)
        package = Package(header=header(), atoms=atoms)
        args.clear()
        atoms.reverse()

        self.assertEqual(candidate.args, ("second", "first", "second"))
        self.assertEqual(tuple(item.id for item in package.atoms), ("atom:z", "atom:a"))

    def test_records_and_package_are_frozen(self) -> None:
        candidate = atom("atom:a")
        package = Package(header=header(), atoms=(candidate,))

        with self.assertRaises(FrozenInstanceError):
            candidate.id = "atom:b"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            package.atoms = ()  # type: ignore[misc]


class CollectionShapeTests(unittest.TestCase):
    def test_string_and_bytes_are_never_treated_as_collections(self) -> None:
        for malformed in ("abc", b"abc", bytearray(b"abc")):
            with self.subTest(field="args", value=type(malformed).__name__):
                with self.assertRaises(TypeError):
                    atom("atom:a", args=malformed)

            with self.subTest(field="positive", value=type(malformed).__name__):
                with self.assertRaises(TypeError):
                    RuleRecord(
                        id="rule:1",
                        version=1,
                        head=ref("atom:h"),
                        positive=malformed,  # type: ignore[arg-type]
                        certificate=ref("cert:1"),
                    )

            with self.subTest(field="atoms", value=type(malformed).__name__):
                with self.assertRaises(TypeError):
                    Package(header=header(), atoms=malformed)  # type: ignore[arg-type]

    def test_mutable_and_duck_typed_record_members_are_rejected(self) -> None:
        fake_ref = {"id": "atom:a", "version": 1}
        fake_atom = {
            "id": "atom:a",
            "version": 1,
            "predicate": "test.predicate",
        }

        with self.assertRaises(TypeError):
            RuleRecord(
                id="rule:1",
                version=1,
                head=fake_ref,  # type: ignore[arg-type]
                certificate=ref("cert:1"),
            )
        with self.assertRaises(TypeError):
            ClosureRecord(
                id="closure:1",
                version=1,
                checker="checker/test-v1",
                result=CheckResult.PASS,
                cut_id="cut:1",
                frame="frame:1",
                selector={"record_type": "atom"},  # type: ignore[arg-type]
            )
        with self.assertRaises(TypeError):
            Package(header=header(), atoms=[fake_atom])  # type: ignore[list-item]

    def test_duplicate_raw_members_are_rejected_for_every_set_valued_shape(self) -> None:
        atom_ref = ref("atom:a")
        face_ref = ref("face:1")
        literal = ClosedNegativeLiteral(
            atom=atom_ref,
            closure=ref("closure:1"),
        )

        cases = (
            lambda: RuleRecord(
                id="rule:positive",
                version=1,
                head=atom_ref,
                positive=[atom_ref, atom_ref],
                certificate=ref("cert:1"),
            ),
            lambda: RuleRecord(
                id="rule:negative",
                version=1,
                head=atom_ref,
                negative=[literal, literal],
                certificate=ref("cert:1"),
            ),
            lambda: RuleRecord(
                id="rule:faces",
                version=1,
                head=atom_ref,
                faces=[face_ref, face_ref],
                certificate=ref("cert:1"),
            ),
            lambda: ClosureRecord(
                id="closure:members",
                version=1,
                checker="checker/test-v1",
                result=CheckResult.PASS,
                cut_id="cut:1",
                frame="frame:1",
                selector=Selector(record_type=RecordKind.ATOM),
                members=[atom_ref, atom_ref],
            ),
            lambda: BasePartition(live=[atom_ref, atom_ref]),
        )

        for index, make_candidate in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises(ValueError):
                    make_candidate()


class CompleteRecordShapeTests(unittest.TestCase):
    def test_face_version_dependency_is_optional_opaque_data(self) -> None:
        without_version = FaceRecord(
            id="face:without-version",
            version=1,
            owner_rule=ref("rule:1"),
            kind="witness",
            boundary="frame:1",
            carrier="account:A",
            blocker_closure=ref("closure:1"),
        )
        with_version = FaceRecord(
            id="face:with-version",
            version=1,
            owner_rule=ref("rule:1"),
            kind="version",
            boundary="frame:1",
            carrier="account:A",
            blocker_closure=ref("closure:1"),
            depends_on_version=VersionToken("account:A", 4),
        )

        self.assertIsNone(without_version.depends_on_version)
        self.assertEqual(
            with_version.depends_on_version,
            VersionToken("account:A", 4),
        )

    def test_all_record_shapes_and_deterministic_accessors(self) -> None:
        atom_a = atom("atom:a")
        atom_b = atom("atom:b")
        cert = certificate("cert:rule", ref("rule:1"))
        closure = ClosureRecord(
            id="closure:1",
            version=1,
            checker="checker/selector-v1",
            result=CheckResult.FAIL,
            cut_id="cut:1",
            frame="frame:1",
            selector=Selector(
                record_type=RecordKind.DISCHARGE,
                where={"challenge": "challenge:1@1"},
            ),
            members=(),
        )
        face = FaceRecord(
            id="face:1",
            version=1,
            owner_rule=ref("rule:1"),
            kind="frame",
            boundary="frame:1",
            carrier="account:A",
            depends_on_version=VersionToken("account:A", 4),
            blocker_closure=closure.ref,
        )
        rule = RuleRecord(
            id="rule:1",
            version=1,
            head=atom_b.ref,
            positive=(atom_a.ref,),
            negative=(
                ClosedNegativeLiteral(atom=ref("atom:n"), closure=closure.ref),
            ),
            certificate=cert.ref,
            faces=(face.ref,),
        )
        contrary = ContraryRecord(
            id="contrary:1",
            version=1,
            left=atom_a.ref,
            right=atom_b.ref,
            boundary="interpretation:1",
        )
        challenge = ChallengeRecord(
            id="challenge:1",
            version=1,
            kind="undercut",
            target_kind=RecordKind.FACE,
            target=face.ref,
            certificate=ref("cert:challenge"),
            discharge_closure=closure.ref,
        )
        discharge = DischargeRecord(
            id="discharge:1",
            version=1,
            challenge=challenge.ref,
            kind="repair",
            certificate=ref("cert:discharge"),
        )
        package = Package(
            header=header(),
            atoms=(atom_b, atom_a),
            rules=(rule,),
            faces=(face,),
            certificates=(cert,),
            closures=(closure,),
            contraries=(contrary,),
            challenges=(challenge,),
            discharges=(discharge,),
            base=BasePartition(open=(atom_a.ref,)),
        )

        expected = (
            (RecordKind.ATOM, atom_b),
            (RecordKind.ATOM, atom_a),
            (RecordKind.RULE, rule),
            (RecordKind.FACE, face),
            (RecordKind.CERTIFICATE, cert),
            (RecordKind.CLOSURE, closure),
            (RecordKind.CONTRARY, contrary),
            (RecordKind.CHALLENGE, challenge),
            (RecordKind.DISCHARGE, discharge),
        )
        self.assertEqual(tuple(package.iter_records()), expected)
        self.assertEqual(package.records(RecordKind.ATOM), (atom_b, atom_a))
        self.assertEqual(contrary.ref, ref("contrary:1"))


if __name__ == "__main__":
    unittest.main()
