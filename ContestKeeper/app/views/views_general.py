from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from ..forms import ProfileBioForm, UserSettingsForm
from ..models import Contest, LeaderboardEntry, JuryScore, Round, Team
from .views_base import RedirectToRegisterMixin


class HomeView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/core/index.html"

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
            status_choices=[choice for choice in Contest.Status.choices if choice[0] != Contest.Status.DRAFT],
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
            "app/core/profile.html",
            self._build_context(request, form, saved=request.GET.get("saved") == "1"),
        )

    def post(self, request):
        form = ProfileBioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("/profile/?saved=1")
        return render(
            request,
            "app/core/profile.html",
            self._build_context(request, form, saved=False),
        )


class DashboardView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/core/dashboard.html"

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
        return render(request, "app/core/settings.html", {
            "form": form,
            "saved": request.GET.get("saved") == "1",
        })

    def post(self, request):
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("/settings/?saved=1")
        return render(request, "app/core/settings.html", {
            "form": form,
            "saved": False,
        })
