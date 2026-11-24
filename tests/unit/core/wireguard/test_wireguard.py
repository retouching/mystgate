import stat
from pathlib import Path

import pytest

from mystgate.core.exceptions import WireGuardError
from mystgate.core.wireguard import ConfigWriter, KeyGenerator


class TestWireGuard:
    def test_generate_derive_and_from_config_file(self, tmp_path: Path) -> None:
        """Generate a keypair, write a rendered config, and recover the same keypair from it."""
        pair = KeyGenerator.generate()
        private_value = pair.private_key.get_secret_value()
        assert private_value != pair.public_key
        assert KeyGenerator.derive_public_key(private_value) == pair.public_key
        assert private_value not in repr(pair)

        template = "[Interface]\nPrivateKey = %private_key%\nAddress = 10.0.0.2/32\n\n[Peer]\nPublicKey = peer\n"
        destination = tmp_path / "wg0.conf"
        ConfigWriter.write_template(template, pair, destination)

        assert stat.S_IMODE(destination.stat().st_mode) == 0o600
        recovered = KeyGenerator.from_config_file(destination)
        assert recovered.public_key == pair.public_key
        assert recovered.private_key.get_secret_value() == private_value

    def test_write_template_refuses_overwrite_unless_requested(self, tmp_path: Path) -> None:
        """Refuse overwriting an existing config file unless overwrite is True."""
        pair = KeyGenerator.generate()
        template = "[Interface]\nPrivateKey = %private_key%\n"
        destination = tmp_path / "wg0.conf"
        ConfigWriter.write_template(template, pair, destination)

        with pytest.raises(WireGuardError):
            ConfigWriter.write_template(template, pair, destination, overwrite=False)

        ConfigWriter.write_template(template, pair, destination, overwrite=True)

    def test_invalid_key_and_template_errors(self, tmp_path: Path) -> None:
        """Raise WireGuardError on malformed keys or missing placeholders."""
        with pytest.raises(WireGuardError):
            KeyGenerator.derive_public_key("not-base64!!!")
        with pytest.raises(WireGuardError):
            KeyGenerator.derive_public_key("AAAA")

        pair = KeyGenerator.generate()
        with pytest.raises(WireGuardError):
            ConfigWriter.render_template("[Interface]\nAddress = 10.0.0.2/32\n", pair)

        bad_file = tmp_path / "bad.conf"
        bad_file.write_text("[Interface]\nAddress = 10.0.0.2/32\n", encoding="utf-8")
        with pytest.raises(WireGuardError):
            KeyGenerator.from_config_file(bad_file)
