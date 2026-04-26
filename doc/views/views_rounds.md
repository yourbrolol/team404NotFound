# Views: Rounds & Submissions

## RoundListView
- **Path**: `app.views.views_rounds.RoundListView`

### Overview
Lists all rounds created for a contest. Available to organizers.

---

## RoundCreateView
- **Path**: `app.views.views_rounds.RoundCreateView`

### Overview
Form view for creating a new round. Sets initial status to `DRAFT`.

---

## RoundActivateView
- **Path**: `app.views.views_rounds.RoundActivateView`

### Overview
Starts a round. Transitions status from `DRAFT` to `ACTIVE` and notifies participants.

---

## RoundCloseSubmissionsView
- **Path**: `app.views.views_rounds.RoundCloseSubmissionsView`

### Overview
Manually closes the submission window for a round. Notifies jury members to begin evaluation.

---

## RoundDetailTeamView
- **Path**: `app.views.views_rounds.RoundDetailTeamView`

### Overview
A team-centric view of a round, showing deadlines, requirements, and the team's current submission status.

---

## SubmissionCreateEditView
- **Path**: `app.views.views_submission.SubmissionCreateEditView`

### Overview
Handles the creation and updating of team submissions. Only accessible while a round is `ACTIVE` and open.
