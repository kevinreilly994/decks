"""Buyer-facing URLs for the roster app."""
from django.urls import path

from . import views

app_name = "roster"

urlpatterns = [
    path("", views.directory, name="directory"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("shortlist/", views.shortlist, name="shortlist"),
    path("shortlist/toggle/<int:pk>/", views.shortlist_toggle, name="shortlist_toggle"),
    path("dj/<slug:slug>/", views.dj_detail, name="dj_detail"),
]
