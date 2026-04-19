import csv

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from ..forms import ScoringCriterionForm

from ..leaderboard import LeaderboardComputer
from ..models import ContestEvaluationPhase, JuryScore, LeaderboardEntry, ScoringCriterion
from .views_team import AdminPermissionMixin, LeaderboardAccessMixin


class ContestLeaderboardView(LeaderboardAccessMixin, TemplateView):
    template_name = "app/leaderboards/leaderboard.html"

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
    template_name = "app/leaderboards/team_leaderboard_detail.html"

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
            {"criterion": criterion, "score": entry.category_scores.get(criterion.name, "")}
            for criterion in criteria
        ]
        breakdown_by_criterion = [
            {"criterion": criterion, "rows": entry.jury_breakdown.get(criterion.name, [])}
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
            return JsonResponse({"detail": "Leaderboard is not yet available. Evaluation is still in progress."}, status=400)

        entries = LeaderboardEntry.objects.filter(contest=self.contest).select_related("team").order_by("rank", "team__name")
        response_data = []
        for entry in entries:
            item = {
                "rank": entry.rank,
                "team": entry.team.name,
                "total_score": entry.total_score,
                "category_scores": entry.category_scores,
            }
            if self.request.user.is_staff or self.request.user == self.contest.organizer or self.request.user.is_jury() or (self.request.user.is_participant() and phase.show_jury_breakdown_to_participants):
                item["jury_breakdown"] = entry.jury_breakdown
            else:
                item["jury_breakdown"] = None

            if self.request.user.is_staff or self.request.user == self.contest.organizer:
                item["missing_scores"] = entry.missing_scores
                item["computation_complete"] = entry.computation_complete
            response_data.append(item)

        return JsonResponse(response_data, safe=False)


class AdminLeaderboardDashboardView(AdminPermissionMixin, TemplateView):
    template_name = "app/leaderboards/admin_leaderboard_dashboard.html"

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


class CriterionCreateView(AdminPermissionMixin, CreateView):
    model = ScoringCriterion
    form_class = ScoringCriterionForm
    template_name = "app/juries/criterion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        context["title"] = "Create Scoring Criterion"
        return context

    def form_valid(self, form):
        form.instance.contest = self.contest
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("admin_leaderboard_dashboard", kwargs={"pk": self.contest.pk})


class CriterionUpdateView(AdminPermissionMixin, UpdateView):
    model = ScoringCriterion
    form_class = ScoringCriterionForm
    template_name = "app/juries/criterion_form.html"
    pk_url_kwarg = "criterion_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        context["title"] = f"Edit Criterion: {self.object.name}"
        return context

    def get_success_url(self):
        return reverse_lazy("admin_leaderboard_dashboard", kwargs={"pk": self.contest.pk})


class CriterionDeleteView(AdminPermissionMixin, DeleteView):
    model = ScoringCriterion
    template_name = "app/announcements/announcement_confirm_delete.html"  # Reusing generic confirm delete
    pk_url_kwarg = "criterion_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        context["object_name"] = f"Scoring Criterion: {self.object.name}"
        context["cancel_url"] = reverse_lazy("admin_leaderboard_dashboard", kwargs={"pk": self.contest.pk})
        return context

    def get_success_url(self):
        return reverse_lazy("admin_leaderboard_dashboard", kwargs={"pk": self.contest.pk})
