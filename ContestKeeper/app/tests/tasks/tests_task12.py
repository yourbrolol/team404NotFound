from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone, translation
from datetime import timedelta
from decimal import Decimal
from app.models import Contest, Round, Team, Submission, User, ScoringCriterion, JuryScore, JuryAssignment

class JuryEvaluationTask12Test(TestCase):
    def setUp(self):
        translation.activate('en')
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.jury = User.objects.create_user(username='jury', password='password', role=User.Role.JURY)
        self.participant = User.objects.create_user(username='part', password='password', role=User.Role.PARTICIPANT)
        
        self.contest = Contest.objects.create(
            name='Evaluation Contest',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=10),
            organizer=self.organizer,
            is_draft=False
        )
        self.contest.jurys.add(self.jury)
        
        self.criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name='Code Quality',
            max_score=100,
            weight=Decimal('0.5'),
            order=1
        )
        
        self.round = Round.objects.create(
            contest=self.contest,
            title='Round 1',
            order=1,
            start_time=timezone.now() - timedelta(hours=2),
            deadline=timezone.now() + timedelta(days=1),
            status=Round.Status.ACTIVE
        )
        
        self.team = Team.objects.create(name='Alpha Team', captain=self.participant)
        self.contest.teams.add(self.team)
        
        # Create JuryAssignment so jury can evaluate
        JuryAssignment.objects.create(contest=self.contest, team=self.team, jury_member=self.jury)
        
        self.submission = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url='https://github.com/alpha',
            video_url='https://vid.com',
            description='Test submission'
        )
        
        self.client = Client()

    def test_jury_can_access_evaluation(self):
        self.client.force_login(self.jury)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': self.team.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Team")

    def test_non_jury_cannot_access_evaluation(self):
        self.client.force_login(self.participant)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': self.team.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_jury_submit_scores(self):
        self.client.force_login(self.jury)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': self.team.pk})
        
        data = {
            f'criterion_{self.criterion.id}': 85
        }
        # We need round_id in query if redirecting back to round_submissions
        response = self.client.post(url + f"?round_id={self.round.id}", data)
        self.assertRedirects(response, reverse('round_submissions', kwargs={'pk': self.contest.pk, 'round_id': self.round.pk}))
        
        score = JuryScore.objects.get(contest=self.contest, team=self.team, jury_member=self.jury, criterion=self.criterion)
        self.assertEqual(score.score, 85)

    def test_score_validation_max_score(self):
        self.client.force_login(self.jury)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': self.team.pk})
        
        data = {
            f'criterion_{self.criterion.id}': 150 # Exceeds max_score=100
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) # Re-renders form
        self.assertTrue(response.context['form'].errors)

    def test_jury_update_score(self):
        JuryScore.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=self.jury,
            criterion=self.criterion,
            score=50
        )
        self.client.force_login(self.jury)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': self.team.pk})
        
        data = {
            f'criterion_{self.criterion.id}': 90
        }
        self.client.post(url, data)
        score = JuryScore.objects.get(criterion=self.criterion)
        self.assertEqual(score.score, 90)
