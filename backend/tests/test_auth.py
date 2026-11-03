from fastapi.testclient import TestClient

from app.core.security import verify_password
from app.models.user import User
from app.main import app
client = TestClient(app)


def test_login_success():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@dfip.local",
            "password": "Admin@123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"


def test_login_wrong_password():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@dfip.local",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@dfip.local",
            "password": "Admin@123",
        },
    )

    assert response.status_code == 401


def test_logout():
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
def test_admin_password_is_hashed(client, db):
    admin = db.query(User).filter(
        User.email == "admin@dfip.local"
    ).first()

    assert admin is not None
    assert admin.password_hash.startswith("$argon2")
    assert verify_password("Admin@123", admin.password_hash)