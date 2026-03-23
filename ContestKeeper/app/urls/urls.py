<<<<<<< HEAD
from .. import views
from django.urls import path, include

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("contests/", include("app.urls.contest_urls")),
    path("applications/", include("app.urls.application_urls")),
    path('contests/<int:pk>/teams/', views.ViewTeamsView.as_view(), name='teams'),
]
=======
from .. import views
from django.urls import path, include

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("contests/", include("app.urls.contest_urls")),
    path("applications/", include("app.urls.application_urls")),
]
>>>>>>> 2dcf23c (changes in views.py and url routing; fixed the font in certain html files.)
