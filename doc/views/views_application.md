# Views: Applications

## ApplyToContestView
- **Path**: `app.views.views_application.ApplyToContestView`

### Overview
Handles initial participant or jury applications to a contest.

---

## AdminApplicationListView
- **Path**: `app.views.views_application.AdminApplicationListView`

### Overview
Organizer view listing all `PENDING` applications (Teams, Juries, and Participants) for a specific contest.

---

## ApplicationActionView
- **Path**: `app.views.views_application.ApplicationActionView`

### Overview
Handles the approval or rejection of an application.
- **On Approval**: Adds the user/team to the contest or team participants.
- **Notification**: Sends an automated notification to the applicant about the status update.
