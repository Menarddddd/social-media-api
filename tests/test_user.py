from httpx import AsyncClient

from tests.helper import auth_header, register_user


async def test_login(client: AsyncClient):
    await register_user(
        client, "kim", "lai", "kimberlylai", "kim@example.com", "menardfrancisco"
    )

    response = await auth_header(client, "kimberlylai", "menardfrancisco")

    assert "Authorization" in response


async def test_create_user(client: AsyncClient):
    response = await register_user(
        client, "test", "test", "testTesT", "TEST@emaiL.com", "password"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == "Test"
    assert data["username"] == "testtest"
    assert data["email"] == "test@email.com"


async def test_get_user(client: AsyncClient):
    # Create a user
    response = await register_user(
        client, "test", "test", "testTesT", "TEST@emaiL.com", "password"
    )
    user_id = response.json()["id"]

    # Get token
    token = await auth_header(client, "testtest", "password")

    user_response = await client.get(f"/api/users/{user_id}", headers=token)

    data = user_response.json()

    assert user_response.status_code == 200
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Test"
    assert data["username"] == "testtest"
    assert data["email"] == "test@email.com"
    assert "password" not in data
    assert "id" in data


async def test_update_user(client: AsyncClient):
    await register_user(
        client, "test", "test", "testTesT", "TEST@emaiL.com", "password"
    )

    token = await auth_header(client, "testtest", "password")
    print("token:" + str(token))

    update_response = await client.patch(
        "/api/users",
        json={
            "first_name": "updated",
            "username": "UpdATed",
            "email": "UpDateD@EMail.com",
        },
        headers=token,
    )

    data = update_response.json()

    assert update_response.status_code == 200
    assert data["first_name"] == "Updated"
    assert data["username"] == "updated"
    assert data["email"] == "updated@email.com"

    await register_user(
        client, "test", "test", "newtest", "newTEST@emaiL.com", "password"
    )

    token = await auth_header(client, "newtest", "password")

    new_response = await client.patch(
        "/api/users",
        json={
            "first_name": "updated",
            "username": "UpdATed",
            "email": "UpDateD@EMail.com",
        },
        headers=token,
    )

    assert new_response.status_code == 409


async def test_delete_user(client: AsyncClient):
    await register_user(
        client, "test", "test", "testtest", "test@email.com", "password"
    )

    token = await auth_header(client, "testtest", "password")

    response = await client.post(
        "/api/users/delete",
        json={"password": "password", "reason": "test"},
        headers=token,
    )

    assert response.status_code == 204
