

"""HTTP transport used by the SDK.

Goals:
- Simple, production-friendly HTTPS support out of the box (public SSL certs).
- Central place to inject auth headers (Bearer token) and common headers.
- Consistent error handling.

mTLS support can be added later by extending the `verify`/`cert` options.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Union
import httpx

from .common import TokenProvider


@dataclass
class HttpTransportError(Exception):
    """Raised when an HTTP request fails (non-2xx or transport error)."""

    message: str
    status_code: Optional[int] = None
    method: Optional[str] = None
    url: Optional[str] = None
    response_text: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.method and self.url:
            parts.append(f"{self.method} {self.url}")
        return " | ".join(parts)


HeadersLike = Optional[Mapping[str, str]]
JsonLike = Any


def _merge_headers(*parts: HeadersLike) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in parts:
        if not p:
            continue
        for k, v in p.items():
            # Normalize to strings for httpx.
            if v is None:
                continue
            out[str(k)] = str(v)
    return out


class HttpTransport:
    """Synchronous HTTP transport.

    Uses `httpx.Client` underneath. HTTPS works by default with system CA bundle.

    Parameters
    - base_url: e.g. "https://iam.dodil.cloud" (or staging)
    - token_provider: adds Authorization: Bearer <token>
    - header_provider: adds extra headers (org/workspace) per request
    - verify: SSL verification. True uses system CAs; can be a path to CA bundle.
    - timeout_s: default request timeout in seconds
    """

    def __init__(
        self,
        base_url: str,
        *,
        token_provider: Optional[TokenProvider] = None,
        header_provider: Optional[HeaderProvider] = None,
        default_headers: HeadersLike = None,
        timeout_s: float = 30.0,
        verify: Union[bool, str] = True,
        user_agent: str = "dodil-sdk-python/0.1",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token_provider = token_provider
        self._header_provider = header_provider
        self._default_headers = _merge_headers(
            {"User-Agent": user_agent, "Accept": "application/json"},
            default_headers,
        )
        self._timeout = httpx.Timeout(timeout_s)

        # Public SSL (HTTPS) verification is enabled by default.
        # Later mTLS can be added via `cert=(cert_path, key_path)`.
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._default_headers,
            verify=verify,
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpTransport":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _per_request_headers(self, extra: HeadersLike) -> Dict[str, str]:
        auth: Dict[str, str] = {}
        if self._token_provider is not None:
            token = self._token_provider.get_access_token()
            if token:
                auth["Authorization"] = f"Bearer {token}"

        provided: Dict[str, str] = {}
        if self._header_provider is not None:
            try:
                provided = dict(self._header_provider.get_headers())
            except Exception as e:
                raise HttpTransportError(message=f"header_provider.get_headers failed: {e}")

        return _merge_headers(auth, provided, extra)

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: JsonLike = None,
        data: Any = None,
        headers: HeadersLike = None,
        timeout_s: Optional[float] = None,
    ) -> httpx.Response:
        """Perform a request and return the raw httpx.Response.

        - path can be relative ("/v1/token") or absolute ("https://...")
        - raises HttpTransportError on network errors or non-2xx status codes
        """

        req_headers = self._per_request_headers(headers)
        timeout = httpx.Timeout(timeout_s) if timeout_s is not None else self._timeout

        try:
            resp = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                data=data,
                headers=req_headers,
                timeout=timeout,
            )
        except httpx.RequestError as e:
            raise HttpTransportError(
                message=f"HTTP request failed: {e}",
                status_code=None,
                method=method,
                url=str(e.request.url) if getattr(e, "request", None) is not None else None,
            )

        if resp.status_code < 200 or resp.status_code >= 300:
            # Keep response text (truncated by caller if needed).
            text = None
            try:
                text = resp.text
            except Exception:
                text = None
            raise HttpTransportError(
                message="HTTP request returned non-success status",
                status_code=resp.status_code,
                method=method,
                url=str(resp.request.url),
                response_text=text,
            )

        return resp

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: JsonLike = None,
        data: Any = None,
        headers: HeadersLike = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        """Perform a request and return parsed JSON.

        Raises HttpTransportError if:
        - request fails
        - non-2xx response
        - invalid JSON returned
        """

        resp = self.request_raw(
            method,
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout_s=timeout_s,
        )

        # If the server returns empty body, return None.
        if not resp.content:
            return None

        try:
            return resp.json()
        except Exception as e:
            raise HttpTransportError(
                message=f"Failed to decode JSON response: {e}",
                status_code=resp.status_code,
                method=method,
                url=str(resp.request.url),
                response_text=resp.text if hasattr(resp, "text") else None,
            )

    # Convenience methods
    def get(self, path: str, *, params: Optional[Mapping[str, Any]] = None, headers: HeadersLike = None) -> Any:
        return self.request_json("GET", path, params=params, headers=headers)

    def post(self, path: str, *, json: JsonLike = None, data: Any = None, headers: HeadersLike = None) -> Any:
        return self.request_json("POST", path, json=json, data=data, headers=headers)

    def put(self, path: str, *, json: JsonLike = None, data: Any = None, headers: HeadersLike = None) -> Any:
        return self.request_json("PUT", path, json=json, data=data, headers=headers)

    def patch(self, path: str, *, json: JsonLike = None, data: Any = None, headers: HeadersLike = None) -> Any:
        return self.request_json("PATCH", path, json=json, data=data, headers=headers)

    def delete(self, path: str, *, json: JsonLike = None, data: Any = None, headers: HeadersLike = None) -> Any:
        return self.request_json("DELETE", path, json=json, data=data, headers=headers)