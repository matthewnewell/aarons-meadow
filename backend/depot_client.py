"""
A thin client for Conway's Depot's own API. Aaron's Meadow's own pages still work fully
standalone if the Depot is down — unlike Task Master, nothing here blocks on it. Two occasions
reach out to it: publishing a spec (registers it as a catalog entry) and resolving a display
name for whoever the Depot says is looking (arrives as `?person_id=` on the Launchpad's own
"launch this app" link — see conways-depot's LaunchpadPage.tsx) so a spec's author is picked up
automatically instead of typed by hand, the same "you don't re-introduce yourself" idea as Task
Master's persona passthrough, just a one-time name lookup rather than a synced identity. Both
fail soft — a spec creates with no author, or publishes with no catalog listing, rather than
blocking on the Depot being reachable. Server-to-server, same reason every cross-app call in
this ecosystem is.
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


def fetch_person_name(person_id: str) -> str | None:
    """Resolves a Depot persona id to its display name. The Depot has no per-id lookup route —
    only the full list (routes/people.py there) — so this fetches that and filters; the list is
    small (a handful of demo personas) and this is called once per "+ New spec" click, not on
    every page load, so the extra weight doesn't matter. None on any failure (Depot down, id not
    found) — the caller falls back to no author, same as if nothing were passed at all."""
    try:
        r = httpx.get(f"{DEPOT_API_URL}/api/people", timeout=3.0)
        if r.status_code != 200:
            return None
        person = next((p for p in r.json() if p.get("id") == person_id), None)
        return person.get("name") if person else None
    except httpx.HTTPError:
        return None
