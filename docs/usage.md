# Usage

This guide covers installing `mystgate`, signing in to Mysterium VPN, listing countries, generating or rotating WireGuard configs, disconnecting sessions, options, exit codes, and logs.

## Commands

```text
mystgate [--version | -V] COMMAND [OPTIONS]
```

| Command | Role |
|---|---|
| `auth` | Sign in to Mysterium VPN via browser approval and save OAuth tokens |
| `status` | Show local authentication, WireGuard keypair, and last session status |
| `countries` | List available countries with merged cities, availability, and IP types |
| `connect` | Create or rotate a `0600` WireGuard `.conf` file (or print it to `stdout`) |
| `disconnect` | Release a server-side WireGuard session by public key |

## 1. Sign In (`auth`)

Mysterium VPN uses passwordless browser approval:

```bash
uv run mystgate auth
```

1. `mystgate` prints an approval URL to `stderr` and waits up to 5 minutes.
2. Open the link in any browser, sign in to your Mysterium account, and approve the CLI.
3. Tokens are saved atomically with `0600` permissions in `tokens.json`. Expired access tokens refresh automatically on `HTTP 401`.

## 2. Check Local Status (`status`)

```bash
uv run mystgate status
uv run mystgate status --json
```

| Option | Default | Role |
|---|---|---|
| `--json` | `false` | Output local status as JSON on `stdout` |

## 3. List Available Countries (`countries`)

```bash
uv run mystgate countries
uv run mystgate countries --type residential
uv run mystgate countries --type hosting
uv run mystgate countries --type residential --json
```

| Option | Default | Role |
|---|---|---|
| `--type`, `-t` | `all` | Filter by IP type (`residential`, `hosting`, or `all`) |
| `--json` | `false` | Output countries as JSON on `stdout` |

## 4. Generate, Switch Location, or Rotate a WireGuard Config (`connect`)

```bash
uv run mystgate connect --country FR --type residential
uv run mystgate connect --country FR --city paris --type residential -o fr-paris.conf
uv run mystgate connect --country US --type hosting --stdout > us.conf
```

| Option | Default | Role |
|---|---|---|
| `--country`, `-c` | *(required)* | Two-letter ISO country code (e.g. `FR`, `US`) |
| `--city` | *(none)* | Optional city identifier |
| `--type`, `-t` | `residential` | IP type (`residential` or `hosting`) |
| `--output`, `-o` | `<state_dir>/wg.conf` | Output path for the WireGuard `.conf` file |
| `--force`, `-f` | `false` | Overwrite the output file if it already exists |
| `--stdout` | `false` | Print the rendered WireGuard config to `stdout` without writing a file |
| `--from-config` | *(none)* | Reuse the private key from an existing `.conf` file to switch location or rotate IP |
| `--new-key` | `false` | Generate a new WireGuard keypair (uses a separate device slot) |
| `--json` | `false` | Output session metadata as JSON on `stdout` |

### Changing Country or Rotating IP on the Same Key

Each WireGuard keypair occupies one device slot on your Mysterium account. By default, `connect` reuses your saved keypair and sends `reset_connection: true`, replacing the session on the same slot:

```bash
uv run mystgate connect --country DE --type residential
uv run mystgate connect --from-config fr-paris.conf --country FR --type residential -o fr-paris.conf --force
```

To allocate a separate device slot with a new keypair:

```bash
uv run mystgate connect --country JP --type residential --new-key -o jp.conf
```

If your account hits its device limit, remove unused slots at `https://app.mysteriumvpn.com/dashboard/devices`.

## 5. Disconnect a Session (`disconnect`)

```bash
uv run mystgate disconnect
uv run mystgate disconnect --config fr-paris.conf
uv run mystgate disconnect --public-key "<base64-public-key>"
```

| Option | Default | Role |
|---|---|---|
| `--config` | *(none)* | Derive the public key locally from a `.conf` file and disconnect it |
| `--public-key` | *(none)* | Disconnect a specific WireGuard public key |

## 6. Console Output and Logs

- **`stdout`**: primary data output (`--stdout`, `--json`, aligned tables, key-value summaries) so commands stay pipeable.
- **`stderr`**: status messages, warnings, errors, and structured logs (`HH:MM:SS [L] <column> : <message>` in UTC when `MYSTGATE_DEBUG=true`). Colors disable automatically on non-TTY streams, `NO_COLOR`, or `TERM=dumb`.
- **Log files**: one JSON object per line in `<MYSTGATE_LOG_DIRECTORY>/mystgate.log` (`DEBUG` level), rotated at `10 MiB` with `5` backups.
- **Redaction**: passwords, tokens, private keys, preshared keys, and configured secrets are masked automatically in console and file logs.

## 7. Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Unclassified application error |
| `2` | Invalid configuration or CLI usage error |
| `3` | Mysterium API request or response error |
| `4` | Authentication required or rejected |
| `5` | WireGuard key or configuration error |
| `6` | Log directory error |
| `130` | Interrupted (`Ctrl+C`) |

## 8. Docker Gateway

See [Docker gateway](docker.md) to run `mystgate` as a WireGuard `wg0` + HTTP/SOCKS5 container with an `iptables` killswitch.
