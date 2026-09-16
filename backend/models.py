"""
Aaron's Meadow: a place non-programmers go to work out what they actually want to build. The
interview assembles a `Spec` — structured enough that a developer can build from it, produced
entirely through conversation, never generated code. See depot_client.py for the one place this
app talks to Conway's Depot (resolving a display name for whoever's using it) — everywhere else
it's fully standalone.

The workbench lifecycle — draft -> in_review -> published — is owned entirely here, and stays
here: a published spec doesn't spin off a Depot Application of its own, it's just a page on this
app's own workbench (`/specs/<id>`) — a plain URL is the whole mechanism if a Depot project ever
wants to point at one specific spec, same "a link is a pointer, never a new catalog entry"
convention every sibling app already runs on for its own cross-references. No auth: like every
other app's journal, `created_by` is a free-text name the browser remembers, not a real account
— `person_id` (below) is the real Depot persona id when one is known (via the `?person_id=` the
Launchpad's launch link carries), used for ownership/filtering; both can be null (opened
standalone, no persona to resolve), in which case a spec just has no owner rather than a fake one.
"""

import json
from datetime import datetime, timezone

from db import _uuid, db


def _now():
    return datetime.now(timezone.utc)


STATUSES = ("draft", "in_review", "published")

# The conformance contract's own 3-way declaration — deliberately not Conway's Depot's real
# two-tier scope+category taxonomy (project|organizational scope, five 15288-derived
# categories). Keeping this thin, as asked: one flat choice a spec author can make without
# having to learn 15288 process groups — informs whoever eventually builds this, never sent
# anywhere (see this module's own docstring on why a published spec stays here, not the Depot).
DECLARED_SCOPES = ("project", "organizational", "general")

# private = only the owner's own "My workbench" view shows it; public = anyone can find it under
# "Public" too — the whole point being someone can invite review on a still-in-progress draft,
# not just a finished spec. Defaults to private: a spec starts as yours alone, you choose to
# open it up. A spec with no owner (person_id null) can still be made public — there's just no
# "My workbench" it will ever show up in.
VISIBILITIES = ("private", "public")


class Spec(db.Model):
    __tablename__ = "spec"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    title = db.Column(db.String(300), nullable=True)  # set once the interview names it
    status = db.Column(db.String(20), nullable=False, default="draft")
    created_by = db.Column(db.String(120), nullable=True)
    person_id = db.Column(db.String(36), nullable=True)  # the real owner — see module docstring
    visibility = db.Column(db.String(10), nullable=False, default="private")  # see VISIBILITIES
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
            "person_id": self.person_id,
            "visibility": self.visibility,
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
        }
