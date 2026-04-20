from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.template import Context, Template
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from home.models import EventYear

from .models import (
    FinAidApplicationReview,
    FinAidReviewer,
    Fin_aid,
    OpportunityGrantApplication,
)


class OpportunityGrantApplyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('applicant', 'a@example.com', 'testpass123')
        self.event_year = EventYear.objects.create(year=2026, home_info='test')
        self.fin = Fin_aid.objects.create(
            title='OG 2026',
            event_year=self.event_year,
            fin_open_date=timezone.now() - timedelta(days=1),
            fin_close_date=timezone.now() + timedelta(days=7),
        )

    def test_legacy_fin_aid_path_redirects_permanently(self):
        response = self.client.get('/2026/fin-aid/apply/', follow=False)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], '/2026/opportunity-grants/apply/')

    def test_apply_redirects_when_not_logged_in(self):
        response = self.client.get('/2026/opportunity-grants/apply/')
        self.assertEqual(response.status_code, 302)

    def test_apply_shows_closed_when_window_passed(self):
        self.fin.fin_close_date = timezone.now() - timedelta(days=1)
        self.fin.save()
        self.client.login(username='applicant', password='testpass123')
        response = self.client.get('/2026/opportunity-grants/apply/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not open')

    def test_apply_one_application_per_user(self):
        self.client.login(username='applicant', password='testpass123')
        payload = {
            'legal_name': 'Test User',
            'country': 'UG',
            'support_type': 'travel',
            'budget_narrative': 'Estimate',
            'why_need_support': 'Because',
            'community_contribution': 'Volunteering',
            'additional_notes': '',
        }
        r1 = self.client.post('/2026/opportunity-grants/apply/', payload)
        self.assertEqual(r1.status_code, 302)
        self.assertEqual(r1.url, reverse('pycon2026:fin_aid_my_application'))
        self.assertEqual(OpportunityGrantApplication.objects.count(), 1)

        r2 = self.client.get('/2026/opportunity-grants/apply/')
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(r2.url, reverse('pycon2026:fin_aid_my_application'))

        r3 = self.client.get('/2026/opportunity-grants/my-application/')
        self.assertEqual(r3.status_code, 200)
        self.assertContains(r3, 'Test User')
        self.assertContains(r3, 'Edit application')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@example.com',
    )
    def test_apply_sends_submission_confirmation_email(self):
        self.client.login(username='applicant', password='testpass123')
        payload = {
            'legal_name': 'Email User',
            'country': 'UG',
            'support_type': 'travel',
            'budget_narrative': 'Estimate',
            'why_need_support': 'Because',
            'community_contribution': 'Volunteering',
            'additional_notes': '',
        }
        self.client.post('/2026/opportunity-grants/apply/', payload)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['a@example.com'])
        self.assertIn('Opportunity grant', msg.subject)
        self.assertIn('OG 2026', msg.body)
        self.assertIn('/2026/opportunity-grants/my-application/', msg.body)
        html_part = msg.alternatives[0][0]
        self.assertIn('OG 2026', html_part)

    def test_apply_redirects_to_my_application_when_window_closed(self):
        self.client.login(username='applicant', password='testpass123')
        OpportunityGrantApplication.objects.create(
            fin_aid=self.fin,
            user=self.user,
            legal_name='Existing',
            country='UG',
            support_type='ticket',
            budget_narrative='a',
            why_need_support='b',
            community_contribution='c',
        )
        self.fin.fin_close_date = timezone.now() - timedelta(days=1)
        self.fin.save()
        response = self.client.get('/2026/opportunity-grants/apply/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pycon2026:fin_aid_my_application'))


class FinAidReviewerAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.reviewer_user = User.objects.create_user('rev', 'r@example.com', 'testpass123')
        self.applicant = User.objects.create_user('app', 'app@example.com', 'testpass123')
        self.event_year = EventYear.objects.create(year=2026, home_info='test')
        self.fin = Fin_aid.objects.create(
            title='OG 2026',
            event_year=self.event_year,
            fin_open_date=timezone.now() - timedelta(days=1),
            fin_close_date=timezone.now() + timedelta(days=7),
        )
        self.application = OpportunityGrantApplication.objects.create(
            fin_aid=self.fin,
            user=self.applicant,
            legal_name='Applicant',
            country='KE',
            support_type='ticket',
            budget_narrative='x',
            why_need_support='y',
            community_contribution='z',
        )

    def test_reviews_list_requires_reviewer(self):
        self.client.login(username='app', password='testpass123')
        response = self.client.get('/2026/opportunity-grants/reviews/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Access required')

    def test_reviewer_can_open_list(self):
        FinAidReviewer.objects.create(user=self.reviewer_user)
        self.client.login(username='rev', password='testpass123')
        response = self.client.get('/2026/opportunity-grants/reviews/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Applicant')


class OpportunityGrantMyApplicationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('owner', 'o@example.com', 'testpass123')
        self.event_year = EventYear.objects.create(year=2026, home_info='test')
        self.fin = Fin_aid.objects.create(
            title='OG 2026',
            event_year=self.event_year,
            fin_open_date=timezone.now() - timedelta(days=1),
            fin_close_date=timezone.now() + timedelta(days=7),
        )
        self.application = OpportunityGrantApplication.objects.create(
            fin_aid=self.fin,
            user=self.user,
            legal_name='Owner Name',
            country='UG',
            support_type='travel',
            budget_narrative='budget',
            why_need_support='why',
            community_contribution='community',
        )

    def test_my_application_requires_login(self):
        response = self.client.get('/2026/opportunity-grants/my-application/')
        self.assertEqual(response.status_code, 302)

    def test_my_application_redirects_when_no_application(self):
        other = User.objects.create_user('nobody', 'n@example.com', 'testpass123')
        self.client.login(username='nobody', password='testpass123')
        response = self.client.get('/2026/opportunity-grants/my-application/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pycon2026:fin_aid_apply'))

    def test_edit_updates_fields(self):
        self.client.login(username='owner', password='testpass123')
        payload = {
            'legal_name': 'Owner Name',
            'country': 'UG',
            'support_type': 'travel',
            'budget_narrative': 'updated budget',
            'why_need_support': 'why',
            'community_contribution': 'community',
            'additional_notes': '',
        }
        r = self.client.post('/2026/opportunity-grants/my-application/edit/', payload)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse('pycon2026:fin_aid_my_application'))
        self.application.refresh_from_db()
        self.assertEqual(self.application.budget_narrative, 'updated budget')

    def test_edit_blocked_after_deadline(self):
        self.fin.fin_close_date = timezone.now() - timedelta(days=1)
        self.fin.save()
        self.client.login(username='owner', password='testpass123')
        response = self.client.get('/2026/opportunity-grants/my-application/edit/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pycon2026:fin_aid_my_application'))

    def test_edit_blocked_after_reviewer_submits_review(self):
        reviewer = FinAidReviewer.objects.create(
            user=User.objects.create_user('rev2', 'rev2@example.com', 'testpass123'),
        )
        FinAidApplicationReview.objects.create(
            application=self.application,
            reviewer=reviewer,
            recommendation=FinAidApplicationReview.RECOMMEND_UNSURE,
        )
        self.client.login(username='owner', password='testpass123')
        response = self.client.get('/2026/opportunity-grants/my-application/edit/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pycon2026:fin_aid_my_application'))
        detail = self.client.get('/2026/opportunity-grants/my-application/')
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(detail, 'Edit application')
        payload = {
            'legal_name': 'Owner Name',
            'country': 'UG',
            'support_type': 'travel',
            'budget_narrative': 'tampered',
            'why_need_support': 'why',
            'community_contribution': 'community',
            'additional_notes': '',
        }
        post = self.client.post('/2026/opportunity-grants/my-application/edit/', payload)
        self.assertEqual(post.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.budget_narrative, 'budget')

    def test_fin_aid_submitted_application_url_tag(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        tpl = Template(
            '{% load fin_aid_review_urls %}'
            '{% fin_aid_submitted_application_url as u %}{{ u }}'
        )
        out = tpl.render(Context({'request': request, 'year': 2026}))
        self.assertEqual(out, reverse('pycon2026:fin_aid_my_application'))

    def test_fin_aid_submitted_application_url_tag_empty_without_application(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = User.objects.create_user('noapp', 'no@example.com', 'x')
        tpl = Template(
            '{% load fin_aid_review_urls %}'
            '{% fin_aid_submitted_application_url as u %}{{ u }}'
        )
        out = tpl.render(Context({'request': request, 'year': 2026}))
        self.assertEqual(out, '')
