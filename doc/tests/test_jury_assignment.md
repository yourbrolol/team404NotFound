# 🧑‍⚖️ Test Documentation: `test_jury_assignment.py`

## Purpose
This test suite verifies the automatic and manual assignment of jury members to teams and ensures that access to evaluation forms and submission lists is correctly restricted based on those assignments.

## Test Class: `JuryAssignmentTest`
Tests the `assign_jury_to_teams` service and related view logic.

### Setup
- Creates an **Organizer** and **three Jury members**.
- Creates a **Contest** and **five Teams**.
- Adds all three jury members to the contest.

### Test Cases
1. **`test_assign_jury_to_teams_logic`** (Service Test)
   - **Scenario**: Use the `assign_jury_to_teams` service to distribute teams among juries.
   - **Action**: Request 2 reviews per team.
   - **Verification**: 
     - Total assignments equal 10 (5 teams * 2 reviews).
     - Each team has exactly 2 assignments.
     - Jury load is balanced (each jury gets 3 or 4 assignments).

2. **`test_assign_jury_view`** (View Test)
   - **Scenario**: Organizer uses the web interface to trigger jury assignment.
   - **Action**: POST to `assign_jury` with `min_reviews=1`.
   - **Verification**: 
     - Redirects to the jury list page.
     - Exactly 5 assignments are created in the database.

3. **`test_jury_evaluation_access_denied_without_assignment`**
   - **Scenario**: A jury member attempts to access the evaluation form for a team they aren't assigned to.
   - **Action**: Jury 1 (assigned only to Team 1) tries to access Team 0's evaluation page.
   - **Verification**: 
     - Accessing Team 0 returns 403 (Forbidden).
     - Accessing Team 1 returns 200 (OK).

4. **`test_round_submissions_list_filtering`**
   - **Scenario**: A jury member views the list of submissions for a round.
   - **Action**: Log in as Jury 1 and access the submissions list.
   - **Verification**: 
     - The list is filtered to only show teams assigned to Jury 1.
     - Teams not assigned to this jury member are hidden from the view.
