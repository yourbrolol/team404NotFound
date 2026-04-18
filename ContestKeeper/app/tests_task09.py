from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.models import Contest, Round, Team, User

class RoundTask09Test(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username='parti', password='password', role=User.Role.PARTICIPANT)
        self.jury = User.objects.create_user(username='jury', password='password', role=User.Role.JURY)
        self.other_user = User.objects.create_user(username='other', password='password', role=User.Role.PARTICIPANT)
        
        self.contest = Contest.objects.create(
            name='Task 09 Test Contest',
            description='Testing detailed view',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            is_draft=False
        )
        self.contest.participants.add(self.participant)
        self.contest.jurys.add(self.jury)
        
        self.team = Team.objects.create(name='Team A')
        self.team.participants.add(self.participant)
        self.contest.teams.add(self.team)
        
        self.round = Round.objects.create(
            contest=self.contest,
            title='Round 1',
            description='Test Round',
            tech_requirements='None',
            must_have=['Item 1'],
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=2),
            status=Round.Status.ACTIVE,
            order=1
        )
        self.client = Client()

    def test_round_detail_access_organizer(self):
        self.client.force_login(self.organizer)
        url = reverse('round_detail', kwargs={'pk': self.contest.pk, 'round_pk': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_organizer'])
        self.assertContains(response, 'Management')

    def test_round_detail_access_participant(self):
        self.client.force_login(self.participant)
        url = reverse('round_detail', kwargs={'pk': self.contest.pk, 'round_pk': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_organizer'])
        self.assertTrue(response.context['is_active'])
        self.assertContains(response, 'Submission')

    def test_round_detail_access_jury(self):
        self.client.force_login(self.jury)
        url = reverse('round_detail', kwargs={'pk': self.contest.pk, 'round_pk': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_jury'])

    def test_round_detail_access_denied_other(self):
        self.client.force_login(self.other_user)
        url = reverse('round_detail', kwargs={'pk': self.contest.pk, 'round_pk': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_round_extend_deadline_get(self):
        self.client.force_login(self.organizer)
        url = reverse('round_extend_deadline', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/round_extend_deadline.html')
