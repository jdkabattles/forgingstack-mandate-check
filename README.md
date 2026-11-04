# ForgingStack Mandate Check

Before your agent acts, check its mandate. One call, one receipt.

mcp-name: io.github.jdkabattles/forgingstack-mandate-check

This is the **public client** for Mandate Check. The service itself —
the decision logic, the receipt chain, the key store, and billing —
runs on ForgingStack's private service and is **not** in this repo.
Copying this repo does not give you the service: you still need an
API key and credits, from signup below.

Live API: https://forgingstack-mandate-check.jkbattles.workers.dev

## What it checks, in order

1. Mandate agent matches the calling agent
2. Mandate principal matches the principal the agent acts for
3. Mandate expiry is parseable and in the future
4. Action is in the mandate's allowed actions

Pass or fail, you get a reason and a hash-chained receipt.

What it does **not** do: decide if an action is wise, legal, or
safe. Mandate fit only.

## Signup (v1)

```bash
curl -X POST https://forgingstack-mandate-check.jkbattles.workers.dev/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'
```

Returns an API key **once** and 100 starter credits. Save the key
immediately — it is stored only as a hash and cannot be shown again.
Email verification is pending, and credit-pack billing is not live
yet, so do not expect a purchase flow in v1.

## Agent sub-keys

A signed-up human creates a key for each agent, capped and revocable:

```bash
curl -X POST https://forgingstack-mandate-check.jkbattles.workers.dev/v1/keys \
  -H "X-API-Key: YOUR_PRIMARY_KEY" -H "Content-Type: application/json" \
  -d '{"agent_name":"my-agent","credits":20}'
```

List with `GET /v1/keys`, revoke with `DELETE /v1/keys/{id}` —
revoking returns unused credits to the primary account.

## Use it (MCP, stdio)

Set the key, then run the MCP server in this repo:

```bash
export FORGINGSTACK_API_KEY="your-key-here"
python -m app.mcp_server
```

Tools: `check_mandate`, `get_credits`, `get_receipt`.
See `SKILL.md` for when to use it and when not to.

## Price

1 credit per check call. A failed decision still costs 1 credit —
the check was performed. An idempotent replay (same
`Idempotency-Key`) is free and returns the original receipt.

## Files in this repo

- `app/mcp_server.py` — MCP wrapper client (stdio, stdlib only)
- `SKILL.md` — when to use it, how to read pass/fail
- `agent-card.json` — A2A-style discovery card
- `server.json` — MCP Registry metadata (draft until PyPI publish)
- `pyproject.toml` — package metadata for the MCP client
