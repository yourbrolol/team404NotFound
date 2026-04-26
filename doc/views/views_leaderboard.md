# Views: Leaderboard

## ContestLeaderboardView
- **Path**: `app.views.views_leaderboard.ContestLeaderboardView`
- **Inherits from**: `LeaderboardAccessMixin`, `TemplateView`

### Overview
Displays the rankings and scores of teams in a contest. Supports pagination and conditional display of jury breakdowns.

---

## AdminLeaderboardDashboardView
- **Path**: `app.views.views_leaderboard.AdminLeaderboardDashboardView`
- **Inherits from**: `AdminPermissionMixin`, `TemplateView`

### Overview
A dashboard for contest organizers to:
- Monitor evaluation progress (progress bar).
- Identify missing scores by jury/team.
- Recalculate the leaderboard manually.
- Export data to CSV or JSON.

---

## Leaderboard Export Views
- **AdminExportLeaderboardView**: Exports the leaderboard in JSON or CSV.
- **ExportEvaluationsCSVView**: Exports a detailed CSV of every jury score.
- **ExportTeamsCSVView**: Exports the list of teams and participants.

---

## LeaderboardAPIView
- **Path**: `app.views.views_leaderboard.LeaderboardAPIView`

### Overview
A JSON endpoint providing real-time leaderboard data, often used by dynamic frontend components.
