from uuid import UUID

from httpx import AsyncClient

from app.models.user import User

""" USER HELPER """


async def register_user(
    client: AsyncClient,
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    password: str,
):

    return await client.post(
        "/api/users",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password": password,
        },
    )


async def registered_user(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "first_name": "test",
            "last_name": "test",
            "username": "testtest",
            "email": "test@email.com",
            "password": "password",
        },
    )

    assert response.status_code == 201


async def auth_header(client: AsyncClient, username: str, password: str) -> dict:
    response = await client.post(
        "/api/users/login", data={"username": username, "password": password}
    )

    # Handle failed login
    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "error": response.json(),
        }

    data = response.json()
    access_token = data.get("access_token")

    if not access_token:
        return {
            "status_code": response.status_code,
            "error": "No access_token in response",
        }

    return {"Authorization": f"Bearer {access_token}"}


"""POST HELPER"""


async def create_post(client: AsyncClient, title: str, content: str, token):
    return await client.post(
        "/api/posts", json={"title": title, "content": content}, headers=token
    )


"""COMMENT HELPER"""


async def create_comment(client: AsyncClient, message: str, post_id: UUID, token):
    return await client.post(
        f"/api/comments/{post_id}",
        json={"message": message},
        headers=token,
    )
