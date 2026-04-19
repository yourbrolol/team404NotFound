from app.models import Notification

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
