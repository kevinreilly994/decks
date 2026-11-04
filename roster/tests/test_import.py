import io

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from roster.importers import import_djs_from_file, import_djs_from_rows
from roster.models import DJ

CSV = (
    "name,genre,home_base,availability,fee_min,fee_max,manager_name,agency,booking_email,instagram\n"
    'Real One,Tech House,"London, UK",available,12000,20000,Sam Agent,Big Agency,book@big.co,@realone\n'
)


@pytest.mark.django_db
def test_import_from_rows_creates_everything():
    rows = [{
        "name": "Real One", "genre": "Tech House", "home_base": "London, UK",
        "availability": "available", "fee_min": "12000", "fee_max": "20000",
        "manager_name": "Sam Agent", "agency": "Big Agency",
        "booking_email": "book@big.co", "instagram": "@realone",
        "spotify_artist_id": "abc123",
    }]
    r = import_djs_from_rows(rows)
    assert r["created"] == 1 and r["updated"] == 0 and r["errors"] == []
    dj = DJ.objects.get(name="Real One")
    assert dj.primary_genre.name == "Tech House"
    assert dj.fee_min == 12000 and dj.spotify_artist_id == "abc123"
    assert dj.management.manager_name == "Sam Agent"
    assert dj.socials.filter(platform="instagram", handle="@realone").exists()


@pytest.mark.django_db
def test_import_missing_genre_is_error():
    r = import_djs_from_rows([{"name": "No Genre", "genre": ""}])
    assert r["created"] == 0
    assert any("missing" in e for e in r["errors"])
    assert not DJ.objects.filter(name="No Genre").exists()


@pytest.mark.django_db
def test_import_is_idempotent():
    rows = [{"name": "Dup", "genre": "Deep House"}]
    import_djs_from_rows(rows)
    r = import_djs_from_rows(rows)
    assert r["updated"] == 1 and r["created"] == 0
    assert DJ.objects.filter(name="Dup").count() == 1


@pytest.mark.django_db
def test_import_from_file_bytes():
    r = import_djs_from_file(io.BytesIO(CSV.encode("utf-8")))
    assert r["created"] == 1
    assert DJ.objects.get(name="Real One").management.agency == "Big Agency"


@pytest.mark.django_db
def test_admin_import_csv_view(client):
    User.objects.create_superuser("adm", "a@x.com", "pw-12345!")
    client.force_login(User.objects.get(username="adm"))
    assert client.get("/admin/roster/dj/import-csv/").status_code == 200
    upload = SimpleUploadedFile("djs.csv", CSV.encode("utf-8"), content_type="text/csv")
    resp = client.post("/admin/roster/dj/import-csv/", {"csv_file": upload})
    assert resp.status_code == 302
    assert DJ.objects.filter(name="Real One").exists()
