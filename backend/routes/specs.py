from flask import Blueprint, jsonify, request

import ai_client
import depot_client
from db import db
from models import DECLARED_SCOPES, STATUSES, Spec

bp = Blueprint("specs", __name__, url_prefix="/api/specs")

_SPEC_FIELDS = (
    "title", "problem_statement", "who_its_for", "key_features", "out_of_scope", "open_questions",
)

_SYSTEM_PROMPT = """You are the interviewer inside Aaron's Meadow — a place non-programmers go
to work out what they actually want to build. You are talking to someone with no software
background. Never use unexplained jargon; if a technical word is unavoidable, define it in the
same breath.

Your job is a real interview, not a form: ask ONE question at a time. Never present a wall of
questions. Push back where it's warranted — agreement is not helpfulness. In particular:
- If what they describe sounds like it's actually two different apps, say so plainly and help
  them see the seam, rather than smoothing it into one spec that quietly does two things.
- If an answer is vague ("something to track stuff"), ask a sharper follow-up instead of
  writing it down as-is.

EARLY IN THE INTERVIEW, ONCE, gently ask whether this needs to exist as an app at all — or
whether it's really automating a process that should just be deleted or simplified instead
(this is not you moralizing; it's a real, useful question — someone digitizing a paper form
should be asked whether the form should exist). Ask it once, record what they concluded in
`deletion_conclusion`, and then never bring it up again.

As the conversation progresses, fill in the spec's own fields via `spec_updates` — only include
a field in `spec_updates` when you actually have new or changed information for it; never
restate a field that hasn't changed. Fields: title (short name for the app), problem_statement
(what's wrong today, in their own words), who_its_for, key_features (plain text, one idea per
line), out_of_scope (what this deliberately does NOT do — as important as what it does),
open_questions (things still unresolved, worth a developer's attention).

Respond with ONLY this JSON shape:
{"reply": "your next message to them, one question or one thought — not a wall of text",
 "spec_updates": {<only fields with new/changed info>},
 "asked_deletion_question": true or false (true only on the turn you're asking it),
 "deletion_conclusion": "<what they concluded, or null if not resolved yet>"}
"""


def _build_context(spec: Spec) -> str:
    lines = ["Spec so far:"]
    for field in _SPEC_FIELDS:
        value = getattr(spec, field)
        lines.append(f"- {field}: {value or '(not yet known)'}")
    lines.append(f"- deletion question already asked: {spec.deletion_question_asked}")
    if spec.deletion_question_conclusion:
        lines.append(f"- deletion question conclusion: {spec.deletion_question_conclusion}")
    return "\n".join(lines)


@bp.get("")
def list_specs():
    specs = Spec.query.order_by(Spec.updated_at.desc()).all()
    return jsonify([s.to_dict() for s in specs])


@bp.post("")
def create_spec():
    body = request.get_json(force=True) or {}
    spec = Spec(created_by=(body.get("created_by") or "").strip() or None)
    db.session.add(spec)
    db.session.commit()
    return jsonify(spec.to_dict()), 201


@bp.get("/<spec_id>")
def get_spec(spec_id):
    return jsonify(Spec.query.get_or_404(spec_id).to_dict())


@bp.delete("/<spec_id>")
def delete_spec(spec_id):
    spec = Spec.query.get_or_404(spec_id)
    if spec.status == "published":
        return jsonify({"error": "a published spec can't be deleted here — it's registered in the Depot's own catalog now"}), 400
    db.session.delete(spec)
    db.session.commit()
    return "", 204


@bp.post("/<spec_id>/chat")
def chat(spec_id):
    """One interview turn: the person's message in, the interviewer's reply — and whatever new
    spec fields it learned — out. Stateless AI call, but unlike every other app's chat (see
    models.py's own docstring), the conversation itself is persisted here, not left to the
    frontend, so a draft can sit on the workbench and get picked back up later with full
    context intact."""
    spec = Spec.query.get_or_404(spec_id)
    if spec.status != "draft":
        return jsonify({"error": "only a draft spec can still be interviewed"}), 400

    body = request.get_json(force=True) or {}
    user_message = (body.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    if not ai_client.is_configured():
        return jsonify({"error": ai_client.NOT_CONFIGURED_MESSAGE}), 200

    messages = spec.message_list
    messages.append({"role": "user", "content": user_message})

    context = _build_context(spec)
    result = ai_client.chat_json(
        messages=[{"role": "user", "content": f"{context}\n\nConversation so far:\n" +
                   "\n".join(f"{m['role']}: {m['content']}" for m in messages)}],
        system=_SYSTEM_PROMPT,
        max_tokens=1024,
    )
    if "error" in result:
        return jsonify({"error": result["error"]}), 200

    reply = (result.get("reply") or "").strip()
    if not reply:
        return jsonify({"error": "AI reply didn't include a message."}), 200

    messages.append({"role": "assistant", "content": reply})
    spec.message_list = messages

    updates = result.get("spec_updates")
    if isinstance(updates, dict):
        for field in _SPEC_FIELDS:
            if field in updates and updates[field]:
                setattr(spec, field, updates[field])

    if not spec.deletion_question_asked and result.get("asked_deletion_question"):
        spec.deletion_question_asked = True
    if result.get("deletion_conclusion"):
        spec.deletion_question_conclusion = result["deletion_conclusion"]

    db.session.commit()
    return jsonify(spec.to_dict())


@bp.put("/<spec_id>/conformance")
def update_conformance(spec_id):
    """The conformance contract's own three answers — declared scope, what it consumes/emits
    from the digital thread. Set directly (a short form, not part of the interview) since
    these are closing-the-loop questions, not brainstorm material."""
    spec = Spec.query.get_or_404(spec_id)
    if spec.status != "draft":
        return jsonify({"error": "conformance answers can only change while still a draft"}), 400

    body = request.get_json(force=True) or {}
    if "declared_scope" in body:
        scope = body["declared_scope"]
        if scope not in DECLARED_SCOPES:
            return jsonify({"error": f"declared_scope must be one of {DECLARED_SCOPES}"}), 400
        spec.declared_scope = scope
    if "consumes" in body:
        spec.consumes = (body["consumes"] or "").strip() or None
    if "emits" in body:
        spec.emits = (body["emits"] or "").strip() or None

    db.session.commit()
    return jsonify(spec.to_dict())


@bp.post("/<spec_id>/submit-for-review")
def submit_for_review(spec_id):
    """draft -> in_review. Requires the conformance contract actually filled in — a title, a
    declared scope, and *some* answer on emits (consumes may legitimately be empty; emitting
    nothing is fine per the spec, but the question still has to have been answered, not
    skipped)."""
    spec = Spec.query.get_or_404(spec_id)
    if spec.status != "draft":
        return jsonify({"error": "only a draft can be submitted for review"}), 400

    missing = []
    if not spec.title:
        missing.append("title")
    if not spec.declared_scope:
        missing.append("declared_scope")
    if spec.emits is None:
        missing.append("emits (say \"nothing\" if that's the honest answer)")
    if missing:
        return jsonify({"error": f"can't submit yet — missing: {', '.join(missing)}"}), 400

    spec.status = "in_review"
    db.session.commit()
    return jsonify(spec.to_dict())


# Depot's own scope is (project|organizational); category is one of five 15288-derived aisles.
# Aaron's Meadow's own thin 3-way declaration maps onto that richer pair only here, at the one
# moment a spec actually needs to speak the Depot's language — see models.py's own note on why
# the interview itself never has to teach 15288.
_DEPOT_MAPPING = {
    "project": ("project", "project"),
    "organizational": ("organizational", "enterprise"),
    "general": ("organizational", "general"),
}


def _human_review_gate(spec: Spec) -> bool:
    """The second half of the review gate — stubbed on purpose, per the user's own call (no
    Scan Me integration for this MVP either; a documentation artifact has no repo for Scan Me
    to scan yet). Always passes for now; this is the one seam a real review queue plugs into
    later without anything else here changing."""
    return True


@bp.post("/<spec_id>/publish")
def publish(spec_id):
    """in_review -> published, and — the actual point — registers the spec as a real Depot
    catalog entry. The spec stays `published` even if that registration call fails (the spec
    itself is the real artifact; the Depot listing is a courtesy) — depot_application_id is
    just null in that case, visible on the record for whoever notices and wants to retry."""
    spec = Spec.query.get_or_404(spec_id)
    if spec.status != "in_review":
        return jsonify({"error": "only a spec already in review can be published"}), 400
    if not _human_review_gate(spec):
        return jsonify({"error": "did not pass review"}), 400

    depot_scope, depot_category = _DEPOT_MAPPING[spec.declared_scope]
    description_parts = [spec.problem_statement or ""]
    if spec.who_its_for:
        description_parts.append(f"For: {spec.who_its_for}")
    description = " — ".join(p for p in description_parts if p) or "A spec from Aaron's Meadow — no working app yet, see the spec itself."

    spec.status = "published"
    app_row = depot_client.register_application(
        name=spec.title,
        description=description,
        scope=depot_scope,
        category=depot_category,
        url=f"{depot_client.MEADOW_FRONTEND_URL}/specs/{spec.id}",
    )
    if app_row:
        spec.depot_application_id = app_row["id"]

    db.session.commit()
    return jsonify(spec.to_dict())
