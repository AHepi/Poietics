from __future__ import annotations

import ast
import builtins
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import hashlib
import importlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import urllib.request

import poietics.generation.extract as extract_module
from poietics.generation.extract import extract_draft
from poietics.generation.model import (
    AttemptRef,
    AttemptRelation,
    GenerationEnvelope,
)
import poietics.generation.ollama as ollama_module
from poietics.generation.ollama import (
    OllamaAdapterCode,
    OllamaAdapterError,
    OllamaAdapterIssue,
    OllamaEndpoint,
    OllamaGenerateRequest,
    OllamaTransportError,
    OllamaTransportRequest,
    OllamaTransportResponse,
    generate_ollama,
)


ACCEPTED_PROFILE_SHA256 = (
    "9bc104160727dcc51ef4ddce6044e5dda81200ac51dc3a9394533cecc2ea433c"
)
REVIEWED_CANDIDATE_SHA256 = (
    "1a7fe234e6a5ae4753177e38c676f8a7cd4d69c155efb0383df0e1af6616f220"
)

A01_PROMPT = b'Return "caf\xc3\xa9".\n'
A01_PROMPT_SHA256 = (
    "sha256:0eb8a0f9ca20a8f70668d89433b6d6bad1e5bad1ff5710f5dd149474472a5c6a"
)
A01_REQUEST_BODY = (
    b'{"model":"test-model","prompt":"Return \\"caf\xc3\xa9\\".\\n",'
    b'"stream":false}'
)
A01_REQUEST_SHA256 = (
    "sha256:65b830219043a20ba744248c7f50f0159b76dd12d7a30385bc3c0ccc8487907f"
)
A01_RESPONSE_BODY = (
    b'{"model":"reported-model","response":"Draft \xe2\x9c\x93\\n",'
    b'"done":true,"done_reason":"stop","thinking":"ignored"}'
)
A01_RESPONSE_SHA256 = (
    "sha256:d86ec9c69622d356a1928c852a94ed47d92a0fb09911dae66c7514748ac9d232"
)
A01_ASSISTANT = b"Draft \xe2\x9c\x93\n"
A01_ASSISTANT_SHA256 = (
    "sha256:db4f81d3aa274d3de4a249fa9d092b97d35ef6cb6b0d2fe786a5f7e2ba734d9f"
)

A19_ASSISTANT = (
    b"<<<PFF-DRAFT/0.1>>>\n"
    b'{"schema":"pff-draft/0.1","atoms":[],"rules":[],'
    b'"evidence_requests":[]}\n'
    b"<<<END-PFF-DRAFT/0.1>>>"
)
A19_ASSISTANT_SHA256 = (
    "sha256:666e782bc2438cde8fb42d9594bb28e4ccefe81960d44ce7e8150f413f9f1d93"
)
A19_RESPONSE_BODY = (
    b'{"model":"reported-model","response":"<<<PFF-DRAFT/0.1>>>\\n'
    b'{\\"schema\\":\\"pff-draft/0.1\\",\\"atoms\\":[],\\"rules\\":[],'
    b'\\"evidence_requests\\":[]}\\n<<<END-PFF-DRAFT/0.1>>>",'
    b'"done":true,"done_reason":"stop"}'
)
A19_RESPONSE_SHA256 = (
    "sha256:ecb68c6cd13c4e11a74ab77cadf4426d6447b51cfb25aa2109e215688db1242f"
)

HTTP_STATUS = "ollama_http_status"
BODY_LIMIT = "ollama_response_body_limit"
RESPONSE_UTF8 = "ollama_response_utf8"
JSON_INVALID = "ollama_response_json_invalid"
DUPLICATE_KEY = "ollama_response_json_duplicate_key"
ROOT_TYPE = "ollama_response_root_type"
FIELD_MISSING = "ollama_response_field_missing"
RESPONSE_SHAPE = "ollama_response_shape"
PROVIDER_ERROR = "ollama_provider_error"
INCOMPLETE = "ollama_response_incomplete"

MODEL_SHAPE_DETAILS = ("expected=nonempty_scalar_string", "limit=4096")
RESPONSE_SHAPE_DETAILS = ("expected=scalar_string",)
DONE_SHAPE_DETAILS = ("expected=boolean",)
REASON_SHAPE_DETAILS = (
    "expected=null_or_nonempty_scalar_string",
    "limit=4096",
)
ERROR_SHAPE_DETAILS = ("expected=nonempty_scalar_string",)


# This is the normative finite fixture population.  It is deliberately not
# computed from the tables or dispatcher below.
DEFINED_IDS = frozenset(
    {
        "A01", "A02",
        "A03M01", "A03P01", "A03M02", "A03P02", "A03M03", "A03P03",
        "A03M04", "A03P04", "A03M05", "A03P05", "A03M06", "A03P06",
        "A03M07", "A03P07", "A03M08", "A03P08", "A03M09", "A03P09",
        "A03M10", "A03P10", "A03M11", "A03P11", "A03M12", "A03P12",
        "A03M13", "A03P13", "A03M14", "A03P14", "A03M15", "A03P15",
        "A04R01", "A04R02", "A04R03", "A04R04",
        "A04T01", "A04T02", "A04T03", "A04T04", "A04T05", "A04T06",
        "A04L01", "A04L02", "A04L03", "A04L04", "A04L05", "A04L06",
        "A04L07", "A04M01", "A04M02", "A04M03", "A04M04", "A04M05",
        "A04M06", "A04I01", "A04I02", "A04I03", "A04I04", "A04I05",
        "A04I06", "A04V01", "A04V02", "A04V03", "A04V04", "A04V05",
        "A04V06", "A04P01", "A04P02", "A04P03", "A04P04", "A04P05",
        "A04P06", "A05S201", "A05S429", "A05S500", "A06MAX", "A06PLUS",
        "A06UTF", "A07", "A07DUP", "A08BOM", "A08TRAIL", "A08NAN",
        "A08PINF", "A08NINF", "A08D64", "A08D65", "A08QBR", "A08SUR",
        "A08UKVSUR", "A08UNKKSUR", "A08DUP", "A08NDUP", "A08RDUP",
        "A08DUAL", "A08WS", "A08INT", "A09NULL", "A09FALSE", "A09ZERO",
        "A09STRING", "A09ARRAY", "A09MULTI", "A10PROVIDER", "A10EEMPTY",
        "A10ENULL", "A10EBOOL", "A10ENUM", "A10EARRAY", "A10EOBJECT",
        "A11AGG", "A11M00", "A11M01", "A11M02", "A11M03", "A11M04",
        "A11M05", "A11M06", "A11M07", "A11M08", "A11M09", "A11R01",
        "A11R02", "A11R03", "A11R04", "A11R05", "A11R06", "A11D00",
        "A11D01", "A11D02", "A11D03", "A11D04", "A11D05", "A11D06",
        "A11D07", "A11F01", "A11F02", "A11F03", "A11F04", "A11F05",
        "A11F06", "A11F07", "A11F08", "A11F09", "A11F10", "A11F11",
        "A11SHAPEFALSE", "A12", "A13", "A14E", "A14N", "A14S",
        "A15Q01", "A15Q02", "A15Q03", "A15Q04", "A15Q05", "A15Q06",
        "A15Q07", "A15Q08", "A15Q09", "A15Q10", "A15Q11", "A15Q12",
        "A15S01", "A15S02", "A15S03", "A15S04", "A15S05", "A15S06",
        "A15S07", "A15S08", "A15S09", "A15S10", "A15S11", "A15S12",
        "A15S13", "A15S14", "A15I01", "A15I02", "A15I03", "A15I04",
        "A15I05", "A15I06", "A15I07", "A15I08", "A15I09", "A15I10",
        "A15E01", "A15E02", "A15E03", "A15E04", "A15E05", "A15E06",
        "A15T01", "A15T02", "A16", "A17", "A18C01", "A18F01",
        "A18F02", "A18F03", "A18H01", "A18H02", "A18H03", "A18R01",
        "A18R02", "A18R03", "A19", "A20AST",
    }
)


SERIALIZER_CASES = (
    ("A03M01", "model", '"', b'"\\""'),
    ("A03P01", "prompt", '"', b'"\\""'),
    ("A03M02", "model", "\\", b'"\\\\"'),
    ("A03P02", "prompt", "\\", b'"\\\\"'),
    ("A03M03", "model", "\b", b'"\\b"'),
    ("A03P03", "prompt", "\b", b'"\\b"'),
    ("A03M04", "model", "\t", b'"\\t"'),
    ("A03P04", "prompt", "\t", b'"\\t"'),
    ("A03M05", "model", "\n", b'"\\n"'),
    ("A03P05", "prompt", "\n", b'"\\n"'),
    ("A03M06", "model", "\f", b'"\\f"'),
    ("A03P06", "prompt", "\f", b'"\\f"'),
    ("A03M07", "model", "\r", b'"\\r"'),
    ("A03P07", "prompt", "\r", b'"\\r"'),
    ("A03M08", "model", "\x00\x1f", b'"\\u0000\\u001f"'),
    ("A03P08", "prompt", "\x00\x1f", b'"\\u0000\\u001f"'),
    ("A03M09", "model", "/", b'"/"'),
    ("A03P09", "prompt", "/", b'"/"'),
    ("A03M10", "model", "\u00e9", b'"\xc3\xa9"'),
    ("A03P10", "prompt", "\u00e9", b'"\xc3\xa9"'),
    ("A03M11", "model", "\u2028", b'"\xe2\x80\xa8"'),
    ("A03P11", "prompt", "\u2028", b'"\xe2\x80\xa8"'),
    ("A03M12", "model", "\u2029", b'"\xe2\x80\xa9"'),
    ("A03P12", "prompt", "\u2029", b'"\xe2\x80\xa9"'),
    ("A03M13", "model", "\U0001f600", b'"\xf0\x9f\x98\x80"'),
    ("A03P13", "prompt", "\U0001f600", b'"\xf0\x9f\x98\x80"'),
    ("A03M14", "model", "\r\n", b'"\\r\\n"'),
    ("A03P14", "prompt", "\r\n", b'"\\r\\n"'),
    ("A03M15", "model", "e\u0301", b'"e\xcc\x81"'),
    ("A03P15", "prompt", "e\u0301", b'"e\xcc\x81"'),
)


REQUEST_CASE_IDS = (
    "A04R01", "A04R02", "A04R03", "A04R04",
    "A04T01", "A04T02", "A04T03", "A04T04", "A04T05", "A04T06",
    "A04L01", "A04L02", "A04L03", "A04L04", "A04L05", "A04L06",
    "A04L07", "A04M01", "A04M02", "A04M03", "A04M04", "A04M05",
    "A04M06", "A04I01", "A04I02", "A04I03", "A04I04", "A04I05",
    "A04I06", "A04V01", "A04V02", "A04V03", "A04V04", "A04V05",
    "A04V06", "A04P01", "A04P02", "A04P03", "A04P04", "A04P05",
    "A04P06", "A18C01",
)

RESPONSE_CASE_IDS = (
    "A05S201", "A05S429", "A05S500", "A06MAX", "A06PLUS", "A06UTF",
    "A07", "A07DUP", "A08BOM", "A08TRAIL", "A08NAN", "A08PINF",
    "A08NINF", "A08D64", "A08D65", "A08QBR", "A08SUR", "A08UKVSUR",
    "A08UNKKSUR", "A08DUP", "A08NDUP", "A08RDUP", "A08DUAL", "A08WS",
    "A08INT", "A09NULL", "A09FALSE", "A09ZERO", "A09STRING", "A09ARRAY",
    "A09MULTI", "A10PROVIDER", "A10EEMPTY", "A10ENULL", "A10EBOOL",
    "A10ENUM", "A10EARRAY", "A10EOBJECT", "A11AGG", "A11M00", "A11M01",
    "A11M02", "A11M03", "A11M04", "A11M05", "A11M06", "A11M07",
    "A11M08", "A11M09", "A11R01", "A11R02", "A11R03", "A11R04",
    "A11R05", "A11R06", "A11D00", "A11D01", "A11D02", "A11D03",
    "A11D04", "A11D05", "A11D06", "A11D07", "A11F01", "A11F02",
    "A11F03", "A11F04", "A11F05", "A11F06", "A11F07", "A11F08",
    "A11F09", "A11F10", "A11F11", "A11SHAPEFALSE", "A12",
)

BOUNDARY_CASE_IDS = (
    "A13", "A14E", "A14N", "A14S",
    "A15Q01", "A15Q02", "A15Q03", "A15Q04", "A15Q05", "A15Q06",
    "A15Q07", "A15Q08", "A15Q09", "A15Q10", "A15Q11", "A15Q12",
    "A15S01", "A15S02", "A15S03", "A15S04", "A15S05", "A15S06",
    "A15S07", "A15S08", "A15S09", "A15S10", "A15S11", "A15S12",
    "A15S13", "A15S14", "A15I01", "A15I02", "A15I03", "A15I04",
    "A15I05", "A15I06", "A15I07", "A15I08", "A15I09", "A15I10",
    "A15E01", "A15E02", "A15E03", "A15E04", "A15E05", "A15E06",
    "A15T01", "A15T02", "A16", "A17", "A18F01", "A18F02", "A18F03",
    "A18H01", "A18H02", "A18H03", "A18R01", "A18R02", "A18R03",
    "A19", "A20AST",
)


MUTATION_TARGETS = {
    "M01": ("A01", "provider_id"),
    "M02": ("A01", "public_parameters"),
    "M03": ("A01", "adapter_id"),
    "M04": ("A01", "request_body"),
    "M05": ("A03M10", "request_token"),
    "M06": ("A03P09", "request_token"),
    "M07": ("A03P15", "request_token"),
    "M08": ("A04R01", "exact_request_type"),
    "M09": ("A18C01", "invocation_revalidation"),
    "M10": ("A04P05", "oversized_prompt_exact_bytes"),
    "M11": ("A04L05", "lineage"),
    "M12": ("A13", "one_send"),
    "M13": ("A05S201", "zero_capture"),
    "M14": ("A15S08", "returned_status_exact_type"),
    "M15": ("A05S500", "status_precedence"),
    "M16": ("A06PLUS", "body_limit_lower_boundary"),
    "M17": ("A07", "strict_utf8"),
    "M18": ("A07DUP", "utf8_precedence"),
    "M19": ("A08NAN", "nonfinite_json"),
    "M20": ("A08QBR", "quoted_depth"),
    "M21": ("A08INT", "opaque_integer_token"),
    "M22": ("A08UKVSUR", "unknown_value_scalar_walk"),
    "M23": ("A08NDUP", "nested_duplicate_walk"),
    "M24": ("A08RDUP", "single_duplicate_issue"),
    "M25": ("A08DUAL", "scalar_before_duplicate"),
    "M26": ("A09ZERO", "root_exact_type"),
    "M27": ("A10PROVIDER", "provider_branch_precedence"),
    "M28": ("A11SHAPEFALSE", "shape_before_incomplete"),
    "M29": ("A04M06", "request_utf8_byte_limit"),
    "M30": ("A12", "model_mismatch_allowed"),
    "M31": ("A01", "assistant_only_capture"),
    "M32": ("A14E", "exception_identity"),
    "M33": ("A14S", "response_exact_type"),
    "M34": ("A15E01", "issue_deduplication"),
    "M35": ("A15I08", "pointer_escape_validation"),
    "M36": ("A18R01", "request_repr_redaction"),
    "M37": ("A20AST", "import_allowlist"),
    "M38": ("A17", "extract_runtime_trap"),
    "M39": ("A01", "exact_envelope_return"),
    "M40": ("A15S10", "returned_body_exact_type"),
    "M41": ("A01", "stream_member"),
    "M42": ("A01", "adapter_version"),
    "M43": ("A20AST", "no_pff_import"),
    "M44": ("A20AST", "no_ground_import"),
    "M45": ("A20AST", "no_network_import"),
    "M46": ("A17", "one_send"),
    "M47": ("A08UNKKSUR", "unknown_key_scalar_walk"),
    "M48": ("A15S09", "returned_status_range"),
    "M49": ("A15E01", "issue_sort"),
    "M50": ("A06UTF", "limit_before_utf8"),
    "M51": ("A06MAX", "body_limit_upper_boundary"),
    "M52": ("A11M09", "response_model_utf8_limit"),
    "M53": ("A11F11", "done_reason_utf8_limit"),
    "M54": ("A05S429", "one_send"),
    "M55": ("A05S201", "exact_200"),
    "M56": ("A10PROVIDER", "provider_text_absent"),
}

MUTATION_IDS = frozenset(
    {
        "M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08",
        "M09", "M10", "M11", "M12", "M13", "M14", "M15", "M16",
        "M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24",
        "M25", "M26", "M27", "M28", "M29", "M30", "M31", "M32",
        "M33", "M34", "M35", "M36", "M37", "M38", "M39", "M40",
        "M41", "M42", "M43", "M44", "M45", "M46", "M47", "M48",
        "M49", "M50", "M51", "M52", "M53", "M54", "M55", "M56",
    }
)


class TextSubclass(str):
    pass


class BytesSubclass(bytes):
    pass


class IntSubclass(int):
    pass


class RequestSubclass(OllamaGenerateRequest):
    pass


class ResponseSubclass(OllamaTransportResponse):
    pass


class AttemptSubclass(AttemptRef):
    pass


class IssueSubclass(OllamaAdapterIssue):
    pass


class TupleSubclass(tuple):
    pass


class DuckRequest:
    __slots__ = (
        "endpoint",
        "attempt",
        "relation",
        "parent",
        "model",
        "prompt_template_id",
        "prompt_template_version",
        "prompt",
    )

    def __init__(self, values: dict[str, object]) -> None:
        for name in self.__slots__:
            setattr(self, name, values[name])


class FakeTransport:
    def __init__(self, result: object) -> None:
        self.result = result
        self.requests: list[object] = []
        self.disabled = False

    def __call__(self, request: object) -> object:
        self.requests.append(request)
        if self.disabled:
            raise AssertionError("transport called after it was disabled")
        return self.result


class RaisingTransport:
    def __init__(self, error: BaseException) -> None:
        self.error = error
        self.requests: list[object] = []

    def __call__(self, request: object) -> object:
        self.requests.append(request)
        raise self.error


def sha256_text(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def issue_projection(error: OllamaAdapterError) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (issue.code.value, issue.path, issue.details)
        for issue in error.issues
    )


def dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        if prefix is not None:
            return prefix + "." + node.attr
    return None


class OllamaAdapterConformanceTests(unittest.TestCase):
    maxDiff = None

    def request_values(self, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "endpoint": OllamaEndpoint.LOCAL,
            "attempt": AttemptRef("session:ollama", 1),
            "relation": AttemptRelation.INITIAL,
            "parent": None,
            "model": "test-model",
            "prompt_template_id": "pff-draft-prompt",
            "prompt_template_version": "1",
            "prompt": A01_PROMPT,
        }
        values.update(overrides)
        return values

    def request(self, **overrides: object) -> OllamaGenerateRequest:
        return OllamaGenerateRequest(**self.request_values(**overrides))

    def invoke(
        self,
        *,
        request: object | None = None,
        response: object | None = None,
        transport: object | None = None,
    ) -> tuple[object | None, BaseException | None, object, int]:
        if request is None:
            request = self.request()
        if transport is None:
            if response is None:
                response = OllamaTransportResponse(200, A01_RESPONSE_BODY)
            transport = FakeTransport(response)
        result: object | None = None
        error: BaseException | None = None
        with patch.object(
            ollama_module,
            "capture_generation",
            wraps=ollama_module.capture_generation,
        ) as capture_spy:
            try:
                result = generate_ollama(request, transport=transport)  # type: ignore[arg-type]
            except BaseException as caught:
                error = caught
            capture_calls = capture_spy.call_count
        return result, error, transport, capture_calls

    def assert_exact_raises(
        self,
        expected_type: type[BaseException],
        operation: object,
    ) -> BaseException:
        try:
            operation()  # type: ignore[operator]
        except BaseException as error:
            self.assertIs(type(error), expected_type)
            return error
        self.fail(f"{expected_type.__name__} was not raised")

    def assert_request_constructor_error(
        self,
        expected_type: type[BaseException],
        **overrides: object,
    ) -> BaseException:
        transport = FakeTransport(OllamaTransportResponse(200, A01_RESPONSE_BODY))
        with patch.object(
            ollama_module,
            "capture_generation",
            wraps=ollama_module.capture_generation,
        ) as capture_spy:
            error = self.assert_exact_raises(
                expected_type,
                lambda: OllamaGenerateRequest(**self.request_values(**overrides)),
            )
        self.assertEqual(transport.requests, [])
        self.assertEqual(capture_spy.call_count, 0)
        return error

    def assert_failure(
        self,
        *,
        expected_issues: tuple[tuple[object, ...], ...],
        status: int = 200,
        body: bytes = A01_RESPONSE_BODY,
        request: OllamaGenerateRequest | None = None,
    ) -> OllamaAdapterError:
        response = OllamaTransportResponse(status, body)
        result, error, transport, capture_calls = self.invoke(
            request=request,
            response=response,
        )
        self.assertIsNone(result)
        self.assertIs(type(error), OllamaAdapterError)
        adapter_error = error
        assert isinstance(adapter_error, OllamaAdapterError)
        self.assertEqual(issue_projection(adapter_error), expected_issues)
        self.assertEqual(len(transport.requests), 1)  # type: ignore[attr-defined]
        self.assertEqual(capture_calls, 0)
        return adapter_error

    def assert_success(
        self,
        *,
        body: bytes = A01_RESPONSE_BODY,
        request: OllamaGenerateRequest | None = None,
        expected_request_body: bytes = A01_REQUEST_BODY,
        expected_provider: str = "ollama-local",
        expected_reported_model: str = "reported-model",
        expected_assistant: bytes = A01_ASSISTANT,
        expected_reason: str | None = "stop",
    ) -> tuple[GenerationEnvelope, FakeTransport]:
        if request is None:
            request = self.request()
        result, error, transport, capture_calls = self.invoke(
            request=request,
            response=OllamaTransportResponse(200, body),
        )
        self.assertIsNone(error)
        self.assertIs(type(result), GenerationEnvelope)
        envelope = result
        assert isinstance(envelope, GenerationEnvelope)
        self.assertEqual(len(transport.requests), 1)  # type: ignore[attr-defined]
        sent = transport.requests[0]  # type: ignore[attr-defined]
        self.assertIs(type(sent), OllamaTransportRequest)
        self.assertEqual(sent.method, "POST")
        self.assertEqual(sent.url, request.endpoint.value)
        self.assertEqual(sent.content_type, "application/json")
        self.assertEqual(sent.body, expected_request_body)
        self.assertEqual(capture_calls, 1)
        self.assertEqual(envelope.profile, "pff-generation/0.1")
        self.assertEqual(envelope.attempt, request.attempt)
        self.assertIs(envelope.relation, request.relation)
        self.assertEqual(envelope.parent, request.parent)
        self.assertEqual(envelope.provider_id, expected_provider)
        self.assertEqual(envelope.adapter_id, "ollama-generate")
        self.assertEqual(envelope.adapter_version, "1")
        self.assertEqual(envelope.requested_model, request.model)
        self.assertEqual(envelope.reported_model, expected_reported_model)
        self.assertEqual(envelope.prompt_template_id, request.prompt_template_id)
        self.assertEqual(
            envelope.prompt_template_version,
            request.prompt_template_version,
        )
        self.assertEqual(envelope.prompt.data, request.prompt)
        self.assertEqual(envelope.prompt.sha256, sha256_text(request.prompt))
        self.assertEqual(
            tuple((item.name, item.value) for item in envelope.public_parameters),
            (("stream", "false"),),
        )
        self.assertEqual(envelope.raw_response.data, expected_assistant)
        self.assertEqual(envelope.raw_response.sha256, sha256_text(expected_assistant))
        self.assertEqual(envelope.finish_reason, expected_reason)
        self.assertIsNone(envelope.provider_request_id)
        return envelope, transport  # type: ignore[return-value]

    def case_a01(self) -> None:
        self.assertEqual(OllamaEndpoint.LOCAL.value, "http://localhost:11434/api/generate")
        self.assertEqual(OllamaEndpoint.CLOUD.value, "https://ollama.com/api/generate")
        self.assertEqual(len(A01_PROMPT), 16)
        self.assertEqual(sha256_text(A01_PROMPT), A01_PROMPT_SHA256)
        self.assertEqual(len(A01_REQUEST_BODY), 68)
        self.assertEqual(sha256_text(A01_REQUEST_BODY), A01_REQUEST_SHA256)
        self.assertEqual(len(A01_RESPONSE_BODY), 105)
        self.assertEqual(sha256_text(A01_RESPONSE_BODY), A01_RESPONSE_SHA256)
        self.assertEqual(len(A01_ASSISTANT), 10)
        self.assertEqual(sha256_text(A01_ASSISTANT), A01_ASSISTANT_SHA256)
        envelope, transport = self.assert_success()
        self.assertEqual(envelope.prompt.sha256, A01_PROMPT_SHA256)
        self.assertEqual(envelope.raw_response.sha256, A01_ASSISTANT_SHA256)
        self.assertNotEqual(envelope.raw_response.data, A01_RESPONSE_BODY)
        self.assertFalse(hasattr(envelope, "thinking"))
        self.assertEqual(transport.requests[0].body, A01_REQUEST_BODY)

    def case_a02(self) -> None:
        request = self.request(endpoint=OllamaEndpoint.CLOUD)
        envelope, transport = self.assert_success(
            request=request,
            expected_provider="ollama-cloud",
        )
        self.assertEqual(
            transport.requests[0].url,
            "https://ollama.com/api/generate",
        )
        self.assertEqual(
            tuple((item.name, item.value) for item in envelope.public_parameters),
            (("stream", "false"),),
        )

    def case_serializer(self, row: tuple[object, ...]) -> None:
        fixture_id, field, scalar, token = row
        self.assertIs(type(fixture_id), str)
        self.assertIs(type(scalar), str)
        self.assertIs(type(token), bytes)
        if field == "model":
            request = self.request(model=scalar, prompt=b"")
            expected = (
                b'{"model":' + token + b',"prompt":"","stream":false}'
            )
        else:
            request = self.request(model="m", prompt=scalar.encode("utf-8"))
            expected = (
                b'{"model":"m","prompt":' + token + b',"stream":false}'
            )
        self.assertNotEqual(expected[-1:], b"\n")
        self.assert_success(request=request, expected_request_body=expected)

    def case_request(self, fixture_id: str) -> None:
        session = "session:ollama"
        a1 = AttemptRef(session, 1)
        a2 = AttemptRef(session, 2)
        unicode_limit = "\u00e9" * 2_048

        if fixture_id == "A04R01":
            request = RequestSubclass(**self.request_values())
            result, error, transport, captures = self.invoke(request=request)
            self.assertIsNone(result)
            self.assertIs(type(error), TypeError)
            self.assertEqual(transport.requests, [])
            self.assertEqual(captures, 0)
            return
        if fixture_id == "A04R02":
            request = self.request_values()
            result, error, transport, captures = self.invoke(request=request)
            self.assertIsNone(result)
            self.assertIs(type(error), TypeError)
            self.assertEqual(transport.requests, [])
            self.assertEqual(captures, 0)
            return
        if fixture_id == "A04R03":
            request = DuckRequest(self.request_values())
            result, error, transport, captures = self.invoke(request=request)
            self.assertIsNone(result)
            self.assertIs(type(error), TypeError)
            self.assertEqual(transport.requests, [])
            self.assertEqual(captures, 0)
            return
        if fixture_id == "A04R04":
            result, error, _transport, captures = self.invoke(
                request=self.request(),
                transport=object(),
            )
            self.assertIsNone(result)
            self.assertIs(type(error), TypeError)
            self.assertEqual(captures, 0)
            return

        constructor_failures: dict[str, tuple[type[BaseException], dict[str, object]]] = {
            "A04T01": (TypeError, {"endpoint": OllamaEndpoint.LOCAL.value}),
            "A04T02": (TypeError, {"attempt": object()}),
            "A04T03": (TypeError, {"relation": "initial"}),
            "A04T04": (TypeError, {"parent": object()}),
            "A04T05": (TypeError, {"attempt": AttemptSubclass(session, 1)}),
            "A04T06": (
                TypeError,
                {
                    "attempt": a2,
                    "relation": AttemptRelation.RETRY,
                    "parent": AttemptSubclass(session, 1),
                },
            ),
            "A04L01": (ValueError, {"parent": a1}),
            "A04L02": (ValueError, {"relation": AttemptRelation.RETRY}),
            "A04L03": (
                ValueError,
                {
                    "attempt": a2,
                    "relation": AttemptRelation.RETRY,
                    "parent": AttemptRef("other", 1),
                },
            ),
            "A04L04": (
                ValueError,
                {
                    "attempt": a2,
                    "relation": AttemptRelation.RETRY,
                    "parent": AttemptRef(session, 2),
                },
            ),
            "A04M01": (ValueError, {"model": ""}),
            "A04M02": (TypeError, {"model": 1}),
            "A04M03": (TypeError, {"model": TextSubclass("m")}),
            "A04M04": (ValueError, {"model": "\ud800"}),
            "A04M06": (ValueError, {"model": unicode_limit + "a"}),
            "A04I01": (ValueError, {"prompt_template_id": ""}),
            "A04I02": (TypeError, {"prompt_template_id": 1}),
            "A04I03": (
                TypeError,
                {"prompt_template_id": TextSubclass("pff-draft-prompt")},
            ),
            "A04I04": (ValueError, {"prompt_template_id": "\ud800"}),
            "A04I06": (
                ValueError,
                {"prompt_template_id": unicode_limit + "a"},
            ),
            "A04V01": (ValueError, {"prompt_template_version": ""}),
            "A04V02": (TypeError, {"prompt_template_version": 1}),
            "A04V03": (
                TypeError,
                {"prompt_template_version": TextSubclass("1")},
            ),
            "A04V04": (ValueError, {"prompt_template_version": "\ud800"}),
            "A04V06": (
                ValueError,
                {"prompt_template_version": unicode_limit + "a"},
            ),
            "A04P01": (TypeError, {"prompt": bytearray()}),
            "A04P02": (ValueError, {"prompt": b"\xff"}),
            "A04P06": (TypeError, {"prompt": BytesSubclass(b"p")}),
        }
        if fixture_id in constructor_failures:
            expected_type, overrides = constructor_failures[fixture_id]
            error = self.assert_request_constructor_error(expected_type, **overrides)
            if fixture_id == "A04P02":
                self.assertIsNone(error.__cause__)
                self.assertTrue(error.__suppress_context__)
            return

        if fixture_id in {"A04L05", "A04L06", "A04L07"}:
            relation = {
                "A04L05": AttemptRelation.RETRY,
                "A04L06": AttemptRelation.REPAIR,
                "A04L07": AttemptRelation.EXTRACT,
            }[fixture_id]
            request = self.request(attempt=a2, relation=relation, parent=a1)
            envelope, _transport = self.assert_success(request=request)
            self.assertEqual(envelope.attempt, a2)
            self.assertIs(envelope.relation, relation)
            self.assertEqual(envelope.parent, a1)
            return

        if fixture_id == "A04M05":
            request = self.request(model=unicode_limit)
            expected = (
                b'{"model":"'
                + b"\xc3\xa9" * 2_048
                + b'","prompt":"Return \\"caf\xc3\xa9\\".\\n","stream":false}'
            )
            envelope, _transport = self.assert_success(
                request=request,
                expected_request_body=expected,
            )
            self.assertEqual(envelope.requested_model, unicode_limit)
            return
        if fixture_id == "A04I05":
            request = self.request(prompt_template_id=unicode_limit)
            envelope, _transport = self.assert_success(request=request)
            self.assertEqual(envelope.prompt_template_id, unicode_limit)
            return
        if fixture_id == "A04V05":
            request = self.request(prompt_template_version=unicode_limit)
            envelope, _transport = self.assert_success(request=request)
            self.assertEqual(envelope.prompt_template_version, unicode_limit)
            return
        if fixture_id == "A04P03":
            request = self.request(prompt=b"")
            expected = b'{"model":"test-model","prompt":"","stream":false}'
            envelope, _transport = self.assert_success(
                request=request,
                expected_request_body=expected,
            )
            self.assertEqual(envelope.prompt.data, b"")
            return
        if fixture_id == "A04P04":
            request = self.request(prompt=b"\xef\xbb\xbf")
            expected = (
                b'{"model":"test-model","prompt":"\xef\xbb\xbf","stream":false}'
            )
            envelope, _transport = self.assert_success(
                request=request,
                expected_request_body=expected,
            )
            self.assertEqual(envelope.prompt.data, b"\xef\xbb\xbf")
            return
        if fixture_id == "A04P05":
            prompt = b"p" * 1_048_577
            request = self.request(prompt=prompt)
            expected = (
                b'{"model":"test-model","prompt":"'
                + b"p" * 1_048_577
                + b'","stream":false}'
            )
            envelope, transport = self.assert_success(
                request=request,
                expected_request_body=expected,
            )
            self.assertEqual(envelope.prompt.data, prompt)
            self.assertEqual(transport.requests[0].body, expected)
            return
        if fixture_id == "A18C01":
            request = self.request()
            object.__setattr__(request, "model", "")
            result, error, transport, captures = self.invoke(request=request)
            self.assertIsNone(result)
            self.assertIs(type(error), ValueError)
            self.assertEqual(transport.requests, [])
            self.assertEqual(captures, 0)
            return
        self.fail(f"request fixture not implemented: {fixture_id}")

    def case_response(self, fixture_id: str) -> None:
        json_prefix = b'{"model":"m","response":"","done":true,"x":'

        failure_rows: dict[str, tuple[int, bytes, tuple[tuple[object, ...], ...]]] = {
            "A05S201": (
                201,
                A01_RESPONSE_BODY,
                ((HTTP_STATUS, "/status", ("status=201",)),),
            ),
            "A05S429": (
                429,
                A01_RESPONSE_BODY,
                ((HTTP_STATUS, "/status", ("status=429",)),),
            ),
            "A05S500": (
                500,
                A01_RESPONSE_BODY + b" " * 4_194_200,
                ((HTTP_STATUS, "/status", ("status=500",)),),
            ),
            "A06PLUS": (
                200,
                A01_RESPONSE_BODY + b" " * 4_194_200,
                (
                    (
                        BODY_LIMIT,
                        "/body",
                        (
                            "resource=response_body_bytes",
                            "actual=4194305",
                            "limit=4194304",
                        ),
                    ),
                ),
            ),
            "A06UTF": (
                200,
                b"\xff" + b"x" * 4_194_304,
                (
                    (
                        BODY_LIMIT,
                        "/body",
                        (
                            "resource=response_body_bytes",
                            "actual=4194305",
                            "limit=4194304",
                        ),
                    ),
                ),
            ),
            "A07": (200, b"\xff", ((RESPONSE_UTF8, "/body", ()),)),
            "A07DUP": (
                200,
                b'\xff{"model":"m","model":"n"}',
                ((RESPONSE_UTF8, "/body", ()),),
            ),
            "A08BOM": (
                200,
                b"\xef\xbb\xbf" + A01_RESPONSE_BODY,
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08TRAIL": (
                200,
                A01_RESPONSE_BODY + b"{}",
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08NAN": (
                200,
                json_prefix + b"NaN}",
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08PINF": (
                200,
                json_prefix + b"Infinity}",
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08NINF": (
                200,
                json_prefix + b"-Infinity}",
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08D65": (
                200,
                json_prefix + b"[" * 64 + b"0" + b"]" * 64 + b"}",
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08SUR": (
                200,
                b'{"model":"m","response":"\\ud800","done":true}',
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08UKVSUR": (
                200,
                b'{"model":"m","response":"","done":true,"x":"\\ud800"}',
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08UNKKSUR": (
                200,
                b'{"model":"m","response":"","done":true,"\\ud800":0}',
                ((JSON_INVALID, "/body", ()),),
            ),
            "A08DUP": (
                200,
                b'{"model":"m","model":"n","response":"","done":true}',
                ((DUPLICATE_KEY, "/body", ()),),
            ),
            "A08NDUP": (
                200,
                b'{"model":"m","response":"","done":true,'
                b'"x":{"k":1,"k":2}}',
                ((DUPLICATE_KEY, "/body", ()),),
            ),
            "A08RDUP": (
                200,
                b'{"model":"m","model":"n","response":"","done":true,'
                b'"x":{"k":1,"k":2}}',
                ((DUPLICATE_KEY, "/body", ()),),
            ),
            "A08DUAL": (
                200,
                b'{"model":"m","model":"n","response":"\\ud800",'
                b'"done":true}',
                ((JSON_INVALID, "/body", ()),),
            ),
            "A09NULL": (200, b"null", ((ROOT_TYPE, "/body", ()),)),
            "A09FALSE": (200, b"false", ((ROOT_TYPE, "/body", ()),)),
            "A09ZERO": (200, b"0", ((ROOT_TYPE, "/body", ()),)),
            "A09STRING": (200, b'""', ((ROOT_TYPE, "/body", ()),)),
            "A09ARRAY": (200, b"[]", ((ROOT_TYPE, "/body", ()),)),
            "A09MULTI": (
                200,
                b'{"model":"m","model":"n","response":"",'
                b'"response":"x","done":true}',
                ((DUPLICATE_KEY, "/body", ()),),
            ),
            "A10PROVIDER": (
                200,
                b'{"error":"provider failed","done":0}',
                ((PROVIDER_ERROR, "/body/error", ()),),
            ),
            "A10EEMPTY": (
                200,
                b'{"error":""}',
                ((RESPONSE_SHAPE, "/body/error", ERROR_SHAPE_DETAILS),),
            ),
            "A10ENULL": (
                200,
                b'{"error":null}',
                ((RESPONSE_SHAPE, "/body/error", ERROR_SHAPE_DETAILS),),
            ),
            "A10EBOOL": (
                200,
                b'{"error":false}',
                ((RESPONSE_SHAPE, "/body/error", ERROR_SHAPE_DETAILS),),
            ),
            "A10ENUM": (
                200,
                b'{"error":0}',
                ((RESPONSE_SHAPE, "/body/error", ERROR_SHAPE_DETAILS),),
            ),
            "A10EARRAY": (
                200,
                b'{"error":[]}',
                ((RESPONSE_SHAPE, "/body/error", ERROR_SHAPE_DETAILS),),
            ),
            "A10EOBJECT": (
                200,
                b'{"error":{}}',
                ((RESPONSE_SHAPE, "/body/error", ERROR_SHAPE_DETAILS),),
            ),
            "A11AGG": (
                200,
                b'{"done":0,"done_reason":""}',
                (
                    (RESPONSE_SHAPE, "/body/done", DONE_SHAPE_DETAILS),
                    (RESPONSE_SHAPE, "/body/done_reason", REASON_SHAPE_DETAILS),
                    (FIELD_MISSING, "/body/model", ()),
                    (FIELD_MISSING, "/body/response", ()),
                ),
            ),
            "A11SHAPEFALSE": (
                200,
                b'{"model":0,"response":"","done":false}',
                ((RESPONSE_SHAPE, "/body/model", MODEL_SHAPE_DETAILS),),
            ),
        }
        if fixture_id in failure_rows:
            status, body, expected = failure_rows[fixture_id]
            if fixture_id == "A05S500":
                self.assertEqual(len(body), 4_194_305)
            if fixture_id == "A06PLUS" or fixture_id == "A06UTF":
                self.assertEqual(len(body), 4_194_305)
            if fixture_id == "A11AGG":
                self.assertEqual(
                    sha256_text(body),
                    "sha256:a14cc5a4f95859b97755c7486c909de56a592e92a09ac9976da47f2f514bc768",
                )
            error = self.assert_failure(
                expected_issues=expected,
                status=status,
                body=body,
            )
            if fixture_id == "A10PROVIDER":
                self.assertNotIn("provider failed", str(error))
                self.assertNotIn("provider failed", repr(error))
                self.assertNotIn("provider failed", repr(error.issues))
            if fixture_id in {"A07", "A08NAN"}:
                self.assertIsNone(error.__cause__)
                self.assertTrue(error.__suppress_context__)
            return

        if fixture_id == "A06MAX":
            body = A01_RESPONSE_BODY + b" " * 4_194_199
            self.assertEqual(len(body), 4_194_304)
            self.assert_success(body=body)
            return
        if fixture_id == "A08D64":
            body = json_prefix + b"[" * 63 + b"0" + b"]" * 63 + b"}"
            self.assert_success(
                body=body,
                expected_reported_model="m",
                expected_assistant=b"",
                expected_reason=None,
            )
            return
        if fixture_id == "A08QBR":
            body = json_prefix + b'"' + b"[" * 65 + b'"}'
            self.assert_success(
                body=body,
                expected_reported_model="m",
                expected_assistant=b"",
                expected_reason=None,
            )
            return
        if fixture_id == "A08WS":
            self.assert_success(body=b" \t\r\n" + A01_RESPONSE_BODY + b"\n\r\t ")
            return
        if fixture_id == "A08INT":
            body = json_prefix + b"7" * 5_000 + b"}"
            saved = sys.get_int_max_str_digits()
            sys.set_int_max_str_digits(4_300)
            try:
                self.assert_success(
                    body=body,
                    expected_reported_model="m",
                    expected_assistant=b"",
                    expected_reason=None,
                )
            finally:
                sys.set_int_max_str_digits(saved)
            return

        if fixture_id.startswith("A11M"):
            model_tokens = {
                "A11M00": b'""',
                "A11M01": b"null",
                "A11M02": b"false",
                "A11M03": b"0",
                "A11M04": b"[]",
                "A11M05": b"{}",
                "A11M06": b'"' + b"m" * 4_096 + b'"',
                "A11M07": b'"' + b"m" * 4_097 + b'"',
                "A11M08": b'"' + b"\xc3\xa9" * 2_048 + b'"',
                "A11M09": b'"' + b"\xc3\xa9" * 2_048 + b'a"',
            }
            token = model_tokens[fixture_id]
            body = b'{"model":' + token + b',"response":"x","done":true}'
            if fixture_id == "A11M06":
                self.assert_success(
                    body=body,
                    expected_reported_model="m" * 4_096,
                    expected_assistant=b"x",
                    expected_reason=None,
                )
            elif fixture_id == "A11M08":
                self.assert_success(
                    body=body,
                    expected_reported_model="\u00e9" * 2_048,
                    expected_assistant=b"x",
                    expected_reason=None,
                )
            else:
                self.assert_failure(
                    expected_issues=(
                        (RESPONSE_SHAPE, "/body/model", MODEL_SHAPE_DETAILS),
                    ),
                    body=body,
                )
            return

        if fixture_id.startswith("A11R"):
            response_tokens = {
                "A11R01": b"null",
                "A11R02": b"false",
                "A11R03": b"0",
                "A11R04": b"[]",
                "A11R05": b"{}",
                "A11R06": b'""',
            }
            token = response_tokens[fixture_id]
            body = b'{"model":"m","response":' + token + b',"done":true}'
            if fixture_id == "A11R06":
                self.assert_success(
                    body=body,
                    expected_reported_model="m",
                    expected_assistant=b"",
                    expected_reason=None,
                )
            else:
                self.assert_failure(
                    expected_issues=(
                        (RESPONSE_SHAPE, "/body/response", RESPONSE_SHAPE_DETAILS),
                    ),
                    body=body,
                )
            return

        if fixture_id.startswith("A11D"):
            done_tokens = {
                "A11D00": None,
                "A11D01": b"null",
                "A11D02": b"0",
                "A11D03": b"1",
                "A11D04": b'"true"',
                "A11D05": b"[]",
                "A11D06": b"{}",
                "A11D07": b"false",
            }
            token = done_tokens[fixture_id]
            if token is None:
                body = b'{"model":"m","response":"x"}'
                expected = ((FIELD_MISSING, "/body/done", ()),)
            else:
                body = b'{"model":"m","response":"x","done":' + token + b"}"
                if fixture_id == "A11D07":
                    expected = ((INCOMPLETE, "/body/done", ()),)
                else:
                    expected = (
                        (RESPONSE_SHAPE, "/body/done", DONE_SHAPE_DETAILS),
                    )
            self.assert_failure(expected_issues=expected, body=body)
            return

        if fixture_id.startswith("A11F"):
            reason_tokens: dict[str, bytes | None] = {
                "A11F01": None,
                "A11F02": b"null",
                "A11F03": b'""',
                "A11F04": b"false",
                "A11F05": b"0",
                "A11F06": b"[]",
                "A11F07": b"{}",
                "A11F08": b'"' + b"r" * 4_096 + b'"',
                "A11F09": b'"' + b"r" * 4_097 + b'"',
                "A11F10": b'"' + b"\xc3\xa9" * 2_048 + b'"',
                "A11F11": b'"' + b"\xc3\xa9" * 2_048 + b'a"',
            }
            token = reason_tokens[fixture_id]
            base = b'{"model":"m","response":"x","done":true'
            body = base + (b"}" if token is None else b',"done_reason":' + token + b"}")
            success_reasons = {
                "A11F01": None,
                "A11F02": None,
                "A11F08": "r" * 4_096,
                "A11F10": "\u00e9" * 2_048,
            }
            if fixture_id in success_reasons:
                self.assert_success(
                    body=body,
                    expected_reported_model="m",
                    expected_assistant=b"x",
                    expected_reason=success_reasons[fixture_id],
                )
            else:
                self.assert_failure(
                    expected_issues=(
                        (
                            RESPONSE_SHAPE,
                            "/body/done_reason",
                            REASON_SHAPE_DETAILS,
                        ),
                    ),
                    body=body,
                )
            return

        if fixture_id == "A12":
            body = (
                b'{"model":"reported-model","response":"x","done":true,'
                b'"z_scalar":7,"z_object":{"k":"v"},'
                b'"z_array":[null,false]}'
            )
            envelope, _transport = self.assert_success(
                body=body,
                expected_reported_model="reported-model",
                expected_assistant=b"x",
                expected_reason=None,
            )
            self.assertEqual(envelope.requested_model, "test-model")
            self.assertEqual(envelope.reported_model, "reported-model")
            self.assertFalse(hasattr(envelope, "z_scalar"))
            self.assertFalse(hasattr(envelope, "z_object"))
            self.assertFalse(hasattr(envelope, "z_array"))
            return
        self.fail(f"response fixture not implemented: {fixture_id}")

    def case_boundary(self, fixture_id: str) -> None:
        if fixture_id == "A13":
            sentinel = OllamaTransportError()
            transport = RaisingTransport(sentinel)
            result, error, _transport, captures = self.invoke(transport=transport)
            self.assertIsNone(result)
            self.assertIs(error, sentinel)
            self.assertEqual(str(error), "Ollama transport failed")
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 0)
            return
        if fixture_id == "A14E":
            sentinel = RuntimeError("sentinel transport exception")
            transport = RaisingTransport(sentinel)
            result, error, _transport, captures = self.invoke(transport=transport)
            self.assertIsNone(result)
            self.assertIs(error, sentinel)
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 0)
            return
        if fixture_id == "A14N":
            transport = FakeTransport(None)
            result, error, _transport, captures = self.invoke(transport=transport)
            self.assertIsNone(result)
            self.assertIs(type(error), TypeError)
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 0)
            return
        if fixture_id == "A14S":
            transport = FakeTransport(ResponseSubclass(200, A01_RESPONSE_BODY))
            result, error, _transport, captures = self.invoke(transport=transport)
            self.assertIsNone(result)
            self.assertIs(type(error), TypeError)
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 0)
            return

        if fixture_id.startswith("A15Q"):
            valid = (
                "POST",
                OllamaEndpoint.LOCAL.value,
                "application/json",
                b"{}",
            )
            if fixture_id == "A15Q01":
                record = OllamaTransportRequest(*valid)
                self.assertEqual(
                    (record.method, record.url, record.content_type, record.body),
                    valid,
                )
                self.assertNotIn("{}", repr(record))
                self.assert_exact_raises(TypeError, lambda: hash(record))
                self.assert_exact_raises(
                    FrozenInstanceError,
                    lambda: setattr(record, "method", "GET"),
                )
                return
            bad_values: dict[str, tuple[type[BaseException], tuple[object, ...]]] = {
                "A15Q02": (TypeError, (1, valid[1], valid[2], valid[3])),
                "A15Q03": (TypeError, (valid[0], 1, valid[2], valid[3])),
                "A15Q04": (TypeError, (valid[0], valid[1], 1, valid[3])),
                "A15Q05": (
                    TypeError,
                    (valid[0], valid[1], valid[2], bytearray(b"{}")),
                ),
                "A15Q06": (ValueError, ("GET", valid[1], valid[2], valid[3])),
                "A15Q07": (
                    ValueError,
                    (valid[0], "http://example.test/", valid[2], valid[3]),
                ),
                "A15Q08": (
                    ValueError,
                    (valid[0], valid[1], "text/plain", valid[3]),
                ),
                "A15Q09": (
                    TypeError,
                    (TextSubclass("POST"), valid[1], valid[2], valid[3]),
                ),
                "A15Q10": (
                    TypeError,
                    (valid[0], TextSubclass(valid[1]), valid[2], valid[3]),
                ),
                "A15Q11": (
                    TypeError,
                    (
                        valid[0],
                        valid[1],
                        TextSubclass("application/json"),
                        valid[3],
                    ),
                ),
                "A15Q12": (
                    TypeError,
                    (valid[0], valid[1], valid[2], BytesSubclass(b"{}")),
                ),
            }
            expected_type, values = bad_values[fixture_id]
            self.assert_exact_raises(
                expected_type,
                lambda: OllamaTransportRequest(*values),
            )
            return

        if fixture_id.startswith("A15S"):
            if fixture_id in {"A15S01", "A15S02"}:
                status = 100 if fixture_id == "A15S01" else 599
                response = OllamaTransportResponse(status, b"")
                self.assertEqual((response.status, response.body), (status, b""))
                return
            direct_failures: dict[
                str,
                tuple[type[BaseException], tuple[object, object]],
            ] = {
                "A15S03": (ValueError, (99, b"")),
                "A15S04": (ValueError, (600, b"")),
                "A15S05": (TypeError, (True, b"")),
                "A15S06": (TypeError, ("200", b"")),
                "A15S07": (TypeError, (200, bytearray())),
                "A15S11": (TypeError, (IntSubclass(200), A01_RESPONSE_BODY)),
                "A15S12": (TypeError, (200, BytesSubclass(A01_RESPONSE_BODY))),
            }
            if fixture_id in direct_failures:
                expected_type, values = direct_failures[fixture_id]
                self.assert_exact_raises(
                    expected_type,
                    lambda: OllamaTransportResponse(*values),
                )
                return
            response = OllamaTransportResponse(200, A01_RESPONSE_BODY)
            mutations: dict[str, tuple[str, object, type[BaseException]]] = {
                "A15S08": ("status", True, TypeError),
                "A15S09": ("status", 99, ValueError),
                "A15S10": ("body", bytearray(A01_RESPONSE_BODY), TypeError),
                "A15S13": ("status", IntSubclass(200), TypeError),
                "A15S14": ("body", BytesSubclass(A01_RESPONSE_BODY), TypeError),
            }
            field, value, expected_type = mutations[fixture_id]
            object.__setattr__(response, field, value)
            transport = FakeTransport(response)
            result, error, _transport, captures = self.invoke(transport=transport)
            self.assertIsNone(result)
            self.assertIs(type(error), expected_type)
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 0)
            return

        if fixture_id.startswith("A15I"):
            valid = (
                OllamaAdapterCode.HTTP_STATUS,
                "/a~1b/~0c",
                ("status=201",),
            )
            if fixture_id == "A15I01":
                issue = OllamaAdapterIssue(*valid)
                self.assertEqual(
                    (issue.code, issue.path, issue.details),
                    valid,
                )
                return
            issue_failures: dict[
                str,
                tuple[type[BaseException], tuple[object, object, object]],
            ] = {
                "A15I02": (
                    TypeError,
                    ("ollama_http_status", valid[1], valid[2]),
                ),
                "A15I03": (TypeError, (valid[0], 1, valid[2])),
                "A15I04": (TypeError, (valid[0], valid[1], ["status=201"])),
                "A15I05": (
                    TypeError,
                    (valid[0], valid[1], TupleSubclass(("status=201",))),
                ),
                "A15I06": (TypeError, (valid[0], valid[1], (201,))),
                "A15I07": (ValueError, (valid[0], "~", valid[2])),
                "A15I08": (ValueError, (valid[0], "/a~2", valid[2])),
                "A15I09": (TypeError, (valid[0], TextSubclass("/a"), valid[2])),
                "A15I10": (
                    TypeError,
                    (valid[0], valid[1], (TextSubclass("status=201"),)),
                ),
            }
            expected_type, values = issue_failures[fixture_id]
            self.assert_exact_raises(
                expected_type,
                lambda: OllamaAdapterIssue(*values),
            )
            return

        if fixture_id.startswith("A15E"):
            z_issue = OllamaAdapterIssue(
                OllamaAdapterCode.HTTP_STATUS,
                "/z",
                ("status=201",),
            )
            a_issue = OllamaAdapterIssue(
                OllamaAdapterCode.RESPONSE_UTF8,
                "/a",
                (),
            )
            if fixture_id == "A15E01":
                supplied = (z_issue, a_issue, z_issue)
                before = (
                    (HTTP_STATUS, "/z", ("status=201",)),
                    (RESPONSE_UTF8, "/a", ()),
                    (HTTP_STATUS, "/z", ("status=201",)),
                )
                self.assertEqual(
                    tuple(
                        (issue.code.value, issue.path, issue.details)
                        for issue in supplied
                    ),
                    before,
                )
                error = OllamaAdapterError(supplied)
                self.assertEqual(
                    tuple(
                        (issue.code.value, issue.path, issue.details)
                        for issue in supplied
                    ),
                    before,
                )
                self.assertIs(supplied[0], z_issue)
                self.assertIs(supplied[2], z_issue)
                self.assertEqual(
                    issue_projection(error),
                    (
                        (RESPONSE_UTF8, "/a", ()),
                        (HTTP_STATUS, "/z", ("status=201",)),
                    ),
                )
                self.assertEqual(len(error.issues), 2)
                return
            if fixture_id == "A15E02":
                expected_type, supplied = ValueError, ()
            elif fixture_id == "A15E03":
                expected_type, supplied = TypeError, [z_issue]
            elif fixture_id == "A15E04":
                expected_type, supplied = TypeError, TupleSubclass((z_issue,))
            elif fixture_id == "A15E05":
                expected_type, supplied = TypeError, (object(),)
            else:
                expected_type = TypeError
                supplied = (
                    IssueSubclass(
                        OllamaAdapterCode.HTTP_STATUS,
                        "/status",
                        ("status=201",),
                    ),
                )
            self.assert_exact_raises(
                expected_type,
                lambda: OllamaAdapterError(supplied),  # type: ignore[arg-type]
            )
            return

        if fixture_id == "A15T01":
            error = OllamaTransportError()
            self.assertIs(type(error), OllamaTransportError)
            self.assertEqual(str(error), "Ollama transport failed")
            self.assertEqual(error.args, ("Ollama transport failed",))
            return
        if fixture_id == "A15T02":
            self.assert_exact_raises(
                TypeError,
                lambda: OllamaTransportError("x"),  # type: ignore[call-arg]
            )
            return

        if fixture_id == "A16":
            secret = "fixture-secret-do-not-log"
            body = b'{"error":"fixture-secret-do-not-log"}'

            class SecretTransport:
                def __init__(self) -> None:
                    self._credential = secret
                    self.response = OllamaTransportResponse(200, body)
                    self.requests: list[object] = []

                def __call__(self, request: object) -> OllamaTransportResponse:
                    self.requests.append(request)
                    return self.response

            request = self.request()
            transport = SecretTransport()
            result, error, _transport, captures = self.invoke(
                request=request,
                transport=transport,
            )
            self.assertIsNone(result)
            self.assertIs(type(error), OllamaAdapterError)
            assert isinstance(error, OllamaAdapterError)
            self.assertEqual(
                issue_projection(error),
                ((PROVIDER_ERROR, "/body/error", ()),),
            )
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 0)
            adapter_surfaces = (
                repr(request),
                repr(transport.requests[0]),
                repr(transport.response),
                str(error),
                repr(error),
                repr(error.issues),
            )
            for surface in adapter_surfaces:
                self.assertNotIn(secret, surface)
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)
            return

        if fixture_id == "A17":
            pff_validate = importlib.import_module("poietics.pff.validate")
            pff_compile = importlib.import_module("poietics.pff.compile")
            ground_evaluate = importlib.import_module("poietics.ground.evaluate")

            def forbidden(*_args: object, **_kwargs: object) -> object:
                raise AssertionError("forbidden adapter side effect")

            trap_patchers = (
                patch.object(extract_module, "extract_draft", side_effect=forbidden),
                patch.object(
                    ollama_module,
                    "extract_draft",
                    create=True,
                    side_effect=forbidden,
                ),
                patch.object(pff_validate, "validate_package", side_effect=forbidden),
                patch.object(pff_compile, "compile_package", side_effect=forbidden),
                patch.object(ground_evaluate, "evaluate", side_effect=forbidden),
                patch.object(builtins, "open", side_effect=forbidden),
                patch.object(builtins, "eval", side_effect=forbidden),
                patch.object(builtins, "exec", side_effect=forbidden),
                patch.object(builtins, "compile", side_effect=forbidden),
                patch.object(builtins, "print", side_effect=forbidden),
                patch.object(Path, "open", side_effect=forbidden),
                patch.object(os, "getenv", side_effect=forbidden),
                patch.object(os, "putenv", side_effect=forbidden),
                patch.object(os, "system", side_effect=forbidden),
                patch.object(subprocess, "run", side_effect=forbidden),
                patch.object(subprocess, "Popen", side_effect=forbidden),
                patch.object(socket, "socket", side_effect=forbidden),
                patch.object(socket, "create_connection", side_effect=forbidden),
                patch.object(urllib.request, "urlopen", side_effect=forbidden),
                patch.object(time, "sleep", side_effect=forbidden),
                patch.object(builtins, "__import__", side_effect=forbidden),
            )
            transport = FakeTransport(OllamaTransportResponse(200, A01_RESPONSE_BODY))
            with ExitStack() as stack:
                traps = [stack.enter_context(patcher) for patcher in trap_patchers]
                result, error, _transport, captures = self.invoke(transport=transport)
            self.assertIsNone(error)
            self.assertIs(type(result), GenerationEnvelope)
            self.assertEqual(len(transport.requests), 1)
            self.assertEqual(captures, 1)
            for trap in traps:
                trap.assert_not_called()
            return

        if fixture_id.startswith("A18F"):
            records = {
                "A18F01": (self.request(), "model", "other"),
                "A18F02": (
                    OllamaTransportRequest(
                        "POST",
                        OllamaEndpoint.LOCAL.value,
                        "application/json",
                        b"{}",
                    ),
                    "body",
                    b"changed",
                ),
                "A18F03": (
                    OllamaTransportResponse(200, A01_RESPONSE_BODY),
                    "body",
                    b"changed",
                ),
            }
            record, field, value = records[fixture_id]
            self.assert_exact_raises(
                FrozenInstanceError,
                lambda: setattr(record, field, value),
            )
            return
        if fixture_id.startswith("A18H"):
            records = {
                "A18H01": self.request(),
                "A18H02": OllamaTransportRequest(
                    "POST",
                    OllamaEndpoint.LOCAL.value,
                    "application/json",
                    b"{}",
                ),
                "A18H03": OllamaTransportResponse(200, A01_RESPONSE_BODY),
            }
            self.assert_exact_raises(TypeError, lambda: hash(records[fixture_id]))
            return
        if fixture_id.startswith("A18R"):
            sentinel = b"repr-secret-sentinel"
            records = {
                "A18R01": self.request(prompt=sentinel),
                "A18R02": OllamaTransportRequest(
                    "POST",
                    OllamaEndpoint.LOCAL.value,
                    "application/json",
                    sentinel,
                ),
                "A18R03": OllamaTransportResponse(200, sentinel),
            }
            self.assertNotIn("repr-secret-sentinel", repr(records[fixture_id]))
            return

        if fixture_id == "A19":
            self.assertEqual(len(A19_ASSISTANT), 115)
            self.assertEqual(sha256_text(A19_ASSISTANT), A19_ASSISTANT_SHA256)
            self.assertEqual(len(A19_RESPONSE_BODY), 200)
            self.assertEqual(sha256_text(A19_RESPONSE_BODY), A19_RESPONSE_SHA256)
            envelope, transport = self.assert_success(
                body=A19_RESPONSE_BODY,
                expected_reported_model="reported-model",
                expected_assistant=A19_ASSISTANT,
                expected_reason="stop",
            )
            transport.disabled = True
            first = extract_draft(envelope)
            second = extract_draft(envelope)
            self.assertEqual(first, second)
            self.assertIs(first.source, envelope)
            self.assertEqual(
                first.payload_sha256,
                "sha256:26a0b36236426e2f2dace4314c2938af3cfa8e26b52baaf25c43c50f9956411a",
            )
            self.assertEqual(first.draft.schema, "pff-draft/0.1")
            self.assertEqual(first.draft.atoms, ())
            self.assertEqual(first.draft.rules, ())
            self.assertEqual(first.draft.evidence_requests, ())
            self.assertEqual(len(transport.requests), 1)
            return

        if fixture_id == "A20AST":
            repository = Path(__file__).resolve().parents[1]
            profile_bytes = (
                repository / "docs" / "PFF_OLLAMA_ADAPTER_PROFILE_V0.1.md"
            ).read_bytes()
            self.assertEqual(
                hashlib.sha256(profile_bytes).hexdigest(),
                ACCEPTED_PROFILE_SHA256,
            )
            self.assertIn(
                REVIEWED_CANDIDATE_SHA256.encode("ascii"),
                profile_bytes,
            )
            source_path = repository / "src" / "poietics" / "generation" / "ollama.py"
            source = source_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(source_path))
            expected_imports = [
                ("import", 0, "", (("json", None),)),
                ("from", 0, "dataclasses", (("dataclass", None),)),
                ("from", 0, "enum", (("StrEnum", None),)),
                ("from", 0, "typing", (("Protocol", None),)),
                (
                    "from",
                    1,
                    "model",
                    (
                        ("AttemptRef", None),
                        ("AttemptRelation", None),
                        ("GenerationEnvelope", None),
                        ("capture_generation", None),
                    ),
                ),
            ]
            actual_imports: list[tuple[object, ...]] = []
            for node in tree.body:
                if isinstance(node, ast.Import):
                    actual_imports.append(
                        (
                            "import",
                            0,
                            "",
                            tuple((item.name, item.asname) for item in node.names),
                        )
                    )
                elif isinstance(node, ast.ImportFrom):
                    actual_imports.append(
                        (
                            "from",
                            node.level,
                            node.module or "",
                            tuple((item.name, item.asname) for item in node.names),
                        )
                    )
            all_import_nodes = tuple(
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            )
            self.assertEqual(actual_imports, expected_imports)
            self.assertEqual(len(all_import_nodes), len(expected_imports))
            call_names = tuple(
                name
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                for name in (dotted_name(node.func),)
                if name is not None
            )
            forbidden_exact = {
                "open",
                "eval",
                "exec",
                "compile",
                "__import__",
                "print",
                "extract_draft",
                "validate_package",
                "compile_package",
                "evaluate",
            }
            forbidden_roots = {
                "os",
                "pathlib",
                "subprocess",
                "socket",
                "urllib",
                "requests",
                "httpx",
                "time",
                "logging",
                "importlib",
            }
            for call_name in call_names:
                self.assertNotIn(call_name, forbidden_exact)
                self.assertNotIn(call_name.split(".", 1)[0], forbidden_roots)
            all_names = {
                node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
            }
            self.assertTrue(forbidden_exact.isdisjoint(all_names))
            string_constants = {
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and type(node.value) is str
            }
            self.assertNotIn("__import__", string_constants)
            self.assertEqual(call_names.count("transport"), 1)
            self.assertEqual(call_names.count("capture_generation"), 1)
            return
        self.fail(f"boundary fixture not implemented: {fixture_id}")

    def test_profile_fixtures_are_defined_dispatched_and_executed(self) -> None:
        self.assertEqual(len(DEFINED_IDS), 211)
        dispatch: dict[str, object] = {}

        def register(fixture_id: str, operation: object) -> None:
            self.assertNotIn(fixture_id, dispatch)
            dispatch[fixture_id] = operation

        register("A01", self.case_a01)
        register("A02", self.case_a02)
        for row in SERIALIZER_CASES:
            fixture_id = row[0]
            assert isinstance(fixture_id, str)
            register(
                fixture_id,
                lambda row=row: self.case_serializer(row),
            )
        for fixture_id in REQUEST_CASE_IDS:
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_request(fixture_id),
            )
        for fixture_id in RESPONSE_CASE_IDS:
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_response(fixture_id),
            )
        for fixture_id in BOUNDARY_CASE_IDS:
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_boundary(fixture_id),
            )

        dispatched_ids = frozenset(dispatch)
        self.assertEqual(len(dispatched_ids), 211)
        self.assertEqual(DEFINED_IDS, dispatched_ids)

        executed_ids: set[str] = set()
        for fixture_id in sorted(DEFINED_IDS):
            with self.subTest(fixture_id=fixture_id):
                try:
                    dispatch[fixture_id]()  # type: ignore[operator]
                finally:
                    executed_ids.add(fixture_id)

        self.assertEqual(DEFINED_IDS, dispatched_ids)
        self.assertEqual(dispatched_ids, frozenset(executed_ids))

    def test_mutation_target_manifest_is_exact_and_closed(self) -> None:
        self.assertEqual(len(MUTATION_IDS), 56)
        self.assertEqual(MUTATION_IDS, frozenset(MUTATION_TARGETS))
        self.assertEqual(len(MUTATION_TARGETS), 56)
        for mutation_id, target in MUTATION_TARGETS.items():
            with self.subTest(mutation_id=mutation_id):
                self.assertIs(type(target), tuple)
                self.assertEqual(len(target), 2)
                fixture_id, assertion_name = target
                self.assertIn(fixture_id, DEFINED_IDS)
                self.assertIs(type(assertion_name), str)
                self.assertTrue(assertion_name)

    def test_reentrant_transport_cannot_rewrite_pre_call_provenance(self) -> None:
        original_attempt = AttemptRef("session:reentrant", 2)
        original_parent = AttemptRef("session:reentrant", 1)
        request = OllamaGenerateRequest(
            endpoint=OllamaEndpoint.LOCAL,
            attempt=original_attempt,
            relation=AttemptRelation.RETRY,
            parent=original_parent,
            model="snapshot-model",
            prompt_template_id="snapshot-template",
            prompt_template_version="snapshot-version",
            prompt=b"snapshot prompt\n",
        )
        expected_request_body = (
            b'{"model":"snapshot-model","prompt":"snapshot prompt\\n",'
            b'"stream":false}'
        )

        class ReentrantTransport:
            def __init__(self) -> None:
                self.requests: list[OllamaTransportRequest] = []

            def __call__(
                self,
                transport_request: OllamaTransportRequest,
            ) -> OllamaTransportResponse:
                self.requests.append(transport_request)
                object.__setattr__(request, "endpoint", OllamaEndpoint.CLOUD)
                object.__setattr__(request, "relation", AttemptRelation.REPAIR)
                object.__setattr__(request, "model", "mutated-model")
                object.__setattr__(request, "prompt_template_id", "mutated-template")
                object.__setattr__(
                    request,
                    "prompt_template_version",
                    "mutated-version",
                )
                object.__setattr__(request, "prompt", b"mutated prompt")
                object.__setattr__(original_attempt, "session_id", "session:mutated")
                object.__setattr__(original_attempt, "sequence", 9)
                object.__setattr__(original_parent, "session_id", "session:mutated")
                object.__setattr__(original_parent, "sequence", 8)
                return OllamaTransportResponse(200, A01_RESPONSE_BODY)

        transport = ReentrantTransport()
        with patch.object(
            ollama_module,
            "capture_generation",
            wraps=ollama_module.capture_generation,
        ) as capture_spy:
            envelope = generate_ollama(request, transport=transport)

        self.assertEqual(len(transport.requests), 1)
        sent = transport.requests[0]
        self.assertIs(type(sent), OllamaTransportRequest)
        self.assertEqual(sent.method, "POST")
        self.assertEqual(sent.url, "http://localhost:11434/api/generate")
        self.assertEqual(sent.content_type, "application/json")
        self.assertEqual(sent.body, expected_request_body)
        self.assertEqual(capture_spy.call_count, 1)

        self.assertIs(request.endpoint, OllamaEndpoint.CLOUD)
        self.assertIs(request.relation, AttemptRelation.REPAIR)
        self.assertEqual(request.model, "mutated-model")
        self.assertEqual(request.prompt_template_id, "mutated-template")
        self.assertEqual(request.prompt_template_version, "mutated-version")
        self.assertEqual(request.prompt, b"mutated prompt")
        self.assertEqual(
            (request.attempt.session_id, request.attempt.sequence),
            ("session:mutated", 9),
        )
        self.assertEqual(
            (request.parent.session_id, request.parent.sequence),
            ("session:mutated", 8),
        )

        self.assertIs(type(envelope), GenerationEnvelope)
        self.assertEqual(
            (envelope.attempt.session_id, envelope.attempt.sequence),
            ("session:reentrant", 2),
        )
        self.assertIs(envelope.relation, AttemptRelation.RETRY)
        self.assertIsNotNone(envelope.parent)
        assert envelope.parent is not None
        self.assertEqual(
            (envelope.parent.session_id, envelope.parent.sequence),
            ("session:reentrant", 1),
        )
        self.assertEqual(envelope.provider_id, "ollama-local")
        self.assertEqual(envelope.adapter_id, "ollama-generate")
        self.assertEqual(envelope.adapter_version, "1")
        self.assertEqual(envelope.requested_model, "snapshot-model")
        self.assertEqual(envelope.reported_model, "reported-model")
        self.assertEqual(envelope.prompt_template_id, "snapshot-template")
        self.assertEqual(envelope.prompt_template_version, "snapshot-version")
        self.assertEqual(envelope.prompt.data, b"snapshot prompt\n")
        self.assertEqual(
            envelope.prompt.sha256,
            "sha256:d386373c65a687ad34bdc52c3aa558c40c73c538b787222c68673baf1e994ef7",
        )
        self.assertEqual(
            tuple((item.name, item.value) for item in envelope.public_parameters),
            (("stream", "false"),),
        )
        self.assertEqual(envelope.raw_response.data, A01_ASSISTANT)
        self.assertEqual(envelope.raw_response.sha256, A01_ASSISTANT_SHA256)
        self.assertEqual(envelope.finish_reason, "stop")
        self.assertIsNone(envelope.provider_request_id)


if __name__ == "__main__":
    unittest.main()
