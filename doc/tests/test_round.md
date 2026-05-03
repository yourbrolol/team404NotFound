# 🔄 Test Documentation: `test_round.py`

## Purpose
This test suite validates the lifecycle of a contest round, including creation, activation, manual closure, deadline extension, and visibility rules for participants.

## Test Class: `RoundLogicTest`
Tests the `Round` model logic and the views used by organizers and teams.

### Setup
- Creates an **Organizer** and a **Participant**.
- Initializes a **Contest** and a **Team**.

### Test Cases
1. **Creation & Validation**
   - **`test_create_round_valid`**: Verifies that an organizer can create a round with all required fields. Ensures the round starts as a `DRAFT`.
   - **`test_create_round_invalid_deadline`**: Ensures round creation fails if the deadline is not after the start time.
   - **`test_create_round_empty_must_have`**: Ensures a round must have at least one checklist item in its `must_have` JSON field.

2. **Lifecycle Management**
   - **`test_activate_draft_round`**: Verifies that an organizer can transition a round from `DRAFT` to `ACTIVE`.
   - **`test_cannot_activate_non_draft`**: Prevents re-activating rounds that are already active or closed.
   - **`test_close_submissions_active_round`**: Verifies that an organizer can manually close a round for submissions.
   - **`test_extend_deadline_active_round`**: Tests the functionality to extend a round's deadline with a reason.
   - **`test_extend_deadline_future_only`**: Ensures that new deadlines must be in the future.

3. **Visibility & Permissions**
   - **`test_team_cannot_see_draft_round`**: Ensures that participants do not see rounds that are still in the `DRAFT` stage.
   - **`test_team_sees_active_round`**: Verifies that active rounds are visible to teams with appropriate status labels.
   - **`test_team_sees_closed_message`**: Verifies that closed rounds show a "CLOSED" status to participants.
   - **`test_organizer_can_only_edit_draft_rounds`**: Restricts editing of round details (like title and requirements) once a round has been activated.

4. **Internal Logic**
   - **`test_round_is_open_property`**: Tests the `is_open()` helper method which checks if the current time is between the start and deadline and if the status is `ACTIVE`.
