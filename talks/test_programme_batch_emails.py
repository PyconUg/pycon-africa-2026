"""Regression: batch status changes must queue distinct programme emails per proposal."""

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import transaction
from django.test import TransactionTestCase, override_settings

from home.models import EventYear
from talks.models import Proposal

User = get_user_model()


@override_settings(
    DEFAULT_FROM_EMAIL="programme-test@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class BatchProgrammeEmailTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.ey, _ = EventYear.objects.get_or_create(
            year=2098,
            defaults={"template_path": "2098/home/home.html", "home_info": ""},
        )
        self.u1 = User.objects.create_user(
            username="batch_prog_u1", email="batch_prog_u1@example.com", password="x"
        )
        self.u2 = User.objects.create_user(
            username="batch_prog_u2", email="batch_prog_u2@example.com", password="x"
        )
        self.p1 = Proposal.objects.create(
            title="Batch test proposal one",
            talk_type="Short Talk",
            talk_category="GP / Web",
            user=self.u1,
            event_year=self.ey,
            status="S",
            user_response="P",
            intended_audience="INT-L",
            elevator_pitch="Pitch one.",
            talk_abstract="Abstract one.",
            recording_release=True,
        )
        self.p2 = Proposal.objects.create(
            title="Batch test proposal two",
            talk_type="Short Talk",
            talk_category="GP / Web",
            user=self.u2,
            event_year=self.ey,
            status="S",
            user_response="P",
            intended_audience="INT-L",
            elevator_pitch="Pitch two.",
            talk_abstract="Abstract two.",
            recording_release=True,
        )

    def _response_href(self, email_message):
        for content, mimetype in email_message.alternatives:
            if mimetype == "text/html":
                return content
        return email_message.body

    def test_batch_accept_sends_distinct_response_urls(self):
        """Mimic admin batch accept in one transaction; each email must contain its proposal's respond URL."""
        qs = Proposal.objects.filter(pk__in=[self.p1.pk, self.p2.pk]).order_by("pk")
        with transaction.atomic():
            for proposal_pk in qs.values_list("pk", flat=True):
                proposal = Proposal.objects.get(pk=proposal_pk)
                proposal.status = "A"
                proposal.save()

        self.assertEqual(len(mail.outbox), 2)

        by_to = {tuple(m.to): m for m in mail.outbox}
        m1 = by_to[("batch_prog_u1@example.com",)]
        m2 = by_to[("batch_prog_u2@example.com",)]
        html_a = self._response_href(m1)
        html_b = self._response_href(m2)

        u1_href = f"/{self.ey.year}/talks/proposal/{self.p1.proposal_id.hashid}/respond/"
        u2_href = f"/{self.ey.year}/talks/proposal/{self.p2.proposal_id.hashid}/respond/"

        self.assertIn(u1_href, html_a)
        self.assertIn(u2_href, html_b)
        self.assertNotEqual(self.p1.proposal_id.hashid, self.p2.proposal_id.hashid)
        self.assertNotIn(u1_href, html_b)
        self.assertNotIn(u2_href, html_a)
