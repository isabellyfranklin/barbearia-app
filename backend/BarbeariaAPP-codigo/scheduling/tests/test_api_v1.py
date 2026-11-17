from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from catalog.models import Servico
from scheduling.services import criar_agendamento
from scheduling.tests.test_scheduling import inicio_em, proxima_data_util

pytestmark = pytest.mark.django_db
API = "/api/v1"


def test_jornada_v1_com_jwt(api_client, cliente, barbeiro, profissional, servico, disponibilidade):
    login = api_client.post(f"{API}/auth/login", {
        "username": cliente.username, "password": "senha12345",
    }, format="json")
    assert login.status_code == 200
    access, refresh = login.data["access"], login.data["refresh"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api_client.get(f"{API}/me").data["perfil"] == "cliente"
    assert api_client.get(f"{API}/services").data[0]["id"] == servico.pk
    assert api_client.get(f"{API}/barbershop").data["id"] == 1
    data = proxima_data_util().isoformat()
    url = f"{API}/professionals/{profissional.pk}/availability"
    slots = api_client.get(url, {"date": data, "service": servico.pk})
    assert slots.status_code == 200
    reserva = api_client.post(f"{API}/appointments", {
        "profissional": profissional.pk, "servico": servico.pk,
        "data_hora": slots.data["slots"][0],
    }, format="json")
    assert reserva.status_code == 201
    pk = reserva.data["id"]
    assert reserva.data["status"] == "pendente"
    assert reserva.data["preco"] == "50.00"
    assert api_client.patch(f"{API}/me/agenda/{pk}/status", {
        "status": "confirmado",
    }, format="json").status_code == 403
    login_barbeiro = api_client.post(f"{API}/auth/login", {
        "username": barbeiro.username, "password": "senha12345",
    }, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_barbeiro.data['access']}")
    assert api_client.get(f"{API}/me/agenda", {"date": data}).data[0]["id"] == pk
    assert api_client.get(f"{API}/me/agenda/week", {"date": data}).data["appointments"][0]["id"] == pk
    assert api_client.patch(f"{API}/me/agenda/{pk}/status", {
        "status": "confirmado",
    }, format="json").data["status"] == "confirmado"
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api_client.patch(f"{API}/appointments/{pk}/cancel").data["status"] == "cancelado"
    assert api_client.get(f"{API}/me/history", {"status": "cancelado"}).data[0]["id"] == pk
    assert slots.data["slots"][0] in api_client.get(url, {"date": data, "service": servico.pk}).data["slots"]
    assert api_client.post(f"{API}/auth/logout", {"refresh": refresh}, format="json").status_code == 204
    assert api_client.post(f"{API}/auth/refresh", {"refresh": refresh}, format="json").status_code == 401


def test_disponibilidade_periodo_respeita_servico(api_client, profissional, disponibilidade):
    servico = Servico.objects.create(nome="Longo", duracao_minutos=60, preco="80")
    data = proxima_data_util().isoformat()
    url = f"{API}/professionals/{profissional.pk}/availability"
    dia = api_client.get(url, {"date": data, "service": servico.pk})
    periodo = api_client.get(url, {"from": data, "to": data, "service": servico.pk})
    assert dia.status_code == periodo.status_code == 200
    assert dia.data["slots"] == periodo.data["days"][0]["slots"]
    assert periodo.data["duration_minutes"] == 60
    assert len(dia.data["slots"]) == 17


@pytest.mark.parametrize("params", [
    {"date": "2026-02-30", "service": 1},
    {"date": "invalida", "service": 1},
    {"date": "2026-11-18"},
    {"date": "2026-11-18", "service": 0},
    {"from": "2026-11-19", "to": "2026-11-18", "service": 1},
    {"date": "2026-11-18", "from": "2026-11-18", "service": 1},
])
def test_disponibilidade_rejeita_entradas_invalidas(api_client, profissional, servico, params):
    if params.get("service") == 1:
        params = {**params, "service": servico.pk}
    assert api_client.get(
        f"{API}/professionals/{profissional.pk}/availability", params,
    ).status_code == 400


@pytest.mark.parametrize("path", ["me/agenda", "me/agenda/week", "admin/appointments", "admin/history"])
def test_filtro_data_impossivel_retorna_400(api_client, administrador, path):
    api_client.force_authenticate(administrador)
    params = {"date": "2026-02-30"} if "history" not in path else {"from": "2026-02-30"}
    assert api_client.get(f"{API}/{path}", params).status_code == 400


def test_historico_rejeita_periodo_invertido(api_client, cliente):
    api_client.force_authenticate(cliente)
    assert api_client.get(f"{API}/me/history", {
        "from": "2026-11-20", "to": "2026-11-19",
    }).status_code == 400


def test_profissional_publico_nao_expoe_conta(api_client, profissional):
    response = api_client.get(f"{API}/professionals/{profissional.pk}")
    assert response.status_code == 200
    assert set(response.data) == {"id", "nome", "especialidades", "bio", "ativo"}


def test_admin_reativa_login_do_barbeiro(api_client, administrador, profissional):
    api_client.force_authenticate(administrador)
    url = f"{API}/admin/professionals/{profissional.pk}"
    assert api_client.delete(url).status_code == 204
    assert api_client.patch(url, {"ativo": True}, format="json").status_code == 200
    profissional.usuario.refresh_from_db()
    assert profissional.usuario.is_active is True


def test_logout_nao_revoga_token_de_outro(api_client, cliente, outro_cliente):
    from rest_framework_simplejwt.tokens import RefreshToken
    outro_token = str(RefreshToken.for_user(outro_cliente))
    api_client.force_authenticate(cliente)
    assert api_client.post(f"{API}/auth/logout", {
        "refresh": outro_token,
    }, format="json").status_code == 403
    RefreshToken(outro_token)  # Continua válido.


def test_alteracao_senha_revoga_tokens(api_client, cliente):
    login = api_client.post(f"{API}/auth/login", {
        "username": cliente.username, "password": "senha12345",
    }, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    assert api_client.post(f"{API}/me/password", {
        "current_password": "errada", "new_password": "NovaSenha#19387",
        "new_password_confirm": "NovaSenha#19387",
    }, format="json").status_code == 400
    assert api_client.post(f"{API}/me/password", {
        "current_password": "senha12345", "new_password": "NovaSenha#19387",
        "new_password_confirm": "NovaSenha#19387",
    }, format="json").status_code == 204
    assert api_client.get(f"{API}/me").status_code == 401
    api_client.credentials()
    assert api_client.post(f"{API}/auth/refresh", {
        "refresh": login.data["refresh"],
    }, format="json").status_code == 401
    assert api_client.post(f"{API}/auth/login", {
        "username": cliente.username, "password": "NovaSenha#19387",
    }, format="json").status_code == 200


def test_registro_nao_aceita_senha_fraca_ou_escalada(api_client):
    payload = {
        "username": "novo", "telefone": "11987654321", "password": "12345678",
        "password_confirm": "12345678", "perfil": "administrador", "is_staff": True,
    }
    assert api_client.post(f"{API}/auth/register", payload, format="json").status_code == 400
    payload.update(password="SenhaForte#19387", password_confirm="SenhaForte#19387")
    result = api_client.post(f"{API}/auth/register", payload, format="json")
    assert result.status_code == 201
    user = get_user_model().objects.get(username="novo")
    assert user.perfil == "cliente" and not user.is_staff


@pytest.mark.parametrize("role", ["cliente", "barbeiro"])
def test_catalogo_escrita_restrita(api_client, request, role, servico):
    api_client.force_authenticate(request.getfixturevalue(role))
    assert api_client.patch(f"{API}/admin/services/{servico.pk}", {
        "preco": "1.00",
    }, format="json").status_code == 403


def test_historia_e_snapshot_preservados(api_client, cliente, profissional, servico, disponibilidade):
    booking = criar_agendamento(
        cliente=cliente, profissional=profissional, servico=servico,
        inicio=inicio_em(proxima_data_util(), 10),
    )
    servico.preco, servico.duracao_minutos, servico.ativo = "200", 60, False
    servico.save()
    api_client.force_authenticate(cliente)
    data = api_client.get(f"{API}/appointments/{booking.pk}").data
    assert data["preco"] == "50.00" and data["duracao_minutos"] == 30
    assert api_client.post(f"{API}/appointments", {
        "profissional": profissional.pk, "servico": servico.pk,
        "data_hora": (timezone.now() + timedelta(days=2)).isoformat(),
    }, format="json").status_code == 400


def test_profissional_nao_altera_agenda_alheia(
    api_client, cliente, profissional, servico, disponibilidade, criar_usuario,
):
    outro = criar_usuario(username="outro_barbeiro", perfil="barbeiro", telefone="11912345678")
    from catalog.models import Profissional
    Profissional.objects.create(usuario=outro)
    booking = criar_agendamento(
        cliente=cliente, profissional=profissional, servico=servico,
        inicio=inicio_em(proxima_data_util(), 10),
    )
    api_client.force_authenticate(outro)
    assert api_client.get(f"{API}/appointments/{booking.pk}").status_code == 404
    assert api_client.get(f"{API}/me/history/professional").data == []
    assert api_client.patch(f"{API}/me/agenda/{booking.pk}/status", {
        "status": "confirmado",
    }, format="json").status_code == 403


def test_health_e_contrato_openapi(api_client):
    assert api_client.get(f"{API}/health").data == {"status": "ok", "database": "ok"}
    schema = api_client.get(f"{API}/schema", HTTP_ACCEPT="application/json")
    assert schema.status_code == 200
    paths = schema.data["paths"]
    for path in [
        "/auth/register", "/auth/login", "/auth/refresh", "/auth/logout", "/me",
        "/me/password", "/barbershop", "/professionals", "/services",
        "/appointments", "/me/agenda", "/me/agenda/week", "/me/history",
        "/me/history/professional", "/admin/history", "/admin/appointments",
        "/admin/professionals", "/admin/services", "/admin/availability",
    ]:
        assert API + path in paths
    assert all(path.startswith(API + "/") for path in paths)
    assert "security" in paths[API + "/appointments"]["post"]
    assert not paths[API + "/services"]["get"].get("security", []) or {} in paths[API + "/services"]["get"]["security"]
    assert api_client.get(f"{API}/docs").status_code == 200