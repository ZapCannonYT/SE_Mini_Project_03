from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_admin_token():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@dfip.local",
            "password": "Admin@123",
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_user_management():
    token = get_admin_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.post(
        "/api/users/",
        headers=headers,
        json={
            "name": "Test Planner",
            "email": "planner@test.com",
            "password": "Planner@123",
            "role": "planner",
        },
    )

    assert response.status_code == 201

    user = response.json()
    user_id = user["id"]

    assert user["email"] == "planner@test.com"
    assert user["role"] == "planner"

    response = client.get(
        "/api/users/",
        headers=headers,
    )

    assert response.status_code == 200

    response = client.put(
        f"/api/users/{user_id}/role",
        headers=headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "viewer"

    response = client.patch(
        f"/api/users/{user_id}/deactivate",
        headers=headers,
    )

    assert response.status_code == 200