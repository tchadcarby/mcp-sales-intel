# mcp-sales-intel

**A production-shaped MCP server that turns any marketplace into competitive intelligence.**

Scout live Fiverr gigs, analyse pricing bands and competition, and get a
data-anchored package-price ladder — all through natural language from Claude,
Cursor, or any MCP client.

This is the reference implementation I use to demonstrate MCP server work:
real external data, bounded inputs, structured errors, caching, and both stdio
and streamable-HTTP transports. Zero secrets required.

---

## Why this exists

Most Fiverr MCP gigs ship a demo server that returns hardcoded JSON. This one
actually scrapes, actually parses, actually computes. It's the difference
between "here's a server" and "here's a server that works on Monday."

## Tools

| Tool | What it does |
|------|--------------|
| `list_gigs` | Scrape live Fiverr search results → title, seller, rating, reviews, entry price, URL. Filter by price/rating. |
| `analyse_market` | Pricing bands, review distribution, and an explicit "open market" verdict from raw page markdown. |
| `price_gig` | A Basic/Standard/Premium ladder anchored to observed medians — not vibes. |

## Quick start

```bash
# stdio (works with Claude Desktop, Cursor, Hermes, mcporter)
uv run mcp-sales-intel

# streamable HTTP (for shared/remote deployments)
MCP_TRANSPORT=streamable-http uv run mcp-sales-intel
```

### Wire it into an MCP client

`claude_desktop_config.json` / Cursor `mcp.json`:

```json
{
  "mcpServers": {
    "sales-intel": {
      "command": "uv",
      "args": ["run", "--directory", "/abs/path/to/mcp-sales-intel", "mcp-sales-intel"]
    }
  }
}
```

## Requirements

- Python 3.12+
- `mcp` Python SDK **2.x** (note: `FastMCP` was renamed `MCPServer` in 2.0)
- `firecrawl` CLI on `PATH` — only for live scraping. The other two tools
  work without it.

## Example

> "Analyse the mcp server development market and price my gig."

The agent calls `list_gigs`, feeds the result to `analyse_market`, then
`price_gig`, and returns a real ladder with the reasoning attached.

## Design notes

- **Bounded inputs.** Query length and `max_results` are clamped; bad ranges
  return a structured error instead of raising.
- **30-minute cache** per query, LRU-evicted, so repeated agent calls don't
  re-scrape and burn credits.
- **Honest failures.** Missing CLI, timeouts, non-zero exits, and layout drift
  all return `{"error": ..., "gigs": []}` rather than fabricating results.

## License

MIT
