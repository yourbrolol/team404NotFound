from . import views
from django.urls import path

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("contests/", views.ContestListView.as_view(), name="contest_list"),
    path("contests/new/", views.ContestCreateView.as_view(), name="contest_create"),
    path("contests/<int:pk>/", views.ContestDetailView.as_view(), name="contest_detail"),
    path("contests/<int:pk>/teams/", views.ViewTeamsView.as_view(), name="contest_teams"),
    path("contests/<int:pk>/teams/<int:ck>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("contests/<int:pk>/edit/", views.ContestEditView.as_view(), name="contest_edit"),
    path("contests/<int:pk>/delete/", views.ContestDeleteView.as_view(), name="contest_delete"),
    path("contests/<int:pk>/apply/<str:app_type>/", views.ApplyToContestView.as_view(), name="apply_to_contest"),
    path("applications/<int:pk>/approve/", views.ApproveApplicationView.as_view(), name="approve_application"),
    path("applications/<int:pk>/reject/", views.RejectApplicationView.as_view(), name="reject_application"),
]