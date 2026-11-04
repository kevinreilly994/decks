"""Seed the roster with the 12 fictional demo DJs from the Phase 0 prototype.

All names, managers, agencies, and contacts are invented. Idempotent: re-running
updates the same records rather than duplicating them.
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from roster.models import (
    DJ,
    EngagementSnapshot,
    Genre,
    Management,
    Release,
    SocialAccount,
    Show,
)

SNAP = date(2026, 11, 1)
FUT = date(2026, 12, 6)
PAST = date(2025, 10, 11)
REL = date(2025, 6, 1)


def _socials(ig, sp, sc, tk):
    return [
        ("instagram", ig[0], f"https://instagram.com/{ig[0].lstrip('@')}", ig[1]),
        ("spotify", sp[0], "https://open.spotify.com/", sp[1]),
        ("soundcloud", sc[0], "https://soundcloud.com/", sc[1]),
        ("tiktok", tk[0], f"https://tiktok.com/{tk[0]}", tk[1]),
    ]


DJS = [
    {"name": "Nova Kane", "genre": "Melodic House", "city": "Berlin, DE",
     "avail": "tentative", "fee": (28000, 40000), "mgr": "Lena Vogt",
     "agency": "Nocturne Artists", "email": "book@nocturne.art", "phone": "+49 30 5540 1188",
     "bio": "Berlin-based melodic house architect known for sunrise closing sets.",
     "socials": _socials(("@novakane", 1204000), ("Nova Kane", 3410000), ("novakane", 410000), ("@novakane", 842000)),
     "snap": (3410000, 1204000, 842000, 410000, 6.8),
     "shows": [(FUT, "Printworks", "London, UK", "confirmed"), (PAST, "Fabric", "London, UK", "played")],
     "releases": [("Solstice", "Afterlife", REL, 4100000), ("Ember", "Afterlife", REL, 6900000)]},
    {"name": "Dexter Vale", "genre": "Tech House", "city": "London, UK",
     "avail": "available", "fee": (18000, 30000), "mgr": "Marcus Hyde",
     "agency": "Lowfreq Mgmt", "email": "hello@lowfreq.io", "phone": "+44 20 7946 0210",
     "bio": "Relentless tech-house groove merchant and London warehouse fixture.",
     "socials": _socials(("@dextervale", 881500), ("Dexter Vale", 2140000), ("dextervale", 690000), ("@dexvale", 1100000)),
     "snap": (2140000, 881500, 1100000, 690000, 7.9),
     "shows": [(FUT, "Club Space", "Miami, US", "confirmed"), (PAST, "DC-10", "Ibiza, ES", "played")],
     "releases": [("Pressure Drop", "Solid Grooves", REL, 3300000), ("Low End", "Repopulate Mars", REL, 5100000)]},
    {"name": "Saffron", "genre": "Deep House", "city": "Amsterdam, NL",
     "avail": "available", "fee": (14000, 22000), "mgr": "Pim de Vries",
     "agency": "Canal Collective", "email": "bookings@canalcollective.nl", "phone": "+31 20 428 9900",
     "bio": "Deep, hypnotic, vocal-led house with a devoted late-night following.",
     "socials": _socials(("@saffronsound", 642000), ("Saffron", 1610000), ("saffron", 880000), ("@saffron", 520000)),
     "snap": (1610000, 642000, 520000, 880000, 8.4),
     "shows": [(FUT, "Shelter", "Amsterdam, NL", "confirmed"), (PAST, "Panorama Bar", "Berlin, DE", "played")],
     "releases": [("Velour", "Dial", REL, 1200000), ("After Hours", "Running Back", REL, 2200000)]},
    {"name": "KULT", "genre": "Afro House", "city": "Lisbon, PT",
     "avail": "booked", "fee": (16000, 24000), "mgr": "Ines Carvalho",
     "agency": "Atlantico Bookings", "email": "book@atlantico.pt", "phone": "+351 21 350 7788",
     "bio": "Afro-house powerhouse blending Angolan percussion with club-ready low end.",
     "socials": _socials(("@kultmusic", 719000), ("KULT", 1870000), ("kult", 330000), ("@kult", 1400000)),
     "snap": (1870000, 719000, 1400000, 330000, 9.1),
     "shows": [(FUT, "Hi Ibiza", "Ibiza, ES", "confirmed"), (PAST, "Afro Nation", "Portimao, PT", "played")],
     "releases": [("Batida", "MoBlack", REL, 5800000), ("Kalunga", "Keinemusik", REL, 7400000)]},
    {"name": "Marlow", "genre": "Progressive House", "city": "Los Angeles, US",
     "avail": "available", "fee": (22000, 35000), "mgr": "Tara Bloom",
     "agency": "Sunset Live", "email": "td@sunsetlive.com", "phone": "+1 310 555 0142",
     "bio": "Big-room progressive with festival-scale drops and crossover appeal.",
     "socials": _socials(("@marlowmusic", 1510000), ("Marlow", 2790000), ("marlow", 210000), ("@marlow", 2200000)),
     "snap": (2790000, 1510000, 2200000, 210000, 4.6),
     "shows": [(FUT, "Echostage", "Washington DC, US", "confirmed"), (PAST, "Electric Zoo", "New York, US", "played")],
     "releases": [("Skyline", "Protocol", REL, 8200000), ("Overdrive", "Spinnin", REL, 11400000)]},
    {"name": "Ivy Sol", "genre": "Organic House", "city": "Tulum, MX",
     "avail": "tentative", "fee": (12000, 18000), "mgr": "Diego Ramos",
     "agency": "Selva Agency", "email": "hola@selva.mx", "phone": "+52 984 141 2200",
     "bio": "Organic, downtempo-to-house journeys built for jungle stages and sunrises.",
     "socials": _socials(("@ivysol", 512000), ("Ivy Sol", 1210000), ("ivysol", 450000), ("@ivysol", 380000)),
     "snap": (1210000, 512000, 380000, 450000, 8.9),
     "shows": [(FUT, "Zamna", "Tulum, MX", "confirmed"), (PAST, "Woomoon", "Ibiza, ES", "played")],
     "releases": [("Raiz", "All Day I Dream", REL, 2400000), ("Cenote", "Sol Selectas", REL, 3600000)]},
    {"name": "Delacroix", "genre": "Melodic Techno", "city": "Paris, FR",
     "avail": "available", "fee": (13000, 20000), "mgr": "Camille Fournier",
     "agency": "Minuit", "email": "contact@minuit.fr", "phone": "+33 1 42 60 3344",
     "bio": "Cinematic melodic techno with a dark romantic edge.",
     "socials": _socials(("@delacroix", 431000), ("Delacroix", 1080000), ("delacroix", 520000), ("@delacroix", 290000)),
     "snap": (1080000, 431000, 290000, 520000, 6.2),
     "shows": [(FUT, "Rex Club", "Paris, FR", "confirmed"), (PAST, "Concrete", "Paris, FR", "played")],
     "releases": [("Noir", "Afterlife", REL, 2900000), ("Reverie", "Stil vor Talent", REL, 3300000)]},
    {"name": "Jin Park", "genre": "Future House", "city": "Seoul, KR",
     "avail": "available", "fee": (11000, 17000), "mgr": "Soo-ah Lim",
     "agency": "Neon Seoul", "email": "book@neonseoul.kr", "phone": "+82 2 558 7700",
     "bio": "High-energy future house with a huge APAC following and TikTok virality.",
     "socials": _socials(("@jinpark", 961000), ("Jin Park", 1420000), ("jinpark", 180000), ("@jinpark", 3100000)),
     "snap": (1420000, 961000, 3100000, 180000, 7.3),
     "shows": [(FUT, "World Club Dome", "Seoul, KR", "confirmed"), (PAST, "Ultra Korea", "Seoul, KR", "played")],
     "releases": [("Neon Drive", "Future House Music", REL, 4500000), ("Hyperbeam", "Spinnin", REL, 6100000)]},
    {"name": "Echo Lane", "genre": "Deep House", "city": "New York, US",
     "avail": "tentative", "fee": (10000, 15000), "mgr": "Rayan Osei",
     "agency": "Borough Sound", "email": "info@boroughsound.nyc", "phone": "+1 212 555 0198",
     "bio": "Soulful, jazz-tinged deep house with a loyal NYC base.",
     "socials": _socials(("@echolane", 381000), ("Echo Lane", 912000), ("echolane", 610000), ("@echolane", 140000)),
     "snap": (912000, 381000, 140000, 610000, 6.7),
     "shows": [(FUT, "Output Reunion", "New York, US", "confirmed"), (PAST, "Nowadays", "New York, US", "played")],
     "releases": [("Harlem Blue", "Defected", REL, 1500000), ("Midnight Local", "Toy Tonics", REL, 2000000)]},
    {"name": "Vantablack", "genre": "Melodic Techno", "city": "Ibiza, ES",
     "avail": "available", "fee": (12000, 19000), "mgr": "Sofia Marin",
     "agency": "Isla Noir", "email": "book@islanoir.es", "phone": "+34 971 300 455",
     "bio": "Dark, driving peak-time melodic techno engineered for the biggest rooms.",
     "socials": _socials(("@vantablack", 561000), ("Vantablack", 1030000), ("vantablack", 470000), ("@vantablack", 410000)),
     "snap": (1030000, 561000, 410000, 470000, 5.9),
     "shows": [(FUT, "Fuse", "Brussels, BE", "confirmed"), (PAST, "Time Warp", "Mannheim, DE", "played")],
     "releases": [("Obsidian", "Drumcode", REL, 2100000), ("Eclipse", "Afterlife", REL, 3000000)]},
    {"name": "Mira Dune", "genre": "Melodic House", "city": "Barcelona, ES",
     "avail": "available", "fee": (9000, 14000), "mgr": "Joan Ferrer",
     "agency": "Mediterraneo Live", "email": "hola@medlive.es", "phone": "+34 93 412 6600",
     "bio": "Breakout melodic house talent with the highest engagement on the roster.",
     "socials": _socials(("@miradune", 341000), ("Mira Dune", 781000), ("miradune", 120000), ("@miradune", 660000)),
     "snap": (781000, 341000, 660000, 120000, 9.4),
     "shows": [(FUT, "Razzmatazz", "Barcelona, ES", "confirmed"), (PAST, "Monegros", "Fraga, ES", "played")],
     "releases": [("Duna", "Anjunadeep", REL, 1100000), ("Costa", "Sol Selectas", REL, 1400000)]},
    {"name": "BRUNO RMX", "genre": "Tech House", "city": "Miami, US",
     "avail": "available", "fee": (9000, 13000), "mgr": "Carla Mendez",
     "agency": "305 Collective", "email": "book@305collective.com", "phone": "+1 305 555 0176",
     "bio": "Latin-flavoured tech house with Miami pool-party energy.",
     "socials": _socials(("@brunormx", 451000), ("BRUNO RMX", 841000), ("brunormx", 260000), ("@brunormx", 780000)),
     "snap": (841000, 451000, 780000, 260000, 6.1),
     "shows": [(FUT, "E11even", "Miami, US", "confirmed"), (PAST, "III Points", "Miami, US", "played")],
     "releases": [("Caliente", "Repopulate Mars", REL, 1300000), ("Sabor", "Insomniac", REL, 1800000)]},
]


class Command(BaseCommand):
    help = "Seed the roster with 12 fictional demo DJs (idempotent)."

    def handle(self, *args, **options):
        for row in DJS:
            genre, _ = Genre.objects.get_or_create(name=row["genre"])
            dj, _ = DJ.objects.update_or_create(
                name=row["name"],
                defaults={
                    "primary_genre": genre,
                    "home_base": row["city"],
                    "availability": row["avail"],
                    "fee_min": row["fee"][0],
                    "fee_max": row["fee"][1],
                    "bio": row["bio"],
                },
            )
            dj.genres.add(genre)
            Management.objects.update_or_create(
                dj=dj,
                defaults={
                    "manager_name": row["mgr"],
                    "agency": row["agency"],
                    "booking_email": row["email"],
                    "phone": row["phone"],
                },
            )
            for platform, handle, url, followers in row["socials"]:
                SocialAccount.objects.update_or_create(
                    dj=dj, platform=platform,
                    defaults={"handle": handle, "url": url, "follower_count": followers},
                )
            sp, ig, tk, sc, eng = row["snap"]
            EngagementSnapshot.objects.update_or_create(
                dj=dj, captured_on=SNAP,
                defaults={
                    "spotify_monthly": sp, "instagram_followers": ig,
                    "tiktok_followers": tk, "soundcloud_followers": sc,
                    "engagement_rate": eng,
                },
            )
            for d, event, city, status in row["shows"]:
                Show.objects.update_or_create(
                    dj=dj, event_name=event, date=d,
                    defaults={"venue_city": city, "status": status},
                )
            for title, label, released, plays in row["releases"]:
                Release.objects.update_or_create(
                    dj=dj, title=title,
                    defaults={"label": label, "released_on": released, "play_count": plays},
                )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DJS)} DJs."))
