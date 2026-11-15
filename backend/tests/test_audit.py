
from app.models import Role
from app.models.audit import AuditLog


def test_successful_login_is_audited(client, db):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@dfip.local",
            "password": "Admin@123",
        },
    )

    assert response.status_code == 200

    log = db.query(AuditLog).filter(
        AuditLog.action == "login",
        AuditLog.result == "success",
    ).first()

    assert log is not None
    assert log.entity == "user"


def test_failed_login_is_audited(client, db):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@dfip.local",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401

    log = db.query(AuditLog).filter(
        AuditLog.action == "login",
        AuditLog.result == "failure",
    ).first()

    assert log is not None
    assert "wrong-password" not in (log.details or "")


def test_admin_can_view_audit_logs(client, auth_headers, db):
    db.add(
        AuditLog(
            action="test_action",
            result="success",
            details="Test audit entry",
        )
    )
    db.commit()

    response = client.get(
        "/api/audit",
        headers=auth_headers(Role.ADMIN),
    )

    assert response.status_code == 200
    assert any(
        log["action"] == "test_action"
        for log in response.json()
    )


def test_planner_cannot_view_audit_logs(client, auth_headers):
    response = client.get(
        "/api/audit",
        headers=auth_headers(Role.PLANNER),
    )

    assert response.status_code == 403


def test_audit_logs_require_authentication(client):
    response = client.get("/api/audit")

    assert response.status_code == 401
