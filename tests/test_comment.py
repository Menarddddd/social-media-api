from httpx import AsyncClient

from tests.helper import auth_header, registered_user, create_post, create_comment


async def test_create_comment(client: AsyncClient):
    # this gives you registered user
    # username: testtest | password: password
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # create you a post
    post_response = await create_post(client, "test", "test", token)
    post_id = post_response.json()["id"]

    response = await create_comment(client, "test", post_id, token)

    data = response.json()

    assert response.status_code == 201
    assert data["message"] == "test"


async def test_get_comment(client: AsyncClient):
    # this gives you registered user
    # username: testtest | password: password
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # create you a post
    post_response = await create_post(client, "test", "test", token)
    post_id = post_response.json()["id"]

    response = await create_comment(client, "test", post_id, token)
    comment_id = response.json()["id"]

    comment_response = await client.get(f"/api/comments/{comment_id}", headers=token)
    data = comment_response.json()

    assert comment_response.status_code == 200
    assert data["message"] == "test"
    assert "id" in data
    assert "author" in data
    assert "post" in data


async def test_update_comment(client: AsyncClient):
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # create you a post
    post_response = await create_post(client, "test", "test", token)
    post_id = post_response.json()["id"]

    response = await create_comment(client, "test", post_id, token)
    comment_id = response.json()["id"]

    # update the comment
    updated_response = await client.patch(
        f"/api/comments/{comment_id}", json={"message": "updated"}, headers=token
    )

    message = updated_response.json()["message"]

    assert updated_response.status_code == 200
    assert message == "updated"


async def test_delete_comment(client: AsyncClient):
    await registered_user(client)

    # helper to get token
    token = await auth_header(client, "testtest", "password")

    # create you a post
    post_response = await create_post(client, "test", "test", token)
    post_id = post_response.json()["id"]

    response = await create_comment(client, "test", post_id, token)
    comment_id = response.json()["id"]

    deleted_response = await client.delete(f"/api/comments/{comment_id}", headers=token)

    assert deleted_response.status_code == 204
