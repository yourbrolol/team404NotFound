# Forms Reference

This document describes the various form classes used for data entry and validation in ContestKeeper.

## Authentication Forms
- **UserRegistrationForm**: Inherits from `UserCreationForm`. Handles username, email, and basic user info.
- **UserSettingsForm**: For updating profile details (bio, email, names).

## Contest Management Forms
- **ContestForm**:
    - **Fields**: `name`, `description`, `registration_start/end`, `start_date/end_date`, `max_teams`, `format`, `is_draft`.
    - **Validation**: Ensures registration ends before contest starts, and contest ends after it starts.
- **AnnouncementForm**: For posting contest-wide news.
- **ScheduleEventForm**: For adding timeline events.
- **ScoringCriterionForm**: For defining what criteria teams are judged on.

## Team & Submission Forms
- **TeamForm**: Collects team identity and contact links (Telegram, Discord, Website).
- **SubmissionForm**: Used by teams to submit their GitHub repositories, demo videos, and live links for a round.

## Evaluation Forms
- **JuryEvaluationForm**:
    - **Type**: `django.forms.Form` (Dynamic).
    - **Overview**: Unlike other model forms, this is built dynamically in `__init__` based on the criteria defined for the specific contest.
    - **Fields**: Each criterion results in a `DecimalField` named `criterion_<id>`.
