import logging
import time
from collections.abc import Callable
from typing import Final

from mystgate.core.exceptions import AuthenticationError
from mystgate.core.logging import LogMarker
from mystgate.core.mysterium import MysteriumClient, OAuthTokens, TokenStore
from mystgate.core.utils import Monotonic, message

AUTH_TIMEOUT_SECONDS: Final[float] = 300.0
POLL_INTERVAL_SECONDS: Final[float] = 5.0
LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class Authenticator:
    def __init__(
        self,
        client: MysteriumClient,
        token_store: TokenStore,
        *,
        monotonic: Monotonic | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize the browser-approval OAuth authentication workflow."""
        self.client = client
        self.token_store = token_store
        self.monotonic = monotonic if monotonic is not None else Monotonic()
        self.sleep = sleep

    def start(self) -> tuple[str, str]:
        """Start an activation session and return its ID and browser approval URL."""
        session_id, url = self.client.start_activation()
        LOGGER.info("Started OAuth activation %s", session_id)
        return session_id, url

    def wait_for_tokens(
        self,
        activation_id: str,
        *,
        timeout_seconds: float = AUTH_TIMEOUT_SECONDS,
        poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
    ) -> OAuthTokens:
        """Poll until the user approves the activation and persist the resulting tokens."""
        deadline = self.monotonic() + timeout_seconds
        while self.monotonic() < deadline:
            status = self.client.poll_activation(activation_id)
            if not status.valid:
                raise AuthenticationError(message("Authentication", "activation expired or rejected"))
            if status.token is not None:
                self.token_store.save(status.token)
                LOGGER.info("%s Saved OAuth tokens", LogMarker.DONE.value)
                return status.token
            self.sleep(poll_interval_seconds)
        raise AuthenticationError(message("Authentication", "timed out waiting for browser approval"))
