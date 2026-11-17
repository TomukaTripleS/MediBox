import logging

import pytest

pytestmark = pytest.mark.django_db


def test_success_logs_do_not_include_request_data(auth_client, users, caplog):
    client = auth_client("owner")
    with caplog.at_level(logging.INFO, logger="kits"):
        response = client.post("/api/kits/", {
            "name": "private-kit-name",
            "password": "private-password",
            "token": "private-token",
        }, format="json")
        assert response.status_code == 201
        kit_id = response.data["id"]
        url = f"/api/kits/{kit_id}/"
        assert client.patch(url, {"name": "private-new-name"}, format="json").status_code == 200
        assert client.delete(url).status_code == 204

    records = [record for record in caplog.records if record.name == "kits.views"]
    assert [record.levelno for record in records] == [logging.INFO] * 3
    assert [record.getMessage() for record in records] == [
        f"Kit {operation}: kit_id={kit_id} user_id={users['owner'].pk}"
        for operation in ("created", "updated", "deleted")
    ]


def test_rejected_requests_are_warnings(auth_client, client, kit, caplog):
    with caplog.at_level(logging.INFO, logger="kits"):
        assert auth_client("member").delete(f"/api/kits/{kit.pk}/").status_code == 403
        assert auth_client("owner").post("/api/kits/", {"name": ""}, format="json").status_code == 400
        assert auth_client("owner").get("/api/kits/999999/").status_code == 404
        assert client.get("/api/kits/").status_code == 401

    records = [record for record in caplog.records if record.name == "kits.views"]
    assert len(records) == 4
    assert all(record.levelno == logging.WARNING for record in records)
    assert [record.getMessage().split("status=")[1] for record in records] == ["403", "400", "404", "401"]
