# Docker Gateway Guide

`docker/Dockerfile`, `docker/compose.yaml`, and `docker/gateway.sh` run `mystgate` as a WireGuard VPN gateway with:

- A `wg0` WireGuard interface inside the container (`NET_ADMIN` + `/dev/net/tun`), shareable with other containers via `network_mode: "service:mystgate"`.
- An `iptables` VPN killswitch (`OUTPUT DROP` by default) preventing traffic leaks if `wg0` drops.
- Built-in HTTP (`8080`) and SOCKS5 (`1080`) proxy listeners via `pproxy` routed through `wg0`.
- Periodic `1.1.1.1` healthchecks, `api.ipify.org` exit-IP checks, automatic rotation on failure, and automatic resume when OAuth tokens are refreshed.

## 1. Quick Start

Build and start with Docker Compose:

```bash
cp .env.example .env
docker compose -f docker/compose.yaml build
docker compose -f docker/compose.yaml run --rm --entrypoint mystgate mystgate auth
docker compose -f docker/compose.yaml up -d
docker compose -f docker/compose.yaml logs -f
```

To build the image directly:

```bash
docker build -f docker/Dockerfile -t mystgate .
```

When ready, the container prints a single summary line:

```text
FR | residential | 88.171.204.238
```

Test the HTTP and SOCKS5 proxies:

```bash
curl -x http://127.0.0.1:8080 https://api.ipify.org?format=json
curl -x socks5h://127.0.0.1:1080 https://api.ipify.org?format=json
```

With proxy authentication enabled (`MYSTGATE_PROXY_USER` and `MYSTGATE_PROXY_PASS`):

```bash
curl -x http://USER:PASS@127.0.0.1:8080 https://api.ipify.org?format=json
curl -x socks5h://USER:PASS@127.0.0.1:1080 https://api.ipify.org?format=json
```

## 2. Environment Variables

Set these in `.env` or pass them before `docker compose`. See [Configuration](configuration.md) for the complete `MYSTGATE_*` reference (including state, logging, and secret handling).

| Variable | Default | Purpose |
|---|---|---|
| `MYSTGATE_COUNTRY` | `FR` | Two-letter ISO country code (`uv run mystgate countries` to list) |
| `MYSTGATE_CITY` | *(empty)* | Optional city slug (e.g. `paris`, `dubai`) |
| `MYSTGATE_IP_TYPE` | `residential` | `residential` or `hosting` |
| `MYSTGATE_HEALTH_INTERVAL` | `30` | Seconds between `1.1.1.1` healthchecks on `wg0` |
| `MYSTGATE_MAX_FAILURES` | `3` | Consecutive failed healthchecks before automatic rotation |
| `MYSTGATE_ROTATE_EVERY` | *(empty)* | Optional periodic rotation interval in seconds (empty = rotate only on health failure) |
| `MYSTGATE_HTTP_PORT` | `8080` | HTTP proxy port inside the container (`0` disables) |
| `MYSTGATE_SOCKS_PORT` | `1080` | SOCKS5 proxy port inside the container (`0` disables) |
| `MYSTGATE_PROXY_USER` | *(empty)* | Optional proxy username |
| `MYSTGATE_PROXY_PASS` | *(empty)* | Optional proxy password |

Example overriding country and IP type on the command line:

```bash
MYSTGATE_COUNTRY=JP MYSTGATE_IP_TYPE=residential docker compose -f docker/compose.yaml up -d
```

## 3. Routing Other Containers Through the VPN (`network_mode`)

Any Docker service can share `mystgate`'s network namespace so all of its traffic goes through `wg0` and is protected by the `iptables` killswitch:

```yaml
services:
  mystgate:
    extends:
      file: docker/compose.yaml
      service: mystgate

  my-app:
    image: curlimages/curl:latest
    network_mode: "service:mystgate"
    depends_on:
      mystgate:
        condition: service_healthy
    command: ["sh", "-c", "curl -s https://api.ipify.org && sleep 3600"]
```

## 4. Killswitch, Healthchecks, and Auth Refresh

- **VPN killswitch**: `iptables` sets `OUTPUT` policy to `DROP` and only allows `lo`, `wg0`, established connections, local Docker subnets (so clients can reach ports `1080`/`8080`), and the active WireGuard peer UDP endpoint. Outbound DNS/HTTPS on the default interface is opened only during `mystgate connect` and immediately locked down afterward.
- **Healthcheck**: both the gateway loop and Docker's `HEALTHCHECK` probe `https://1.1.1.1/cdn-cgi/trace` via `--interface wg0`.
- **Fail-closed on rotation failure**: if `mystgate connect`, `wg-quick up`, or the post-connect `1.1.1.1` healthcheck fails, `wg0` is brought down and `pproxy` is stopped immediately so no unencrypted traffic can pass.
- **Auto-resume on auth refresh**: if Mysterium tokens expire (`exit_code=4`), the container cuts the tunnel and stays running while watching `/data/state/tokens.json`. Re-authenticate in place without restarting the container:

```bash
docker compose -f docker/compose.yaml exec mystgate mystgate auth
```

As soon as browser approval completes, the gateway detects the updated `tokens.json` within 2 seconds and brings the VPN and proxies back up automatically.

## 5. Useful Operations

```bash
# List available countries using the container's saved session
docker compose -f docker/compose.yaml exec mystgate mystgate countries --type residential

# Check container status and saved session
docker compose -f docker/compose.yaml exec mystgate mystgate status

# Disconnect the active server-side Mysterium session
docker compose -f docker/compose.yaml exec mystgate mystgate disconnect

# Stop container and remove it (keeps saved tokens and keypair in volumes)
docker compose -f docker/compose.yaml down
```

## 6. Logs

- Gateway lifecycle events (`connect`, healthcheck failures, rotation, auth wait) are written to `stderr` (`docker compose -f docker/compose.yaml logs -f`).
- Structured CLI JSON logs are written to `/data/logs/mystgate.log` inside the `mystgate_logs` volume (`10 MiB` x `5` backups, secrets redacted).
