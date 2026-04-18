from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from ..models import Application, Contest, User, Team
from ..forms import TeamForm
from .views_base import RedirectToRegisterMixin


class ViewTeamsView(RedirectToRegisterMixin, ListView):
    template_name = "app/teams.html"
    context_object_name = "teams"

    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return self.contest.teams.all()

    def get_context_data(self, **kwargs):
        return super().get_context_data(contest=self.contest, **kwargs)


class ViewJurysView(RedirectToRegisterMixin, ListView):
    template_name = "app/jurys.html"
    context_object_name = "jurys"

    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return self.contest.jurys.all()

    def get_context_data(self, **kwargs):
        return super().get_context_data(contest=self.contest, **kwargs)


class TeamDetailView(RedirectToRegisterMixin, DetailView):
    template_name = "app/team.html"
    context_object_name = "team"

    def get_object(self, queryset=None):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return get_object_or_404(self.contest.teams, pk=self.kwargs["ck"])

    def get_context_data(self, **kwargs):
        team_apps = self.object.team_apps.filter(status=Application.Status.PENDING)
        return super().get_context_data(contest=self.contest, team_applications=team_apps, **kwargs)


class TeamActionMixin(RedirectToRegisterMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        self.team = get_object_or_404(self.contest.teams, pk=kwargs["ck"])
        if request.user != self.team.captain:
            return HttpResponseForbidden("You are not the captain of this team.")
        self.target_user = get_object_or_404(User, pk=kwargs["user_id"])
        return super().dispatch(request, *args, **kwargs)


class TeamKickView(TeamActionMixin, View):
    def post(self, request, *args, **kwargs):
        if self.target_user in self.team.participants.all():
            self.team.participants.remove(self.target_user)
        return redirect("team_detail", pk=self.contest.pk, ck=self.team.pk)


class TeamBlockView(TeamActionMixin, View):
    def post(self, request, *args, **kwargs):
        if self.target_user in self.team.participants.all():
            self.team.participants.remove(self.target_user)
        self.team.blacklisted_members.add(self.target_user)
        self.team.team_apps.filter(user=self.target_user, status=Application.Status.PENDING).update(status=Application.Status.REJECTED)
        return redirect("team_detail", pk=self.contest.pk, ck=self.team.pk)


class TeamUnblockView(TeamActionMixin, View):
    def post(self, request, *args, **kwargs):
        self.team.blacklisted_members.remove(self.target_user)
        return redirect("team_detail", pk=self.contest.pk, ck=self.team.pk)


class LeaderboardAccessMixin(RedirectToRegisterMixin):
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)


class AdminPermissionMixin(LeaderboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if request.user.is_authenticated and request.user != self.contest.organizer and not request.user.is_staff:
            return HttpResponseForbidden("You do not have admin access to this contest.")
        return super().dispatch(request, *args, **kwargs)


from django.views.generic import UpdateView
from django.urls import reverse_lazy

class TeamUpdateView(RedirectToRegisterMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "app/team_form.html"
    context_object_name = "team"

    def get_object(self, queryset=None):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        team = get_object_or_404(self.contest.teams, pk=self.kwargs["ck"])
        if self.request.user != team.captain:
             # This is a simple check, better to use a mixin but for now this works matching existing patterns
             pass
        return team

    def get_context_data(self, **kwargs):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return super().get_context_data(contest=self.contest, **kwargs)

    def get_success_url(self):
        return reverse_lazy("team_detail", kwargs={"pk": self.kwargs["pk"], "ck": self.kwargs["ck"]})

    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        team = get_object_or_404(self.contest.teams, pk=kwargs["ck"])
        if request.user != team.captain:
            return HttpResponseForbidden("You are not the captain of this team.")
        return super().dispatch(request, *args, **kwargs)
