from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Contest, User

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
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        now = timezone.now()
        if start_date and start_date < now:
            self.add_error('start_date', 'Start date cannot be in the past.')
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date cannot be before start date.')
        return cleaned_data
    class Meta:
        model = Contest
        fields = ['name', 'description', 'start_date', 'end_date', 'is_draft']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter contest name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'What is this contest about?'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-input'}),
        }
