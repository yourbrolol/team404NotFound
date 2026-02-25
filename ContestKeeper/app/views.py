from django.contrib.auth import login
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserRegistrationForm, ContestForm

from .models import Contest, Application

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("register")
    
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

def home(request):
    if not request.user.is_authenticated:
        return redirect("register")

    return render(request, "app/index.html")

def contest_list(request):
    contests = Contest.objects.exclude(status=Contest.Status.DRAFT).values()
    from django.http import JsonResponse
    return JsonResponse(list(contests), safe=False)

def contest_create(request):
    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.organizer = request.user
            contest.save()
            form.save_m2m()  # Save Many-to-Many relationships
            return redirect('home')
    else:
        form = ContestForm()
    
    return render(request, "app/contest_form.html", {"form": form})

def contest_edit(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if contest.organizer != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not the organizer of this contest.")
    
    if request.method == 'POST':
        form = ContestForm(request.POST, instance=contest)
        if form.is_valid():
            form.save()
            return redirect('contest_detail', pk=pk)
    else:
        form = ContestForm(instance=contest)
    
    return render(request, "app/contest_form.html", {"form": form, "is_edit": True})

def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)

    if contest.status == Contest.Status.DRAFT and contest.organizer != request.user:
        from django.http import Http404
        raise Http404("Contest is in draft or you don't have access.")

    p_applications = contest.contest_apps.filter(application_type=Application.Type.PARTICIPANT, status=Application.Status.PENDING)
    j_applications = contest.contest_apps.filter(application_type=Application.Type.JURY, status=Application.Status.PENDING)
    
    context = {
        "contest": contest,
        "participant_applications": p_applications,
        "jury_applications": j_applications,
        "has_pending_p_app": contest.contest_apps.filter(user=request.user, application_type=Application.Type.PARTICIPANT, status=Application.Status.PENDING).exists() if request.user.is_authenticated else False,
        "has_pending_j_app": contest.contest_apps.filter(user=request.user, application_type=Application.Type.JURY, status=Application.Status.PENDING).exists() if request.user.is_authenticated else False,
    }
    return render(request, "app/contest_detail.html", context)

def apply_to_contest(request, pk, app_type):
    contest = get_object_or_404(Contest, pk=pk)

    if contest.status == Contest.Status.DRAFT:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Cannot apply to a draft contest.")

    role_type = Application.Type.PARTICIPANT if app_type == 'participant' else Application.Type.JURY

    if not Application.objects.filter(user=request.user, contest=contest, application_type=role_type).exists():
        Application.objects.create(
            user=request.user,
            contest=contest,
            application_type=role_type
        )
    
    return redirect('contest_detail', pk=pk)

def approve_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.user == application.contest.organizer:
        application.status = Application.Status.APPROVED
        application.save()
        if application.application_type == Application.Type.PARTICIPANT:
            application.contest.participants.add(application.user)
        else:
            application.contest.jurys.add(application.user)
            
    return redirect('contest_detail', pk=application.contest.pk)

def reject_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.user == application.contest.organizer:
        application.status = Application.Status.REJECTED
        application.save()
        
    return redirect('contest_detail', pk=application.contest.pk)

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)