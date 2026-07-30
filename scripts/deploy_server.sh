#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="project-reader-api.service"
ROOT_DIR="/opt/project-reader"
EXPECTED_COMMIT=""
INSTALL_APACHE=0
PUBLIC_API_URL="https://reader-api.merrinworld.uk"
PAGES_ORIGIN="https://armpitpete.github.io"

usage() {
  cat <<'USAGE'
Usage: scripts/deploy_server.sh --expected-commit <40-char-sha> [options]

Options:
  --repo-root <path>       Production checkout, default /opt/project-reader
  --service <name>         systemd unit name, default project-reader-api.service
  --public-api-url <url>   Public HTTPS API URL, default https://reader-api.merrinworld.uk
  --pages-origin <origin>  Allowed frontend CORS origin, default https://armpitpete.github.io
  --install-apache         Install and enable the bundled Apache vhost
USAGE
}

fail() {
  echo "Project Reader deploy failed: $*" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --expected-commit)
      EXPECTED_COMMIT="${2:-}"
      shift 2
      ;;
    --repo-root)
      ROOT_DIR="${2:-}"
      shift 2
      ;;
    --service)
      SERVICE_NAME="${2:-}"
      shift 2
      ;;
    --public-api-url)
      PUBLIC_API_URL="${2:-}"
      shift 2
      ;;
    --pages-origin)
      PAGES_ORIGIN="${2:-}"
      shift 2
      ;;
    --install-apache)
      INSTALL_APACHE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument $1"
      ;;
  esac
done

[[ "$(id -u)" == "0" ]] || fail "run as root on Merrin's Oracle VPS"
[[ "$EXPECTED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail "--expected-commit must be a 40-character lowercase Git SHA"

ROOT_REAL="$(realpath -m "$ROOT_DIR")"
case "$ROOT_REAL" in
  /opt/project-reader|/opt/project-reader/*) ;;
  *) fail "refusing to deploy outside /opt/project-reader" ;;
esac

[[ -d "$ROOT_REAL/.git" ]] || fail "$ROOT_REAL must be an existing git checkout"
[[ -f "$ROOT_REAL/config/env" ]] || fail "create $ROOT_REAL/config/env from config/env.example"
[[ -f "$ROOT_REAL/deploy/systemd/project-reader-api.service" ]] || fail "missing systemd unit in checkout"

ENV_MODE="$(stat -c '%a' "$ROOT_REAL/config/env")"
[[ "$ENV_MODE" == "600" || "$ENV_MODE" == "400" ]] || fail "$ROOT_REAL/config/env must be chmod 600 or 400"
ENV_HASH_BEFORE="$(sha256sum "$ROOT_REAL/config/env" | awk '{print $1}')"

id project-reader >/dev/null 2>&1 || useradd --system --home-dir "$ROOT_REAL" --shell /usr/sbin/nologin project-reader
install -d -o project-reader -g project-reader -m 0750 "$ROOT_REAL/.cache"

git -C "$ROOT_REAL" fetch --prune origin main
REMOTE_HEAD="$(git -C "$ROOT_REAL" rev-parse origin/main)"
[[ "$REMOTE_HEAD" == "$EXPECTED_COMMIT" ]] || fail "origin/main is $REMOTE_HEAD, not expected $EXPECTED_COMMIT"
git -C "$ROOT_REAL" diff --quiet || fail "production checkout has unstaged changes"
git -C "$ROOT_REAL" diff --cached --quiet || fail "production checkout has staged changes"

if systemctl is-active --quiet "$SERVICE_NAME"; then
  systemctl stop "$SERVICE_NAME"
fi

git -C "$ROOT_REAL" checkout main
git -C "$ROOT_REAL" merge --ff-only "$EXPECTED_COMMIT"

VENV_PYTHON="$ROOT_REAL/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
  python3 -m venv "$ROOT_REAL/.venv"
fi
"$VENV_PYTHON" -m pip install -q --upgrade pip
"$VENV_PYTHON" -m pip install -q -e "$ROOT_REAL"
"$VENV_PYTHON" -m compileall -q "$ROOT_REAL/src" "$ROOT_REAL/scripts"

install -m 0644 "$ROOT_REAL/deploy/systemd/project-reader-api.service" "/etc/systemd/system/$SERVICE_NAME"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null

if [[ "$INSTALL_APACHE" == "1" ]]; then
  [[ -f "$ROOT_REAL/deploy/apache/reader-api.merrinworld.uk.conf" ]] || fail "missing Apache vhost in checkout"
  [[ -f /etc/letsencrypt/live/reader-api.merrinworld.uk/fullchain.pem ]] || fail "TLS certificate is missing for reader-api.merrinworld.uk"
  install -m 0644 "$ROOT_REAL/deploy/apache/reader-api.merrinworld.uk.conf" /etc/apache2/sites-available/reader-api.merrinworld.uk.conf
  a2enmod proxy proxy_http headers rewrite ssl >/dev/null
  a2ensite reader-api.merrinworld.uk.conf >/dev/null
  apache2ctl configtest
fi

systemctl start "$SERVICE_NAME"

# shellcheck disable=SC1091
set -a
. "$ROOT_REAL/config/env"
set +a
BIND_HOST="${PROJECT_READER_BIND_HOST:-127.0.0.1}"
BIND_PORT="${PROJECT_READER_BIND_PORT:-8091}"

curl -fsS "http://$BIND_HOST:$BIND_PORT/health" | "$VENV_PYTHON" -m json.tool >/dev/null
curl -fsS "http://$BIND_HOST:$BIND_PORT/ready" | "$VENV_PYTHON" -m json.tool >/dev/null
STATUS_JSON="$(curl -fsS "http://$BIND_HOST:$BIND_PORT/api/v1/status")"
echo "$STATUS_JSON" | "$VENV_PYTHON" -m json.tool >/dev/null
echo "$STATUS_JSON" | grep -F "project_reader.evidence.collect_public_evidence" >/dev/null

READ_JSON="$(curl -fsS -m 180 \
  -H 'content-type: application/json' \
  -X POST \
  --data '{"repository":"armpitpete/over-my-home"}' \
  "http://$BIND_HOST:$BIND_PORT/api/v1/read")"
echo "$READ_JSON" | "$VENV_PYTHON" -m json.tool >/dev/null
echo "$READ_JSON" | grep -F '"ok": true' >/dev/null
echo "$READ_JSON" | grep -F '"repository": "armpitpete/over-my-home"' >/dev/null
echo "$READ_JSON" | grep -F '"status": "Unknown"' >/dev/null

if [[ "$INSTALL_APACHE" == "1" ]]; then
  systemctl reload apache2
  curl -fsS "$PUBLIC_API_URL/health" | "$VENV_PYTHON" -m json.tool >/dev/null
  curl -fsS "$PUBLIC_API_URL/api/v1/status" | "$VENV_PYTHON" -m json.tool >/dev/null
  CORS_HEADERS="$(mktemp)"
  curl -fsS -o /dev/null -D "$CORS_HEADERS" \
    -X OPTIONS \
    -H "Origin: $PAGES_ORIGIN" \
    -H "Access-Control-Request-Method: POST" \
    "$PUBLIC_API_URL/api/v1/read"
  grep -Fi "access-control-allow-origin: $PAGES_ORIGIN" "$CORS_HEADERS" >/dev/null
  rm -f "$CORS_HEADERS"
fi

ENV_HASH_AFTER="$(sha256sum "$ROOT_REAL/config/env" | awk '{print $1}')"
[[ "$ENV_HASH_AFTER" == "$ENV_HASH_BEFORE" ]] || fail "config/env changed during deploy"
FINAL_HEAD="$(git -C "$ROOT_REAL" rev-parse HEAD)"
[[ "$FINAL_HEAD" == "$EXPECTED_COMMIT" ]] || fail "deployed checkout is $FINAL_HEAD, not expected $EXPECTED_COMMIT"
[[ -z "$(git -C "$ROOT_REAL" status --porcelain --untracked-files=no)" ]] || fail "tracked checkout is not clean after deploy"
systemctl is-active --quiet "$SERVICE_NAME" || fail "$SERVICE_NAME is not active"

echo "Project Reader deployed $FINAL_HEAD at $PUBLIC_API_URL"
