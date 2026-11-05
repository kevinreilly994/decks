"""Data model for the Decks roster.

Mirrors the Phase 0 prototype per-DJ data shape. Presentation formatting is kept
out of the models; helper properties provide the few convenience accessors the
admin uses.
"""
from __future__ import annotations

from django.db import models
from django.utils.text import slugify


class Availability(models.TextChoices):
    AVAILABLE = "available", "Available"
    TENTATIVE = "tentative", "Tentative"
    BOOKED = "booked", "Booked / Limited"


class Platform(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    SPOTIFY = "spotify", "Spotify"
    SOUNDCLOUD = "soundcloud", "SoundCloud"
    TIKTOK = "tiktok", "TikTok"
    YOUTUBE = "youtube", "YouTube"


class ShowStatus(models.TextChoices):
    CONFIRMED = "confirmed", "Confirmed"
    OFFER = "offer", "Offer out"
    PLAYED = "played", "Played"


class DataSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    SPOTIFY = "spotify", "Spotify"
    BANDSINTOWN = "bandsintown", "Bandsintown"
    SONGKICK = "songkick", "Songkick"
    INSTAGRAM = "instagram", "Instagram"


class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DJ(models.Model):
    name = models.CharField(max_length=120)
    real_name = models.CharField(max_length=120, blank=True, help_text="Internal only")
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    primary_genre = models.ForeignKey(
        Genre, on_delete=models.PROTECT, related_name="primary_djs"
    )
    genres = models.ManyToManyField(Genre, blank=True, related_name="djs")
    home_base = models.CharField(max_length=120, help_text="e.g. Berlin, DE")
    bio = models.TextField(blank=True)
    headshot = models.ImageField(upload_to="headshots/", blank=True)
    headshot_source_url = models.URLField(
        blank=True, help_text="Where the headshot came from (provenance)"
    )
    spotify_artist_id = models.CharField(
        max_length=64, blank=True, help_text="Spotify artist ID for live sync"
    )
    bandsintown_artist = models.CharField(
        max_length=160, blank=True,
        help_text="Bandsintown artist name (defaults to the DJ name)",
    )
    availability = models.CharField(
        max_length=12, choices=Availability.choices, default=Availability.AVAILABLE
    )
    fee_min = models.PositiveIntegerField(null=True, blank=True)
    fee_max = models.PositiveIntegerField(null=True, blank=True)
    fee_currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "DJ"
        verbose_name_plural = "DJs"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def fee_display(self) -> str:
        sym = {"USD": "$", "EUR": "EUR ", "GBP": "GBP "}.get(self.fee_currency, "")
        if self.fee_min and self.fee_max:
            return f"{sym}{self.fee_min // 1000}k-{self.fee_max // 1000}k"
        if self.fee_min:
            return f"from {sym}{self.fee_min // 1000}k"
        return "-"

    @property
    def score(self):
        pop = getattr(self, "popularity", None)
        return pop.score if pop else None

    def upcoming_shows(self):
        return self.shows.exclude(status=ShowStatus.PLAYED).order_by("date")

    def past_shows(self):
        return self.shows.filter(status=ShowStatus.PLAYED).order_by("-date")

    def latest_snapshot(self):
        cache = getattr(self, "prefetched_snapshots", None)
        if cache is not None:
            return cache[0] if cache else None
        return self.snapshots.order_by("-captured_on").first()

    def next_show(self):
        cache = getattr(self, "prefetched_shows", None)
        if cache is not None:
            return next((s for s in cache if s.status != ShowStatus.PLAYED), None)
        return self.shows.exclude(status=ShowStatus.PLAYED).order_by("date").first()


class SocialAccount(models.Model):
    dj = models.ForeignKey(DJ, on_delete=models.CASCADE, related_name="socials")
    platform = models.CharField(max_length=12, choices=Platform.choices)
    handle = models.CharField(max_length=120)
    url = models.URLField(blank=True)
    follower_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["platform"]
        unique_together = ("dj", "platform")

    def __str__(self) -> str:
        return f"{self.get_platform_display()}: {self.handle}"


class Management(models.Model):
    dj = models.OneToOneField(DJ, on_delete=models.CASCADE, related_name="management")
    manager_name = models.CharField(max_length=120)
    agency = models.CharField(max_length=120, blank=True)
    booking_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    booking_notes = models.TextField(blank=True, help_text="Rider, travel, deposit terms")

    class Meta:
        verbose_name = "Management & booking"
        verbose_name_plural = "Management & booking"

    def __str__(self) -> str:
        if self.agency:
            return f"{self.manager_name} ({self.agency})"
        return self.manager_name


class Show(models.Model):
    dj = models.ForeignKey(DJ, on_delete=models.CASCADE, related_name="shows")
    date = models.DateField(db_index=True)
    event_name = models.CharField(max_length=160)
    venue_city = models.CharField(max_length=160)
    status = models.CharField(
        max_length=12, choices=ShowStatus.choices, default=ShowStatus.OFFER, db_index=True
    )
    source = models.CharField(
        max_length=12, choices=DataSource.choices, default=DataSource.MANUAL
    )

    class Meta:
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.event_name} - {self.date}"


class Release(models.Model):
    dj = models.ForeignKey(DJ, on_delete=models.CASCADE, related_name="releases")
    title = models.CharField(max_length=160)
    label = models.CharField(max_length=120, blank=True)
    released_on = models.DateField()
    play_count = models.PositiveBigIntegerField(null=True, blank=True)
    url = models.URLField(blank=True)
    source = models.CharField(
        max_length=12, choices=DataSource.choices, default=DataSource.MANUAL
    )

    class Meta:
        ordering = ["-released_on"]

    def __str__(self) -> str:
        return self.title


class EngagementSnapshot(models.Model):
    dj = models.ForeignKey(DJ, on_delete=models.CASCADE, related_name="snapshots")
    captured_on = models.DateField(db_index=True)
    spotify_monthly = models.PositiveBigIntegerField(null=True, blank=True)
    instagram_followers = models.PositiveBigIntegerField(null=True, blank=True)
    tiktok_followers = models.PositiveBigIntegerField(null=True, blank=True)
    soundcloud_followers = models.PositiveBigIntegerField(null=True, blank=True)
    engagement_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="Percent"
    )
    source = models.CharField(
        max_length=12, choices=DataSource.choices, default=DataSource.MANUAL
    )

    class Meta:
        ordering = ["-captured_on"]
        unique_together = ("dj", "captured_on")

    def __str__(self) -> str:
        return f"{self.dj.name} @ {self.captured_on}"

    @property
    def social_total(self) -> int:
        return sum(
            v or 0
            for v in (
                self.instagram_followers,
                self.tiktok_followers,
                self.soundcloud_followers,
            )
        )


class PopularityScore(models.Model):
    dj = models.OneToOneField(DJ, on_delete=models.CASCADE, related_name="popularity")
    score = models.PositiveSmallIntegerField(default=0)
    streaming_component = models.SmallIntegerField(default=0)
    social_component = models.SmallIntegerField(default=0)
    engagement_component = models.SmallIntegerField(default=0)
    demand_component = models.SmallIntegerField(default=0)
    delta_7d = models.SmallIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-score"]

    def __str__(self) -> str:
        return f"{self.dj.name}: {self.score}"
