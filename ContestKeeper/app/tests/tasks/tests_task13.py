from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.models import Contest, Round, ScheduleEvent, User

class ScheduleTask13Test(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='org', role=User.Role.ORGANIZER)
        self.contest = Contest.objects.create(
            name='Schedule Contest',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=5),
            organizer=self.organizer,
            is_draft=False
        )
        self.round = Round.objects.create(
            contest=self.contest,
            title='Round 1',
            order=1,
            start_time=timezone.now() + timedelta(hours=1),
            deadline=timezone.now() + timedelta(hours=3),
            status=Round.Status.ACTIVE
        )
        self.client = Client()

    def test_schedule_regeneration(self):
        self.client.force_login(self.organizer)
        url = reverse('schedule_regenerate', kwargs={'pk': self.contest.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('schedule', kwargs={'pk': self.contest.pk}))
        
        events = ScheduleEvent.objects.filter(contest=self.contest)
        # Should have 2 events: Start and Deadline for Round 1
        self.assertEqual(events.count(), 2)
        self.assertTrue(events.filter(title__contains='Start').exists())
        self.assertTrue(events.filter(title__contains='Deadline').exists())

    def test_schedule_sorting(self):
        # Create events out of order
        ScheduleEvent.objects.create(
            contest=self.contest,
            title='Later Event',
            start_time=timezone.now() + timedelta(hours=10)
        )
        ScheduleEvent.objects.create(
            contest=self.contest,
            title='Earlier Event',
            start_time=timezone.now() + timedelta(hours=1)
        )
        
        url = reverse('schedule', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)
        events = list(response.context['events'])
        self.assertEqual(events[0].title, 'Earlier Event')
        self.assertEqual(events[1].title, 'Later Event')

    def test_next_event_widget(self):
        # Future event
        event = ScheduleEvent.objects.create(
            contest=self.contest,
            title='Upcoming Keynote',
            start_time=timezone.now() + timedelta(hours=5)
        )
        
        url = reverse('contest_detail', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)
        if 'next_event' not in response.context:
            print("CONTEXT keys observed:", [k for k in response.context])
        self.assertEqual(response.context['next_event'], event)

    def test_next_event_widget_ignores_past(self):
        # Past event
        ScheduleEvent.objects.create(
            contest=self.contest,
            title='Past Workshop',
            start_time=timezone.now() - timedelta(hours=5)
        )
        
        url = reverse('contest_detail', kwargs={'pk': self.contest.pk})
        response = self.client.get(url)
        self.assertIsNone(response.context['next_event'])
