from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("contests/", views.contest_list, name="contest_list"),
    path("contests/new/", views.contest_create, name="contest_create"),
    path("contests/<int:pk>/", views.contest_detail, name="contest_detail"),
    path("contests/<int:pk>/edit/", views.contest_edit, name="contest_edit"),
    path("contests/<int:pk>/apply/<str:app_type>/", views.apply_to_contest, name="apply_to_contest"),
    path("applications/<int:pk>/approve/", views.approve_application, name="approve_application"),
    path("applications/<int:pk>/reject/", views.reject_application, name="reject_application"),
]
