from pathlib import Path

import httpx
import respx
from pydantic import SecretStr

from mystgate.core.config import Settings
from mystgate.core.mysterium import IPType, MysteriumClient, OAuthTokens, TokenStore
from mystgate.core.mysterium.client import API_BASE_URL
from mystgate.core.vpn import (
    Authenticator,
    ConnectionManager,
    ConnectOptions,
    LocationCatalog,
    StateStore,
)
from mystgate.core.wireguard import KeyGenerator
from tests.support import SettingsFactory
from tests.unit.support import FakeMonotonic


class TestVPN:
    @staticmethod
    def make_authed_client(tmp_path: Path) -> tuple[Settings, TokenStore, StateStore, MysteriumClient]:
        """Build isolated settings, stores, and an authenticated MysteriumClient."""
        settings = SettingsFactory.build(tmp_path)
        token_store = TokenStore(settings.state_directory)
        token_store.save(OAuthTokens(access_token=SecretStr("acc"), refresh_token=SecretStr("ref")))
        state_store = StateStore(settings.state_directory)
        client = MysteriumClient(settings, token_store=token_store)
        return settings, token_store, state_store, client

    @respx.mock
    def test_location_catalog_merges_countries_cities_and_types(self, tmp_path: Path) -> None:
        """Merge residential and hosting locations per country with deduplicated available cities."""
        _, _, _, client = self.make_authed_client(tmp_path)
        respx.get(f"{API_BASE_URL}/connection/config/locations", params={"ip_type": "residential"}).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "country": "FR",
                        "is_available": True,
                        "translations": {"en": "France"},
                        "cities": [
                            {"city": "paris", "is_available": True, "translations": {"en": "Paris"}},
                            {"city": "lyon", "is_available": False, "translations": {"en": "Lyon"}},
                        ],
                    }
                ],
            )
        )
        respx.get(f"{API_BASE_URL}/connection/config/locations", params={"ip_type": "hosting"}).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "country": "FR",
                        "is_available": True,
                        "translations": {"en": "France"},
                        "cities": [
                            {"city": "paris", "is_available": True, "translations": {"en": "Paris"}},
                            {"city": "marseille", "is_available": True, "translations": {"en": "Marseille"}},
                        ],
                    },
                    {
                        "country": "DE",
                        "is_available": True,
                        "translations": {"en": "Germany"},
                        "cities": [],
                    },
                ],
            )
        )

        with client:
            rows = LocationCatalog(client).list_countries(None)

        assert [row.code for row in rows] == ["DE", "FR"]
        fr = rows[1]
        assert fr.name == "France"
        assert fr.cities == ["Marseille", "Paris"]
        assert fr.available is True
        assert fr.ip_types == [IPType.RESIDENTIAL, IPType.HOSTING]

    @respx.mock
    def test_connection_manager_connect_from_config_and_disconnect(self, tmp_path: Path) -> None:
        """Reuse private key from an existing config file for rotation and disconnect."""
        _, _, state_store, client = self.make_authed_client(tmp_path)
        existing_pair = KeyGenerator.generate()
        existing_conf = tmp_path / "custom.conf"
        existing_conf.write_text(
            f"[Interface]\nPrivateKey = {existing_pair.private_key.get_secret_value()}\n",
            encoding="utf-8",
        )

        connect_route = respx.post(f"{API_BASE_URL}/connection/connect").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "s-1",
                    "exit_ip": "203.0.113.5",
                    "ip_type": "residential",
                    "country": "FR",
                    "city": "paris",
                    "limit_exceeded": False,
                    "wg_config": "[Interface]\nPrivateKey = %private_key%\n",
                },
            )
        )
        disconnect_route = respx.get(f"{API_BASE_URL}/connection/disconnect").mock(return_value=httpx.Response(200))

        with client:
            manager = ConnectionManager(client, state_store)
            options = ConnectOptions(
                country="FR",
                ip_type=IPType.RESIDENTIAL,
                city="paris",
                output=existing_conf,
                overwrite=True,
                from_config=existing_conf,
            )
            result = manager.connect(options)
            assert result.public_key == existing_pair.public_key
            assert connect_route.called

            disconnected_key = manager.disconnect(config_path=existing_conf)
            assert disconnected_key == existing_pair.public_key
            assert disconnect_route.called

    @respx.mock
    def test_authenticator_polls_and_saves_tokens(self, tmp_path: Path) -> None:
        """Poll activation until tokens arrive and persist them to TokenStore."""
        settings = SettingsFactory.build(tmp_path)
        token_store = TokenStore(settings.state_directory)
        respx.post(f"{API_BASE_URL}/auth/activation").mock(return_value=httpx.Response(200))
        respx.get(f"{API_BASE_URL}/auth/activation/act-9").mock(
            side_effect=[
                httpx.Response(200, json={"id": "act-9", "valid": True, "token": None}),
                httpx.Response(
                    200,
                    json={
                        "id": "act-9",
                        "valid": True,
                        "token": {"access_token": "a1", "refresh_token": "r1"},
                    },
                ),
            ]
        )

        monotonic = FakeMonotonic()
        with MysteriumClient(settings, token_store=token_store) as client:
            authenticator = Authenticator(
                client,
                token_store,
                monotonic=monotonic,
                sleep=monotonic.advance,
            )
            tokens = authenticator.wait_for_tokens("act-9", timeout_seconds=30.0, poll_interval_seconds=5.0)
            assert tokens.access_token.get_secret_value() == "a1"
            assert token_store.exists()
