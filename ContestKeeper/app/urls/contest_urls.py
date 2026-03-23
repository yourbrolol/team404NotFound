from .. import views
from django.urls import path

urlpatterns = [
    path("", views.ContestListView.as_view(), name="contest_list"),
    path("new/", views.ContestFormView.as_view(), name="contest_create"),
    path("<int:pk>/", views.ContestDetailView.as_view(), name="contest_detail"),
    path("<int:pk>/teams/", views.ViewTeamsView.as_view(), name="contest_teams"),
    path("<int:pk>/jurys/", views.ViewJurysView.as_view(), name="contest_jurys"),
    path("<int:pk>/teams/<int:ck>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("<int:pk>/edit/", views.ContestFormView.as_view(), name="contest_edit"),
    path("<int:pk>/delete/", views.ContestDeleteView.as_view(), name="contest_delete"),
    path("<int:pk>/apply/<str:app_type>/", views.ApplyToContestView.as_view(), name="apply_to_contest"),
]
