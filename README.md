# AStockEvent — MCP server for Chinese A-share regulatory filings

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io/)

**Current state folded from A-share filings — not a raw event dump.**

An event feed tells you a plan was announced in June and amended in August. You still
have to work out what is true today. This server does that fold for you: who is still
selling down, which penalty cases are open, which inquiry letters are unanswered.

Every value links back to the source PDF published by the exchange, so you can check us.

---

## Connect

This is a **remote MCP server** (Streamable HTTP). There is nothing to install —
point your MCP client at the URL:

```
https://astockevent.com/mcp/
```

No API key, no sign-up. Rate limits apply and the response tells you when you hit one.

<details>
<summary>Claude Desktop / any client that takes a remote URL</summary>

```json
{
  "mcpServers": {
    "astockevent": {
      "url": "https://astockevent.com/mcp/"
    }
  }
}
```
</details>

Prefer HTTP? The same data is available over REST — see
**[astockevent.com/docs](https://astockevent.com/docs)**, with the machine-readable
contract at [`/openapi.json`](https://astockevent.com/openapi.json).

---

## Tools

| Tool | What it answers |
|---|---|
| `list_coverage` | What is in scope and what the limits are. Call this before concluding data is missing. |
| `get_entity_state` | Folded state for a company, or for a shareholder across every company they touch. |
| `get_event_with_context` | One event plus its whole timeline, in a single call. |
| `whats_new` | What changed recently, cursor-paged. |
| `scan_recent_events` | Cross-company scan by filing type and date range. |

## Coverage

**Three filing types today**, stated plainly — more are being added. We would rather
tell you the boundary than let you discover it by trial and error.

| Type | Folded into |
|---|---|
| Share reduction by major shareholders | The plan that is still live, and how much of its cap is used up |
| Administrative penalty proceedings | Each case grouped by case number, folded to its current stage |
| Exchange inquiry letters | Received / replied / overdue — the state of the conversation |

Call `list_coverage` for the authoritative, always-current answer.

---

## Two things worth knowing

**Empty is not the same as unknown.** A company with no filings of a type comes back
as *covered, nothing found* — not as an empty result. A security we do not carry comes
back as *not found*, with a reason. Telling those two apart is the point of this service.

**We report, we do not judge.** Objective extractions only: no ratings, no scores, no
attribution of price moves. What you build on top of the facts is yours.

---

## Status

Pre-release. Coverage is narrow and stated honestly; the API may change.
If you are using it and something is missing or wrong, we want to hear it —
[tell us here](https://astockevent.com/feedback) or email `contact@astockevent.com`.

## About this repository

This repo is the **public front door**: what the server is, how to connect, and the
[`server.json`](./server.json) descriptor for the MCP registry.

The server itself is *remote* — you point a client at a URL rather than installing code —
so there is no server implementation to publish here. Extraction engines, crawlers and
schemas live in a private repository.

## License

MIT — see [LICENSE](./LICENSE).
