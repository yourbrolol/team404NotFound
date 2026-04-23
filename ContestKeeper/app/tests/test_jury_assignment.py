from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.models import Contest, Team, User, JuryAssignment, Round, Submission
from app.services import assign_jury_to_teams

class JuryAssignmentTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.jury1 = User.objects.create_user(username='jury1', password='password', role=User.Role.JURY)
        self.jury2 = User.objects.create_user(username='jury2', password='password', role=User.Role.JURY)
        self.jury3 = User.objects.create_user(username='jury3', password='password', role=User.Role.JURY)
        
        self.contest = Contest.objects.create(
            name='Test Contest',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=5),
            organizer=self.organizer,
            is_draft=False
        )
        self.contest.jurys.add(self.jury1, self.jury2, self.jury3)
        
        for i in range(5):
            team = Team.objects.create(name=f'Team {i}', status=Team.Status.ACTIVE)
            self.contest.teams.add(team)
            
        self.client = Client()

    def test_assign_jury_to_teams_logic(self):
        num_assignments = assign_jury_to_teams(self.contest, min_reviews_per_team=2)
        
        # 5 teams * 2 reviews = 10 assignments
        self.assertEqual(num_assignments, 10)
        self.assertEqual(JuryAssignment.objects.filter(contest=self.contest).count(), 10)
        
        for team in self.contest.teams.all():
            self.assertEqual(JuryAssignment.objects.filter(contest=self.contest, team=team).count(), 2)
            
        # Check that jury members have roughly even load
        # 10 assignments / 3 juries = 3 or 4 per jury
        for jury in [self.jury1, self.jury2, self.jury3]:
            count = JuryAssignment.objects.filter(contest=self.contest, jury_member=jury).count()
            self.assertIn(count, [3, 4])

    def test_assign_jury_view(self):
        self.client.force_login(self.organizer)
        url = reverse('assign_jury', kwargs={'pk': self.contest.pk})
        response = self.client.post(url, {'min_reviews': 1})
        self.assertRedirects(response, reverse('contest_jurys', kwargs={'pk': self.contest.pk}))
        
        # 5 teams * 1 review = 5 assignments
        self.assertEqual(JuryAssignment.objects.filter(contest=self.contest).count(), 5)

    def test_jury_evaluation_access_denied_without_assignment(self):
        # Assign jury1 to some teams, but NOT Team 0
        team0 = self.contest.teams.get(name='Team 0')
        team1 = self.contest.teams.get(name='Team 1')
        JuryAssignment.objects.create(contest=self.contest, team=team1, jury_member=self.jury1)
        
        self.client.force_login(self.jury1)
        
        # Try to evaluate Team 0 (not assigned)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': team0.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Try to evaluate Team 1 (assigned)
        url = reverse('jury_evaluate', kwargs={'pk': self.contest.pk, 'team_pk': team1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_round_submissions_list_filtering(self):
        # Assign jury1 to Team 0 and Team 1 only
        team0 = self.contest.teams.get(name='Team 0')
        team1 = self.contest.teams.get(name='Team 1')
        team2 = self.contest.teams.get(name='Team 2')
        JuryAssignment.objects.create(contest=self.contest, team=team0, jury_member=self.jury1)
        JuryAssignment.objects.create(contest=self.contest, team=team1, jury_member=self.jury1)
        
        # Create a round and submissions
        rnd = Round.objects.create(
            contest=self.contest, title='R1', start_time=timezone.now(), 
            deadline=timezone.now()+timedelta(hours=1), order=1
        )
        Submission.objects.create(round=rnd, team=team0, github_url='http://h.com', video_url='http://v.com')
        Submission.objects.create(round=rnd, team=team1, github_url='http://h.com', video_url='http://v.com')
        Submission.objects.create(round=rnd, team=team2, github_url='http://h.com', video_url='http://v.com')
        
        self.client.force_login(self.jury1)
        url = reverse('round_submissions', kwargs={'pk': self.contest.pk, 'round_id': rnd.pk})
        response = self.client.get(url)
        
        self.assertEqual(len(response.context['submissions']), 2)
        team_names = [s.team.name for s in response.context['submissions']]
        self.assertIn('Team 0', team_names)
        self.assertIn('Team 1', team_names)
        self.assertNotIn('Team 2', team_names)
