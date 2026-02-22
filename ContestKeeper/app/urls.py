from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("contests/", views.contest_list, name="contest_list"),
    path("contests/new/", views.contest_create, name="contest_create"),
    path("contests/<int:pk>/", views.contest_detail, name="contest_detail"),
]
