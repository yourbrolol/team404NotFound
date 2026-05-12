import os
import django
import sys
from datetime import timedelta
from django.utils import timezone

# Add the project directory to sys.path
sys.path.append('/mnt/data/Documents/Projects/StarForLife/team404NotFound/ContestKeeper')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ContestKeeper.settings')
django.setup()

from app.models import User, Contest, Announcement, ScheduleEvent, Round

def populate_extras():
    print("Populating extra announcements and schedules...")
    
    root_admin = User.objects.get(username="root_admin")
    event_nexus = User.objects.get(username="event_nexus")
    spark_labs = User.objects.get(username="spark_labs")
    
    # 1. Announcements for all contests
    announcements_data = [
        ("Retro Web Revival", spark_labs, "Winners Announced!", "Congratulations to the winners! Check the leaderboard."),
        ("Retro Web Revival", spark_labs, "Final Review in Progress", "The jury is reviewing the final batch of code."),
        ("Python Efficiency Sprint", event_nexus, "Leaderboard Finalized", "All scores are in. Well done!"),
        ("Python Efficiency Sprint", event_nexus, "Check your feedback", "The jury has left comments on your submissions."),
        ("The AI Edge", root_admin, "New Dataset Released", "A new training set is available for the second round."),
        ("The AI Edge", root_admin, "Server Maintenance", "Dashboard will be down for 10 minutes at midnight."),
        ("Decentralized Future", spark_labs, "Security First!", "Remember to audit your smart contracts before submission."),
        ("Decentralized Future", spark_labs, "Round 1 Checklist", "Ensure you have met all requirements listed in the round description."),
        ("Global Green Tech", event_nexus, "Registration Open!", "Spread the word! Early bird registration ends in 2 days."),
        ("Global Green Tech", event_nexus, "Mentorship Program", "We have invited 5 industry experts to mentor teams."),
        ("Cyber Security Dash", spark_labs, "Draft Note", "This contest is still in draft phase. Stay tuned for updates."),
    ]
    
    for c_name, author, title, content in announcements_data:
        try:
            contest = Contest.objects.get(name=c_name)
            Announcement.objects.get_or_create(
                contest=contest,
                title=title,
                defaults={'content': content, 'author': author}
            )
        except Contest.DoesNotExist:
            print(f"Contest {c_name} not found.")

    # 2. Schedule Events for all contests
    schedule_data = [
        # Retro Web Revival
        ("Retro Web Revival", "Opening Ceremony", "Kickoff event.", 0, 2, ScheduleEvent.EventType.OTHER),
        ("Retro Web Revival", "Code Jam Start", "Initial coding phase.", 2, 48, ScheduleEvent.EventType.ROUND),
        ("Retro Web Revival", "Mid-week Checkpoint", "Progress report.", 72, 74, ScheduleEvent.EventType.OTHER),
        ("Retro Web Revival", "Submission Deadline", "Hard deadline.", 160, 168, ScheduleEvent.EventType.DEADLINE),
        ("Retro Web Revival", "Award Ceremony", "Winner announcement.", 180, 182, ScheduleEvent.EventType.OTHER),
        
        # Python Efficiency Sprint
        ("Python Efficiency Sprint", "Kickoff Webinar", "How to win the sprint.", 0, 1, ScheduleEvent.EventType.WORKSHOP),
        ("Python Efficiency Sprint", "Coding Phase", "Main competition time.", 1, 96, ScheduleEvent.EventType.ROUND),
        ("Python Efficiency Sprint", "Final Push", "Last 24 hours.", 96, 120, ScheduleEvent.EventType.DEADLINE),
        
        # The AI Edge
        ("The AI Edge", "ML Workshop", "Intro to advanced ML techniques.", 24, 28, ScheduleEvent.EventType.WORKSHOP),
        ("The AI Edge", "Data Science Q&A", "Ask the experts.", 48, 50, ScheduleEvent.EventType.OTHER),
        
        # Decentralized Future
        ("Decentralized Future", "Smart Contract Audit 101", "How to write secure code.", 12, 14, ScheduleEvent.EventType.WORKSHOP),
        ("Decentralized Future", "Web3 Networking", "Meet other builders.", 36, 38, ScheduleEvent.EventType.OTHER),
        
        # Global Green Tech
        ("Global Green Tech", "Launch Event", "Global stream for the launch.", 0, 2, ScheduleEvent.EventType.OTHER),
        ("Global Green Tech", "Sustainability Webinar", "Expert talk on green tech.", 48, 50, ScheduleEvent.EventType.WORKSHOP),
    ]
    
    for c_name, title, desc, start_off, end_off, e_type in schedule_data:
        try:
            contest = Contest.objects.get(name=c_name)
            ScheduleEvent.objects.get_or_create(
                contest=contest,
                title=title,
                defaults={
                    'description': desc,
                    'start_time': contest.start_date + timedelta(hours=start_off),
                    'end_time': contest.start_date + timedelta(hours=end_off) if end_off else None,
                    'event_type': e_type
                }
            )
        except Contest.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error adding schedule for {c_name}: {e}")

    print("Extra population complete!")

if __name__ == "__main__":
    populate_extras()
