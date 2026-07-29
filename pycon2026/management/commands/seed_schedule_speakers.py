"""Seed local dev data: a User + Profile + accepted Proposal for every speaker
named in the static 2026 schedule (pycon2026/schedule_data.py), so the
"click a speaker name on the schedule" flow can be tested against real
matches instead of an empty Profile table.

Bios/abstracts are placeholder text explicitly marked as seed data - not
real biographical claims about these speakers.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from home.models import EventYear
from registration.models import Profile
from talks.models import Proposal

from pycon2026.schedule_data import SCHEDULE_DATA

DEFAULT_TALK_TYPE = "Short Talk"
DEFAULT_TALK_CATEGORY = "ET"
LABEL_TALK_TYPE = {
    "tutorial": "Tutorial",
    "short talk": "Short Talk",
    "talk": "Long Talk",
}


def _talk_type_from_label(label):
    if not label:
        return DEFAULT_TALK_TYPE
    kind = label.split("·")[0].strip().lower()
    return LABEL_TALK_TYPE.get(kind, DEFAULT_TALK_TYPE)


def _iter_schedule_entries():
    """Yield (speaker, title, talk_type) for every named slot in SCHEDULE_DATA."""
    for day in SCHEDULE_DATA:
        for slot in day.get("slots", []):
            for cell in slot.get("cells", []):
                if cell.get("speaker") and cell.get("title"):
                    yield cell["speaker"], cell["title"], _talk_type_from_label(cell.get("label"))
            for talk in slot.get("talks", []):
                if talk.get("speaker") and talk.get("title"):
                    yield talk["speaker"], talk["title"], "Lightning Talk"


def _split_name(full_name):
    parts = full_name.strip().split(None, 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")


class Command(BaseCommand):
    help = (
        "Seed a confirmed Profile + Proposal for every speaker named in the 2026 "
        "schedule, so the schedule's speaker-name links resolve to real profiles "
        "in local dev. Safe to re-run (idempotent)."
    )

    def handle(self, *args, **options):
        event_year, _ = EventYear.objects.get_or_create(year=2026)

        # One representative talk per speaker is enough to make them a
        # "confirmed speaker" - keep the first title we see for each name.
        by_speaker = {}
        for speaker, title, talk_type in _iter_schedule_entries():
            by_speaker.setdefault(speaker, (title, talk_type))

        created = 0
        for speaker, (title, talk_type) in by_speaker.items():
            name, surname = _split_name(speaker)
            slug = slugify(speaker) or "speaker"
            username = f"schedule_seed_{slug}"[:150]

            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{slug}@example.invalid",
                    "first_name": name,
                    "last_name": surname,
                },
            )

            Profile.objects.get_or_create(
                user=user,
                defaults={
                    "name": name,
                    "surname": surname,
                    "is_visible": True,
                    "city": "Kampala",
                    "country": "UG",
                    "biography": (
                        f"[Seed data for local testing] Placeholder bio for {speaker}, "
                        f'speaking on "{title}" at PyCon Africa 2026.'
                    ),
                },
            )

            Proposal.objects.get_or_create(
                user=user,
                title=title,
                event_year=event_year,
                defaults={
                    "talk_type": talk_type,
                    "talk_category": DEFAULT_TALK_CATEGORY,
                    "status": "A",
                    "user_response": "A",
                    "elevator_pitch": f"[Seed data] {title}",
                    "talk_abstract": f'[Seed data] Placeholder abstract for "{title}".',
                },
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} speaker(s) as confirmed speakers for PyCon Africa {event_year.year}."
        ))
