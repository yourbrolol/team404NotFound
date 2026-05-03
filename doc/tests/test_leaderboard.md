# 📊 Test Documentation: `test_leaderboard.py`

## Purpose
This test suite covers the leaderboard logic, including score computation, handling of missing scores, rank generation, tie detection, and data export.

## Test Classes

### 1. `LeaderboardLogicTest`
Tests the integration between the evaluation phase and the leaderboard visibility.
- **`test_contest_leaderboard_not_available_before_completion`**: Verifies that participants see a "not available" message if the evaluation is still in progress.
- **`test_finish_evaluation_creates_leaderboard_with_missing_scores`**: Ensures that an organizer can manually finish an evaluation even if some scores are missing, and that those missing scores are correctly recorded in the leaderboard entry.

### 2. `LeaderboardHelperFunctionsTest`
Tests the underlying helper functions in `app.leaderboard`.
- **`test_compute_leaderboard_orders_teams_by_weighted_score`**: 
  - **Scenario**: Two teams with different scores across multiple criteria with different weights.
  - **Action**: Compute the leaderboard.
  - **Verification**: Teams are ranked correctly based on their weighted total scores.
- **`test_get_missing_scores_reports_unscored_slots`**: Validates the detection of missing scores for specific team/jury/criterion combinations.
- **`test_save_leaderboard_persists_entries_and_marks_phase_complete`**: 
  - **Scenario**: All scores are submitted.
  - **Action**: Save the leaderboard.
  - **Verification**: `LeaderboardEntry` objects are created, the evaluation phase is marked as `COMPLETED`, and `all_scores_complete` is set to `True`. Also tests tie detection (`is_tied`).
- **`test_export_csv_returns_ranked_rows`**: Ensures the CSV export function returns a correctly formatted string containing ranks, team names, and scores.
