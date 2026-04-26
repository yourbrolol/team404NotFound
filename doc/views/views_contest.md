# Views: Contest Management

## ContestListView
- **Path**: `app.views.views_contest.ContestListView`
- **Inherits from**: `django.views.generic.ListView`

### Overview
Provides a JSON-formatted list of all contests that are not in `DRAFT` status.

### Key Methods
- `get_queryset()`: Excludes draft contests and returns values.
- `render_to_response()`: Returns a `JsonResponse`.

---

## ContestDetailView
- **Path**: `app.views.views_contest.ContestDetailView`
- **Inherits from**: `django.views.generic.DetailView`

### Overview
Displays comprehensive information about a single contest, including registration status, upcoming events, and application summaries.

### Key Methods
- `get_object()`: Ensures that draft contests are only accessible to their organizers.
- `get_context_data()`: Injects user-specific team info, pending applications, and the active round into the template.

---

## ContestFormView
- **Path**: `app.views.views_contest.ContestFormView`
- **Inherits from**: `app.views.views_base.RedirectToRegisterMixin`, `django.views.View`

### Overview
A dual-purpose view for creating new contests and editing existing ones.

### Key Methods
- `get()`: Renders the contest form.
- `post()`: Validates and saves the contest instance. Assigns the current user as the organizer for new contests.

---

## ContestDeleteView
- **Path**: `app.views.views_contest.ContestDeleteView`
- **Inherits from**: `app.views.views_base.OrganizerRequiredMixin`, `django.views.View`

### Overview
Handles the deletion of a contest. Requires the user to be the contest organizer.

### Key Methods
- `post()`: Deletes the contest and redirects to the dashboard.
