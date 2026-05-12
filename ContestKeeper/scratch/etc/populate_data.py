import os
import django
import sys
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

# Add the project directory to sys.path
sys.path.append('/mnt/data/Documents/Projects/StarForLife/team404NotFound/ContestKeeper')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ContestKeeper.settings')
django.setup()

from app.models import (
    User, Contest, Team, ScoringCriterion, JuryAssignment, 
    JuryScore, Application, RoleApplication, Announcement, 
    Notification, ScheduleEvent, Round, Submission
)

def populate():
    print("Starting data population...")
    
    # 1. Scoring Criteria
    contests = Contest.objects.all()
    criteria_names = {
        "Retro Web Revival": ["Visual Aesthetics", "Code Cleanliness", "Historical Accuracy"],
        "Python Efficiency Sprint": ["Algorithm Performance", "Memory Usage", "Pythonic Style"],
        "The AI Edge": ["Model Accuracy", "Technical Complexity", "Innovation"], # Innovation exists
        "Decentralized Future": ["Security", "Smart Contract Logic", "UI/UX"],
        "Global Green Tech": ["Sustainability Impact", "Feasibility", "Presentation"],
    }
    
    for contest_name, names in criteria_names.items():
        try:
            contest = Contest.objects.get(name=contest_name)
            for i, name in enumerate(names):
                ScoringCriterion.objects.get_or_create(
                    contest=contest,
                    name=name,
                    defaults={
                        'max_score': 100,
                        'weight': Decimal("1.00"),
                        'order': i
                    }
                )
        except Contest.DoesNotExist:
            print(f"Contest {contest_name} not found.")

    # 2. Additional Teams for historical contests
    try:
        retro_contest = Contest.objects.get(name="Retro Web Revival")
        spark_labs = User.objects.get(username="spark_labs")
        participants = list(User.objects.filter(role=User.Role.PARTICIPANT))
        
        # Add 3 more teams to Retro Web Revival to reach 5
        extra_teams = [
            ("VGA_Warriors", participants[4:6]),
            ("C64_Legends", participants[6:8]),
            ("Terminal_Turtles", participants[8:10]),
        ]
        
        for t_name, members in extra_teams:
            team, created = Team.objects.get_or_create(
                name=t_name,
                defaults={'status': Team.Status.ACTIVE, 'captain': members[0]}
            )
            if created:
                team.participants.set(members)
                retro_contest.teams.add(team)
                
                # Add submissions for these teams
                round_1 = retro_contest.rounds.filter(order=1).first()
                if round_1:
                    Submission.objects.get_or_create(
                        round=round_1,
                        team=team,
                        defaults={
                            'github_url': f"https://github.com/test/{t_name}",
                            'video_url': f"https://youtube.com/watch?v={t_name}",
                            'description': f"Retro project by {t_name}"
                        }
                    )
    except Exception as e:
        print(f"Error adding extra teams: {e}")

    # 3. Jury Assignments
    # doc/test_data.md:
    # Retro Web Revival Jurors: pixel_perfect, silent_evaluator
    # Python Efficiency Sprint Jurors: logic_wizard, bug_hunter
    # The AI Edge Jurors: data_druid, cloud_surfer, vision_vanguard
    # Decentralized Future Jurors: silent_evaluator, security_pro (security_pro might not exist)
    
    jury_map = {
        "Retro Web Revival": ["pixel_perfect", "silent_evaluator"],
        "Python Efficiency Sprint": ["logic_wizard", "bug_hunter"],
        "The AI Edge": ["data_druid", "cloud_surfer", "vision_vanguard"],
        "Decentralized Future": ["silent_evaluator"],
    }
    
    for c_name, j_usernames in jury_map.items():
        try:
            contest = Contest.objects.get(name=c_name)
            for j_name in j_usernames:
                try:
                    jury_user = User.objects.get(username=j_name)
                    contest.jurys.add(jury_user)
                    # Assign to all teams in this contest
                    for team in contest.teams.all():
                        JuryAssignment.objects.get_or_create(
                            contest=contest,
                            team=team,
                            jury_member=jury_user
                        )
                except User.DoesNotExist:
                    print(f"Jury user {j_name} not found.")
        except Contest.DoesNotExist:
            pass

    # 4. Jury Scores (Historical)
    import random
    for contest in Contest.objects.filter(status=Contest.Status.FINISHED):
        criteria = contest.scoring_criteria.all()
        assignments = JuryAssignment.objects.filter(contest=contest)
        for ass in assignments:
            for crit in criteria:
                JuryScore.objects.get_or_create(
                    contest=contest,
                    team=ass.team,
                    jury_member=ass.jury_member,
                    criterion=crit,
                    defaults={'score': Decimal(str(random.randint(70, 100)))}
                )

    # 5. Applications
    try:
        green_tech = Contest.objects.get(name="Global Green Tech")
        p1 = User.objects.get(username="lazy_bear")
        p2 = User.objects.get(username="mighty-lion")
        
        Application.objects.get_or_create(
            user=p1,
            contest=green_tech,
            application_type=Application.Type.PARTICIPANT,
            defaults={'status': Application.Status.PENDING}
        )
        
        # Role Applications
        RoleApplication.objects.get_or_create(
            username="new_judge_alex",
            defaults={
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Judge',
                'password': 'hashed_password',
                'desired_role': User.Role.JURY,
                'reason': 'I have judge 5 hackathons before.',
                'experience': 'Senior Dev at Google',
                'status': RoleApplication.Status.PENDING
            }
        )
        
        RoleApplication.objects.get_or_create(
            username="bad_actor",
            defaults={
                'email': 'bad@example.com',
                'first_name': 'Bad',
                'last_name': 'Actor',
                'password': 'hashed_password',
                'desired_role': User.Role.ORGANIZER,
                'reason': 'I want to mess things up.',
                'experience': 'None',
                'status': RoleApplication.Status.REJECTED
            }
        )
    except Exception as e:
        print(f"Error adding applications: {e}")

    # 6. Announcements
    try:
        root_admin = User.objects.get(username="root_admin")
        ai_edge = Contest.objects.get(name="The AI Edge")
        
        Announcement.objects.get_or_create(
            contest=ai_edge,
            title="Halfway Point Reached!",
            content="Great job everyone! Don't forget to update your progress in the dashboard.",
            author=root_admin,
            is_pinned=True
        )
        
        Announcement.objects.get_or_create(
            contest=ai_edge,
            title="New Resource: GPU Cluster Access",
            content="We have provided free access to GPU clusters for the next 48 hours.",
            author=root_admin
        )
    except Exception as e:
        print(f"Error adding announcements: {e}")

    # 7. Notifications
    try:
        all_users = User.objects.all()[:10]
        for user in all_users:
            Notification.objects.create(
                recipient=user,
                notification_type=Notification.Type.ANNOUNCEMENT,
                title="Welcome to ContestKeeper",
                message="We are glad to have you here! Check out the active contests.",
                link="/contests/"
            )
    except Exception as e:
        print(f"Error adding notifications: {e}")

    # 8. Schedule Events
    try:
        ai_edge = Contest.objects.get(name="The AI Edge")
        now = timezone.now()
        
        ScheduleEvent.objects.get_or_create(
            contest=ai_edge,
            title="Opening Ceremony",
            defaults={
                'description': 'Welcome speech and rules explanation.',
                'start_time': ai_edge.start_date,
                'end_time': ai_edge.start_date + timedelta(hours=2),
                'event_type': ScheduleEvent.EventType.OTHER
            }
        )
        
        ScheduleEvent.objects.get_or_create(
            contest=ai_edge,
            title="Submission Deadline",
            defaults={
                'description': 'Last chance to submit your projects!',
                'start_time': ai_edge.end_date - timedelta(hours=1),
                'end_time': ai_edge.end_date,
                'event_type': ScheduleEvent.EventType.DEADLINE
            }
        )
    except Exception as e:
        print(f"Error adding schedule events: {e}")

    print("Data population complete!")

if __name__ == "__main__":
    populate()
