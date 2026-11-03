"""MCP wrapper client for ForgingStack Mandate Check, v0.2.0.

An agent-native service must be usable by agents, not just by humans
with curl. MCP is the standard interface agents already speak, so the
wrapper exposes the same live REST API as MCP tools, with no duplicated
decision logic: every tool call goes through the REST API, so metering
and receipts stay in one place. The service itself is private; this
file is only a client.

Protocol: JSON-RPC 2.0 over stdio, no new dependencies (stdlib only).
Supported methods: initialize, ping, tools/list, tools/call.
Notifications (no id, e.g. notifications/initialized) get no response.

Environment:
  FORGINGSTACK_API_BASE  default https://forgingstack-mandate-check.jkbattles.workers.dev
  FORGINGSTACK_API_KEY   required; sign up via POST /v1/signup (key shown once)

Run:  python -m app.mcp_server
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get(
    "FORGINGSTACK_API_BASE",
    "https://forgingstack-mandate-check.jkbattles.workers.dev",
)
API_KEY = os.environ.get("FORGINGSTACK_API_KEY", "")

TOOLS = [
    {
        "name": "check_mandate",
        "description": "Check an agent action against its mandate. Returns a "
        "pass/fail decision and a receipt. Costs 1 credit per call; "
        "an idempotency key replay is free.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "principal": {"type": "string"},
                "action": {"type": "string"},
                "mandate": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "principal": {"type": "string"},
                        "allowed_actions": {
                            "type": "array", "items": {"type": "string"}
                        },
                        "expires_at": {"type": "string"},
                        "scope": {"type": "string"},
                    },
                    "required": [
                        "agent_id", "principal", "allowed_actions", "expires_at"
                    ],
                },
                "idempotency_key": {"type": "string"},
            },
            "required": ["agent_id", "principal", "action", "mandate"],
        },
    },
    {
        "name": "get_credits",
        "description": "Remaining credit balance for the configured API key.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_receipt",
        "description": "Fetch a past mandate-check receipt by id.",
        "inputSchema": {
            "type": "object",
            "properties": {"receipt_id": {"type": "integer"}},
            "required": ["receipt_id"],
        },
    },
]


def _http(method, path, body=None, idempotency_key=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("X-API-Key", API_KEY)
    req.add_header("Content-Type", "application/json")
    # A User-Agent is required: the default Python urllib agent is
    # rejected (Cloudflare 1010) through some egress paths.
    req.add_header("User-Agent", "ForgingStack-Mandate-Check/0.2.0")
    if idempotency_key:
        req.add_header("Idempotency-Key", idempotency_key)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {"detail": "api error"}


def _text(payload, is_error=False):
    return {
        "content": [{"type": "text", "text": json.dumps(payload)}],
        "isError": is_error,
    }


def handle(msg):
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "forgingstack-mandate-check", "version": "0.2.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "check_mandate":
            body = {k: args[k] for k in
                    ("agent_id", "principal", "action", "mandate")}
            status, data = _http(
                "POST", "/v1/check-mandate", body,
                args.get("idempotency_key"),
            )
            return _text(data, is_error=status >= 400)
        if name == "get_credits":
            status, data = _http("GET", "/v1/credits")
            return _text(data, is_error=status >= 400)
        if name == "get_receipt":
            status, data = _http(
                "GET", f"/v1/receipts/{args['receipt_id']}"
            )
            return _text(data, is_error=status >= 400)
        raise ValueError(f"unknown tool: {name}")
    raise ValueError(f"unknown method: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Notifications carry no id and get no response.
        if "id" not in msg:
            continue
        try:
            result = handle(msg)
            out = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
        except Exception as exc:  # noqa: BLE001 - MCP error surface
            out = {
                "jsonrpc": "2.0", "id": msg["id"],
                "error": {"code": -32603, "message": str(exc)},
            }
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
