"""
Aaron's Meadow: a place non-programmers go to work out what they actually want to build. The
interview assembles a `Spec` — structured enough that a developer can build from it, produced
entirely through conversation, never generated code. See depot_client.py for the one place this
app talks to Conway's Depot (registering a spec once it's published) — everywhere else it's
fully standalone, same "a link is a pointer, never a live integration" rule every sibling app
runs on, just applied to a one-time write instead of a stored pointer.

The workbench lifecycle — draft -> in_review -> published — is owned entirely here; the Depot
only ever sees `published` (a single Application row created at that moment). No auth: like
every other app's journal, "who" is a free-text name the browser remembers, not a real account.
"""

import json
from datetime import datetime, timezone

from db import _uuid, db


def _now():
    return datetime.now(timezone.utc)


STATUSES = ("draft", "in_review", "published")

# The conformance contract's own 3-way declaration — deliberately not Conway's Depot's real
# two-tier scope+category taxonomy (project|organizational scope, five 15288-derived
# categories). Keeping this thin, as asked: one flat choice, mapped onto the Depot's richer
# fields only at publish time (see routes/specs.py's _DEPOT_MAPPING) — a spec author never has
# to learn 15288 process groups to describe what they're proposing.
DECLARED_SCOPES = ("project", "organizational", "general")


class Spec(db.Model):
    __tablename__ = "spec"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    title = db.Column(db.String(300), nullable=True)  # set once the interview names it
    status = db.Column(db.String(20), nullable=False, default="draft")
    created_by = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now, nullable=False)

    # The full interview, persisted (not the usual ecosystem-wide "frontend owns history,
    # backend is stateless" pattern every other app's chat uses) — deliberate: a workbench
    # draft is meant to sit around and get picked back up days later, so the conversation has
    # to survive a reload the way The Fixer's or Value Stream's chat panes don't need to.
    # JSON in a Text column, same "short list, no child table" convention as Project.channels.
    messages = db.Column(db.Text, nullable=True)  # [{role, content}, ...]

    # The spec that assembles itself as the interview goes — a fixed, known shape (not an
    # arbitrary AI-shaped blob) so the frontend can render each field predictably as it fills
    # in. Every field starts null/empty; the interview fills them in, never all at once.
    problem_statement = db.Column(db.Text, nullable=True)
    who_its_for = db.Column(db.Text, nullable=True)
    key_features = db.Column(db.Text, nullable=True)  # newline-separated, kept as plain text
    out_of_scope = db.Column(db.Text, nullable=True)
    open_questions = db.Column(db.Text, nullable=True)

    # The deletion question — asked once, early, then never again. See routes/specs.py's
    # system prompt for the actual framing ("does this need to exist at all").
    deletion_question_asked = db.Column(db.Boolean, nullable=False, default=False)
    deletion_question_conclusion = db.Column(db.Text, nullable=True)

    # The conformance contract, filled in before a spec can move to in_review — see
    # routes/specs.py's submit_for_review.
    declared_scope = db.Column(db.String(20), nullable=True)  # see DECLARED_SCOPES
    consumes = db.Column(db.Text, nullable=True)  # what it reads from the digital thread
    emits = db.Column(db.Text, nullable=True)  # what it writes back — "nothing" is a fine answer

    # Set once publish actually registers the spec in the Depot's own catalog — see
    # depot_client.register_application. Null if that call failed; the spec is still
    # `published` either way, since the spec itself is the real artifact.
    depot_application_id = db.Column(db.String(36), nullable=True)

    @property
    def message_list(self) -> list[dict]:
        return json.loads(self.messages) if self.messages else []

    @message_list.setter
    def message_list(self, value: list[dict]) -> None:
        self.messages = json.dumps(value) if value else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.message_list,
            "problem_statement": self.problem_statement,
            "who_its_for": self.who_its_for,
            "key_features": self.key_features,
            "out_of_scope": self.out_of_scope,
            "open_questions": self.open_questions,
            "deletion_question_asked": self.deletion_question_asked,
            "deletion_question_conclusion": self.deletion_question_conclusion,
            "declared_scope": self.declared_scope,
            "consumes": self.consumes,
            "emits": self.emits,
            "depot_application_id": self.depot_application_id,
        }
