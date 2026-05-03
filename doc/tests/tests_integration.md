# 🔗 Test Documentation: `tests_integration.py`

## Purpose
This module contains supplementary integration tests for core ContestKeeper workflows, specifically focusing on draft visibility, pagination, and basic permission checks for round creation.

## Test Class: `ContestKeeperIntegrationTest`
A set of integration tests covering TASK-33 core requirements.

### Setup
- Creates an **Organizer**, a **Jury member**, and two **Participants**.
- Uses a single `django.test.Client` instance for sequential role-based testing.

### Test Cases
1. **`test_contest_creation_and_publish_flow`**
   - **Scenario**: Creating a draft contest and then publishing it.
   - **Verification**: Status transitions from `DRAFT` to `REGISTRATION` upon updating `is_draft=False`.
2. **`test_scoring_criterion_creation`**
   - **Scenario**: Directly creating a scoring criterion for a contest.
   - **Verification**: Checks that the criterion is correctly saved with its weight, max score, and order.
3. **`test_team_creation_and_join`**
   - **Scenario**: A participant creates a team for a contest.
   - **Verification**: Ensures the team is created and the user is set as the captain.
4. **`test_draft_contest_visibility_restriction`**
   - **Scenario**: Attempting to view a draft contest as a participant vs as an organizer.
   - **Verification**: Participants are denied access (302/403/404), while organizers can view the contest (200).
5. **`test_leaderboard_access_for_participant`**
   - **Scenario**: A participant attempts to view a contest leaderboard.
   - **Verification**: The leaderboard page renders correctly if entries exist.
6. **`test_round_creation_permission`**
   - **Scenario**: Participant vs Organizer attempting to create a round.
   - **Verification**: Participants are blocked; organizers are allowed.
7. **`test_leaderboard_pagination_rendering`**
   - **Scenario**: A contest with a large number of teams (55) and leaderboard entries.
   - **Verification**: Ensures the leaderboard page renders successfully even with many entries (pagination test).
