
from app.models import Role, User


def test_admin_can_list_users(client, auth_headers):
    response = client.get(
        "/api/users",
        headers=auth_headers(Role.ADMIN),
    )

    assert response.status_code == 200

    users = response.json()

    assert len(users) >= 1
    assert any(user["email"] == "admin@dfip.local" for user in users)


def test_admin_can_create_user(client, auth_headers):
    response = client.post(
        "/api/users",
        headers=auth_headers(Role.ADMIN),
        json={
            "name": "Test Planner",
            "email": "newplanner@example.com",
            "password": "Planner@123",
            "role": "planner",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Planner"
    assert data["email"] == "newplanner@example.com"
    assert data["role"] == "planner"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data


def test_admin_cannot_create_duplicate_email(client, auth_headers):
    user_data = {
        "name": "Test Planner",
        "email": "duplicate@example.com",
        "password": "Planner@123",
        "role": "planner",
    }

    first_response = client.post(
        "/api/users",
        headers=auth_headers(Role.ADMIN),
        json=user_data,
    )

    second_response = client.post(
        "/api/users",
        headers=auth_headers(Role.ADMIN),
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_planner_cannot_list_users(client, auth_headers):
    response = client.get(
        "/api/users",
        headers=auth_headers(Role.PLANNER),
    )

    assert response.status_code == 403


def test_viewer_cannot_list_users(client, auth_headers):
    response = client.get(
        "/api/users",
        headers=auth_headers(Role.VIEWER),
    )

    assert response.status_code == 403


def test_users_endpoint_requires_authentication(client):
    response = client.get("/api/users")

    assert response.status_code == 401


def test_admin_cannot_change_own_role(client, auth_headers, db):
    headers = auth_headers(Role.ADMIN)

    admin = db.query(User).filter(
        User.email == "admin@test.local"
    ).first()

    response = client.patch(
        f"/api/users/{admin.id}/role",
        headers=headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 400


def test_admin_cannot_deactivate_own_account(client, auth_headers, db):
    headers = auth_headers(Role.ADMIN)

    admin = db.query(User).filter(
        User.email == "admin@test.local"
    ).first()

    response = client.patch(
        f"/api/users/{admin.id}/deactivate",
        headers=headers,
    )

    assert response.status_code == 400


def test_admin_can_change_another_users_role(client, auth_headers, db):
    auth_headers(Role.PLANNER)
    admin_headers = auth_headers(Role.ADMIN)

    planner = db.query(User).filter(
        User.email == "planner@test.local"
    ).first()

    response = client.patch(
        f"/api/users/{planner.id}/role",
        headers=admin_headers,
        json={"role": "viewer"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


def test_admin_can_deactivate_another_user(client, auth_headers, db):
    planner_headers = auth_headers(Role.PLANNER)
    admin_headers = auth_headers(Role.ADMIN)

    planner = db.query(User).filter(
        User.email == "planner@test.local"
    ).first()

    response = client.patch(
        f"/api/users/{planner.id}/deactivate",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    next_request = client.get(
        "/api/inventory",
        headers=planner_headers,
    )

    assert next_request.status_code == 401
