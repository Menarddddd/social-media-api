import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/users",
        json={
            "first_name": "kim",
            "last_name": "lai",
            "username": "kimberlylai",
            "email": "kim@example.com",
            "password": "menardfrancisco",
        },
    )

    response = await client.post(
        "/api/users/login",
        data={
            "username": "kimberlylai",
            "password": "menardfrancisco",
        },
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "first_name": "test",
            "last_name": "test",
            "username": "TestTest",
            "email": "teST@eMail.com",
            "password": "asdasdasd",
        },
    )

    assert response.status_code == 201

    data = response.json()
    data["message"] = {
        "message": "You've successfully created your account. You can now login with it"
    }
