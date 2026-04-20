from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from app.models import Contest


class RedirectToRegisterMixin(LoginRequiredMixin):
    """Redirect unauthenticated users to the register page."""
    login_url = "register"
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
        if self.contest.organizer != request.user:
            return HttpResponseForbidden("You are not the organizer of this contest.")
        return super().dispatch(request, *args, **kwargs)


class JuryRequiredMixin(RedirectToRegisterMixin, ContestContextMixin):
    """Allow access only to users who are assigned as Jurys for the contest."""
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.contest.jurys.filter(pk=request.user.pk).exists():
            return HttpResponseForbidden("You are not a Jury member for this contest.")
        return super().dispatch(request, *args, **kwargs)


