# Models: Notifications & Schedule

## Notification Class
- **Path**: `app.models.Notification`

### Overview
Real-time alerts sent to users about contest events.

### Key Attributes
- `recipient`: `ForeignKey` to `User`.
- `notification_type`: Choice field (e.g., `ROUND_STARTED`, `DEADLINE_APPROACHING`).
- `title`: `CharField`.
- `message`: `TextField`.
- `is_read`: `BooleanField`.

---

## Announcement Class
- **Path**: `app.models.Announcement`

### Overview
Official messages posted by organizers for a contest.

### Key Attributes
- `contest`: `ForeignKey` to `Contest`.
- `title`: `CharField`.
- `content`: `TextField`.
- `is_pinned`: `BooleanField`.
- `author`: `ForeignKey` to `User`.

---

## ScheduleEvent Class
- **Path**: `app.models.ScheduleEvent`

### Overview
Timeline events for a contest (Rounds, Deadlines, Workshops).

### Key Attributes
- `contest`: `ForeignKey` to `Contest`.
- `title`: `CharField`.
- `start_time/end_time`: `DateTimeField`.
- `event_type`: Choice field (`ROUND`, `DEADLINE`, `WORKSHOP`, `OTHER`).
- `round`: Optional `ForeignKey` to `Round`.
