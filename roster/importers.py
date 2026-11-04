"""CSV bulk import for DJs.

Expected header columns (case-insensitive; unknown columns ignored):
  name, genre, home_base, availability, fee_min, fee_max, bio,
  manager_name, agency, booking_email, phone,
  instagram, spotify, soundcloud, tiktok,
  spotify_artist_id, bandsintown_artist, headshot_source_url

Only `name` and `genre` are required per row. Existing DJs (matched by name)
are updated, so re-importing is idempotent.
"""
from __future__ import annotations

import csv
import io

from .models import DJ, Availability, Genre, Management, SocialAccount

SOCIAL_COLUMNS = ("instagram", "spotify", "soundcloud", "tiktok")
_AVAIL = {a.value for a in Availability}


def _to_int(value):
    value = (value or "").strip().replace(",", "").replace("$", "")
    return int(value) if value.isdigit() else None


def import_djs_from_rows(rows):
    """Import an iterable of dict rows. Returns {created, updated, errors}."""
    result = {"created": 0, "updated": 0, "errors": []}
    for line, raw in enumerate(rows, start=2):  # row 1 is the header
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        name = row.get("name", "")
        genre_name = row.get("genre", "")
        if not name or not genre_name:
            result["errors"].append(f"row {line}: missing required name or genre")
            continue

        availability = row.get("availability", "").lower() or Availability.AVAILABLE
        if availability not in _AVAIL:
            availability = Availability.AVAILABLE

        genre, _ = Genre.objects.get_or_create(name=genre_name)
        dj, created = DJ.objects.update_or_create(
            name=name,
            defaults={
                "primary_genre": genre,
                "home_base": row.get("home_base", ""),
                "bio": row.get("bio", ""),
                "availability": availability,
                "fee_min": _to_int(row.get("fee_min")),
                "fee_max": _to_int(row.get("fee_max")),
                "spotify_artist_id": row.get("spotify_artist_id", ""),
                "bandsintown_artist": row.get("bandsintown_artist", ""),
                "headshot_source_url": row.get("headshot_source_url")
                or row.get("headshot_url", ""),
            },
        )
        dj.genres.add(genre)

        if any(row.get(k) for k in ("manager_name", "agency", "booking_email", "phone")):
            Management.objects.update_or_create(
                dj=dj,
                defaults={
                    "manager_name": row.get("manager_name", ""),
                    "agency": row.get("agency", ""),
                    "booking_email": row.get("booking_email", ""),
                    "phone": row.get("phone", ""),
                },
            )

        for platform in SOCIAL_COLUMNS:
            handle = row.get(platform, "")
            if handle:
                SocialAccount.objects.update_or_create(
                    dj=dj, platform=platform, defaults={"handle": handle}
                )

        result["created" if created else "updated"] += 1
    return result


def import_djs_from_file(fileobj):
    """Import from a text/binary file-like object containing CSV."""
    data = fileobj.read()
    if isinstance(data, bytes):
        data = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(data))
    return import_djs_from_rows(reader)
