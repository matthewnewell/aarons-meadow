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


def test_new_spec_has_no_owner_and_is_private_by_default(client):
    spec = client.post("/api/specs", json={}).get_json()
    assert spec["person_id"] is None
    assert spec["visibility"] == "private"


def test_create_spec_with_a_person_id_sets_ownership(client):
    spec = client.post("/api/specs", json={"person_id": "person-abc"}).get_json()
    assert spec["person_id"] == "person-abc"


def test_list_filters_by_person_id_regardless_of_visibility(client):
    mine = client.post("/api/specs", json={"person_id": "person-abc"}).get_json()
    client.post("/api/specs", json={"person_id": "person-xyz"}).get_json()

    res = client.get("/api/specs?person_id=person-abc")
    ids = [s["id"] for s in res.get_json()]
    assert ids == [mine["id"]]


def test_list_filters_by_public_visibility_across_owners(client):
    mine = client.post("/api/specs", json={"person_id": "person-abc"}).get_json()
    client.put(f"/api/specs/{mine['id']}/visibility", json={"visibility": "public"})
    client.post("/api/specs", json={"person_id": "person-xyz"}).get_json()  # stays private

    res = client.get("/api/specs?visibility=public")
    ids = [s["id"] for s in res.get_json()]
    assert ids == [mine["id"]]


def test_visibility_rejects_an_invalid_value(client):
    spec = client.post("/api/specs", json={}).get_json()
    res = client.put(f"/api/specs/{spec['id']}/visibility", json={"visibility": "everyone"})
    assert res.status_code == 400


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


def test_publish_stays_in_the_meadow(client):
    """in_review -> published shouldn't touch the Depot at all anymore — no network call to
    fail/succeed, just a status flip. Regression test for the "stopped registering a separate
    Depot Application per spec" fix."""
    created = client.post("/api/specs", json={}).get_json()
    spec_id = created["id"]
    client.put(f"/api/specs/{spec_id}/conformance", json={
        "declared_scope": "general", "consumes": "", "emits": "nothing",
    })
    with client.application.app_context():
        from models import Spec
        s = Spec.query.get(spec_id)
        s.title = "Test App"
        db.session.commit()
    client.post(f"/api/specs/{spec_id}/submit-for-review")

    res = client.post(f"/api/specs/{spec_id}/publish")
    assert res.status_code == 200
    spec = res.get_json()
    assert spec["status"] == "published"
    assert "depot_application_id" not in spec


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
