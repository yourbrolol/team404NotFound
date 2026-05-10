from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from django.views import View
from django.views.generic import TemplateView

from app.forms import ProfileBioForm, UserSettingsForm
from app.models import Contest, LeaderboardEntry, JuryScore, Round, Team, JuryAssignment, Submission
from app.views.views_base import RedirectToRegisterMixin
from django.utils.translation import gettext as _


def _error_context(request, status_code, error_title, error_message):
    return {
        'status_code': status_code,
        'error_title': error_title,
        'error_message': error_message,
        'back_url': request.META.get('HTTP_REFERER') or reverse('dashboard'),
    }


def error_400_view(request, exception):
    return render(
        request,
        'app/errors/error.html',
        _error_context(request, 400, _('Bad request'), str(exception)),
        status=400,
    )


def error_403_view(request, exception):
    return render(
        request,
        'app/errors/error.html',
        _error_context(request, 403, _('Forbidden'), str(exception)),
        status=403,
    )


def error_404_view(request, exception):
    return render(
        request,
        'app/errors/error.html',
        _error_context(
            request,
            404,
            _('Page not found'),
            _('The page you were looking for does not exist.'),
        ),
        status=404,
    )


def error_500_view(request):
    return render(
        request,
        'app/errors/error.html',
        _error_context(
            request,
            500,
            _('Server error'),
            _('An internal server error occurred.'),
        ),
        status=500,
    )


class HomeView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/core/index.html"
    paginate_by = 4

    def get_context_data(self, **kwargs):
        contests = Contest.objects.exclude(status=Contest.Status.DRAFT)
        
        query = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "").upper()
        valid_statuses = {choice for choice, _ in Contest.Status.choices if choice != Contest.Status.DRAFT}
        
        if query:
            contests = contests.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        if status_filter in valid_statuses:
            contests = contests.filter(status=status_filter)
        else:
            status_filter = ""

        contests = contests.order_by("start_date", "name")
        
        # Pagination
        page_number = self.request.GET.get("page")
        paginator = Paginator(contests, self.paginate_by)
        page_obj = paginator.get_page(page_number)

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
            contests=page_obj,
            page_obj=page_obj,
            search_query=query,
            status_filter=status_filter,
            status_choices=[choice for choice in Contest.Status.choices if choice[0] != Contest.Status.DRAFT],
            user_contest=user_contest,
            user_team=user_team,
            active_round=active_round,
            **kwargs,
        )


class ProfileView(RedirectToRegisterMixin, View):
    def _build_jury_review_context(self, user):
        jury_scores = (
            JuryScore.objects.filter(jury_member=user)
            .select_related("contest", "team", "criterion")
            .order_by("-updated_at", "contest__name", "team__name")
        )

        pending_reviews = []
        seen_review_slots = set()

        assigned_contest_ids = set(
            JuryAssignment.objects.filter(jury_member=user).values_list("contest_id", flat=True)
        )
        judged_contest_ids = set()
        if user.is_jury():
            judged_contest_ids = set(
                user.judged_contests.exclude(status=Contest.Status.DRAFT).values_list("id", flat=True)
            )

        contest_ids = assigned_contest_ids | judged_contest_ids
        contests = (
            Contest.objects.filter(id__in=contest_ids)
            .exclude(status=Contest.Status.DRAFT)
            .prefetch_related("scoring_criteria")
            .order_by("name")
        )

        for contest in contests:
            criteria = list(contest.scoring_criteria.order_by("order", "name"))
            if not criteria:
                continue

            existing_pairs = set(
                JuryScore.objects.filter(contest=contest, jury_member=user).values_list("team_id", "criterion_id")
            )

            assignments = (
                JuryAssignment.objects.filter(contest=contest, jury_member=user)
                .select_related("team")
                .order_by("team__name")
            )
            if assignments.exists():
                teams_to_evaluate = [assignment.team for assignment in assignments]
            elif user.is_jury() and not JuryAssignment.objects.filter(contest=contest).exists():
                teams_to_evaluate = list(
                    Team.objects.filter(submissions__round__contest=contest).distinct().order_by("name")
                )
            else:
                teams_to_evaluate = []

            for team in teams_to_evaluate:
                if not Submission.objects.filter(round__contest=contest, team=team).exists():
                    continue

                slot_key = (contest.id, team.id)
                if slot_key in seen_review_slots:
                    continue
                seen_review_slots.add(slot_key)

                missing = [
                    criterion
                    for criterion in criteria
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

        return {
            "jury_scores": jury_scores,
            "pending_reviews": pending_reviews,
            "show_jury_reviews": user.is_jury() or bool(assigned_contest_ids) or jury_scores.exists(),
        }

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

        context.update(self._build_jury_review_context(user))

        if user.is_organizer():
            organized_contests = user.organized_contests.order_by("-start_date", "name")
            context.update(
                organized_contests=organized_contests,
                show_organizer_contests=True,
            )
        else:
            context["show_organizer_contests"] = False

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
            contests = Contest.objects.filter(
                Q(participants=user) | Q(teams__participants=user)
            ).exclude(status=Contest.Status.DRAFT).distinct()
        else:
            contests = Contest.objects.none()

        query = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "").upper()
        valid_statuses = {choice for choice, _ in Contest.Status.choices}

        if query:
            contests = contests.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(format__icontains=query)
                | Q(organizer__username__icontains=query)
            )

        if status_filter in valid_statuses:
            contests = contests.filter(status=status_filter)
        else:
            status_filter = ""

        contests = contests.order_by("-start_date", "name")

        return super().get_context_data(
            contests=contests,
            search_query=query,
            status_filter=status_filter,
            status_choices=Contest.Status.choices,
            **kwargs,
        )


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
