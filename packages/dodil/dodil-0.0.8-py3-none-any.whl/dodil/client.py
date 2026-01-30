"""Root SDK client.

Pattern
-------
- `Client` owns shared configuration + auth (a TokenProvider).
- Services are exposed as lazy handles (e.g. `client.vng`).
- A service handle can create bound clients (e.g. `client.vng.connect(...)`).

Example
-------

```py
from dodil import Client

c = Client(profile="staging", service_account_id="...", service_account_secret="...")

# VNG defaults to gRPC and can run with defaults
vng = c.vng.connect()
# stub = vng.stub(VngServiceStub)
# resp = await stub.HealthCheck(...)

c.close()
```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .common import Profile
from .transport import TokenProvider
from .auth.authorization import ServiceAccountTokenManager
from .vng.vng_client import VngConfig, VngServiceHandle
from .vbase.vbase_client import VBaseConfig, VBaseServiceHandle
from .vspace import VSpace, VSpaceServiceHandle



@dataclass(frozen=True)
class ClientConfig:
    """Shared configuration for the root client."""

    profile: Profile = "staging"

    # Transport defaults
    timeout_s: float = 30.0
    verify_ssl: bool = True

    # Optional per-service defaults
    vng: Optional[VngConfig] = None
    vbase: Optional[VBaseConfig] = None


class Client:
    """Root DODIL SDK client.

    The client owns a TokenProvider (auth) and exposes service handles.
    """

    def __init__(
        self,
        *,
        profile: Profile = "staging",
        service_account_id: Optional[str] = None,
        service_account_secret: Optional[str] = None,
        token_provider: Optional[TokenProvider] = None,
        timeout_s: float = 30.0,
        verify_ssl: bool = True,
        vng: Optional[VngConfig] = None,
        vbase: Optional[VBaseConfig] = None,
    ) -> None:
        self.profile: Profile = profile
        self.timeout_s: float = float(timeout_s)
        self.verify_ssl: bool = bool(verify_ssl)

        # Auth wiring:
        # - If caller supplies token_provider, use it.
        # - Else if service account creds provided, build ServiceAccountTokenManager.
        # - Else no auth (anonymous).
        self.token_provider: Optional[TokenProvider]
        self._owns_token_provider: bool = False

        if token_provider is not None:
            self.token_provider = token_provider
        elif service_account_id and service_account_secret:
            self.token_provider = ServiceAccountTokenManager(
                service_account_id=service_account_id,
                service_account_secret=service_account_secret,
                profile=profile,
            )
            self._owns_token_provider = True
        else:
            self.token_provider = None

        self._cfg = ClientConfig(
            profile=profile,
            timeout_s=self.timeout_s,
            verify_ssl=self.verify_ssl,
            vng=vng,
            vbase=vbase,
        )

        # Lazy service handles
        self._vng: Optional[VngServiceHandle] = None
        self._vbase: Optional[VBaseServiceHandle] = None
        self._vspace: Optional[VSpaceServiceHandle] = None

    # -------------------------
    # Service handles (lazy)
    # -------------------------

    @property
    def vng(self) -> VngServiceHandle:
        """VNG service handle (lazy)."""
        if self._vng is None:
            self._vng = VngServiceHandle(owner=self, config=self._cfg.vng)
        return self._vng

    @property
    def vbase(self) -> VBaseServiceHandle:
        """VBase service handle (lazy)."""
        if self._vbase is None:
            self._vbase = VBaseServiceHandle(owner=self, default_config=self._cfg.vbase)
        return self._vbase

    @property
    def vspace(self) -> VSpaceServiceHandle:
        """VSpace service handle (lazy)."""
        if self._vspace is None:
            self._vspace = VSpaceServiceHandle(vbase=self.vbase.connect(), vng=self.vng.connect())
        return self._vspace

    # -------------------------
    # Lifecycle
    # -------------------------

    def close(self) -> None:
        """Close resources owned by the root client.

        Note: bound service clients created via `.connect()` may own their own
        channels/transports and should be closed by the caller.
        """
        
        if self._owns_token_provider and self.token_provider is not None:
            close_fn = getattr(self.token_provider, "close", None)
            if callable(close_fn):
                close_fn()

