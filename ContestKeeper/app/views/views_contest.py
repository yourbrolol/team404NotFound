from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView

from ..forms import ContestForm
from ..models import Application, Contest
from .views_base import RedirectToRegisterMixin


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
        if is_authenticated:
            user_team = contest.teams.filter(participants=user).first()

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

        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        context.update({
            "user_team": user_team,
            "team_applications": t_applications,
            "jury_applications": j_applications,
            "participant_applications": p_applications,
            "next_event": contest.schedule_events.filter(start_time__gte=timezone.now()).order_by("start_time", "order").first(),
            "has_pending_p_app": contest.contest_apps.filter(
                user=user,
                application_type=Application.Type.TEAM,
                status=Application.Status.PENDING,
            ).exists() if is_authenticated else False,
            "has_pending_j_app": contest.contest_apps.filter(
                user=user,
                application_type=Application.Type.JURY,
                status=Application.Status.PENDING,
            ).exists() if is_authenticated else False,
        })
        return context


class ContestFormView(RedirectToRegisterMixin, View):
    """Handles contest creation (no pk in URL) and editing (pk present)."""
    template_name = "app/contest_form.html"

    def _get_contest(self):
        pk = self.kwargs.get("pk")
        if pk is None:
            return None, False
        contest = Contest.objects.filter(pk=pk).first()
        return contest, (contest is not None and contest.organizer != self.request.user)

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


class ContestDeleteView(RedirectToRegisterMixin, View):
    model = Contest
    success_url = "dashboard"

    def get(self, request, *args, **kwargs):
        return redirect("contest_detail", pk=kwargs["pk"])
