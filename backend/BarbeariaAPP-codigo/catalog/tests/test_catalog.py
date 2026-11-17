import pytest
from django.contrib.auth import get_user_model

from catalog.models import Barbearia, Profissional, Servico

pytestmark = pytest.mark.django_db


def test_barbearia_e_registro_unico(api_client):
    primeira = api_client.get("/api/barbershop")
    segunda = api_client.get("/api/barbershop")

    assert primeira.status_code == 200
    assert segunda.status_code == 200
    assert primeira.data["id"] == segunda.data["id"] == 1
    assert Barbearia.objects.count() == 1


def test_lista_apenas_servicos_ativos(api_client, servico):
    Servico.objects.create(
        nome="Inativo",
        duracao_minutos=30,
        preco="10.00",
        ativo=False,
    )

    resposta = api_client.get("/api/services")

    assert resposta.status_code == 200
    assert len(resposta.data) == 1
    assert resposta.data[0]["nome"] == servico.nome
    assert resposta.data[0]["preco"] == "50.00"


def test_lista_apenas_profissionais_ativos(api_client, profissional):
    outro_usuario = get_user_model().objects.create_user(
        username="inativo",
        password="senha12345",
        perfil="barbeiro",
        telefone="11955550000",
    )
    Profissional.objects.create(usuario=outro_usuario, ativo=False)

    resposta = api_client.get("/api/professionals")

    assert resposta.status_code == 200
    assert len(resposta.data) == 1
    assert resposta.data[0]["id"] == profissional.id


def test_admin_atualiza_dados_da_barbearia(api_client, administrador):
    api_client.force_authenticate(administrador)

    resposta = api_client.patch(
        "/api/admin/barbershop",
        {"nome": "Nova Barbearia", "cidade": "Campinas"},
        format="json",
    )

    assert resposta.status_code == 200
    assert resposta.data["nome"] == "Nova Barbearia"
    assert Barbearia.load().nome == "Nova Barbearia"


def test_cliente_nao_acessa_area_administrativa(api_client, cliente):
    api_client.force_authenticate(cliente)

    resposta = api_client.get("/api/admin/services")

    assert resposta.status_code == 403


def test_admin_cria_profissional_com_usuario_barbeiro(api_client, administrador):
    api_client.force_authenticate(administrador)

    resposta = api_client.post(
        "/api/admin/professionals",
        {
            "username": "novo_barbeiro",
            "email": "barbeiro@exemplo.com",
            "first_name": "Novo",
            "last_name": "Barbeiro",
            "telefone": "11944443333",
            "password": "senhaSegura123",
            "especialidades": "Degradê",
        },
        format="json",
    )

    assert resposta.status_code == 201
    usuario = get_user_model().objects.get(username="novo_barbeiro")
    assert usuario.perfil == "barbeiro"
    assert usuario.profissional.especialidades == "Degradê"


def test_admin_desativa_servico_em_vez_de_excluir(api_client, administrador, servico):
    api_client.force_authenticate(administrador)

    resposta = api_client.delete(f"/api/admin/services/{servico.id}")

    assert resposta.status_code == 204
    servico.refresh_from_db()
    assert servico.ativo is False
    assert Servico.objects.filter(pk=servico.pk).exists()
