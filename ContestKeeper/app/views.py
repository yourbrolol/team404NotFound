import csv

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView, DeleteView

from .forms import UserRegistrationForm, ContestForm, UserSettingsForm, ProfileBioForm
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
)

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

class ProfileView(RedirectToRegisterMixin, View):
    def get(self, request):
        form = ProfileBioForm(instance=request.user)
        return render(request, "app/profile.html", {
            "form": form,
            "saved": request.GET.get("saved") == "1",
        })

    def post(self, request):
        form = ProfileBioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("/profile/?saved=1")
        return render(request, "app/profile.html", {
            "form": form,
            "saved": False,
        })

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
        
        logger = logging.getLogger(__name__)
        logger.info(f"Round {round_obj.id} ({round_obj.title}) activated at {timezone.now()} by {request.user.username}")
        
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
        
        logger = logging.getLogger(__name__)
        logger.info(f"Round {round_obj.id} ({round_obj.title}) submissions closed manually at {timezone.now()}")
        
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
