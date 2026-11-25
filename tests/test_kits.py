import pytest

from kits.models import Kit

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ["owner", "member"])
def test_list_and_retrieve_only_accessible_kits(auth_client, users, kit, role):
    hidden = Kit.objects.create(name="Чужа", owner=users["outsider"])
    client = auth_client(role)
    response = client.get("/api/kits/")
    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [kit.id]
    response = client.get(f"/api/kits/{kit.id}/")
    assert response.status_code == 200
    assert response.data == {"id": kit.id, "name": kit.name, "owner": users["owner"].id, "members": [users["member"].id]}
    assert client.get(f"/api/kits/{hidden.id}/").status_code == 404


def test_create_assigns_current_user_as_owner(auth_client, users):
    response = auth_client("owner").post("/api/kits/", {
        "name": "Сімейна", "owner": users["outsider"].id,
        "members": [users["member"].id],
    }, format="json")
    assert response.status_code == 201
    kit = Kit.objects.get(pk=response.data["id"])
    assert kit.owner == users["owner"]
    assert kit.name == "Сімейна"
    assert list(kit.members.all()) == [users["member"]]


def test_create_without_members(auth_client):
    response = auth_client("member").post("/api/kits/", {"name": "Моя"}, format="json")
    assert response.status_code == 201
    assert response.data["members"] == []


@pytest.mark.parametrize("data", [
    {},
    {"name": ""},
    {"name": "   "},
    {"name": "x" * 151},
    {"name": "Нова", "members": [999999]},
])
def test_invalid_create_does_not_save(auth_client, data):
    response = auth_client("owner").post("/api/kits/", data, format="json")
    assert response.status_code == 400
    assert Kit.objects.count() == 0


@pytest.mark.parametrize("role", ["owner", "member"])
@pytest.mark.parametrize("method", ["put", "patch"])
def test_owner_and_member_can_rename(auth_client, users, kit, role, method):
    response = getattr(auth_client(role), method)(f"/api/kits/{kit.id}/", {
        "name": "Нова назва", "owner": users["outsider"].id,
    }, format="json")
    assert response.status_code == 200
    kit.refresh_from_db()
    assert kit.name == "Нова назва"
    assert kit.owner == users["owner"]
    assert list(kit.members.all()) == [users["member"]]


def test_owner_can_replace_members(auth_client, users, kit):
    client = auth_client("owner")
    response = client.patch(f"/api/kits/{kit.id}/", {"members": [users["outsider"].id]}, format="json")
    assert response.status_code == 200
    assert list(kit.members.all()) == [users["outsider"]]
    assert auth_client("member").get(f"/api/kits/{kit.id}/").status_code == 404
    assert auth_client("outsider").get(f"/api/kits/{kit.id}/").status_code == 200
    assert client.patch(f"/api/kits/{kit.id}/", {"members": []}, format="json").status_code == 200
    assert kit.members.count() == 0


@pytest.mark.parametrize("method", ["put", "patch"])
def test_member_cannot_change_members(auth_client, users, kit, method):
    response = getattr(auth_client("member"), method)(f"/api/kits/{kit.id}/", {
        "name": "Не зберігати", "members": [users["outsider"].id],
    }, format="json")
    assert response.status_code == 403
    kit.refresh_from_db()
    assert kit.name == "Домашня аптечка"
    assert list(kit.members.all()) == [users["member"]]


@pytest.mark.parametrize("method,data", [
    ("put", {}),
    ("patch", {"name": ""}),
    ("patch", {"members": [999999]}),
])
def test_invalid_update(auth_client, kit, method, data):
    response = getattr(auth_client("owner"), method)(f"/api/kits/{kit.id}/", data, format="json")
    assert response.status_code == 400
    kit.refresh_from_db()
    assert kit.name == "Домашня аптечка"


def test_only_owner_can_delete(auth_client, kit):
    url = f"/api/kits/{kit.id}/"
    assert auth_client("member").delete(url).status_code == 403
    assert Kit.objects.filter(pk=kit.id).exists()
    response = auth_client("owner").delete(url)
    assert response.status_code == 204
    assert response.content == b""
    assert not Kit.objects.filter(pk=kit.id).exists()


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_outsider_cannot_access(auth_client, kit, method):
    client = auth_client("outsider")
    assert client.get("/api/kits/").data == []
    response = getattr(client, method)(f"/api/kits/{kit.id}/")
    assert response.status_code == 404
    assert Kit.objects.filter(pk=kit.id).exists()


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_missing_kit(auth_client, method):
    assert getattr(auth_client("owner"), method)("/api/kits/999999/").status_code == 404


@pytest.mark.parametrize("method,detail", [
    ("get", False),
    ("post", False),
    ("get", True),
    ("put", True),
    ("patch", True),
    ("delete", True),
])
def test_authentication_required(client, kit, method, detail):
    url = f"/api/kits/{kit.id}/" if detail else "/api/kits/"
    assert getattr(client, method)(url).status_code == 401
    assert Kit.objects.filter(pk=kit.id).exists()


def test_invalid_token(client):
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid")
    assert client.get("/api/kits/").status_code == 401
