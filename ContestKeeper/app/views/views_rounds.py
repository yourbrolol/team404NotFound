import json
import logging

from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, DetailView

from django.utils.translation import gettext as _
from app.models import Contest, Notification, Round, Submission
from app.services import notify_contest_jury, notify_contest_participants
from app.views.views_base import OrganizerRequiredMixin, RedirectToRegisterMixin, ContestContextMixin


class RoundListView(OrganizerRequiredMixin, ListView):
    template_name = "app/rounds/round_list.html"
    context_object_name = "rounds"

    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return Round.objects.filter(contest=self.contest).order_by("order")

    def get_context_data(self, **kwargs):
        return super().get_context_data(contest=self.contest, **kwargs)


class RoundCreateView(OrganizerRequiredMixin, CreateView):
    model = Round
    template_name = "app/rounds/round_form.html"
    fields = ["title", "description", "tech_requirements", "must_have", "start_time", "deadline", "materials"]

    def get_context_data(self, **kwargs):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return super().get_context_data(contest=self.contest, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.contest_id = self.kwargs["pk"]

        if obj.deadline <= obj.start_time:
            form.add_error("deadline", _("Deadline must be after start time."))
            return self.form_invalid(form)

        if obj.deadline < timezone.now():
            form.add_error("deadline", _("Deadline cannot be in the past."))
            return self.form_invalid(form)

        if not isinstance(obj.must_have, list) or len(obj.must_have) == 0:
            form.add_error("must_have", _("Must have at least one checklist item."))
            return self.form_invalid(form)

        last_round = Round.objects.filter(contest=obj.contest).order_by("-order").first()
        obj.order = (last_round.order + 1) if last_round else 1
        obj.created_by = self.request.user
        obj.status = Round.Status.DRAFT
        materials_str = self.request.POST.get("materials", "").strip()
        if materials_str:
            try:
                obj.materials = json.loads(materials_str)
            except json.JSONDecodeError:
                obj.materials = []
        else:
            obj.materials = []
        obj.save()

        return redirect("contest_rounds", pk=obj.contest.pk)


class RoundEditView(OrganizerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)

        if round_obj.status != Round.Status.DRAFT:
            return HttpResponseForbidden(_("Cannot edit a round that is not in DRAFT status."))

        return render(request, "app/rounds/round_form.html", {"contest": contest, "round": round_obj})

    def post(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)

        if round_obj.status != Round.Status.DRAFT:
            return HttpResponseForbidden(_("Cannot edit a round that is not in DRAFT status."))

        round_obj.title = request.POST.get("title", round_obj.title)
        round_obj.description = request.POST.get("description", round_obj.description)
        round_obj.tech_requirements = request.POST.get("tech_requirements", round_obj.tech_requirements)

        try:
            must_have = json.loads(request.POST.get("must_have", "[]"))
            if not must_have:
                return render(request, "app/rounds/round_form.html", {
                    "contest": contest,
                    "round": round_obj,
                    "error": _("Must have at least one checklist item."),
                })
            round_obj.must_have = must_have
        except json.JSONDecodeError:
            return render(request, "app/rounds/round_form.html", {
                "contest": contest,
                "round": round_obj,
                "error": _("Invalid must_have format."),
            })

        if request.POST.get("start_time"):
            start_time = parse_datetime(request.POST.get("start_time"))
            if start_time and timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time)
            if start_time:
                round_obj.start_time = start_time

        if request.POST.get("deadline"):
            deadline = parse_datetime(request.POST.get("deadline"))
            if deadline and timezone.is_naive(deadline):
                deadline = timezone.make_aware(deadline)
            if deadline:
                if deadline <= round_obj.start_time:
                    return render(request, "app/rounds/round_form.html", {
                        "contest": contest,
                        "round": round_obj,
                        "error": _("Deadline must be after start time."),
                    })
                if deadline < timezone.now():
                    return render(request, "app/rounds/round_form.html", {
                        "contest": contest,
                        "round": round_obj,
                        "error": _("Deadline cannot be in the past."),
                    })
                round_obj.deadline = deadline

        try:
            materials = json.loads(request.POST.get("materials", "[]"))
            round_obj.materials = materials
        except json.JSONDecodeError:
            pass

        round_obj.save()
        return redirect("contest_rounds", pk=contest.pk)


class RoundActivateView(OrganizerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)

        if round_obj.status != Round.Status.DRAFT:
            return HttpResponseForbidden(_("Can only activate DRAFT rounds. Current status: %(status)s") % {'status': round_obj.status})

        round_obj.status = Round.Status.ACTIVE
        round_obj.save()

        logging.getLogger(__name__).info(
            "Round %s (%s) activated by %s",
            round_obj.id,
            round_obj.title,
            request.user.username,
        )

        notify_contest_participants(
            contest,
            Notification.Type.ROUND_STARTED,
            _("Round started: %(title)s") % {'title': round_obj.title},
            _("New round '%(title)s' is now active in '%(contest)s'. Deadline: %(deadline)s") % {
                'title': round_obj.title,
                'contest': contest.name,
                'deadline': round_obj.deadline.strftime('%b %d, %H:%M')
            },
            link=reverse("round_detail_team", kwargs={"pk": contest.pk, "round_id": round_obj.pk}),
        )
        return redirect("contest_rounds", pk=contest.pk)


class RoundCloseSubmissionsView(OrganizerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)

        if round_obj.status != Round.Status.ACTIVE:
            return HttpResponseForbidden(_("Can only close submissions for ACTIVE rounds."))

        round_obj.status = Round.Status.SUBMISSION_CLOSED
        round_obj.save()

        logging.getLogger(__name__).info("Round %s submissions closed manually", round_obj.id)
        notify_contest_participants(
            contest,
            Notification.Type.SUBMISSIONS_CLOSED,
            _("Submissions closed: %(title)s") % {'title': round_obj.title},
            _("Submissions for round '%(title)s' in '%(contest)s' are now closed.") % {
                'title': round_obj.title,
                'contest': contest.name
            },
            link=reverse("round_detail_team", kwargs={"pk": contest.pk, "round_id": round_obj.pk}),
        )
        notify_contest_jury(
            contest,
            Notification.Type.SUBMISSIONS_CLOSED,
            _("Submissions closed: %(title)s") % {'title': round_obj.title},
            _("Submissions for round '%(title)s' in '%(contest)s' are closed. You can now start evaluations.") % {
                'title': round_obj.title,
                'contest': contest.name
            },
            link=reverse("dashboard"),
        )
        return redirect("contest_rounds", pk=contest.pk)


class RoundExtendDeadlineView(OrganizerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)
        error = kwargs.get("error")
        return render(request, "app/rounds/round_extend_deadline.html", {
            "contest": contest,
            "round": round_obj,
            "error": error
        })

    def post(self, request, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=kwargs["round_id"], contest=contest)

        if round_obj.status != Round.Status.ACTIVE:
            return HttpResponseForbidden(_("Can only extend deadline for ACTIVE rounds."))

        new_deadline_str = request.POST.get("new_deadline")
        if not new_deadline_str:
            return self.get(request, *args, error=_("New deadline is required."), **kwargs)

        new_deadline = parse_datetime(new_deadline_str)
        if not new_deadline:
            return self.get(request, *args, error=_("Invalid datetime format."), **kwargs)
        if timezone.is_naive(new_deadline):
            new_deadline = timezone.make_aware(new_deadline)
        if new_deadline < timezone.now():
            return self.get(request, *args, error=_("New deadline cannot be in the past."), **kwargs)

        old_deadline = round_obj.deadline
        round_obj.deadline = new_deadline
        round_obj.save()

        logging.getLogger(__name__).info(
            "Round %s deadline extended from %s to %s by %s",
            round_obj.id,
            old_deadline,
            new_deadline,
            request.user.username,
        )
        return redirect("contest_rounds", pk=contest.pk)


class ContestRoundsTeamView(RedirectToRegisterMixin, TemplateView):
    template_name = "app/contests/contest_rounds_team.html"

    def get_context_data(self, **kwargs):
        contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        now = timezone.now()
        active_rounds = contest.rounds.filter(status=Round.Status.ACTIVE, start_time__lte=now).order_by("order")
        closed_rounds = contest.rounds.filter(status=Round.Status.SUBMISSION_CLOSED).order_by("order")
        evaluated_rounds = contest.rounds.filter(status=Round.Status.EVALUATED).order_by("order")
        return super().get_context_data(
            contest=contest,
            active_rounds=active_rounds,
            closed_rounds=closed_rounds,
            evaluated_rounds=evaluated_rounds,
        )


class RoundDetailTeamView(RedirectToRegisterMixin, DetailView):
    """Legacy view - now uses the same template as RoundDetailView.
    This view is maintained for backward compatibility but delegates to the same template."""
    model = Round
    template_name = "app/rounds/round_detail.html"
    context_object_name = "round"
    pk_url_kwarg = "round_id"

    def get_object(self, queryset=None):
        contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=self.kwargs["round_id"], contest=contest)
        
        if round_obj.status == Round.Status.DRAFT:
            raise Http404(_("This round is not available yet."))
        
        return round_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        round_obj = self.object
        user = self.request.user
        contest = round_obj.contest

        now = timezone.now()
        is_active = round_obj.status == Round.Status.ACTIVE and round_obj.start_time <= now
        is_open = is_active and round_obj.deadline > now
        time_remaining = round_obj.time_remaining() if is_active else None

        user_team = contest.teams.filter(participants=user).first()
        user_submission = None
        if user_team:
            user_submission = Submission.objects.filter(round=round_obj, team=user_team).first()

        context.update({
            "contest": contest,
            "is_organizer": False,  # Team view is never for organizer
            "is_jury": contest.jurys.filter(pk=user.pk).exists(),
            "is_active": is_active,
            "is_open": is_open,
            "time_remaining": time_remaining,
            "user_submission": user_submission,
            "user_team": user_team,
            "submission_count": 0,  # Not shown to team members
        })
        return context


class RoundDetailView(RedirectToRegisterMixin, ContestContextMixin, DetailView):
    model = Round
    template_name = "app/rounds/round_detail.html"
    context_object_name = "round"
    pk_url_kwarg = "round_pk"

    def get_object(self, queryset=None):
        contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        round_obj = get_object_or_404(Round, pk=self.kwargs["round_pk"], contest=contest)

        user = self.request.user
        is_organizer = contest.organizer == user
        is_jury = contest.jurys.filter(pk=user.pk).exists()
        is_participant = contest.participants.filter(pk=user.pk).exists()
        is_team_member = contest.teams.filter(participants=user).exists()

        if round_obj.status == Round.Status.DRAFT and not (is_organizer or user.is_staff):
            raise Http404(_("This round is not available yet."))

        if not (is_organizer or is_jury or is_participant or is_team_member or user.is_staff):
            raise Http404(_("You do not have access to this contest."))

        return round_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        round_obj = self.object
        user = self.request.user
        contest = round_obj.contest

        now = timezone.now()
        is_active = round_obj.status == Round.Status.ACTIVE and round_obj.start_time <= now
        is_open = is_active and round_obj.deadline > now
        time_remaining = round_obj.time_remaining() if is_active else None

        user_team = contest.teams.filter(participants=user).first()
        user_submission = None
        if user_team:
            user_submission = Submission.objects.filter(round=round_obj, team=user_team).first()

        context.update({
            "contest": contest,
            "is_organizer": contest.organizer == user or user.is_staff,
            "is_jury": contest.jurys.filter(pk=user.pk).exists(),
            "is_active": is_active,
            "is_open": is_open,
            "time_remaining": time_remaining,
            "user_submission": user_submission,
            "user_team": user_team,
            "submission_count": round_obj.submissions.count() if (contest.organizer == user or user.is_staff) else 0,
        })
        return context
