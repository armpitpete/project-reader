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
  local extra_query=${5:-}
  local network_mode=${6:-normal}
  local url="http://127.0.0.1:${PORT}/?repo=${repository}&autorun=1${extra_query}"
  local -a network_args=()
  if [[ "$network_mode" == "block-api" ]]; then
    network_args+=("--host-resolver-rules=MAP api.github.com 127.0.0.1")
  fi

  "$browser" \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    --hide-scrollbars \
    "${network_args[@]}" \
    --window-size="${width},${height}" \
    --virtual-time-budget=20000 \
    --screenshot="$OUTPUT_DIR/${slug}.png" \
    "$url" >/dev/null 2>&1
  "$browser" \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    "${network_args[@]}" \
    --virtual-time-budget=20000 \
    --dump-dom \
    "$url" >"$OUTPUT_DIR/${slug}.html" 2>/dev/null
  test -s "$OUTPUT_DIR/${slug}.png"
  test -s "$OUTPUT_DIR/${slug}.html"
}

capture synth-desktop AudioKit/AudioKitSynthOne 1440 1800
capture synth-mobile AudioKit/AudioKitSynthOne 390 1600
capture course-desktop microsoft/AI-For-Beginners 1440 1800
capture course-mobile microsoft/AI-For-Beginners 390 1600
capture cloudflared-desktop cloudflare/cloudflared 1440 1900
capture cloudflared-mobile cloudflare/cloudflared 390 1700
capture fallback-desktop cloudflare/cloudflared 1440 1900 "" block-api
capture fallback-mobile cloudflare/cloudflared 390 1700 "" block-api

grep -F "playable open-source synthesizer app" "$OUTPUT_DIR/synth-desktop.html"
grep -F "musicians" "$OUTPUT_DIR/synth-desktop.html"
grep -F "Get or open the app" "$OUTPUT_DIR/synth-desktop.html"
grep -F "Study or change the source code" "$OUTPUT_DIR/synth-desktop.html"
grep -F "oscillators, filters, reverbs and effects" "$OUTPUT_DIR/synth-desktop.html"
grep -F "iPhone/Universal version and accessibility support" "$OUTPUT_DIR/synth-desktop.html"
grep -F "preset search, a MIDI learn matrix and assignable touchpads" "$OUTPUT_DIR/synth-desktop.html"
! grep -Eqi "Ableton Link SDK|From: Localizations" "$OUTPUT_DIR/synth-desktop.html"

grep -F "beginner curriculum for learning artificial intelligence" "$OUTPUT_DIR/course-desktop.html"
grep -F "24 lessons" "$OUTPUT_DIR/course-desktop.html"
grep -F "Start with the course setup" "$OUTPUT_DIR/course-desktop.html"
grep -F "Browse the course lessons" "$OUTPUT_DIR/course-desktop.html"
grep -F "business uses of AI" "$OUTPUT_DIR/course-desktop.html"
grep -F "deeper mathematics of deep learning" "$OUTPUT_DIR/course-desktop.html"
! grep -Eqi "@girlie|Machine Learning for Beginners Curriculum|:---:" "$OUTPUT_DIR/course-desktop.html"

for proof in cloudflared-desktop cloudflared-mobile fallback-desktop fallback-mobile; do
  grep -F "Command-line network client or service" "$OUTPUT_DIR/${proof}.html"
  grep -F "command-line client and background service for Cloudflare Tunnel" "$OUTPUT_DIR/${proof}.html"
  grep -F "outbound connections" "$OUTPUT_DIR/${proof}.html"
  grep -F "Install or download the command-line client" "$OUTPUT_DIR/${proof}.html"
  grep -F "Read the Cloudflare Tunnel documentation" "$OUTPUT_DIR/${proof}.html"
  grep -F "implemented Cloudflare Tunnel client and daemon" "$OUTPUT_DIR/${proof}.html"
  ! grep -Eqi "Website or web application|Deprecated versions|Cap.?n Proto" "$OUTPUT_DIR/${proof}.html"
done

grep -F "GitHub's metadata service could not be reached" "$OUTPUT_DIR/fallback-desktop.html" && exit 1 || true
grep -F "GitHub's metadata API was unavailable, so this reading uses the public README directly" "$OUTPUT_DIR/fallback-desktop.html"
grep -F "README-only reading" "$OUTPUT_DIR/fallback-desktop.html"
grep -F "Reading complete using the public README fallback" "$OUTPUT_DIR/fallback-desktop.html"
! grep -Fq "GitHub's public request limit has been reached" "$OUTPUT_DIR/fallback-desktop.html"

for proof in "$OUTPUT_DIR"/*.html; do
  ! grep -Fq "coding or markup language" "$proof"
done

printf 'browser-proof=pass\n'
