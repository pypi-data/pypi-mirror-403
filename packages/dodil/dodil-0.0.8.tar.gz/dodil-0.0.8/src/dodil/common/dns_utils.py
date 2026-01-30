from typing import Optional, Literal
from urllib.parse import urlparse

Profile = Literal["prod", "staging"]


def _api_base_url(profile: Profile, override: Optional[str] = None) -> str:
    """Resolve the API HTTP base URL (scheme + host).

    - If `override` is provided, it may be a full URL (recommended) or a host/target.
    - Returns a normalized string without a trailing slash.
    """
    if override:
        return override.rstrip("/")
    return "https://api.dev.dodil.io" if profile == "staging" else "https://api.dodil.io"


def _to_grpc_target(value: str) -> str:
    """Convert a URL/host into a gRPC target (host:port).

    Accepts:
      - https://host -> host:443
      - http://host  -> host:80
      - host:port    -> host:port
      - host         -> host:443 (assume TLS)
    """
    v = (value or "").strip()
    if not v:
        raise ValueError("gRPC target is empty")

    if "://" in v:
        u = urlparse(v)
        host = u.hostname or ""
        if not host:
            raise ValueError(f"Invalid URL: {value!r}")
        port = u.port
        if port is None:
            port = 443 if (u.scheme or "").lower() == "https" else 80
        return f"{host}:{port}"

    # Already looks like host:port
    if ":" in v:
        return v

    # Host only -> assume TLS/443
    return f"{v}:443"


def _api_grpc_target(profile: Profile, override: Optional[str] = None) -> str:
    """Resolve the API gRPC target (host:port) for a given profile.

    - If `override` is provided, it may be either a URL (https://...) or a target (host:port).
    - If no override is provided, this derives the host from `_api_base_url` and converts it to host:port.
    """
    base = _api_base_url(profile, override)
    return _to_grpc_target(base)
