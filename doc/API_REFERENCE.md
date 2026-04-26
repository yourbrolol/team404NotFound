# API Reference: ContestKeeper

This document lists the primary endpoints available in the ContestKeeper application.

## 1. General & Authentication

| Method | Endpoint | Name | Purpose |
|--------|----------|------|---------|
| GET | `/` | `home` | Landing page. |
| GET | `/dashboard/` | `dashboard` | User-specific dashboard (Organizer, Jury, or Participant). |
| GET/POST | `/register/` | `register` | User registration. |
| GET/POST | `/profile/` | `profile` | View/edit user profile. |
| GET/POST | `/settings/` | `settings` | User account settings. |

## 2. Contest Management

| Method | Endpoint | Name | Purpose |
|--------|----------|------|---------|
| GET | `/contests/` | `contest_list` | List of all contests. |
| GET/POST | `/contests/new/` | `contest_create` | Create a new contest (Organizer only). |
| GET | `/contests/<pk>/` | `contest_detail` | Detailed view of a contest. |
| GET/POST | `/contests/<pk>/edit/` | `contest_edit` | Edit contest details. |
| POST | `/contests/<pk>/delete/` | `contest_delete` | Delete a contest. |
| GET | `/contests/<pk>/analytics/` | `organizer_analytics` | Contest statistics and analytics. |

## 3. Teams & Applications

| Method | Endpoint | Name | Purpose |
|--------|----------|------|---------|
| POST | `/contests/<pk>/apply/<type>/` | `apply_to_contest` | Apply as Jury, Team, or Participant. |
| GET | `/contests/<pk>/teams/` | `contest_teams` | List of teams in a contest. |
| GET/POST | `/contests/<pk>/teams/new/` | `team_create` | Create a new team for a contest. |
| GET | `/contests/<pk>/teams/<ck>/` | `team_detail` | Detailed view of a team. |
| POST | `/applications/<pk>/approve/` | `approve_application` | Approve a contest application. |
| POST | `/applications/<pk>/reject/` | `reject_application` | Reject a contest application. |
| GET | `/contests/<pk>/teams/export/` | `export_teams_csv` | Export team list as CSV. |

## 4. Rounds & Submissions

| Method | Endpoint | Name | Purpose |
|--------|----------|------|---------|
| GET | `/contests/<pk>/rounds/` | `contest_rounds` | List of rounds in a contest. |
| GET/POST | `/contests/<pk>/rounds/new/` | `round_create` | Create a new round. |
| GET/POST | `/contests/<pk>/rounds/<id>/submit/` | `submission_create` | Submit work for a specific round. |
| GET | `/contests/<pk>/rounds/<id>/submissions/` | `round_submissions` | List all submissions for a round. |
| GET | `/contests/<pk>/rounds/<id>/submissions/<sub>/` | `submission_detail` | Detailed view of a specific submission. |
| POST | `/contests/<pk>/rounds/<id>/activate/` | `round_activate` | Start a round. |
| POST | `/contests/<pk>/rounds/<id>/close/` | `round_close_submissions` | Close submissions for a round. |

## 5. Evaluation & Leaderboard

| Method | Endpoint | Name | Purpose |
|--------|----------|------|---------|
| GET | `/contests/<pk>/leaderboard/` | `contest_leaderboard` | View the contest leaderboard. |
| GET | `/contests/<pk>/leaderboard/api/` | `contest_leaderboard_api` | JSON API for leaderboard data. |
| GET/POST | `/contests/<pk>/evaluate/<team_pk>/` | `jury_evaluate` | Jury interface for scoring a team. |
| POST | `/contests/<pk>/leaderboard/recalculate/` | `admin_recalculate_leaderboard` | Trigger leaderboard recomputation. |
| POST | `/contests/<pk>/leaderboard/finish/` | `admin_finish_evaluation` | Finalize evaluations for a contest. |

## 6. Utilities & Notifications

| Method | Endpoint | Name | Purpose |
|--------|----------|------|---------|
| GET | `/notifications/` | `notification_list` | List of user notifications. |
| POST | `/notifications/<pk>/read/` | `notification_read` | Mark a notification as read. |
| GET | `/contests/<pk>/announcements/` | `announcement_list` | Contest announcements. |
| GET | `/contests/<pk>/schedule/` | `schedule` | Contest schedule/timeline. |
