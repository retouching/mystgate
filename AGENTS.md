# mystgate

`mystgate` is a Python CLI tool that talks to the Mysterium VPN API to generate and manage WireGuard configuration files (`auth`, `countries`, `connect`, `disconnect`, `status`). It uses a flat package layout (`mystgate/` at repository root, no `src/` folder) split into `mystgate/core/` and `mystgate/commands/`, `click` for the CLI, `pydantic` / `pydantic-settings` for data and environment configuration (`MYSTGATE_*` + `.env`), structured logging with secret redaction and rotating JSON log files, `httpx` for HTTP requests, and `cryptography` for WireGuard X25519 keys.

## Definition of done

Every change is done only when all of the following hold:

1. **Tests first (TDD)**: write or update unit tests in `tests/unit/` covering the change, with network access disabled (`pytest-socket`). Run only the changed unit test files during iterations (`uv run pytest tests/unit/<changed>`).
2. **All checks pass with zero warnings or skipped failures**:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy`
   - `uv run lint-imports`
   - `uv run pytest` (full unit suite; skip if a push is planned since `pre-push` runs it)
   - `uv run pytest tests/integration/<changed>` / `uv run pytest tests/e2e/<changed>` when those areas changed
   - `uv run --isolated --no-dev --group test mystgate --help`
   - `uv run --isolated --no-dev --group test pytest`
3. **Zero ignored failures**: fix every failing test, warning, lint, type, or import-contract error encountered (even if it looks pre-existing or unrelated) and every minor issue found during review.
4. **Docs stay in sync**: user-visible CLI, Docker, or configuration changes update `README.md`, `docs/*.md`, and `.env.example` in the same commit; architectural or rule changes update `AGENTS.md` and `docs/agents/*.md` in the same commit.
5. **Hooks**: never run `pre-commit run` by hand; Git triggers `commit-msg`, `pre-commit`, and `pre-push` hooks automatically.

## Before you change a part

Read the matching page before editing:

| Area | Guide |
|---|---|
| Packages, import boundaries, CLI routing, exit codes | [docs/agents/architecture.md](docs/agents/architecture.md) |
| Settings, environment variables, secrets, `.env.example` | [docs/agents/configuration.md](docs/agents/configuration.md) |
| Terminal output, `core/logging/`, redaction, rotating JSON logs | [docs/agents/console.md](docs/agents/console.md) |
| Unit/integration/e2e tests, fakes, `pytest-socket`, layout checks | [docs/agents/tests.md](docs/agents/tests.md) |
| Local skills (`sketch`, `plan`, `execute`) and per-runtime agents | [docs/agents/workflow.md](docs/agents/workflow.md) |

## Rules of the layout

These 14 rules hold across the entire repository, including `tests/`. Every rule is enforced by code review, `ruff`, `mypy`, `import-linter`, or `tests/unit/test_layout.py`.

1. **One subject per file.**
   - One public class per file (with constants used only by that class), except `models.py` and `schemas.py` which may group Pydantic models.
   - Fixed filenames inside any package: `models.py`, `schemas.py`, `enums.py`, `exceptions.py`, `constants.py`, `types.py`.
   - Any other file is named in `snake_case` after its class without the package's leading words, never plural for one class.
   - Exception, log, and console messages use `message(subject, outcome, *causes)` from `mystgate.core.utils` and never contain secrets.
2. **One subject per folder.** Split multi-subject folders into sub-packages (`core/utils/`, `core/logging/`, `core/logging/files/`, `core/wireguard/`, `core/mysterium/`, `core/vpn/`, `commands/`).
3. **An object does its own work.** Operations on one object belong to its class (`Settings`, `Redactor`, `LoggingSession`, `Terminal`, `KeyGenerator`, `ConfigWriter`, `MysteriumClient`, `TokenStore`, `StateStore`).
4. **A collection does the work of the collection.** Collection classes filter, merge, and sort their items without unrelated orchestration or I/O.
5. **Coordination with business rules gets its own class.** Multi-object workflows live in `mystgate/core/vpn/` (`Authenticator`, `LocationCatalog`, `ConnectionManager`), receiving dependencies via `__init__` and never importing `click`, `httpx`, or `cryptography`.
6. **Variable rules are composed, not inherited.** Express variable rule lists as small concrete classes composed in an ordered list rather than inheritance chains.
7. **Code lives with its users — declare no `Protocol`.** Keep code in the package that uses it, in the closest common parent, or in `core/utils/` if it knows nothing of `mystgate`. Never declare `Protocol`; annotate with concrete classes and subclass them for fakes in `tests/`. `mystgate` never imports `tests`.
8. **`core/utils/` is generic.** Function modules use plural nouns (`messages.py`, `files.py`, `texts.py`); single-class files are named after the class (`clock.py`, `monotonic.py`); `core/utils/__init__.py` re-exports public names via `__all__`. `core/utils/` imports nothing from `mystgate`.
9. **Commands only route.** Files in `mystgate/commands/` declare `click.Command` / `click.Group` classes, load `Settings`, build frozen input models (`ConnectOptions`), open `LoggingSession`, invoke `mystgate.core`, and render output through `Terminal`. Zero business logic, zero direct HTTP calls, zero bare `print()`.
10. **Strict import direction.** Enforced by `import-linter`:
    - `core.utils` imports nothing from `mystgate`.
    - `core.exceptions` imports only `core.utils`.
    - `core.config`, `core.logging`, and `core.wireguard` import only `core.utils` and `core.exceptions`.
    - `core.mysterium` imports only `core.config`, `core.logging`, `core.utils`, and `core.exceptions`.
    - `core.vpn` never imports `click`, `httpx`, `cryptography`, or `commands`.
    - `core` never imports `commands`.
    - `commands` is imported by `__main__` and `tests` alone.
    - `mystgate` never imports `tests`; `tests.e2e` never imports `mystgate`.
11. **Everything is a class.** In `mystgate/core/` (outside `core/utils/`) and `mystgate/commands/`, all functions are methods of a class. Module-level functions exist only in `core/utils/`. CLI commands and groups are subclasses of `click.Command` / `click.Group`.
12. **Configuration is one subject of strict Pydantic models.** Single frozen `Settings(BaseSettings)` in `mystgate/core/config.py`, reading `MYSTGATE_*` from environment / `.env` (`SecretStr` for secrets), loaded once per command via `Settings.load()`. `.env.example` stays synchronized and verified by `tests/unit/core/test_config.py`.
13. **External tools and specialized libraries are isolated.** Enforced by `ruff` `TID251` and `import-linter`:
    - No subprocesses anywhere outside `tests/stacks/docker_stack.py`.
    - `httpx` is imported in `mystgate.core.mysterium` (and `tests`) alone.
    - `cryptography` is imported in `mystgate.core.wireguard` alone.
14. **Uniform errors and exit codes.** Every domain failure raises a subclass of `MystgateError` in `mystgate/core/exceptions.py` with `exit_code: ClassVar[int]`. `Mystgate.run()` catches `MystgateError`, `click.ClickException`, and `(click.Abort, KeyboardInterrupt)` (exit code `130`), writes to `stderr`, and never leaks secrets.

## Rules of the code

These rules apply to both `mystgate/` and `tests/`:

- **Pydantic everywhere, never `dataclasses`.** Every data model is a Pydantic `BaseModel`. `ruff` bans `dataclasses` via `TID251`.
- **Docstrings**: every method and function has an imperative docstring (`"""Generate a WireGuard keypair."""`), enforced by `D401`. Nothing else has a docstring (no module, class, or constant docstrings).
- **No `#` comments**, except `# noqa: <CODE>` and `# type: ignore[<code_name>]` (and YAML/TOML/INI/Dockerfile config files).
- **No leading `_` names**: no module, class, function, method, parameter, attribute, or constant may start with `_`. Lone `_` for discarded values and Python dunders are allowed.
- **Constants**: extract a `Final` (or `ClassVar[...]`) `UPPER_CASE` constant only for tunable values, import-time compiled objects, or non-text values shared across two or more places; use `MappingProxyType` for dicts.
- **Imports & exports**: package `__init__.py` re-exports public names via `__all__`; other packages import from the package; sibling modules import each other by full module path; type-only imports use `from __future__ import annotations` and `if TYPE_CHECKING:`.
- **Strict typing**: `mypy --strict`, `warn_unreachable = true`, `disallow_any_unimported = true`. Never use `Any` or `dict` casts where a static base or Pydantic model applies.
- **Acronyms in class names** are uppercase: `APIError`, `WireGuardError`, `CLI`, `JSONFormatter`, `HTTP`.
- **Symmetric class naming**: qualify every variant of a concept explicitly rather than leaving one bare alongside a qualified variant.
- **Language**: all code, docstrings, logs, user/agent docs, and commit messages are in English.

## Documents

Keep human documentation and AI agent documentation strictly separate:

- **Human docs** (`README.md`, `docs/usage.md`, `docs/configuration.md`, `docs/docker.md`, `docs/mysterium-api.md`, `.env.example`) describe installation, configuration, CLI usage, Docker operation, and the Mysterium HTTP API only. Never mention internal Python classes, modules, or test fakes, and never mention or link to `AGENTS.md`, `CLAUDE.md`, `docs/agents/`, `.agents/`, `.antigravity/`, `.claude/`, or `.codex/`.
- **AI agent docs** (`AGENTS.md`, symlinked as `CLAUDE.md`, and `docs/agents/*.md`) hold architecture, code rules, logging, configuration, test conventions, and agent workflow. Never use `AGENTS.md` as a contributor link for humans.

## Git

- **Conventional Commits** in English (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `build:`, `chore:`, `ci:`), `!` for breaking changes without a `BREAKING CHANGE:` footer.
- **Atomic commits**: small, focused commits passing all checks, committed directly on the current branch unless a branch is requested. Fold late fixes with `--fixup` + `--autosquash` before push.
- **No attribution footers**: no `Co-Authored-By` lines or AI-generated notices.
- **Never push** without asking the owner.

## Working with the owner

- Build only what is asked.
- Ask open design choices one question at a time with concrete options and a recommendation.
- Ask before dispatching subagents unless the owner invokes `execute`.
- Feature changes follow `sketch` -> `plan` -> `execute`, with specs and plans stored in `~/.cache/mystgate/scratchpad/{specs,plans}/` (never in `/tmp` or inside the repository).

## Hooks

`.pre-commit-config.yaml` installs `commit-msg`, `pre-commit`, and `pre-push` hooks via `uv run pre-commit install`. Never run `pre-commit run` by hand.

## Commands

```bash
uv sync
uv run pre-commit install
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run lint-imports
uv run pytest
uv run mystgate --help
```
