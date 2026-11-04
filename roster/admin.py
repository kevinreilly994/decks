"""Admin configured for hand curation of the roster (Phase 1 primary UI)."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    DJ,
    EngagementSnapshot,
    Genre,
    Management,
    PopularityScore,
    Release,
    SocialAccount,
    Show,
)


class ManagementInline(admin.StackedInline):
    model = Management
    extra = 0
    can_delete = False
    verbose_name_plural = "Management & booking"


class SocialAccountInline(admin.TabularInline):
    model = SocialAccount
    extra = 1


class ShowInline(admin.TabularInline):
    model = Show
    extra = 1
    ordering = ("date",)


class ReleaseInline(admin.TabularInline):
    model = Release
    extra = 1


class EngagementSnapshotInline(admin.TabularInline):
    model = EngagementSnapshot
    extra = 1


@admin.register(DJ)
class DJAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "primary_genre",
        "home_base",
        "availability",
        "score_display",
    )
    list_filter = ("primary_genre", "availability", "is_active")
    search_fields = ("name", "real_name", "home_base")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("headshot_preview", "created_at", "updated_at")
    inlines = [
        ManagementInline,
        SocialAccountInline,
        ShowInline,
        ReleaseInline,
        EngagementSnapshotInline,
    ]

    @admin.display(description="Score", ordering="popularity__score")
    def score_display(self, obj):
        return obj.score if obj.score is not None else "-"

    @admin.display(description="Headshot")
    def headshot_preview(self, obj):
        if obj.headshot:
            return format_html(
                '<img src="{}" style="height:80px;border-radius:8px">',
                obj.headshot.url,
            )
        return "No headshot uploaded"


@admin.register(PopularityScore)
class PopularityScoreAdmin(admin.ModelAdmin):
    list_display = (
        "dj",
        "score",
        "delta_7d",
        "streaming_component",
        "social_component",
        "engagement_component",
        "demand_component",
        "computed_at",
    )
    ordering = ("-score",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Show)
admin.site.register(Release)
admin.site.register(EngagementSnapshot)
