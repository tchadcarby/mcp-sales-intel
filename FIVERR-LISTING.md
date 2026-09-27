# Fiverr Listing — MCP Server Development

Pricing anchored to live-scraped market data (Sept 27, 2026):
- N = 6 MCP gigs, entry-price median **$125**, p75 **$250**, max **$350**
- Median reviews **4** → 83% of the market is open
- Category incumbent `aiintegration`: $350 / $1,000 / $2,000, 5 reviews total

Package ladder derived by the server's own `price_gig` tool from that sample:
**Basic $150 · Standard $300 · Premium $660**

> Re-run `price_gig` before publishing — market moves. Do not hand-edit prices.

---

## GIG TITLE (80 char limit — all verified)

```
I will build an MCP server for Claude, Cursor or your AI agent
```
(62 chars)

## BACKUP TITLES (A/B test after 30 days — all ≤80 verified)

```
I will build a production ready MCP server for Claude or Cursor   (63)
I will build a custom MCP server in Python or TypeScript          (56)
I will migrate your MCP server from v1 FastMCP to v2 MCPServer    (62)
I will build an MCP server connecting your AI to real APIs and DB (65)
```

---

## PACKAGES

### 🥉 Basic — $150 · 3 days
- 1 MCP server, up to **3 tools**
- 1 data source or API integration
- Python (FastAPI) **or** TypeScript/Node
- **SDK 2.x** (`MCPServer`) — current API
- Error handling + input validation
- Source code + setup README
- 1 revision

### 🥈 Standard — $300 · 5 days
Everything in Basic, plus:
- Up to **7 tools**
- Up to **3 integrations** (APIs, Postgres/MySQL/Mongo, CRM, files)
- **stdio + streamable-HTTP** dual transport
- Tool schemas with clear descriptions for reliable LLM tool-calling
- Structured error responses
- Test suite proving each tool returns real data
- Client config for Claude Desktop / Cursor
- 2 revisions

### 🥇 Premium — $660 · 7 days
Everything in Standard, plus:
- Up to **12 tools**, 5+ integrations
- Auth (API key / OAuth) + **read-only or scoped write tools**
- Advanced patterns: pagination, retries, rate-limit backoff, caching
- Docker packaging + deploy config
- Full API documentation
- **Live walkthrough call** so your team can run it themselves
- 3 revisions

**Rush (24h): +40% on any tier.**

---

## GIG DESCRIPTION

```
Connect your AI agent to your REAL tools, APIs and databases — with a custom
MCP server your team actually owns.

I build production-ready Model Context Protocol servers in Python and TypeScript,
so Claude, Cursor, ChatGPT or your own agent can search your data, call your
APIs and execute real business actions.

⚠️ READ THIS FIRST — SDK 2.x
The MCP Python SDK changed. FastMCP was renamed to MCPServer in v2.0, and most
MCP servers and tutorials online still target v1 and no longer run. I build on
2.x and, if you already have a v1 server, I can migrate it.

WHAT I BUILD
✓ Custom MCP servers from scratch (Python / TypeScript / Node)
✓ REST + GraphQL API integrations
✓ PostgreSQL, MySQL, MongoDB, SQLite
✓ CRM and business system integrations
✓ File, document and knowledge tools
✓ Auth and scoped access
✓ Testing, error handling, documentation
✓ stdio and streamable-HTTP deployment

WHAT THIS UNLOCKS
Your AI agent can search and read business data, call external services, create
and update records, process documents, and automate repetitive workflows —
with guardrails, not just guesses.

WHY BUY THIS INSTEAD OF A GENERIC TEMPLATE
Most sellers send a demo that returns hardcoded JSON. I send a working server
plus a TEST SUITE proving each tool returns real data. You verify it works
before you pay a cent for the rest.

Every server ships with:
• Clean, documented source you own
• Client config for Claude Desktop / Cursor / any MCP client
• Honest error handling — failures say what actually went wrong
• A README your team can follow without me

Message me with your use case and I'll tell you straight whether this is the
right tool — or whether you don't need one.
```

---

## FAQ (paste into buyer questions)

**Q: What do I need to provide?**
A: Just your use case and the API/DB you want to connect. I'll tell you if you
need keys. I never ask for production secrets — use a test key or .env.

**Q: Which SDK version will I get?**
A: MCP Python SDK 2.x (`MCPServer`). Note v1 `FastMCP` code no longer runs on
2.x. Need to stay on v1 or migrate an existing server? Message me — I'll do
either.

**Q: How do I test it before final payment?**
A: On Standard and Premium I deliver the working server with a test suite first.
You run it against live data and confirm the tools work, then we close out.

**Q: Can you connect it to my database/API if it requires auth?**
A: Yes — I'll use env vars or scoped credentials, never hardcoded secrets.

**Q: Do I own the code?**
A: Completely. Full source in the delivery, yours to use and modify.

**Q: What if I need more tools later?**
A: Message me — I offer add-ons and maintenance. Most follow-ups are one tool
plus a test.

---

## REQURESMENTS (order form)

1. **What should the server do?** Describe the task, in plain language.
2. **Data source(s):** API endpoints, DB type + schema, files, or CRM.
3. **Preferred language:** Python / TypeScript / Node (I'll recommend if unsure).
4. **Client(s):** Claude Desktop, Cursor, ChatGPT, your own agent, or all.
5. **Auth needed?** If yes, what kind and how should permissions be scoped?
6. **Existing server to migrate?** (v1 → v2) Include the code or repo link.

---

## SEARCH TAGS
`mcp server`, `model context protocol`, `mcp`, `ai agent tools`, `claude mcp`,
`cursor mcp`, `ai agent development`, `mcp server python`, `mcp server typescript`

**Category:** Programming & Tech → AI Development → AI Websites & Software

---

## GIG IMAGE / DEMO — THE EDGE

Competitors in this category have no proof. Ship all three:

1. **Animated GIF (< 8s, loop):** terminal showing the server starting, a
   `list_tools` call returning the tools, and a real tool call returning live
   Fiverr data. This repo does exactly this — `uv run` and it works.
2. **"Built on SDK 2.x" badge** in the thumbnail. Instantly separates you from
   the v1 crowd.
3. **First image = the 2.x warning.** Most sellers' first image is stock
   art. Leading with the migration insight gets clicks from the exact people
   who are about to be broken by this.

---

## PROOF ASSET (free with Basic, drives the "verify before you pay" claim)
Public repo: `mcp-sales-intel` — a working server anyone can `uv run` and hit
live data with. Point to it in the description. No competitor is offering a
runnable artifact.

---

## PRICING NOTE
Ladder is data-derived. Re-run the server's `price_gig` against a fresh scrape
before any price change, and after ~20 completed orders — review the Basic-tier
conversion and adjust within the $100–$150 band if conversion is weak.
