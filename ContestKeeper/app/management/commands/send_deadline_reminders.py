from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Round, Notification
from app.services import notify_user

class Command(BaseCommand):
    help = "Send notifications for rounds with deadlines in the next 24 hours"

    def handle(self, *args, **options):
        now = timezone.now()
        window_start = now
        window_end = now + timedelta(hours=24)

        rounds = Round.objects.filter(
            status=Round.Status.ACTIVE,
            deadline__gte=window_start,
            deadline__lte=window_end,
        )

        for round_obj in rounds:
            # Find teams that haven't submitted
            submitted_team_ids = round_obj.submissions.values_list('team_id', flat=True)
            teams_without_submission = round_obj.contest.teams.exclude(id__in=submitted_team_ids)

            for team in teams_without_submission:
                for member in team.participants.all():
                    # Avoid duplicate reminders (check if already sent in the last 24h)
                    already_sent = Notification.objects.filter(
                        recipient=member,
                        notification_type=Notification.Type.DEADLINE_APPROACHING,
                        link__contains=f"/rounds/{round_obj.pk}/",
                        created_at__gte=now - timedelta(hours=24),
                    ).exists()
                    
                    if not already_sent:
                        notify_user(
                            member,
                            Notification.Type.DEADLINE_APPROACHING,
                            f"Deadline approaching: {round_obj.title}",
                            f"Less than 24 hours until the submission deadline for '{round_obj.title}' in '{round_obj.contest.name}'. Submit your work before {round_obj.deadline.strftime('%b %d, %H:%M UTC')}.",
                            link=f"/contests/{round_obj.contest.pk}/rounds/{round_obj.pk}/",
                        )

        self.stdout.write(self.style.SUCCESS(f"Processed {rounds.count()} rounds."))
