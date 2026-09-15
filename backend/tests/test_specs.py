import os
import sys

os.environ["DATA_DIR"] = os.path.join(os.path.dirname(__file__), "_tmp_data")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shutil

import pytest

from app import create_app
from db import db


@pytest.fixture()
def client():
    shutil.rmtree(os.environ["DATA_DIR"], ignore_errors=True)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.session.remove()
    shutil.rmtree(os.environ["DATA_DIR"], ignore_errors=True)


def test_seeded_draft(client):
    res = client.get("/api/specs")
    assert res.status_code == 200
    specs = res.get_json()
    assert len(specs) == 1
    assert specs[0]["status"] == "draft"
    assert specs[0]["deletion_question_asked"] is True
    assert len(specs[0]["messages"]) == 6


def test_create_spec(client):
    res = client.post("/api/specs", json={"created_by": "Someone"})
    assert res.status_code == 201
    spec = res.get_json()
    assert spec["status"] == "draft"
    assert spec["title"] is None


def test_chat_reports_ai_not_configured(client):
    created = client.post("/api/specs", json={}).get_json()
    res = client.post(f"/api/specs/{created['id']}/chat", json={"message": "I want an app"})
    assert res.status_code == 200
    assert "error" in res.get_json()


def test_chat_requires_a_message(client):
    created = client.post("/api/specs", json={}).get_json()
    res = client.post(f"/api/specs/{created['id']}/chat", json={"message": "  "})
    assert res.status_code == 400


def test_conformance_requires_valid_scope(client):
    created = client.post("/api/specs", json={}).get_json()
    res = client.put(f"/api/specs/{created['id']}/conformance", json={"declared_scope": "nonsense"})
    assert res.status_code == 400

    res = client.put(f"/api/specs/{created['id']}/conformance", json={"declared_scope": "general", "emits": "nothing"})
    assert res.status_code == 200
    assert res.get_json()["declared_scope"] == "general"


def test_submit_for_review_requires_conformance_contract(client):
    created = client.post("/api/specs", json={}).get_json()
    res = client.post(f"/api/specs/{created['id']}/submit-for-review")
    assert res.status_code == 400
    assert "missing" in res.get_json()["error"]


def test_full_lifecycle_to_submit(client):
    created = client.post("/api/specs", json={}).get_json()
    spec_id = created["id"]

    # Title only arrives via chat in the real flow; set it directly here since AI isn't
    # configured in tests — mirrors what a completed interview would have left behind.
    client.put(f"/api/specs/{spec_id}/conformance", json={
        "declared_scope": "general", "consumes": "", "emits": "nothing",
    })

    # Still missing a title.
    res = client.post(f"/api/specs/{spec_id}/submit-for-review")
    assert res.status_code == 400

    with client.application.app_context():
        from models import Spec
        s = Spec.query.get(spec_id)
        s.title = "Test App"
        db.session.commit()

    res = client.post(f"/api/specs/{spec_id}/submit-for-review")
    assert res.status_code == 200
    assert res.get_json()["status"] == "in_review"


def test_delete_blocked_once_published(client):
    created = client.post("/api/specs", json={}).get_json()
    spec_id = created["id"]
    with client.application.app_context():
        from models import Spec
        s = Spec.query.get(spec_id)
        s.status = "published"
        db.session.commit()

    res = client.delete(f"/api/specs/{spec_id}")
    assert res.status_code == 400
