from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView

from ..forms import ScheduleEventForm
from ..models import JuryScore, LeaderboardEntry, ScheduleEvent, Submission
from ..services import generate_schedule_from_rounds
from .views_base import ContestContextMixin, OrganizerRequiredMixin


class OrganizerAnalyticsView(OrganizerRequiredMixin, TemplateView):
    template_name = "app/analytics.html"

    def get_context_data(self, **kwargs):
        from django.db.models import Avg

        context = super().get_context_data(**kwargs)
        contest = self.contest
        teams_count = contest.teams.count()
        jury_members = contest.jurys.all()
        criteria = contest.scoring_criteria.all().order_by("order")
        entries = LeaderboardEntry.objects.filter(contest=contest)

        submission_stats = []
        max_bar_width = 300
        bar_height = 24
        bar_gap = 8
        for i, r in enumerate(contest.rounds.all().order_by("order")):
            submitted = r.submissions.count()
            pct = round(submitted / teams_count * 100, 1) if teams_count else 0
            submission_stats.append({
                "name": r.title,
                "submitted": submitted,
                "total": teams_count,
                "pct": pct,
                "bar_y": i * (bar_height + bar_gap),
                "bar_width": int(pct * (max_bar_width / 100)),
            })

        score_stats = []
        for i, c in enumerate(criteria):
            avg_score = JuryScore.objects.filter(contest=contest, criterion=c).aggregate(avg=Avg("score"))["avg"] or 0
            pct = round(float(avg_score) / float(c.max_score) * 100, 1) if c.max_score else 0
            score_stats.append({
                "name": c.name,
                "avg": round(float(avg_score), 1),
                "max": c.max_score,
                "pct": pct,
                "bar_y": i * (bar_height + bar_gap),
                "bar_width": int(pct * (max_bar_width / 100)),
            })

        jury_stats = []
        criteria_count = criteria.count()
        expected_per_jury = teams_count * criteria_count
        for jury in jury_members:
            actual = JuryScore.objects.filter(contest=contest, jury_member=jury).count()
            pct = round(actual / expected_per_jury * 100, 1) if expected_per_jury > 0 else 0
            jury_stats.append({
                "username": jury.username,
                "actual": actual,
                "expected": expected_per_jury,
                "percent": pct,
            })

        distribution = [0] * 10
        max_possible = sum(c.max_score * c.weight for c in criteria)
        for entry in entries:
            score = float(entry.total_score)
            if max_possible > 0:
                bucket = min(int((score / float(max_possible)) * 10), 9)
                distribution[bucket] += 1

        context.update({
            "total_teams": teams_count,
            "total_jury": jury_members.count(),
            "total_submissions": Submission.objects.filter(round__contest=contest).count(),
            "total_evaluations": JuryScore.objects.filter(contest=contest).count(),
            "submission_stats": submission_stats,
            "submission_svg_height": len(submission_stats) * (bar_height + bar_gap),
            "score_stats": score_stats,
            "score_svg_height": len(score_stats) * (bar_height + bar_gap),
            "jury_stats": jury_stats,
            "distribution": distribution,
            "max_count": max(distribution) if distribution else 0,
            "max_possible": float(max_possible),
            "entries_count": entries.count(),
        })
        return context


class ScheduleView(ContestContextMixin, ListView):
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
