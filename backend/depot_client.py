"""
A thin client for Conway's Depot's own API. Aaron's Meadow's own pages work fully standalone if
the Depot is down — nothing here blocks on it. The one thing it's used for: resolving a display
name for whoever the Depot says is looking (arrives as `?person_id=` on the Launchpad's own
"launch this app" link — see conways-depot's LaunchpadPage.tsx) so a new spec's author is picked
up automatically instead of typed by hand, the same "you don't re-introduce yourself" idea as
Task Master's persona passthrough, just a one-time name lookup rather than a synced identity.
Fails soft — a spec just creates with no author rather than blocking on the Depot being
reachable. Server-to-server, same reason every cross-app call in this ecosystem is.

Publishing a spec does NOT call anything here — a published spec stays on this app's own
workbench, never a new Depot Application; see models.py's own docstring for why.
"""

import os

import httpx

DEPOT_API_URL = os.environ.get("DEPOT_API_URL", "http://localhost:8090").rstrip("/")


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
