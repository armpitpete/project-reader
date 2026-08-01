#!/usr/bin/env bash
set -euo pipefail

PUBLIC_DIR=${1:?public artifact directory required}
OUTPUT_DIR=${2:?output directory required}
PORT=${PROJECT_READER_PROOF_PORT:-8765}

mkdir -p "$OUTPUT_DIR"

browser=""
for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
  if command -v "$candidate" >/dev/null 2>&1; then
    browser=$(command -v "$candidate")
    break
  fi
done
if [[ -z "$browser" ]]; then
  echo "No Chromium-compatible browser found" >&2
  exit 2
fi

python -m http.server "$PORT" --bind 127.0.0.1 --directory "$PUBLIC_DIR" >"$OUTPUT_DIR/server.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
sleep 2

capture() {
  local slug=$1
  local repository=$2
  local width=$3
  local height=$4
  local url="http://127.0.0.1:${PORT}/?repo=${repository}&autorun=1"
  "$browser" \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    --hide-scrollbars \
    --window-size="${width},${height}" \
    --virtual-time-budget=15000 \
    --screenshot="$OUTPUT_DIR/${slug}.png" \
    "$url" >/dev/null 2>&1
  "$browser" \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    --virtual-time-budget=15000 \
    --dump-dom \
    "$url" >"$OUTPUT_DIR/${slug}.html" 2>/dev/null
  test -s "$OUTPUT_DIR/${slug}.png"
  test -s "$OUTPUT_DIR/${slug}.html"
}

capture synth-desktop AudioKit/AudioKitSynthOne 1440 1800
capture synth-mobile AudioKit/AudioKitSynthOne 390 1600
capture course-desktop microsoft/AI-For-Beginners 1440 1800
capture course-mobile microsoft/AI-For-Beginners 390 1600

grep -F "playable open-source synthesizer app" "$OUTPUT_DIR/synth-desktop.html"
grep -F "musicians" "$OUTPUT_DIR/synth-desktop.html"
grep -F "Get or open the app" "$OUTPUT_DIR/synth-desktop.html"
grep -F "beginner curriculum for learning artificial intelligence" "$OUTPUT_DIR/course-desktop.html"
grep -F "24 lessons" "$OUTPUT_DIR/course-desktop.html"
grep -F "Start with the course setup" "$OUTPUT_DIR/course-desktop.html"

printf 'browser-proof=pass\n'
