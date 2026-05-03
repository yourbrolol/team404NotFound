# 📤 Test Documentation: `test_submission.py`

## Purpose
This test suite covers the submission process for contest rounds. It ensures that teams can correctly submit their work, that submissions follow unique constraints, and that access permissions are strictly enforced for both creating and viewing submissions.

## Test Classes

### 1. `SubmissionModelTest`
Focuses on the `Submission` model's constraints and helper methods.
- **`test_create_submission_with_valid_data`**: Verifies that all fields (GitHub, Video, Demo, Description) are correctly saved.
- **`test_unique_together_round_team`**: Ensures a team can only have **one** submission per round.
- **`test_is_editable`**: Validates the `is_editable` property based on:
  - Round status (`ACTIVE` vs `SUBMISSION_CLOSED`).
  - Current time vs Round deadline.
- **`test_cascade_delete`**: Verifies that deleting a team or a round also removes the associated submissions.

### 2. `SubmissionUITest`
Tests the views and permissions related to submissions.
- **`test_submission_form_access_denied_for_non_team_members`**: Prevents users from submitting for teams they don't belong to.
- **`test_submission_creation_success`**: Tests the POST request for creating a new submission.
- **`test_submission_edit_success`**: Verifies that submitting the form again for the same round updates the existing submission instead of creating a new one.
- **`test_submission_creation_denied_after_deadline`**: Ensures that even an `ACTIVE` round rejects submissions if the current time is past the deadline.
- **`test_submission_detail_visibility`**: 
  - **Allowed**: Team members, Organizers, and Jury members.
  - **Denied**: Participants from other teams.
- **`test_round_submissions_list_permissions`**: 
  - **Allowed**: Organizers and Jury members can see the list of all submissions.
  - **Denied**: Regular participants cannot see other teams' submissions in a list.
