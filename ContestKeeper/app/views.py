from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView, DeleteView

from .forms import UserRegistrationForm, ContestForm, UserSettingsForm
from .models import Contest, Application

# ── Mixins ────────────────────────────────────────────────────────────────────

class RedirectToRegisterMixin(LoginRequiredMixin):
    """Redirect unauthenticated users to the register page."""
    login_url = "register"
    raise_exception = False

class OrganizerRequiredMixin(RedirectToRegisterMixin):
    """Allow access only to the organizer of the contest identified by <pk>."""
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if contest.organizer != request.user:
            return HttpResponseForbidden("You are not the organizer of this contest.")
        return response

# ── Utility ───────────────────────────────────────────────────────────────────

def _make_template_view(template_name):
    """Factory: returns a login-required TemplateView for the given template."""
    return type("TemplateView", (RedirectToRegisterMixin, TemplateView), {"template_name": template_name})

# ── General views ─────────────────────────────────────────────────────────────

class HomeView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/index.html"
    def get_context_data(self, **kwargs):
        contests = Contest.objects.exclude(status=Contest.Status.DRAFT)
        return super().get_context_data(contests=contests, **kwargs)
ProfileView = _make_template_view("app/profile.html")

class DashboardView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/dashboard.html"
    def get_context_data(self, **kwargs):
        user = self.request.user
        if user.is_organizer():
            contests = user.organized_contests.all()
        elif user.is_jury():
            contests = user.judged_contests.exclude(status=Contest.Status.DRAFT)
        elif user.is_participant():
            contests = user.participated_contests.exclude(status=Contest.Status.DRAFT)
        else:
            contests = Contest.objects.none()
        return super().get_context_data(contests=contests, **kwargs)

class SettingsView(RedirectToRegisterMixin, View):
    def get(self, request):
        form = UserSettingsForm(instance=request.user)
        return render(request, "app/settings.html", {
            "form": form,
            "saved": request.GET.get("saved") == "1",
        })

    def post(self, request):
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("/settings/?saved=1")
        return render(request, "app/settings.html", {
            "form": form,
            "saved": False,
        })

# ── Contest views ─────────────────────────────────────────────────────────────

class ContestListView(ListView):
    """Returns a JSON list of all non-draft contests."""
    model = Contest
    def get_queryset(self):
        return Contest.objects.exclude(status=Contest.Status.DRAFT).values()
    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(list(self.get_queryset()), safe=False)

class ContestDetailView(DetailView):
    model = Contest
    template_name = "app/contest_detail.html"
    context_object_name = "contest"
    def get_object(self, queryset=None):
        contest = super().get_object(queryset)
        if contest.status == Contest.Status.DRAFT and contest.organizer != self.request.user:
            raise Http404("Contest is in draft or you don't have access.")
        return contest
    def get_context_data(self, **kwargs):
        contest = self.object
        user = self.request.user
        is_authenticated = user.is_authenticated
        user_team = None
        if is_authenticated: user_team = contest.teams.filter(participants=user).first()
        t_applications = contest.contest_apps.filter(
            application_type=Application.Type.TEAM,
            status=Application.Status.PENDING,
        )
        j_applications = contest.contest_apps.filter(
            application_type=Application.Type.JURY,
            status=Application.Status.PENDING,
        )
        p_applications = contest.contest_apps.filter(
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING,
        )
        return super().get_context_data(
            user_team=user_team,
            team_applications=t_applications,
            jury_applications=j_applications,
            participant_applications=p_applications,
            has_pending_p_app=contest.contest_apps.filter(
                user=user,
                application_type=Application.Type.TEAM,
                status=Application.Status.PENDING,
            ).exists() if is_authenticated else False,
            has_pending_j_app=contest.contest_apps.filter(
                user=user,
                application_type=Application.Type.JURY,
                status=Application.Status.PENDING,
            ).exists() if is_authenticated else False,
            **kwargs,
        )

class ContestFormView(RedirectToRegisterMixin, View):
    """Handles contest creation (no pk in URL) and editing (pk present)."""
    template_name = "app/contest_form.html"

    def _get_contest(self):
        """Return (contest_or_None, is_forbidden)."""
        pk = self.kwargs.get("pk")
        if pk is None:
            return None, False
        contest = get_object_or_404(Contest, pk=pk)
        return contest, (contest.organizer != self.request.user)

    def get(self, request, *args, **kwargs):
        contest, forbidden = self._get_contest()
        if forbidden:
            return HttpResponseForbidden("You are not the organizer of this contest.")
        form = ContestForm(instance=contest)
        return render(request, self.template_name, {"form": form, "is_edit": contest is not None})

    def post(self, request, *args, **kwargs):
        contest, forbidden = self._get_contest()
        if forbidden:
            return HttpResponseForbidden("You are not the organizer of this contest.")
        form = ContestForm(request.POST, request.FILES, instance=contest)
        if form.is_valid():
            obj = form.save(commit=False)
            if contest is None:
                obj.organizer = request.user
            obj.save()
            return redirect("home") if contest is None else redirect("contest_detail", pk=obj.pk)
        return render(request, self.template_name, {"form": form, "is_edit": contest is not None})

class ContestDeleteView(OrganizerRequiredMixin, DeleteView):
    model = Contest
    success_url = reverse_lazy("dashboard")
    def get(self, request, *args, **kwargs):
        # No confirmation template — redirect back if accessed via GET.
        return redirect("contest_detail", pk=kwargs["pk"])

# ── Application views ─────────────────────────────────────────────────────────

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
                    if application.application_type == Application.Type.TEAM:
                        if application.team:
                            application.contest.teams.add(application.team)
                    elif application.application_type == Application.Type.JURY:
                        application.contest.jurys.add(application.user)
                    elif application.application_type == Application.Type.PARTICIPANT:
                        # Could be a participant applying to a team or to the contest itself
                        if application.team:
                            application.team.participants.add(application.user)
                        else:
                            application.contest.participants.add(application.user)
                            
            elif action == "reject":
                application.status = Application.Status.REJECTED
                application.save()
                
            if is_captain and not is_organizer:
                return redirect("team_detail", pk=application.contest.pk, ck=application.team.pk)
                
        return redirect("contest_detail", pk=application.contest.pk)


class ApplyToContestView(RedirectToRegisterMixin, View):
    http_method_names = ["post"]
    def post(self, request, pk, app_type):
        contest = get_object_or_404(Contest, pk=pk)
        if contest.status == Contest.Status.DRAFT:
            return HttpResponseForbidden("Cannot apply to a draft contest.")
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

# ── Team views ────────────────────────────────────────────────────────────────

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
        team = self.get_object()
        team_apps = team.team_apps.filter(status=Application.Status.PENDING)
        return super().get_context_data(contest=self.contest, team_applications=team_apps, **kwargs)

class TeamActionMixin(RedirectToRegisterMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        self.team = get_object_or_404(self.contest.teams, pk=kwargs["ck"])
        if request.user != self.team.captain:
            return HttpResponseForbidden("You are not the captain of this team.")
        self.target_user = get_object_or_404(User, pk=kwargs["user_id"])
        return response

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

class TeamApplicationsView(RedirectToRegisterMixin, ListView):
    template_name = "app/teams_applications.html"
    context_object_name = "applications"
    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return self.contest.team_applications.all()
    def get_context_data(self, **kwargs):
        return super().get_context_data(contest=self.contest, **kwargs)

# ── Auth views ────────────────────────────────────────────────────────────────

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)