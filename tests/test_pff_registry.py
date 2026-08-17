from __future__ import annotations

import ast
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import poietics.pff.registry as registry_module
from poietics.pff.model import RecordKind, RecordRef
from poietics.pff.registry import (
    ArgumentTypeContract,
    CheckerContract,
    CheckerDetailField,
    CheckerDetailType,
    CheckerUse,
    ChallengeTargetContract,
    ComputabilityClass,
    ContraryPolicy,
    ContraryPolicyMode,
    DischargeCompatibility,
    FramePolicy,
    FramePolicyMode,
    GradePolicy,
    LocalClosureSemantics,
    PredicateDefinition,
    PredicateRegistry,
    RegistryCatalog,
    RegistryDefinitionError,
    RegistryDefinitionErrorCode,
    SelectorFieldContract,
)


def argument_type() -> ArgumentTypeContract:
    return ArgumentTypeContract(
        argument_type_id="entity_ref",
        version=1,
        required_prefix="entity:",
    )


def exact_frame_policy() -> FramePolicy:
    return FramePolicy(
        frame_policy_id="exact-package",
        version=1,
        mode=FramePolicyMode.EXACT_PACKAGE,
    )


def forbidden_contrary_policy() -> ContraryPolicy:
    return ContraryPolicy(
        contrary_policy_id="forbidden",
        version=1,
        mode=ContraryPolicyMode.FORBIDDEN,
    )


def comparison_contrary_policy() -> ContraryPolicy:
    return ContraryPolicy(
        contrary_policy_id="entity-boundary",
        version=1,
        mode=ContraryPolicyMode.STABLE_COMPARISON_BOUNDARY,
        comparison_boundary="interpretation:1",
        comparison_arg_positions=(0,),
        include_frame=True,
    )


def rule_checker() -> CheckerContract:
    return CheckerContract(
        checker_id="rule-witness/v1",
        version=1,
        uses={CheckerUse.CERTIFICATE},
        certificate_subject_kinds={RecordKind.RULE},
        detail_fields=(
            CheckerDetailField(
                key="witness_ref",
                value_type=CheckerDetailType.NONEMPTY_STRING,
            ),
        ),
    )


def closure_checker() -> CheckerContract:
    return CheckerContract(
        checker_id="materialised-selector/v1",
        version=1,
        uses={CheckerUse.CLOSURE},
        local_closure_semantics=LocalClosureSemantics.MATERIALISED_SELECTOR_V1,
        closure_selector_kinds={RecordKind.DISCHARGE},
        selector_fields=(
            SelectorFieldContract(
                record_type=RecordKind.DISCHARGE,
                field="challenge",
                value_type=CheckerDetailType.RECORD_REF,
                allowed_record_kinds={RecordKind.CHALLENGE},
            ),
        ),
        closure_frame_policy_id="exact-package",
    )


def predicate(**changes: object) -> PredicateDefinition:
    candidate = PredicateDefinition(
        predicate_id="test.derived",
        version=1,
        arg_type_ids=("entity_ref",),
        frame_policy_id="exact-package",
        grade_policy=GradePolicy.FORBIDDEN,
        computability_class=ComputabilityClass.FIN,
        primitive_allowed=False,
        allowed_face_kinds={"frame"},
        allowed_challenge_kinds={"undercut"},
        checker_contract_ids={"rule-witness/v1"},
        contrary_policy_id="entity-boundary",
        rule_schema_ids={"schema:test-derived"},
    )
    return replace(candidate, **changes)


def make_registry(
    *,
    predicates: object | None = None,
    argument_types: object | None = None,
    frame_policies: object | None = None,
    contrary_policies: object | None = None,
    checker_contracts: object | None = None,
    rule_schema_ids: object | None = None,
    **changes: object,
) -> PredicateRegistry:
    values: dict[str, object] = {
        "registry_id": "test-registry/1",
        "version": 1,
        "argument_types": (argument_type(),)
        if argument_types is None
        else argument_types,
        "frame_policies": (exact_frame_policy(),)
        if frame_policies is None
        else frame_policies,
        "contrary_policies": (
            forbidden_contrary_policy(),
            comparison_contrary_policy(),
        )
        if contrary_policies is None
        else contrary_policies,
        "checker_contracts": (rule_checker(), closure_checker())
        if checker_contracts is None
        else checker_contracts,
        "predicates": (predicate(),) if predicates is None else predicates,
        "rule_schema_ids": {"schema:test-derived"}
        if rule_schema_ids is None
        else rule_schema_ids,
    }
    values.update(changes)
    return PredicateRegistry(**values)  # type: ignore[arg-type]


class LocalPolicyTests(unittest.TestCase):
    def test_argument_type_is_nominal_deterministic_and_has_no_callback(self) -> None:
        contract = argument_type()

        self.assertTrue(contract.accepts("entity:e"))
        self.assertFalse(contract.accepts("outcome:q"))
        self.assertFalse(contract.accepts(""))
        self.assertFalse(contract.accepts(1))
        self.assertFalse(hasattr(contract, "validator"))

    def test_frame_modes_are_exact_and_nonempty(self) -> None:
        exact = exact_frame_policy()
        nonempty = FramePolicy(
            frame_policy_id="nonempty",
            version=1,
            mode=FramePolicyMode.NONEMPTY,
        )

        self.assertTrue(exact.accepts("frame:1", package_frame="frame:1"))
        self.assertFalse(exact.accepts("frame:2", package_frame="frame:1"))
        self.assertTrue(nonempty.accepts("frame:2", package_frame="frame:1"))
        self.assertFalse(nonempty.accepts("", package_frame="frame:1"))

    def test_grade_policy_accepts_only_the_frozen_grade_vocabulary(self) -> None:
        for grade in ("h", "rho", "Phi"):
            self.assertTrue(GradePolicy.REQUIRED.accepts(grade))
            self.assertTrue(GradePolicy.OPTIONAL.accepts(grade))
        self.assertTrue(GradePolicy.FORBIDDEN.accepts(None))
        self.assertTrue(GradePolicy.OPTIONAL.accepts(None))
        self.assertFalse(GradePolicy.REQUIRED.accepts(None))
        self.assertFalse(GradePolicy.FORBIDDEN.accepts("h"))
        self.assertFalse(GradePolicy.OPTIONAL.accepts("unknown"))

    def test_contrary_policy_has_stable_boundary_and_comparison_key(self) -> None:
        forbidden = forbidden_contrary_policy()
        comparison = comparison_contrary_policy()

        self.assertFalse(forbidden.accepts_boundary("interpretation:1"))
        self.assertIsNone(forbidden.comparison_key(args=("entity:e",), frame="f"))
        self.assertTrue(comparison.accepts_boundary("interpretation:1"))
        self.assertFalse(comparison.accepts_boundary("interpretation:2"))
        self.assertEqual(
            comparison.comparison_key(args=("entity:e",), frame="frame:1"),
            ("interpretation:1", "frame:1", "entity:e"),
        )
        self.assertNotEqual(
            comparison.comparison_key(args=("entity:e",), frame="frame:1"),
            comparison.comparison_key(args=("entity:other",), frame="frame:1"),
        )

    def test_checker_contract_is_local_shape_metadata_only(self) -> None:
        checker = rule_checker()

        self.assertTrue(checker.permits_certificate(RecordKind.RULE))
        self.assertFalse(checker.permits_certificate(RecordKind.CHALLENGE))
        self.assertTrue(checker.accepts_details({"witness_ref": "witness:1"}))
        self.assertFalse(checker.accepts_details({}))
        self.assertFalse(checker.accepts_details({"witness_ref": 17}))
        self.assertFalse(checker.supports_closure_selector(RecordKind.DISCHARGE))
        self.assertFalse(hasattr(checker, "required_detail_keys"))

        selector_checker = closure_checker()
        self.assertTrue(
            selector_checker.accepts_selector_shape(
                record_type=RecordKind.DISCHARGE,
                where={"challenge": RecordRef("challenge:1", 1)},
            )
        )
        self.assertFalse(
            selector_checker.accepts_selector_shape(
                record_type=RecordKind.DISCHARGE,
                where={"bogus": 17},
            )
        )
        self.assertIs(
            selector_checker.local_closure_semantics,
            LocalClosureSemantics.MATERIALISED_SELECTOR_V1,
        )


class RegistryConstructionTests(unittest.TestCase):
    def assert_registry_error(
        self,
        code: RegistryDefinitionErrorCode,
        factory: object,
    ) -> None:
        with self.assertRaises(RegistryDefinitionError) as caught:
            factory()  # type: ignore[operator]
        self.assertEqual(caught.exception.code, code)

    def test_registry_copies_and_deeply_freezes_all_authority_inputs(self) -> None:
        predicates = [predicate()]
        schemas = ["schema:test-derived"]
        registry = make_registry(predicates=predicates, rule_schema_ids=schemas)
        predicates.clear()
        schemas.clear()

        self.assertEqual(tuple(item.predicate_id for item in registry.predicates), ("test.derived",))
        self.assertEqual(registry.rule_schema_ids, frozenset({"schema:test-derived"}))
        self.assertIsInstance(registry.predicates, tuple)
        self.assertIsInstance(registry.known_face_kinds, frozenset)
        self.assertIsInstance(
            registry.discharge_compatibility[1].admissible_discharge_kinds,
            frozenset,
        )
        with self.assertRaises(FrozenInstanceError):
            registry.registry_id = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            registry.predicates[0].primitive_allowed = True  # type: ignore[misc]

    def test_rejects_duplicate_definition_and_vocabulary_ids(self) -> None:
        duplicate_factories = (
            lambda: make_registry(argument_types=(argument_type(), argument_type())),
            lambda: make_registry(predicates=(predicate(), predicate())),
            lambda: make_registry(rule_schema_ids=["schema:test-derived"] * 2),
        )
        for factory in duplicate_factories:
            with self.subTest(factory=factory):
                self.assert_registry_error(
                    RegistryDefinitionErrorCode.DUPLICATE_ID,
                    factory,
                )

    def test_every_versioned_definition_rejects_bool_zero_and_negative(self) -> None:
        examples = (
            argument_type(),
            exact_frame_policy(),
            forbidden_contrary_policy(),
            rule_checker(),
            predicate(),
            make_registry(),
        )
        for example in examples:
            for bad_version in (True, 0, -1):
                with self.subTest(type=type(example).__name__, version=bad_version):
                    self.assert_registry_error(
                        RegistryDefinitionErrorCode.INVALID_VERSION,
                        lambda example=example, bad_version=bad_version: replace(
                            example,
                            version=bad_version,
                        ),
                    )

    def test_rejects_unknown_predicate_references_at_registry_construction(self) -> None:
        cases = (
            (
                RegistryDefinitionErrorCode.UNKNOWN_ARGUMENT_TYPE,
                predicate(arg_type_ids=("missing",)),
            ),
            (
                RegistryDefinitionErrorCode.UNKNOWN_FRAME_POLICY,
                predicate(frame_policy_id="missing"),
            ),
            (
                RegistryDefinitionErrorCode.UNKNOWN_CONTRARY_POLICY,
                predicate(contrary_policy_id="missing"),
            ),
            (
                RegistryDefinitionErrorCode.UNKNOWN_CHECKER_CONTRACT,
                predicate(checker_contract_ids={"missing"}),
            ),
            (
                RegistryDefinitionErrorCode.UNKNOWN_FACE_KIND,
                predicate(allowed_face_kinds={"missing"}),
            ),
            (
                RegistryDefinitionErrorCode.UNKNOWN_CHALLENGE_KIND,
                predicate(allowed_challenge_kinds={"missing"}),
            ),
            (
                RegistryDefinitionErrorCode.UNKNOWN_RULE_SCHEMA,
                predicate(rule_schema_ids={"missing"}),
            ),
        )
        for code, bad_predicate in cases:
            with self.subTest(code=code):
                self.assert_registry_error(
                    code,
                    lambda bad_predicate=bad_predicate: make_registry(
                        predicates=(bad_predicate,)
                    ),
                )

    def test_rejects_incoherent_checker_and_contrary_contracts(self) -> None:
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: CheckerDetailField(
                key="subject",
                value_type=CheckerDetailType.RECORD_REF,
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: CheckerContract(
                checker_id="inert-selector-field",
                version=1,
                uses={CheckerUse.CLOSURE},
                closure_selector_kinds={RecordKind.DISCHARGE},
                selector_fields=(
                    SelectorFieldContract(
                        record_type=RecordKind.CHALLENGE,
                        field="target",
                        value_type=CheckerDetailType.RECORD_REF,
                        allowed_record_kinds={RecordKind.ATOM},
                    ),
                ),
                closure_frame_policy_id="exact-package",
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: CheckerContract(
                checker_id="empty",
                version=1,
                uses=frozenset(),
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: CheckerContract(
                checker_id="local-certificate",
                version=1,
                uses={CheckerUse.CERTIFICATE},
                local_closure_semantics=(
                    LocalClosureSemantics.MATERIALISED_SELECTOR_V1
                ),
                certificate_subject_kinds={RecordKind.RULE},
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: replace(
                closure_checker(),
                local_closure_semantics=LocalClosureSemantics.NONE,
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: replace(
                closure_checker(),
                checker_id="materialised-selector-alias/v1",
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: replace(
                closure_checker(),
                uses={CheckerUse.CLOSURE, CheckerUse.CERTIFICATE},
                certificate_subject_kinds={RecordKind.RULE},
            ),
        )
        for selector_field in (
            SelectorFieldContract(
                record_type=RecordKind.DISCHARGE,
                field="challenge",
                value_type=CheckerDetailType.NONEMPTY_STRING,
            ),
            SelectorFieldContract(
                record_type=RecordKind.DISCHARGE,
                field="challenge",
                value_type=CheckerDetailType.RECORD_REF,
                allowed_record_kinds={RecordKind.CLOSURE},
            ),
            SelectorFieldContract(
                record_type=RecordKind.DISCHARGE,
                field="future-selector",
                value_type=CheckerDetailType.NONEMPTY_STRING,
            ),
        ):
            with self.subTest(selector_field=selector_field):
                self.assert_registry_error(
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                    lambda selector_field=selector_field: replace(
                        closure_checker(),
                        selector_fields=(selector_field,),
                    ),
                )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: CheckerContract(
                checker_id="certificate-without-subjects",
                version=1,
                uses={CheckerUse.CERTIFICATE},
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: CheckerContract(
                checker_id="closure-without-frame-policy",
                version=1,
                uses={CheckerUse.CLOSURE},
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: ContraryPolicy(
                contrary_policy_id="bad-forbidden",
                version=1,
                mode=ContraryPolicyMode.FORBIDDEN,
                comparison_boundary="forbidden-boundary",
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.UNKNOWN_FRAME_POLICY,
            lambda: make_registry(
                checker_contracts=(
                    rule_checker(),
                    replace(
                        closure_checker(),
                        closure_frame_policy_id="missing",
                    ),
                ),
            ),
        )

    def test_challenge_target_contracts_are_complete_and_typed(self) -> None:
        authority = make_registry()
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: replace(
                authority,
                challenge_target_contracts=authority.challenge_target_contracts[:-1],
            ),
        )
        undercut_override = tuple(
            replace(item, allowed_target_kinds={RecordKind.ATOM})
            if item.challenge_kind == "undercut"
            else item
            for item in authority.challenge_target_contracts
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: replace(
                authority,
                challenge_target_contracts=undercut_override,
            ),
        )
        narrowed_targets = tuple(
            replace(item, allowed_target_kinds={RecordKind.FACE})
            if item.challenge_kind == "undercut"
            else item
            for item in authority.challenge_target_contracts
        )
        narrowed = replace(
            authority,
            challenge_target_contracts=narrowed_targets,
        )
        self.assertEqual(
            narrowed.allowed_challenge_target_kinds("undercut"),
            frozenset({RecordKind.FACE}),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: ChallengeTargetContract(
                challenge_kind="undercut",
                allowed_target_kinds={RecordKind.ATOM, RecordKind.CLOSURE},
            ),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: make_registry(
                predicates=(predicate(checker_contract_ids={"closure-only"}),),
                checker_contracts=(
                    rule_checker(),
                    CheckerContract(
                        checker_id="closure-only",
                        version=1,
                        uses={CheckerUse.CLOSURE},
                        closure_selector_kinds={RecordKind.DISCHARGE},
                        closure_frame_policy_id="exact-package",
                    ),
                ),
            ),
        )

    def test_required_face_kind_is_exact_immutable_and_structurally_coherent(
        self,
    ) -> None:
        class StringSubclass(str):
            pass

        default_contract = ChallengeTargetContract(
            challenge_kind="undercut",
            allowed_target_kinds={RecordKind.RULE, RecordKind.FACE},
        )
        exact_contract = ChallengeTargetContract(
            challenge_kind="localisation_gap",
            allowed_target_kinds={RecordKind.FACE},
            required_face_kind="localisation",
        )

        self.assertIsNone(default_contract.required_face_kind)
        self.assertEqual(exact_contract.required_face_kind, "localisation")
        self.assertEqual(
            exact_contract.allowed_target_kinds,
            frozenset({RecordKind.FACE}),
        )
        with self.assertRaises(FrozenInstanceError):
            exact_contract.required_face_kind = "recovery"  # type: ignore[misc]

        for bad_value in ("", 17, StringSubclass("localisation")):
            with self.subTest(bad_value=bad_value):
                with self.assertRaises(RegistryDefinitionError) as caught:
                    ChallengeTargetContract(
                        challenge_kind="localisation_gap",
                        allowed_target_kinds={RecordKind.FACE},
                        required_face_kind=bad_value,  # type: ignore[arg-type]
                    )
                self.assertEqual(
                    caught.exception.code,
                    RegistryDefinitionErrorCode.INVALID_ID,
                )
                self.assertEqual(
                    caught.exception.location,
                    "challenge_target:localisation_gap.required_face_kind",
                )
                self.assertEqual(caught.exception.identifiers, ())

        with self.assertRaises(RegistryDefinitionError) as caught:
            ChallengeTargetContract(
                challenge_kind="localisation_gap",
                allowed_target_kinds={RecordKind.RULE},
                required_face_kind="",
            )
        self.assertEqual(
            caught.exception.code,
            RegistryDefinitionErrorCode.INVALID_ID,
        )
        self.assertEqual(
            caught.exception.location,
            "challenge_target:localisation_gap.required_face_kind",
        )
        self.assertEqual(caught.exception.identifiers, ())

        for incoherent_targets in (
            {RecordKind.RULE},
            {RecordKind.RULE, RecordKind.FACE},
            frozenset(),
        ):
            with self.subTest(incoherent_targets=incoherent_targets):
                with self.assertRaises(RegistryDefinitionError) as caught:
                    ChallengeTargetContract(
                        challenge_kind="localisation_gap",
                        allowed_target_kinds=incoherent_targets,
                        required_face_kind="localisation",
                    )
                self.assertEqual(
                    caught.exception.code,
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                )
                self.assertEqual(
                    caught.exception.location,
                    "challenge_target:localisation_gap.required_face_kind",
                )
                self.assertEqual(caught.exception.identifiers, ())

    def test_core_required_face_mappings_and_extension_lookup_are_exact(self) -> None:
        authority = make_registry()
        expected = {
            "localisation_gap": "localisation",
            "recovery_gap": "recovery",
            "closure_gap": "closure",
        }

        for challenge_kind, face_kind in expected.items():
            with self.subTest(challenge_kind=challenge_kind):
                contract = authority.challenge_target_contract(challenge_kind)
                self.assertEqual(contract.required_face_kind, face_kind)
                self.assertEqual(
                    contract.allowed_target_kinds,
                    frozenset({RecordKind.FACE}),
                )
                self.assertEqual(
                    authority.allowed_challenge_target_kinds(challenge_kind),
                    contract.allowed_target_kinds,
                )

        self.assertIsNone(
            authority.challenge_target_contract("undercut").required_face_kind
        )
        with self.assertRaises(KeyError):
            authority.challenge_target_contract("missing")

        extension_kind = "extension_gap"
        extension_contract = ChallengeTargetContract(
            challenge_kind=extension_kind,
            allowed_target_kinds={RecordKind.FACE},
            required_face_kind="frame",
        )
        extended = replace(
            authority,
            known_challenge_kinds=authority.known_challenge_kinds | {extension_kind},
            discharge_compatibility=(
                *authority.discharge_compatibility,
                DischargeCompatibility(challenge_kind=extension_kind),
            ),
            challenge_target_contracts=(
                *authority.challenge_target_contracts,
                extension_contract,
            ),
        )
        self.assertIs(
            extended.challenge_target_contract(extension_kind),
            extension_contract,
        )
        self.assertEqual(
            extended.allowed_challenge_target_kinds(extension_kind),
            frozenset({RecordKind.FACE}),
        )

        unknown_extension_contract = replace(
            extension_contract,
            required_face_kind="missing-extension-face",
        )
        with self.assertRaises(RegistryDefinitionError) as caught:
            replace(
                authority,
                known_challenge_kinds=authority.known_challenge_kinds
                | {extension_kind},
                discharge_compatibility=(
                    *authority.discharge_compatibility,
                    DischargeCompatibility(challenge_kind=extension_kind),
                ),
                challenge_target_contracts=(
                    *authority.challenge_target_contracts,
                    unknown_extension_contract,
                ),
            )
        self.assertEqual(
            caught.exception.code,
            RegistryDefinitionErrorCode.UNKNOWN_FACE_KIND,
        )
        self.assertEqual(
            caught.exception.location,
            "registry:test-registry/1.challenge_target_contracts",
        )
        self.assertEqual(
            caught.exception.identifiers,
            ("missing-extension-face",),
        )

    def test_required_face_ceiling_and_unknown_face_precedence_are_exact(self) -> None:
        authority = make_registry()

        unknown_face_targets = tuple(
            replace(item, required_face_kind="missing-face-kind")
            if item.challenge_kind == "localisation_gap"
            else item
            for item in authority.challenge_target_contracts
        )
        with self.assertRaises(RegistryDefinitionError) as caught:
            replace(
                authority,
                challenge_target_contracts=unknown_face_targets,
            )
        self.assertEqual(
            caught.exception.code,
            RegistryDefinitionErrorCode.UNKNOWN_FACE_KIND,
        )
        self.assertEqual(
            caught.exception.location,
            "registry:test-registry/1.challenge_target_contracts",
        )
        self.assertEqual(caught.exception.identifiers, ("missing-face-kind",))

        two_unknown_face_targets = tuple(
            replace(
                item,
                required_face_kind={
                    "localisation_gap": "missing-z-face-kind",
                    "recovery_gap": "missing-a-face-kind",
                }[item.challenge_kind],
            )
            if item.challenge_kind in {"localisation_gap", "recovery_gap"}
            else item
            for item in authority.challenge_target_contracts
        )
        with self.assertRaises(RegistryDefinitionError) as caught:
            replace(
                authority,
                challenge_target_contracts=two_unknown_face_targets,
            )
        self.assertEqual(
            caught.exception.code,
            RegistryDefinitionErrorCode.UNKNOWN_FACE_KIND,
        )
        self.assertEqual(
            caught.exception.location,
            "registry:test-registry/1.challenge_target_contracts",
        )
        self.assertEqual(
            caught.exception.identifiers,
            ("missing-a-face-kind", "missing-z-face-kind"),
        )

        ceiling_changes = (
            ("localisation_gap", {"required_face_kind": "recovery"}),
            ("localisation_gap", {"required_face_kind": None}),
            (
                "undercut",
                {
                    "allowed_target_kinds": {RecordKind.FACE},
                    "required_face_kind": "frame",
                },
            ),
        )
        for challenge_kind, changes in ceiling_changes:
            with self.subTest(challenge_kind=challenge_kind, changes=changes):
                changed_targets = tuple(
                    replace(item, **changes)
                    if item.challenge_kind == challenge_kind
                    else item
                    for item in authority.challenge_target_contracts
                )
                with self.assertRaises(RegistryDefinitionError) as caught:
                    replace(
                        authority,
                        challenge_target_contracts=changed_targets,
                    )
                self.assertEqual(
                    caught.exception.code,
                    RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
                )
                self.assertEqual(
                    caught.exception.location,
                    "registry:test-registry/1.challenge_target_contracts",
                )
                self.assertEqual(caught.exception.identifiers, (challenge_kind,))

        two_ceiling_offenders = tuple(
            replace(
                item,
                **{
                    "localisation_gap": {"required_face_kind": "recovery"},
                    "undercut": {
                        "allowed_target_kinds": {RecordKind.FACE},
                        "required_face_kind": "frame",
                    },
                }[item.challenge_kind],
            )
            if item.challenge_kind in {"localisation_gap", "undercut"}
            else item
            for item in authority.challenge_target_contracts
        )
        with self.assertRaises(RegistryDefinitionError) as caught:
            replace(
                authority,
                challenge_target_contracts=two_ceiling_offenders,
            )
        self.assertEqual(
            caught.exception.code,
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
        )
        self.assertEqual(
            caught.exception.location,
            "registry:test-registry/1.challenge_target_contracts",
        )
        self.assertEqual(
            caught.exception.identifiers,
            ("localisation_gap", "undercut"),
        )

    def test_rejects_incoherent_compatibility_vocabulary(self) -> None:
        table = tuple(make_registry().discharge_compatibility)
        self.assert_registry_error(
            RegistryDefinitionErrorCode.INCOHERENT_CONTRACT,
            lambda: make_registry(discharge_compatibility=table[:-1]),
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.UNKNOWN_CHALLENGE_KIND,
            lambda: make_registry(
                discharge_compatibility=(
                    *table,
                    DischargeCompatibility(challenge_kind="unknown"),
                )
            ),
        )
        modified = tuple(
            replace(
                item,
                admissible_discharge_kinds={"unknown-discharge"},
            )
            if item.challenge_kind == "rebut"
            else item
            for item in table
        )
        self.assert_registry_error(
            RegistryDefinitionErrorCode.UNKNOWN_DISCHARGE_KIND,
            lambda: make_registry(discharge_compatibility=modified),
        )


class RegistryLookupTests(unittest.TestCase):
    def test_registry_exposes_exact_policy_and_compatibility_lookup(self) -> None:
        registry = make_registry()

        self.assertEqual(registry.predicate("test.derived"), predicate())
        self.assertEqual(registry.argument_type("entity_ref"), argument_type())
        self.assertEqual(registry.frame_policy("exact-package"), exact_frame_policy())
        self.assertEqual(
            registry.contrary_policy("entity-boundary"),
            comparison_contrary_policy(),
        )
        self.assertEqual(registry.checker_contract("rule-witness/v1"), rule_checker())
        self.assertEqual(
            registry.allowed_challenge_target_kinds("undercut"),
            frozenset({RecordKind.RULE, RecordKind.FACE}),
        )
        self.assertEqual(
            registry.admissible_discharge_kinds("undercut"),
            frozenset({"repair", "malformed_or_inapplicable"}),
        )
        self.assertTrue(
            registry.is_discharge_compatible(
                challenge_kind="undercut",
                discharge_kind="repair",
            )
        )
        self.assertFalse(
            registry.is_discharge_compatible(
                challenge_kind="undercut",
                discharge_kind="recovery_witness",
            )
        )
        with self.assertRaises(KeyError):
            registry.predicate("missing")
        with self.assertRaises(KeyError):
            registry.is_discharge_compatible(
                challenge_kind="undercut",
                discharge_kind="unknown",
            )

    def test_catalog_rejects_duplicate_ids_and_has_no_version_fallback(self) -> None:
        registry = make_registry()
        duplicate_id = replace(registry, version=2)

        self.assert_registry_catalog_duplicate(registry, duplicate_id)
        catalog = RegistryCatalog(registries=[registry])
        self.assertIs(catalog.lookup("test-registry/1"), registry)
        with self.assertRaises(KeyError):
            catalog.lookup("test-registry")
        with self.assertRaises(KeyError):
            catalog.lookup("test-registry/2")
        self.assertFalse(hasattr(catalog, "register"))

    def assert_registry_catalog_duplicate(
        self,
        first: PredicateRegistry,
        second: PredicateRegistry,
    ) -> None:
        with self.assertRaises(RegistryDefinitionError) as caught:
            RegistryCatalog(registries=(first, second))
        self.assertEqual(
            caught.exception.code,
            RegistryDefinitionErrorCode.DUPLICATE_REGISTRY_ID,
        )


class DependencyBoundaryTests(unittest.TestCase):
    def test_registry_imports_only_the_pff_model_from_project_code(self) -> None:
        source = Path(registry_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        import_from_signatures = {
            (
                node.level,
                node.module,
                frozenset((alias.name, alias.asname) for alias in node.names),
            )
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        import_signatures = {
            (alias.name, alias.asname)
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        self.assertEqual(
            import_from_signatures,
            {
                (0, "__future__", frozenset({("annotations", None)})),
                (
                    0,
                    "collections.abc",
                    frozenset({("Iterable", None), ("Mapping", None)}),
                ),
                (
                    0,
                    "dataclasses",
                    frozenset({("dataclass", None), ("field", None)}),
                ),
                (0, "enum", frozenset({("StrEnum", None)})),
                (0, "types", frozenset({("MappingProxyType", None)})),
                (0, "typing", frozenset({("TypeVar", None)})),
                (
                    1,
                    "model",
                    frozenset({("RecordKind", None), ("RecordRef", None)}),
                ),
            },
        )
        self.assertEqual(import_signatures, set())


if __name__ == "__main__":
    unittest.main()
