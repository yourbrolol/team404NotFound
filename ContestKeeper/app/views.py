import csv

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView, DeleteView

from .forms import (
    UserRegistrationForm, ContestForm, UserSettingsForm, ProfileBioForm,
    AnnouncementForm, ScheduleEventForm
)
from .leaderboard import LeaderboardComputer
from .models import (
    Application,
    Contest,
    ContestEvaluationPhase,
    JuryScore,
    LeaderboardEntry,
    Round,
    ScoringCriterion,
    Team,
    User,
    Notification,
    Announcement,
    ScheduleEvent,
)
from .services import notify_user, notify_contest_participants, notify_contest_jury, generate_schedule_from_rounds

# ── Mixins ────────────────────────────────────────────────────────────────────

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

# ── Utility ───────────────────────────────────────────────────────────────────

def _make_template_view(template_name):
    """Factory: returns a login-required TemplateView for the given template."""
    return type("TemplateView", (RedirectToRegisterMixin, TemplateView), {"template_name": template_name})

# ── General views ─────────────────────────────────────────────────────────────

class HomeView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/index.html"

    def get_context_data(self, **kwargs):
        contests = Contest.objects.exclude(status=Contest.Status.DRAFT)
        status_filter = self.request.GET.get("status", "")
        valid_statuses = {choice for choice, _ in Contest.Status.choices if choice != Contest.Status.DRAFT}
        if status_filter in valid_statuses:
            contests = contests.filter(status=status_filter)
        else:
            status_filter = ""

        user_contest = None
        user_team = None
        active_round = None

        user = self.request.user
        if user.is_authenticated and user.is_participant():
            contest_priority = [
                Contest.Status.RUNNING,
                Contest.Status.REGISTRATION,
                Contest.Status.FINISHED,
            ]
            for status in contest_priority:
                user_team = (
                    Team.objects.filter(participants=user, teams_in_contests__status=status)
                    .select_related("captain")
                    .prefetch_related("teams_in_contests")
                    .order_by("name")
                    .first()
                )
                if user_team:
                    user_contest = (
                        user_team.teams_in_contests.exclude(status=Contest.Status.DRAFT)
                        .filter(status=status)
                        .order_by("start_date")
                        .first()
                    )
                    if user_contest:
                        break

            if user_contest:
                active_round = (
                    user_contest.rounds.filter(status=Round.Status.ACTIVE)
                    .order_by("deadline", "order")
                    .first()
                )

        return super().get_context_data(
            contests=contests.order_by("start_date", "name"),
            status_filter=status_filter,
            status_choices=[
                choice for choice in Contest.Status.choices if choice[0] != Contest.Status.DRAFT
            ],
            user_contest=user_contest,
            user_team=user_team,
            active_round=active_round,
            **kwargs,
        )

class ProfileView(RedirectToRegisterMixin, View):
    def _build_context(self, request, form, saved=False):
        user = request.user
        context = {
            "form": form,
            "saved": saved,
        }

        if user.is_participant():
            teams = (
                Team.objects.filter(participants=user)
                .prefetch_related("teams_in_contests")
                .order_by("name")
                .distinct()
            )
            captained_team_ids = set(user.captained_teams.values_list("id", flat=True))
            participant_team_rows = []
            for team in teams:
                contests = list(team.teams_in_contests.exclude(status=Contest.Status.DRAFT).order_by("-start_date", "name"))
                if contests:
                    for contest in contests:
                        participant_team_rows.append(
                            {
                                "team": team,
                                "contest": contest,
                                "is_captain": team.id in captained_team_ids,
                            }
                        )
                else:
                    participant_team_rows.append(
                        {
                            "team": team,
                            "contest": None,
                            "is_captain": team.id in captained_team_ids,
                        }
                    )

            leaderboard_entries = (
                LeaderboardEntry.objects.filter(team__participants=user)
                .select_related("contest", "team")
                .order_by("contest__start_date", "rank", "team__name")
            )

            context.update(
                participant_team_rows=participant_team_rows,
                leaderboard_entries=leaderboard_entries,
            )

        elif user.is_jury():
            jury_scores = (
                JuryScore.objects.filter(jury_member=user)
                .select_related("contest", "team", "criterion")
                .order_by("-updated_at", "contest__name", "team__name")
            )
            pending_reviews = []
            judged_contests = user.judged_contests.exclude(status=Contest.Status.DRAFT).prefetch_related("teams", "scoring_criteria")
            for contest in judged_contests:
                existing_pairs = set(
                    JuryScore.objects.filter(contest=contest, jury_member=user).values_list("team_id", "criterion_id")
                )
                for team in contest.teams.order_by("name"):
                    missing = [
                        criterion
                        for criterion in contest.scoring_criteria.order_by("order", "name")
                        if (team.id, criterion.id) not in existing_pairs
                    ]
                    if missing:
                        pending_reviews.append(
                            {
                                "contest": contest,
                                "team": team,
                                "missing_criteria": missing,
                            }
                        )

            context.update(
                jury_scores=jury_scores,
                pending_reviews=pending_reviews,
            )

        elif user.is_organizer():
            organized_contests = user.organized_contests.order_by("-start_date", "name")
            context.update(organized_contests=organized_contests)

        return context

    def get(self, request):
        form = ProfileBioForm(instance=request.user)
        return render(
            request,
            "app/profile.html",
            self._build_context(request, form, saved=request.GET.get("saved") == "1"),
        )

    def post(self, request):
        form = ProfileBioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("/profile/?saved=1")
        return render(
            request,
            "app/profile.html",
            self._build_context(request, form, saved=False),
        )

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
                            
            if action == "reject":
                application.status = Application.Status.REJECTED
                application.save()
            
            # TASK-20: Notify applicant
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

# ── Announcement views ────────────────────────────────────────────────────────

class AnnouncementListView(LoginRequiredMixin, ContestContextMixin, ListView):
    model = Announcement
    template_name = "app/announcements.html"
    context_object_name = "announcements"

    def get_queryset(self):
        return Announcement.objects.filter(contest=self.contest)

class AnnouncementCreateView(OrganizerRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "app/announcement_form.html"

    def form_valid(self, form):
        form.instance.contest = self.contest
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        if form.cleaned_data.get("notify_participants"):
            notify_contest_participants(
                self.contest,
                Notification.Type.ANNOUNCEMENT,
                f"New announcement: {form.instance.title}",
                form.instance.content[:200] + "...",
                link=reverse("announcement_list", kwargs={"pk": self.contest.pk})
            )
        messages.success(self.request, "Announcement published successfully.")
        return response

    def get_success_url(self):
        return reverse("announcement_list", kwargs={"pk": self.contest.pk})

class AnnouncementDeleteView(OrganizerRequiredMixin, DeleteView):
    model = Announcement
    template_name = "app/announcement_confirm_delete.html"

    def get_success_url(self):
        return reverse("announcement_list", kwargs={"pk": self.contest.pk})

# ── Analytics views ──────────────────────────────────────────────────────────

class OrganizerAnalyticsView(OrganizerRequiredMixin, TemplateView):
    template_name = "app/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contest = self.contest
        from .models import Round, Submission, JuryScore, LeaderboardEntry
        from django.db.models import Avg

        # 1. Summary Numbers
        teams_count = contest.teams.count()
        jury_members = contest.jurys.all()
        jury_count = jury_members.count()
        submissions_count = Submission.objects.filter(round__contest=contest).count()
        leaderboard_entries_count = LeaderboardEntry.objects.filter(contest=contest).count()

        # 2. Submission rate per round
        rounds = contest.rounds.all().order_by('order')
        submission_stats = []
        max_bar_width = 300
        bar_height = 24
        bar_gap = 8

        for i, r in enumerate(rounds):
            submitted = r.submissions.count()
            pct = round(submitted / teams_count * 100, 1) if teams_count else 0
            submission_stats.append({
                'name': r.title,
                'submitted': submitted,
                'total': teams_count,
                'pct': pct,
                'bar_y': i * (bar_height + bar_gap),
                'bar_width': int(pct * (max_bar_width / 100)),
            })

        # 3. Average scores radar/bar chart (per criterion)
        criteria = contest.scoring_criteria.all().order_by('order')
        score_stats = []
        for i, c in enumerate(criteria):
            avg_score = JuryScore.objects.filter(contest=contest, criterion=c).aggregate(avg=Avg('score'))['avg'] or 0
            pct = round(float(avg_score) / float(c.max_score) * 100, 1) if c.max_score else 0
            score_stats.append({
                'name': c.name,
                'avg': round(float(avg_score), 1),
                'max': c.max_score,
                'pct': pct,
                'bar_y': i * (bar_height + bar_gap),
                'bar_width': int(pct * (max_bar_width / 100)),
            })

        # 4. Jury progress
        criteria_count = criteria.count()
        expected_per_jury = teams_count * criteria_count
        jury_stats = []
        for jury in jury_members:
            actual = JuryScore.objects.filter(contest=contest, jury_member=jury).count()
            pct = round(actual / expected_per_jury * 100, 1) if expected_per_jury > 0 else 0
            jury_stats.append({
                "username": jury.username,
                "actual": actual,
                "expected": expected_per_jury,
                "percent": pct,
            })

        # 5. Score Distribution (existing)
        entries = LeaderboardEntry.objects.filter(contest=contest)
        distribution = [0] * 10
        max_possible = sum(c.max_score * c.weight for c in criteria)
        
        for entry in entries:
            score = float(entry.total_score)
            if max_possible > 0:
                bucket = min(int((score / float(max_possible)) * 10), 9)
                distribution[bucket] += 1
        
        max_count = max(distribution) if distribution else 0

        context.update({
            "total_teams": teams_count,
            "total_jury": jury_count,
            "total_submissions": submissions_count,
            "total_evaluations": JuryScore.objects.filter(contest=contest).count(),
            "submission_stats": submission_stats,
            "submission_svg_height": len(submission_stats) * (bar_height + bar_gap),
            "score_stats": score_stats,
            "score_svg_height": len(score_stats) * (bar_height + bar_gap),
            "jury_stats": jury_stats,
            "distribution": distribution,
            "max_count": max_count,
            "max_possible": float(max_possible),
            "entries_count": entries.count(),
        })
        return context

class ScheduleView(LoginRequiredMixin, ContestContextMixin, ListView):
    model = ScheduleEvent
    template_name = "app/schedule.html"
    context_object_name = "events"

    def get_queryset(self):
        return ScheduleEvent.objects.filter(contest=self.contest)

class ScheduleEventCreateView(OrganizerRequiredMixin, CreateView):
    model = ScheduleEvent
    form_class = ScheduleEventForm
    template_name = "app/schedule_event_form.html"

    def form_valid(self, form):
        form.instance.contest = self.contest
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("schedule", kwargs={"pk": self.contest.pk})

class ScheduleEventDeleteView(OrganizerRequiredMixin, DeleteView):
    model = ScheduleEvent
    template_name = "app/schedule_event_confirm_delete.html"

    def get_success_url(self):
        return reverse("schedule", kwargs={"pk": self.contest.pk})

class RegenerateScheduleView(OrganizerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        count = generate_schedule_from_rounds(self.contest)
        messages.success(request, f"Schedule regenerated from {count} round events.")
        return redirect("schedule", pk=self.contest.pk)

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

class TeamApplicationsView(RedirectToRegisterMixin, ListView):
    template_name = "app/teams_applications.html"
    context_object_name = "applications"
    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return self.contest.contest_apps.filter(application_type=Application.Type.TEAM)
    def get_context_data(self, **kwargs):
        return super().get_context_data(contest=self.contest, **kwargs)

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

class ContestLeaderboardView(LeaderboardAccessMixin, TemplateView):
    template_name = "app/leaderboard.html"

    def get_context_data(self, **kwargs):
        phase, _ = ContestEvaluationPhase.objects.get_or_create(
            contest=self.contest,
            defaults={
                "status": ContestEvaluationPhase.Status.NOT_STARTED,
                "trigger_type": ContestEvaluationPhase.TriggerType.AUTO,
            },
        )

        if phase.status != ContestEvaluationPhase.Status.COMPLETED:
            if LeaderboardComputer.is_ready_for_auto_activation(self.contest):
                LeaderboardComputer.compute_leaderboard(
                    self.contest,
                    trigger_type=ContestEvaluationPhase.TriggerType.AUTO,
                )
                phase.refresh_from_db()

        if phase.status != ContestEvaluationPhase.Status.COMPLETED:
            return super().get_context_data(
                contest=self.contest,
                phase=phase,
                leaderboard_available=False,
                not_available_message="Leaderboard is not yet available. Evaluation is still in progress.",
            )

        raw_entries = LeaderboardEntry.objects.filter(contest=self.contest).select_related("team").order_by("rank", "team__name")
        criteria = ScoringCriterion.objects.filter(contest=self.contest).order_by("order")
        entries = [
            {
                "entry": entry,
                "category_values": [entry.category_scores.get(criterion.name, "") for criterion in criteria],
            }
            for entry in raw_entries
        ]
        can_view_missing = self.request.user.is_staff or self.request.user == self.contest.organizer
        show_jury_breakdown = (
            self.request.user.is_staff
            or self.request.user == self.contest.organizer
            or self.request.user.is_jury()
            or (self.request.user.is_participant() and phase.show_jury_breakdown_to_participants)
        )

        return super().get_context_data(
            contest=self.contest,
            phase=phase,
            leaderboard_available=True,
            entries=entries,
            criteria=criteria,
            show_jury_breakdown=show_jury_breakdown,
            can_view_missing=can_view_missing,
            overall_missing=LeaderboardComputer.get_missing_scores(self.contest),
        )

class TeamDetailLeaderboardView(LeaderboardAccessMixin, TemplateView):
    template_name = "app/team_leaderboard_detail.html"

    def get(self, request, *args, **kwargs):
        self.team = get_object_or_404(self.contest.teams, pk=kwargs["team_pk"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        phase, _ = ContestEvaluationPhase.objects.get_or_create(
            contest=self.contest,
            defaults={
                "status": ContestEvaluationPhase.Status.NOT_STARTED,
                "trigger_type": ContestEvaluationPhase.TriggerType.AUTO,
            },
        )

        if phase.status != ContestEvaluationPhase.Status.COMPLETED:
            if LeaderboardComputer.is_ready_for_auto_activation(self.contest):
                LeaderboardComputer.compute_leaderboard(
                    self.contest,
                    trigger_type=ContestEvaluationPhase.TriggerType.AUTO,
                )
                phase.refresh_from_db()

        if phase.status != ContestEvaluationPhase.Status.COMPLETED:
            return super().get_context_data(
                contest=self.contest,
                team=self.team,
                phase=phase,
                leaderboard_available=False,
                not_available_message="Leaderboard is not yet available. Evaluation is still in progress.",
            )

        entry = LeaderboardEntry.objects.filter(contest=self.contest, team=self.team).first()
        if entry is None:
            return super().get_context_data(
                contest=self.contest,
                team=self.team,
                phase=phase,
                leaderboard_available=False,
                not_available_message="Leaderboard is not yet available. Evaluation is still in progress.",
            )

        criteria = ScoringCriterion.objects.filter(contest=self.contest).order_by("order")
        category_breakdown = [
            {
                "criterion": criterion,
                "score": entry.category_scores.get(criterion.name, ""),
            }
            for criterion in criteria
        ]
        breakdown_by_criterion = [
            {
                "criterion": criterion,
                "rows": entry.jury_breakdown.get(criterion.name, []),
            }
            for criterion in criteria
        ]
        show_jury_breakdown = (
            self.request.user.is_staff
            or self.request.user == self.contest.organizer
            or self.request.user.is_jury()
            or (self.request.user.is_participant() and phase.show_jury_breakdown_to_participants)
        )
        jury_breakdown_message = None
        if self.request.user.is_participant() and not phase.show_jury_breakdown_to_participants:
            jury_breakdown_message = "Jury breakdown is not available for participants at this time."

        return super().get_context_data(
            contest=self.contest,
            team=self.team,
            entry=entry,
            phase=phase,
            category_breakdown=category_breakdown,
            breakdown_by_criterion=breakdown_by_criterion,
            leaderboard_available=True,
            show_jury_breakdown=show_jury_breakdown,
            jury_breakdown_message=jury_breakdown_message,
            can_view_missing=(self.request.user.is_staff or self.request.user == self.contest.organizer),
        )

class LeaderboardAPIView(LeaderboardAccessMixin, View):
    def get(self, request, *args, **kwargs):
        phase, _ = ContestEvaluationPhase.objects.get_or_create(
            contest=self.contest,
            defaults={
                "status": ContestEvaluationPhase.Status.NOT_STARTED,
                "trigger_type": ContestEvaluationPhase.TriggerType.AUTO,
            },
        )

        if phase.status != ContestEvaluationPhase.Status.COMPLETED:
            if LeaderboardComputer.is_ready_for_auto_activation(self.contest):
                LeaderboardComputer.compute_leaderboard(self.contest, trigger_type=ContestEvaluationPhase.TriggerType.AUTO)
                phase.refresh_from_db()

        if phase.status != ContestEvaluationPhase.Status.COMPLETED:
            return JsonResponse({
                "detail": "Leaderboard is not yet available. Evaluation is still in progress."
            }, status=400)

        entries = LeaderboardEntry.objects.filter(contest=self.contest).select_related("team").order_by("rank", "team__name")
        response_data = []
        for entry in entries:
            item = {
                "rank": entry.rank,
                "team": entry.team.name,
                "total_score": entry.total_score,
                "category_scores": entry.category_scores,
            }
            if self.request.user.is_staff or self.request.user == self.contest.organizer or self.request.user.is_jury():
                item["jury_breakdown"] = entry.jury_breakdown
            elif self.request.user.is_participant() and phase.show_jury_breakdown_to_participants:
                item["jury_breakdown"] = entry.jury_breakdown
            else:
                item["jury_breakdown"] = None

            if self.request.user.is_staff or self.request.user == self.contest.organizer:
                item["missing_scores"] = entry.missing_scores
                item["computation_complete"] = entry.computation_complete
            response_data.append(item)

        return JsonResponse(response_data, safe=False)

class AdminLeaderboardDashboardView(AdminPermissionMixin, TemplateView):
    template_name = "app/admin_leaderboard_dashboard.html"

    def get_context_data(self, **kwargs):
        phase, _ = ContestEvaluationPhase.objects.get_or_create(
            contest=self.contest,
            defaults={
                "status": ContestEvaluationPhase.Status.NOT_STARTED,
                "trigger_type": ContestEvaluationPhase.TriggerType.AUTO,
            },
        )

        criteria = ScoringCriterion.objects.filter(contest=self.contest).order_by("order")
        total_expected = criteria.count() * self.contest.jurys.count() * self.contest.teams.count()
        submitted = JuryScore.objects.filter(contest=self.contest).count()
        progress_percent = 0 if total_expected == 0 else min(100, round(submitted * 100.0 / total_expected, 2))
        missing_scores = LeaderboardComputer.get_missing_scores(self.contest)
        raw_entries = LeaderboardEntry.objects.filter(contest=self.contest).select_related("team").order_by("rank", "team__name")
        entries_data = [
            {
                "entry": entry,
                "category_values": [entry.category_scores.get(criterion.name, "") for criterion in criteria],
            }
            for entry in raw_entries
        ]

        return super().get_context_data(
            contest=self.contest,
            phase=phase,
            criteria=criteria,
            submitted=submitted,
            expected=total_expected,
            progress_percent=progress_percent,
            missing_scores=missing_scores,
            entries=entries_data,
            show_jury_breakdown_to_participants=phase.show_jury_breakdown_to_participants,
        )

class AdminFinishEvaluationView(AdminPermissionMixin, View):
    def post(self, request, *args, **kwargs):
        LeaderboardComputer.compute_leaderboard(
            self.contest,
            force_complete=True,
            trigger_type=ContestEvaluationPhase.TriggerType.MANUAL,
        )
        return redirect("admin_leaderboard_dashboard", pk=self.contest.pk)

class AdminToggleJuryBreakdownView(AdminPermissionMixin, View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        phase, _ = ContestEvaluationPhase.objects.get_or_create(
            contest=self.contest,
            defaults={
                "status": ContestEvaluationPhase.Status.NOT_STARTED,
                "trigger_type": ContestEvaluationPhase.TriggerType.AUTO,
            },
        )
        phase.show_jury_breakdown_to_participants = action == "show"
        phase.save()
        return redirect("admin_leaderboard_dashboard", pk=self.contest.pk)

class AdminRecalculateLeaderboardView(AdminPermissionMixin, View):
    def post(self, request, *args, **kwargs):
        LeaderboardComputer.compute_leaderboard(
            self.contest,
            force_complete=False,
            preserve_completed_at=True,
        )
        return redirect("admin_leaderboard_dashboard", pk=self.contest.pk)

class AdminExportLeaderboardView(AdminPermissionMixin, View):
    def get(self, request, *args, **kwargs):
        export_format = request.GET.get("format", "json").lower()
        if export_format == "csv":
            header, rows = LeaderboardComputer.export_csv(self.contest)
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f"attachment; filename=contest_{self.contest.pk}_leaderboard.csv"
            writer = csv.writer(response)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
            return response

        data = LeaderboardComputer.export_data(self.contest, user_is_admin=True)
        return JsonResponse(data, safe=False)

class ExportEvaluationsCSVView(AdminPermissionMixin, View):
    def get(self, request, *args, **kwargs):
        header, rows = LeaderboardComputer.export_evaluations_csv(self.contest)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename=contest_{self.contest.pk}_evaluations.csv"
        writer = csv.writer(response)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
        return response

class ExportTeamsCSVView(AdminPermissionMixin, View):
    def get(self, request, *args, **kwargs):
        header, rows = LeaderboardComputer.export_teams_csv(self.contest)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename=contest_{self.contest.pk}_teams.csv"
        writer = csv.writer(response)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
        return response

# ── Round Management views ────────────────────────────────────────────────────

class RoundListView(OrganizerRequiredMixin, ListView):
    """List all rounds for a contest (organizer only)."""
    template_name = "app/round_list.html"
    context_object_name = "rounds"
    
    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return Round.objects.filter(contest=self.contest).order_by("order")
    
    def get_context_data(self, **kwargs):
        return super().get_context_data(contest=self.contest, **kwargs)

class RoundCreateView(OrganizerRequiredMixin, CreateView):
    """Create a new round for a contest."""
    model = Round
    template_name = "app/round_form.html"
    fields = ["title", "description", "tech_requirements", "must_have", "start_time", "deadline", "materials"]
    
    def get_context_data(self, **kwargs):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return super().get_context_data(contest=self.contest, **kwargs)
    
    def form_valid(self, form):
        from django.utils import timezone
        obj = form.save(commit=False)
        obj.contest_id = self.kwargs["pk"]
        
        # Validation
        if obj.deadline <= obj.start_time:
            form.add_error("deadline", "Deadline must be after start time.")
            return self.form_invalid(form)
        
        if obj.deadline < timezone.now():
            form.add_error("deadline", "Deadline cannot be in the past.")
            return self.form_invalid(form)
        
        if not obj.must_have or len(obj.must_have) == 0:
            form.add_error("must_have", "Must have at least one checklist item.")
            return self.form_invalid(form)
        
        # Auto-assign order
        last_round = Round.objects.filter(contest=obj.contest).order_by("-order").first()
        obj.order = (last_round.order + 1) if last_round else 1
        obj.created_by = self.request.user
        obj.status = Round.Status.DRAFT
        obj.save()
        
        return redirect("contest_rounds", pk=obj.contest.pk)

class RoundEditView(OrganizerRequiredMixin, View):
    """Edit a round (only allowed when status=DRAFT)."""
    
    def get(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)
        
        if round_obj.status != Round.Status.DRAFT:
            return HttpResponseForbidden("Cannot edit a round that is not in DRAFT status.")
        
        return render(request, "app/round_form.html", {"contest": contest, "round": round_obj})
    
    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)
        
        if round_obj.status != Round.Status.DRAFT:
            return HttpResponseForbidden("Cannot edit a round that is not in DRAFT status.")
        
        round_obj.title = request.POST.get("title", round_obj.title)
        round_obj.description = request.POST.get("description", round_obj.description)
        round_obj.tech_requirements = request.POST.get("tech_requirements", round_obj.tech_requirements)
        
        try:
            import json
            must_have = json.loads(request.POST.get("must_have", "[]"))
            if not must_have or len(must_have) == 0:
                return render(request, "app/round_form.html", {
                    "contest": contest,
                    "round": round_obj,
                    "error": "Must have at least one checklist item."
                })
            round_obj.must_have = must_have
        except:
            return render(request, "app/round_form.html", {
                "contest": contest,
                "round": round_obj,
                "error": "Invalid must_have format."
            })
        
        # Update timeline if provided
        if request.POST.get("start_time"):
            from django.utils.dateparse import parse_datetime
            start_time = parse_datetime(request.POST.get("start_time"))
            if start_time:
                # Make timezone-aware if not already
                if timezone.is_naive(start_time):
                    start_time = timezone.make_aware(start_time)
                round_obj.start_time = start_time
        
        if request.POST.get("deadline"):
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(request.POST.get("deadline"))
            if deadline:
                # Make timezone-aware if not already
                if timezone.is_naive(deadline):
                    deadline = timezone.make_aware(deadline)
                
                if deadline <= round_obj.start_time:
                    return render(request, "app/round_form.html", {
                        "contest": contest,
                        "round": round_obj,
                        "error": "Deadline must be after start time."
                    })
                if deadline < timezone.now():
                    return render(request, "app/round_form.html", {
                        "contest": contest,
                        "round": round_obj,
                        "error": "Deadline cannot be in the past."
                    })
                round_obj.deadline = deadline
        
        try:
            materials = json.loads(request.POST.get("materials", "[]"))
            round_obj.materials = materials
        except:
            pass
        
        round_obj.save()
        return redirect("contest_rounds", pk=contest.pk)

class RoundActivateView(OrganizerRequiredMixin, View):
    """Activate a round (transition from DRAFT to ACTIVE)."""
    
    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        import logging
        
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)
        
        if round_obj.status != Round.Status.DRAFT:
            return HttpResponseForbidden(f"Can only activate DRAFT rounds. Current status: {round_obj.status}")
        
        round_obj.status = Round.Status.ACTIVE
        round_obj.save()
        
        logger.info(f"Round {round_obj.id} ({round_obj.title}) activated at {timezone.now()} by {request.user.username}")
        
        # TASK-20: Notify participants
        notify_contest_participants(
            contest,
            Notification.Type.ROUND_STARTED,
            f"Round started: {round_obj.title}",
            f"New round '{round_obj.title}' is now active in '{contest.name}'. Deadline: {round_obj.deadline.strftime('%b %d, %H:%M')}.",
            link=reverse("round_detail_team", kwargs={"pk": contest.pk, "round_id": round_obj.pk})
        )
        
        return redirect("contest_rounds", pk=contest.pk)

class RoundCloseSubmissionsView(OrganizerRequiredMixin, View):
    """Close submissions for a round (manual override)."""
    
    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        import logging
        
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)
        
        if round_obj.status != Round.Status.ACTIVE:
            return HttpResponseForbidden("Can only close submissions for ACTIVE rounds.")
        
        round_obj.status = Round.Status.SUBMISSION_CLOSED
        round_obj.save()
        
        logger.info(f"Round {round_obj.id} ({round_obj.title}) submissions closed manually at {timezone.now()}")
        
        # TASK-20: Notify participants and jury
        notify_contest_participants(
            contest,
            Notification.Type.SUBMISSIONS_CLOSED,
            f"Submissions closed: {round_obj.title}",
            f"Submissions for round '{round_obj.title}' in '{contest.name}' are now closed.",
            link=reverse("round_detail_team", kwargs={"pk": contest.pk, "round_id": round_obj.pk})
        )
        notify_contest_jury(
            contest,
            Notification.Type.SUBMISSIONS_CLOSED,
            f"Submissions closed: {round_obj.title}",
            f"Submissions for round '{round_obj.title}' in '{contest.name}' are closed. You can now start evaluations.",
            link=reverse("dashboard")
        )
        
        return redirect("contest_rounds", pk=contest.pk)

class RoundExtendDeadlineView(OrganizerRequiredMixin, View):
    """Extend the deadline for an ACTIVE round."""
    
    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime
        import logging
        
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)
        
        if round_obj.status != Round.Status.ACTIVE:
            return HttpResponseForbidden("Can only extend deadline for ACTIVE rounds.")
        
        new_deadline_str = request.POST.get("new_deadline")
        if not new_deadline_str:
            return render(request, "app/round_extend_deadline.html", {
                "contest": contest,
                "round": round_obj,
                "error": "New deadline is required."
            })
        
        # Parse the datetime from datetime-local input
        new_deadline = parse_datetime(new_deadline_str)
        if not new_deadline:
            return render(request, "app/round_extend_deadline.html", {
                "contest": contest,
                "round": round_obj,
                "error": "Invalid datetime format."
            })
        
        # Make timezone-aware if not already
        if timezone.is_naive(new_deadline):
            new_deadline = timezone.make_aware(new_deadline)
        
        if new_deadline < timezone.now():
            return render(request, "app/round_extend_deadline.html", {
                "contest": contest,
                "round": round_obj,
                "error": "New deadline cannot be in the past."
            })
        
        old_deadline = round_obj.deadline
        round_obj.deadline = new_deadline
        round_obj.save()
        
        logger = logging.getLogger(__name__)
        logger.info(f"Round {round_obj.id} deadline extended from {old_deadline} to {new_deadline} by {request.user.username}")
        
        return redirect("contest_rounds", pk=contest.pk)

# ── Team Views: Contest Rounds ────────────────────────────────────────────────

class ContestRoundsTeamView(RedirectToRegisterMixin, TemplateView):
    """Teams view all ACTIVE and EVALUATED rounds for a contest."""
    template_name = "app/contest_rounds_team.html"
    
    def get_context_data(self, **kwargs):
        from django.utils import timezone
        contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        now = timezone.now()
        
        # Show ACTIVE, SUBMISSION_CLOSED (message only), and EVALUATED rounds
        active_rounds = Round.objects.filter(
            contest=contest, 
            status=Round.Status.ACTIVE,
            start_time__lte=now
        ).order_by("order")
        
        closed_rounds = Round.objects.filter(
            contest=contest,
            status=Round.Status.SUBMISSION_CLOSED
        ).order_by("order")
        
        evaluated_rounds = Round.objects.filter(
            contest=contest,
            status=Round.Status.EVALUATED
        ).order_by("order")
        
        return super().get_context_data(
            contest=contest,
            active_rounds=active_rounds,
            closed_rounds=closed_rounds,
            evaluated_rounds=evaluated_rounds,
        )

class RoundDetailTeamView(RedirectToRegisterMixin, TemplateView):
    """Team view of a single round detail."""
    template_name = "app/round_detail_team.html"
    
    def get_context_data(self, **kwargs):
        from django.utils import timezone
        contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=self.kwargs["round_id"], contest=contest)
        
        # Only show if ACTIVE, SUBMISSION_CLOSED, or EVALUATED
        if round_obj.status == Round.Status.DRAFT:
            raise Http404("This round is not available yet.")
        
        now = timezone.now()
        is_active = round_obj.status == Round.Status.ACTIVE and round_obj.start_time <= now
        is_open = is_active and round_obj.deadline > now
        time_remaining = round_obj.time_remaining() if is_active else None
        
        return super().get_context_data(
            contest=contest,
            round=round_obj,
            is_active=is_active,
            is_open=is_open,
            time_remaining=time_remaining,
        )

# ── Auth views ────────────────────────────────────────────────────────────────────────────────

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

# ── Notification views ────────────────────────────────────────────────────────

class NotificationListView(RedirectToRegisterMixin, ListView):
    model = Notification
    template_name = "app/notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return self.request.user.notifications.all()

class MarkNotificationReadView(RedirectToRegisterMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(request.user.notifications, pk=pk)
        notification.is_read = True
        notification.save()
        if notification.link:
            return redirect(notification.link)
        return redirect("notification_list")

class MarkAllReadView(RedirectToRegisterMixin, View):
    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect("notification_list")
