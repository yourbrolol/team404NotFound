from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from ..forms import SubmissionForm
from ..models import Contest, Round, Submission
from .views_base import RedirectToRegisterMixin
from .views_base import OrganizerRequiredMixin


class SubmissionCreateEditView(RedirectToRegisterMixin, View):
    template_name = "app/submission_form.html"

    def get_round_and_team(self, request, pk, round_id):
        contest = get_object_or_404(Contest, pk=pk)
        round_obj = get_object_or_404(Round, pk=round_id, contest=contest)
        team = contest.teams.filter(participants=request.user).first()
        if not team:
            raise Http404("You are not part of any team in this contest.")
        return contest, round_obj, team

    def get(self, request, pk, round_id):
        contest, round_obj, team = self.get_round_and_team(request, pk, round_id)
        if not round_obj.is_open():
            return HttpResponseForbidden("This round is not currently open for submissions.")
        submission = Submission.objects.filter(round=round_obj, team=team).first()
        form = SubmissionForm(instance=submission)
        return render(request, self.template_name, {
            "contest": contest,
            "round": round_obj,
            "team": team,
            "form": form,
            "is_edit": submission is not None,
        })

    def post(self, request, pk, round_id):
        contest, round_obj, team = self.get_round_and_team(request, pk, round_id)
        if not round_obj.is_open():
            return HttpResponseForbidden("This round is not currently open for submissions.")
        submission = Submission.objects.filter(round=round_obj, team=team).first()
        form = SubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.round = round_obj
            obj.team = team
            obj.save()
            return redirect("round_detail_team", pk=contest.pk, round_id=round_obj.pk)
        return render(request, self.template_name, {
            "contest": contest,
            "round": round_obj,
            "team": team,
            "form": form,
            "is_edit": submission is not None,
        })


class SubmissionDetailView(RedirectToRegisterMixin, DetailView):
    model = Submission
    template_name = "app/submission_detail.html"
    context_object_name = "submission"
    pk_url_kwarg = "sub_pk"

    def get_object(self, queryset=None):
        submission = super().get_object(queryset)
        user = self.request.user
        contest = submission.round.contest
        is_member = submission.team.participants.filter(pk=user.pk).exists()
        is_organizer = contest.organizer == user
        is_jury = contest.jurys.filter(pk=user.pk).exists()
        if not (is_member or is_organizer or is_jury or user.is_staff):
            raise Http404("You do not have access to this submission.")
        return submission

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.object.round.contest
        context["round"] = self.object.round
        return context


class RoundSubmissionsListView(OrganizerRequiredMixin, ListView):
    template_name = "app/submission_list.html"
    context_object_name = "submissions"

    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        self.round = get_object_or_404(Round, pk=kwargs["round_id"], contest=self.contest)
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        is_organizer = self.contest.organizer == request.user
        is_jury = self.contest.jurys.filter(pk=request.user.pk).exists()
        if not (is_organizer or is_jury or request.user.is_staff):
            return HttpResponseForbidden("You do not have access to this page.")
        return super(OrganizerRequiredMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Submission.objects.filter(round=self.round).order_by("-submitted_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        context["round"] = self.round
        return context
