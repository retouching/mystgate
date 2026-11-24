# Console & Logging

All terminal rendering and structured logging live under `mystgate/core/logging/`.

## Terminal Output (`mystgate/core/logging/terminal.py`)

- `Terminal` owns `stdout` and `stderr` text streams:
  - `stdout`: primary command output (generated WireGuard `.conf`, `--json` payloads, plain tables, key-value summaries). Must stay clean and pipeable.
  - `stderr`: status messages, panels, warnings, and errors.
- Never call bare `print()`.

## Structured Logging (`mystgate/core/logging/`)

- **`enums.py`**:
  - `LogColumn(StrEnum)`: fixed columns matching CLI workflows (`CLI`, `API`, `WIREGUARD`, `CONFIG`), with `width() -> int` returning `max(len(c) for c in cls)`.
  - `LogMarker(StrEnum)`: `DONE = "[+]"`, `SKIPPED = "[-]"`, `PROBLEM = "[!]"`.
- **`constants.py`**:
  - `CONSOLE_ONLY: Final = MappingProxyType({"console_only": True})`
  - `UNREDACTED: Final = MappingProxyType({"unredacted": True, "console_only": True})`
- **`context.py`** — `LogContext`: `ContextVar`s for `log_depth` (default `0`) and `log_column` (default `None`), with `@classmethod @contextmanager def nested()`, `column(name)`, and `keep_place(record)`.
- **`redactor.py`** — `Redactor`:
  - Redacts URL passwords (`://user:pass@host` -> `://user:<redacted>@host`).
  - Redacts `password`, `secret`, `token`, `private_key`, `preshared_key`, `access_token`, `refresh_token` followed by `:` or `=` (case-insensitive).
  - Redacts every secret returned by `Settings.secrets()` as a whole value (sorted longest-first, boundary-aware on `[\w-]`).
- **`indented_formatter.py`** — `IndentedFormatter(logging.Formatter)`: prepends `"  " * log_depth`.
- **`formatter.py`** — `ConsoleFormatter(IndentedFormatter)`:
  - Format: `HH:MM:SS [L] <column:<width> : <message>` in UTC (`time.gmtime`).
  - Levels: `[D]` grey, `[I]` cyan, `[W]` yellow, `[E]` red.
  - Markers: `[+]` green, `[-]` grey, `[!]` yellow (`WARNING`) or red (`ERROR+`).
  - Respects `isatty()`, `NO_COLOR`, and `TERM != "dumb"`.
- **`files/log_files.py`** — `LogFiles`: `RotatingFileHandler` on `<log_directory>/mystgate.log` (`10 MiB` max, `5` backups, UTF-8), skipping `record.console_only`.
- **`files/json_formatter.py`** — `JSONFormatter`: one JSON line per event (`time`, `level`, `logger`, `column`, `message`, optional `exception`), passed through `Redactor`.
- **`session.py`** — `LoggingSession`: context manager attaching console (`stderr`, `DEBUG` if `settings.debug` else `INFO`) and rotating JSON file handler (`DEBUG`) to logger `mystgate` (`propagate = False`). Raises `LoggingError` when the log directory is invalid or unwritable.
