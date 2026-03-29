from httpx import AsyncClient

from tests.helper import auth_header, registered_user, create_post


async def test_create_post(client: AsyncClient):
    # this gives you registered user
    # username: testtest | password: password
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # helper to create post
    post_response = await create_post(client, "test", "test", token)

    data = post_response.json()

    assert post_response.status_code == 201
    assert data["title"] == "Test"
    assert data["content"] == "test"


async def test_get_post(client: AsyncClient):
    # this gives you registered user
    # username: testtest | password: password
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # helper to create post
    response = await create_post(client, "test", "test", token)
    post_id = response.json()["id"]

    post_response = await client.get(f"/api/posts/{post_id}", headers=token)
    data = post_response.json()

    assert post_response.status_code == 200
    assert data["title"] == "Test"
    assert data["content"] == "test"
    assert "id" in data
    assert "date_created" in data


async def test_update_post(client: AsyncClient):
    # this gives you registered user
    # username: testtest | password: password
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # helper to create post
    post_response = await create_post(client, "test", "test", token)

    data = post_response.json()
    post_id = data["id"]

    update_response = await client.patch(
        f"/api/posts/{post_id}",
        json={"title": "Updated", "content": "UPDATED"},
        headers=token,
    )

    data = update_response.json()

    assert update_response.status_code == 200
    assert data["title"] == "Updated"
    assert data["content"] == "UPDATED"


async def test_delete_post(client: AsyncClient):
    # this gives you registered user
    # username: testtest | password: password
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # helper to create post
    post_response = await create_post(client, "test", "test", token)

    data = post_response.json()
    post_id = data["id"]

    delete_response = await client.delete(
        f"/api/posts/{post_id}",
        headers=token,
    )

    assert delete_response.status_code == 204
