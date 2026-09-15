"""
A thin client for Conway's Depot's own API — used only when a spec is published. Unlike Task
Master (which depends on the Depot live for identity on every page load), Aaron's Meadow's own
pages work fully standalone; the Depot only needs to be reachable at the moment someone clicks
Publish, to register the finished spec as a catalog entry. Server-to-server, same reason every
cross-app call in this ecosystem is.
"""

import os

import httpx

DEPOT_API_URL = os.environ.get("DEPOT_API_URL", "http://localhost:8090").rstrip("/")
# Where this app's own frontend lives — used to build the `url` a published spec's Application
# row points at (its own read-only spec page, not a running product; see routes/specs.py).
MEADOW_FRONTEND_URL = os.environ.get("MEADOW_FRONTEND_URL", "http://localhost:5187").rstrip("/")


def register_application(*, name: str, description: str, scope: str, category: str, url: str) -> dict | None:
    """Registers a published spec as a Depot Application. Returns the created row, or None on
    any failure — the caller decides what that means for the publish flow (see routes/specs.py:
    publishing still marks the spec published even if this fails, since the spec itself is the
    real artifact; the Depot listing is a courtesy, not the source of truth)."""
    try:
        r = httpx.post(
            f"{DEPOT_API_URL}/api/applications",
            json={
                "name": name,
                "description": description,
                "owning_team": "Aaron's Meadow",
                "team_type": "enabling",
                "scope": scope,
                "category": category,
                "url": url,
            },
            timeout=5.0,
        )
        if r.status_code not in (200, 201):
            return None
        return r.json()
    except httpx.HTTPError:
        return None
