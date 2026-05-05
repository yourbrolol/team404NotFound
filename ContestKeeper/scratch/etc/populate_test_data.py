import os
import sys
import django
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ContestKeeper.settings")

# Configure a separate database for this script
from django.conf import settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.getcwd(), 'test_db.sqlite3'),
    }
}
settings.DATABASES = DATABASES

django.setup()

from app.models import User, Team, Contest, Round, Submission, ScoringCriterion, JuryAssignment, JuryScore

def create_users():
    print("Creating users...")
    users = {}
    
    # Admin
    admin = User.objects.create_superuser('root_admin', 'admin@example.com', 'password')
    admin.role = User.Role.ORGANIZER
    admin.bio = "Lead platform architect and global moderator."
    admin.save()
    users['root_admin'] = admin
    
    # Organizers
    event_nexus = User.objects.create_user('event_nexus', 'nexus@example.com', 'password')
    event_nexus.role = User.Role.ORGANIZER
    event_nexus.is_staff = True
    event_nexus.bio = "Professional hackathon organizer with 10+ years experience."
    event_nexus.save()
    users['event_nexus'] = event_nexus
    
    spark_labs = User.objects.create_user('spark_labs', 'spark@example.com', 'password')
    spark_labs.role = User.Role.ORGANIZER
    spark_labs.bio = "Innovation hub focusing on student-led initiatives."
    spark_labs.save()
    users['spark_labs'] = spark_labs
    
    # Jurors
    juror_data = [
        ('silent_evaluator', 'Backend Architecture & Scalability'),
        ('pixel_perfect', 'UI/UX Design and Frontend Excellence'),
        ('bug_hunter', 'Cybersecurity and Quality Assurance'),
        ('logic_wizard', 'Algorithms and Data Structures'),
        ('cloud_surfer', 'DevOps and Cloud Infrastructure'),
        ('data_druid', 'Machine Learning and Analytics'),
        ('vision_vanguard', 'Product Vision and Market Fit'),
    ]
    for username, expertise in juror_data:
        u = User.objects.create_user(username, f'{username}@example.com', 'password')
        u.role = User.Role.JURY
        u.bio = expertise
        u.save()
        users[username] = u
        
    # Participants
    participants = [
        'bold-eagle', 'fast_tiger', 'silent-fox', 'clever_owl', 'brave-wolf',
        'lazy_bear', 'mighty-lion', 'quick_hawk', 'fierce-shark', 'gentle_deer',
        'bright-lynx', 'shadow_panther', 'silver-cobra', 'golden_falcon', 'iron-whale'
    ]
    for username in participants:
        u = User.objects.create_user(username, f'{username}@example.com', 'password')
        u.role = User.Role.PARTICIPANT
        u.save()
        users[username] = u
        
    return users

def create_contests(users):
    print("Creating contests...")
    now = timezone.now()
    
    # Contest A: Retro Web Revival (Finished)
    contest_a = Contest.objects.create(
        name="Retro Web Revival",
        description="Revive the 90s web aesthetics with modern tech.",
        registration_start=now - timedelta(days=30),
        registration_end=now - timedelta(days=25),
        start_date=now - timedelta(days=24),
        end_date=now - timedelta(days=18),
        organizer=users['spark_labs'],
        is_draft=False
    )
    contest_a.jurys.add(users['pixel_perfect'], users['silent_evaluator'])
    
    # Contest B: Python Efficiency Sprint (Finished)
    contest_b = Contest.objects.create(
        name="Python Efficiency Sprint",
        description="Write the most efficient Python code for complex algorithms.",
        registration_start=now - timedelta(days=20),
        registration_end=now - timedelta(days=16),
        start_date=now - timedelta(days=15),
        end_date=now - timedelta(days=10),
        organizer=users['event_nexus'],
        is_draft=False
    )
    contest_b.jurys.add(users['logic_wizard'], users['bug_hunter'])
    
    # Contest C: The AI Edge (Running)
    contest_c = Contest.objects.create(
        name="The AI Edge",
        description="Building the next generation of AI-powered tools.",
        registration_start=now - timedelta(days=10),
        registration_end=now - timedelta(days=5),
        start_date=now - timedelta(days=4),
        end_date=now + timedelta(days=5),
        organizer=users['root_admin'],
        is_draft=False
    )
    contest_c.jurys.add(users['data_druid'], users['cloud_surfer'], users['vision_vanguard'])
    
    # Contest D: Decentralized Future (Running)
    contest_d = Contest.objects.create(
        name="Decentralized Future",
        description="Exploring Web3 and decentralized protocols.",
        registration_start=now - timedelta(days=8),
        registration_end=now - timedelta(days=3),
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=10),
        organizer=users['spark_labs'],
        is_draft=False
    )
    contest_d.jurys.add(users['silent_evaluator']) # Added later as per scenario
    
    # Contest E: Global Green Tech (Registration)
    contest_e = Contest.objects.create(
        name="Global Green Tech",
        description="Eco-friendly tech solutions for a sustainable world.",
        registration_start=now - timedelta(days=4),
        registration_end=now + timedelta(days=3),
        start_date=now + timedelta(days=5),
        end_date=now + timedelta(days=12),
        organizer=users['event_nexus'],
        is_draft=False
    )
    
    # Contest F: Cyber Security Dash (Draft)
    contest_f = Contest.objects.create(
        name="Cyber Security Dash",
        description="Identify and patch vulnerabilities in record time.",
        start_date=now + timedelta(days=20),
        end_date=now + timedelta(days=25),
        organizer=users['spark_labs'],
        is_draft=True
    )
    
    return {
        'A': contest_a, 'B': contest_b, 'C': contest_c, 
        'D': contest_d, 'E': contest_e, 'F': contest_f
    }

def create_teams_and_submissions(users, contests):
    print("Creating teams and submissions...")
    
    # --- Contest A: Retro Web Revival ---
    # Team OldSchool
    team_os = Team.objects.create(name="OldSchool", status=Team.Status.ACTIVE, captain=users['bold-eagle'])
    team_os.participants.add(users['bold-eagle'], users['fast_tiger'])
    contests['A'].teams.add(team_os)
    
    # Team PixelPioneers
    team_pp = Team.objects.create(name="PixelPioneers", status=Team.Status.ACTIVE, captain=users['silent-fox'])
    team_pp.participants.add(users['silent-fox'], users['clever_owl'])
    contests['A'].teams.add(team_pp)
    
    # Create Round and Submissions for A
    round_a = Round.objects.create(
        contest=contests['A'], title="Main Round", order=1,
        start_time=contests['A'].start_date, deadline=contests['A'].end_date,
        status=Round.Status.EVALUATED
    )
    
    Submission.objects.create(
        round=round_a, team=team_os, 
        github_url="https://github.com/test/oldschool", 
        video_url="https://youtube.com/test1",
        description="A retro site using 90s table layouts."
    )
    Submission.objects.create(
        round=round_a, team=team_pp, 
        github_url="https://github.com/test/pixelpioneers", 
        video_url="https://youtube.com/test2",
        description="Animated GIFs and marquee tags everywhere."
    )
    
    # --- Contest C: The AI Edge ---
    # Team NeuralKnights
    team_nk = Team.objects.create(name="NeuralKnights", status=Team.Status.ACTIVE, captain=users['brave-wolf'])
    team_nk.participants.add(users['brave-wolf'], users['mighty-lion'])
    contests['C'].teams.add(team_nk)
    
    # Team DataDragons
    team_dd = Team.objects.create(name="DataDragons", status=Team.Status.ACTIVE, captain=users['quick_hawk'])
    team_dd.participants.add(users['quick_hawk'], users['fierce-shark'])
    contests['C'].teams.add(team_dd)
    
    # Team CodeCommandos
    team_cc = Team.objects.create(name="CodeCommandos", status=Team.Status.ACTIVE, captain=users['gentle_deer'])
    team_cc.participants.add(users['gentle_deer'], users['bright-lynx'])
    contests['C'].teams.add(team_cc)
    
    round_c = Round.objects.create(
        contest=contests['C'], title="Innovation Phase", order=1,
        start_time=contests['C'].start_date, deadline=contests['C'].end_date,
        status=Round.Status.ACTIVE
    )
    
    # NeuralKnights - Rated
    sub_nk = Submission.objects.create(
        round=round_c, team=team_nk, 
        github_url="https://github.com/test/neuralknights", 
        video_url="https://youtube.com/test3",
        description="High quality ML model."
    )
    # Scoring for NeuralKnights
    crit_c = ScoringCriterion.objects.create(contest=contests['C'], name="Innovation", max_score=100)
    JuryAssignment.objects.create(contest=contests['C'], team=team_nk, jury_member=users['data_druid'])
    JuryScore.objects.create(contest=contests['C'], team=team_nk, jury_member=users['data_druid'], criterion=crit_c, score=Decimal("95.00"))

    # DataDragons - Submitted (Pending)
    Submission.objects.create(
        round=round_c, team=team_dd, 
        github_url="https://github.com/test/datadragons", 
        video_url="https://youtube.com/test4",
        description="Fresh submission."
    )
    JuryAssignment.objects.create(contest=contests['C'], team=team_dd, jury_member=users['data_druid'])

    # CodeCommandos - Draft (we don't have a 'draft' status in Submission model, but we can simulate it by missing fields or a separate flag if it existed.
    # Looking at models, there is no Draft status for Submission. It's either there or not.
    # However, Team has a status. Or the user meant "Not yet posted".
    # I'll just NOT create a submission for CodeCommandos yet.
    
    # --- Contest D: Decentralized Future ---
    team_bb = Team.objects.create(name="BlockBuilders", status=Team.Status.ACTIVE, captain=users['shadow_panther'])
    team_bb.participants.add(users['shadow_panther'], users['silver-cobra'])
    contests['D'].teams.add(team_bb)
    
    team_ch = Team.objects.create(name="ChainChasers", status=Team.Status.ACTIVE, captain=users['golden_falcon'])
    team_ch.participants.add(users['golden_falcon'], users['iron-whale'])
    contests['D'].teams.add(team_ch)
    
    round_d = Round.objects.create(
        contest=contests['D'], title="Genesis Round", order=1,
        start_time=contests['D'].start_date, deadline=contests['D'].end_date,
        status=Round.Status.ACTIVE
    )
    
    Submission.objects.create(
        round=round_d, team=team_bb, 
        github_url="https://github.com/test/blockbuilders", 
        video_url="https://youtube.com/test5",
        description="Blockchain solution."
    )
    JuryAssignment.objects.create(contest=contests['D'], team=team_bb, jury_member=users['silent_evaluator'])

def main():
    if os.path.exists('test_db.sqlite3'):
        os.remove('test_db.sqlite3')
        print("Removed existing test_db.sqlite3")
        
    print("Running migrations...")
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    
    users = create_users()
    contests = create_contests(users)
    create_teams_and_submissions(users, contests)
    
    print("\nSuccessfully created test_db.sqlite3 with populated data!")

if __name__ == "__main__":
    main()
