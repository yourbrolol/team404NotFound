from datetime import timedelta

from app.tests.base import BaseSecureTestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Contest, Round, Team, User


class RoundDetailTemplateTest(BaseSecureTestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="round_template_org",
            password="password",
            role=User.Role.ORGANIZER,
        )
        self.participant = User.objects.create_user(
            username="round_template_participant",
            password="password",
            role=User.Role.PARTICIPANT,
        )
        self.contest = Contest.objects.create(
            name="Round Template Contest",
            description="Contest for round template tests",
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            is_draft=False,
        )
        self.team = Team.objects.create(
            name="Round Template Team",
            captain=self.participant,
            status=Team.Status.ACTIVE,
        )
        self.team.participants.add(self.participant)
        self.contest.teams.add(self.team)
        self.round = Round.objects.create(
            contest=self.contest,
            title="Shared Detail Round",
            description="Round description",
            tech_requirements="Python",
            must_have=["Submit project"],
            materials=[],
            start_time=timezone.now() - timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=2),
            status=Round.Status.ACTIVE,
            order=1,
            created_by=self.organizer,
        )

    def test_team_round_detail_uses_shared_round_detail_template(self):
        self.client.force_login(self.participant)

        response = self.client.get(
            reverse(
                "round_detail_team",
                kwargs={"pk": self.contest.pk, "round_id": self.round.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/rounds/round_detail.html")
        self.assertTemplateNotUsed(response, "app/rounds/round_detail_team.html")
