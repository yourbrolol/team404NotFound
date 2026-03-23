from .. import views
from django.urls import path

urlpatterns = [
    path("<int:pk>/approve/", views.ApplicationActionView.as_view(), {"action": "approve"}, name="approve_application"),
    path("<int:pk>/reject/",  views.ApplicationActionView.as_view(), {"action": "reject"},  name="reject_application"),
]
