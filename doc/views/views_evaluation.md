# Views: Evaluation & Leaderboard

## AssignJuryView
- **Path**: `app.views.views_evaluation.AssignJuryView`

### Overview
Triggers the automatic assignment of jury members to teams for a contest. Uses the `assign_jury_to_teams` service.

---

## JuryEvaluationView
- **Path**: `app.views.views_evaluation.JuryEvaluationView`

### Overview
The scoring interface for jury members. Allows inputting scores for each criterion for a specific team.
- **Access Control**: Limited to jury members assigned to the team.
- **Read-only State**: Scores cannot be edited once the evaluation phase is marked as `COMPLETED`.

---

## ContestLeaderboardView
- **Path**: `app.views.views_leaderboard.ContestLeaderboardView`

### Overview
Publicly displays the rankings and scores for all teams in a contest. Handles automatic recomputation if the contest is ready.

---

## AdminLeaderboardDashboardView
- **Path**: `app.views.views_leaderboard.AdminLeaderboardDashboardView`

### Overview
A management dashboard for organizers to monitor evaluation progress, view missing scores, and finalize the leaderboard.

---

## Criterion Management
Views for managing scoring criteria within a contest:
- **CriterionCreateView**: Add a new scoring criterion.
- **CriterionUpdateView**: Edit an existing criterion.
- **CriterionDeleteView**: Remove a criterion.
