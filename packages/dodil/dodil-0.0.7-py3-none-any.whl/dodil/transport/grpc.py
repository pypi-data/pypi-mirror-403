

"""gRPC transport helpers for the DODIL Python SDK.

Goal
----
Provide a small, reusable transport layer (like HttpTransport) for gRPC services.

Design
------
- A `GrpcTransport` owns a gRPC channel (secure or insecure).
- A token provider (OIDC service-account) can be attached to automatically inject
  `authorization: Bearer <token>` metadata for all RPCs.
- Default metadata and sane keepalive options are supported.

This module does NOT depend on any generated stubs/protos. Service clients can
construct their stubs using `GrpcTransport.stub(StubClass)`.

Example
-------

```python
from dodil.grpc import GrpcTransport
from dodil.auth.authorization import ServiceAccountTokenManager
from dodil.vng.v1.vng_pb2_grpc import VngServiceStub

provider = ServiceAccountTokenManager(
    service_account_id="...",
    service_account_secret="...",
    profile="staging",
)

transport = GrpcTransport(
    target="vng-grpc.dev.dodil.io:443",
    token_provider=provider,
    secure=True,
)

stub = transport.stub(VngServiceStub)
resp = stub.HealthCheck(...)

transport.close()
provider.close()
```

Async usage (grpc.aio)
----------------------
If you use `grpc.aio` stubs, use `AsyncGrpcTransport` instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union

import grpc

from .common import TokenProvider


Metadata = Sequence[Tuple[str, str]]


class GrpcTransportError(RuntimeError):
    """SDK-level transport error for gRPC operations."""


def _normalize_metadata(md: Optional[Mapping[str, str]] = None) -> List[Tuple[str, str]]:
    if not md:
        return []
    return [(str(k).lower(), str(v)) for k, v in md.items()]


def _merge_metadata(base: Metadata, extra: Optional[Metadata]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = list(base or [])
    if extra:
        out.extend([(str(k).lower(), str(v)) for k, v in extra])
    return out


@dataclass(frozen=True)
class GrpcTlsConfig:
    """TLS configuration for secure gRPC channels.

    If only `root_certificates_pem` is provided, this config enables standard TLS.
    If `private_key_pem` and `certificate_chain_pem` are also provided, this enables
    mutual TLS (mTLS).
    """

    root_certificates_pem: Optional[bytes] = None
    private_key_pem: Optional[bytes] = None
    certificate_chain_pem: Optional[bytes] = None
    # Optional server name override.
    server_hostname: Optional[str] = None


@dataclass(frozen=True)
class GrpcTransportConfig:
    """Configuration for gRPC channels."""

    target: str
    secure: bool = True

    # Auth
    token_provider: Optional[TokenProvider] = None
    authorization_header: str = "authorization"
    token_prefix: str = "Bearer "

    # Metadata
    default_metadata: Optional[Mapping[str, str]] = None

    # Timeouts
    default_timeout_s: Optional[float] = 30.0

    # TLS
    tls: Optional[GrpcTlsConfig] = None

    # Channel options (keepalive/retries/etc)
    # See https://grpc.github.io/grpc/python/grpc.html#grpc.insecure_channel
    options: Optional[Sequence[Tuple[str, Any]]] = None


class _ClientCallDetails(grpc.ClientCallDetails):
    """A mutable ClientCallDetails wrapper used by interceptors."""

    def __init__(
        self,
        method: str,
        timeout: Optional[float],
        metadata: Optional[Metadata],
        credentials: Optional[grpc.CallCredentials],
        wait_for_ready: Optional[bool],
        compression: Optional[grpc.Compression],
    ) -> None:
        self.method = method
        self.timeout = timeout
        self.metadata = metadata
        self.credentials = credentials
        self.wait_for_ready = wait_for_ready
        self.compression = compression


class _AuthInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor, grpc.StreamUnaryClientInterceptor, grpc.StreamStreamClientInterceptor):
    """Interceptor that injects Authorization + default metadata."""

    def __init__(
        self,
        *,
        token_provider: Optional[TokenProvider],
        base_metadata: Metadata,
        authorization_header: str,
        token_prefix: str,
        default_timeout_s: Optional[float],
    ) -> None:
        self._token_provider = token_provider
        self._base_metadata = list(base_metadata or [])
        self._auth_header = authorization_header.lower()
        self._token_prefix = token_prefix
        self._default_timeout_s = default_timeout_s

    def _apply(self, client_call_details: grpc.ClientCallDetails) -> grpc.ClientCallDetails:
        md = _merge_metadata(self._base_metadata, client_call_details.metadata)

        # Inject bearer token.
        if self._token_provider is not None:
            try:
                token = self._token_provider.get_access_token()  # sync interface
            except Exception as e:
                raise GrpcTransportError(f"Failed to get access token: {e}")

            if token:
                md.append((self._auth_header, f"{self._token_prefix}{token}"))

        timeout = client_call_details.timeout
        if timeout is None and self._default_timeout_s is not None:
            timeout = float(self._default_timeout_s)

        return _ClientCallDetails(
            method=client_call_details.method,
            timeout=timeout,
            metadata=md,
            credentials=client_call_details.credentials,
            wait_for_ready=getattr(client_call_details, "wait_for_ready", None),
            compression=getattr(client_call_details, "compression", None),
        )

    # grpc interceptors
    def intercept_unary_unary(self, continuation, client_call_details, request):
        return continuation(self._apply(client_call_details), request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        return continuation(self._apply(client_call_details), request)

    def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        return continuation(self._apply(client_call_details), request_iterator)

    def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        return continuation(self._apply(client_call_details), request_iterator)


TStub = TypeVar("TStub")


def _default_channel_options() -> List[Tuple[str, Any]]:
    # Reasonable defaults; services can override via config.options.
    return [
        ("grpc.keepalive_time_ms", 30_000),
        ("grpc.keepalive_timeout_ms", 10_000),
        ("grpc.keepalive_permit_without_calls", 1),
        ("grpc.http2.max_pings_without_data", 0),
        ("grpc.http2.min_time_between_pings_ms", 10_000),
        ("grpc.http2.min_ping_interval_without_data_ms", 10_000),
        # NOTE: retry behavior is largely controlled server-side and by service config.
    ]


class GrpcTransport:
    """Synchronous gRPC transport based on `grpc.Channel`.

    Use this for generated sync stubs (grpc, not grpc.aio).
    """

    def __init__(self, *, target: str, token_provider: Optional[TokenProvider] = None, secure: bool = True, tls: Optional[GrpcTlsConfig] = None, default_metadata: Optional[Mapping[str, str]] = None, default_timeout_s: Optional[float] = 30.0, options: Optional[Sequence[Tuple[str, Any]]] = None) -> None:
        self._cfg = GrpcTransportConfig(
            target=target,
            secure=secure,
            token_provider=token_provider,
            tls=tls,
            default_metadata=default_metadata,
            default_timeout_s=default_timeout_s,
            options=options,
        )

        base_md = _normalize_metadata(self._cfg.default_metadata)

        # Interceptor will inject auth + defaults on every call.
        self._interceptor = _AuthInterceptor(
            token_provider=self._cfg.token_provider,
            base_metadata=base_md,
            authorization_header=self._cfg.authorization_header,
            token_prefix=self._cfg.token_prefix,
            default_timeout_s=self._cfg.default_timeout_s,
        )

        channel_options = list(_default_channel_options())
        if self._cfg.options:
            channel_options.extend(list(self._cfg.options))

        if self._cfg.secure:
            creds = self._build_ssl_channel_credentials(self._cfg.tls)
            ch: grpc.Channel = grpc.secure_channel(self._cfg.target, creds, options=channel_options)
        else:
            ch = grpc.insecure_channel(self._cfg.target, options=channel_options)

        self._channel: grpc.Channel = grpc.intercept_channel(ch, self._interceptor)

    @property
    def channel(self) -> grpc.Channel:
        return self._channel

    def close(self) -> None:
        try:
            self._channel.close()
        except Exception:
            # grpc close is best-effort
            return

    def stub(self, stub_cls: Type[TStub], *args: Any, **kwargs: Any) -> TStub:
        """Construct a generated stub bound to this transport's channel."""
        return stub_cls(self._channel, *args, **kwargs)

    @staticmethod
    def _build_ssl_channel_credentials(tls: Optional[GrpcTlsConfig]) -> grpc.ChannelCredentials:
        if tls is None:
            return grpc.ssl_channel_credentials()

        # mTLS if both key + cert chain are provided.
        if tls.private_key_pem and tls.certificate_chain_pem:
            return grpc.ssl_channel_credentials(
                root_certificates=tls.root_certificates_pem,
                private_key=tls.private_key_pem,
                certificate_chain=tls.certificate_chain_pem,
            )

        # Standard TLS
        return grpc.ssl_channel_credentials(root_certificates=tls.root_certificates_pem)


# ------------------------------
# Async transport (grpc.aio)
# ------------------------------


class _AioClientCallDetails:
    """
    Mutable wrapper for ClientCallDetails to allow modifying metadata/timeout.
    We don't inherit from grpc.aio.ClientCallDetails because it is a namedtuple
    and doesn't accept extra args (like compression is sometimes missing) easily
    without overriding __new__.
    """
    def __init__(
        self,
        method: str,
        timeout: Optional[float],
        metadata: Optional[Metadata],
        credentials: Optional[grpc.CallCredentials],
        wait_for_ready: Optional[bool],
        compression: Optional[grpc.Compression] = None,
    ) -> None:
        self.method = method
        self.timeout = timeout
        self.metadata = metadata
        self.credentials = credentials
        self.wait_for_ready = wait_for_ready
        self.compression = compression


class _AioAuthInterceptor(
    grpc.aio.UnaryUnaryClientInterceptor,
    grpc.aio.UnaryStreamClientInterceptor,
    grpc.aio.StreamUnaryClientInterceptor,
    grpc.aio.StreamStreamClientInterceptor,
):
    def __init__(
        self,
        *,
        token_provider: Optional[TokenProvider],
        base_metadata: Metadata,
        authorization_header: str,
        token_prefix: str,
        default_timeout_s: Optional[float],
    ) -> None:
        self._token_provider = token_provider
        self._base_metadata = list(base_metadata or [])
        self._auth_header = authorization_header.lower()
        self._token_prefix = token_prefix
        self._default_timeout_s = default_timeout_s

    def _apply(self, client_call_details: grpc.aio.ClientCallDetails) -> grpc.aio.ClientCallDetails:
        md = _merge_metadata(self._base_metadata, client_call_details.metadata)

        if self._token_provider is not None:
            try:
                token = self._token_provider.get_access_token()  # sync interface
            except Exception as e:
                raise GrpcTransportError(f"Failed to get access token: {e}")
            if token:
                md.append((self._auth_header, f"{self._token_prefix}{token}"))

        timeout = client_call_details.timeout
        if timeout is None and self._default_timeout_s is not None:
            timeout = float(self._default_timeout_s)

        return _AioClientCallDetails(
            method=client_call_details.method,
            timeout=timeout,
            metadata=md,
            credentials=client_call_details.credentials,
            wait_for_ready=getattr(client_call_details, "wait_for_ready", None),
            compression=getattr(client_call_details, "compression", None),
        )

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        return await continuation(self._apply(client_call_details), request)

    async def intercept_unary_stream(self, continuation, client_call_details, request):
        return await continuation(self._apply(client_call_details), request)

    async def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        return await continuation(self._apply(client_call_details), request_iterator)

    async def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        return await continuation(self._apply(client_call_details), request_iterator)


class AsyncGrpcTransport:
    """Async gRPC transport based on `grpc.aio.Channel`.

    Use this for generated async stubs (grpc.aio).
    """

    def __init__(self, *, target: str, token_provider: Optional[TokenProvider] = None, secure: bool = True, tls: Optional[GrpcTlsConfig] = None, default_metadata: Optional[Mapping[str, str]] = None, default_timeout_s: Optional[float] = 30.0, options: Optional[Sequence[Tuple[str, Any]]] = None) -> None:
        self._cfg = GrpcTransportConfig(
            target=target,
            secure=secure,
            token_provider=token_provider,
            tls=tls,
            default_metadata=default_metadata,
            default_timeout_s=default_timeout_s,
            options=options,
        )

        base_md = _normalize_metadata(self._cfg.default_metadata)
        self._interceptor = _AioAuthInterceptor(
            token_provider=self._cfg.token_provider,
            base_metadata=base_md,
            authorization_header=self._cfg.authorization_header,
            token_prefix=self._cfg.token_prefix,
            default_timeout_s=self._cfg.default_timeout_s,
        )

        channel_options = list(_default_channel_options())
        if self._cfg.options:
            channel_options.extend(list(self._cfg.options))

        if self._cfg.secure:
            print(f"[AsyncGrpcTransport] Creating SECURE channel to {self._cfg.target}")
            creds = GrpcTransport._build_ssl_channel_credentials(self._cfg.tls)
            ch: grpc.aio.Channel = grpc.aio.secure_channel(
                self._cfg.target,
                creds,
                options=channel_options,
                interceptors=[self._interceptor],
            )
        else:
            print(f"[AsyncGrpcTransport] Creating INSECURE channel to {self._cfg.target}")
            ch = grpc.aio.insecure_channel(
                self._cfg.target,
                options=channel_options,
                interceptors=[self._interceptor],
            )

        self._channel = ch

    @property
    def channel(self) -> grpc.aio.Channel:
        return self._channel

    async def close(self) -> None:
        try:
            await self._channel.close()
        except Exception:
            return

    def stub(self, stub_cls: Type[TStub], *args: Any, **kwargs: Any) -> TStub:
        return stub_cls(self._channel, *args, **kwargs)

    async def __aenter__(self) -> "AsyncGrpcTransport":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()