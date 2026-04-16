from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from ..models import Application, Contest, Notification
from ..services import notify_user
from .views_base import RedirectToRegisterMixin


class ApplicationActionView(RedirectToRegisterMixin, View):
    """Approve or reject an application; `action` kwarg comes from the URL."""

    def post(self, request, pk, action):
        application = get_object_or_404(Application, pk=pk)
        is_organizer = application.contest and request.user == application.contest.organizer
        is_captain = application.team and request.user == application.team.captain

        if is_organizer or is_captain:
            if action == "approve":
                application.status = Application.Status.APPROVED
                application.save()

                if is_captain and not is_organizer:
                    application.team.participants.add(application.user)
                elif is_organizer:
                    if application.application_type == Application.Type.TEAM and application.team:
                        if application.contest.max_teams and application.contest.teams.count() >= application.contest.max_teams:
                            messages.error(
                                request,
                                f"Cannot approve: Contest '{application.contest.name}' has reached its maximum of {application.contest.max_teams} teams."
                            )
                            return redirect("contest_detail", pk=application.contest.pk)
                        application.contest.teams.add(application.team)
                    elif application.application_type == Application.Type.JURY:
                        application.contest.jurys.add(application.user)
                    elif application.application_type == Application.Type.PARTICIPANT:
                        if application.team:
                            application.team.participants.add(application.user)
                        else:
                            application.contest.participants.add(application.user)
            elif action == "reject":
                application.status = Application.Status.REJECTED
                application.save()

            status_text = "approved" if action == "approve" else "rejected"
            notify_user(
                application.user,
                Notification.Type.APPLICATION_UPDATE,
                f"Application {status_text}",
                f"Your application for '{application.contest.name}' has been {status_text}.",
                link=reverse("contest_detail", kwargs={"pk": application.contest.pk})
            )

            if is_captain and not is_organizer:
                return redirect("team_detail", pk=application.contest.pk, ck=application.team.pk)

        return redirect("contest_detail", pk=application.contest.pk)


class ApplyToContestView(RedirectToRegisterMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk, app_type):
        contest = get_object_or_404(Contest, pk=pk)
        if contest.status == Contest.Status.DRAFT:
            return HttpResponseForbidden("Cannot apply to a draft contest.")

        from django.utils import timezone

        now = timezone.now()
        if contest.registration_start and now < contest.registration_start:
            messages.error(request, "Registration for this contest has not started yet.")
            return redirect("contest_detail", pk=pk)
        if contest.registration_end and now >= contest.registration_end:
            messages.error(request, "Registration for this contest has already closed.")
            return redirect("contest_detail", pk=pk)

        if app_type == "participant":
            role_type = Application.Type.PARTICIPANT
        elif app_type == "jury":
            role_type = Application.Type.JURY
        else:
            return HttpResponseForbidden("Invalid application type.")

        Application.objects.get_or_create(
            user=request.user,
            contest=contest,
            application_type=role_type,
        )
        return redirect("contest_detail", pk=pk)
