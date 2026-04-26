# Models: Contest & Phases

## Contest Class
- **Path**: `app.models.Contest`
- **Inherits from**: `django.db.models.Model`

### Overview
The central entity representing a competition. Manages dates, participants, and status.

### Key Attributes
- `name`: `CharField` (max 100).
- `status`: `CharField` with choices: `DRAFT`, `REGISTRATION`, `RUNNING`, `FINISHED`.
- `is_draft`: `BooleanField`.
- `registration_start/end`: `DateTimeField` for registration period.
- `start_date/end_date`: `DateTimeField` for the contest duration.
- `organizer`: `ForeignKey` to `User`.
- `jurys`: `ManyToManyField` to `User`.
- `teams`: `ManyToManyField` to `Team`.

### Key Properties
- `is_registration_open`: Returns `True` if current time is within registration dates and not a draft.

---

## Round Class
- **Path**: `app.models.Round`
- **Inherits from**: `django.db.models.Model`

### Overview
A specific stage within a contest with its own deadline and requirements.

### Key Attributes
- `contest`: `ForeignKey` to `Contest`.
- `title`: `CharField` (max 200).
- `status`: `CharField` with choices: `DRAFT`, `ACTIVE`, `SUBMISSION_CLOSED`, `EVALUATED`.
- `start_time`: `DateTimeField`.
- `deadline`: `DateTimeField`.
- `order`: `PositiveIntegerField` (round number).

### Key Methods
- `is_active()`: `True` if active and started.
- `is_open()`: `True` if active and before deadline.
- `time_remaining()`: Returns `timedelta` until deadline.

---

## ContestEvaluationPhase Class
- **Path**: `app.models.ContestEvaluationPhase`
- **Inherits from**: `django.db.models.Model`

### Overview
Manages the evaluation state for a contest.

### Key Attributes
- `contest`: `OneToOneField` to `Contest`.
- `status`: `CharField` (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`).
- `trigger_type`: `CharField` (`AUTO`, `MANUAL`).
- `all_scores_complete`: `BooleanField`.
