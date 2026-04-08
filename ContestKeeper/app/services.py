from .models import Notification

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
