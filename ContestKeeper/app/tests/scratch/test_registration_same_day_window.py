from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from app.models import Contest, Team, User


class SameDayRegistrationWindowTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username='organizer_same_day',
            email='organizer_same_day@test.com',
            password='password123',
            role=User.Role.ORGANIZER,
        )
        self.participant = User.objects.create_user(
            username='participant_same_day',
            email='participant_same_day@test.com',
            password='password123',
            role=User.Role.PARTICIPANT,
        )
        now = timezone.now()
        self.contest = Contest.objects.create(
            name='Same Day Registration Contest',
            description='Contest with registration window inside a single calendar day.',
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=5),
            registration_start=now - timedelta(minutes=2),
            registration_end=now + timedelta(minutes=2),
            organizer=self.organizer,
            is_draft=False,
        )
        self.client = Client()

    def test_same_day_registration_window_is_open(self):
        self.assertTrue(self.contest.is_registration_open)

    def test_team_creation_allowed_during_same_day_registration_window(self):
        self.client.force_login(self.participant)
        url = reverse('team_create', kwargs={'pk': self.contest.pk})
        response = self.client.post(url, {'name': 'Team Same Day'})

        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(
            Team.objects.filter(name='Team Same Day', captain=self.participant).exists()
        )

    def test_contest_detail_shows_future_registration_opens(self):
        self.contest.registration_start = timezone.now() + timedelta(minutes=30)
        self.contest.registration_end = timezone.now() + timedelta(hours=1)
        self.contest.save()

        self.client.force_login(self.participant)
        url = reverse('contest_detail', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Opens on', response.content.decode())
