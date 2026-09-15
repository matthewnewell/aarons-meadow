# Aaron's Meadow

A place non-programmers go to work out what they actually want to build. Named after Aaron
Meadows, a very talented software engineer.

## The idea

The meadow is a place, not a tool — you walk in and work. An interview, one question at a
time, no jargon without a definition in the same breath, produces a **specification**, not
working code. The handoff to implementation is a human one: a developer reads the finished
spec and builds from it. If a real execution environment ever gets swapped in, it slots in
behind the interview layer without the front end changing — nothing about this MVP forecloses
that, it just doesn't build it.

**The spec assembles itself visibly as you talk.** Conversation on one side, the spec filling
in on the other — you watch the artifact form instead of being handed one at the end.

**The interviewer pushes back.** If what you describe is really two apps, it says so.
Agreement is not helpfulness.

**The deletion question**, once, early: does this need to exist as an app at all, or is it
really a process that should be deleted or simplified instead? Asked gently but for real,
the conclusion recorded, then never brought up again. An app store full of digitized bad
processes is worse than an empty one.

## The lifecycle

```
draft ──> in_review ──> published
```

Aaron's Meadow owns this whole lifecycle — Conway's Depot only ever sees `published`. The
**workbench** (drafts and in-review specs) is distinct from "my apps" in the Depot, which are
apps you *use*, not ones still being worked out.

Publishing registers the spec as a real Application in the Depot's own catalog — scope and
category mapped from the spec's own thin 3-way declaration (`project` / `organizational` /
`general`) onto the Depot's richer two-tier taxonomy, so an author never has to learn 15288
process groups to describe what they're proposing (see `backend/routes/specs.py`'s
`_DEPOT_MAPPING`). The registered `url` points at the spec's own read-only page here — there's
no running product yet, so there's nothing else for it to point at.

## Review gate

Two seams, deliberately thin for this MVP:

1. Scan Me (the Depot's cybersecurity conformance app) — **not wired in**. It scans a GitHub
   repo's dependencies; a documentation-only spec has no repo yet for it to check. Revisit once
   a real execution environment exists.
2. Human review — **stubbed**. `_human_review_gate()` in `backend/routes/specs.py` always
   passes for now; a real review queue plugs in there without anything else changing.

## The conformance contract — kept thin

Before a spec can move to `in_review`, it needs:
- A title
- A declared scope (`project` / `organizational` / `general`)
- An answer on what it emits to the digital thread ("nothing" is a fine, honest answer)

What it *consumes* may legitimately be blank. Style — splash page, then views — is suggested by
example (every sibling app already does it this way), never enforced anywhere in code.

## Stack

Flask + SQLAlchemy + SQLite backend, React + TypeScript + Vite frontend — the same shape as
every sibling app in this ecosystem. `backend/ai_client.py` is the same file, ported verbatim
(Claude / Gemini / Ollama, off by default).

## Run it

Backend:

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py          # :8101
```

Frontend:

```bash
cd frontend
npm install
npm run dev                      # :5187, proxies /api to :8101
```

Fully standalone day to day — unlike Task Master, nothing here needs the Depot live except the
one moment someone clicks Publish (`DEPOT_API_URL`, default `http://localhost:8090`).

## AI (optional)

Off by default. Set in `backend/.env` or the environment:

```
AI_PROVIDER=claude   # or "gemini", "ollama"
AI_API_KEY=...
AI_MODEL=...           # optional override
```

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q
```
