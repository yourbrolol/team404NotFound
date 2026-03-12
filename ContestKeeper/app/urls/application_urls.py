from .. import views
from django.urls import path

urlpatterns = [
    path("<int:pk>/approve/", views.ApproveApplicationView.as_view(), name="approve_application"),
    path("<int:pk>/reject/", views.RejectApplicationView.as_view(), name="reject_application")
]