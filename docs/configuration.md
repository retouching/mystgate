# Configuration

`mystgate` reads settings from environment variables with the `MYSTGATE_` prefix and from a `.env` file in the working directory. Environment variables override `.env`.

Invalid settings stop the command immediately with exit code `2` and print the refused variables to `stderr` without echoing any secret value:

```text
Error: Configuration: invalid (MYSTGATE_DEBUG: Input should be a valid boolean)
```

## `.env.example`

```dotenv
MYSTGATE_STATE_DIRECTORY=.mystgate/session
MYSTGATE_LOG_DIRECTORY=.mystgate/logs
MYSTGATE_DEBUG=false
MYSTGATE_PROXY_USER=
MYSTGATE_PROXY_PASS=
```

## CLI Variables

| Variable | Default | Role |
|---|---|---|
| `MYSTGATE_STATE_DIRECTORY` | `.mystgate/session` | Directory storing `tokens.json`, `keypair.json`, `session.json`, and `wg.conf` (`0600`) |
| `MYSTGATE_LOG_DIRECTORY` | `.mystgate/logs` | Directory for rotating JSON log files (`mystgate.log`) |
| `MYSTGATE_DEBUG` | `false` | Enables `DEBUG` console logging on `stderr` |
| `MYSTGATE_PROXY_USER` | *(empty)* | Optional username for the Docker HTTP/SOCKS5 proxy |
| `MYSTGATE_PROXY_PASS` | *(empty)* | Optional password for the Docker HTTP/SOCKS5 proxy (secret) |

Empty strings for `MYSTGATE_STATE_DIRECTORY` or `MYSTGATE_LOG_DIRECTORY` fall back to their default paths. Empty strings for `MYSTGATE_PROXY_USER` or `MYSTGATE_PROXY_PASS` are treated as unset.

## Docker Gateway Variables

Used by the Docker gateway container (`docker/compose.yaml`):

| Variable | Default | Role |
|---|---|---|
| `MYSTGATE_COUNTRY` | `FR` | Two-letter uppercase ISO country code (`mystgate countries` to list) |
| `MYSTGATE_CITY` | *(empty)* | Optional city slug (for example `paris`, `dubai`) |
| `MYSTGATE_IP_TYPE` | `residential` | Exit node type: `residential` or `hosting` |
| `MYSTGATE_HEALTH_INTERVAL` | `30` | Seconds between `1.1.1.1` healthchecks on `wg0` |
| `MYSTGATE_MAX_FAILURES` | `3` | Consecutive failed healthchecks before automatic rotation |
| `MYSTGATE_ROTATE_EVERY` | *(empty)* | Optional periodic rotation interval in seconds (empty rotates only on health failure) |
| `MYSTGATE_HTTP_PORT` | `8080` | HTTP proxy port inside the container (`0` disables) |
| `MYSTGATE_SOCKS_PORT` | `1080` | SOCKS5 proxy port inside the container (`0` disables) |

## Secrets

- Leave secrets empty in `.env.example` and never commit `.env`.
- Secret values (`MYSTGATE_PROXY_PASS`), OAuth tokens, and WireGuard private keys are redacted automatically from console output, error messages, and JSON log files.
- State files (`tokens.json`, `keypair.json`, `session.json`, and generated `.conf` files) are written atomically with `0600` permissions.
