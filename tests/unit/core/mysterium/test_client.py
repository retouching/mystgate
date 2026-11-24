from pathlib import Path

import httpx
import pytest
import respx
from pydantic import SecretStr

from mystgate.core.exceptions import APIError, AuthenticationError
from mystgate.core.mysterium import IPType, MysteriumClient, OAuthTokens, TokenStore
from mystgate.core.mysterium.client import API_BASE_URL, AUTHORIZE_URL
from tests.support import SettingsFactory


class TestMysteriumClient:
    @respx.mock
    def test_activation_flow_and_user_agent(self, tmp_path: Path) -> None:
        """Start activation with Go-http-client UA and parse polling response."""
        settings = SettingsFactory.build(tmp_path)
        start_route = respx.post(f"{API_BASE_URL}/auth/activation").mock(return_value=httpx.Response(200))
        respx.get(f"{API_BASE_URL}/auth/activation/act-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "act-1",
                    "valid": True,
                    "token": {"access_token": "acc-1", "refresh_token": "ref-1"},
                },
            )
        )

        with MysteriumClient(settings) as client:
            session_id, url = client.start_activation("act-1")
            status = client.poll_activation(session_id)

        assert start_route.calls.last.request.headers["User-Agent"] == "Go-http-client/1.1"
        assert url == f"{AUTHORIZE_URL}?response_type=activation_none&client_id=cli&request_id=act-1"
        assert status.valid is True
        assert status.token is not None
        assert status.token.access_token.get_secret_value() == "acc-1"

    @respx.mock
    def test_list_locations_refreshes_expired_token_on_401(self, tmp_path: Path) -> None:
        """Refresh OAuth tokens automatically when an authenticated request returns 401."""
        settings = SettingsFactory.build(tmp_path)
        store = TokenStore(settings.state_directory)
        store.save(OAuthTokens(access_token=SecretStr("old-acc"), refresh_token=SecretStr("old-ref")))

        locations_route = respx.get(f"{API_BASE_URL}/connection/config/locations").mock(
            side_effect=[
                httpx.Response(401),
                httpx.Response(
                    200,
                    json=[
                        {
                            "country": "FR",
                            "total": 12,
                            "is_available": True,
                            "translations": {"en": "France"},
                            "cities": [
                                {
                                    "city": "paris",
                                    "total": 8,
                                    "is_available": True,
                                    "translations": {"en": "Paris"},
                                }
                            ],
                        }
                    ],
                ),
            ]
        )
        refresh_route = respx.post(f"{API_BASE_URL}/oauth/token").mock(
            return_value=httpx.Response(200, json={"access_token": "new-acc", "refresh_token": "new-ref"})
        )

        with MysteriumClient(settings, token_store=store) as client:
            locations = client.list_locations(IPType.RESIDENTIAL)

        assert refresh_route.called
        assert locations_route.call_count == 2
        assert len(locations) == 1
        assert locations[0].country == "FR"
        assert locations[0].display_name() == "France"
        assert locations[0].cities[0].city == "paris"
        assert store.load().access_token.get_secret_value() == "new-acc"

    @respx.mock
    def test_connect_and_disconnect_and_limit_exceeded(self, tmp_path: Path) -> None:
        """Connect, raise APIError when limit_exceeded is true, and disconnect by public key."""
        settings = SettingsFactory.build(tmp_path)
        store = TokenStore(settings.state_directory)
        store.save(OAuthTokens(access_token=SecretStr("acc"), refresh_token=SecretStr("ref")))

        respx.post(f"{API_BASE_URL}/connection/connect").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "id": "sess-1",
                        "exit_ip": "198.51.100.1",
                        "ip_type": "residential",
                        "country": "FR",
                        "city": "paris",
                        "limit_exceeded": False,
                        "wg_config": "[Interface]\nPrivateKey = %private_key%\n",
                    },
                ),
                httpx.Response(200, json={"limit_exceeded": True}),
            ]
        )
        disconnect_route = respx.get(f"{API_BASE_URL}/connection/disconnect").mock(return_value=httpx.Response(200))

        with MysteriumClient(settings, token_store=store) as client:
            conn = client.connect("pub-key-1", "fr", IPType.RESIDENTIAL, city="paris")
            assert conn.exit_ip == "198.51.100.1"
            assert conn.metadata().country == "FR"

            with pytest.raises(APIError, match="device limit reached"):
                client.connect("pub-key-1", "fr", IPType.RESIDENTIAL)

            client.disconnect("pub-key-1")

        assert disconnect_route.called
        assert disconnect_route.calls.last.request.url.params["public_key"] == "pub-key-1"


class TestTokenStore:
    def test_raises_when_missing_and_updates_fingerprint_on_save(self, tmp_path: Path) -> None:
        """Raise AuthenticationError when missing and change fingerprint when refreshed."""
        store = TokenStore(tmp_path / "empty")
        assert not store.exists()
        assert store.fingerprint() is None
        with pytest.raises(AuthenticationError):
            store.load()

        store.save(OAuthTokens(access_token=SecretStr("a1"), refresh_token=SecretStr("r1")))
        first_fp = store.fingerprint()
        assert first_fp is not None
        store.save(OAuthTokens(access_token=SecretStr("a2-longer"), refresh_token=SecretStr("r2-longer")))
        assert store.fingerprint() != first_fp
