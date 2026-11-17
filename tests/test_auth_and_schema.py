import pytest

pytestmark = pytest.mark.django_db


def test_jwt_login_refresh_and_access(client, users):
    response = client.post("/api/token/", {"username": "owner", "password": "study-password-2026"}, format="json")
    assert response.status_code == 200
    assert "access" in response.data
    refreshed = client.post("/api/token/refresh/", {"refresh": response.data["refresh"]}, format="json")
    assert refreshed.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed.data['access']}")
    assert client.get("/api/kits/").status_code == 200


def test_invalid_credentials_and_refresh(client, users):
    assert client.post("/api/token/", {"username": "owner", "password": "wrong"}).status_code == 401
    assert client.post("/api/token/refresh/", {"refresh": "invalid"}).status_code == 401


def test_openapi_schema_and_swagger_are_public(client):
    response = client.get("/api/schema/?format=json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    paths = schema["paths"]
    assert {"get", "post"} <= paths["/api/kits/"].keys()
    detail = paths["/api/kits/{id}/"]
    assert {"get", "put", "patch", "delete"} <= detail.keys()
    assert detail["get"]["parameters"][0]["name"] == "id"
    assert "403" in detail["delete"]["responses"]
    assert "204" in detail["delete"]["responses"]
    assert paths["/api/kits/"]["post"]["requestBody"]
    assert paths["/api/kits/"]["get"]["security"] == [{"jwtAuth": []}]
    assert schema["components"]["securitySchemes"]["jwtAuth"]["scheme"] == "bearer"
    assert {"id", "name", "owner", "members"} <= schema["components"]["schemas"]["Kit"]["properties"].keys()
    response = client.get("/api/docs/")
    assert response.status_code == 200
    assert b"SwaggerUIBundle" in response.content
