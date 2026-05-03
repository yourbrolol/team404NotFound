# 🔗 Test Documentation: `test_integration.py`

## Purpose
This module contains detailed integration tests for ContestKeeper's main user scenarios (TASK-33). It covers complex end-to-end workflows, access control, registration windows, and the notification pipeline.

## Test Classes

### 1. `TestParticipantEndToEndFlow`
Simulates a full participant journey.
- **Workflow**: Registration → Team creation → Join team → Submission (including updates) → Evaluation → Viewing Leaderboard.
- **Key Checks**: Ensures submissions are editable while the round is open but locked once closed.

### 2. `TestOrganizerContestLifecycle`
Focuses on the administrative side of a contest.
- **Workflow**: Create draft → Publish → Add criteria → Post announcements → Generate schedule from rounds.
- **Key Checks**: Status transition from `DRAFT` to `REGISTRATION` and automatic generation of `ScheduleEvent` objects.

### 3. `TestJuryEvaluationFlow`
Covers the jury member's workflow.
- **Workflow**: Login → View assigned teams → Submit scores → Read-only check after finalization.
- **Key Checks**: Ensures that after the evaluation phase is marked `COMPLETED`, the scoring forms become read-only or inaccessible for further edits.

### 4. `TestAccessControl`
Strictly tests permissions and authorization.
- **Test Cases**:
  - Non-captains cannot kick members.
  - Non-organizers cannot activate rounds.
  - Non-jury members cannot access evaluation pages.
  - Unauthenticated users are redirected to login and cannot mutate data (e.g., create teams).

### 5. `TestRegistrationWindow`
Ensures that registration timing rules are respected.
- **Test Cases**:
  - Blocks team creation if the registration window has ended.
  - Blocks team creation if the registration window hasn't started yet.

### 6. `TestNotificationPipeline`
Validates the delivery of system notifications.
- **Test Cases**:
  - Notifications for application approval.
  - Notifications for the start of a round sent to all team participants.
  - Notifications for announcements.
