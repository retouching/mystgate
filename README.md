<p align="center">
  <img alt="mystgate" src="docs/assets/logo.svg" width="160">
</p>

<h1 align="center">mystgate</h1>

<p align="center">
  Generate WireGuard configs from Mysterium VPN and run a WireGuard VPN + HTTP/SOCKS5 gateway with killswitch and auto-rotation.
</p>

<p align="center">
  <img alt="Python 3.14" src="https://img.shields.io/badge/python-3.14-blue.svg">
  <img alt="uv" src="https://img.shields.io/badge/managed%20with-uv-DE5FE9.svg">
  <img alt="Docker" src="https://img.shields.io/badge/docker-ready-2496ED.svg">
</p>

`mystgate` is a Python CLI for Mysterium VPN with the `mystgate` command. It signs in through browser approval (`auth`), lists countries filtered by residential or hosting IP type (`countries`), generates or rotates `0600` WireGuard `.conf` files without `wg` (`connect`), releases sessions (`disconnect`), reports local state (`status`), and ships a Docker gateway (`wg0`, `iptables` killswitch, HTTP/SOCKS5 proxy, `1.1.1.1` healthcheck, `api.ipify.org` exit-IP check, and automatic resume on auth refresh).

## Install

`mystgate` requires Python 3.14 and [uv](https://docs.astral.sh/uv/). Docker with Compose is optional and only needed for the VPN gateway container.

```bash
uv sync --no-dev
cp .env.example .env
uv run mystgate auth
```

Secret variables (`MYSTGATE_PROXY_PASS`) are left empty in `.env.example` and never logged.

## Example

```bash
uv run mystgate countries --type residential
uv run mystgate connect --country FR --type residential
docker compose -f docker/compose.yaml up -d
```

## Documentation

- [Usage](docs/usage.md): authentication, country discovery, WireGuard config generation, rotation, disconnect, options, exit codes, and logs.
- [Configuration](docs/configuration.md): `MYSTGATE_*` environment variables, `.env.example`, validation errors, and secret handling.
- [Docker gateway](docs/docker.md): WireGuard `wg0` container, `iptables` killswitch, HTTP/SOCKS5 proxy, `network_mode` sharing, and live auth refresh.
- [Mysterium VPN API](docs/mysterium-api.md): OAuth activation, token refresh, locations, connect/rotate, and disconnect endpoints.
