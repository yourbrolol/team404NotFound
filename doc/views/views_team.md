# Views: Team & Jury Management

## ViewTeamsView
- **Path**: `app.views.views_team.ViewTeamsView`

### Overview
Lists all teams participating in a specific contest. Shows pending team applications to organizers.

---

## TeamDetailView
- **Path**: `app.views.views_team.TeamDetailView`

### Overview
Displays team details, members, and pending join requests (visible to the team captain).

---

## TeamCreateView
- **Path**: `app.views.views_team.TeamCreateView`

### Overview
Handles team creation for a contest.
- **Validation**: Checks registration dates and ensures the user isn't already in a team for this contest.
- **Action**: Creates the team and a corresponding `TEAM` application for the organizer's approval.

---

## TeamUpdateView
- **Path**: `app.views.views_team.TeamUpdateView`

### Overview
Allows team captains to edit team details (name, description, links).

---

## TeamJoinView
- **Path**: `app.views.views_team.TeamJoinView`

### Overview
Handles requests from participants to join a specific team. Creates a `PARTICIPANT` application.

---

## Team Management Actions
The following views handle specific team management tasks:
- **TeamKickView**: Captain removes a participant from the team.
- **TeamBlockView**: Captain removes a member and adds them to the team's blacklist.
- **TeamUnblockView**: Captain removes a user from the blacklist.

---

## ViewJurysView
- **Path**: `app.views.views_team.ViewJurysView`

### Overview
Lists all jury members assigned to a contest and their team assignments.
