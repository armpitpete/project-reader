from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_systemd_unit_runs_as_dedicated_unprivileged_service() -> None:
    unit = (ROOT / "deploy/systemd/project-reader-api.service").read_text(
        encoding="utf-8"
    )

    assert "User=project-reader" in unit
    assert "Group=project-reader" in unit
    assert "WorkingDirectory=/opt/project-reader" in unit
    assert "EnvironmentFile=/opt/project-reader/config/env" in unit
    assert "Environment=PYTHONDONTWRITEBYTECODE=1" in unit
    assert "uvicorn project_reader.api:app" in unit
    assert "NoNewPrivileges=true" in unit
    assert "PrivateTmp=true" in unit
    assert "ProtectSystem=strict" in unit
    assert "ReadWritePaths=/opt/project-reader/.cache" in unit


def test_apache_vhost_uses_authorised_api_hostname_and_local_proxy() -> None:
    vhost = (ROOT / "deploy/apache/reader-api.merrinworld.uk.conf").read_text(
        encoding="utf-8"
    )

    assert "ServerName reader-api.merrinworld.uk" in vhost
    assert "<VirtualHost 10.0.0.107:443>" in vhost
    assert "SSLCertificateFile /etc/letsencrypt/live/reader-api.merrinworld.uk/fullchain.pem" in vhost
    assert "ProxyPass / http://127.0.0.1:8091/" in vhost
    assert "ProxyAddHeaders On" in vhost
    assert "RequestHeader unset X-Forwarded-For early" in vhost
    assert "LimitRequestBody 4096" in vhost
    assert "X-Content-Type-Options" in vhost
    assert "Referrer-Policy" in vhost


def test_deploy_script_preserves_exact_commit_and_server_secret_file() -> None:
    script = (ROOT / "scripts/deploy_server.sh").read_text(encoding="utf-8")

    assert "--expected-commit" in script
    assert "origin/main is $REMOTE_HEAD, not expected $EXPECTED_COMMIT" in script
    assert "ENV_HASH_BEFORE" in script
    assert "ENV_HASH_AFTER" in script
    assert "config/env changed during deploy" in script
    assert "project-reader-api.service" in script
    assert "reader-api.merrinworld.uk" in script
    assert "armpitpete/over-my-home" in script
    assert "access-control-allow-origin: $PAGES_ORIGIN" in script


def test_example_env_stages_both_pages_origins_for_identity_migration() -> None:
    env = (ROOT / "config/env.example").read_text(encoding="utf-8")

    assert (
        "PROJECT_READER_ALLOWED_ORIGINS="
        "https://armpitpete.github.io,https://merrinworld.github.io"
    ) in env
    assert "PROJECT_READER_API_BASE_URL=https://reader-api.merrinworld.uk" in env
    assert "PROJECT_READER_GITHUB_TOKEN=" in env
    assert "PRIVATE KEY" not in env.upper()
