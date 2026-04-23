import random
from app.models import Notification, JuryAssignment

def assign_jury_to_teams(contest, min_reviews_per_team=2):
    """
    Randomly and evenly assign jury members to teams for a contest.
    
    Args:
        contest: Contest instance
        min_reviews_per_team: how many jury members should review each team
        
    Returns:
        Number of assignments created.
    """
    jurys = list(contest.jurys.all())
    teams = list(contest.teams.all())
    
    if not jurys:
        return 0
    
    # If we have fewer jurys than min_reviews, cap it
    k = min(min_reviews_per_team, len(jurys))
    
    # Clear existing assignments for this contest
    JuryAssignment.objects.filter(contest=contest).delete()
    
    assignments = []
    
    # Simple round-robin like distribution to keep it even
    # Shuffle juries to ensure randomness
    random.shuffle(jurys)
    
    jury_pool = jurys * ((len(teams) * k // len(jurys)) + 1)
    pool_idx = 0
    
    for team in teams:
        # For each team, we need k unique jury members
        assigned_to_team = 0
        tried_indices = set()
        
        while assigned_to_team < k:
            jury = jury_pool[pool_idx % len(jury_pool)]
            
            # Ensure jury member is not already assigned to this team
            if jury not in [a.jury_member for a in assignments if a.team == team]:
                assignments.append(JuryAssignment(
                    contest=contest,
                    team=team,
                    jury_member=jury
                ))
                assigned_to_team += 1
            
            pool_idx += 1
            
    JuryAssignment.objects.bulk_create(assignments)
    return len(assignments)

def notify_user(user, notification_type, title, message, link=""):
    """Create a single notification for a user."""
    return Notification.objects.create(
        recipient=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )

def notify_contest_participants(contest, notification_type, title, message, link=""):
    """Notify all participants (team members) of a contest."""
    users = set()
    for team in contest.teams.all():
        for member in team.participants.all():
            users.add(member)
    
    notifications = [
        Notification(
            recipient=u,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        for u in users
    ]
    Notification.objects.bulk_create(notifications)

def notify_contest_jury(contest, notification_type, title, message, link=""):
    """Notify all jury members of a contest."""
    notifications = [
        Notification(
            recipient=j,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        for j in contest.jurys.all()
    ]
    Notification.objects.bulk_create(notifications)


def generate_schedule_from_rounds(contest):
    """Automatically generate schedule events based on contest rounds."""
    from app.models import ScheduleEvent
    
    # Clear existing auto-generated round events
    ScheduleEvent.objects.filter(contest=contest, event_type=ScheduleEvent.EventType.ROUND).delete()
    ScheduleEvent.objects.filter(contest=contest, event_type=ScheduleEvent.EventType.DEADLINE).delete()
    
    events = []
    for rnd in contest.rounds.all():
        # Start event
        events.append(ScheduleEvent(
            contest=contest,
            title=f"Start: {rnd.title}",
            description=rnd.description,
            start_time=rnd.start_time,
            end_time=rnd.start_time,
            event_type=ScheduleEvent.EventType.ROUND,
            order=rnd.order * 10
        ))
        
        # Deadline event
        events.append(ScheduleEvent(
            contest=contest,
            title=f"Deadline: {rnd.title}",
            description=f"Submission deadline for {rnd.title}.",
            start_time=rnd.deadline,
            end_time=rnd.deadline,
            event_type=ScheduleEvent.EventType.DEADLINE,
            order=rnd.order * 10 + 5
        ))
    
    ScheduleEvent.objects.bulk_create(events)
    return len(events)
