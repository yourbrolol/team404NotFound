from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone, translation
from datetime import timedelta
from app.models import Contest, Round, Team, Submission, User

class SubmissionTask11Test(TestCase):
    def setUp(self):
        translation.activate('en')
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.captain = User.objects.create_user(username='captain', password='password', role=User.Role.PARTICIPANT)
        self.other_user = User.objects.create_user(username='other', password='password', role=User.Role.PARTICIPANT)
        
        self.contest = Contest.objects.create(
            name='Test Contest',
            description='Test Submission UI',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=10),
            organizer=self.organizer,
            is_draft=False
        )
        
        self.round = Round.objects.create(
            contest=self.contest,
            title='Round 1',
            order=1,
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(days=1),
            status=Round.Status.ACTIVE
        )
        
        self.team = Team.objects.create(name='Test Team', captain=self.captain)
        self.team.participants.add(self.captain)
        self.contest.teams.add(self.team)
        self.contest.participants.add(self.captain)
        
        self.client = Client()

    def test_submission_create_flow(self):
        self.client.force_login(self.captain)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        
        # GET form
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST submission
        data = {
            'github_url': 'https://github.com/test/repo',
            'video_url': 'https://youtube.com/watch?v=123',
            'description': 'This is our project.'
        }
        res_post = self.client.post(url, data)
        self.assertRedirects(res_post, reverse('round_detail', kwargs={'pk': self.contest.pk, 'round_pk': self.round.pk}))
        
        self.assertTrue(Submission.objects.filter(team=self.team, round=self.round).exists())

    def test_submission_edit_flow(self):
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://old.com',
            video_url='https://old-video.com',
            description='Old desc'
        )
        self.client.force_login(self.captain)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        
        data = {
            'github_url': 'https://new.com',
            'video_url': 'https://youtube.com/new',
            'description': 'New desc'
        }
        self.client.post(url, data)
        sub.refresh_from_db()
        self.assertEqual(sub.github_url, 'https://new.com')

    def test_non_team_member_cannot_submit(self):
        self.client.force_login(self.other_user)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404) # View returns 404 if not in team

    def test_late_submission_is_forbidden(self):
        # Set deadline to past
        self.round.deadline = timezone.now() - timedelta(hours=1)
        self.round.save()
        
        self.client.force_login(self.captain)
        url = reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk})
        
        response = self.client.post(url, {'github_url': 'https://test.com', 'video_url': 'https://y.com', 'description': 'desc'})
        self.assertEqual(response.status_code, 403) # Forbidden

    def test_submission_detail_access(self):
        sub = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://git.com',
            video_url='https://vid.com',
            description='desc'
        )
        url = reverse('submission_detail', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk, 'sub_pk': sub.pk})
        
        # Member can see
        self.client.force_login(self.captain)
        self.assertEqual(self.client.get(url).status_code, 200)
        
        # Non-member cannot see
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(url).status_code, 404)
        
        # Organizer can see
        self.client.force_login(self.organizer)
        self.assertEqual(self.client.get(url).status_code, 200)
