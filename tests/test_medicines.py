import pytest

from kits.models import Kit
from medicines.models import Medicine

pytestmark = pytest.mark.django_db

DATA = {"name": "Парацетамол", "form": "tablet", "unit": "pcs"}


@pytest.fixture
def medicine(kit):
    return Medicine.objects.create(kit=kit, **DATA)


@pytest.mark.parametrize("role", ["owner", "member"])
def test_create(auth_client, kit, role):
    response = auth_client(role).post(f"/api/kits/{kit.id}/medicines/", DATA, format="json")
    assert response.status_code == 201
    assert response.data == {"id": response.data["id"], **DATA}
    assert Medicine.objects.get().kit == kit


@pytest.mark.parametrize("data", [
    {},
    {**DATA, "name": ""},
    {**DATA, "name": "x" * 151},
    {**DATA, "form": "pill"},
    {**DATA, "unit": "kg"},
])
def test_invalid_create(auth_client, kit, data):
    response = auth_client("owner").post(f"/api/kits/{kit.id}/medicines/", data, format="json")
    assert response.status_code == 400
    assert Medicine.objects.count() == 0


def test_duplicate_is_rejected(auth_client, kit, medicine):
    data = {**DATA, "name": "ПАРАЦЕТАМОЛ"}
    response = auth_client("owner").post(f"/api/kits/{kit.id}/medicines/", data, format="json")
    assert response.status_code == 400
    assert Medicine.objects.count() == 1


def test_same_name_with_other_form_is_allowed(auth_client, kit, medicine):
    data = {**DATA, "form": "syrup", "unit": "ml"}
    response = auth_client("owner").post(f"/api/kits/{kit.id}/medicines/", data, format="json")
    assert response.status_code == 201


def test_list_shows_only_this_kit(auth_client, users, kit, medicine):
    other = Kit.objects.create(name="Дача", owner=users["owner"])
    Medicine.objects.create(kit=other, name="Ібупрофен", form="tablet", unit="pcs")
    response = auth_client("member").get(f"/api/kits/{kit.id}/medicines/")
    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [medicine.id]


@pytest.mark.parametrize("search, names", [
    ("пара", ["Парацетамол"]),
    ("ПАРА", ["Парацетамол"]),
    ("фен", ["Ібупрофен"]),
    ("", ["Ібупрофен", "Парацетамол"]),
    ("аспірин", []),
])
def test_search(auth_client, kit, medicine, search, names):
    Medicine.objects.create(kit=kit, name="Ібупрофен", form="tablet", unit="pcs")
    response = auth_client("owner").get(f"/api/kits/{kit.id}/medicines/", {"search": search})
    assert sorted(item["name"] for item in response.data) == sorted(names)


@pytest.mark.parametrize("role", ["owner", "member"])
def test_retrieve_update_delete(auth_client, kit, medicine, role):
    client = auth_client(role)
    detail = f"/api/kits/{kit.id}/medicines/{medicine.id}/"
    assert client.get(detail).data == {"id": medicine.id, **DATA}
    assert client.put(detail, {**DATA, "name": "Ібупрофен"}, format="json").status_code == 200
    assert client.patch(detail, {"unit": "g"}, format="json").status_code == 200
    medicine.refresh_from_db()
    assert (medicine.name, medicine.search_name, medicine.unit) == ("Ібупрофен", "ібупрофен", "g")
    assert client.delete(detail).status_code == 204
    assert Medicine.objects.count() == 0


def test_outsider_gets_404(auth_client, kit, medicine):
    client = auth_client("outsider")
    detail = f"/api/kits/{kit.id}/medicines/{medicine.id}/"
    assert client.get(f"/api/kits/{kit.id}/medicines/").status_code == 404
    assert client.post(f"/api/kits/{kit.id}/medicines/", DATA, format="json").status_code == 404
    assert client.get(detail).status_code == 404
    assert client.patch(detail, {"name": "Аспірин"}, format="json").status_code == 404
    assert client.delete(detail).status_code == 404
    assert Medicine.objects.get() == medicine


def test_medicine_from_other_kit_is_404(auth_client, users, kit, medicine):
    own = Kit.objects.create(name="Моя", owner=users["outsider"])
    response = auth_client("outsider").get(f"/api/kits/{own.id}/medicines/{medicine.id}/")
    assert response.status_code == 404


def test_requires_token(client, kit):
    assert client.get(f"/api/kits/{kit.id}/medicines/").status_code == 401
