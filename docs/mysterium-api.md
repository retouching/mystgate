# Mysterium VPN API Guide

This document describes the Mysterium VPN HTTP API contract used by `mystgate` (the same API used by Mysterium's official Linux CLI).

## Base URL and Required Headers

- **API base URL**: `https://api.mysteriumvpn.com/api/v1`
- **OAuth authorize URL**: `https://app.mysteriumvpn.com/oauth/authorize`
- **Client ID**: `cli`
- **User-Agent**: `Go-http-client/1.1`

> Cloudflare in front of `api.mysteriumvpn.com` blocks default Python user agents (error `1010`). Every request must send `User-Agent: Go-http-client/1.1`.

Authenticated endpoints require:

```http
Authorization: Bearer <access_token>
Accept: application/json
User-Agent: Go-http-client/1.1
```

## 1. Authentication (Browser Activation OAuth)

Mysterium CLI authentication uses a 3-step browser approval flow.

### Step 1: Start Activation

`POST /auth/activation`

```bash
ACTIVATION_ID=$(python3 -c "import uuid; print(uuid.uuid4())")

curl -sS -X POST "https://api.mysteriumvpn.com/api/v1/auth/activation" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Content-Type: application/json" \
  -d "{\"id\": \"${ACTIVATION_ID}\"}"
```

### Step 2: Approve in Browser

Open the following URL in any browser and approve the login request (valid for 5 minutes):

```text
https://app.mysteriumvpn.com/oauth/authorize?response_type=activation_none&client_id=cli&request_id=<ACTIVATION_ID>
```

### Step 3: Poll Activation Status

`GET /auth/activation/{activation_id}`

```bash
curl -sS "https://api.mysteriumvpn.com/api/v1/auth/activation/${ACTIVATION_ID}" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Accept: application/json"
```

Response while waiting:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "valid": true,
  "token": null
}
```

Response once approved:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "valid": true,
  "token": {
    "access_token": "<jwt-access-token>",
    "refresh_token": "<refresh-token>"
  }
}
```

If `valid` is `false`, the activation expired or was rejected.

### Refreshing Expired Tokens

When any authenticated endpoint returns `HTTP 401`, exchange the refresh token:

`POST /oauth/token`

```bash
curl -sS -X POST "https://api.mysteriumvpn.com/api/v1/oauth/token" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "refresh_token",
    "client_id": "cli",
    "refresh_token": "<refresh_token>"
  }'
```

Response:

```json
{
  "access_token": "<new-access-token>",
  "refresh_token": "<new-refresh-token>"
}
```

Always persist both tokens because refresh tokens may rotate.

## 2. Discovering Countries and Cities

Supported `ip_type` values:
- `residential`: residential exit nodes
- `hosting`: datacenter/hosting exit nodes

### Country Codes Summary

`GET /connection/config?ip_type=residential|hosting`

```bash
curl -sS "https://api.mysteriumvpn.com/api/v1/connection/config?ip_type=residential" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Response:

```json
{
  "countries": ["AD", "AE", "AL", "...", "ZA"],
  "top_countries": ["GB", "US"]
}
```

### Detailed Locations (Countries, Cities, Translations, Availability)

`GET /connection/config/locations?ip_type=residential|hosting`

```bash
curl -sS "https://api.mysteriumvpn.com/api/v1/connection/config/locations?ip_type=residential" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Response (list of countries):

```json
[
  {
    "country": "AE",
    "total": 25,
    "is_available": true,
    "translations": {
      "en": "United Arab Emirates",
      "fr": "Émirats Arabes Unis"
    },
    "supported_plans": ["plan_monthly", "plan_yearly"],
    "cities": [
      {
        "city": "dubai",
        "total": 14,
        "is_available": true,
        "latitude": 25.25847,
        "longitude": 55.30472,
        "translations": {
          "en": "Dubai City",
          "fr": "Dubaï"
        },
        "supported_plans": ["plan_monthly", "plan_yearly"]
      }
    ]
  }
]
```

Use the `country` ISO-2 code (uppercase) and the `cities[].city` slug when calling `/connection/connect`.

## 3. Creating or Rotating a WireGuard Session

`POST /connection/connect`

Before calling this endpoint, generate an X25519 WireGuard keypair locally and send only the base64 `public_key`. Your `private_key` never leaves your machine.

```bash
curl -sS -X POST "https://api.mysteriumvpn.com/api/v1/connection/connect" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key": "<base64-wireguard-public-key>",
    "country": "FR",
    "city": "paris",
    "ip_type": "residential",
    "os_type": "linux-cli",
    "cli_version": "0.3.2",
    "os_version": "Linux",
    "reset_connection": true
  }'
```

Fields:
- `public_key`: base64 X25519 public key identifying the device slot.
- `country`: 2-letter uppercase ISO country code.
- `city`: optional city slug from `/connection/config/locations`.
- `ip_type`: `residential` or `hosting`.
- `reset_connection`: set to `true` to replace any existing session for this `public_key` (lets you switch countries or rotate exit IP without consuming a new device slot).

Response:

```json
{
  "id": "session-uuid",
  "exit_ip": "198.51.100.42",
  "ip_type": "residential",
  "country": "FR",
  "city": "paris",
  "limit_exceeded": false,
  "wg_config": "[Interface]\nPrivateKey = %private_key%\nAddress = 10.182.0.2/32\nDNS = 1.1.1.1\n\n[Peer]\nPublicKey = ...\nAllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = 198.51.100.42:51820\n"
}
```

Post-processing:
1. Check `limit_exceeded`: if `true`, all account device slots are occupied; remove a device at `https://app.mysteriumvpn.com/dashboard/devices`.
2. Replace the `%private_key%` placeholder in `wg_config` with your local WireGuard private key and save the file with `0600` permissions.

## 4. Disconnecting a Session

`GET /connection/disconnect?public_key=<base64-public-key>`

```bash
curl -sS -G "https://api.mysteriumvpn.com/api/v1/connection/disconnect" \
  --data-urlencode "public_key=${WG_PUBLIC_KEY}" \
  -H "User-Agent: Go-http-client/1.1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

Releases the active server-side WireGuard session bound to `public_key`.
