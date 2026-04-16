from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from ..models import Notification
from .views_base import RedirectToRegisterMixin


class NotificationListView(RedirectToRegisterMixin, ListView):
    model = Notification
    template_name = "app/notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return self.request.user.notifications.all()


class MarkNotificationReadView(RedirectToRegisterMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(request.user.notifications, pk=pk)
        notification.is_read = True
        notification.save()
        if notification.link:
            return redirect(notification.link)
        return redirect("notification_list")


class MarkAllReadView(RedirectToRegisterMixin, View):
    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect("notification_list")
