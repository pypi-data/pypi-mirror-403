from django.urls import path
from . import views

urlpatterns = [
    path("toggle-sidebar/", views.toggle_sidebar, name="toggle_sidebar"),
]
