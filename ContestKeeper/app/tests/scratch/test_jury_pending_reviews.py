from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.models import (
    Contest,
    JuryAssignment,
    JuryScore,
    Round,
    ScoringCriterion,
    Submission,
    Team,
    User,
)

class JuryPendingReviewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username="org", password="password", role=User.Role.ORGANIZER)
        self.jury = User.objects.create_user(username="jury", password="password", role=User.Role.JURY)
        self.participant = User.objects.create_user(username="part", password="password", role=User.Role.PARTICIPANT)
        now = timezone.now()

        # Create a contest
        self.contest = Contest.objects.create(
            name="Test Contest",
            description="Test Description",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        # Add jury to the contest
        self.contest.jurys.add(self.jury)

        # Create a team and add it to the contest
        self.team = Team.objects.create(name="Team A", status=Team.Status.ACTIVE)
        self.team.participants.add(self.participant)
        self.contest.teams.add(self.team)

        # Create a round and a submission
        self.round = Round.objects.create(
            contest=self.contest,
            title="Round 1",
            description="Round 1",
            tech_requirements="None",
            start_time=now - timedelta(hours=2),
            deadline=now + timedelta(hours=2),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer
        )
        self.submission = Submission.objects.create(
            round=self.round,
            team=self.team,
            github_url="https://github.com/test/test",
            video_url="https://youtube.com/test",
        )

        # Create a scoring criterion
        self.criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Utility",
            max_score=10,
            weight=Decimal("1.0"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=1
        )

    def test_pending_reviews_not_shown_if_jury_not_in_contest_jurys(self):
        """Test that pending reviews are NOT shown if the jury member is NOT in the contest.jurys M2M field, even if they have assignments."""
        # Create another jury member NOT in the contest
        outsider_jury = User.objects.create_user(username="outsider", password="password", role=User.Role.JURY)
        
        # Create JuryAssignment for the outsider
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=outsider_jury
        )

        self.client.force_login(outsider_jury)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        # It should NOT contain "Team A" because the contest is not in outsider_jury.judged_contests
        self.assertNotContains(response, "Team A")
        self.assertContains(response, "You have no pending reviews right now.")

    def test_pending_reviews_with_assignment(self):
        """Test that pending reviews show up when a JuryAssignment exists."""
        # Create JuryAssignment
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=self.jury
        )

        self.client.force_login(self.jury)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        # Check if the team name is in the response (it should be in Pending Reviews)
        self.assertContains(response, "Team A")
        # Check if "Pending Reviews" section is present
        self.assertContains(response, "Pending Reviews")

    def test_pending_reviews_without_assignment_but_with_submissions(self):
        """Test that pending reviews show up when no JuryAssignment exists but teams have submissions."""
        # Ensure no assignments exist for this contest
        JuryAssignment.objects.filter(contest=self.contest).delete()

        self.client.force_login(self.jury)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Team A")
        self.assertContains(response, "Pending Reviews")

    def test_pending_reviews_empty_when_other_jury_has_assignments(self):
        """Test that pending reviews are empty for a jury member if OTHER jury members have assignments but they don't."""
        other_jury = User.objects.create_user(username="other_jury", password="password", role=User.Role.JURY)
        self.contest.jurys.add(other_jury)
        
        # Assign Team A to other_jury
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=other_jury
        )
        
        # Now self.jury has NO assignments, but the contest HAS assignments
        self.client.force_login(self.jury)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        # Team A should NOT be in pending reviews for self.jury
        self.assertNotContains(response, "Team A")

    def test_pending_reviews_empty_when_no_criteria(self):
        """Test that pending reviews are empty if the contest has no scoring criteria."""
        # Delete all criteria for the contest
        ScoringCriterion.objects.filter(contest=self.contest).delete()
        
        # Ensure assignment exists
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=self.jury
        )

        self.client.force_login(self.jury)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        # Should NOT contain Team A because there's nothing to rate
        self.assertNotContains(response, "Team A")
        self.assertContains(response, "You have no pending reviews right now.")

    def test_pending_reviews_for_superuser_without_jury_role(self):
        """Test that pending reviews are empty for a superuser if they don't have the JURY role, even if assigned."""
        admin = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        # Ensure role is NOT Jury (default is PARTICIPANT)
        admin.role = User.Role.PARTICIPANT
        admin.save()
        
        self.contest.jurys.add(admin)
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=admin
        )

        self.client.force_login(admin)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        # It should NOT show jury section at all, because they are PARTICIPANT
        self.assertNotContains(response, "Pending Reviews")

    def test_pending_reviews_for_organizer_who_is_also_jury(self):
        """Test that an organizer who is also a jury member DOES NOT see pending reviews (potential bug)."""
        # User role is ORGANIZER
        # They are in contest.jurys
        self.contest.jurys.add(self.organizer)
        JuryAssignment.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=self.organizer
        )

        self.client.force_login(self.organizer)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        # It currently SHOWS "My Contests" but NOT "Pending Reviews" because of elif chain
        self.assertContains(response, "My Contests")
        self.assertNotContains(response, "Pending Reviews")
