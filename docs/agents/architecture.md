# Architecture

## Package Map

Flat layout at repository root (`mystgate/`, no `src/` folder), split into `core/` and `commands/`:

```text
mystgate/
├── __init__.py              Package metadata
├── __main__.py              Mystgate(click.Group) entrypoint and exit-code translation
├── core/
│   ├── __init__.py
│   ├── exceptions.py        MystgateError hierarchy with exit_code: ClassVar[int]
│   ├── config.py            Settings(BaseSettings) reading MYSTGATE_* and .env
│   ├── utils/               Generic helpers (Clock, Monotonic, files, messages, texts)
│   ├── logging/             Structured stderr logging, Redactor, Terminal, LoggingSession
│   │   └── files/           Rotating JSON log files (LogFiles, JSONFormatter)
│   ├── wireguard/           X25519 key generation, WireGuard Pydantic models, 0600 config writer
│   ├── mysterium/           Mysterium VPN HTTP client, API schemas, and TokenStore
│   └── vpn/                 Domain coordination (Authenticator, LocationCatalog, ConnectionManager, StateStore)
└── commands/                Thin click.Command subclasses routing to core/ (auth, connect, countries, disconnect, status)
```

## Import Boundaries

Enforced by `import-linter` (`uv run lint-imports`):

| Package | Allowed internal imports | Restricted external libraries |
|---|---|---|
| `core.utils` | none | none |
| `core.exceptions` | `core.utils` | none |
| `core.config` | `core.utils`, `core.exceptions` | none |
| `core.logging` | `core.utils`, `core.exceptions` | none |
| `core.wireguard` | `core.utils`, `core.exceptions` | sole importer of `cryptography` |
| `core.mysterium` | `core.config`, `core.logging`, `core.utils`, `core.exceptions` | sole importer of `httpx` (plus `tests`) |
| `core.vpn` | `core.config`, `core.exceptions`, `core.logging`, `core.mysterium`, `core.utils`, `core.wireguard` | never imports `click`, `httpx`, `cryptography` |
| `core` | never imports `commands` | none |
| `commands` | `core` packages; imported by `__main__` and `tests` alone | never imports `httpx` or `cryptography` directly |

`mystgate` never imports `tests`; `tests.e2e` never imports `mystgate`.

## CLI Entrypoint & Exit Codes

`Mystgate(click.Group)` in `mystgate/__main__.py` registers `--version` / `-V` (via `importlib.metadata.version("mystgate")`) and attaches command classes from `mystgate.commands`.

`Mystgate.run(arguments=None, *, commands=None) -> int` invokes Click with `standalone_mode=False` and maps failures deterministically:

- `MystgateError` -> renders error to `stderr`, returns `error.exit_code` (`1` base, `2` configuration, `3` API, `4` authentication, `5` WireGuard, `6` logging)
- `click.ClickException` -> renders to `stderr`, returns `error.exit_code`
- `(click.Abort, KeyboardInterrupt)` -> renders `Command: interrupted` to `stderr`, returns `130`
