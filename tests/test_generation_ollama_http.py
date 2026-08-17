from __future__ import annotations

import ast
import builtins
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import hashlib
import http.client
import importlib
import inspect
import logging
import os
from pathlib import Path
import socket
import subprocess
import textwrap
import time
import unittest
from unittest.mock import patch
import urllib.request

import poietics.generation as generation_package
import poietics.generation.extract as extract_module
from poietics.generation.model import (
    AttemptRef,
    AttemptRelation,
    GenerationEnvelope,
)
import poietics.generation.ollama as ollama_module
from poietics.generation.ollama import (
    OllamaAdapterCode,
    OllamaAdapterError,
    OllamaEndpoint,
    OllamaGenerateRequest,
    OllamaTransportError,
    OllamaTransportRequest,
    OllamaTransportResponse,
    generate_ollama,
)
import poietics.generation.ollama_http as ollama_http_module
from poietics.generation.ollama_http import OllamaHttpTransport
import poietics.pff.compile as pff_compile_module
import poietics.pff.validate as pff_validate_module


ground_evaluate_module = importlib.import_module("poietics.ground.evaluate")


ACCEPTED_PROFILE_SHA256 = (
    "c9f756048bd7ff29ae160a7499576f64a8bfc52b7e1c13ab493b49119d35e0e5"
)
REVIEWED_CANDIDATE_SHA256 = (
    "41a5b07d24734dc59364a8a6d91bd77e081e3a42393972d1295b50fc21644b9e"
)

BODY = b'{"x":1}'
RESPONSE_BODY = b'{"ok":true}'
READ_AMOUNT = 4_194_305

LOCAL_URL = "http://localhost:11434/api/generate"
CLOUD_URL = "https://ollama.com/api/generate"

LOCAL_HEADERS = (
    ("Accept", "application/json"),
    ("Accept-Encoding", "identity"),
    ("Connection", "close"),
    ("Content-Length", "7"),
    ("Content-Type", "application/json"),
)
CLOUD_HEADERS = LOCAL_HEADERS + (("Authorization", "Bearer token!"),)

LOCAL_SUCCESS_TRACE = (
    ("factory", "http", "localhost", 11434, 120),
    ("request", "POST", "/api/generate", BODY, LOCAL_HEADERS, False),
    ("getresponse",),
    ("status",),
    ("read", READ_AMOUNT),
    ("response.close",),
    ("connection.close",),
)
CLOUD_SUCCESS_TRACE = (
    ("factory", "https", "ollama.com", 443, 37),
    ("request", "POST", "/api/generate", BODY, CLOUD_HEADERS, False),
    ("getresponse",),
    ("status",),
    ("read", READ_AMOUNT),
    ("response.close",),
    ("connection.close",),
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

A01_LOCAL_HEADERS = (
    ("Accept", "application/json"),
    ("Accept-Encoding", "identity"),
    ("Connection", "close"),
    ("Content-Length", "68"),
    ("Content-Type", "application/json"),
)
A01_CLOUD_HEADERS = A01_LOCAL_HEADERS + (
    ("Authorization", "Bearer token!"),
)


DEFINED_IDS = frozenset(
    {
        "D01API",
        "D02KEYOK", "D02KEYTYPE", "D02KEYVALUE",
        "D03TIMEOK", "D03TIMETYPE", "D03TIMEVALUE",
        "D04LOCAL", "D05CLOUD", "D06NOKEY", "D07LOCALKEY",
        "D08EMPTYBODY", "D08ONEBODY", "D08BIGBODY", "D09STATUS",
        "D10BODYZERO", "D10BODYMAX", "D10BODYSENTINEL",
        "D10BODYOVERFAKE", "D11STATUSBAD", "D11BODYBAD",
        "D12MISSSTATUS", "D12MISSREAD",
        "D13OSFACTORY", "D13OSREQUEST", "D13OSGET", "D13OSSTATUS",
        "D13OSREAD", "D14HTTPFACTORY", "D14HTTPREQUEST", "D14HTTPGET",
        "D14HTTPSTATUS", "D14HTTPREAD", "D15UNEXPECTED", "D16BASE",
        "D17CLOSERESP", "D17CLOSECONN", "D17CLOSEMAPPED",
        "D17CLOSEUNEXPECTED", "D18BASERESP", "D18BASECONN",
        "D19REFACTORY", "D19ASTCONFIG", "D19ASTREQUEST",
        "D20REQTYPE", "D20REQCORRUPT", "D20CFGCORRUPT",
        "D21NOINSPECT", "D22REDIRECT", "D23SECRETS", "D24RUNTIME",
        "D25AST", "D26COMPOSELOCAL", "D27COMPOSECLOUD",
        "D28STATUSSIZE", "D28OKSIZE", "D29FRESH", "D30IMPORT",
    }
)


MUTATION_TARGETS = {
    "M01": ("D25AST", "exact_import_set"),
    "M02": ("D01API", "credential_absent_from_repr"),
    "M03": ("D02KEYVALUE", "empty_key_rejected"),
    "M04": ("D02KEYVALUE", "space_rejected"),
    "M05": ("D02KEYVALUE", "key_byte_limit"),
    "M06": ("D03TIMETYPE", "bool_timeout_rejected"),
    "M07": ("D03TIMEVALUE", "zero_timeout_rejected"),
    "M08": ("D01API", "generated_equality"),
    "M09": ("D04LOCAL", "local_factory_host"),
    "M10": ("D04LOCAL", "local_factory_port"),
    "M11": ("D05CLOUD", "cloud_factory_kind"),
    "M12": ("D05CLOUD", "cloud_factory_host"),
    "M13": ("D05CLOUD", "cloud_factory_port"),
    "M14": ("D06NOKEY", "missing_key_pre_io"),
    "M15": ("D07LOCALKEY", "local_authorization_absent"),
    "M16": ("D05CLOUD", "cloud_authorization_present"),
    "M17": ("D05CLOUD", "cloud_header_order"),
    "M18": ("D04LOCAL", "accept_header_present"),
    "M19": ("D08ONEBODY", "content_length_present"),
    "M20": ("D04LOCAL", "chunked_false"),
    "M21": ("D04LOCAL", "generate_path"),
    "M22": ("D04LOCAL", "body_unchanged"),
    "M23": ("D22REDIRECT", "redirect_one_request"),
    "M24": ("D09STATUS", "rate_limit_one_request"),
    "M25": ("D09STATUS", "server_error_one_request"),
    "M26": ("D10BODYZERO", "bounded_read_argument"),
    "M27": ("D10BODYSENTINEL", "sentinel_prefix_length"),
    "M28": ("D10BODYOVERFAKE", "one_read_only"),
    "M29": ("D11BODYBAD", "exact_bytes_result"),
    "M30": ("D11STATUSBAD", "exact_int_status"),
    "M31": ("D11STATUSBAD", "status_before_read"),
    "M32": ("D10BODYOVERFAKE", "fake_overrun_rejected"),
    "M33": ("D12MISSSTATUS", "attribute_error_unchanged"),
    "M34": ("D13OSREAD", "mapped_error_clean_chain"),
    "M35": ("D14HTTPREAD", "http_exception_mapped"),
    "M36": ("D15UNEXPECTED", "unexpected_identity"),
    "M37": ("D16BASE", "base_identity"),
    "M38": ("D13OSREAD", "response_close_present"),
    "M39": ("D13OSREQUEST", "connection_close_present"),
    "M40": ("D13OSREAD", "cleanup_order"),
    "M41": ("D17CLOSERESP", "response_close_error_suppressed"),
    "M42": ("D17CLOSERESP", "cleanup_continues"),
    "M43": ("D18BASERESP", "base_close_not_caught"),
    "M44": ("D19REFACTORY", "request_snapshot"),
    "M45": ("D19REFACTORY", "credential_snapshot"),
    "M46": ("D19ASTCONFIG", "configuration_single_load"),
    "M47": ("D20REQCORRUPT", "invocation_request_revalidation"),
    "M48": ("D20CFGCORRUPT", "invocation_config_revalidation"),
    "M49": ("D21NOINSPECT", "headers_not_read"),
    "M50": ("D21NOINSPECT", "opaque_gzip_bytes"),
    "M51": ("D23SECRETS", "transport_repr_redaction"),
    "M52": ("D13OSFACTORY", "mapped_error_no_cause"),
    "M53": ("D25AST", "no_extract_import"),
    "M54": ("D24RUNTIME", "filesystem_trap"),
    "M55": ("D29FRESH", "connection_not_reused"),
    "M56": ("D30IMPORT", "construction_no_connection"),
    "M57": ("D09STATUS", "status_500_passthrough"),
    "M58": ("D05CLOUD", "header_insertion_order"),
    "M59": ("D01API", "exact_all"),
    "M60": ("D20REQTYPE", "request_subclass_rejected"),
    "M61": ("D28OKSIZE", "adapter_body_limit_preserved"),
    "M62": ("D21NOINSPECT", "content_length_not_read"),
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
        "M57", "M58", "M59", "M60", "M61", "M62",
    }
)


SUPPLEMENTAL_FIXTURE_IDS = frozenset(
    {
        "S01KEYERROR",
        "S02NOSURFACE",
        "S03KEYOPAQUE",
        "S04TIME600",
        "S05STATUSBOUNDS",
        "S06FRESHERROR",
    }
)

SUPPLEMENTAL_MUTATION_TARGETS = {
    "X01": ("D10BODYOVERFAKE", "one_total_read"),
    "X02": ("S01KEYERROR", "invalid_key_error_redaction"),
    "X03": ("S02NOSURFACE", "no_public_credential_surface"),
    "X04": ("S03KEYOPAQUE", "authorization_key_byte_identity"),
    "X05": ("S04TIME600", "timeout_upper_bound_forwarded"),
    "X06": ("S05STATUSBOUNDS", "status_boundary_passthrough"),
    "X07": ("S06FRESHERROR", "recognized_error_freshness"),
}

SUPPLEMENTAL_MUTATION_IDS = frozenset(
    {"X01", "X02", "X03", "X04", "X05", "X06", "X07"}
)


class TextSubclass(str):
    pass


class IntSubclass(int):
    pass


class BytesSubclass(bytes):
    pass


class RequestSubclass(OllamaTransportRequest):
    pass


class SlotsDuckRequest:
    __slots__ = ("method", "url", "content_type", "body")

    def __init__(self) -> None:
        self.method = "POST"
        self.url = LOCAL_URL
        self.content_type = "application/json"
        self.body = BODY


class SentinelError(Exception):
    pass


Hook = object


def _run_hook(hooks: dict[str, Hook], name: str) -> None:
    hook = hooks.get(name)
    if hook is not None:
        hook()  # type: ignore[operator]


class FakeResponse:
    def __init__(
        self,
        events: list[tuple[object, ...]],
        hooks: dict[str, Hook],
        *,
        status: object,
        body: object,
    ) -> None:
        self._events = events
        self._hooks = hooks
        self._status = status
        self._body = body

    @property
    def status(self) -> object:
        self._events.append(("status",))
        _run_hook(self._hooks, "status")
        return self._status

    def read(self, amount: object = None) -> object:
        self._events.append(("read", amount))
        _run_hook(self._hooks, "read")
        return self._body

    def close(self) -> None:
        self._events.append(("response.close",))
        _run_hook(self._hooks, "response.close")


class MissingStatusResponse:
    def __init__(
        self,
        events: list[tuple[object, ...]],
        hooks: dict[str, Hook],
        *,
        body: object,
    ) -> None:
        self._events = events
        self._hooks = hooks
        self._body = body

    def read(self, amount: object = None) -> object:
        self._events.append(("read", amount))
        return self._body

    def close(self) -> None:
        self._events.append(("response.close",))
        _run_hook(self._hooks, "response.close")


class MissingReadResponse:
    def __init__(
        self,
        events: list[tuple[object, ...]],
        hooks: dict[str, Hook],
        *,
        status: object,
    ) -> None:
        self._events = events
        self._hooks = hooks
        self._status = status

    @property
    def status(self) -> object:
        self._events.append(("status",))
        return self._status

    def close(self) -> None:
        self._events.append(("response.close",))
        _run_hook(self._hooks, "response.close")


class ForbiddenInspectionResponse(FakeResponse):
    @property
    def headers(self) -> object:
        raise AssertionError("forbidden-response-inspection")

    @property
    def reason(self) -> object:
        raise AssertionError("forbidden-response-inspection")

    @property
    def url(self) -> object:
        raise AssertionError("forbidden-response-inspection")

    @property
    def request_id(self) -> object:
        raise AssertionError("forbidden-response-inspection")

    @property
    def location(self) -> object:
        raise AssertionError("forbidden-response-inspection")

    def getheader(self, _name: object, _default: object = None) -> object:
        raise AssertionError("forbidden-response-inspection")


class FakeConnection:
    def __init__(
        self,
        events: list[tuple[object, ...]],
        hooks: dict[str, Hook],
        response: object,
    ) -> None:
        self._events = events
        self._hooks = hooks
        self._response = response

    def request(
        self,
        method: object,
        path: object,
        *,
        body: object,
        headers: object,
        encode_chunked: object,
    ) -> None:
        self._events.append(
            (
                "request",
                method,
                path,
                body,
                tuple(headers.items()),  # type: ignore[union-attr]
                encode_chunked,
            )
        )
        _run_hook(self._hooks, "request")

    def getresponse(self) -> object:
        self._events.append(("getresponse",))
        _run_hook(self._hooks, "getresponse")
        return self._response

    def close(self) -> None:
        self._events.append(("connection.close",))
        _run_hook(self._hooks, "connection.close")


class FakeNetwork:
    def __init__(
        self,
        *,
        status: object = 200,
        body: object = RESPONSE_BODY,
        hooks: dict[str, Hook] | None = None,
        response_kind: str = "normal",
    ) -> None:
        self.status = status
        self.body = body
        self.hooks = {} if hooks is None else hooks
        self.response_kind = response_kind
        self.events: list[tuple[object, ...]] = []
        self.connections: list[FakeConnection] = []
        self.responses: list[object] = []
        self.http_factory_calls = 0
        self.https_factory_calls = 0

    def _response(self) -> object:
        if self.response_kind == "missing-status":
            return MissingStatusResponse(
                self.events,
                self.hooks,
                body=self.body,
            )
        if self.response_kind == "missing-read":
            return MissingReadResponse(
                self.events,
                self.hooks,
                status=self.status,
            )
        response_type = (
            ForbiddenInspectionResponse
            if self.response_kind == "forbidden"
            else FakeResponse
        )
        return response_type(
            self.events,
            self.hooks,
            status=self.status,
            body=self.body,
        )

    def _factory(
        self,
        kind: str,
        host: object,
        port: object,
        *,
        timeout: object,
    ) -> FakeConnection:
        self.events.append(("factory", kind, host, port, timeout))
        _run_hook(self.hooks, "factory")
        response = self._response()
        connection = FakeConnection(self.events, self.hooks, response)
        self.responses.append(response)
        self.connections.append(connection)
        return connection

    def http_factory(
        self,
        host: object,
        port: object,
        *,
        timeout: object,
    ) -> FakeConnection:
        self.http_factory_calls += 1
        return self._factory("http", host, port, timeout=timeout)

    def https_factory(
        self,
        host: object,
        port: object,
        *,
        timeout: object,
    ) -> FakeConnection:
        self.https_factory_calls += 1
        return self._factory("https", host, port, timeout=timeout)

    def patches(self) -> tuple[object, object]:
        return (
            patch.object(
                ollama_http_module.http.client,
                "HTTPConnection",
                self.http_factory,
            ),
            patch.object(
                ollama_http_module.http.client,
                "HTTPSConnection",
                self.https_factory,
            ),
        )


def _raise(error: BaseException) -> None:
    raise error


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        if prefix is not None:
            return prefix + "." + node.attr
    return None


def _issue_projection(
    error: OllamaAdapterError,
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (issue.code.value, issue.path, issue.details)
        for issue in error.issues
    )


class OllamaHttpTransportConformanceTests(unittest.TestCase):
    maxDiff = None

    def direct_request(
        self,
        *,
        cloud: bool = False,
        body: bytes = BODY,
    ) -> OllamaTransportRequest:
        return OllamaTransportRequest(
            method="POST",
            url=CLOUD_URL if cloud else LOCAL_URL,
            content_type="application/json",
            body=body,
        )

    def generate_request(
        self,
        *,
        endpoint: OllamaEndpoint = OllamaEndpoint.LOCAL,
    ) -> OllamaGenerateRequest:
        return OllamaGenerateRequest(
            endpoint=endpoint,
            attempt=AttemptRef("session:ollama", 1),
            relation=AttemptRelation.INITIAL,
            parent=None,
            model="test-model",
            prompt_template_id="pff-draft-prompt",
            prompt_template_version="1",
            prompt=A01_PROMPT,
        )

    def invoke(
        self,
        transport: object,
        request: object,
        network: FakeNetwork,
    ) -> tuple[object | None, BaseException | None]:
        result: object | None = None
        error: BaseException | None = None
        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            try:
                result = transport(request)  # type: ignore[operator]
            except BaseException as caught:
                error = caught
        return result, error

    def assert_exact_error(
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

    def assert_clean_transport_error(
        self,
        error: BaseException | None,
    ) -> OllamaTransportError:
        self.assertIs(type(error), OllamaTransportError)
        assert isinstance(error, OllamaTransportError)
        self.assertEqual(str(error), "Ollama transport failed")
        self.assertEqual(error.args, ("Ollama transport failed",))
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        return error

    def assert_response(
        self,
        result: object | None,
        error: BaseException | None,
        *,
        status: int = 200,
        body: bytes = RESPONSE_BODY,
    ) -> OllamaTransportResponse:
        self.assertIsNone(error)
        self.assertIs(type(result), OllamaTransportResponse)
        assert isinstance(result, OllamaTransportResponse)
        self.assertEqual(result.status, status)
        self.assertEqual(result.body, body)
        return result

    def assert_a01_envelope(
        self,
        envelope: object,
        *,
        provider_id: str,
    ) -> GenerationEnvelope:
        self.assertIs(type(envelope), GenerationEnvelope)
        assert isinstance(envelope, GenerationEnvelope)
        self.assertEqual(envelope.profile, "pff-generation/0.1")
        self.assertIs(type(envelope.attempt), AttemptRef)
        self.assertEqual(envelope.attempt.session_id, "session:ollama")
        self.assertEqual(envelope.attempt.sequence, 1)
        self.assertIs(envelope.relation, AttemptRelation.INITIAL)
        self.assertIsNone(envelope.parent)
        self.assertEqual(envelope.provider_id, provider_id)
        self.assertEqual(envelope.adapter_id, "ollama-generate")
        self.assertEqual(envelope.adapter_version, "1")
        self.assertEqual(envelope.requested_model, "test-model")
        self.assertEqual(envelope.reported_model, "reported-model")
        self.assertEqual(envelope.prompt_template_id, "pff-draft-prompt")
        self.assertEqual(envelope.prompt_template_version, "1")
        self.assertEqual(envelope.prompt.data, A01_PROMPT)
        self.assertEqual(envelope.prompt.sha256, A01_PROMPT_SHA256)
        self.assertEqual(
            tuple((item.name, item.value) for item in envelope.public_parameters),
            (("stream", "false"),),
        )
        self.assertEqual(envelope.raw_response.data, A01_ASSISTANT)
        self.assertEqual(envelope.raw_response.sha256, A01_ASSISTANT_SHA256)
        self.assertEqual(envelope.finish_reason, "stop")
        self.assertIsNone(envelope.provider_request_id)
        return envelope

    def call_ast(self) -> ast.FunctionDef:
        source = Path(ollama_http_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "OllamaHttpTransport":
                for member in node.body:
                    if isinstance(member, ast.FunctionDef) and member.name == "__call__":
                        return member
        self.fail("OllamaHttpTransport.__call__ AST was not found")

    def assert_configuration_ast(self) -> None:
        function = self.call_ast()
        field_loads: dict[str, list[ast.Attribute]] = {
            "_cloud_api_key": [],
            "_timeout_seconds": [],
        }
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.ctx, ast.Load)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and node.attr in field_loads
            ):
                field_loads[node.attr].append(node)
        self.assertEqual(len(field_loads["_cloud_api_key"]), 1)
        self.assertEqual(len(field_loads["_timeout_seconds"]), 1)

        factory_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and _dotted_name(node.func)
            in {
                "http.client.HTTPConnection",
                "http.client.HTTPSConnection",
            }
        ]
        self.assertEqual(len(factory_calls), 2)
        first_factory_line = min(node.lineno for node in factory_calls)
        self.assertLess(field_loads["_cloud_api_key"][0].lineno, first_factory_line)
        self.assertLess(field_loads["_timeout_seconds"][0].lineno, first_factory_line)

    def assert_request_snapshot_ast(self) -> None:
        function = self.call_ast()
        snapshot_statements = [
            statement
            for statement in function.body
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            and isinstance(statement.value, ast.Call)
            and _dotted_name(statement.value.func) == "OllamaTransportRequest"
        ]
        self.assertEqual(len(snapshot_statements), 1)
        snapshot = snapshot_statements[0]
        later_request_loads = [
            node
            for statement in function.body
            if statement.lineno > snapshot.lineno
            for node in ast.walk(statement)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id == "request"
        ]
        self.assertEqual(later_request_loads, [])

    def case_api(self) -> None:
        self.assertEqual(ollama_http_module.__all__, ("OllamaHttpTransport",))
        self.assertEqual(
            OllamaHttpTransport.__slots__,
            ("_cloud_api_key", "_timeout_seconds"),
        )
        transport = OllamaHttpTransport("token!", 37)
        assignment_error = self.assert_exact_error(
            FrozenInstanceError,
            lambda: setattr(transport, "_timeout_seconds", 38),
        )
        deletion_error = self.assert_exact_error(
            FrozenInstanceError,
            lambda: delattr(transport, "_cloud_api_key"),
        )
        self.assertTrue(str(assignment_error))
        self.assertTrue(str(deletion_error))
        self.assert_exact_error(TypeError, lambda: hash(transport))

        for surface in (repr(transport), str(transport)):
            self.assertNotIn("_cloud_api_key", surface)
            self.assertNotIn("_timeout_seconds", surface)
            self.assertNotIn("token!", surface)
            self.assertNotIn("OllamaHttpTransport(", surface)
        self.assertEqual(transport, OllamaHttpTransport("token!", 37))
        self.assertNotEqual(transport, OllamaHttpTransport("token?", 37))
        self.assertNotEqual(transport, OllamaHttpTransport("token!", 38))
        self.assertNotEqual(transport, object())
        self.assertNotEqual(transport, ("token!", 37))
        init_parameters = tuple(inspect.signature(OllamaHttpTransport.__init__).parameters.values())
        self.assertEqual(
            tuple(parameter.name for parameter in init_parameters),
            ("self", "cloud_api_key", "timeout_seconds"),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                for parameter in init_parameters
            )
        )
        self.assertIs(init_parameters[1].default, None)
        self.assertEqual(init_parameters[2].default, 120)
        call_parameters = tuple(inspect.signature(OllamaHttpTransport.__call__).parameters.values())
        self.assertEqual(
            tuple(parameter.name for parameter in call_parameters),
            ("self", "request"),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.POSITIONAL_ONLY
                for parameter in call_parameters
            )
        )
        self.assertFalse(
            any(
                name.startswith("cloud_api_key")
                for name in dir(transport)
                if not name.startswith("_")
            )
        )

    def case_key(self, fixture_id: str) -> None:
        network = FakeNetwork()
        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            if fixture_id == "D02KEYOK":
                for value in (None, "!", "A" * 4_096):
                    with self.subTest(value_length=None if value is None else len(value)):
                        transport = OllamaHttpTransport(value)
                        self.assertIs(type(transport), OllamaHttpTransport)
            elif fixture_id == "D02KEYTYPE":
                for value in (b"x", TextSubclass("x"), 1):
                    with self.subTest(value=value):
                        self.assert_exact_error(
                            TypeError,
                            lambda value=value: OllamaHttpTransport(value),
                        )
            else:
                for value in (
                    "",
                    " ",
                    "\x7f",
                    "\n",
                    "\u00e9",
                    "A" * 4_097,
                ):
                    with self.subTest(value_length=len(value), value_prefix=value[:1]):
                        self.assert_exact_error(
                            ValueError,
                            lambda value=value: OllamaHttpTransport(value),
                        )
        self.assertEqual(network.events, [])
        self.assertEqual(network.http_factory_calls, 0)
        self.assertEqual(network.https_factory_calls, 0)

    def case_timeout(self, fixture_id: str) -> None:
        network = FakeNetwork()
        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            if fixture_id == "D03TIMEOK":
                values = tuple(OllamaHttpTransport(timeout_seconds=value) for value in (1, 120, 600))
                self.assertEqual(values[1], OllamaHttpTransport(timeout_seconds=120))
                self.assertNotEqual(values[0], values[1])
                self.assertNotEqual(values[1], values[2])
            elif fixture_id == "D03TIMETYPE":
                for value in (True, IntSubclass(1), 1.0):
                    with self.subTest(value=value):
                        self.assert_exact_error(
                            TypeError,
                            lambda value=value: OllamaHttpTransport(
                                timeout_seconds=value,  # type: ignore[arg-type]
                            ),
                        )
            else:
                for value in (0, -1, 601):
                    with self.subTest(value=value):
                        self.assert_exact_error(
                            ValueError,
                            lambda value=value: OllamaHttpTransport(
                                timeout_seconds=value,
                            ),
                        )
        self.assertEqual(network.events, [])
        self.assertEqual(network.http_factory_calls, 0)
        self.assertEqual(network.https_factory_calls, 0)

    def case_canonical(self, fixture_id: str) -> None:
        if fixture_id == "D04LOCAL":
            network = FakeNetwork()
            result, error = self.invoke(
                OllamaHttpTransport(),
                self.direct_request(),
                network,
            )
            self.assert_response(result, error)
            self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
            self.assertEqual(network.http_factory_calls, 1)
            self.assertEqual(network.https_factory_calls, 0)
            return

        if fixture_id == "D05CLOUD":
            network = FakeNetwork()
            result, error = self.invoke(
                OllamaHttpTransport("token!", 37),
                self.direct_request(cloud=True),
                network,
            )
            self.assert_response(result, error)
            self.assertEqual(tuple(network.events), CLOUD_SUCCESS_TRACE)
            self.assertEqual(network.http_factory_calls, 0)
            self.assertEqual(network.https_factory_calls, 1)
            return

        if fixture_id == "D06NOKEY":
            errors: list[OllamaTransportError] = []
            for _attempt in range(2):
                network = FakeNetwork()
                result, error = self.invoke(
                    OllamaHttpTransport(),
                    self.direct_request(cloud=True),
                    network,
                )
                self.assertIsNone(result)
                errors.append(self.assert_clean_transport_error(error))
                self.assertEqual(network.events, [])
                self.assertEqual(network.http_factory_calls, 0)
                self.assertEqual(network.https_factory_calls, 0)
            self.assertIsNot(errors[0], errors[1])
            return

        network = FakeNetwork()
        secret = "local-secret!"
        transport = OllamaHttpTransport(secret)
        result, error = self.invoke(
            transport,
            self.direct_request(),
            network,
        )
        self.assert_response(result, error)
        self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
        request_event = network.events[1]
        self.assertEqual(request_event[4], LOCAL_HEADERS)
        self.assertNotIn(secret, repr(transport))
        self.assertNotIn(secret, str(transport))
        self.assertNotIn(secret, repr(result))

    def case_body(self, fixture_id: str) -> None:
        rows = {
            "D08EMPTYBODY": (b"", "0"),
            "D08ONEBODY": (b"x", "1"),
            "D08BIGBODY": (b"x" * 100_000, "100000"),
        }
        body, expected_length = rows[fixture_id]
        expected_headers = (
            ("Accept", "application/json"),
            ("Accept-Encoding", "identity"),
            ("Connection", "close"),
            ("Content-Length", expected_length),
            ("Content-Type", "application/json"),
        )
        network = FakeNetwork()
        result, error = self.invoke(
            OllamaHttpTransport(),
            self.direct_request(body=body),
            network,
        )
        self.assert_response(result, error)
        self.assertEqual(
            network.events[1],
            (
                "request",
                "POST",
                "/api/generate",
                body,
                expected_headers,
                False,
            ),
        )
        self.assertEqual(network.events.count(("getresponse",)), 1)
        self.assertEqual(network.events.count(("read", READ_AMOUNT)), 1)

    def case_status(self) -> None:
        for status in (201, 301, 400, 404, 429, 500, 502):
            with self.subTest(status=status):
                network = FakeNetwork(status=status)
                result, error = self.invoke(
                    OllamaHttpTransport(),
                    self.direct_request(),
                    network,
                )
                self.assert_response(result, error, status=status)
                self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
                self.assertEqual(network.events.count(("request", "POST", "/api/generate", BODY, LOCAL_HEADERS, False)), 1)

    def case_response_body(self, fixture_id: str) -> None:
        if fixture_id == "D10BODYZERO":
            body = b""
        elif fixture_id == "D10BODYMAX":
            body = b"x" * 4_194_304
        elif fixture_id == "D10BODYSENTINEL":
            body = b"x" * 4_194_305
        else:
            body = b"x" * 4_194_306
        network = FakeNetwork(body=body)
        result, error = self.invoke(
            OllamaHttpTransport(),
            self.direct_request(),
            network,
        )
        read_events = [
            event
            for event in network.events
            if event and event[0] == "read"
        ]
        self.assertEqual(read_events, [("read", READ_AMOUNT)])
        self.assertEqual(network.events[-2:], [("response.close",), ("connection.close",)])
        if fixture_id == "D10BODYOVERFAKE":
            self.assertIsNone(result)
            self.assert_clean_transport_error(error)
        else:
            self.assert_response(result, error, body=body)
            self.assertEqual(len(result.body), len(body))  # type: ignore[union-attr]

    def case_bad_return(self, fixture_id: str) -> None:
        if fixture_id == "D11STATUSBAD":
            rows: tuple[tuple[object, type[BaseException]], ...] = (
                (True, TypeError),
                (IntSubclass(200), TypeError),
                (99, ValueError),
                (600, ValueError),
            )
            for value, _constructor_error in rows:
                with self.subTest(value=value):
                    network = FakeNetwork(status=value)
                    result, error = self.invoke(
                        OllamaHttpTransport(),
                        self.direct_request(),
                        network,
                    )
                    self.assertIsNone(result)
                    self.assert_clean_transport_error(error)
                    self.assertEqual(
                        tuple(network.events),
                        LOCAL_SUCCESS_TRACE[:4]
                        + (("response.close",), ("connection.close",)),
                    )
                    self.assertNotIn(("read", READ_AMOUNT), network.events)
            return

        for value in (bytearray(b"x"), BytesSubclass(b"x")):
            with self.subTest(value_type=type(value).__name__):
                network = FakeNetwork(body=value)
                result, error = self.invoke(
                    OllamaHttpTransport(),
                    self.direct_request(),
                    network,
                )
                self.assertIsNone(result)
                self.assert_clean_transport_error(error)
                self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)

    def case_missing_shape(self, fixture_id: str) -> None:
        response_kind = (
            "missing-status" if fixture_id == "D12MISSSTATUS" else "missing-read"
        )
        network = FakeNetwork(response_kind=response_kind)
        result, error = self.invoke(
            OllamaHttpTransport(),
            self.direct_request(),
            network,
        )
        self.assertIsNone(result)
        self.assertIs(type(error), AttributeError)
        if fixture_id == "D12MISSSTATUS":
            expected = LOCAL_SUCCESS_TRACE[:3] + (
                ("response.close",),
                ("connection.close",),
            )
        else:
            expected = LOCAL_SUCCESS_TRACE[:4] + (
                ("response.close",),
                ("connection.close",),
            )
        self.assertEqual(tuple(network.events), expected)

    def _exchange_hook_trace(
        self,
        stage: str,
    ) -> tuple[tuple[object, ...], ...]:
        if stage == "factory":
            return LOCAL_SUCCESS_TRACE[:1]
        if stage == "request":
            return LOCAL_SUCCESS_TRACE[:2] + (("connection.close",),)
        if stage == "getresponse":
            return LOCAL_SUCCESS_TRACE[:3] + (("connection.close",),)
        if stage == "status":
            return LOCAL_SUCCESS_TRACE[:4] + (
                ("response.close",),
                ("connection.close",),
            )
        if stage == "read":
            return LOCAL_SUCCESS_TRACE[:5] + (
                ("response.close",),
                ("connection.close",),
            )
        raise AssertionError(f"unknown stage: {stage}")

    def case_recognized_error(self, fixture_id: str) -> None:
        stage_names = {
            "D13OSFACTORY": ("factory", OSError),
            "D13OSREQUEST": ("request", OSError),
            "D13OSGET": ("getresponse", OSError),
            "D13OSSTATUS": ("status", OSError),
            "D13OSREAD": ("read", OSError),
            "D14HTTPFACTORY": ("factory", http.client.HTTPException),
            "D14HTTPREQUEST": ("request", http.client.HTTPException),
            "D14HTTPGET": ("getresponse", http.client.HTTPException),
            "D14HTTPSTATUS": ("status", http.client.HTTPException),
            "D14HTTPREAD": ("read", http.client.HTTPException),
        }
        stage, exception_type = stage_names[fixture_id]
        message = "network-sentinel" if exception_type is OSError else "http-sentinel"
        network = FakeNetwork(
            hooks={
                stage: lambda: _raise(exception_type(message)),
            }
        )
        result, error = self.invoke(
            OllamaHttpTransport(),
            self.direct_request(),
            network,
        )
        self.assertIsNone(result)
        self.assert_clean_transport_error(error)
        self.assertEqual(tuple(network.events), self._exchange_hook_trace(stage))

    def case_unexpected(self, fixture_id: str) -> None:
        for stage in ("factory", "request", "getresponse", "status", "read"):
            with self.subTest(stage=stage):
                sentinel: BaseException
                if fixture_id == "D15UNEXPECTED":
                    sentinel = SentinelError("unexpected-sentinel")
                else:
                    sentinel = KeyboardInterrupt("base-sentinel")
                network = FakeNetwork(
                    hooks={stage: lambda sentinel=sentinel: _raise(sentinel)}
                )
                result, error = self.invoke(
                    OllamaHttpTransport(),
                    self.direct_request(),
                    network,
                )
                self.assertIsNone(result)
                self.assertIs(error, sentinel)
                self.assertEqual(
                    tuple(network.events),
                    self._exchange_hook_trace(stage),
                )

    def case_close(self, fixture_id: str) -> None:
        if fixture_id == "D17CLOSERESP":
            close_error = SentinelError("response-close")
            network = FakeNetwork(
                hooks={
                    "response.close": lambda: _raise(close_error),
                }
            )
            result, error = self.invoke(
                OllamaHttpTransport(),
                self.direct_request(),
                network,
            )
            self.assert_response(result, error)
            self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
            return

        if fixture_id == "D17CLOSECONN":
            close_error = SentinelError("connection-close")
            network = FakeNetwork(
                hooks={
                    "connection.close": lambda: _raise(close_error),
                }
            )
            result, error = self.invoke(
                OllamaHttpTransport(),
                self.direct_request(),
                network,
            )
            self.assert_response(result, error)
            self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
            return

        if fixture_id == "D17CLOSEMAPPED":
            network = FakeNetwork(
                hooks={
                    "read": lambda: _raise(OSError("network-sentinel")),
                    "response.close": lambda: _raise(
                        SentinelError("response-close")
                    ),
                    "connection.close": lambda: _raise(
                        SentinelError("connection-close")
                    ),
                }
            )
            result, error = self.invoke(
                OllamaHttpTransport(),
                self.direct_request(),
                network,
            )
            self.assertIsNone(result)
            self.assert_clean_transport_error(error)
            self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
            return

        if fixture_id == "D17CLOSEUNEXPECTED":
            read_error = SentinelError("read-unexpected")
            network = FakeNetwork(
                hooks={
                    "read": lambda: _raise(read_error),
                    "response.close": lambda: _raise(
                        SentinelError("response-close")
                    ),
                    "connection.close": lambda: _raise(
                        SentinelError("connection-close")
                    ),
                }
            )
            result, error = self.invoke(
                OllamaHttpTransport(),
                self.direct_request(),
                network,
            )
            self.assertIsNone(result)
            self.assertIs(error, read_error)
            self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
            return

        if fixture_id == "D18BASERESP":
            base_error = KeyboardInterrupt("response-base")
            network = FakeNetwork(
                hooks={
                    "response.close": lambda: _raise(base_error),
                }
            )
            result, error = self.invoke(
                OllamaHttpTransport(),
                self.direct_request(),
                network,
            )
            self.assertIsNone(result)
            self.assertIs(error, base_error)
            self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE[:-1])
            return

        base_error = KeyboardInterrupt("connection-base")
        network = FakeNetwork(
            hooks={
                "connection.close": lambda: _raise(base_error),
            }
        )
        result, error = self.invoke(
            OllamaHttpTransport(),
            self.direct_request(),
            network,
        )
        self.assertIsNone(result)
        self.assertIs(error, base_error)
        self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)

    def case_reentrant_factory(self) -> None:
        request = self.direct_request(cloud=True)
        transport = OllamaHttpTransport("token!", 120)

        def mutate() -> None:
            object.__setattr__(request, "body", b"mutated")
            object.__setattr__(transport, "_cloud_api_key", "changed!")
            object.__setattr__(transport, "_timeout_seconds", 121)

        network = FakeNetwork(hooks={"factory": mutate})
        result, error = self.invoke(transport, request, network)
        self.assert_response(result, error)
        expected = (
            ("factory", "https", "ollama.com", 443, 120),
            ("request", "POST", "/api/generate", BODY, CLOUD_HEADERS, False),
            ("getresponse",),
            ("status",),
            ("read", READ_AMOUNT),
            ("response.close",),
            ("connection.close",),
        )
        self.assertEqual(tuple(network.events), expected)
        self.assertEqual(request.body, b"mutated")
        self.assertEqual(transport, OllamaHttpTransport("changed!", 121))

    def case_request_type(self) -> None:
        values: tuple[object, ...] = (
            RequestSubclass(
                method="POST",
                url=LOCAL_URL,
                content_type="application/json",
                body=BODY,
            ),
            {
                "method": "POST",
                "url": LOCAL_URL,
                "content_type": "application/json",
                "body": BODY,
            },
            SlotsDuckRequest(),
        )
        for value in values:
            with self.subTest(value_type=type(value).__name__):
                network = FakeNetwork()
                result, error = self.invoke(OllamaHttpTransport(), value, network)
                self.assertIsNone(result)
                self.assertIs(type(error), TypeError)
                self.assertEqual(network.events, [])

    def case_corruption(self, fixture_id: str) -> None:
        if fixture_id == "D20REQCORRUPT":
            rows = (
                ("method", "GET", ValueError),
                ("url", "http://example.invalid/api/generate", ValueError),
                ("content_type", "text/plain", ValueError),
                ("body", bytearray(BODY), TypeError),
            )
            for field, value, expected_type in rows:
                with self.subTest(field=field):
                    request = self.direct_request()
                    object.__setattr__(request, field, value)
                    network = FakeNetwork()
                    result, error = self.invoke(
                        OllamaHttpTransport(),
                        request,
                        network,
                    )
                    self.assertIsNone(result)
                    self.assertIs(type(error), expected_type)
                    self.assertEqual(network.events, [])
            return

        rows = (
            ("_cloud_api_key", "", ValueError),
            ("_cloud_api_key", b"x", TypeError),
            ("_timeout_seconds", 0, ValueError),
            ("_timeout_seconds", True, TypeError),
        )
        for field, value, expected_type in rows:
            with self.subTest(field=field, value=value):
                transport = OllamaHttpTransport("token!", 120)
                object.__setattr__(transport, field, value)
                network = FakeNetwork()
                result, error = self.invoke(
                    transport,
                    self.direct_request(),
                    network,
                )
                self.assertIsNone(result)
                self.assertIs(type(error), expected_type)
                self.assertEqual(network.events, [])

    def case_no_inspection(self, fixture_id: str) -> None:
        if fixture_id == "D21NOINSPECT":
            status = 200
            body = b"\x1f\x8bopaque"
        else:
            status = 301
            body = b"redirect"
        network = FakeNetwork(
            status=status,
            body=body,
            response_kind="forbidden",
        )
        result, error = self.invoke(
            OllamaHttpTransport(),
            self.direct_request(),
            network,
        )
        self.assert_response(result, error, status=status, body=body)
        self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
        self.assertEqual(
            network.events.count(
                ("request", "POST", "/api/generate", BODY, LOCAL_HEADERS, False)
            ),
            1,
        )

    def case_secrets(self) -> None:
        key = "super-secret!"
        body = b"body-secret"
        transport = OllamaHttpTransport(key)
        captured_log_text: list[str] = []

        def capture_log(
            _logger: object,
            _level: object,
            message: object,
            args: object,
            *unused_args: object,
            **unused_kwargs: object,
        ) -> None:
            captured_log_text.append(str(message))
            captured_log_text.append(repr(args))

        network = FakeNetwork(
            hooks={
                "request": lambda: _raise(OSError("network-sentinel")),
            }
        )
        with patch.object(logging.Logger, "_log", capture_log):
            result, error = self.invoke(
                transport,
                self.direct_request(cloud=True, body=body),
                network,
            )
        self.assertIsNone(result)
        mapped = self.assert_clean_transport_error(error)
        surfaces = (
            repr(transport),
            str(transport),
            repr(mapped),
            str(mapped),
            repr(mapped.args),
            repr(mapped.__cause__),
            repr(mapped.__context__),
            "\n".join(captured_log_text),
        )
        for surface in surfaces:
            self.assertNotIn(key, surface)
            self.assertNotIn(body.decode("ascii"), surface)
        self.assertEqual(captured_log_text, [])
        expected_headers = (
            ("Accept", "application/json"),
            ("Accept-Encoding", "identity"),
            ("Connection", "close"),
            ("Content-Length", "11"),
            ("Content-Type", "application/json"),
            ("Authorization", "Bearer super-secret!"),
        )
        self.assertEqual(
            tuple(network.events),
            (
                ("factory", "https", "ollama.com", 443, 120),
                (
                    "request",
                    "POST",
                    "/api/generate",
                    body,
                    expected_headers,
                    False,
                ),
                ("connection.close",),
            ),
        )

    def case_runtime_boundary(self) -> None:
        network = FakeNetwork()
        forbidden_imports: list[str] = []
        original_import = builtins.__import__

        def guarded_import(
            name: str,
            globals_value: object = None,
            locals_value: object = None,
            fromlist: object = (),
            level: int = 0,
        ) -> object:
            if name.split(".", 1)[0] in {
                "requests",
                "httpx",
                "ollama",
            }:
                forbidden_imports.append(name)
                raise AssertionError("forbidden-sdk-import")
            return original_import(
                name,
                globals_value,  # type: ignore[arg-type]
                locals_value,  # type: ignore[arg-type]
                fromlist,  # type: ignore[arg-type]
                level,
            )

        def forbidden(*_args: object, **_kwargs: object) -> object:
            raise AssertionError("forbidden-runtime-operation")

        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            stack.enter_context(patch.object(builtins, "open", forbidden))
            stack.enter_context(patch.object(builtins, "__import__", guarded_import))
            stack.enter_context(patch.object(os, "getenv", forbidden))
            stack.enter_context(patch.object(os.environ, "get", forbidden))
            stack.enter_context(patch.object(urllib.request, "getproxies", forbidden))
            stack.enter_context(patch.object(urllib.request, "urlopen", forbidden))
            stack.enter_context(patch.object(socket, "create_connection", forbidden))
            stack.enter_context(patch.object(subprocess, "Popen", forbidden))
            stack.enter_context(patch.object(time, "sleep", forbidden))
            stack.enter_context(patch.object(logging.Logger, "_log", forbidden))
            stack.enter_context(patch.object(ollama_module.json, "loads", forbidden))
            stack.enter_context(patch.object(extract_module, "extract_draft", forbidden))
            stack.enter_context(patch.object(pff_validate_module, "validate_package", forbidden))
            stack.enter_context(patch.object(pff_compile_module, "compile_package", forbidden))
            stack.enter_context(patch.object(ground_evaluate_module, "evaluate", forbidden))
            result = OllamaHttpTransport()(self.direct_request())
        self.assertIs(type(result), OllamaTransportResponse)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, RESPONSE_BODY)
        self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)
        self.assertEqual(forbidden_imports, [])
        self.assertEqual(network.events.count(("getresponse",)), 1)

    def case_ast(self) -> None:
        source = Path(ollama_http_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        module_imports: list[tuple[object, ...]] = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                module_imports.append(
                    (
                        "import",
                        node.level if hasattr(node, "level") else 0,
                        tuple((alias.name, alias.asname) for alias in node.names),
                    )
                )
            elif isinstance(node, ast.ImportFrom):
                module_imports.append(
                    (
                        "from",
                        node.level,
                        node.module,
                        tuple((alias.name, alias.asname) for alias in node.names),
                    )
                )
        expected_imports = [
            ("import", 0, (("http.client", None),)),
            ("from", 0, "dataclasses", (("dataclass", None),)),
            (
                "from",
                1,
                "ollama",
                (
                    ("OllamaEndpoint", None),
                    ("OllamaTransportError", None),
                    ("OllamaTransportRequest", None),
                    ("OllamaTransportResponse", None),
                ),
            ),
        ]
        self.assertEqual(module_imports, expected_imports)

        all_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        self.assertEqual(len(all_imports), 3)
        self.assertTrue(all(node in tree.body for node in all_imports))

        call_names = tuple(
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for name in (_dotted_name(node.func),)
            if name is not None
        )
        forbidden_exact = {
            "open",
            "print",
            "eval",
            "exec",
            "compile",
            "__import__",
            "getattr",
            "extract_draft",
            "validate_package",
            "compile_package",
            "evaluate",
        }
        forbidden_roots = {
            "os",
            "pathlib",
            "socket",
            "subprocess",
            "urllib",
            "requests",
            "httpx",
            "ollama",
            "logging",
            "time",
            "random",
            "signal",
            "threading",
            "multiprocessing",
            "importlib",
            "json",
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
        self.assertNotIn("OLLAMA_API_KEY", string_constants)
        self.assert_configuration_ast()
        self.assert_request_snapshot_ast()

    def case_composition(self, fixture_id: str) -> None:
        is_cloud = fixture_id == "D27COMPOSECLOUD"
        endpoint = OllamaEndpoint.CLOUD if is_cloud else OllamaEndpoint.LOCAL
        network = FakeNetwork(body=A01_RESPONSE_BODY)
        transport = (
            OllamaHttpTransport("token!", 37)
            if is_cloud
            else OllamaHttpTransport()
        )
        result, error = self.invoke(
            lambda request: generate_ollama(request, transport=transport),
            self.generate_request(endpoint=endpoint),
            network,
        )
        self.assertIsNone(error)
        envelope = self.assert_a01_envelope(
            result,
            provider_id="ollama-cloud" if is_cloud else "ollama-local",
        )
        self.assertEqual(len(A01_PROMPT), 16)
        self.assertEqual(len(A01_REQUEST_BODY), 68)
        self.assertEqual(len(A01_RESPONSE_BODY), 105)
        self.assertEqual(len(A01_ASSISTANT), 10)
        self.assertEqual(
            "sha256:" + hashlib.sha256(A01_PROMPT).hexdigest(),
            A01_PROMPT_SHA256,
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(A01_REQUEST_BODY).hexdigest(),
            A01_REQUEST_SHA256,
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(A01_RESPONSE_BODY).hexdigest(),
            A01_RESPONSE_SHA256,
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(A01_ASSISTANT).hexdigest(),
            A01_ASSISTANT_SHA256,
        )
        self.assertEqual(envelope.prompt.sha256, A01_PROMPT_SHA256)
        self.assertEqual(envelope.raw_response.sha256, A01_ASSISTANT_SHA256)
        if is_cloud:
            expected_trace = (
                ("factory", "https", "ollama.com", 443, 37),
                (
                    "request",
                    "POST",
                    "/api/generate",
                    A01_REQUEST_BODY,
                    A01_CLOUD_HEADERS,
                    False,
                ),
                ("getresponse",),
                ("status",),
                ("read", READ_AMOUNT),
                ("response.close",),
                ("connection.close",),
            )
            self.assertNotIn("token!", repr(envelope))
            self.assertNotIn("token!", repr(envelope.__dict__) if hasattr(envelope, "__dict__") else "")
        else:
            expected_trace = (
                ("factory", "http", "localhost", 11434, 120),
                (
                    "request",
                    "POST",
                    "/api/generate",
                    A01_REQUEST_BODY,
                    A01_LOCAL_HEADERS,
                    False,
                ),
                ("getresponse",),
                ("status",),
                ("read", READ_AMOUNT),
                ("response.close",),
                ("connection.close",),
            )
        self.assertEqual(tuple(network.events), expected_trace)
        self.assertEqual(network.events.count(expected_trace[1]), 1)

    def case_adapter_limit(self, fixture_id: str) -> None:
        status = 500 if fixture_id == "D28STATUSSIZE" else 200
        body = b"x" * 4_194_305
        network = FakeNetwork(status=status, body=body)
        result, error = self.invoke(
            lambda request: generate_ollama(
                request,
                transport=OllamaHttpTransport(),
            ),
            self.generate_request(),
            network,
        )
        self.assertIsNone(result)
        self.assertIs(type(error), OllamaAdapterError)
        assert isinstance(error, OllamaAdapterError)
        if fixture_id == "D28STATUSSIZE":
            expected = (
                (
                    OllamaAdapterCode.HTTP_STATUS.value,
                    "/status",
                    ("status=500",),
                ),
            )
        else:
            expected = (
                (
                    OllamaAdapterCode.RESPONSE_BODY_LIMIT.value,
                    "/body",
                    (
                        "resource=response_body_bytes",
                        "actual=4194305",
                        "limit=4194304",
                    ),
                ),
            )
        self.assertEqual(_issue_projection(error), expected)
        self.assertEqual(network.events.count(("read", READ_AMOUNT)), 1)
        self.assertEqual(network.events[-2:], [("response.close",), ("connection.close",)])

    def case_fresh_connections(self) -> None:
        network = FakeNetwork()
        transport = OllamaHttpTransport()
        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            first = transport(self.direct_request())
            second = transport(self.direct_request())
        self.assertIs(type(first), OllamaTransportResponse)
        self.assertEqual(first.status, 200)
        self.assertEqual(first.body, RESPONSE_BODY)
        self.assertIs(type(second), OllamaTransportResponse)
        self.assertEqual(second.status, 200)
        self.assertEqual(second.body, RESPONSE_BODY)
        self.assertEqual(len(network.connections), 2)
        self.assertIsNot(network.connections[0], network.connections[1])
        self.assertEqual(len(network.responses), 2)
        self.assertIsNot(network.responses[0], network.responses[1])
        self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE * 2)

    def case_import_boundary(self) -> None:
        network = FakeNetwork()
        environment_reads: list[tuple[object, ...]] = []
        filesystem_calls: list[tuple[object, ...]] = []
        log_calls: list[tuple[object, ...]] = []

        original_get = os.environ.get
        original_open = builtins.open

        def observed_get(*args: object, **kwargs: object) -> object:
            environment_reads.append(args)
            return original_get(*args, **kwargs)

        def observed_open(*args: object, **kwargs: object) -> object:
            filesystem_calls.append(args)
            return original_open(*args, **kwargs)

        def observed_log(*args: object, **kwargs: object) -> None:
            log_calls.append(args)

        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            stack.enter_context(patch.object(os.environ, "get", observed_get))
            stack.enter_context(patch.object(builtins, "open", observed_open))
            stack.enter_context(patch.object(logging.Logger, "_log", observed_log))
            reloaded = importlib.reload(ollama_http_module)
            importlib.reload(generation_package)
            constructed = reloaded.OllamaHttpTransport()
        self.assertIs(type(constructed), reloaded.OllamaHttpTransport)
        self.assertEqual(network.events, [])
        self.assertEqual(network.http_factory_calls, 0)
        self.assertEqual(network.https_factory_calls, 0)
        self.assertEqual(environment_reads, [])
        self.assertEqual(filesystem_calls, [])
        self.assertEqual(log_calls, [])

    def supplemental_key_error_redaction(self) -> None:
        rows: tuple[
            tuple[object, type[BaseException], tuple[str, ...]], ...
        ] = (
            (
                "\ud800surrogate-secret",
                ValueError,
                ("\ud800surrogate-secret", "surrogate-secret"),
            ),
            (
                "cl\u00e9-nonascii-secret",
                ValueError,
                ("cl\u00e9-nonascii-secret", "nonascii-secret"),
            ),
            (
                "invalid secret-value",
                ValueError,
                ("invalid secret-value", "secret-value"),
            ),
            (
                b"bytes-type-secret",
                TypeError,
                ("bytes-type-secret", "b'bytes-type-secret'"),
            ),
            (
                TextSubclass("subclass-type-secret"),
                TypeError,
                ("subclass-type-secret", "'subclass-type-secret'"),
            ),
        )
        network = FakeNetwork()
        with ExitStack() as stack:
            for fake_patch in network.patches():
                stack.enter_context(fake_patch)
            for value, expected_type, forbidden_tokens in rows:
                with self.subTest(value_type=type(value).__name__):
                    error = self.assert_exact_error(
                        expected_type,
                        lambda value=value: OllamaHttpTransport(value),
                    )
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                    surfaces = (
                        str(error),
                        repr(error),
                        repr(error.args),
                        repr(error.__cause__),
                        repr(error.__context__),
                    )
                    for surface in surfaces:
                        for token in forbidden_tokens:
                            self.assertNotIn(token, surface)
        self.assertEqual(network.events, [])
        self.assertEqual(network.http_factory_calls, 0)
        self.assertEqual(network.https_factory_calls, 0)

    def supplemental_no_public_credential_surface(self) -> None:
        transport = OllamaHttpTransport("surface-secret~")
        class_public = tuple(
            sorted(
                name
                for name in vars(OllamaHttpTransport)
                if not name.startswith("_")
            )
        )
        instance_public = tuple(
            sorted(name for name in dir(transport) if not name.startswith("_"))
        )
        self.assertEqual(class_public, ())
        self.assertEqual(instance_public, ())
        self.assertFalse(hasattr(transport, "__dict__"))
        self.assertNotIn("surface-secret~", repr(transport))
        self.assertNotIn("surface-secret~", str(transport))

    def supplemental_opaque_authorization_key(self) -> None:
        key = "MiXeD-._~!$&'()*+,;=:@"
        headers = LOCAL_HEADERS + (("Authorization", "Bearer " + key),)
        network = FakeNetwork()
        result, error = self.invoke(
            OllamaHttpTransport(key),
            self.direct_request(cloud=True),
            network,
        )
        self.assert_response(result, error)
        self.assertEqual(
            tuple(network.events),
            (
                ("factory", "https", "ollama.com", 443, 120),
                (
                    "request",
                    "POST",
                    "/api/generate",
                    BODY,
                    headers,
                    False,
                ),
                ("getresponse",),
                ("status",),
                ("read", READ_AMOUNT),
                ("response.close",),
                ("connection.close",),
            ),
        )
        authorization = network.events[1][4][-1]  # type: ignore[index]
        self.assertEqual(authorization, ("Authorization", "Bearer " + key))

    def supplemental_timeout_upper_bound(self) -> None:
        network = FakeNetwork()
        result, error = self.invoke(
            OllamaHttpTransport(timeout_seconds=600),
            self.direct_request(),
            network,
        )
        self.assert_response(result, error)
        expected = (
            ("factory", "http", "localhost", 11434, 600),
            *LOCAL_SUCCESS_TRACE[1:],
        )
        self.assertEqual(tuple(network.events), expected)

    def supplemental_status_boundaries(self) -> None:
        for status in (100, 599):
            with self.subTest(status=status):
                network = FakeNetwork(status=status)
                result, error = self.invoke(
                    OllamaHttpTransport(),
                    self.direct_request(),
                    network,
                )
                self.assert_response(result, error, status=status)
                self.assertEqual(tuple(network.events), LOCAL_SUCCESS_TRACE)

    def supplemental_recognized_error_freshness(self) -> None:
        transport = OllamaHttpTransport()
        first_network = FakeNetwork(
            hooks={
                "factory": lambda: _raise(OSError("network-sentinel")),
            }
        )
        first_result, first_error = self.invoke(
            transport,
            self.direct_request(),
            first_network,
        )
        second_network = FakeNetwork(
            hooks={
                "read": lambda: _raise(
                    http.client.HTTPException("http-sentinel")
                ),
            }
        )
        second_result, second_error = self.invoke(
            transport,
            self.direct_request(),
            second_network,
        )
        self.assertIsNone(first_result)
        self.assertIsNone(second_result)
        first_mapped = self.assert_clean_transport_error(first_error)
        second_mapped = self.assert_clean_transport_error(second_error)
        self.assertIsNot(first_mapped, second_mapped)
        self.assertEqual(tuple(first_network.events), LOCAL_SUCCESS_TRACE[:1])
        self.assertEqual(
            tuple(second_network.events),
            LOCAL_SUCCESS_TRACE[:5]
            + (("response.close",), ("connection.close",)),
        )

    def test_accepted_profile_and_reviewed_candidate_identities_are_pinned(self) -> None:
        profile_path = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "PFF_OLLAMA_HTTP_TRANSPORT_PROFILE_V0.1.md"
        )
        accepted = profile_path.read_bytes()
        self.assertEqual(hashlib.sha256(accepted).hexdigest(), ACCEPTED_PROFILE_SHA256)

        record = (
            "\n## 14. Acceptance record\n\n"
            "```text\n"
            "profile: pff-ollama-http-transport/0.1\n"
            "status: accepted\n"
            "accepted_on: 2026-08-18\n"
            "reviewed_candidate_sha256: sha256:"
            + REVIEWED_CANDIDATE_SHA256
            + "\n"
            "review_result: architecture=clean; semantic_audit=clean; "
            "test_design=clean\n"
            "```\n"
        ).encode("utf-8")
        self.assertTrue(accepted.endswith(record))
        candidate = accepted[: -len(record)]
        accepted_status = b"**Status:** ACCEPTED  \n"
        candidate_status = "**Status:** CANDIDATE \u2014 NOT ACCEPTED  \n".encode("utf-8")
        self.assertEqual(candidate.count(accepted_status), 1)
        candidate = candidate.replace(accepted_status, candidate_status, 1)
        self.assertEqual(
            hashlib.sha256(candidate).hexdigest(),
            REVIEWED_CANDIDATE_SHA256,
        )

    def test_profile_fixtures_are_defined_dispatched_and_executed(self) -> None:
        self.assertEqual(len(DEFINED_IDS), 58)
        dispatch: dict[str, object] = {}

        def register(fixture_id: str, operation: object) -> None:
            self.assertNotIn(fixture_id, dispatch)
            dispatch[fixture_id] = operation

        register("D01API", self.case_api)
        for fixture_id in ("D02KEYOK", "D02KEYTYPE", "D02KEYVALUE"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_key(fixture_id),
            )
        for fixture_id in ("D03TIMEOK", "D03TIMETYPE", "D03TIMEVALUE"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_timeout(fixture_id),
            )
        for fixture_id in ("D04LOCAL", "D05CLOUD", "D06NOKEY", "D07LOCALKEY"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_canonical(fixture_id),
            )
        for fixture_id in ("D08EMPTYBODY", "D08ONEBODY", "D08BIGBODY"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_body(fixture_id),
            )
        register("D09STATUS", self.case_status)
        for fixture_id in (
            "D10BODYZERO",
            "D10BODYMAX",
            "D10BODYSENTINEL",
            "D10BODYOVERFAKE",
        ):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_response_body(fixture_id),
            )
        for fixture_id in ("D11STATUSBAD", "D11BODYBAD"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_bad_return(fixture_id),
            )
        for fixture_id in ("D12MISSSTATUS", "D12MISSREAD"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_missing_shape(fixture_id),
            )
        for fixture_id in (
            "D13OSFACTORY",
            "D13OSREQUEST",
            "D13OSGET",
            "D13OSSTATUS",
            "D13OSREAD",
            "D14HTTPFACTORY",
            "D14HTTPREQUEST",
            "D14HTTPGET",
            "D14HTTPSTATUS",
            "D14HTTPREAD",
        ):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_recognized_error(fixture_id),
            )
        for fixture_id in ("D15UNEXPECTED", "D16BASE"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_unexpected(fixture_id),
            )
        for fixture_id in (
            "D17CLOSERESP",
            "D17CLOSECONN",
            "D17CLOSEMAPPED",
            "D17CLOSEUNEXPECTED",
            "D18BASERESP",
            "D18BASECONN",
        ):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_close(fixture_id),
            )
        register("D19REFACTORY", self.case_reentrant_factory)
        register("D19ASTCONFIG", self.assert_configuration_ast)
        register("D19ASTREQUEST", self.assert_request_snapshot_ast)
        register("D20REQTYPE", self.case_request_type)
        for fixture_id in ("D20REQCORRUPT", "D20CFGCORRUPT"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_corruption(fixture_id),
            )
        for fixture_id in ("D21NOINSPECT", "D22REDIRECT"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_no_inspection(fixture_id),
            )
        register("D23SECRETS", self.case_secrets)
        register("D24RUNTIME", self.case_runtime_boundary)
        register("D25AST", self.case_ast)
        for fixture_id in ("D26COMPOSELOCAL", "D27COMPOSECLOUD"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_composition(fixture_id),
            )
        for fixture_id in ("D28STATUSSIZE", "D28OKSIZE"):
            register(
                fixture_id,
                lambda fixture_id=fixture_id: self.case_adapter_limit(fixture_id),
            )
        register("D29FRESH", self.case_fresh_connections)
        register("D30IMPORT", self.case_import_boundary)

        dispatched_ids = frozenset(dispatch)
        self.assertEqual(len(dispatched_ids), 58)
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
        self.assertEqual(len(MUTATION_IDS), 62)
        self.assertEqual(MUTATION_IDS, frozenset(MUTATION_TARGETS))
        self.assertEqual(len(MUTATION_TARGETS), 62)
        for mutation_id, target in MUTATION_TARGETS.items():
            with self.subTest(mutation_id=mutation_id):
                self.assertIs(type(target), tuple)
                self.assertEqual(len(target), 2)
                fixture_id, assertion_name = target
                self.assertIn(fixture_id, DEFINED_IDS)
                self.assertIs(type(assertion_name), str)
                self.assertTrue(assertion_name)

    def test_supplemental_regressions_are_defined_dispatched_and_executed(self) -> None:
        dispatch = {
            "S01KEYERROR": self.supplemental_key_error_redaction,
            "S02NOSURFACE": self.supplemental_no_public_credential_surface,
            "S03KEYOPAQUE": self.supplemental_opaque_authorization_key,
            "S04TIME600": self.supplemental_timeout_upper_bound,
            "S05STATUSBOUNDS": self.supplemental_status_boundaries,
            "S06FRESHERROR": self.supplemental_recognized_error_freshness,
        }
        dispatched_ids = frozenset(dispatch)
        self.assertEqual(len(SUPPLEMENTAL_FIXTURE_IDS), 6)
        self.assertEqual(SUPPLEMENTAL_FIXTURE_IDS, dispatched_ids)

        executed_ids: set[str] = set()
        for fixture_id in sorted(SUPPLEMENTAL_FIXTURE_IDS):
            with self.subTest(fixture_id=fixture_id):
                try:
                    dispatch[fixture_id]()
                finally:
                    executed_ids.add(fixture_id)
        self.assertEqual(dispatched_ids, frozenset(executed_ids))

    def test_supplemental_mutation_manifest_is_exact_and_closed(self) -> None:
        self.assertEqual(len(SUPPLEMENTAL_MUTATION_IDS), 7)
        self.assertEqual(
            SUPPLEMENTAL_MUTATION_IDS,
            frozenset(SUPPLEMENTAL_MUTATION_TARGETS),
        )
        target_fixture_ids = DEFINED_IDS | SUPPLEMENTAL_FIXTURE_IDS
        for mutation_id, target in SUPPLEMENTAL_MUTATION_TARGETS.items():
            with self.subTest(mutation_id=mutation_id):
                self.assertIs(type(target), tuple)
                self.assertEqual(len(target), 2)
                fixture_id, assertion_name = target
                self.assertIn(fixture_id, target_fixture_ids)
                self.assertIs(type(assertion_name), str)
                self.assertTrue(assertion_name)


if __name__ == "__main__":
    unittest.main()
