import models  # noqa: F401
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + __import__("os").path.join(__import__("tempfile").gettempdir(),"novasphere_test.db")
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient

import main


def test_health():
    c = TestClient(main.app)
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_signup_login_me():
    c = TestClient(main.app)
    r = c.post("/api/auth/signup", data={"username": "user1", "password": "pass1234"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # cookie set
    r2 = c.get("/api/auth/me")
    assert r2.status_code == 200
    assert r2.json().get("ok") is True


def test_dashboard_protected():
    c = TestClient(main.app)
    r = c.get("/", follow_redirects=False)
    assert r.status_code in (303, 307, 302, 401)


def test_ai_analyze():
    c = TestClient(main.app)
    c.post("/api/auth/signup", data={"username": "aiuser", "password": "pass1234"})
    r = c.post("/api/insights", json={"events": [{"level": "error", "msg": "boom"}], "metrics": {"cpu": 90}})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert len(r.json()["insights"]) >= 1