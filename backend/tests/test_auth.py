def test_register_login_me(client, register, auth_header):
    register("w@t.kz", "worker_01")
    me = client.get("/auth/me", headers=auth_header("w@t.kz")).json()
    assert me["pseudonym"] == "worker_01"
    assert me["role"] == "worker"
    assert me["trust_level"] == "user"


def test_email_is_lowercased(client, register, auth_header):
    register("Test@Example.KZ", "case_user")
    assert client.get("/auth/me", headers=auth_header("test@example.kz")).status_code == 200


def test_wrong_password(client, register):
    register("w@t.kz", "worker_01")
    response = client.post(
        "/auth/login", data={"username": "w@t.kz", "password": "burys-parol"}
    )
    assert response.status_code == 401


def test_duplicate_email_and_pseudonym(client, register):
    register("w@t.kz", "worker_01")
    duplicate_email = client.post(
        "/auth/register",
        json={
            "email": "w@t.kz",
            "password": "sekret123",
            "pseudonym": "basqa_atau",
            "role": "worker",
        },
    )
    assert duplicate_email.status_code == 409
    duplicate_pseudonym = client.post(
        "/auth/register",
        json={
            "email": "basqa@t.kz",
            "password": "sekret123",
            "pseudonym": "worker_01",
            "role": "worker",
        },
    )
    assert duplicate_pseudonym.status_code == 409


def test_invalid_token(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer zhalgan.token.123"}
    )
    assert response.status_code == 401


def test_short_password_rejected(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "w@t.kz",
            "password": "qysqa",
            "pseudonym": "worker_01",
            "role": "worker",
        },
    )
    assert response.status_code == 422
