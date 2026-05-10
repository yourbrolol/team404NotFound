from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from app.models import Contest, User, Announcement, ScheduleEvent, Submission, Team, ScoringCriterion, RoleApplication

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name")

class ProfileBioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("bio",)
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": _("Tell us about yourself...")}),
        }

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "bio")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Your username")}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": _("Your email address")}),
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Your first name")}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Your last name")}),
            "bio": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": _("Tell us about yourself...")}),
        }

class ContestForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        reg_start = cleaned_data.get('registration_start')
        reg_end = cleaned_data.get('registration_end')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if reg_start and reg_end and reg_end < reg_start:
            self.add_error('registration_end', _('Registration end cannot be before registration start.'))
        
        if reg_end and start_date and start_date < reg_end:
            self.add_error('start_date', _('Contest start date cannot be before registration end.'))
            
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _('Contest end date cannot be before start date.'))
            
        return cleaned_data

    class Meta:
        model = Contest
        fields = [
            'name', 'description', 'registration_start', 'registration_end', 
            'start_date', 'end_date', 'max_teams', 'format', 'is_draft'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Enter contest name')}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': _('What is this contest about?')}),
            'registration_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}, format='%Y-%m-%dT%H:%M'),
            'registration_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}, format='%Y-%m-%dT%H:%M'),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}, format='%Y-%m-%dT%H:%M'),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}, format='%Y-%m-%dT%H:%M'),
            'max_teams': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': _('No limit if empty')}),
            'format': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Online, Onsite, Hybrid...')}),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }


class AnnouncementForm(forms.ModelForm):
    notify_participants = forms.BooleanField(required=False, initial=True, label=_("Notify participants"), help_text=_("Send notification to all participants"))

    class Meta:
        model = Announcement
        fields = ["title", "content", "is_pinned"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Announcement title")}),
            "content": forms.Textarea(attrs={"class": "form-input", "rows": 5, "placeholder": _("Announcement content...")}),
            "is_pinned": forms.CheckboxInput(),
        }


class ScheduleEventForm(forms.ModelForm):
    class Meta:
        model = ScheduleEvent
        fields = ["title", "description", "start_time", "end_time", "event_type"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Event title")}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": _("Short description")}),
            "start_time": forms.DateTimeInput(attrs={"type": "hidden"}, format='%Y-%m-%dT%H:%M'),
            "end_time": forms.DateTimeInput(attrs={"type": "hidden"}, format='%Y-%m-%dT%H:%M'),
            "event_type": forms.Select(attrs={"class": "form-input"}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["github_url", "video_url", "live_demo_url", "description"]
        widgets = {
            "github_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://github.com/..."}),
            "video_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://youtube.com/..."}),
            "live_demo_url": forms.URLInput(attrs={"class": "form-input", "placeholder": _("https://... (optional)")}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4, "placeholder": _("What was done, how to run...")}),
        }

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description", "organization", "telegram_link", "discord_link", "website_link"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Team name")}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": _("What is your team about?")}),
            "organization": forms.TextInput(attrs={"class": "form-input", "placeholder": _("University, Company, etc.")}),
            "telegram_link": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://t.me/yourteam"}),
            "discord_link": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://discord.gg/yourteam"}),
            "website_link": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://yourteam.com"}),
        }

class ScoringCriterionForm(forms.ModelForm):
    class Meta:
        model = ScoringCriterion
        fields = ["name", "max_score", "weight", "aggregation_type", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": _("e.g. Design, Technical quality...")}),
            "max_score": forms.NumberInput(attrs={"class": "form-input"}),
            "weight": forms.NumberInput(attrs={"class": "form-input", "step": "0.1"}),
            "aggregation_type": forms.Select(attrs={"class": "form-input"}),
            "order": forms.NumberInput(attrs={"class": "form-input"}),
        }

class JuryEvaluationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        criteria = kwargs.pop('criteria', [])
        initial_scores = kwargs.pop('initial_scores', {})
        super().__init__(*args, **kwargs)
        
        for criterion in criteria:
            field_name = f'criterion_{criterion.id}'
            self.fields[field_name] = forms.DecimalField(
                label=criterion.name,
                min_value=0,
                max_value=criterion.max_score,
                initial=initial_scores.get(criterion.id),
                widget=forms.NumberInput(attrs={
                    'class': 'form-input',
                    'placeholder': f'0 - {criterion.max_score}',
                    'step': '0.01'
                }),
                help_text=_("Max points: %(max_score)s | Weight: %(weight)s") % {
                    'max_score': criterion.max_score,
                    'weight': criterion.weight
                }
            )


class RoleApplicationForm(forms.ModelForm):
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": _("Your password")})
    )
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": _("Confirm password")})
    )

    class Meta:
        model = RoleApplication
        fields = ("username", "email", "first_name", "last_name", "desired_role", "reason", "experience")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Username")}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": _("Email")}),
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": _("First Name")}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": _("Last Name")}),
            "desired_role": forms.Select(attrs={"class": "form-input"}),
            "reason": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": _("Why do you want to join?")}),
            "experience": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": _("Relevant experience")}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", _("Passwords do not match."))
        return cleaned_data
