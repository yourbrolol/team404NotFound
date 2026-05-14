from django.core.management import call_command
from app.tests.base import BaseSecureTestCase
from django.contrib.auth import get_user_model
from app.models import Contest, Team, Round, Submission, JuryAssignment, JuryScore, ScoringCriterion

User = get_user_model()

class SeedDataTest(BaseSecureTestCase):
    def test_seed_data_command(self):
        """Test that seed_data command populates the database correctly."""
        # Run the command
        call_command('seed_data', clear=True)

        # Verify Users
        self.assertTrue(User.objects.filter(username="organizer").exists())
        self.assertTrue(User.objects.filter(username="jury_1").exists())
        self.assertTrue(User.objects.filter(username="captain_1").exists())

        # Verify Contest
        contest = Contest.objects.get(name="AI Innovation Hackathon 2026")
        self.assertEqual(contest.organizer.username, "organizer")

        # Verify Teams
        self.assertEqual(contest.teams.count(), 3)
        self.assertTrue(Team.objects.filter(name="Alpha Force 1").exists())

        # Verify Rounds
        self.assertEqual(contest.rounds.count(), 1)
        self.assertEqual(contest.rounds.first().title, "Prototype Development")

        # Verify Submissions
        self.assertEqual(Submission.objects.count(), 3)

        # Verify Scoring Criteria
        self.assertEqual(ScoringCriterion.objects.filter(contest=contest).count(), 3)

        # Verify Jury Assignments
        self.assertEqual(JuryAssignment.objects.filter(contest=contest).count(), 6) # 3 teams * 2 juries

        # Verify Scores
        self.assertEqual(JuryScore.objects.count(), 18) # 6 assignments * 3 criteria
