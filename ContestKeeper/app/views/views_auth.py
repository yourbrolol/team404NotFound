from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView
from django.contrib.auth.views import PasswordChangeView

from app.forms import UserRegistrationForm, RoleApplicationForm


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = "/"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)


class RoleApplicationView(FormView):
    form_class = RoleApplicationForm
    template_name = "registration/login_extended.html"
    success_url = reverse_lazy("role_application_success")

    def form_valid(self, form):
        role_app = form.save(commit=False)
        # Hash the password before saving
        role_app.password = make_password(form.cleaned_data["password"])
        role_app.save()
        return super().form_valid(form)


class RoleApplicationSuccessView(TemplateView):
    template_name = "registration/role_application_success.html"


class CustomPasswordChangeView(PasswordChangeView):
    template_name = "app/core/change_password.html"
    success_url = reverse_lazy("profile")

    def get_success_url(self):
        return str(self.success_url) + "?saved=1"
