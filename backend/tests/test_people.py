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


def test_unresolvable_person_returns_200_not_found(client):
    """No live Depot in the test environment — same "fail soft, not error" contract as every
    other cross-app read in this ecosystem: a 200 saying nothing was found, never a 4xx/5xx."""
    res = client.get("/api/people/some-persona-id")
    assert res.status_code == 200
    body = res.get_json()
    assert body == {"found": False, "name": None}
