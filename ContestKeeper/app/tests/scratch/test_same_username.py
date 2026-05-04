from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationTest(TestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.username = 'testuser'
        self.password = 'password123'
        self.email = 'test@example.com'
        User.objects.create_user(username=self.username, password=self.password, email=self.email)

    def test_duplicate_username_registration(self):
        """Test that registering with an existing username fails."""
        response = self.client.post(self.register_url, {
            'username': self.username,
            'email': 'newuser@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        # Check that we stay on the register page (200 OK) and have error in context
        self.assertEqual(response.status_code, 200)
        # We can also check if the error message is present in the response
        self.assertContains(response, "User with this Username already exists.")

    def test_case_insensitive_username_registration(self):
        """Test that registering with a username that differs only in case fails."""
        response = self.client.post(self.register_url, {
            'username': self.username.upper(), # 'TESTUSER'
            'email': 'another@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User with this Username already exists.")