from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone, translation
from datetime import timedelta
from app.models import Contest, Application, Team, User

class RegistrationControlTask10Test(TestCase):
    def setUp(self):
        translation.activate('en')
        self.organizer = User.objects.create_user(username='org', password='password', role=User.Role.ORGANIZER)
        self.participant = User.objects.create_user(username='parti', password='password', role=User.Role.PARTICIPANT)
        
        self.contest = Contest.objects.create(
            name='Reg Control Contest',
            description='Test registration window',
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=10),
            registration_start=timezone.now() + timedelta(days=1),
            registration_end=timezone.now() + timedelta(days=2),
            organizer=self.organizer,
            is_draft=False
        )
        self.client = Client()

    def test_team_create_before_registration_fails(self):
        # Registration starts in 1 day
        self.client.force_login(self.participant)
        url = reverse('team_create', kwargs={'pk': self.contest.pk})
        response = self.client.post(url, {'name': 'Early Birds'})
        # Should redirect to contest_detail (302)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Team.objects.filter(name='Early Birds').exists())

    def test_apply_after_registration_fails(self):
        # Set registration to the past
        self.contest.registration_start = timezone.now() - timedelta(days=5)
        self.contest.registration_end = timezone.now() - timedelta(days=1)
        self.contest.save()
        
        self.client.force_login(self.participant)
        url = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'participant'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Application.objects.count(), 0)

    def test_admin_application_list_grouping(self):
        # Open registration
        self.contest.registration_start = timezone.now() - timedelta(days=1)
        self.contest.registration_end = timezone.now() + timedelta(days=1)
        self.contest.save()
        self.contest.refresh_from_db()
        
        # Create a team application
        self.client.force_login(self.participant)
        url = reverse('team_create', kwargs={'pk': self.contest.pk})
        res_team = self.client.post(url, {'name': 'New Team'}, follow=True)
        # Success redirects to contest_detail
        self.assertEqual(res_team.status_code, 200) 
        self.assertTrue(Team.objects.filter(name='New Team').exists())
        
        # Create a jury application
        jury_user = User.objects.create_user(username='jury_cand', password='password', role=User.Role.JURY)
        self.client.force_login(jury_user)
        url_jury = reverse('apply_to_contest', kwargs={'pk': self.contest.pk, 'app_type': 'jury'})
        self.client.post(url_jury, follow=True)
        
        # Check admin list
        self.client.force_login(self.organizer)
        url_admin = reverse('admin_application_list', kwargs={'pk': self.contest.pk})
        response = self.client.get(url_admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['team_apps']), 1)
        self.assertEqual(len(response.context['jury_apps']), 1)

    def test_application_action_redirects_back_to_list(self):
        app = Application.objects.create(
            user=self.participant,
            contest=self.contest,
            application_type=Application.Type.PARTICIPANT,
            status=Application.Status.PENDING
        )
        self.client.force_login(self.organizer)
        url = reverse('approve_application', kwargs={'pk': app.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('admin_application_list', kwargs={'pk': self.contest.pk}))
