from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override
from datetime import timedelta
from app.leaderboard import compute_leaderboard, export_csv, get_missing_scores, save_leaderboard
from app.models import (
    Application,
    Contest,
    ContestEvaluationPhase,
    JuryScore,
    LeaderboardEntry,
    Round,
    ScoringCriterion,
    Submission,
    Team,
    User,
)



from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
class HomeViewTaskTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username="home_org", password="password", role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username="home_participant", password="password", role=User.Role.PARTICIPANT)
        now = timezone.now()

        self.registration_contest = Contest.objects.create(
            name="Reg Cup",
            description="Registration contest",
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=4),
            organizer=self.organizer,
            is_draft=False,
        )
        self.running_contest = Contest.objects.create(
            name="Run Cup",
            description="Running contest",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=2),
            organizer=self.organizer,
            is_draft=False,
        )
        self.finished_contest = Contest.objects.create(
            name="Done Cup",
            description="Finished contest",
            start_date=now - timedelta(days=5),
            end_date=now - timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        self.draft_contest = Contest.objects.create(
            name="Draft Cup",
            description="Draft contest",
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=6),
            organizer=self.organizer,
            is_draft=True,
        )

    def test_home_shows_all_non_draft_contests(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reg Cup")
        self.assertContains(response, "Run Cup")
        self.assertContains(response, "Done Cup")
        self.assertNotContains(response, "Draft Cup")

    def test_home_status_filter_limits_contests(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"), {"status": Contest.Status.REGISTRATION})

        self.assertContains(response, "Reg Cup")
        self.assertNotContains(response, "Run Cup")
        self.assertNotContains(response, "Done Cup")

    def test_home_invalid_status_filter_falls_back_to_all(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"), {"status": "NOT_A_REAL_STATUS"})

        self.assertContains(response, "Reg Cup")
        self.assertContains(response, "Run Cup")
        self.assertContains(response, "Done Cup")

    def test_home_quick_access_appears_for_participant_with_active_contest(self):
        team = Team.objects.create(name="Rocket", captain=self.participant, status=Team.Status.ACTIVE)
        team.participants.add(self.participant)
        self.running_contest.teams.add(team)
        Round.objects.create(
            contest=self.running_contest,
            title="Speed Round",
            description="Round description",
            tech_requirements="Python",
            must_have=["API"],
            start_time=timezone.now() - timedelta(hours=2),
            deadline=timezone.now() + timedelta(hours=5),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )

        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Your current contest")
        self.assertContains(response, "Rocket")
        self.assertContains(response, "Speed Round")
        self.assertContains(response, "Open Current Round")

    def test_home_quick_access_hidden_when_participant_has_no_team(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))

        self.assertNotContains(response, "Your current contest")


class AuthLanguageSelectorTest(TestCase):
    def test_login_page_has_language_selector(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("set_language")}"')
        self.assertContains(response, 'name="next" type="hidden"')
        self.assertContains(response, 'name="language"')
        self.assertContains(response, 'aria-label="Select language"')
        self.assertContains(response, '<html lang="en"')
        self.assertContains(response, 'English (en)')
        self.assertContains(response, 'value="uk"')

    def test_register_page_has_language_selector(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("set_language")}"')
        self.assertContains(response, 'name="next" type="hidden"')
        self.assertContains(response, 'name="language"')
        self.assertContains(response, 'aria-label="Select language"')
        self.assertContains(response, '<html lang="en"')
        self.assertContains(response, 'English (en)')
        self.assertContains(response, 'value="uk"')


class ProfileViewTaskTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username="profile_org", password="password", role=User.Role.ORGANIZER)
        self.jury = User.objects.create_user(username="profile_jury", password="password", role=User.Role.JURY)
        self.participant = User.objects.create_user(username="profile_participant", password="password", role=User.Role.PARTICIPANT)
        self.member = User.objects.create_user(username="profile_member", password="password", role=User.Role.PARTICIPANT)
        now = timezone.now()

        self.contest = Contest.objects.create(
            name="Profile Contest",
            description="Contest for profile tests",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        self.team = Team.objects.create(name="Winners", captain=self.participant, status=Team.Status.ACTIVE)
        self.team.participants.add(self.participant, self.member)
        self.contest.teams.add(self.team)
        self.contest.jurys.add(self.jury)

        self.criterion = ScoringCriterion.objects.create(
            contest=self.contest,
            name="Backend",
            max_score=100,
            weight=Decimal("1.00"),
            aggregation_type=ScoringCriterion.AggregationType.AVERAGE,
            order=1,
        )

    def test_profile_for_participant_shows_teams_and_leaderboard_history(self):
        LeaderboardEntry.objects.create(
            contest=self.contest,
            team=self.team,
            rank=1,
            total_score=Decimal("95.00"),
            is_tied=False,
            category_scores={"Backend": "95.00"},
        )

        self.client.force_login(self.participant)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Teams")
        self.assertContains(response, "Winners")
        self.assertContains(response, "Captain")
        self.assertContains(response, "Leaderboard History")
        self.assertContains(response, "95.00")

    def test_profile_for_jury_shows_pending_and_completed_reviews(self):
        # Create JuryAssignment first
        from app.models import JuryAssignment
        JuryAssignment.objects.create(contest=self.contest, team=self.team, jury_member=self.jury)
        
        JuryScore.objects.create(
            contest=self.contest,
            team=self.team,
            jury_member=self.jury,
            criterion=self.criterion,
            score=Decimal("88.00"),
        )
        second_team = Team.objects.create(name="Challengers", captain=self.member, status=Team.Status.ACTIVE)
        second_team.participants.add(self.member)
        self.contest.teams.add(second_team)
        # Add JuryAssignment for second_team
        JuryAssignment.objects.create(contest=self.contest, team=second_team, jury_member=self.jury)

        self.client.force_login(self.jury)
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "Pending Reviews")
        self.assertContains(response, "Challengers")
        self.assertContains(response, "Completed Reviews")
        self.assertContains(response, "88.00")

    def test_home_page_pagination_with_many_contests(self):
        """Test home page handles many contests properly"""
        # Create many contests to test pagination/display
        for i in range(20):
            Contest.objects.create(
                name=f'Contest {i}',
                description=f'Description {i}',
                start_date=timezone.now() + timedelta(days=i),
                end_date=timezone.now() + timedelta(days=i+1),
                organizer=self.organizer,
                is_draft=False,
            )
        
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))
        
        self.assertEqual(response.status_code, 200)
        # Should contain some contests but not necessarily all
        self.assertContains(response, "Contest")

    def test_home_page_with_no_contests(self):
        """Test home page when no contests exist"""
        # Delete all contests
        Contest.objects.all().delete()
        
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No contests available")

    def test_contest_detail_draft_contest_hidden_from_participants(self):
        """Test that draft contests are not accessible to participants"""
        draft_contest = Contest.objects.create(
            name='Secret Draft',
            description='Hidden contest',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            is_draft=True,
        )
        
        self.client.force_login(self.participant)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': draft_contest.pk}))
        
        self.assertEqual(response.status_code, 404)

    def test_contest_detail_organizer_can_see_draft(self):
        """Test that organizers can see their own draft contests"""
        draft_contest = Contest.objects.create(
            name='My Draft',
            description='Visible to organizer',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            is_draft=True,
        )
        
        self.client.force_login(self.organizer)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': draft_contest.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Draft')

    def test_contest_detail_hides_public_leaderboard_card_for_organizer(self):
        """Organizers use the admin leaderboard dashboard instead of the public card."""
        self.contest.end_date = timezone.now() - timedelta(minutes=1)
        self.contest.save()

        self.client.force_login(self.organizer)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('admin_leaderboard_dashboard', kwargs={'pk': self.contest.pk}))
        self.assertNotContains(response, reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))

    def test_contest_detail_shows_public_leaderboard_card_for_participant_after_finish(self):
        """Participants still get the public leaderboard card after the contest finishes."""
        self.contest.end_date = timezone.now() - timedelta(minutes=1)
        self.contest.save()

        self.client.force_login(self.participant)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))

    def test_contest_detail_active_round_uses_judge_button_for_jury(self):
        self.contest.jurys.add(self.jury)
        Round.objects.create(
            contest=self.contest,
            title="Active Jury Round",
            description="Round description",
            tech_requirements="Python",
            must_have=["Submit project"],
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=2),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )

        self.client.force_login(self.jury)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Judge")
        self.assertContains(response, reverse('contest_rounds_team', kwargs={'pk': self.contest.pk}))
        self.assertNotContains(response, "View &amp; Submit")

        with override("uk"):
            response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))

        self.assertContains(response, "Оцінити")

    def test_contest_detail_active_round_keeps_submit_button_for_participant(self):
        active_round = Round.objects.create(
            contest=self.contest,
            title="Active Participant Round",
            description="Round description",
            tech_requirements="Python",
            must_have=["Submit project"],
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=2),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )

        self.client.force_login(self.participant)
        response = self.client.get(reverse('contest_detail', kwargs={'pk': self.contest.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View & Submit")
        self.assertContains(
            response,
            reverse('round_detail_team', kwargs={'pk': self.contest.pk, 'round_id': active_round.pk}),
        )

    def test_apply_to_nonexistent_contest_returns_404(self):
        """Test applying to a contest that doesn't exist"""
        self.client.force_login(self.participant)
        response = self.client.post(reverse('apply_to_contest', kwargs={'pk': 99999, 'app_type': 'participant'}))
        
        self.assertEqual(response.status_code, 404)

    def test_apply_as_wrong_role_fails(self):
        """Test that participants cannot apply as jury and vice versa"""
        # Participant trying to apply as jury
        self.client.force_login(self.participant)
        response = self.client.post(reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'jury'}))
        
        self.assertEqual(response.status_code, 403)
        
        # Jury trying to apply as participant
        self.client.force_login(self.jury)
        response = self.client.post(reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'participant'}))
        
        self.assertEqual(response.status_code, 403)

    def test_team_creation_requires_captain(self):
        """Test that team creation fails without a captain"""
        self.client.force_login(self.participant)
        response = self.client.post(reverse('team_create', kwargs={'pk': self.contest.pk}), {
            'name': 'Captainless Team',
            'description': 'This should fail',
        })
        
        # Should fail because captain is required
        self.assertEqual(Team.objects.filter(name='Captainless Team').count(), 0)

    def test_round_creation_requires_organizer_permission(self):
        """Test that only organizers can create rounds"""
        self.client.force_login(self.participant)
        future_start = timezone.now() + timedelta(days=1)
        future_end = timezone.now() + timedelta(days=2)
        
        response = self.client.post(
            reverse('round_create', kwargs={'pk': self.contest.pk}),
            {
                'title': 'Unauthorized Round',
                'description': 'Should not be created',
                'tech_requirements': 'Python',
                'must_have': '["Item 1"]',
                'start_time': future_start.strftime('%Y-%m-%dT%H:%M'),
                'deadline': future_end.strftime('%Y-%m-%dT%H:%M'),
                'materials': '[]'
            }
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Round.objects.filter(title='Unauthorized Round').count(), 0)

    def test_submission_creation_requires_team_membership(self):
        """Test that only team members can create submissions"""
        other_participant = User.objects.create_user(username='other_part', password='password', role=User.Role.PARTICIPANT)
        
        # Create a round first
        round_obj = Round.objects.create(
            contest=self.contest,
            title="Round 1",
            description="Round 1 description",
            tech_requirements="Python",
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=5),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )
        
        self.client.force_login(other_participant)
        response = self.client.post(
            reverse('submission_create', kwargs={'pk': self.contest.pk, 'round_id': round_obj.id}),
            {
                'github_url': 'https://github.com/example/repo',
                'video_url': 'https://youtube.com/watch?v=abc',
                'description': 'Should not work',
            }
        )
        
        self.assertEqual(response.status_code, 403)

    def test_leaderboard_view_before_evaluation_complete(self):
        """Test participants cannot access the leaderboard before the contest finishes."""
        self.client.force_login(self.participant)
        response = self.client.get(reverse('contest_leaderboard', kwargs={'pk': self.contest.pk}))
        
        self.assertEqual(response.status_code, 403)

    def test_profile_view_for_organizer_shows_organized_contests(self):
        """Test that organizers see their organized contests in profile"""
        self.client.force_login(self.organizer)
        response = self.client.get(reverse('profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Contests')
        self.assertContains(response, 'Profile Contest')

    def test_contest_status_filter_edge_cases(self):
        """Test contest status filtering with edge cases"""
        self.client.force_login(self.participant)
        
        # Test with empty status
        response = self.client.get(reverse("home"), {"status": ""})
        self.assertEqual(response.status_code, 200)
        
        # Test with status that has no matches
        finished_contest = Contest.objects.create(
            name='Finished Long Ago',
            description='Old contest',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=5),
            organizer=self.organizer,
            is_draft=False,
        )
        
        response = self.client.get(reverse("home"), {"status": "registration"})
        self.assertNotContains(response, 'Finished Long Ago')

    def test_home_quick_access_with_multiple_active_contests(self):
        """Test quick access when participant has multiple active contests"""
        # Create another contest with the participant
        other_contest = Contest.objects.create(
            name='Second Contest',
            description='Another active contest',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            organizer=self.organizer,
            is_draft=False,
        )
        
        other_team = Team.objects.create(name="Second Team", captain=self.participant, status=Team.Status.ACTIVE)
        other_team.participants.add(self.participant)
        other_contest.teams.add(other_team)
        
        Round.objects.create(
            contest=other_contest,
            title="Second Round",
            description="Another round",
            tech_requirements="Python",
            must_have=["API"],
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=5),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )
        
        self.client.force_login(self.participant)
        response = self.client.get(reverse("home"))
        
        # Should show some quick access, but may prioritize one contest
        self.assertContains(response, "Your current contest")

    def test_invalid_form_data_handling(self):
        """Test that invalid form data is handled gracefully"""
        self.client.force_login(self.organizer)
        
        # Try to create contest with invalid dates
        response = self.client.post(reverse('contest_create'), {
            'name': 'Invalid Contest',
            'description': 'Should fail validation',
            'start_date': '2023-01-01T10:00',
            'end_date': '2023-01-01T09:00',  # End before start
            'is_draft': 'on',
        })
        
        # Should return to form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error')

    def test_permission_denied_redirects_appropriately(self):
        """Test that permission denied responses redirect or show appropriate messages"""
        self.client.force_login(self.participant)
        
        # Try to access organizer-only view
        response = self.client.get(reverse('admin_finish_evaluation', kwargs={'pk': self.contest.pk}))
        
        # Should redirect or show permission denied
        self.assertIn(response.status_code, [302, 403])

    def test_empty_team_profile_view(self):
        """Test profile view for user with no teams"""
        lonely_participant = User.objects.create_user(username='lonely', password='password', role=User.Role.PARTICIPANT)
        
        self.client.force_login(lonely_participant)
        response = self.client.get(reverse('profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Teams')
        # Should show empty or no teams message
        self.assertNotContains(response, 'Captain')  # No captaincy

    def test_profile_for_organizer_shows_managed_contests(self):
        self.client.force_login(self.organizer)
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "My Contests")
        self.assertContains(response, "Profile Contest")
        self.assertContains(response, "Running")

    def test_profile_empty_states_render_for_user_without_related_data(self):
        empty_participant = User.objects.create_user(username="lonely_user", password="password", role=User.Role.PARTICIPANT)

        self.client.force_login(empty_participant)
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "You are not part of any teams yet.")
        self.assertContains(response, "No leaderboard results available yet.")


