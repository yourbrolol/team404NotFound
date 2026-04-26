# Models: Schedule

## ScheduleEvent Class
- **Path**: `app.models.ScheduleEvent`
- **Inherits from**: `django.db.models.Model`

### Overview
Represents a specific event on the contest timeline. Used to display the contest schedule to participants.

### Key Attributes
- `contest`: `ForeignKey` to `Contest`. The contest this event belongs to.
- `title`: `CharField` (max 200). The name of the event.
- `description`: `TextField` (optional). Additional details about the event.
- `start_time`: `DateTimeField`. When the event begins.
- `end_time`: `DateTimeField` (optional). When the event ends.
- `event_type`: `CharField` with choices: `ROUND`, `DEADLINE`, `WORKSHOP`, `OTHER`.
- `round`: `ForeignKey` to `Round` (optional). Links the event to a specific contest round.
- `order`: `PositiveIntegerField`. Used for sorting events that start at the same time.

### Meta
- `ordering`: `['start_time', 'order']`.
