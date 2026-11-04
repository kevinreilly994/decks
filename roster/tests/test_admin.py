import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_admin_requires_login(client):
    resp = client.get("/admin/")
    assert resp.status_code == 302


@pytest.mark.django_db
def test_admin_dj_changelist_loads_for_staff(client):
    User.objects.create_superuser("boss", "boss@example.com", "pw-12345!")
    client.force_login(User.objects.get(username="boss"))
    resp = client.get("/admin/roster/dj/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_health_endpoint_ok(client):
    resp = client.get("/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
