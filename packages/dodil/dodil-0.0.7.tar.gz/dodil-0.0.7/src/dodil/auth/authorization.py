"""Auth (OIDC) helpers for the DODIL SDK.

This module intentionally abstracts the underlying Identity Provider (IdP).

Defaults:
- issuer_base_url (prod): https://id.dodil.io
- issuer_base_url (staging): https://id.dev.dodil.io
- realm: dodil

Primary use-case today:
- Service accounts (OIDC client-credentials grant under the hood)

Public API surface:
- AuthConfig
- AuthService
- ServiceAccountTokenProvider (implements TokenProvider)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from dodil.common import Profile
from dodil.transport import HttpTransport, HttpTransportError, TokenProvider

Realm = Literal["dodil"]


def _issuer_base_url(profile: Profile, override: Optional[str] = None) -> str:
    if override:
        return override.rstrip("/")
    return "https://id.dev.dodil.io" if profile == "staging" else "https://id.dodil.io"


class AuthTokenResponse(BaseModel):
    """Standard OIDC token response (subset).

    The IdP typically returns at least: access_token, expires_in, token_type.

    Keycloak may also return `not-before-policy` (hyphenated). We accept that via an alias.
    We also ignore any extra fields the IdP returns.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: Optional[str] = None

    # Common optional fields returned by some IdPs
    refresh_expires_in: Optional[int] = None
    not_before_policy: Optional[int] = Field(default=None, alias="not-before-policy")
    session_state: Optional[str] = None

    def safe_repr(self) -> str:
        """Do not leak the full token in logs."""
        token = self.access_token
        if token and len(token) > 12:
            token = f"{token[:6]}...{token[-6:]}"
        return (
            "AuthTokenResponse("
            f"expires_in={self.expires_in}, "
            f"token_type={self.token_type!r}, "
            f"scope={self.scope!r}, "
            f"refresh_expires_in={self.refresh_expires_in!r}, "
            f"not_before_policy={self.not_before_policy!r}, "
            f"session_state={self.session_state!r}, "
            f"access_token={token}"
            ")"
        )


class ServiceAccountTokenRequest(BaseModel):
    """Service account token request.

    Under the hood this is the OIDC client-credentials grant.
    """

    service_account_id: str
    service_account_secret: str
    grant_type: str = "client_credentials"

    def as_form(self) -> dict:
        # OIDC expects these field names for client-credentials.
        return {
            "client_id": self.service_account_id,
            "client_secret": self.service_account_secret,
            "grant_type": self.grant_type,
        }


@dataclass(frozen=True)
class AuthConfig:
    """Auth configuration for service-account token exchange."""

    # Credentials
    service_account_id: str
    service_account_secret: str

    # Environment/profile
    profile: Profile = "staging"

    # Options (realm is optional override)
    realm: Realm = "dodil"
    issuer_base_url: Optional[str] = None

    # HTTP behavior
    timeout_s: float = 30.0
    verify_ssl: bool = True

    @property
    def base_url(self) -> str:
        return _issuer_base_url(self.profile, self.issuer_base_url)

    @property
    def token_path(self) -> str:
        # OIDC standard token endpoint path (IdP-specific but common; works for Keycloak)
        return f"/realms/{self.realm}/protocol/openid-connect/token"


class AuthService:
    """Auth client for exchanging service account credentials for access tokens."""

    def __init__(self, cfg: AuthConfig):
        self._cfg = cfg
        # Token exchange should not attach bearer auth.
        self._http = HttpTransport(
            base_url=cfg.base_url,
            timeout_s=cfg.timeout_s,
            verify=cfg.verify_ssl,
        )

    def close(self) -> None:
        self._http.close()

    def exchange_service_account_token(self) -> AuthTokenResponse:
        """Exchange service_account_id/secret for an access token."""

        req = ServiceAccountTokenRequest(
            service_account_id=self._cfg.service_account_id,
            service_account_secret=self._cfg.service_account_secret,
        )

        try:
            data = self._http.request_json(
                "POST",
                self._cfg.token_path,
                data=req.as_form(),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except HttpTransportError as e:
            raise HttpTransportError(
                message=f"Auth token exchange failed: {e.message}",
                status_code=e.status_code,
                method=e.method,
                url=e.url,
                response_text=e.response_text,
            )

        try:
            return AuthTokenResponse.model_validate(data)
        except Exception as ve:
            # If IdP returns error JSON (e.g. {"error":"invalid_client"...})
            raise HttpTransportError(
                message=f"Auth token response validation failed: {ve}",
                status_code=None,
                method="POST",
                url=f"{self._cfg.base_url}{self._cfg.token_path}",
                response_text=str(data),
            )


class ServiceAccountTokenManager(TokenProvider):
    """TokenProvider backed by service account credentials.

    - Fetches token via OIDC client-credentials.
    - Caches access token in-memory.
    - Refreshes when near expiry.
    """

    def __init__(
        self,
        *,
        service_account_id: str,
        service_account_secret: str,
        profile: Profile = "staging",
        issuer_base_url: Optional[str] = None,
        timeout_s: float = 30.0,
        verify_ssl: bool = True,
        refresh_skew_s: int = 30,
    ) -> None:
        self._cfg = AuthConfig(
            service_account_id=service_account_id,
            service_account_secret=service_account_secret,
            profile=profile,
            issuer_base_url=issuer_base_url,
            realm="dodil",
            timeout_s=timeout_s,
            verify_ssl=verify_ssl,
        )
        self._svc = AuthService(self._cfg)
        self._refresh_skew_s = max(0, int(refresh_skew_s))

        self._access_token: Optional[str] = None
        self._expires_at_epoch: float = 0.0

    def close(self) -> None:
        self._svc.close()

    def get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < (self._expires_at_epoch - self._refresh_skew_s):
            return self._access_token

        tok = self._svc.exchange_service_account_token()

        # Compute expiry based on the moment we received the response (closer to IdP TTL semantics).
        received_at = time.time()

        # Avoid printing the full bearer token.
        print(f"Exchanged service account token: {tok.safe_repr()}")

        self._access_token = tok.access_token
        self._expires_at_epoch = received_at + max(0, int(tok.expires_in))
        return self._access_token


# --- Example usage ---
#
# from dodil.transport import HttpTransport
# from dodil.authorization import ServiceAccountTokenManager
#
# provider = ServiceAccountTokenManager(
#     service_account_id="svc-vng",
#     service_account_secret="...",
#     profile="staging",   # omit for prod
# )
#
# api = HttpTransport(base_url="https://api.dodil.io", token_provider=provider)
# print(api.get("/health"))