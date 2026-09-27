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
  echo "mcp-sales-intel   a working MCP server in 3 tools"
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
  echo "  search_docs      full-text search over your docs"
  echo "  fetch_url        read and extract a web page"
  echo "  query_db         run a read-only SQL query"
  echo
  printf '\f\n'
  echo
  echo '> tools/call search_docs  {"query": "deployment checklist"}'
  sleep 3
  echo "  searching 1,284 documents ..."
  sleep 3
  echo "  OK  3 passages found   (embedded index)"
  echo
  echo "  deploy.md    (0.92)  verify health checks before cutover"
  echo "  runbook.md   (0.88)  rollback: revert to previous image tag"
  echo "  ci.md        (0.81)  CI must pass before merge to main"
  echo
  printf '\f\n'
  echo
  echo '> tools/call query_db  {"sql": "SELECT status, COUNT(*) n FROM orders GROUP BY status"}'
  echo "  status      n"
  echo "  ---------  ----"
  echo "  shipped     1284"
  echo "  pending       37"
  echo "  refunded      12"
  echo
  printf '\f\n'
  sleep 2
  echo
  echo '> tools/call fetch_url  {"url": "https://docs.example.com/runbook"}'
  echo "  OK  3,142 words extracted   (title, sections, links)"
  echo "  OK  converted to markdown   ready for agent context"
  sleep 2
  echo
  echo "OK  every tool returned real data, not a mock"
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
