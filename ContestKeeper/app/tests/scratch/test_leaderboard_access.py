from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from app.models import Contest, User, Team
from datetime import timedelta

class LeaderboardAccessTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username='parti', password='password', role=User.Role.PARTICIPANT)
        
        self.contest = Contest.objects.create(
            name='Test Contest',
            description='Test Description',
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1), # Running
            organizer=self.organizer,
            is_draft=False
        )
        # Ensure status is updated (it updates on save)
        self.contest.save()
        
        self.client = Client()

    def test_leaderboard_url_access_before_finished(self):
        """Leaderboard URL should NOT be accessible before the contest is finished."""
        # Test for participant
        self.client.force_login(self.participant)
        response = self.client.get(reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))
        # User says "it cannot be accessed... neither through URL (/leaderboard)"
        # We should decide what status code to return. 403 or 404.
        # Given "cannot be accessed", 404 or 403 is fine. I'll check for 403 (Forbidden) or 404 (Not Found).
        # Let's assume 403 for now as it's a permission issue, or redirect to detail with error.
        # But "cannot be accessed" usually means you can't see the content.
        self.assertIn(response.status_code, [403, 404])

    def test_leaderboard_card_not_shown_before_finished(self):
        """Leaderboard card should NOT be in contest_detail before the contest is finished."""
        self.client.force_login(self.participant)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        # Check that the leaderboard link is NOT present
        # We'll use a specific ID or text to check.
        # I'll look for the text "Leaderboard" or the URL.
        self.assertNotContains(response, reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))

    def test_leaderboard_access_after_finished(self):
        """Leaderboard should be accessible and visible after the contest is finished."""
        # Finish the contest
        self.contest.end_date = timezone.now() - timedelta(minutes=1)
        self.contest.save()
        self.assertEqual(self.contest.status, Contest.Status.FINISHED)
        
        self.client.force_login(self.participant)
        
        # Check URL access
        response = self.client.get(reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Check card visibility
        response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))
