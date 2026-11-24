#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="${MYSTGATE_STATE_DIRECTORY:-/data/state}"
WG_CONF="/etc/wireguard/wg0.conf"
TOKENS_FILE="${STATE_DIR}/tokens.json"

COUNTRY="${MYSTGATE_COUNTRY:-FR}"
CITY="${MYSTGATE_CITY:-}"
IP_TYPE="${MYSTGATE_IP_TYPE:-residential}"
HEALTH_INTERVAL="${MYSTGATE_HEALTH_INTERVAL:-30}"
MAX_FAILURES="${MYSTGATE_MAX_FAILURES:-3}"
ROTATE_EVERY="${MYSTGATE_ROTATE_EVERY:-}"
HTTP_PORT="${MYSTGATE_HTTP_PORT:-8080}"
SOCKS_PORT="${MYSTGATE_SOCKS_PORT:-1080}"
PROXY_USER="${MYSTGATE_PROXY_USER:-}"
PROXY_PASS="${MYSTGATE_PROXY_PASS:-}"

PPROXY_PID=""
DEFAULT_IFACE="$(ip route show default | awk '/default/ {print $5; exit}')"
LOCAL_NETS="$(ip -o -f inet addr show dev "$DEFAULT_IFACE" | awk '{print $4}')"

log() {
    printf '%s [I] gateway   : %s\n' "$(date -u +%H:%M:%S)" "$*" >&2
}

tokens_fp() {
    if [ -f "$TOKENS_FILE" ]; then
        stat -c '%Y:%s' "$TOKENS_FILE"
    else
        echo "missing"
    fi
}

stop_proxy() {
    if [ -n "$PPROXY_PID" ] && kill -0 "$PPROXY_PID" 2>/dev/null; then
        kill "$PPROXY_PID" 2>/dev/null || true
        wait "$PPROXY_PID" 2>/dev/null || true
    fi
    PPROXY_PID=""
}

start_proxy() {
    stop_proxy
    local auth_suffix=""
    if [ -n "$PROXY_USER" ] && [ -n "$PROXY_PASS" ]; then
        auth_suffix="#${PROXY_USER}:${PROXY_PASS}"
    fi
    local args=()
    if [ "$HTTP_PORT" -gt 0 ]; then
        args+=("-l" "http://0.0.0.0:${HTTP_PORT}${auth_suffix}")
    fi
    if [ "$SOCKS_PORT" -gt 0 ]; then
        args+=("-l" "socks5://0.0.0.0:${SOCKS_PORT}${auth_suffix}")
    fi
    if [ "${#args[@]}" -eq 0 ]; then
        return
    fi
    pproxy "${args[@]}" >/dev/null 2>&1 &
    PPROXY_PID=$!
}

apply_killswitch_base() {
    iptables -F OUTPUT
    iptables -P OUTPUT DROP
    iptables -A OUTPUT -o lo -j ACCEPT
    iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -o wg0 -j ACCEPT
    for net in $LOCAL_NETS; do
        iptables -A OUTPUT -d "$net" -j ACCEPT
    done
}

allow_api_temporarily() {
    iptables -I OUTPUT 1 -o "$DEFAULT_IFACE" -p udp --dport 53 -j ACCEPT
    iptables -I OUTPUT 1 -o "$DEFAULT_IFACE" -p tcp --dport 53 -j ACCEPT
    iptables -I OUTPUT 1 -o "$DEFAULT_IFACE" -p tcp --dport 443 -j ACCEPT
}

lock_to_endpoint() {
    local endpoint_host=$1
    local endpoint_port=$2
    apply_killswitch_base
    iptables -A OUTPUT -o "$DEFAULT_IFACE" -d "$endpoint_host" -p udp --dport "$endpoint_port" -j ACCEPT
}

cut_tunnel() {
    stop_proxy
    wg-quick down wg0 >/dev/null 2>&1 || true
    apply_killswitch_base
}

cleanup() {
    log "Shutting down gateway..."
    cut_tunnel
    exit 0
}
trap cleanup INT TERM

check_health() {
    curl -fsS --interface wg0 --max-time 10 "https://1.1.1.1/cdn-cgi/trace" >/dev/null 2>&1
}

check_real_ip() {
    curl -fsS --interface wg0 --max-time 10 "https://api.ipify.org" 2>/dev/null || echo "-"
}

connect_and_start() {
    while true; do
        local before_fp
        before_fp="$(tokens_fp)"

        cut_tunnel
        allow_api_temporarily

        local cmd=(mystgate connect --country "$COUNTRY" --type "$IP_TYPE" -o "$WG_CONF" --force)
        if [ -n "$CITY" ]; then
            cmd+=(--city "$CITY")
        fi

        local exit_code=0
        "${cmd[@]}" >/dev/null || exit_code=$?
        apply_killswitch_base

        if [ "$exit_code" -eq 4 ]; then
            log "Tunnel cut (auth required). Run 'docker compose exec mystgate mystgate auth'; waiting..."
            while [ "$(tokens_fp)" = "$before_fp" ]; do
                sleep 2
            done
            log "Detected refreshed auth tokens, reconnecting..."
            continue
        fi

        if [ "$exit_code" -ne 0 ]; then
            log "Tunnel cut (connect failed exit=${exit_code}). Retrying in ${HEALTH_INTERVAL}s..."
            local waited=0
            while [ "$waited" -lt "$HEALTH_INTERVAL" ]; do
                sleep 2
                waited=$((waited + 2))
                if [ "$(tokens_fp)" != "$before_fp" ]; then
                    log "Detected refreshed auth tokens, retrying immediately..."
                    break
                fi
            done
            continue
        fi

        chmod 600 "$WG_CONF"
        local endpoint endpoint_host endpoint_port
        endpoint="$(awk -F '=' '/^[[:space:]]*Endpoint[[:space:]]*=/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$WG_CONF")"
        endpoint_host="${endpoint%:*}"
        endpoint_port="${endpoint##*:}"

        if ! wg-quick up wg0 >/dev/null 2>&1; then
            log "Tunnel cut (wg-quick up failed). Retrying in ${HEALTH_INTERVAL}s..."
            cut_tunnel
            sleep "$HEALTH_INTERVAL"
            continue
        fi

        lock_to_endpoint "$endpoint_host" "$endpoint_port"
        sleep 1

        if ! check_health; then
            log "Tunnel cut (1.1.1.1 healthcheck failed after connect). Retrying in ${HEALTH_INTERVAL}s..."
            cut_tunnel
            sleep "$HEALTH_INTERVAL"
            continue
        fi

        start_proxy
        local real_ip
        real_ip="$(check_real_ip)"
        printf '%s | %s | %s\n' "$COUNTRY" "$IP_TYPE" "$real_ip"
        return 0
    done
}

connect_and_start
LAST_ROTATION="$(date +%s)"
FAILURES=0

while true; do
    sleep "$HEALTH_INTERVAL"
    if check_health; then
        FAILURES=0
    else
        FAILURES=$((FAILURES + 1))
        log "Health failed (${FAILURES}/${MAX_FAILURES})"
    fi

    ROTATE_DUE=0
    if [ -n "$ROTATE_EVERY" ]; then
        NOW="$(date +%s)"
        if [ $((NOW - LAST_ROTATION)) -ge "$ROTATE_EVERY" ]; then
            ROTATE_DUE=1
        fi
    fi

    if [ "$FAILURES" -ge "$MAX_FAILURES" ] || [ "$ROTATE_DUE" -eq 1 ]; then
        log "Rotating VPN tunnel..."
        connect_and_start
        LAST_ROTATION="$(date +%s)"
        FAILURES=0
    fi
done
