from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, CreateView, UpdateView

from app.models import Application, Contest, User, Team, JuryAssignment
from django.contrib.auth import get_user_model
from app.forms import TeamForm
from app.views.views_base import RedirectToRegisterMixin


class ViewTeamsView(RedirectToRegisterMixin, ListView):
    template_name = "app/teams/teams.html"
    context_object_name = "teams"

    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return self.contest.teams.all()

    def get_context_data(self, **kwargs):
        user_team = None
        team_applications = None
        has_pending_application = False
        if self.request.user.is_authenticated:
            user_team = self.contest.teams.filter(participants=self.request.user).first()
            has_pending_application = Application.objects.filter(
                user=self.request.user,
                contest=self.contest,
                application_type=Application.Type.PARTICIPANT,
                status=Application.Status.PENDING
            ).exists()
            if self.request.user == self.contest.organizer:
                team_applications = Application.objects.filter(
                    contest=self.contest,
                    application_type=Application.Type.TEAM,
                    status=Application.Status.PENDING
                ).select_related('user', 'team')
        
        return super().get_context_data(
            contest=self.contest, 
            user_team=user_team, 
            team_applications=team_applications,
            has_pending_application=has_pending_application,
            **kwargs
        )


class ViewJurysView(RedirectToRegisterMixin, ListView):
    template_name = "app/juries/jurys.html"
    context_object_name = "jurys"

    def get_queryset(self):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return self.contest.jurys.all()

    def get_context_data(self, **kwargs):
        assignments = JuryAssignment.objects.filter(contest=self.contest).select_related('team', 'jury_member')
        jury_applications = None
        if self.request.user.is_authenticated and self.request.user == self.contest.organizer:
            jury_applications = Application.objects.filter(
                contest=self.contest,
                application_type=Application.Type.JURY,
                status=Application.Status.PENDING
            ).select_related('user')
        return super().get_context_data(contest=self.contest, assignments=assignments, jury_applications=jury_applications, **kwargs)


class TeamDetailView(RedirectToRegisterMixin, DetailView):
    template_name = "app/teams/team.html"
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
            return HttpResponseForbidden(_("You are not the captain of this team."))
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


class OrganizerOnlyMixin(RedirectToRegisterMixin):
    """Mixin that restricts access to the contest organizer only."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if request.user != self.contest.organizer:
            return HttpResponseForbidden(_("Only the organizer can perform this action."))
        return super().dispatch(request, *args, **kwargs)


class TeamDeleteView(RedirectToRegisterMixin, View):
    """Allows the contest organizer or team captain to delete a team from their contest."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        self.team = get_object_or_404(self.contest.teams, pk=kwargs["ck"])
        if request.user != self.contest.organizer and request.user != self.team.captain:
            return HttpResponseForbidden(_("Only the organizer or team captain can delete this team."))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        team = self.team
        # Remove all applications associated with this team in this contest
        Application.objects.filter(contest=self.contest, team=team).delete()
        # Remove all jury assignments for this team
        JuryAssignment.objects.filter(contest=self.contest, team=team).delete()
        team.delete()
        messages.success(request, _("Team deleted successfully."))
        return redirect("contest_teams", pk=self.contest.pk)


class JuryKickView(OrganizerOnlyMixin, View):
    """Allows the contest organizer to remove a jury member from their contest."""

    def post(self, request, *args, **kwargs):
        jury_member = get_object_or_404(get_user_model(), pk=kwargs["user_id"])
        # Remove all jury assignments for this member in this contest
        JuryAssignment.objects.filter(contest=self.contest, jury_member=jury_member).delete()
        # Remove from the contest's jury M2M relation
        self.contest.jurys.remove(jury_member)
        # Reject their outstanding jury application if any
        Application.objects.filter(
            contest=self.contest,
            user=jury_member,
            application_type=Application.Type.JURY,
        ).update(status=Application.Status.REJECTED)
        messages.success(request, _("Jury member '%(username)s' removed from the contest.") % {'username': jury_member.username})
        return redirect("contest_jurys", pk=self.contest.pk)


class LeaderboardAccessMixin(RedirectToRegisterMixin):
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)


class AdminPermissionMixin(LeaderboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        if request.user.is_authenticated and request.user != self.contest.organizer and not request.user.is_staff:
            return HttpResponseForbidden(_("You do not have admin access to this contest."))
        return super().dispatch(request, *args, **kwargs)



class TeamUpdateView(RedirectToRegisterMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "app/teams/team_form.html"
    context_object_name = "team"

    def get_object(self, queryset=None):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        team = get_object_or_404(self.contest.teams, pk=self.kwargs["ck"])
        if self.request.user != team.captain:
             # This is a simple check, better to use a mixin but for now this works matching existing patterns
             pass
        return team

    def get_context_data(self, **kwargs):
        self.contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return super().get_context_data(contest=self.contest, **kwargs)

    def get_success_url(self):
        return reverse_lazy("team_detail", kwargs={"pk": self.kwargs["pk"], "ck": self.kwargs["ck"]})

    def dispatch(self, request, *args, **kwargs):
        self.contest = get_object_or_404(Contest, pk=kwargs["pk"])
        team = get_object_or_404(self.contest.teams, pk=kwargs["ck"])
        if request.user != team.captain and request.user != self.contest.organizer:
            return HttpResponseForbidden(_("You are not authorized to edit this team."))
        return super().dispatch(request, *args, **kwargs)


class TeamCreateView(RedirectToRegisterMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = "app/teams/team_create_form.html"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        contest = get_object_or_404(Contest, pk=self.kwargs["pk"])
        
        # Check registration dates
        now = timezone.now()
        if contest.registration_start and now < contest.registration_start:
            messages.error(self.request, _("Registration for this contest has not started yet."))
            return redirect("contest_detail", pk=contest.pk)
        if contest.registration_end and now >= contest.registration_end:
            messages.error(self.request, _("Registration for this contest has closed."))
            return redirect("contest_detail", pk=contest.pk)

        # Check if user already in a team for this contest
        if contest.teams.filter(participants=self.request.user).exists():
            messages.error(self.request, _("You are already a member of a team in this contest."))
            return redirect("contest_detail", pk=contest.pk)

        # Check for existing application of type TEAM for this contest
        # Use first() to avoid MultipleObjectsReturned (though unique constraint should prevent it)
        existing_app = Application.objects.filter(
            user=self.request.user,
            contest=contest,
            application_type=Application.Type.TEAM
        ).first()

        if existing_app and existing_app.status != Application.Status.REJECTED:
            messages.error(self.request, _("You already have a team application for this contest."))
            return redirect("contest_detail", pk=contest.pk)

        team = form.save()
        team.captain = self.request.user
        team.participants.add(self.request.user)
        team.save()
        
        # Create or update application for the contest
        # Use get_or_create with only unique fields in lookup to avoid IntegrityError
        app, created = Application.objects.get_or_create(
            user=self.request.user,
            contest=contest,
            application_type=Application.Type.TEAM,
            defaults={'team': team, 'status': Application.Status.PENDING}
        )
        if not created:
            app.team = team
            app.status = Application.Status.PENDING
            app.save()
        
        messages.success(self.request, _("Team '%(name)s' created! Approval from organizer is pending.") % {'name': team.name})
        return redirect("contest_detail", pk=contest.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = get_object_or_404(Contest, pk=self.kwargs["pk"])
        return context


class TeamJoinView(RedirectToRegisterMixin, View):
    def post(self, request, pk, ck):
        contest = get_object_or_404(Contest, pk=pk)
        team = get_object_or_404(contest.teams, pk=ck)
        
        # Prevent blocked users from applying to this team
        if team.blacklisted_members.filter(pk=request.user.pk).exists():
            messages.error(request, _("You are blocked from joining this team."))
            return redirect("contest_teams", pk=pk)
        
        # Prevent double application or joining if already in a team
        if contest.teams.filter(participants=request.user).exists():
            messages.error(request, _("You are already in a team for this contest."))
            return redirect("contest_teams", pk=pk)

        # Check for existing application of type PARTICIPANT to avoid IntegrityError
        existing_app = Application.objects.filter(
            user=request.user, 
            contest=contest, 
            application_type=Application.Type.PARTICIPANT
        ).first()

        if existing_app:
            if existing_app.team == team:
                if existing_app.status == Application.Status.PENDING:
                    messages.info(request, _("You have already applied to this team."))
                else:
                    # If was rejected or approved (shouldn't be here if approved due to line 191), try again
                    existing_app.status = Application.Status.PENDING
                    existing_app.save()
                    messages.success(request, _("Application to join '%(name)s' submitted!") % {'name': team.name})
            elif existing_app.status != Application.Status.REJECTED:
                 messages.error(request, _("You already have a pending application for another team in this contest."))
            else:
                # Switching team application after rejection
                existing_app.team = team
                existing_app.status = Application.Status.PENDING
                existing_app.save()
                messages.success(request, _("Application to join '%(name)s' submitted!") % {'name': team.name})
            return redirect("contest_teams", pk=pk)
        
        Application.objects.create(
            user=request.user,
            contest=contest,
            team=team,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING
        )
        messages.success(request, _("Application to join '%(name)s' submitted!") % {'name': team.name})
        return redirect("contest_teams", pk=pk)


class TeamLeaveView(RedirectToRegisterMixin, View):
    def post(self, request, pk, ck):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        contest = get_object_or_404(Contest, pk=pk)
        team = get_object_or_404(contest.teams, pk=ck)

        if request.user == team.captain:
            return HttpResponseForbidden(_("Team captain cannot leave the team."))
        if not team.participants.filter(pk=request.user.pk).exists():
            return HttpResponseForbidden(_("You are not a member of this team."))

        team.participants.remove(request.user)
        Application.objects.filter(
            user=request.user,
            contest=contest,
            team=team,
            application_type=Application.Type.PARTICIPANT,
        ).delete()

        messages.success(request, _("You have left the team."))
        return redirect("contest_detail", pk=contest.pk)
