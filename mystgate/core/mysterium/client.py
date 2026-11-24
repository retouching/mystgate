import logging
import platform
import uuid
from pathlib import Path
from types import TracebackType
from typing import Final
from urllib.parse import urlencode

import httpx
from pydantic import TypeAdapter, ValidationError

from mystgate.core.config import Settings
from mystgate.core.exceptions import APIError, AuthenticationError
from mystgate.core.mysterium.enums import IPType
from mystgate.core.mysterium.schemas import (
    ActivationStatus,
    ConnectionResponse,
    CountryLocation,
    OAuthTokens,
)
from mystgate.core.mysterium.token_store import TokenStore
from mystgate.core.utils import message

API_BASE_URL: Final[str] = "https://api.mysteriumvpn.com/api/v1"
AUTHORIZE_URL: Final[str] = "https://app.mysteriumvpn.com/oauth/authorize"
CLIENT_ID: Final[str] = "cli"
CLI_VERSION: Final[str] = "0.3.2"
OS_TYPE: Final[str] = "linux-cli"
USER_AGENT: Final[str] = "Go-http-client/1.1"
REQUEST_TIMEOUT_SECONDS: Final[float] = 30.0
LOCATIONS_ADAPTER: Final[TypeAdapter[list[CountryLocation]]] = TypeAdapter(list[CountryLocation])
LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class MysteriumClient:
    def __init__(
        self,
        settings: Settings,
        *,
        token_store: TokenStore | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the Mysterium VPN HTTP client with automatic token refresh."""
        self.settings = settings
        self.token_store = token_store if token_store is not None else TokenStore(settings.state_directory)
        self.owns_client = http_client is None
        self.client = (
            http_client
            if http_client is not None
            else httpx.Client(
                base_url=API_BASE_URL,
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        )

    def __enter__(self) -> MysteriumClient:
        """Return the client when entering a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the owned HTTP client when leaving a context manager."""
        del exc_type, exc_val, exc_tb
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self.owns_client:
            self.client.close()

    @staticmethod
    def detect_os_version() -> str:
        """Read a human-readable OS version string for connection requests."""
        release_file = Path("/etc/os-release")
        if release_file.is_file():
            try:
                for line in release_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip('"')
            except OSError:
                pass
        return f"{platform.system()} {platform.release()}"

    def request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, object] | None = None,
        token: str | None = None,
    ) -> object:
        """Send an HTTP request to the Mysterium API and decode JSON if present."""
        headers: dict[str, str] = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = self.client.request(method, endpoint, params=params, json=body, headers=headers)
        except httpx.HTTPError as error:
            raise APIError(message("Mysterium API", "request failed", str(error))) from error

        if response.status_code == 401:
            raise AuthenticationError(message("Mysterium API", "unauthorized", "HTTP 401"))
        if response.status_code == 403:
            raise AuthenticationError(message("Mysterium API", "forbidden", "HTTP 403"))
        if response.is_error:
            raise APIError(message("Mysterium API", "error response", f"HTTP {response.status_code}"))

        if not response.text.strip():
            return None
        try:
            return response.json()
        except ValueError as error:
            raise APIError(message("Mysterium API", "invalid JSON response")) from error

    def refresh_tokens(self) -> OAuthTokens:
        """Refresh and persist OAuth tokens using the stored refresh token."""
        saved = self.token_store.load()
        raw = self.request_raw(
            "POST",
            "/oauth/token",
            body={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "refresh_token": saved.refresh_token.get_secret_value(),
            },
        )
        try:
            fresh = OAuthTokens.model_validate(raw)
        except ValidationError as error:
            raise AuthenticationError(message("Authentication", "invalid refresh response")) from error
        self.token_store.save(fresh)
        LOGGER.debug("Refreshed OAuth tokens")
        return fresh

    def request_authed(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, object] | None = None,
    ) -> object:
        """Send an authenticated request and retry once after refreshing on HTTP 401."""
        tokens = self.token_store.load()
        try:
            return self.request_raw(
                method,
                endpoint,
                params=params,
                body=body,
                token=tokens.access_token.get_secret_value(),
            )
        except AuthenticationError:
            fresh = self.refresh_tokens()
            return self.request_raw(
                method,
                endpoint,
                params=params,
                body=body,
                token=fresh.access_token.get_secret_value(),
            )

    def start_activation(self, activation_id: str | None = None) -> tuple[str, str]:
        """Register a browser activation session and return its ID and approval URL."""
        session_id = activation_id if activation_id is not None else str(uuid.uuid4())
        self.request_raw("POST", "/auth/activation", body={"id": session_id})
        query = urlencode(
            {
                "response_type": "activation_none",
                "client_id": CLIENT_ID,
                "request_id": session_id,
            }
        )
        return session_id, f"{AUTHORIZE_URL}?{query}"

    def poll_activation(self, activation_id: str) -> ActivationStatus:
        """Fetch the current approval state of an OAuth activation session."""
        raw = self.request_raw("GET", f"/auth/activation/{activation_id}")
        try:
            status = ActivationStatus.model_validate(raw)
        except ValidationError as error:
            raise APIError(message("Mysterium API", "invalid activation payload")) from error
        if status.id != activation_id:
            raise APIError(message("Mysterium API", "activation ID mismatch"))
        return status

    def list_locations(self, ip_type: IPType) -> list[CountryLocation]:
        """Fetch all country and city locations for a given IP type."""
        raw = self.request_authed("GET", "/connection/config/locations", params={"ip_type": ip_type.value})
        try:
            return LOCATIONS_ADAPTER.validate_python(raw)
        except ValidationError as error:
            raise APIError(message("Mysterium API", "invalid locations payload")) from error

    def connect(
        self,
        public_key: str,
        country: str,
        ip_type: IPType,
        *,
        city: str | None = None,
        reset_connection: bool = True,
    ) -> ConnectionResponse:
        """Request a WireGuard session and configuration template from Mysterium."""
        payload: dict[str, object] = {
            "public_key": public_key,
            "country": country.upper(),
            "ip_type": ip_type.value,
            "os_type": OS_TYPE,
            "cli_version": CLI_VERSION,
            "os_version": self.detect_os_version(),
            "reset_connection": reset_connection,
        }
        if city:
            payload["city"] = city
        raw = self.request_authed("POST", "/connection/connect", body=payload)
        try:
            connection = ConnectionResponse.model_validate(raw)
        except ValidationError as error:
            raise APIError(message("Mysterium API", "invalid connect payload")) from error

        if connection.limit_exceeded:
            raise APIError(
                message(
                    "Mysterium API",
                    "device limit reached",
                    "remove a device at https://app.mysteriumvpn.com/dashboard/devices",
                )
            )
        return connection

    def disconnect(self, public_key: str) -> None:
        """Release the server-side WireGuard session associated with public_key."""
        self.request_authed("GET", "/connection/disconnect", params={"public_key": public_key})
