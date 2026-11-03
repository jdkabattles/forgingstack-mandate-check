# ForgingStack Mandate Check — skill for agents

Use this tool when an agent is about to act for a principal and the
caller wants proof the action was inside the mandate.

## When to use it

- Before a consequential action: reading, writing, sending, spending,
  or deleting on someone else's behalf.
- When the mandate is explicit: a named agent, a named principal, a
  list of allowed actions, and an expiry.

## When NOT to use it

- To decide if an action is wise, legal, or safe. This tool checks
  mandate fit only.
- When there is no mandate. Do not invent one to pass the check.

## How to call it (MCP)

Tool: `check_mandate`
Arguments: `agent_id`, `principal`, `action`, `mandate` with
`agent_id`, `principal`, `allowed_actions`, `expires_at`
(optional: `scope`, `idempotency_key`).

## How to read the result

- `decision: "pass"` → act, and keep the receipt id.
- `decision: "fail"` → do not act. The `reason` is the whole
  explanation: `mandate_agent_mismatch`,
  `mandate_principal_mismatch`, `mandate_expired`, or
  `action_not_in_mandate`.
- A failed decision still costs 1 credit. An idempotency-key replay
  is free and returns the original receipt.

## Status

Live, v0.2.0. API: https://forgingstack-mandate-check.jkbattles.workers.dev
Signup: POST /v1/signup with an email returns an API key once and
100 starter credits. Humans create agent sub-keys with POST /v1/keys.
Email verification is pending, and credit-pack billing is not live yet.
