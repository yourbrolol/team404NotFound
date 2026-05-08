from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from app.models import Contest, JuryAssignment


class RedirectToRegisterMixin(LoginRequiredMixin):
    """Redirect unauthenticated users to the register page."""
    login_url = "accounts/login"
    raise_exception = False


class ContestContextMixin:
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class OrganizerRequiredMixin(RedirectToRegisterMixin, ContestContextMixin):
    """Allow access only to the organizer of the contest identified by <pk>."""
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.contest.organizer != request.user and not request.user.is_staff:
            return HttpResponseForbidden("You are not the organizer of this contest.")
        return super().dispatch(request, *args, **kwargs)


class JuryRequiredMixin(RedirectToRegisterMixin, ContestContextMixin):
    """Allow access only to users who are assigned as Jurys for the contest."""
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        is_contest_jury = self.contest.jurys.filter(pk=request.user.pk).exists()
        is_assigned_jury = JuryAssignment.objects.filter(contest=self.contest, jury_member=request.user).exists()
        if not (is_contest_jury or is_assigned_jury):
            return HttpResponseForbidden("You are not a Jury member for this contest.")
        return super().dispatch(request, *args, **kwargs)


class OrganizerOrJuryMixin(RedirectToRegisterMixin, ContestContextMixin):
    """Allow access to organizers, jury members, or staff for the contest."""
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        is_organizer = self.contest.organizer == request.user
        is_jury = (
            self.contest.jurys.filter(pk=request.user.pk).exists()
            or JuryAssignment.objects.filter(contest=self.contest, jury_member=request.user).exists()
        )
        if not (is_organizer or is_jury or request.user.is_staff):
            return HttpResponseForbidden("You do not have access to this page.")
        return super().dispatch(request, *args, **kwargs)


