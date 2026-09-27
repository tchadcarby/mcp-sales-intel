"""
mcp-sales-intel — a production-shaped MCP server.

Demonstrates the exact capability set that sells on Fiverr:
  - real external data (live Fiverr marketplace scan)
  - structured, typed tool outputs
  - error handling + bounded inputs
  - both stdio and streamable-http transports
  - zero-secret design (no API keys required)

Built for MCP Python SDK 2.x (MCPServer, formerly FastMCP).
"""

from __future__ import annotations

import json
import os
import re
import statistics
import time
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

SCRAPE_CMD = "firecrawl"
CACHE_TTL_SECONDS = 60 * 30
MAX_QUERY_LEN = 120

# ---------------------------------------------------------------- infra

_cache: dict[str, tuple[float, Any]] = {}
_cache_lock_hit_log: list[str] = []


def _cache_get(key: str) -> Any | None:
    hit = _cache.get(key)
    if hit and (time.time() - hit[0]) < CACHE_TTL_SECONDS:
        return hit[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)
    # keep cache bounded
    if len(_cache) > 64:
        for k in sorted(_cache, key=lambda k: _cache[k][0])[:16]:
            _cache.pop(k, None)


def _require_cmd() -> str | None:
    from shutil import which

    return which(SCRAPE_CMD)


def _parse_gigs(markdown: str) -> list[dict[str, Any]]:
    """Pull (title, seller, rating, reviews, price) out of Fiverr search cards."""
    pattern = re.compile(
        r"\[I will ([^\]]{10,200})\]\(https://www\.fiverr\.com/([a-z0-9_\-]+)/"
        r"([a-z0-9\-]{15,})[^)]*\)[^\[]*\*\*([\d.]+)\*\*\((\d+)\)[^$]*?From\$(\d+)"
    )
    out, seen = [], set()
    for title, seller, slug, rating, reviews, price in pattern.findall(markdown):
        if slug in seen:
            continue
        seen.add(slug)
        out.append(
            {
                "title": title.strip(),
                "seller": seller,
                "slug": slug,
                "url": f"https://www.fiverr.com/{seller}/{slug}",
                "rating": float(rating),
                "reviews": int(reviews),
                "entry_price_usd": int(price),
            }
        )
    return out


# ---------------------------------------------------------------- server

mcp = MCPServer(
    name="sales-intel",
    instructions=(
        "Live marketplace intelligence. Use list_gigs to scout a category, then "
        "analyse_market to get pricing bands and competition metrics for it."
    ),
)


@mcp.tool(
    name="list_gigs",
    title="List gigs in a category",
    description=(
        "Scrape live Fiverr search results for a query and return gig cards with "
        "title, seller, rating, review count, entry price and URL. "
        "Use this to scout what sellers are actually offering and charging."
    ),
)
def list_gigs(
    query: str,
    max_results: int = 20,
    min_price: int | None = None,
    max_price: int | None = None,
    min_rating: float | None = None,
) -> dict[str, Any]:
    """Scout live Fiverr gigs for a query.

    Args:
        query: Search terms, e.g. "mcp server development".
        max_results: Cap on returned gigs (1-60).
        min_price: Optional minimum entry price in USD.
        max_price: Optional maximum entry price in USD.
        min_rating: Optional minimum seller rating, e.g. 4.5.
    """
    if not isinstance(query, str) or not query.strip():
        return {"error": "query must be a non-empty string", "gigs": []}
    query = query.strip()
    if len(query) > MAX_QUERY_LEN:
        return {"error": f"query too long (max {MAX_QUERY_LEN} chars)", "gigs": []}

    max_results = max(1, min(int(max_results or 20), 60))
    if (min_price is not None and max_price is not None) and min_price > max_price:
        return {"error": "min_price cannot exceed max_price", "gigs": []}

    if _require_cmd() is None:
        return {
            "error": (
                f"'{SCRAPE_CMD}' CLI not found on PATH. This server shells out to it "
                "for live scraping. Install firecrawl-cli or pass a pre-scraped "
                "markdown file to analyse_market."
            ),
            "gigs": [],
        }

    slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")
    cache_key = f"gigs::{slug}"
    gigs = _cache_get(cache_key)
    from_cache = gigs is not None
    if gigs is None:
        import subprocess

        url = f"https://www.fiverr.com/search/gigs?query={query.replace(' ', '%20')}"
        try:
            proc = subprocess.run(
                [SCRAPE_CMD, "scrape", url, "--format", "markdown"],
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            return {"error": "scrape timed out after 180s", "gigs": []}
        except Exception as exc:  # noqa: BLE001
            return {"error": f"scrape failed: {type(exc).__name__}: {exc}", "gigs": []}

        if proc.returncode != 0:
            return {
                "error": f"scrape exited {proc.returncode}: {proc.stderr.strip()[:300]}",
                "gigs": [],
            }
        gigs = _parse_gigs(proc.stdout)
        if not gigs:
            return {
                "error": "no gigs parsed — page layout may have changed or query returned nothing",
                "gigs": [],
            }
        _cache_set(cache_key, gigs)

    # post-filter (cache holds the unfiltered set)
    out = list(gigs)
    if min_price is not None:
        out = [g for g in out if g["entry_price_usd"] >= min_price]
    if max_price is not None:
        out = [g for g in out if g["entry_price_usd"] <= max_price]
    if min_rating is not None:
        out = [g for g in out if g["rating"] >= min_rating]
    out = out[:max_results]

    prices = [g["entry_price_usd"] for g in out] or [0]
    return {
        "query": query,
        "count": len(out),
        "from_cache": from_cache,
        "price_summary_usd": {
            "min": min(prices),
            "median": int(statistics.median(prices)),
            "max": max(prices),
        },
        "gigs": out,
    }


@mcp.tool(
    name="analyse_market",
    title="Analyse a market from scraped markdown",
    description=(
        "Take raw Fiverr search-page markdown (as a string) and compute pricing "
        "bands, review-count distribution and an 'open market' verdict — i.e. how "
        "reachable a new seller is. Use for competitive analysis without re-scraping."
    ),
)
def analyse_market(
    markdown: str,
    open_market_review_threshold: int = 15,
) -> dict[str, Any]:
    """Compute market metrics from already-scraped markdown.

    Args:
        markdown: Raw markdown from a Fiverr gig search results page.
        open_market_review_threshold: Gigs at or below this many reviews count as
            reachable for a new seller.
    """
    if not isinstance(markdown, str) or len(markdown.strip()) < 200:
        return {"error": "markdown too short to analyse (need >200 chars)", "verdict": None}

    gigs = _parse_gigs(markdown)
    if not gigs:
        return {"error": "no gigs parsed from markdown", "verdict": None}

    prices = sorted(g["entry_price_usd"] for g in gigs)
    reviews = sorted(g["reviews"] for g in gigs)

    def pct(xs: list[int], p: float) -> int:
        return xs[min(len(xs) - 1, int(len(xs) * p))]

    open_gigs = [g for g in gigs if g["reviews"] <= open_market_review_threshold]
    well_paid_open = [
        g for g in open_gigs if g["entry_price_usd"] >= 50
    ]

    if not open_gigs:
        verdict = "closed — incumbents hold deep review moats"
    elif len(well_paid_open) / len(gigs) >= 0.15:
        verdict = "open — thin competition at >=$50 entry price"
    else:
        verdict = "contested — open gigs skew cheap"

    return {
        "gig_count": len(gigs),
        "entry_price_usd": {
            "min": prices[0],
            "p25": pct(prices, 0.25),
            "median": int(statistics.median(prices)),
            "p75": pct(prices, 0.75),
            "max": prices[-1],
        },
        "reviews": {
            "min": reviews[0],
            "median": int(statistics.median(reviews)),
            "p75": pct(reviews, 0.75),
            "max": reviews[-1],
        },
        "open_market": {
            "threshold": open_market_review_threshold,
            "open_gigs": len(open_gigs),
            "open_share": round(len(open_gigs) / len(gigs), 3),
            "open_and_well_paid": len(well_paid_open),
        },
        "verdict": verdict,
        "top_open_opportunities": sorted(
            open_gigs, key=lambda g: -g["entry_price_usd"]
        )[:5],
    }


@mcp.tool(
    name="price_gig",
    title="Recommend a gig price ladder",
    description=(
        "Given a set of gigs (or a market query), recommend a three-tier Basic/"
        "Standard/Premium package ladder with prices anchored to observed medians."
    ),
)
def price_gig(
    gigs: list[dict[str, Any]] | None = None,
    query: str | None = None,
    floor_usd: int = 25,
) -> dict[str, Any]:
    """Recommend a package ladder anchored to observed market prices.

    Args:
        gigs: Optional list of {"entry_price_usd": int, "reviews": int} dicts.
        query: Optional query to scrape if no gigs supplied.
        floor_usd: Minimum price for the Basic tier.
    """
    pool: list[dict[str, Any]] = list(gigs or [])

    if not pool and query:
        scraped = list_gigs(query, max_results=40)
        if scraped.get("error"):
            return {"error": scraped["error"], "ladder": None}
        pool = scraped["gigs"]

    if not pool:
        return {"error": "provide gigs[] or query= to price against", "ladder": None}

    prices = sorted(int(g.get("entry_price_usd", 0)) for g in pool if g.get("entry_price_usd"))
    if not prices:
        return {"error": "no usable prices in input", "ladder": None}

    med = statistics.median(prices)
    p75 = prices[min(len(prices) - 1, int(len(prices) * 0.75))]

    open_prices = [
        g["entry_price_usd"]
        for g in pool
        if g.get("reviews", 999) <= 15 and g.get("entry_price_usd")
    ]
    open_med = statistics.median(open_prices) if open_prices else med

    basic = max(floor_usd, int(round(open_med)))
    std = max(basic * 2, int(round(med)))
    prem = max(int(round(std * 2.2)), int(round(p75 * 2)))

    return {
        "observed": {
            "n": len(prices),
            "median": int(med),
            "p75": int(p75),
            "open_market_median": int(open_med),
        },
        "ladder": {
            "basic": {"price_usd": basic,
                      "scope": "narrow but complete, 1 integration, fast delivery"},
            "standard": {"price_usd": std,
                         "scope": "most common ask, multiple tools/integrations"},
            "premium": {"price_usd": prem,
                        "scope": "full system, docs, deployment, revisions"},
        },
        "rationale": (
            f"Basic ${basic} anchored to open-market median (${int(open_med)}). "
            f"Standard ${std} = 2x Basic, floored at overall median (${int(med)}). "
            f"Premium ${prem} = 2.2x Standard, floored at 2x p75 (${int(p75)}). "
            f"Floors ensure each tier is at least the observed market rate for that "
            f"scope; the ladder ascends monotonically."
        ),
    }


def main() -> None:
    transport: Literal["stdio", "sse", "streamable-http"] = os.environ.get(
        "MCP_TRANSPORT", "stdio"
    )  # type: ignore[assignment]
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
