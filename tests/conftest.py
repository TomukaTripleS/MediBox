import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from kits.models import Kit


@pytest.fixture(scope="session")
def password_hash():
    return make_password("study-password-2026")


@pytest.fixture
def users(db, password_hash):
    return {
        role: get_user_model().objects.create(username=role, password=password_hash)
        for role in ("owner", "member", "outsider")
    }


@pytest.fixture
def kit(users):
    kit = Kit.objects.create(name="Домашня аптечка", owner=users["owner"])
    kit.members.add(users["member"])
    return kit


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(users):
    def authenticate(role):
        client = APIClient()
        token = RefreshToken.for_user(users[role]).access_token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return authenticate
