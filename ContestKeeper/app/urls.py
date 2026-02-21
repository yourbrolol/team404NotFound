from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.RegisterView.as_view(), name="register"),
]