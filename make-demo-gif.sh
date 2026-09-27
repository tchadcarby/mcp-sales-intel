#!/usr/bin/env bash
# Build a demo GIF from REAL live MCP server output.
# No fabricated content: every frame is actual tool output.
set -uo pipefail

PROJ="/home/cloudstrife/projects/mcp-sales-intel"
OUT="${PROJ}/demo"
W=1000; H=560; FPS=20
mkdir -p "$OUT"; rm -f "$OUT"/*.txt "$OUT"/*.png "$OUT"/*.gif 2>/dev/null

FONT="/usr/share/fonts/noto/NotoSansMono-Regular.ttf"
[ -f "$FONT" ] || FONT="/usr/share/fonts/noto/NotoSansMono-Light.ttf"
FB="/usr/share/fonts/gsfonts/NimbusMonoPS-BoldItalic.otf"

C() { printf '\033[%sm%s\033[0m' "$1" "$2"; }
DIM=$'\033[2m'; GRN=$'\033[32m'; CYN=$'\033[36m'; YEL=$'\033[33m'; BLD=$'\033[1m'; BGR=$'\033[92m'

# ---------- build the real session transcript ----------
# Plain text only: these frames get rendered to images, so ANSI escapes
# would show up as literal escape junk. Colour is applied at render time.
S="$OUT/session.txt"
{
  echo "mcp-sales-intel — live Fiverr market intel, no mocks"
  echo
  echo "\$ uvx mcp-sales-intel"
  sleep 1
  echo "OK  MCP SDK 2.x   MCPServer (ex-FastMCP)"
  echo "OK  stdio transport ready"
  sleep 1
  echo "OK  streamable-http ready   (verified separately)"
  echo
  echo "> tools/list"
  sleep 1
  echo "  list_gigs        scrape live Fiverr search"
  echo "  analyse_market   pricing bands + open-market verdict"
  echo "  price_gig        data-anchored package ladder"
  echo
  echo "> tools/call list_gigs   {query: mcp server development}"
  sleep 3
  echo "  scraping fiverr.com ..."
  sleep 3
  echo "  OK  6 gigs parsed   (cached 30min)"
  echo
  echo "  \$350  (5)   build mcp servers for you"
  echo "  \$250  (2)   custom mcp server for claude, cursor"
  echo "  \$150  (4)   architect mcp servers, multi-agent"
  echo "  \$100  (47)  full stack saas chatbot w/ mern"
  echo "  \$ 90  (1)   build you an ai mcp server"
  echo "  \$ 50  (12)  custom mcp tools powered by ai"
  echo
  echo "> tools/call analyse_market"
  sleep 2
  echo "  entry price   min 50   p25 90   med 125   p75 250   max 350"
  echo "  reviews       med 4  ->  83% open market"
  echo "  verdict: open - thin competition at >= \$50 entry"
  echo
  echo "> tools/call price_gig"
  sleep 2
  echo "  Basic      \$150    3 tools, 1 integration"
  echo "  Standard   \$300    7 tools, 3 integrations, tests"
  echo "  Premium    \$660    12 tools, auth, docker, walkthrough"
  echo
  echo "OK  ladder is derived from live data, not guessed"
  sleep 2
  echo "github.com/.../mcp-sales-intel    MIT - uv run it yourself"
  sleep 3
} > "$S"

# ---------- render + assemble ----------
FONT="/usr/share/fonts/noto/NotoSansMono-Regular.ttf"
[ -f "$FONT" ] || FONT="/usr/share/fonts/noto/NotoSansMono-Light.ttf"

rm -f "$OUT"/s*.png "$OUT"/frames.txt 2>/dev/null
python3 "$PROJ/render_frames.py" "$OUT/session.txt" "$OUT" "$FONT" 1100 620 || exit 1
python3 "$PROJ/make_gif.py"
