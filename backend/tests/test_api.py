"""API tests in demo mode (tiny untrained model) - CD-5 functional and security test cases."""
import base64
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app(Settings(demo_mode=True, api_key=None))) as test_client:
        yield test_client


def jpeg_bytes(width=240, height=300):
    pixels = (np.random.default_rng(0).random((height, width, 3)) * 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="JPEG")
    return buffer.getvalue()


def post(client, data, image=None, name="face.jpg", mime="image/jpeg"):
    return client.post("/api/v1/analyze", data=data, files={"image": (name, image or jpeg_bytes(), mime)})


def test_health_reports_demo_model(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["model_loaded"] and body["demo_mode"]


def test_analyze_returns_prediction_heatmap_and_recommendations(client):
    response = post(client, {"consent": "true", "age": "16", "sex": "male"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["skin_type"] in ("dry", "normal", "oily")
    assert sum(body["probabilities"].values()) == pytest.approx(1.0, abs=1e-3)
    for key in ("face_image", "heatmap_image"):
        assert Image.open(io.BytesIO(base64.b64decode(body[key]))).size == (384, 384)
    assert [s["key"] for s in body["recommendations"]["steps"]] == ["cleanse", "treat", "protect"]
    assert response.headers["cache-control"] == "no-store"
    assert body["quality"]["passed"] is True


def test_consent_is_required(client):
    assert post(client, {"consent": "false"}).status_code == 400


def test_non_image_is_rejected(client):
    assert post(client, {"consent": "true"}, image=b"not an image", name="a.txt", mime="text/plain").status_code == 415


def test_invalid_age_is_rejected(client):
    assert post(client, {"consent": "true", "age": "9"}).status_code == 422


def test_oversized_upload_is_rejected():
    app = create_app(Settings(demo_mode=True, api_key=None, max_upload_mb=0.01))
    with TestClient(app) as small:
        assert post(small, {"consent": "true"}).status_code == 413


def test_api_key_is_enforced_except_health():
    with TestClient(create_app(Settings(demo_mode=True, api_key="secret"))) as secured:
        assert secured.get("/api/v1/skin-types").status_code == 401
        assert secured.get("/api/v1/skin-types", headers={"X-API-Key": "secret"}).status_code == 200
        assert secured.get("/api/v1/health").status_code == 200


def dark_jpeg():
    pixels = (np.random.default_rng(1).random((300, 240, 3)) * 40).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_dark_photo_is_rejected_by_quality_gate():
    with TestClient(create_app(Settings(demo_mode=True, api_key=None, quality_gate="reject"))) as strict:
        response = post(strict, {"consent": "true"}, image=dark_jpeg())
        assert response.status_code == 422
        assert "too dark" in response.json()["detail"]


def test_warn_mode_returns_the_quality_report():
    with TestClient(create_app(Settings(demo_mode=True, api_key=None, quality_gate="warn"))) as lenient:
        response = post(lenient, {"consent": "true"}, image=dark_jpeg())
        assert response.status_code == 200
        quality = response.json()["quality"]
        assert quality["passed"] is False and quality["issues"]


def test_web_app_is_served_with_security_headers(client):
    page = client.get("/app/")
    assert page.status_code == 200 and "<title>Glowrithm (web test build)</title>" in page.text
    assert "camera=(self)" in page.headers["permissions-policy"]
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert client.get("/app/app.js").status_code == 200
    root = client.get("/", follow_redirects=False)
    assert root.status_code in (302, 307) and root.headers["location"] == "/app/"


def test_web_app_can_be_switched_off():
    with TestClient(create_app(Settings(demo_mode=True, api_key=None, serve_web=False))) as plain:
        assert plain.get("/app/").status_code == 404
        assert plain.get("/").json()["name"] == "Glowrithm API"
