import io
import logging
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from mystgate.core.exceptions import LoggingError
from mystgate.core.logging import CONSOLE_ONLY, LogColumn, LogContext, LoggingSession, LogMarker, Redactor
from tests.support import JSONLog


class TestRedactor:
    def test_scrubs_urls_key_values_and_configured_secrets(self) -> None:
        """Redact passwords in URLs, sensitive key-value pairs, and explicit secrets."""
        redactor = Redactor(["my-secret-value"])
        sample = "proxy=http://alice:hunter2@127.0.0.1:8080 private_key=ABC123 token=XYZ999 raw=my-secret-value"
        cleaned = redactor.scrub(sample)
        assert "hunter2" not in cleaned
        assert "ABC123" not in cleaned
        assert "XYZ999" not in cleaned
        assert "my-secret-value" not in cleaned
        assert "alice:<redacted>@127.0.0.1:8080" in cleaned

    @given(
        st.text(
            alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=" \t\n\r'\";,"),
            min_size=6,
            max_size=32,
        ).filter(lambda item: item not in "<redacted>")
    )
    def test_scrubs_arbitrary_token_values(self, secret: str) -> None:
        """Never leave a configured secret intact in scrubbed log text."""
        redactor = Redactor([secret])
        cleaned = redactor.scrub(f"event value={secret} end")
        assert cleaned == "event value=<redacted> end"
        assert secret not in cleaned


class TestLoggingSession:
    def test_writes_redacted_console_and_json_logs(self, tmp_path: Path) -> None:
        """Emit redacted console and JSON lines while skipping console-only records in files."""
        stream = io.StringIO()
        with (
            LoggingSession(tmp_path, debug=True, secrets=["secret-token"], stream=stream),
            LogContext.column(LogColumn.WIREGUARD),
        ):
            logger = logging.getLogger("mystgate.test")
            logger.info("%s Started with secret-token", LogMarker.DONE.value)
            with LogContext.nested():
                logger.debug("Nested secret-token detail")
            logger.info("Console only line", extra=dict(CONSOLE_ONLY))

        console_output = stream.getvalue()
        assert "secret-token" not in console_output
        assert "<redacted>" in console_output
        assert "wireguard" in console_output
        assert "  Nested <redacted> detail" in console_output
        assert "Console only line" in console_output

        records = JSONLog.read(tmp_path)
        assert len(records) == 2
        assert all("secret-token" not in str(record["message"]) for record in records)
        assert records[0]["column"] == "wireguard"

    def test_raises_when_directory_is_a_file(self, tmp_path: Path) -> None:
        """Raise LoggingError when the configured log directory path is a regular file."""
        file_path = tmp_path / "not-a-dir"
        file_path.write_text("x", encoding="utf-8")
        with pytest.raises(LoggingError) as info, LoggingSession(file_path):
            pass
        assert info.value.exit_code == 6
