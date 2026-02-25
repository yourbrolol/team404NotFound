from django.test import TestCase
from django.utils import timezone
from .models import Contest, User

class ContestModelTest(TestCase):
	def test_create_and_retrieve_contest(self):
		organizer = User.objects.create_user(username='org1', password='pass', role=User.Role.ORGANIZER)
		contest = Contest.objects.create(
			name='Test Contest',
			description='A test contest.',
			start_date=timezone.now(),
			end_date=timezone.now(),
			organizer=organizer,
			status=Contest.Status.DRAFT
		)
		retrieved = Contest.objects.get(name='Test Contest')
		self.assertEqual(retrieved.description, 'A test contest.')
		self.assertEqual(retrieved.organizer.username, 'org1')
