def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_profile(client):
    payload = {
        "name": "Maria Souza",
        "email": "Maria@Exemplo.com",
        "password": "segredo123",
        "phone": "(11) 90000-0000",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "maria@exemplo.com"
    assert body["user"]["role"] == "CLIENT"

    duplicate = client.post("/api/v1/auth/register", json=payload)
    assert duplicate.status_code == 409

    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "senha-errada"},
    )
    assert wrong.status_code == 401

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["name"] == "Maria Souza"

    updated = client.patch(
        "/api/v1/auth/me", headers=headers, json={"name": "Maria S. Souza"}
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Maria S. Souza"


def test_profile_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer token-invalido"}
        ).status_code
        == 401
    )


def test_barbershop_onboarding(client):
    payload = {
        "name": "Navalha de Ouro",
        "city": "Campinas",
        "timezone": "America/Sao_Paulo",
        "owner_name": "Dono da Navalha",
        "owner_email": "dono@navalha.com",
        "owner_password": "senha123",
    }
    response = client.post("/api/v1/auth/register/barbershop", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["role"] == "ADMIN"

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    mine = client.get("/api/v1/barbershops/mine", headers=headers)
    assert mine.status_code == 200
    assert [shop["name"] for shop in mine.json()] == ["Navalha de Ouro"]

    invalid_tz = client.post(
        "/api/v1/auth/register/barbershop",
        json={**payload, "owner_email": "outro@navalha.com", "timezone": "Marte/Base"},
    )
    assert invalid_tz.status_code == 422
