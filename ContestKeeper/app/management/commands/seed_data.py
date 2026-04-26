import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from app.models import (
    Contest, Team, ScoringCriterion, JuryAssignment, JuryScore, 
    Round, Submission, Application, Announcement, ScheduleEvent,
    ContestEvaluationPhase, Notification
)

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with demo data for all roles and features."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing data...")
            User.objects.filter(is_superuser=False).delete()
            Contest.objects.all().delete()
            Team.objects.all().delete()
            # Cascade deletes should handle the rest

        self.stdout.write("Seeding data...")

        try:
            with transaction.atomic():
                self.seed_everything()
            self.stdout.write(self.style.SUCCESS("Successfully seeded database with demo data!"))
            self.stdout.write("\nCredentials:")
            self.stdout.write("  Organizer: organizer / password123")
            self.stdout.write("  Jury 1: jury_1 / password123")
            self.stdout.write("  Jury 2: jury_2 / password123")
            self.stdout.write("  Captain 1: captain_1 / password123")
            self.stdout.write("  Captain 2: captain_2 / password123")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding data: {e}"))
            import traceback
            traceback.print_exc()

    def seed_everything(self):
        # 1. Create Users
        password = "password123"
        
        organizer = User.objects.create_user(
            username="organizer", 
            email="organizer@demo.com", 
            password=password,
            role=User.Role.ORGANIZER,
            first_name="Oleh",
            last_name="Organizerov"
        )
        
        juries = [
            User.objects.create_user(
                username=f"jury_{i}", 
                email=f"jury_{i}@demo.com", 
                password=password,
                role=User.Role.JURY,
                first_name=f"Jury_{i}",
                last_name="Judge"
            ) for i in range(1, 3)
        ]
        
        participants = [
            User.objects.create_user(
                username=f"captain_{i}", 
                email=f"captain_{i}@demo.com", 
                password=password,
                role=User.Role.PARTICIPANT,
                first_name=f"Captain_{i}",
                last_name="Team"
            ) for i in range(1, 4)
        ]
        
        members = [
            User.objects.create_user(
                username=f"member_{i}", 
                email=f"member_{i}@demo.com", 
                password=password,
                role=User.Role.PARTICIPANT,
                first_name=f"Member_{i}",
                last_name="Team"
            ) for i in range(1, 4)
        ]

        # 2. Create Contest
        now = timezone.now()
        contest = Contest.objects.create(
            name="AI Innovation Hackathon 2026",
            description="A prestigious hackathon focusing on Generative AI and Agentic Workflows.",
            registration_start=now - timedelta(days=5),
            registration_end=now + timedelta(days=2),
            start_date=now + timedelta(days=3),
            end_date=now + timedelta(days=10),
            max_teams=10,
            format="Hybrid",
            organizer=organizer,
            is_draft=False
        )
        contest.jurys.add(*juries)

        # 3. Create Teams
        teams = []
        for i in range(3):
            team = Team.objects.create(
                name=f"Alpha Force {i+1}",
                description=f"A highly skilled team focused on solving complex AI problems.",
                captain=participants[i],
                organization="Tech University",
                telegram_link="https://t.me/demo_team",
                status=Team.Status.ACTIVE
            )
            team.participants.add(participants[i], members[i])
            contest.teams.add(team)
            teams.append(team)
            
            # Create approved application
            Application.objects.create(
                user=participants[i],
                contest=contest,
                team=team,
                application_type=Application.Type.TEAM,
                status=Application.Status.APPROVED
            )

        # 4. Create Rounds
        round1 = Round.objects.create(
            contest=contest,
            title="Prototype Development",
            description="Create a working prototype of your AI agent.",
            tech_requirements="Python 3.12+, OpenAI API or Local LLM.",
            must_have=["Working API", "Readme file", "Basic UI"],
            start_time=now - timedelta(days=1),
            deadline=now + timedelta(days=5),
            materials=[{"label": "API Docs", "url": "https://example.com/docs"}],
            status=Round.Status.ACTIVE,
            order=1,
            created_by=organizer
        )

        # 5. Create Submissions
        for team in teams:
            Submission.objects.create(
                round=round1,
                team=team,
                github_url=f"https://github.com/demo/{team.name.replace(' ', '-')}",
                video_url="https://youtube.com/watch?v=demo",
                description=f"This is our submission for the Prototype round. We implemented a multi-agent system."
            )

        # 6. Scoring Criteria
        criteria = [
            ScoringCriterion.objects.create(contest=contest, name="Innovation", max_score=10, weight=Decimal("1.5"), order=1),
            ScoringCriterion.objects.create(contest=contest, name="Technical Depth", max_score=10, weight=Decimal("1.0"), order=2),
            ScoringCriterion.objects.create(contest=contest, name="User Experience", max_score=10, weight=Decimal("0.5"), order=3),
        ]

        # 7. Jury Assignments
        for team in teams:
            for jury in juries:
                JuryAssignment.objects.create(
                    contest=contest,
                    team=team,
                    jury_member=jury
                )

        # 8. Create Scores
        for team in teams:
            for jury in juries:
                for criterion in criteria:
                    JuryScore.objects.create(
                        contest=contest,
                        team=team,
                        jury_member=jury,
                        criterion=criterion,
                        score=Decimal(str(random.randint(7, 10)))
                    )

        # 9. Announcements
        Announcement.objects.create(
            contest=contest,
            title="Welcome to the Hackathon!",
            content="We are excited to see your amazing ideas. Good luck to all teams!",
            author=organizer,
            is_pinned=True
        )

        # 10. Schedule Events
        ScheduleEvent.objects.create(
            contest=contest,
            title="Opening Ceremony",
            description="Join us for the official kickoff.",
            start_time=now + timedelta(days=3, hours=10),
            event_type=ScheduleEvent.EventType.OTHER,
            order=1
        )
        
        ScheduleEvent.objects.create(
            contest=contest,
            title="Round 1 Deadline",
            start_time=round1.deadline,
            event_type=ScheduleEvent.EventType.DEADLINE,
            round=round1,
            order=2
        )

        # 11. Evaluation Phase
        ContestEvaluationPhase.objects.get_or_create(
            contest=contest,
            defaults={'status': ContestEvaluationPhase.Status.IN_PROGRESS}
        )

        # 12. Notifications
        for user in participants + members:
            Notification.objects.create(
                recipient=user,
                notification_type=Notification.Type.REGISTRATION_OPEN,
                title="Registration Open",
                message=f"Registration for {contest.name} is now open!",
                link=f"/contests/{contest.pk}/"
            )
