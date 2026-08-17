"""Concrete standard-library HTTP transport for Ollama generation."""

import http.client
from dataclasses import dataclass

from .ollama import (
    OllamaEndpoint,
    OllamaTransportError,
    OllamaTransportRequest,
    OllamaTransportResponse,
)


__all__ = ("OllamaHttpTransport",)


def _validate_cloud_api_key(value: str | None) -> None:
    if value is None:
        return
    if type(value) is not str:
        raise TypeError("cloud_api_key must be a string or None")
    if (
        not value
        or len(value) > 4_096
        or any(not 0x21 <= ord(character) <= 0x7E for character in value)
    ):
        raise ValueError("cloud_api_key must be visible ASCII within its limit")


def _validate_timeout_seconds(value: int) -> None:
    if type(value) is not int:
        raise TypeError("timeout_seconds must be an integer")
    if not 1 <= value <= 600:
        raise ValueError("timeout_seconds must be in 1..600")


def _close(subject: object) -> None:
    try:
        subject.close()
    except Exception:
        pass


@dataclass(frozen=True, slots=True, repr=False, init=False)
class OllamaHttpTransport:
    _cloud_api_key: str | None
    _timeout_seconds: int

    __hash__ = None

    def __init__(
        self,
        cloud_api_key: str | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        _validate_cloud_api_key(cloud_api_key)
        _validate_timeout_seconds(timeout_seconds)
        object.__setattr__(self, "_cloud_api_key", cloud_api_key)
        object.__setattr__(self, "_timeout_seconds", timeout_seconds)

    def __call__(
        self,
        request: OllamaTransportRequest,
        /,
    ) -> OllamaTransportResponse:
        if type(request) is not OllamaTransportRequest:
            raise TypeError("request must be an OllamaTransportRequest")

        cloud_api_key = self._cloud_api_key
        timeout_seconds = self._timeout_seconds
        _validate_cloud_api_key(cloud_api_key)
        _validate_timeout_seconds(timeout_seconds)
        snapshot = OllamaTransportRequest(
            method=request.method,
            url=request.url,
            content_type=request.content_type,
            body=request.body,
        )

        is_cloud = snapshot.url == OllamaEndpoint.CLOUD.value
        if is_cloud:
            if cloud_api_key is None:
                raise OllamaTransportError()
            authorization = cloud_api_key
        else:
            authorization = None

        body = snapshot.body
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
            "Content-Length": str(len(body)),
            "Content-Type": "application/json",
        }
        if authorization is not None:
            headers["Authorization"] = "Bearer " + authorization

        connection = None
        response = None
        status = 0
        response_body = b""
        transport_failed = False
        try:
            try:
                if is_cloud:
                    connection = http.client.HTTPSConnection(
                        "ollama.com",
                        443,
                        timeout=timeout_seconds,
                    )
                else:
                    connection = http.client.HTTPConnection(
                        "localhost",
                        11434,
                        timeout=timeout_seconds,
                    )
            except (OSError, http.client.HTTPException):
                transport_failed = True

            if not transport_failed:
                try:
                    connection.request(
                        "POST",
                        "/api/generate",
                        body=body,
                        headers=headers,
                        encode_chunked=False,
                    )
                except (OSError, http.client.HTTPException):
                    transport_failed = True

            if not transport_failed:
                try:
                    response = connection.getresponse()
                except (OSError, http.client.HTTPException):
                    transport_failed = True

            if not transport_failed:
                try:
                    status = response.status
                except (OSError, http.client.HTTPException):
                    transport_failed = True
                else:
                    if type(status) is not int or not 100 <= status <= 599:
                        transport_failed = True

            if not transport_failed:
                try:
                    response_body = response.read(4_194_305)
                except (OSError, http.client.HTTPException):
                    transport_failed = True
                else:
                    if (
                        type(response_body) is not bytes
                        or len(response_body) > 4_194_305
                    ):
                        transport_failed = True
        finally:
            if response is not None:
                _close(response)
            if connection is not None:
                _close(connection)

        if transport_failed:
            raise OllamaTransportError()
        return OllamaTransportResponse(status=status, body=response_body)
