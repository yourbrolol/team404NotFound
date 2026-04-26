# Views: Analytics & Schedule

## OrganizerAnalyticsView
- **Path**: `app.views.views_analytics.OrganizerAnalyticsView`

### Overview
A comprehensive analytics dashboard for organizers.
- **Submission Stats**: Bar charts showing submission progress per round.
- **Score Stats**: Average scores per criterion.
- **Jury Progress**: Tracking how many evaluations each jury member has completed.
- **Score Distribution**: A histogram of total team scores.

---

## Schedule Management
Views for managing the contest timeline:
- **ScheduleView**: Displays the chronological list of events (Rounds, Deadlines, etc.).
- **ScheduleEventCreateView**: Manually add a custom event to the schedule.
- **ScheduleEventDeleteView**: Remove an event.
- **RegenerateScheduleView**: Automatically populates the schedule based on existing rounds.
