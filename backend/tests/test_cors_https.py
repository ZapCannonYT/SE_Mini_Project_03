"""TC-SEC-05 (DFIP-SR-005): CORS is limited to the frontend origin; HTTPS dev setup is present."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def preflight(origin: str):
    return client.options(
        "/api/products",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )


def test_allowed_frontend_origin_gets_cors_headers():
    res = preflight("https://localhost:5173")
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "https://localhost:5173"


def test_other_origin_gets_no_cors_headers():
    res = preflight("https://evil.example.com")
    assert "access-control-allow-origin" not in res.headers


def test_wildcard_is_never_allowed():
    s = Settings(cors_origins="*, https://localhost:5173")
    assert s.cors_origin_list == ["https://localhost:5173"]


def test_dev_certificate_script_exists_and_certs_are_ignored():
    assert (ROOT / "scripts" / "make_dev_cert.py").is_file()
    assert "certs/" in (ROOT / ".gitignore").read_text().splitlines()
