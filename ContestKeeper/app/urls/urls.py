from .. import views
from django.urls import path, include

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("contests/", include("app.urls.contest_urls")),
    path("applications/", include("app.urls.application_urls")),
]
