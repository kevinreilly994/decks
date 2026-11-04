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
from urllib.parse import urlparse

from django.db import transaction

from .models import DJ, Availability, Genre, Management, SocialAccount

SOCIAL_COLUMNS = ("instagram", "spotify", "soundcloud", "tiktok")
_AVAIL = {a.value for a in Availability}


def _to_int(value):
    value = (value or "").strip().replace(",", "").replace("$", "")
    return int(value) if value.isdigit() else None


def import_djs_from_rows(rows):
    """Import an iterable of dict rows. Returns {created, updated, errors}.

    Only columns present and non-empty in a row are written, so re-importing a
    partial CSV never blanks previously-curated fields. Each row runs in its own
    transaction: a bad row is recorded in `errors` and skipped, not fatal.
    """
    result = {"created": 0, "updated": 0, "errors": []}
    for line, raw in enumerate(rows, start=2):  # row 1 is the header
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        name = row.get("name", "")
        if not name or not row.get("genre", ""):
            result["errors"].append(f"row {line}: missing required name or genre")
            continue
        try:
            with transaction.atomic():
                created = _apply_row(row, result, line)
        except Exception as exc:
            result["errors"].append(f"row {line} ({name}): {exc}")
            continue
        result["created" if created else "updated"] += 1
    return result


def _apply_row(row, result, line):
    name = row["name"]
    genre, _ = Genre.objects.get_or_create(name=row["genre"])
    dj = DJ.objects.filter(name=name).first()
    created = dj is None
    dj = dj or DJ(name=name)
    dj.primary_genre = genre

    if row.get("home_base"):
        dj.home_base = row["home_base"]
    if row.get("bio"):
        dj.bio = row["bio"]
    if row.get("availability"):
        av = row["availability"].lower()
        dj.availability = av if av in _AVAIL else Availability.AVAILABLE
    for col in ("fee_min", "fee_max"):
        if row.get(col):
            val = _to_int(row[col])
            if val is None:
                result["errors"].append(f"row {line}: unparseable {col}")
            else:
                setattr(dj, col, val)
    if row.get("spotify_artist_id"):
        dj.spotify_artist_id = row["spotify_artist_id"]
    if row.get("bandsintown_artist"):
        dj.bandsintown_artist = row["bandsintown_artist"]
    hs = row.get("headshot_source_url") or row.get("headshot_url") or ""
    if hs and urlparse(hs).scheme in ("http", "https"):
        dj.headshot_source_url = hs
    elif hs:
        result["errors"].append(f"row {line}: ignored non-http headshot URL")

    dj.save()
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
    return created


def import_djs_from_file(fileobj):
    """Import from a text/binary file-like object containing CSV."""
    data = fileobj.read()
    if isinstance(data, bytes):
        data = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(data))
    return import_djs_from_rows(reader)
