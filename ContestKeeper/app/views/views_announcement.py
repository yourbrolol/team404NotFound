from django.contrib import messages
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView

from ..forms import AnnouncementForm
from ..models import Announcement, Notification
from ..services import notify_contest_participants
from .views_base import ContestContextMixin, OrganizerRequiredMixin


class AnnouncementListView(ContestContextMixin, ListView):
    model = Announcement
    template_name = "app/announcements/announcements.html"
    context_object_name = "announcements"

    def get_queryset(self):
        return Announcement.objects.filter(contest=self.contest)


class AnnouncementCreateView(OrganizerRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "app/announcements/announcement_form.html"

    def form_valid(self, form):
        form.instance.contest = self.contest
        form.instance.author = self.request.user
        response = super().form_valid(form)

        if form.cleaned_data.get("notify_participants"):
            notify_contest_participants(
                self.contest,
                Notification.Type.ANNOUNCEMENT,
                f"New announcement: {form.instance.title}",
                form.instance.content[:200] + "...",
                link=reverse("announcement_list", kwargs={"pk": self.contest.pk})
            )
        messages.success(self.request, "Announcement published successfully.")
        return response

    def get_success_url(self):
        return reverse("announcement_list", kwargs={"pk": self.contest.pk})


class AnnouncementDeleteView(OrganizerRequiredMixin, DeleteView):
    model = Announcement
    template_name = "app/announcements/announcement_confirm_delete.html"

    def get_success_url(self):
        return reverse("announcement_list", kwargs={"pk": self.contest.pk})
