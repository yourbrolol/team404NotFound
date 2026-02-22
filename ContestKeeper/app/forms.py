from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Contest

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "email")

class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'description', 'start_date', 'end_date', 'jury', 'participants']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter contest name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'What is this contest about?'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'jury': forms.SelectMultiple(attrs={'class': 'form-input'}),
            'participants': forms.SelectMultiple(attrs={'class': 'form-input'}),
        }
