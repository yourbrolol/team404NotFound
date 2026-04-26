# Views: Authentication

## RegisterView
- **Path**: `app.views.views_auth.RegisterView`
- **Inherits from**: `django.views.generic.CreateView`

### Overview
Handles new user registration. Upon successful form submission, the user is automatically logged in and redirected to the home page.

### Key Attributes
- `form_class`: `UserRegistrationForm`.
- `template_name`: `"registration/register.html"`.
- `success_url`: `"/"`.

### Key Methods
- `form_valid(form)`: Saves the user, logs them in using `django.contrib.auth.login`, and performs the redirect.

### Usage Scenario
Used by participants and jury members to create their accounts on the platform.
