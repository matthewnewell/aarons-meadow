"""
Demo seed — one draft spec, mid-interview, so the workbench isn't an empty shell on first
look. A shop-floor scrap/rework reason log: realistic for an aerospace manufacturer (this
company's own domain — see user-company-context), and a genuine example of the deletion
question landing on "keep it" rather than "don't build this."
"""

from db import db
from models import Spec

_MESSAGES = [
    {"role": "assistant", "content": "Welcome to the meadow. What are you trying to build?"},
    {"role": "user", "content": "Something to track why parts get scrapped or reworked on the shop floor. Right now it's all in people's heads or scribbled on paper travelers."},
    {"role": "assistant", "content": "Before we go further — does this need to be an app at all, or is the real fix getting people to actually fill out the paper traveler consistently? I ask because a lot of \"let's digitize it\" ideas are really \"let's finally enforce the process we already have.\""},
    {"role": "user", "content": "No, the information genuinely isn't captured anywhere useful today — it's not that people skip a form, there's no form. It just gets said out loud in a hallway and forgotten."},
    {"role": "assistant", "content": "Got it — that's a real gap, not paperwork for its own sake. Who'd actually use this day to day?"},
    {"role": "user", "content": "Manufacturing engineers and quality leads, mostly when they're trying to figure out why the same failure keeps happening."},
]


def seed_if_empty():
    if Spec.query.count() > 0:
        return

    spec = Spec(
        title="Scrap & Rework Reason Log",
        status="draft",
        created_by="Sam Ortiz",
        problem_statement=(
            "Shop floor scrap and rework happen but the reasons live in people's heads or "
            "scattered paper travelers — nobody can see the patterns."
        ),
        who_its_for="Manufacturing engineers and quality leads reviewing recurring failure modes.",
        key_features=(
            "Log a scrap/rework event with a reason code\n"
            "Weekly summary of the top recurring reasons\n"
            "Link an event to the part number and job"
        ),
        out_of_scope=(
            "Not a full MRB (Material Review Board) disposition workflow — just capturing why, "
            "not managing the disposition process itself."
        ),
        open_questions=(
            "Does this need to tie back to Conway's Depot's own project id, or is it purely a "
            "shop-floor tool with no project context?"
        ),
        deletion_question_asked=True,
        deletion_question_conclusion=(
            "Concluded the process should stay — it's real information currently getting lost, "
            "not paperwork for its own sake. What's unnecessary is the disconnected "
            "sticky-note/verbal version, not the underlying need."
        ),
    )
    spec.message_list = _MESSAGES
    db.session.add(spec)
    db.session.commit()
