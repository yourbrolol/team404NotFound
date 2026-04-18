from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Contest, User, Announcement, ScheduleEvent, Submission, Team, ScoringCriterion

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name")

class ProfileBioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("bio",)
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Tell us about yourself..."}),
        }

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "bio")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": "Your username"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "Your email address"}),
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Your first name"}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Your last name"}),
            "bio": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Tell us about yourself..."}),
        }

class ContestForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        reg_start = cleaned_data.get('registration_start')
        reg_end = cleaned_data.get('registration_end')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if reg_start and reg_end and reg_end < reg_start:
            self.add_error('registration_end', 'Registration end cannot be before registration start.')
        
        if reg_end and start_date and start_date < reg_end:
            self.add_error('start_date', 'Contest start date cannot be before registration end.')
            
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'Contest end date cannot be before start date.')
            
        return cleaned_data

    class Meta:
        model = Contest
        fields = [
            'name', 'description', 'registration_start', 'registration_end', 
            'start_date', 'end_date', 'max_teams', 'format', 'is_draft'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter contest name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'What is this contest about?'}),
            'registration_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'registration_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'max_teams': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'No limit if empty'}),
            'format': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Online, Onsite, Hybrid...'}),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }


class AnnouncementForm(forms.ModelForm):
    notify_participants = forms.BooleanField(required=False, initial=True, help_text="Send notification to all participants")

    class Meta:
        model = Announcement
        fields = ["title", "content", "is_pinned"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Announcement title"}),
            "content": forms.Textarea(attrs={"class": "form-input", "rows": 5, "placeholder": "Announcement content..."}),
            "is_pinned": forms.CheckboxInput(),
        }


class ScheduleEventForm(forms.ModelForm):
    class Meta:
        model = ScheduleEvent
        fields = ["title", "description", "start_time", "end_time", "event_type"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Event title"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Short description"}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-input"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-input"}),
            "event_type": forms.Select(attrs={"class": "form-input"}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["github_url", "video_url", "live_demo_url", "description"]
        widgets = {
            "github_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://github.com/..."}),
            "video_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://youtube.com/..."}),
            "live_demo_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://... (optional)"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4, "placeholder": "What was done, how to run..."}),
        }

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description", "organization", "telegram_link", "discord_link", "website_link"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Team name"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "What is your team about?"}),
            "organization": forms.TextInput(attrs={"class": "form-input", "placeholder": "University, Company, etc."}),
            "telegram_link": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://t.me/yourteam"}),
            "discord_link": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://discord.gg/yourteam"}),
            "website_link": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://yourteam.com"}),
        }

class ScoringCriterionForm(forms.ModelForm):
    class Meta:
        model = ScoringCriterion
        fields = ["name", "max_score", "weight", "aggregation_type", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Design, Technical quality..."}),
            "max_score": forms.NumberInput(attrs={"class": "form-input"}),
            "weight": forms.NumberInput(attrs={"class": "form-input", "step": "0.1"}),
            "aggregation_type": forms.Select(attrs={"class": "form-input"}),
            "order": forms.NumberInput(attrs={"class": "form-input"}),
        }
