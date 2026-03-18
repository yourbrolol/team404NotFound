from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView, UpdateView, DeleteView

from .forms import UserRegistrationForm, ContestForm
from .models import Contest, Application

# Mixins

class RedirectToRegisterMixin(LoginRequiredMixin):
    """Redirect unauthenticated users to the register page."""
    login_url = "register"
    raise_exception = False

class OrganizerRequiredMixin(RedirectToRegisterMixin):
    """Allow access only to the organizer of the contest identified by <pk>."""
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # If LoginRequiredMixin already redirected, respect that.
        if not request.user.is_authenticated:
            return response
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if contest.organizer != request.user:
            return HttpResponseForbidden("You are not the organizer of this contest.")
        return response

# General views

class HomeView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/index.html"

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

class ProfileView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/profile.html"

# Contest views

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

        t_applications = contest.contest_apps.filter(
            application_type=Application.Type.TEAM,
            status=Application.Status.PENDING,
        )
        j_applications = contest.contest_apps.filter(
            application_type=Application.Type.JURY,
            status=Application.Status.PENDING,
        )
        return super().get_context_data(
            team_applications=t_applications,
            jury_applications=j_applications,
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

class ContestCreateView(RedirectToRegisterMixin, CreateView):
    model = Contest
    form_class = ContestForm
    template_name = "app/contest_form.html"
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)

class ContestEditView(OrganizerRequiredMixin, UpdateView):
    model = Contest
    form_class = ContestForm
    template_name = "app/contest_form.html"
    def get_success_url(self):
        return reverse_lazy("contest_detail", kwargs={"pk": self.object.pk})
    def get_context_data(self, **kwargs):
        return super().get_context_data(is_edit=True, **kwargs)

class ContestDeleteView(OrganizerRequiredMixin, DeleteView):
    model = Contest
    success_url = reverse_lazy("dashboard")
    def get(self, request, *args, **kwargs):
        # No confirmation template — redirect back if accessed via GET.
        return redirect("contest_detail", pk=kwargs["pk"])

# Application views

class ApplicationActionView(RedirectToRegisterMixin, View):
    """
    Base class for approve/reject actions.
    Subclasses set `new_status` and optionally override `on_approved`.
    """
    new_status = None
    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        if request.user == application.contest.organizer:
            application.status = self.new_status
            application.save()
            self.on_status_set(application)
        return redirect("contest_detail", pk=application.contest.pk)
    def on_status_set(self, application):
        """Hook called after status is saved. Override in subclasses."""
        pass

class ApproveApplicationView(ApplicationActionView):
    new_status = Application.Status.APPROVED
    def on_status_set(self, application):
        if application.application_type == Application.Type.TEAM:
            if application.team:
                application.contest.teams.add(application.team)
        elif application.application_type == Application.Type.JURY:
            application.contest.jurys.add(application.user)

class RejectApplicationView(ApplicationActionView):
    new_status = Application.Status.REJECTED

class ApplyToContestView(RedirectToRegisterMixin, View):
    http_method_names = ["post"]
    def post(self, request, pk, app_type):
        contest = get_object_or_404(Contest, pk=pk)
        if contest.status == Contest.Status.DRAFT:
            return HttpResponseForbidden("Cannot apply to a draft contest.")
        role_type = (
            Application.Type.PARTICIPANT
            if app_type == "participant"
            else Application.Type.JURY
        )
        Application.objects.get_or_create(
            user=request.user,
            contest=contest,
            application_type=role_type,
        )
        return redirect("contest_detail", pk=pk)

# Team views  (stubs – to be implemented)

class ViewTeamsView(RedirectToRegisterMixin, View):
    def get(self, request, pk):
        contest = get_object_or_404(Contest, pk=pk)
        return render(request, "app/teams.html", {"contest": contest, "teams": contest.teams.all()})

class TeamDetailView(RedirectToRegisterMixin, View):
    def get(self, request, pk, ck):
        contest = get_object_or_404(Contest, pk=pk)
        team = get_object_or_404(contest.teams, pk=ck)
        return render(request, "app/team.html", {"contest": contest, "team": team})

# Auth views

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)