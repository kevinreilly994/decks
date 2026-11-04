"""Root URL config. Phase 1: admin + a health check only (no buyer views yet)."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]

admin.site.site_header = "Decks - Booking Room"
admin.site.site_title = "Decks admin"
admin.site.index_title = "Roster management"
