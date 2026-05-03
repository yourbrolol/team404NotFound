# 🖼️ Test Documentation: `test_views.py`

## Purpose
This test suite focuses on the high-level dashboard views: the Home page (Contest Discovery) and the User Profile. It ensures that data is correctly filtered and displayed based on the user's role and current contest involvement.

## Test Classes

### 1. `HomeViewTaskTest`
Tests the `HomeView` logic, which is the landing page for all users.
- **`test_home_shows_all_non_draft_contests`**: Ensures that participants see all active, registration, and finished contests, but **never** draft contests.
- **`test_home_status_filter_limits_contests`**: Verifies that the status filter (e.g., `?status=REGISTRATION`) correctly limits the list of contests.
- **`test_home_invalid_status_filter_falls_back_to_all`**: Ensures that providing an invalid status in the URL query doesn't crash the page and instead shows all contests.
- **`test_home_quick_access_appears_for_participant_with_active_contest`**: 
  - **Scenario**: A participant is in an active team with an active round.
  - **Verification**: A "Your current contest" quick-access card appears on the home page with direct links to the round and their team.
- **`test_home_quick_access_hidden_when_participant_has_no_team`**: Ensures the quick-access card is hidden for users not currently participating in a running contest.

### 2. `ProfileViewTaskTest`
Tests the `ProfileView` which adapts to the user's role (Organizer, Jury, or Participant).
- **`test_profile_for_participant_shows_teams_and_leaderboard_history`**: 
  - Verifies that participants see their team memberships (with "Captain" label if applicable).
  - Verifies that their past performance (leaderboard ranks and scores) is displayed.
- **`test_profile_for_jury_shows_pending_and_completed_reviews`**: 
  - Splits the jury view into "Pending Reviews" (teams assigned but not scored) and "Completed Reviews" (already scored).
- **`test_profile_for_organizer_shows_managed_contests`**: 
  - Displays a list of contests the user is organizing, including their current status.
- **`test_profile_empty_states_render_for_user_without_related_data`**: 
  - Ensures clean "empty state" messages (e.g., "You are not part of any teams yet") are shown instead of just blank white space.
