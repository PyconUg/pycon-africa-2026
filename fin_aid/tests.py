from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.db import IntegrityError, transaction
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
    RegionalGrantApplication,
    RegionalGrantApplicationReview,
    RegionalGrantCountryAssignment,
)


class OpportunityGrantApplyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('applicant', 'a@example.com', 'testpass123')
        self.event_year, _ = EventYear.objects.get_or_create(
            year=2026,
            defaults={'home_info': 'test'},
        )
        self.fin = Fin_aid.objects.create(
            title='OG 2026',
            event_year=self.event_year,
            fin_open_date=timezone.now() - timedelta(days=1),
            fin_close_date=timezone.now() + timedelta(days=7),
        )

    def test_public_page_shows_guidelines_and_closed_banner_after_deadline(self):
        self.fin.fin_close_date = timezone.now() - timedelta(days=1)
        self.fin.save()
        response = self.client.get('/2026/opportunity-grants/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Applications closed')
        self.assertContains(response, 'PyCon Africa 2026 Opportunity Grants Programme')
        self.assertNotContains(
            response,
            'Opportunity grant information will be available soon',
        )

    def test_form_status_message_uses_local_timezone_not_utc(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        eat = ZoneInfo('Africa/Kampala')
        close_at = datetime(2026, 6, 1, 23, 0, tzinfo=eat)
        self.assertEqual(
            self.fin.format_window_datetime(close_at),
            '1 June 2026, 23:00 (EAT)',
        )
        self.fin.fin_close_date = timezone.now() - timedelta(hours=1)
        self.fin.save()
        msg = self.fin.get_form_status_message()
        self.assertIn('(EAT)', msg)
        self.assertNotIn('2026-06-01 20:00:00', msg)

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
        self.event_year, _ = EventYear.objects.get_or_create(
            year=2026,
            defaults={'home_info': 'test'},
        )
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
        self.event_year, _ = EventYear.objects.get_or_create(
            year=2026,
            defaults={'home_info': 'test'},
        )
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


def _make_regional_application(country, email, **overrides):
    from datetime import date

    fields = {
        'country': country,
        'full_name': 'Test Applicant',
        'email': email,
        'phone': '+256700000000',
        'city': 'Kampala',
        'gender': 'female',
        'dob': date(1995, 1, 1),
        'is_18': True,
        'status': 'student',
        'field': 'Computer Science',
        'python_level': 'intermediate',
        'python_duration': '1_2y',
        'why_attend': 'To learn and connect.',
        'hope_to_gain': 'New skills.',
        'interests': 'ai_ml',
        'attend_all': True,
        'represent_professionally': True,
        'share_publicly': True,
        'can_cover_expenses_with_ticket': 'yes',
        'can_attend_with_travel_support': 'yes',
        'financial_support': 'travel',
    }
    fields.update(overrides)
    return RegionalGrantApplication.objects.create(**fields)


class RegionalGrantReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Deliberately NOT a FinAidReviewer — regional grant reviewers can be any user account.
        self.reviewer = User.objects.create_user('regreviewer', 'rr@example.com', 'testpass123')
        RegionalGrantCountryAssignment.objects.create(reviewer=self.reviewer, country='kenya')

        self.kenya_app = _make_regional_application('kenya', 'kenya-applicant@example.com')
        self.rwanda_app = _make_regional_application('rwanda', 'rwanda-applicant@example.com')

        self.client.login(username='regreviewer', password='testpass123')

    def test_any_user_can_be_assigned_as_reviewer_without_fin_aid_reviewer_profile(self):
        self.assertFalse(FinAidReviewer.objects.filter(user=self.reviewer).exists())
        self.assertTrue(
            RegionalGrantCountryAssignment.objects.filter(reviewer=self.reviewer, country='kenya').exists()
        )

    def test_reviewer_only_sees_assigned_country_applications(self):
        response = self.client.get(reverse('pycon2026:regional_grant_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.kenya_app.full_name)
        applications_shown = list(response.context['unreviewed_applications'])
        self.assertIn(self.kenya_app, applications_shown)
        self.assertNotIn(self.rwanda_app, applications_shown)

    def test_user_without_country_assignment_sees_empty_state(self):
        User.objects.create_user('noassign', 'noassign@example.com', 'testpass123')
        self.client.login(username='noassign', password='testpass123')
        response = self.client.get(reverse('pycon2026:regional_grant_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['no_countries_assigned'])

    def test_reviewer_blocked_from_unassigned_country_application(self):
        response = self.client.get(
            reverse('pycon2026:regional_grant_review_detail', kwargs={'pk': self.rwanda_app.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            RegionalGrantApplicationReview.objects.filter(
                application=self.rwanda_app, reviewer=self.reviewer
            ).exists()
        )

    def test_submit_review_persists_weighted_total_score(self):
        payload = {
            'is_community_member': 'on',
            'is_active_contributor': 'on',
            'is_knowledge_sharer': '',
            'python_level': 'advanced',
            'python_duration': '2y_plus',
            'financial_need': 'travel',
            'is_woman': 'on',
            'has_disability': '',
            'is_student': 'on',
            'alignment_score': '4',
            'recommendation': 'accept',
            'comments': 'Strong applicant',
        }
        response = self.client.post(
            reverse('pycon2026:regional_grant_review_detail', kwargs={'pk': self.kenya_app.pk}),
            payload,
        )
        self.assertEqual(response.status_code, 302)
        review = RegionalGrantApplicationReview.objects.get(
            application=self.kenya_app, reviewer=self.reviewer
        )
        # community (1+1+0)*3=6, python (2+3)*2=10, financial 3*3=9, diversity (1+0+1)*5=10, alignment 4
        self.assertEqual(review.total_score, 6 + 10 + 9 + 10 + 4)
        self.assertEqual(review.recommendation, 'accept')

    def test_duplicate_review_by_same_reviewer_is_rejected_at_db_level(self):
        RegionalGrantApplicationReview.objects.create(application=self.kenya_app, reviewer=self.reviewer)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RegionalGrantApplicationReview.objects.create(
                    application=self.kenya_app, reviewer=self.reviewer
                )


class RegionalGrantReviewerNotificationTests(TestCase):
    def setUp(self):
        self.reviewer = User.objects.create_user('notifyme', 'notifyme@example.com', 'testpass123')
        RegionalGrantCountryAssignment.objects.create(reviewer=self.reviewer, country='kenya')
        RegionalGrantCountryAssignment.objects.create(reviewer=self.reviewer, country='rwanda')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@example.com',
    )
    def test_send_regional_grant_reviewer_assignment_email(self):
        from .email_notifications import send_regional_grant_reviewer_assignment_email

        sent = send_regional_grant_reviewer_assignment_email(self.reviewer, ['Kenya', 'Rwanda'])
        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['notifyme@example.com'])
        self.assertIn('Kenya', msg.body)
        self.assertIn('Rwanda', msg.body)
        self.assertIn(reverse('pycon2026:regional_grant_reviews'), msg.body)
        html_part = msg.alternatives[0][0]
        self.assertIn('Kenya', html_part)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@example.com',
    )
    def test_admin_action_emails_selected_reviewers(self):
        staff = User.objects.create_superuser('admin_notify', 'admin_notify@example.com', 'testpass123')
        client = Client()
        client.login(username='admin_notify', password='testpass123')

        assignment = RegionalGrantCountryAssignment.objects.filter(reviewer=self.reviewer).first()
        response = client.post(
            reverse('admin:fin_aid_regionalgrantcountryassignment_changelist'),
            {
                'action': 'notify_reviewers_action',
                '_selected_action': [str(assignment.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['notifyme@example.com'])
        self.assertIn('Kenya', msg.body)
        self.assertIn('Rwanda', msg.body)

