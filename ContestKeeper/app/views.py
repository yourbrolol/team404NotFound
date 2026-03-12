from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserRegistrationForm, ContestForm
from .models import Contest, Application

# General views

def home(request):
    if not request.user.is_authenticated:
        return redirect("register")
    return render(request, "app/index.html")

@login_required(login_url="register")
def dashboard(request):
    user = request.user
    if user.is_organizer():
        contests = user.organized_contests.all()
    elif user.is_jury():
        contests = user.judged_contests.exclude(status=Contest.Status.DRAFT)
    elif user.is_participant():
        contests = user.participated_contests.exclude(status=Contest.Status.DRAFT)
    else:
        contests = Contest.objects.none()
    return render(request, "app/dashboard.html", {"contests": contests})

@login_required(login_url="register")
def profile(request):
    return render(request, "app/profile.html")

# Contest views

def contest_list(request):
    """Returns a JSON list of all non-draft contests."""
    contests = Contest.objects.exclude(status=Contest.Status.DRAFT).values()
    return JsonResponse(list(contests), safe=False)

def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if contest.status == Contest.Status.DRAFT and contest.organizer != request.user:
        raise Http404("Contest is in draft or you don't have access.")
    is_authenticated = request.user.is_authenticated
    p_applications = contest.contest_apps.filter(
        application_type=Application.Type.PARTICIPANT,
        status=Application.Status.PENDING,
    )
    j_applications = contest.contest_apps.filter(
        application_type=Application.Type.JURY,
        status=Application.Status.PENDING,
    )
    context = {
        "contest": contest,
        "participant_applications": p_applications,
        "jury_applications": j_applications,
        "has_pending_p_app": contest.contest_apps.filter(
            user=request.user,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING,
        ).exists() if is_authenticated else False,
        "has_pending_j_app": contest.contest_apps.filter(
            user=request.user,
            application_type=Application.Type.JURY,
            status=Application.Status.PENDING,
        ).exists() if is_authenticated else False,
    }
    return render(request, "app/contest_detail.html", context)

@login_required(login_url="register")
def contest_create(request):
    if request.method == "POST":
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.organizer = request.user
            contest.save()
            form.save_m2m()
            return redirect("home")
    else:
        form = ContestForm()
    return render(request, "app/contest_form.html", {"form": form})

@login_required(login_url="register")
def contest_edit(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if contest.organizer != request.user:
        return HttpResponseForbidden("You are not the organizer of this contest.")
    if request.method == "POST":
        form = ContestForm(request.POST, instance=contest)
        if form.is_valid():
            form.save()
            return redirect("contest_detail", pk=pk)
    else:
        form = ContestForm(instance=contest)
    return render(request, "app/contest_form.html", {"form": form, "is_edit": True})

@login_required(login_url="register")
def contest_delete(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if contest.organizer != request.user:
        return HttpResponseForbidden("You are not authorized to delete this contest.")
    if request.method == "POST":
        contest.delete()
        return redirect("dashboard")
    return redirect("contest_detail", pk=pk)

# Application views

@login_required(login_url="register")
def apply_to_contest(request, pk, app_type):
    contest = get_object_or_404(Contest, pk=pk)
    if contest.status == Contest.Status.DRAFT:
        return HttpResponseForbidden("Cannot apply to a draft contest.")
    role_type = (
        Application.Type.PARTICIPANT
        if app_type == "participant"
        else Application.Type.JURY
    )
    Application.objects.get_or_create(
        user=request.user,
        contest=contest,
        application_type=role_type,
    )
    return redirect("contest_detail", pk=pk)

@login_required(login_url="register")
def approve_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.user == application.contest.organizer:
        application.status = Application.Status.APPROVED
        application.save()
        if application.application_type == Application.Type.PARTICIPANT:
            application.contest.participants.add(application.user)
        else:
            application.contest.jurys.add(application.user)
    return redirect("contest_detail", pk=application.contest.pk)

@login_required(login_url="register")
def reject_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.user == application.contest.organizer:
        application.status = Application.Status.REJECTED
        application.save()
    return redirect("contest_detail", pk=application.contest.pk)

# Team views

@login_required(login_url="register")
def view_teams(request, pk):
    # TODO: implement team listing for contest <pk>
    return HttpResponse("Team listing not yet implemented.")

@login_required(login_url="register")
def team_detail(request, pk, ck):
    # TODO: implement team detail for team <ck> within contest <pk>
    return HttpResponse(f"Team {ck} in contest {pk} – not yet implemented.")

# Auth views

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)