# PFF Ollama HTTP Transport Profile v0.1

**Status:** ACCEPTED  
**Scope:** concrete standard-library HTTP transport for the accepted Ollama adapter only  
**Repository baseline:** `4e4427aef3e37c29d1ed9189d9488094fdbb8f18`  
**Controlling adapter profile:** `PFF_OLLAMA_ADAPTER_PROFILE_V0.1.md`,
SHA-256 `9bc104160727dcc51ef4ddce6044e5dda81200ac51dc3a9394533cecc2ea433c`

## 1. Purpose, authority, and boundary

This profile freezes one optional concrete transport below the already accepted
pure adapter:

```text
OllamaGenerateRequest
    -> generate_ollama
    -> OllamaTransportRequest
    -> OllamaHttpTransport
    -> one HTTP exchange
    -> OllamaTransportResponse
    -> GenerationEnvelope
```

The accepted adapter remains the only owner of request JSON, response semantics,
diagnostics, and capture. This transport owns only connection selection,
credential injection, request framing, one bounded response read, cleanup, and
translation of recognized network failures. It never interprets provider JSON
and never constructs a generation envelope itself.

The authority order is:

1. the accepted adapter profile controls all imported adapter types and
   semantics;
2. this profile controls the concrete transport behavior stated below; and
3. the dated official Ollama and Python documentation in section 11 is evidence,
   not authority over unspecified client policy.

Every new decision in this document is `[N]`. There are no `[S]` or `[C]`
claims beyond exact references to the controlling profile, and no `[D]` rule is
implemented here. The profile identity is `pff-ollama-http-transport/0.1`.

The implementation module is `poietics.generation.ollama_http`. Dependency is
one-way: `ollama_http -> ollama`. The accepted `ollama` module and the inert
`poietics.generation` initializer do not import this concrete transport.

## 2. Public API and construction

The later implementation defines `__all__ = ("OllamaHttpTransport",)` and
exposes exactly one supported public name:

```python
@dataclass(frozen=True, slots=True, repr=False, init=False)
class OllamaHttpTransport:
    _cloud_api_key: str | None
    _timeout_seconds: int

    __hash__ = None

    def __init__(
        self,
        cloud_api_key: str | None = None,
        timeout_seconds: int = 120,
    ) -> None: ...

    def __call__(
        self,
        request: OllamaTransportRequest,
        /,
    ) -> OllamaTransportResponse: ...
```

The stored credential and timeout fields are private. Generated `repr` is
disabled, field assignment fails, and instances are unhashable. No public
property returns the credential. Generated equality remains enabled and
compares both private fields exactly; it is not an authentication or
constant-time comparison interface.

`cloud_api_key` is either `None` or an exact `str`. A present value:

- is nonempty;
- contains only U+0021 through U+007E inclusive;
- is at most 4,096 UTF-8 bytes; and
- is copied as the immutable string value without normalization or trimming.

A wrong exact type raises `TypeError`; an empty, non-visible-ASCII, control,
space, non-ASCII, or oversized value raises `ValueError`. These restrictions
prevent header injection; they are not claimed to reproduce an undocumented
Ollama token grammar.

`timeout_seconds` is an exact `int` in `1..600`. `bool`, int subclasses, and
other types raise `TypeError`; values outside the range raise `ValueError`.

Construction performs no environment, file, keyring, network, DNS, or TLS
operation. In particular, it never reads `OLLAMA_API_KEY`. Supplying a key is an
explicit caller responsibility. No key appears in transport-generated `repr`,
`str`, exception text, exception arguments, diagnostics, response records, or
generation envelopes. An arbitrary unexpected exception supplied by patched or
foreign code propagates by identity under section 7 and is outside that output
guarantee; the transport itself never adds the key to it.

## 3. Invocation prevalidation and snapshots

Each call first requires `type(request) is OllamaTransportRequest`; subclasses,
mappings, and duck types raise `TypeError`. Before any connection factory is
called, the transport:

1. reads its private credential and timeout exactly once into local immutable
   values and revalidates them with the constructor rules;
2. revalidates every request field under the controlling adapter contract; and
3. constructs a fresh exact `OllamaTransportRequest` snapshot.

Thus low-level mutation through `object.__setattr__` to an invalid value is
rejected before I/O. A valid-to-valid mutation is indistinguishable from
ordinary current state and is accepted, then snapshotted.
After snapshotting, the transport never rereads the caller request or its own
fields. A re-entrant connection factory can mutate those objects but cannot
change the outbound bytes, authorization value, timeout, or returned record for
the active call. Later HTTP callbacks receive no caller request or transport
object from production; the same no-reread rule is enforced statically.

For a cloud URL with no snapshotted credential, the call raises a fresh
`OllamaTransportError()` before either connection factory is called. A local
request never requires or sends a credential, even when the transport was
constructed with one.

All prevalidation failures have zero connection-factory, request,
`getresponse`, read, and close calls.

## 4. Endpoint and connection mapping

Only the exact URLs already admitted by `OllamaTransportRequest` are supported:

| Request URL | Fresh connection constructor |
|---|---|
| `http://localhost:11434/api/generate` | `http.client.HTTPConnection("localhost", 11434, timeout=TIMEOUT)` |
| `https://ollama.com/api/generate` | `http.client.HTTPSConnection("ollama.com", 443, timeout=TIMEOUT)` |

`TIMEOUT` is the snapshotted integer. HTTPS uses the standard-library default
TLS context and hostname verification supplied by `HTTPSConnection`; callers
cannot inject a context, host, port, path, proxy, or connection object.

Each invocation constructs exactly one new connection. There is no pool,
reuse, transport-selected alternate endpoint or host, failover, proxy lookup,
redirect following, application-level retry, backoff, sleep, or second HTTP
request. The standard connection may try multiple address records returned by
name resolution as part of that one connection attempt. An HTTP redirect,
rate-limit, or server error is an ordinary response status and is returned to
the adapter.

## 5. Exact request operation

The transport invokes the new connection exactly once as follows, where `BODY`
is the snapshotted `request.body` without transformation:

```python
connection.request(
    "POST",
    "/api/generate",
    body=BODY,
    headers=HEADERS,
    encode_chunked=False,
)
```

The exact `HEADERS` mapping passed to `http.client` contains these string pairs:

| Header | Local | Cloud |
|---|---|---|
| `Accept` | `application/json` | `application/json` |
| `Accept-Encoding` | `identity` | `identity` |
| `Connection` | `close` | `close` |
| `Content-Length` | exact ASCII decimal `len(BODY)` | exact ASCII decimal `len(BODY)` |
| `Content-Type` | `application/json` | `application/json` |
| `Authorization` | absent | `Bearer ` plus the snapshotted key |

There are no other entries in the mapping. Map insertion order is exactly the
table order, with `Authorization` last for cloud. `http.client` may add the
protocol-required `Host` header on the wire; the transport does not supply or
override it. Explicit `Content-Length` and `encode_chunked=False` forbid
chunked request framing. Empty and arbitrarily large adapter request bodies are
sent unchanged; this profile adds no prompt or request-body limit.

The transport then calls `connection.getresponse()` exactly once.

## 6. Bounded response and returned record

After `getresponse` succeeds, the transport reads the response exactly once:

```python
body = response.read(4_194_305)
```

This is the accepted adapter's 4,194,304-byte maximum plus one sentinel byte.
The transport never calls an unbounded `read`, never directly reads or derives
an allocation/read size from `Content-Length`, and never decompresses a content
encoding. Standard `http.client` transfer-framing decoding and its own framing
completeness behavior remain in force; the transport adds no second
completeness probe. The returned body is
therefore the exact available prefix of at most 4,194,305 bytes. A larger body
is intentionally not drained; adapter status-before-size precedence remains
authoritative.

The transport reads and validates `response.status` before calling `read`. It
must be an exact `int` in `100..599`; an invalid value becomes a fresh
`OllamaTransportError()` and suppresses the read. With a valid status, the read
result must be exact `bytes` of at most 4,194,305 bytes; an invalid type or
overlong fake result becomes a fresh `OllamaTransportError()`. Missing
`status`, `read`, or other ordinary shape members naturally raises
`AttributeError`, which is an unexpected exception and propagates unchanged.
No response `Content-Type`, headers, reason phrase, URL, or request identifier
is read or retained.

On a valid status and body, the transport constructs and returns exactly:

```python
OllamaTransportResponse(status=status, body=body)
```

Statuses including 201, 301, 400, 404, 429, 500, and 502 are not interpreted or
followed. The accepted adapter decides whether the status or body is valid.

## 7. Failure translation and cleanup

The recognized exchange failures are `OSError` and
`http.client.HTTPException` raised while:

- constructing the selected connection;
- calling `request`;
- calling `getresponse`;
- reading `response.status`; or
- calling `response.read`.

Each recognized failure yields one newly constructed `OllamaTransportError()`.
The raise occurs outside the caught exception handler, with no cause or context,
so provider body bytes, request bytes, hosts, and credentials cannot survive in
an exception chain. There is no retry and no partial response.

Every other `Exception`, including a test sentinel or programmer error, and
every `BaseException` outside `Exception`, propagates as the identical object.
The transport does not wrap it.

Cleanup begins after the exchange outcome is known. If a response object was
obtained, `response.close()` is attempted first. If a connection object was
created, `connection.close()` is attempted second. Each applicable close is
called once by `OllamaHttpTransport`; any internal close performed by
`http.client` is outside that count. A helper catches and suppresses only
ordinary `Exception` from a close, so such cleanup failure never replaces a
successful response, a mapped network failure, or an unchanged unexpected
exception, and cleanup continues.
A `BaseException` from a close is not caught: it propagates immediately under
normal Python exception precedence and may prevent the later close.

Connection-constructor failure creates no object and has no close. Request or
`getresponse` failure closes only the connection. Status/read failure closes
the response and then the connection. Cleanup never causes retry or a second
read.

`OllamaTransportError` retains the accepted fixed message only. The concrete
transport does not introduce a diagnostic enum or provider-specific error
payload.

## 8. Dependency, I/O, and security boundary

Production imports are exactly:

```python
import http.client
from dataclasses import dataclass

from .ollama import (
    OllamaEndpoint,
    OllamaTransportError,
    OllamaTransportRequest,
    OllamaTransportResponse,
)
```

No other transport-authored import, dynamic import, module lookup, callback
registry, SDK, parser, extractor, PFF, ground, provider library, environment,
filesystem, logging, metrics, tracing, random, clock, signal, thread, process,
or sleep operation is allowed. The only transport-authored ambient I/O is the
selected `http.client` connection. Standard `HTTPSConnection` may use platform
name resolution, trust stores, and TLS configuration internally; this profile
does not claim to replace or suppress those standard-library/platform effects.

Default tests and qualification patch both connection classes with inert fakes.
They never open a socket, perform DNS/TLS, read a credential, or call Ollama.
The supplied or deployment API key is never a fixture and never enters source,
Git, test output, mutation evidence, or an acceptance record.

The later implementation gate may change exactly:

- `src/poietics/generation/ollama_http.py`;
- `tests/test_generation_ollama_http.py`; and
- `README.md`.

The accepted adapter, package initializer, packaging metadata, every other
generation file, PFF, ground, and all other repository paths remain
byte-identical to the published baseline.

## 9. Executable conformance manifest

Every expected request, mapping, byte string, event sequence, exception, and
returned record is literal test data. Tests may not call production helpers to
calculate expectations.

### 9.1 Canonical fake language and literals

Tests replace the two attributes `ollama_http.http.client.HTTPConnection` and
`HTTPSConnection` with independent factories. A factory accepts exactly
`(host, port, *, timeout)` and appends this event before returning a connection:

```text
("factory", "http"|"https", HOST, PORT, TIMEOUT)
```

The connection implements only `request`, `getresponse`, and `close`. The
response implements a logging `status` property, `read`, and `close`. Each
transport-issued call appends exactly one of:

```text
("request", METHOD, PATH, BODY, tuple(HEADERS.items()), ENCODE_CHUNKED)
("getresponse",)
("status",)
("read", AMOUNT)
("response.close",)
("connection.close",)
```

A hook is independently assigned to factory, request, getresponse, status,
read, response-close, or connection-close. Its exact actions are `return`,
`raise OSError("network-sentinel")`,
`raise http.client.HTTPException("http-sentinel")`, raise one preconstructed
`SentinelError("unexpected-sentinel")`, raise one preconstructed
`KeyboardInterrupt("base-sentinel")`, or perform the exact re-entrant mutation
named by a fixture and then return. `SentinelError` is a test-local exact
`Exception` subclass. Tests assert exception identity where required.

The canonical direct requests and immutable expected mappings are:

```text
BODY = b'{"x":1}'
RESPONSE_BODY = b'{"ok":true}'

LOCAL_REQUEST = OllamaTransportRequest(
    method="POST",
    url="http://localhost:11434/api/generate",
    content_type="application/json",
    body=BODY,
)
CLOUD_REQUEST = same fields except url="https://ollama.com/api/generate"

LOCAL_HEADERS = (
    ("Accept", "application/json"),
    ("Accept-Encoding", "identity"),
    ("Connection", "close"),
    ("Content-Length", "7"),
    ("Content-Type", "application/json"),
)
CLOUD_HEADERS = LOCAL_HEADERS + (("Authorization", "Bearer token!"),)
```

The literal successful local trace is:

```text
("factory", "http", "localhost", 11434, 120)
("request", "POST", "/api/generate", BODY, LOCAL_HEADERS, False)
("getresponse",)
("status",)
("read", 4194305)
("response.close",)
("connection.close",)
```

The cloud trace substitutes `("factory","https","ollama.com",443,37)` and
`CLOUD_HEADERS`. Success returns exact
`OllamaTransportResponse(status=200, body=RESPONSE_BODY)`. No fake has any
header/reason/URL/request-ID property unless a fixture explicitly supplies a
property that raises `AssertionError("forbidden-response-inspection")`.

The composition fixtures reuse the controlling adapter A01 literals verbatim:
`AttemptRef("session:ollama",1)`, `INITIAL`, no parent, model `test-model`,
template `pff-draft-prompt@1`, and the 16 prompt bytes/digest stated there. The
exact outbound body is its 68 bytes, SHA-256
`65b830219043a20ba744248c7f50f0159b76dd12d7a30385bc3c0ccc8487907f`.
The fake returns its exact status-200 105-byte body, SHA-256
`d86ec9c69622d356a1928c852a94ed47d92a0fb09911dae66c7514748ac9d232`.
The expected envelope is A01's complete literal projection, including the
10-byte assistant with digest
`db4f81d3aa274d3de4a249fa9d092b97d35ef6cb6b0d2fe786a5f7e2ba734d9f`;
local provider is `ollama-local`, cloud provider is `ollama-cloud`, and the sole
public parameter is `stream=false`.

### 9.2 Exact fixture population

Each table row is one independently dispatched fixture. A row that names
several values is table-driven and must record one executed subtest and exact
outcome for every listed value; the row itself fails if any member is omitted.

| ID | Exact construction and named observable |
|---|---|
| D01API | `__all__ == ("OllamaHttpTransport",)`; exact private slots are `_cloud_api_key`,`_timeout_seconds`; assignment/deletion raises exact `dataclasses.FrozenInstanceError`; hash raises TypeError; repr/str contain neither private field name nor `token!` and are not dataclass field reprs; equality is true only for the same two exact field values. |
| D02KEYOK | Keys `None`, `!`, and `A` repeated 4,096 construct; zero fake calls. |
| D02KEYTYPE | Key values `b"x"`, a `str` subclass, and `1` each raise TypeError; zero fake calls. |
| D02KEYVALUE | Key values `""`, space, DEL, LF, `é`, and `A` repeated 4,097 each raise ValueError; zero fake calls. |
| D03TIMEOK | Timeouts 1, 120, and 600 construct and retain exact equality distinctions; zero fake calls. |
| D03TIMETYPE | `True`, an int subclass, and `1.0` each raise TypeError; zero fake calls. |
| D03TIMEVALUE | 0, -1, and 601 each raise ValueError; zero fake calls. |
| D04LOCAL | Canonical local success has exactly the literal local trace and response record; HTTPS factory count is zero. |
| D05CLOUD | `token!`, timeout 37, canonical cloud success has exactly the literal cloud trace and response; HTTP factory count is zero. |
| D06NOKEY | Canonical cloud request with no key raises a fresh fixed-text OllamaTransportError with no cause/context and an empty trace. |
| D07LOCALKEY | Local transport with key `local-secret!` has LOCAL_HEADERS exactly and the secret is absent from returned/public surfaces. |
| D08EMPTYBODY | Direct local request body `b""` has Content-Length `0` and is passed unchanged. |
| D08ONEBODY | Direct local request body `b"x"` has Content-Length `1` and is passed unchanged. |
| D08BIGBODY | Direct local request body `b"x"*100000` has Content-Length `100000` and is passed unchanged. |
| D09STATUS | Each exact status 201,301,400,404,429,500,502 returns unchanged with RESPONSE_BODY and exactly the success trace. |
| D10BODYZERO | Status 200/body `b""` returns exactly and read event is `("read",4194305)`. |
| D10BODYMAX | Status 200/body `b"x"*4194304` returns exactly after one bounded read. |
| D10BODYSENTINEL | Status 200/body `b"x"*4194305` returns exactly after one bounded read and no drain. |
| D10BODYOVERFAKE | Fake read returns `b"x"*4194306`; fresh transport error, response then connection cleanup, no record. |
| D11STATUSBAD | Status values `True`, an int subclass, 99, and 600 each map to fresh transport error after `status`; `read` is absent; both closes occur. |
| D11BODYBAD | Read values `bytearray(b"x")` and a bytes subclass each map to fresh transport error after the one read and both closes. |
| D12MISSSTATUS | Exact response object has `read`/`close` but no `status`; its AttributeError propagates, no read, then response/connection close. |
| D12MISSREAD | Exact response object has status 200/close but no `read`; its AttributeError propagates after status, then both closes. |
| D13OSFACTORY | OSError factory hook maps to fresh clean-chain transport error; trace is only the factory event. |
| D13OSREQUEST | OSError request hook maps; trace ends with one connection close. |
| D13OSGET | OSError getresponse hook maps; trace ends with one connection close. |
| D13OSSTATUS | OSError status hook maps; trace ends response-close then connection-close; no read. |
| D13OSREAD | OSError read hook maps; trace ends response-close then connection-close. |
| D14HTTPFACTORY | HTTPException factory hook has the same mapping and factory-only trace. |
| D14HTTPREQUEST | HTTPException request hook maps with one connection close. |
| D14HTTPGET | HTTPException getresponse hook maps with one connection close. |
| D14HTTPSTATUS | HTTPException status hook maps with both closes and no read. |
| D14HTTPREAD | HTTPException read hook maps with both closes. |
| D15UNEXPECTED | At each of factory,request,getresponse,status,read, one preconstructed SentinelError propagates by identity; each exact reached trace/cleanup prefix is asserted. |
| D16BASE | At each of factory,request,getresponse,status,read, one preconstructed KeyboardInterrupt propagates by identity; each exact reached trace/cleanup prefix is asserted. |
| D17CLOSERESP | On successful exchange, response-close SentinelError is suppressed, connection close occurs, exact response returns. |
| D17CLOSECONN | On successful exchange, connection-close SentinelError is suppressed and exact response returns. |
| D17CLOSEMAPPED | Read OSError plus ordinary errors from both closes yields only fresh clean-chain transport error and both close events. |
| D17CLOSEUNEXPECTED | Read SentinelError plus ordinary errors from both closes preserves the identical read sentinel and both close events. |
| D18BASERESP | Response-close KeyboardInterrupt propagates by identity and prevents the connection-close event. |
| D18BASECONN | Connection-close KeyboardInterrupt propagates by identity after response close. |
| D19REFACTORY | Cloud factory hook changes caller body to `b"mutated"`, transport key to `changed!`, timeout to 121; factory args/request still use original 120, `token!`, BODY. |
| D19ASTCONFIG | In `OllamaHttpTransport.__call__`, AST Load nodes for `self._cloud_api_key` and `self._timeout_seconds` each occur exactly once and precede either connection-factory call. |
| D19ASTREQUEST | After the statement assigning the fresh `OllamaTransportRequest` snapshot, the remaining `__call__` AST contains zero Load nodes for the caller parameter `request`. |
| D20REQTYPE | Request subclass, mapping, and slots duck each raise TypeError with empty trace. |
| D20REQCORRUPT | Exact request separately corrupted to method `GET`, unknown URL, wrong content type, or bytearray body raises controlling TypeError/ValueError with empty trace. |
| D20CFGCORRUPT | Exact transport separately corrupted to empty/bytes key or timeout 0/bool raises constructor-equivalent TypeError/ValueError with empty trace. |
| D21NOINSPECT | Forbidden response properties all raise if touched; canonical gzip-looking body `b"\x1f\x8bopaque"` returns byte-identically. |
| D22REDIRECT | Status 301/body `b"redirect"` and a forbidden Location property return exact record after one request and no property access. |
| D23SECRETS | Key `super-secret!` and body `b"body-secret"` are absent from transport/mapped-error repr,str,args,cause,context and captured test log text. |
| D24RUNTIME | Runtime traps for os/env/proxy/filesystem/logging/SDK/sleep/parser/extractor/PFF/ground/second request remain untouched during canonical success. |
| D25AST | AST imports equal section 8 exactly; no dynamic/function-local import or forbidden call is present. The configuration/caller-read assertions of D19ASTCONFIG/D19ASTREQUEST are independently repeated. |
| D26COMPOSELOCAL | Controlling A01 through canonical local fake produces exact A01 envelope and one literal 68-byte physical request with Content-Length `68`. |
| D27COMPOSECLOUD | A01 changed only to CLOUD through key `token!` produces exact cloud envelope/header and no credential in graph. |
| D28STATUSSIZE | `generate_ollama` with transport status 500/body `b"x"*4194305` emits only exact adapter HTTP-status issue. |
| D28OKSIZE | Same with status 200 emits only exact adapter body-limit issue with actual 4194305. |
| D29FRESH | Two canonical local calls create two distinct fake connections and each has one success trace; neither is reused. |
| D30IMPORT | Import/reload of module and package initializer plus transport construction has zero fake/env/filesystem/log calls. |

The exact declared population is:

```text
D = {
  D01API,
  D02KEYOK,D02KEYTYPE,D02KEYVALUE,
  D03TIMEOK,D03TIMETYPE,D03TIMEVALUE,
  D04LOCAL,D05CLOUD,D06NOKEY,D07LOCALKEY,
  D08EMPTYBODY,D08ONEBODY,D08BIGBODY,D09STATUS,
  D10BODYZERO,D10BODYMAX,D10BODYSENTINEL,D10BODYOVERFAKE,
  D11STATUSBAD,D11BODYBAD,D12MISSSTATUS,D12MISSREAD,
  D13OSFACTORY,D13OSREQUEST,D13OSGET,D13OSSTATUS,D13OSREAD,
  D14HTTPFACTORY,D14HTTPREQUEST,D14HTTPGET,D14HTTPSTATUS,D14HTTPREAD,
  D15UNEXPECTED,D16BASE,
  D17CLOSERESP,D17CLOSECONN,D17CLOSEMAPPED,D17CLOSEUNEXPECTED,
  D18BASERESP,D18BASECONN,
  D19REFACTORY,D19ASTCONFIG,D19ASTREQUEST,
  D20REQTYPE,D20REQCORRUPT,D20CFGCORRUPT,
  D21NOINSPECT,D22REDIRECT,D23SECRETS,D24RUNTIME,D25AST,
  D26COMPOSELOCAL,D27COMPOSECLOUD,D28STATUSSIZE,D28OKSIZE,D29FRESH,D30IMPORT
}
```

The qualification harness proves exact set equality
`D == D_dispatch == D_executed`; a count or green discovery run is insufficient.

## 10. Mutation qualification

Every mutation below is applied alone to a fresh authenticated implementation
copy. The named fixture must fail at its named observable while all setup and
unlisted assertions remain green. Syntax/import/setup/earlier-gate failure is a
wrong-reason kill; a green named assertion is a survivor.

| ID | One-mechanism mutation | Required discriminator |
|---|---|---|
| M01 | insert module import `from os import getenv` and constructor call `getenv("OLLAMA_API_KEY")` | D25AST exact import set |
| M02 | change dataclass `repr=False` to `repr=True` | D01API `token!` absent from repr |
| M03 | delete nonempty key check | D02KEYVALUE empty key raises ValueError |
| M04 | replace visible-ASCII lower bound U+0021 by U+0020 | D02KEYVALUE space raises ValueError |
| M05 | replace key byte maximum 4,096 by 4,097 | D02KEYVALUE 4,097 bytes raises ValueError |
| M06 | replace exact timeout type check by `isinstance(..., int)` | D03TIMETYPE bool raises TypeError |
| M07 | replace timeout lower bound 1 by 0 | D03TIMEVALUE zero raises ValueError |
| M08 | change dataclass equality to `eq=False` | D01API equal field pairs compare equal |
| M09 | replace local host literal `localhost` by `127.0.0.1` | D04LOCAL factory host |
| M10 | replace local port 11434 by 11435 | D04LOCAL factory port |
| M11 | replace cloud `HTTPSConnection` by `HTTPConnection` | D05CLOUD factory kind |
| M12 | replace cloud host `ollama.com` by `www.ollama.com` | D05CLOUD factory host |
| M13 | replace cloud port 443 by 80 | D05CLOUD factory port |
| M14 | move cloud missing-key check after factory construction | D06NOKEY empty trace |
| M15 | add Authorization to local headers | D07LOCALKEY exact LOCAL_HEADERS |
| M16 | omit cloud Authorization entry | D05CLOUD exact CLOUD_HEADERS |
| M17 | append Authorization before Content-Type | D05CLOUD exact header insertion order |
| M18 | delete `Accept` header | D04LOCAL exact LOCAL_HEADERS |
| M19 | delete explicit `Content-Length` header | D08ONEBODY exact headers |
| M20 | change `encode_chunked=False` to `True` | D04LOCAL request event final value |
| M21 | replace `/api/generate` path by `/api/chat` | D04LOCAL request path |
| M22 | replace outbound body with `bytes(reversed(body))` | D04LOCAL canonical non-palindromic BODY identity |
| M23 | on exact 301 perform a second request | D22REDIRECT request count one |
| M24 | on exact 429 perform a second request | D09STATUS 429 request count one |
| M25 | on exact 500 perform a second request | D09STATUS 500 request count one |
| M26 | replace `read(4_194_305)` by `read()` | D10BODYZERO exact read event |
| M27 | replace read bound 4,194,305 by 4,194,304 | D10BODYSENTINEL exact returned length |
| M28 | append a second `read(1)` drain | D10BODYOVERFAKE one read event |
| M29 | coerce non-bytes read result with `bytes(body)` | D11BODYBAD bytearray maps error |
| M30 | accept bool status via `isinstance(status,int)` | D11STATUSBAD bool maps error |
| M31 | move `read` before status validation | D11STATUSBAD no read event |
| M32 | delete read-result maximum check | D10BODYOVERFAKE maps error |
| M33 | map `AttributeError` as a recognized transport failure | D12MISSSTATUS identical AttributeError |
| M34 | raise mapped error directly inside OSError handler | D13OSREAD cause/context both None |
| M35 | remove `HTTPException` from recognized tuple | D14HTTPREAD fixed transport error |
| M36 | catch every `Exception` as transport failure | D15UNEXPECTED identical sentinel |
| M37 | catch `BaseException` as transport failure | D16BASE identical KeyboardInterrupt |
| M38 | delete transport-issued `response.close()` | D13OSREAD response-close event |
| M39 | delete transport-issued `connection.close()` | D13OSREQUEST connection-close event |
| M40 | swap response/connection cleanup order | D13OSREAD exact final two events |
| M41 | remove suppression around response close | D17CLOSERESP exact successful response |
| M42 | return immediately after ordinary response-close failure | D17CLOSERESP connection-close event |
| M43 | catch `BaseException` in cleanup helper | D18BASERESP identical KeyboardInterrupt |
| M44 | build outbound body from caller request after factory returns | D19REFACTORY original BODY event |
| M45 | build Authorization from transport field after factory returns | D19REFACTORY original token header |
| M46 | insert a second `self._timeout_seconds` Load immediately before factory selection | D19ASTCONFIG exact Load count one |
| M47 | delete invocation request reconstruction/revalidation | D20REQCORRUPT empty trace |
| M48 | delete invocation configuration revalidation | D20CFGCORRUPT empty trace |
| M49 | access response `headers` before status | D21NOINSPECT forbidden property untouched |
| M50 | gzip-decompress read bytes | D21NOINSPECT exact gzip-looking bytes |
| M51 | add key to transport repr | D23SECRETS secret absent |
| M52 | raise mapped error with caught exception as cause | D13OSFACTORY clean cause/context |
| M53 | add absolute `from poietics.generation.extract import extract_draft` | D25AST exact import set |
| M54 | insert `open("/forbidden-ollama-transport", "rb")` at start of `__call__` | D24RUNTIME filesystem trap untouched |
| M55 | store and reuse connection across calls | D29FRESH two distinct connections |
| M56 | instantiate HTTPConnection during transport construction | D30IMPORT zero factory calls |
| M57 | translate exact status 500 to transport error | D09STATUS 500 exact response record |
| M58 | sort header names before request | D05CLOUD exact insertion order |
| M59 | omit `__all__` | D01API exact public tuple |
| M60 | accept request subclasses via `isinstance` | D20REQTYPE subclass raises TypeError |
| M61 | return sentinel-length transport failure instead of response | D28OKSIZE adapter body-limit issue |
| M62 | insert `response.getheader("Content-Length")` before status access | D21NOINSPECT forbidden `getheader` trap untouched |

The exact declared population is:

```text
M = {
  M01,M02,M03,M04,M05,M06,M07,M08,M09,M10,
  M11,M12,M13,M14,M15,M16,M17,M18,M19,M20,
  M21,M22,M23,M24,M25,M26,M27,M28,M29,M30,
  M31,M32,M33,M34,M35,M36,M37,M38,M39,M40,
  M41,M42,M43,M44,M45,M46,M47,M48,M49,M50,
  M51,M52,M53,M54,M55,M56,M57,M58,M59,M60,
  M61,M62
}
```

Qualification requires exact `M == M_dispatch == M_executed`, zero survivors,
zero wrong-reason kills, one green focused-suite control, and one green
full-suite control. Each mutation is applied alone. Its single named target
assertion must fail, every prerequisite/reachability assertion and every
unlisted assertion must remain green, and execution must reach the named gate.
Evidence records authenticated source/test hashes, exact mutation patch hash,
target assertion, terminal frame, classification, and unchanged-file proof.

## 11. Dated external evidence

The following official documentation was consulted on 2026-08-18:

- [Ollama API introduction](https://docs.ollama.com/api/introduction) for the
  default local and cloud API bases;
- [Generate](https://docs.ollama.com/api/generate) for `POST /api/generate`;
- [Authentication](https://docs.ollama.com/api/authentication) for no local
  authentication and direct cloud bearer authentication;
- [Errors](https://docs.ollama.com/api/errors) for representative statuses; and
- [Python `http.client`](https://docs.python.org/3/library/http.client.html) for
  connection/request/response primitives.

Those pages do not freeze this profile's timeout, retry, redirect, key syntax,
header mapping, response limit, cleanup, exception, or test policies. Those are
all explicitly `[N]`.

## 12. Explicit deferrals

This profile does not authorize:

- an environment/file/keyring/CLI credential loader, secret persistence,
  rotation, redaction service, or logging;
- live-provider tests, deployment configuration, proxy support, custom CA/TLS
  contexts, cancellation, connection pooling, streaming, or async transport;
- retry, backoff, redirect following, `Retry-After`, failover, model fallback,
  or automatic repair;
- response semantic parsing, extraction, binding, evidence/checker execution,
  PFF validation/compilation/evaluation, or ground evaluation; or
- any use of a real API key in repository, default tests, qualification, or
  acceptance evidence.

A separately authorized optional-live smoke may later inject a deployment
secret and call the published transport. It cannot become normative evidence.
The trusted draft-to-package binder remains a separate future profile.

## 13. Acceptance and later qualification

Profile acceptance is documentation-only. It requires authentication of the
exact candidate bytes, baseline, and controlling-profile hash; three
independent read-only `CLEAN` reviews; and a finding that all semantics,
fixtures, and mutations are determinate and dispatchable. It requires no
implementation, test, provider, credential, or network call.

Later implementation qualification is separate. It requires exact fixture and
mutation population equality, zero survivors and wrong-reason kills, focused
and full green suites, static/runtime isolation evidence, no real network or
credential use, and independent clean reviews. Qualification cannot alter the
accepted authority bytes.

Acceptance changes only the status line from `CANDIDATE — NOT ACCEPTED` to
`ACCEPTED` and appends exactly one LF plus this section, with one final LF:

````text
## 14. Acceptance record

```text
profile: pff-ollama-http-transport/0.1
status: accepted
accepted_on: 2026-08-18
reviewed_candidate_sha256: sha256:<64 lowercase hexadecimal digits>
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
````

`reviewed_candidate_sha256` is SHA-256 over the complete candidate bytes,
including its existing final LF, before the two acceptance transformations. No
other byte may change during acceptance. Implementation begins only after the
accepted profile is published.

## 14. Acceptance record

```text
profile: pff-ollama-http-transport/0.1
status: accepted
accepted_on: 2026-08-18
reviewed_candidate_sha256: sha256:41a5b07d24734dc59364a8a6d91bd77e081e3a42393972d1295b50fc21644b9e
review_result: architecture=clean; semantic_audit=clean; test_design=clean
```
