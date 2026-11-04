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
    change_list_template = "admin/roster/dj/change_list.html"
    actions = ["sync_providers"]
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

    def get_urls(self):
        from django.urls import path
        extra = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv),
                name="roster_dj_import_csv",
            ),
        ]
        return extra + super().get_urls()

    def import_csv(self, request):
        from django.contrib import messages
        from django.core.management import call_command
        from django.shortcuts import redirect
        from django.template.response import TemplateResponse

        from .importers import import_djs_from_file

        if request.method == "POST":
            upload = request.FILES.get("csv_file")
            if not upload:
                self.message_user(request, "No file uploaded.", level=messages.ERROR)
                return redirect("..")
            result = import_djs_from_file(upload)
            try:
                call_command("recompute_scores")
            except Exception:
                pass
            self.message_user(
                request,
                f"Imported {result['created']} new and {result['updated']} updated DJ(s).",
                level=messages.SUCCESS,
            )
            for err in result["errors"][:20]:
                self.message_user(request, err, level=messages.WARNING)
            return redirect("..")

        context = {
            **self.admin_site.each_context(request),
            "title": "Import DJs from CSV",
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/roster/dj/import_csv.html", context)

    @admin.action(description="Sync releases & shows from providers (Spotify, Bandsintown)")
    def sync_providers(self, request, queryset):
        from django.contrib import messages

        from .providers import get_provider, sync_dj
        from .scoring import recompute_all

        providers = []
        for name in ("spotify", "bandsintown"):
            try:
                p = get_provider(name)
            except ValueError:
                continue
            if getattr(type(p), "is_configured", lambda: True)():
                providers.append(p)
        if not providers:
            self.message_user(
                request,
                "No providers configured. Set SPOTIFY_CLIENT_ID/SECRET and/or "
                "BANDSINTOWN_APP_ID in the environment.",
                level=messages.ERROR,
            )
            return

        shows = releases = errors = count = 0
        for dj in queryset:
            count += 1
            for p in providers:
                try:
                    c = sync_dj(dj, p)
                    shows += c["shows"]
                    releases += c["releases"]
                except Exception:
                    errors += 1
        try:
            recompute_all()
        except Exception:
            pass
        self.message_user(
            request,
            f"Synced {count} DJ(s) via {len(providers)} provider(s): "
            f"{releases} releases, {shows} shows, {errors} error(s).",
            level=messages.WARNING if errors else messages.SUCCESS,
        )


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
