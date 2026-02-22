from django.contrib.auth import login
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserRegistrationForm, ContestForm

from .models import Contest

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("register")
    
    user = request.user
    if user.is_admin():
        contests = Contest.objects.all()
    elif user.is_organizer():
        contests = user.organized_contests.all()
    elif user.is_jury():
        contests = user.judged_contests.all()
    elif user.is_participant():
        contests = user.participated_contests.all()
    else:
        contests = Contest.objects.none()

    return render(request, "app/dashboard.html", {"contests": contests})

def home(request):
    if not request.user.is_authenticated:
        return redirect("register")

    return render(request, "app/index.html")

def contest_list(request):
    # Returns raw contests data as requested (placeholder for now)
    contests = Contest.objects.all().values()
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

def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    return render(request, "app/contest_detail.html", {"contest": contest})

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)