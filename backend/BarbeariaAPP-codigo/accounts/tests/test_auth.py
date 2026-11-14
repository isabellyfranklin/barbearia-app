import pytest

pytestmark = pytest.mark.django_db


def test_registro_cria_cliente_e_retorna_tokens(api_client):
    resposta = api_client.post(
        "/api/auth/register",
        {
            "username": "novo",
            "email": "novo@exemplo.com",
            "first_name": "Novo",
            "last_name": "Cliente",
            "telefone": "11911112222",
            "password": "senhaSegura123",
            "password_confirm": "senhaSegura123",
        },
        format="json",
    )

    assert resposta.status_code == 201
    assert resposta.data["user"]["perfil"] == "cliente"
    assert resposta.data["access"]
    assert resposta.data["refresh"]


def test_registro_rejeita_senhas_diferentes(api_client):
    resposta = api_client.post(
        "/api/auth/register",
        {
            "username": "novo",
            "telefone": "11911112222",
            "password": "senhaSegura123",
            "password_confirm": "outraSenha123",
        },
        format="json",
    )

    assert resposta.status_code == 400
    assert "password_confirm" in resposta.data


def test_login_retorna_tokens_e_usuario(api_client, cliente):
    resposta = api_client.post(
        "/api/auth/login",
        {"username": "cliente", "password": "senha12345"},
        format="json",
    )

    assert resposta.status_code == 200
    assert resposta.data["access"]
    assert resposta.data["refresh"]
    assert resposta.data["user"]["username"] == "cliente"


def test_login_com_senha_invalida_falha(api_client, cliente):
    resposta = api_client.post(
        "/api/auth/login",
        {"username": "cliente", "password": "errada"},
        format="json",
    )

    assert resposta.status_code == 401


def test_me_exige_autenticacao(api_client):
    resposta = api_client.get("/api/me")

    assert resposta.status_code == 401


def test_me_retorna_usuario_autenticado(api_client, cliente):
    api_client.force_authenticate(cliente)

    resposta = api_client.get("/api/me")

    assert resposta.status_code == 200
    assert resposta.data["username"] == "cliente"
    assert resposta.data["perfil"] == "cliente"


def test_logout_invalida_refresh_token(api_client, cliente):
    login = api_client.post(
        "/api/auth/login",
        {"username": "cliente", "password": "senha12345"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resposta = api_client.post(
        "/api/auth/logout",
        {"refresh": login.data["refresh"]},
        format="json",
    )

    assert resposta.status_code == 204


def test_superusuario_recebe_perfil_administrador(db):
    from django.contrib.auth import get_user_model

    usuario = get_user_model().objects.create_superuser(
        username="root",
        email="root@exemplo.com",
        password="senhaSegura123",
    )

    assert usuario.perfil == "administrador"
    assert usuario.is_staff is True
    assert usuario.is_superuser is True
