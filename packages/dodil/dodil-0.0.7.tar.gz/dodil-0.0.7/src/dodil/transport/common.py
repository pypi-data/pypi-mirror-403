from typing import Mapping, Protocol

class TokenProvider(Protocol):
    """Provides access tokens for outgoing requests."""

    def get_access_token(self) -> str:
        """Return a valid access token (may be cached/refreshed internally)."""
        ...


class HeaderProvider(Protocol):
    """Optional provider for additional headers (org/workspace ids, etc.)."""

    def get_headers(self) -> Mapping[str, str]:
        """Return headers to attach to each outgoing request."""
        ...