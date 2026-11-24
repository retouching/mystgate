# Configuration

## Loading Rules

All configuration lives in a single frozen `Settings(BaseSettings)` class in `mystgate/core/config.py`:

- Environment prefix: `MYSTGATE_`
- Reads environment variables first, then `.env` (`extra="ignore"`, `frozen=True`).
- Loaded once per command via `Settings.load()`.
- Validation errors raise `ConfigurationError(message("Configuration", "invalid", *causes))` with `exit_code = 2`, listing refused `MYSTGATE_*` variables in field order without ever echoing secret values.

## Baseline Variables

| Variable | Type | Default | Role |
|---|---|---|---|
| `MYSTGATE_STATE_DIRECTORY` | `Path` | `.mystgate/session` | Local state directory (`tokens.json`, `keypair.json`, `session.json`, `.conf`) |
| `MYSTGATE_LOG_DIRECTORY` | `Path` | `.mystgate/logs` | Directory for rotating JSON log files |
| `MYSTGATE_DEBUG` | `bool` | `False` | Enable `DEBUG` console logging |
| `MYSTGATE_PROXY_USER` | `str \| None` | `None` | Optional proxy username |
| `MYSTGATE_PROXY_PASS` | `SecretStr \| None` | `None` | Optional proxy password (never logged) |

Fixed endpoints (`API_BASE_URL`, `AUTHORIZE_URL`), timeouts, retry counts, and file size limits do not belong in `Settings`; keep them as `Final` constants on their owning module/class.

## Secrets & `.env.example`

- Every secret field uses `pydantic.SecretStr`.
- `Settings.secrets()` returns a `tuple[str, ...]` of all non-empty secret values to register in `Redactor`.
- `.env.example` lists every `MYSTGATE_*` variable with safe copyable defaults and empty values for secrets.
- `tests/unit/core/test_config.py` verifies that `.env.example` stays in sync with `Settings` fields and never embeds real secret values.

## Checklist to Add a Variable

1. Add the typed field and validator to `Settings` in `mystgate/core/config.py`.
2. If it is a secret, type it as `SecretStr` and include it in `Settings.secrets()`.
3. Add it to `.env.example` (empty if secret).
4. Add unit tests in `tests/unit/core/test_config.py` covering defaults, valid values, and validation errors.
5. Update `docs/configuration.md`, `README.md` (if needed), and `docs/agents/configuration.md` in the same commit.
