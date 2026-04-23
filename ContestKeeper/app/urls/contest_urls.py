from app import views
from django.urls import path

urlpatterns = [
    path("",                                    views.ContestListView.as_view(),   name="contest_list"),
    path("new/",                                views.ContestFormView.as_view(),   name="contest_create"),
    path("<int:pk>/",                           views.ContestDetailView.as_view(), name="contest_detail"),
    path("<int:pk>/teams/",                     views.ViewTeamsView.as_view(),     name="contest_teams"),
    path("<int:pk>/jurys/",                     views.ViewJurysView.as_view(),     name="contest_jurys"),
    path("<int:pk>/leaderboard/",                views.ContestLeaderboardView.as_view(), name="contest_leaderboard"),
    path("<int:pk>/leaderboard/api/",            views.LeaderboardAPIView.as_view(), name="contest_leaderboard_api"),
    path("<int:pk>/leaderboard/admin/",          views.AdminLeaderboardDashboardView.as_view(), name="admin_leaderboard_dashboard"),
    path("<int:pk>/leaderboard/finish/",         views.AdminFinishEvaluationView.as_view(), name="admin_finish_evaluation"),
    path("<int:pk>/leaderboard/jury-toggle/",    views.AdminToggleJuryBreakdownView.as_view(), name="admin_toggle_jury_breakdown"),
    path("<int:pk>/leaderboard/recalculate/",    views.AdminRecalculateLeaderboardView.as_view(), name="admin_recalculate_leaderboard"),
    path("<int:pk>/leaderboard/export/",         views.AdminExportLeaderboardView.as_view(), name="admin_export_leaderboard"),
    path("<int:pk>/leaderboard/export/evaluations/", views.ExportEvaluationsCSVView.as_view(), name="export_evaluations_csv"),
    path("<int:pk>/criteria/new/",               views.CriterionCreateView.as_view(), name="criterion_create"),
    path("<int:pk>/criteria/<int:criterion_id>/edit/", views.CriterionUpdateView.as_view(), name="criterion_edit"),
    path("<int:pk>/criteria/<int:criterion_id>/delete/", views.CriterionDeleteView.as_view(), name="criterion_delete"),
    path("<int:pk>/applications/",               views.AdminApplicationListView.as_view(), name="admin_application_list"),
    path("<int:pk>/teams/export/",               views.ExportTeamsCSVView.as_view(), name="export_teams_csv"),
    path("<int:pk>/teams/new/",                 views.TeamCreateView.as_view(),    name="team_create"),
    path("<int:pk>/teams/<int:ck>/",            views.TeamDetailView.as_view(),    name="team_detail"),
    path("<int:pk>/teams/<int:ck>/join/",       views.TeamJoinView.as_view(),      name="team_join"),
    path("<int:pk>/teams/<int:ck>/edit/",       views.TeamUpdateView.as_view(),    name="team_edit"),
    path("<int:pk>/teams/<int:ck>/kick/<int:user_id>/",     views.TeamKickView.as_view(),      name="team_kick"),
    
    # Announcements
    path("<int:pk>/announcements/",             views.AnnouncementListView.as_view(),   name="announcement_list"),
    path("<int:pk>/announcements/create/",      views.AnnouncementCreateView.as_view(), name="announcement_create"),
    path("<int:pk>/announcements/<int:ack>/delete/", views.AnnouncementDeleteView.as_view(), name="announcement_delete"),
    
    # Schedule
    path("<int:pk>/schedule/",                  views.ScheduleView.as_view(),           name="schedule"),
    path("<int:pk>/schedule/create/",           views.ScheduleEventCreateView.as_view(),name="schedule_event_create"),
    path("<int:pk>/schedule/<int:eck>/delete/", views.ScheduleEventDeleteView.as_view(), name="schedule_event_delete"),
    path("<int:pk>/schedule/regenerate/",       views.RegenerateScheduleView.as_view(), name="schedule_regenerate"),
    path("<int:pk>/analytics/",                 views.OrganizerAnalyticsView.as_view(), name="organizer_analytics"),
    
    path("<int:pk>/teams/<int:ck>/block/<int:user_id>/",    views.TeamBlockView.as_view(),     name="team_block"),
    path("<int:pk>/teams/<int:ck>/unblock/<int:user_id>/",  views.TeamUnblockView.as_view(),   name="team_unblock"),
    path("<int:pk>/edit/",                      views.ContestFormView.as_view(),   name="contest_edit"),
    path("<int:pk>/delete/",                    views.ContestDeleteView.as_view(), name="contest_delete"),
    path("<int:pk>/apply/<str:app_type>/",      views.ApplyToContestView.as_view(),name="apply_to_contest"),
    path("<int:pk>/rounds/",                    views.RoundListView.as_view(),     name="contest_rounds"),
    path("<int:pk>/rounds/new/",                views.RoundCreateView.as_view(),   name="round_create"),
    path("<int:pk>/rounds/<int:round_id>/edit/",       views.RoundEditView.as_view(),     name="round_edit"),
    path("<int:pk>/rounds/<int:round_id>/activate/",   views.RoundActivateView.as_view(), name="round_activate"),
    path("<int:pk>/rounds/<int:round_id>/close/",      views.RoundCloseSubmissionsView.as_view(), name="round_close_submissions"),
    path("<int:pk>/rounds/<int:round_id>/extend/",     views.RoundExtendDeadlineView.as_view(), name="round_extend_deadline"),
    path("<int:pk>/rounds/team/",               views.ContestRoundsTeamView.as_view(), name="contest_rounds_team"),
    path("<int:pk>/rounds/<int:round_id>/team/", views.RoundDetailTeamView.as_view(), name="round_detail_team"),
    path("<int:pk>/rounds/<int:round_pk>/",     views.RoundDetailView.as_view(),     name="round_detail"),
    
    # Submissions
    path("<int:pk>/rounds/<int:round_id>/submit/", views.SubmissionCreateEditView.as_view(), name="submission_create"),
    path("<int:pk>/rounds/<int:round_id>/submissions/", views.RoundSubmissionsListView.as_view(), name="round_submissions"),
    path("<int:pk>/rounds/<int:round_id>/submissions/<int:sub_pk>/", views.SubmissionDetailView.as_view(), name="submission_detail"),
    path("<int:pk>/evaluate/<int:team_pk>/", views.JuryEvaluationView.as_view(), name="jury_evaluate"),
    path("<int:pk>/jurys/assign/", views.AssignJuryView.as_view(), name="assign_jury"),
]
