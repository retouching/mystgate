# Tests

## Three-Level Layout

```text
tests/
├── constants.py              ROOT and shared test constants
├── support/                  Shared fakes/factories across levels (Isolation, FakeClock, JSONLog, SettingsFactory)
├── stacks/
│   └── docker_stack.py       DockerStack (sole test file exempt from subprocess TID251)
├── unit/
│   ├── conftest.py           pytest-socket + autouse Isolation
│   ├── support/              Unit-only fakes (FakeMonotonic, ColumnRecorder)
│   ├── test_layout.py        AST rules (no comments, no Protocol, no leading _, docstrings, Test* classes)
│   ├── test_main.py          Root CLI group and exit-code translation
│   ├── core/                 Mirrors mystgate/core/ (test_config.py, utils/, logging/, wireguard/, mysterium/, vpn/)
│   └── commands/             Mirrors mystgate/commands/
├── integration/
│   ├── conftest.py           autouse Isolation
│   └── core/                 Real filesystem, .env, 0600 state, and rotating JSON log integration tests
└── e2e/
    ├── e2e_test.py           E2ETest base attaching class-scoped DockerStack
    └── test_commands.py      Black-box container tests (imports nothing from mystgate)
```

## Rules

- **Classes everywhere**: every test is a method inside `class Test<Class>:` (enforced by `tests/unit/test_layout.py`).
- **Network disabled in unit tests**: `tests/unit/conftest.py` calls `pytest_socket.disable_socket(allow_unix_socket=True)` and runs `Isolation.apply(tmp_path, monkeypatch)` automatically.
- **No `Protocol` fakes, no `unittest.mock.patch`**: test fakes subclass the real concrete class. Use `respx` / `httpx.MockTransport` for HTTP.
- **Hypothesis invariants**: use `@given(...)` for text/parser/security invariants (`printable`, `parse_duration`, `Redactor`).
- **Black-box E2E**: `tests/e2e/` never imports `mystgate` (enforced by `import-linter`).
- **Temp files**: pass `--basetemp ~/.cache/mystgate/scratchpad/tmp/pytest`, never `/tmp`.
- **Zero ignored failures**: fix every failing test, warning, lint, or type error encountered (even if it looks pre-existing or unrelated) and every minor issue found during review.

## Execution Cadence

| Moment | Command |
|---|---|
| **During an iteration (RED & GREEN)** | `uv run pytest tests/unit/<changed_test_files> --basetemp ~/.cache/mystgate/scratchpad/tmp/pytest` |
| **End of feature (integration)** | `uv run pytest tests/integration/<changed_test_files> --basetemp ~/.cache/mystgate/scratchpad/tmp/pytest` |
| **End of feature (e2e)** | `uv run pytest tests/e2e/<changed_test_files> --basetemp ~/.cache/mystgate/scratchpad/tmp/pytest` |
| **End of work (no push planned)** | `uv run pytest --basetemp ~/.cache/mystgate/scratchpad/tmp/pytest` |
| **After dependency / `pyproject.toml` change** | `uv run --isolated --no-dev --group test mystgate --help && uv run --isolated --no-dev --group test pytest` |
