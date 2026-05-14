from app.tests.base import BaseSecureTestCase
from django.test import Client
from django.urls import reverse
from app.models import Contest, ScoringCriterion, User

class ScoringCriteriaTask08Test(BaseSecureTestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.other_user = User.objects.create_user(username='other', password='password', role=User.Role.PARTICIPANT)
        
        from django.utils import timezone
        self.contest = Contest.objects.create(
            name='Scoring Test Contest',
            description='Testing criteria CRUD',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            organizer=self.organizer,
            is_draft=False
        )
        # self.client = self.client_class()  # Removed redundant insecure client

    def test_criterion_create_organizer(self):
        self.client.force_login(self.organizer)
        url = reverse('criterion_create', kwargs={'pk': self.contest.pk})
        response = self.client.post(url, {
            'name': 'Innovation',
            'max_score': 10,
            'weight': 1.5,
            'aggregation_type': ScoringCriterion.AggregationType.AVERAGE,
            'order': 1
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ScoringCriterion.objects.filter(name='Innovation', contest=self.contest).exists())

    def test_criterion_update_organizer(self):
        criterion = ScoringCriterion.objects.create(
            contest=self.contest, name='Design', max_score=10, weight=1.0, order=1
        )
        self.client.force_login(self.organizer)
        url = reverse('criterion_edit', kwargs={'pk': self.contest.pk, 'criterion_id': criterion.pk})
        response = self.client.post(url, {
            'name': 'Great Design',
            'max_score': 10,
            'weight': 2.0,
            'aggregation_type': ScoringCriterion.AggregationType.AVERAGE,
            'order': 1
        })
        self.assertEqual(response.status_code, 302)
        criterion.refresh_from_db()
        self.assertEqual(criterion.name, 'Great Design')
        self.assertEqual(criterion.weight, 2.0)

    def test_criterion_delete_organizer(self):
        criterion = ScoringCriterion.objects.create(
            contest=self.contest, name='To Delete', max_score=10, weight=1.0, order=1
        )
        self.client.force_login(self.organizer)
        url = reverse('criterion_delete', kwargs={'pk': self.contest.pk, 'criterion_id': criterion.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ScoringCriterion.objects.filter(pk=criterion.pk).exists())

    def test_criterion_add_link_present_on_dashboard(self):
        self.client.force_login(self.organizer)
        url = reverse('admin_leaderboard_dashboard', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('criterion_create', kwargs={'pk': self.contest.pk}))

    def test_finish_evaluation_requires_browser_confirmation(self):
        self.client.force_login(self.organizer)
        url = reverse('admin_leaderboard_dashboard', kwargs={'pk': self.contest.pk})
        finish_url = reverse('admin_finish_evaluation', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{finish_url}"')
        self.assertContains(
            response,
            'data-confirm-message="Are you sure you want to finish evaluation? This action cannot be undone."',
        )
        self.assertContains(response, "onsubmit=\"return confirm(this.getAttribute('data-confirm-message'));\"")

    def test_criterion_access_denied_role(self):
        self.client.force_login(self.other_user)
        url = reverse('criterion_create', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)
        # In this project, unauthorized access might return 403 or 404 depending on mixin logic
        self.assertIn(response.status_code, [403, 404])
