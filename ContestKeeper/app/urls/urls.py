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
    path("notifications/", views.NotificationListView.as_view(), name="notification_list"),
    path("notifications/<int:pk>/read/", views.MarkNotificationReadView.as_view(), name="notification_read"),
    path("notifications/mark-all-read/", views.MarkAllReadView.as_view(), name="notifications_mark_all_read"),
]
