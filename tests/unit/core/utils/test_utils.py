import stat
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from mystgate.core.utils import Clock, Monotonic, message, parse_duration, printable, write_private


class TestUtils:
    def test_message_formats_with_and_without_causes(self) -> None:
        """Format messages cleanly with optional non-empty causes."""
        assert message("Configuration", "invalid") == "Configuration: invalid"
        assert message("Configuration", "invalid", "missing key", "", "bad url") == (
            "Configuration: invalid (missing key, bad url)"
        )

    @given(st.text())
    def test_printable_always_produces_printable_text(self, value: str) -> None:
        """Ensure printable() removes every control character for arbitrary inputs."""
        cleaned = printable(value)
        assert all(ch.isprintable() for ch in cleaned)

    @given(
        st.integers(min_value=1, max_value=10000),
        st.sampled_from(["", "s", "m", "h", "d"]),
    )
    def test_parse_duration_positive_for_valid_inputs(self, amount: int, unit: str) -> None:
        """Return a strictly positive float for any valid positive duration string."""
        seconds = parse_duration(f"{amount}{unit}")
        assert seconds > 0

    def test_parse_duration_rejects_invalid_values(self) -> None:
        """Reject malformed or non-positive duration strings."""
        with pytest.raises(ValueError, match="invalid duration"):
            parse_duration("abc")
        with pytest.raises(ValueError, match="positive"):
            parse_duration("0s")

    def test_write_private_creates_0600_file_atomically(self, tmp_path: Path) -> None:
        """Write sensitive content with 0600 file mode and 0700 parent directory."""
        target = tmp_path / "secure" / "secret.txt"
        write_private(target, "secret-data")
        assert target.read_text(encoding="utf-8") == "secret-data"
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700

    def test_clock_and_monotonic_return_values(self) -> None:
        """Return a timezone-aware UTC datetime and a float monotonic timestamp."""
        now = Clock.now()
        assert now.tzinfo is not None
        assert isinstance(Monotonic()(), float)
