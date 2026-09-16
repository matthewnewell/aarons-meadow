"""
One route: resolve a Depot persona id to a display name, so the workbench can fill in a new
spec's author automatically instead of asking for it by hand. See depot_client.fetch_person_name
for why this is a one-time lookup rather than a synced persona, unlike Task Master's own
routes/people.py (which mirrors the Depot's full list, since it needs the whole switcher).
"""

from flask import Blueprint, jsonify

import depot_client

bp = Blueprint("people", __name__, url_prefix="/api/people")


@bp.get("/<person_id>")
def get_person_name(person_id):
    """Always 200 — an unresolved id (Depot down, id doesn't exist) is a normal state here, not
    an error, same convention as every other cross-app read in this ecosystem (see the Depot's
    own /summary and /journal proxies)."""
    name = depot_client.fetch_person_name(person_id)
    return jsonify({"found": name is not None, "name": name})
