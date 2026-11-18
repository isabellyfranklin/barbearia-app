from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from scheduling.models import Agendamento
from scheduling.services import (
    atualizar_status,
    cancelar_agendamento,
    criar_agendamento,
    horarios_disponiveis,
    horarios_disponiveis_periodo,
)

pytestmark = pytest.mark.django_db


def proxima_data_util():
    data = timezone.localdate() + timedelta(days=1)
    while data.weekday() > 5:  # domingo não tem disponibilidade
        data += timedelta(days=1)
    return data


def inicio_em(data, hora, minuto=0):
    return timezone.make_aware(
        datetime.combine(data, time(hora, minuto)),
        timezone.get_current_timezone(),
    )


def test_horarios_disponiveis_respeitam_blocos(profissional, disponibilidade):
    data = proxima_data_util()

    slots = horarios_disponiveis(profissional, data)

    assert len(slots) == 18  # 09:00 até 17:30, de 30 em 30 minutos
    assert slots[0] == inicio_em(data, 9)
    assert slots[-1] == inicio_em(data, 17, 30)


def test_horarios_disponiveis_excluem_agendamentos(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )

    slots = horarios_disponiveis(profissional, data)

    assert inicio_em(data, 10) not in slots
    assert inicio_em(data, 9, 30) in slots
    assert inicio_em(data, 10, 30) in slots


def test_horarios_disponiveis_consideram_duracao_do_servico(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )

    slots = horarios_disponiveis(profissional, data, duracao_minutos=60)

    assert inicio_em(data, 9, 30) not in slots
    assert inicio_em(data, 10) not in slots
    assert inicio_em(data, 10, 30) in slots
    assert inicio_em(data, 11) in slots


def test_disponibilidade_periodo_le_em_lote(
    cliente, profissional, servico, disponibilidade, django_assert_num_queries
):
    de = proxima_data_util()
    ate = de + timedelta(days=14)
    horario_ocupado = inicio_em(de, 10)
    criar_agendamento(
        cliente=cliente, profissional=profissional, servico=servico, inicio=horario_ocupado
    )

    with django_assert_num_queries(2):
        dias = horarios_disponiveis_periodo(profissional, de, ate, 30)

    assert list(dias) == [
        data
        for i in range(15)
        if (data := de + timedelta(days=i)).weekday() < 6
    ]
    assert horario_ocupado not in dias[de]
    assert inicio_em(de, 10, 30) in dias[de]
    assert inicio_em(ate, 10) in dias[ate]


def test_criar_agendamento_copia_preco_e_duracao(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()

    agendamento = criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 11),
        observacoes="Primeira visita",
    )

    assert agendamento.status == Agendamento.Status.PENDENTE
    assert agendamento.duracao_minutos == servico.duracao_minutos
    assert agendamento.preco == servico.preco
    assert agendamento.fim == inicio_em(data, 11, 30)


def test_criar_agendamento_bloqueia_conflito(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )

    with pytest.raises(ValidationError):
        criar_agendamento(
            cliente=cliente,
            profissional=profissional,
            servico=servico,
            inicio=inicio_em(data, 10, 15),
        )


def test_criar_agendamento_fora_da_disponibilidade(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()

    with pytest.raises(ValidationError):
        criar_agendamento(
            cliente=cliente,
            profissional=profissional,
            servico=servico,
            inicio=inicio_em(data, 20),
        )


def test_criar_agendamento_no_passado(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = timezone.localdate() - timedelta(days=1)
    while data.weekday() > 5:
        data -= timedelta(days=1)

    with pytest.raises(ValidationError):
        criar_agendamento(
            cliente=cliente,
            profissional=profissional,
            servico=servico,
            inicio=inicio_em(data, 10),
        )


def test_cancelar_libera_horario(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    agendamento = criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )

    cancelar_agendamento(agendamento)

    assert inicio_em(data, 10) in horarios_disponiveis(profissional, data)


def test_transicoes_de_status_validas(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    agendamento = criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )

    atualizar_status(agendamento, Agendamento.Status.CONFIRMADO)
    assert agendamento.status == Agendamento.Status.CONFIRMADO

    atualizar_status(agendamento, Agendamento.Status.CONCLUIDO)
    assert agendamento.status == Agendamento.Status.CONCLUIDO


def test_transicao_de_status_invalida(
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    agendamento = criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )

    with pytest.raises(ValidationError):
        atualizar_status(agendamento, Agendamento.Status.CONCLUIDO)


def test_api_cria_agendamento_e_impede_duplicidade(
    api_client,
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    payload = {
        "profissional": profissional.id,
        "servico": servico.id,
        "data_hora": inicio_em(data, 10).isoformat(),
    }
    api_client.force_authenticate(cliente)

    primeira = api_client.post("/api/appointments", payload, format="json")
    segunda = api_client.post("/api/appointments", payload, format="json")

    assert primeira.status_code == 201
    assert primeira.data["status"] == "pendente"
    assert primeira.data["preco"] == "50.00"
    assert segunda.status_code == 400


def test_cliente_nao_ve_agendamento_de_outro(
    api_client,
    cliente,
    outro_cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    agendamento = criar_agendamento(
        cliente=outro_cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )
    api_client.force_authenticate(cliente)

    resposta = api_client.get(f"/api/appointments/{agendamento.id}")

    assert resposta.status_code == 404


def test_cliente_cancela_proprio_agendamento(
    api_client,
    cliente,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    agendamento = criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )
    api_client.force_authenticate(cliente)

    resposta = api_client.patch(f"/api/appointments/{agendamento.id}/cancel")

    assert resposta.status_code == 200
    assert resposta.data["status"] == "cancelado"


def test_agenda_do_barbeiro_mostra_proprios_atendimentos(
    api_client,
    cliente,
    barbeiro,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )
    api_client.force_authenticate(barbeiro)

    resposta = api_client.get(f"/api/me/agenda?date={data.isoformat()}")

    assert resposta.status_code == 200
    assert len(resposta.data) == 1
    assert resposta.data[0]["profissional"] == profissional.id


def test_barbeiro_confirma_proprio_atendimento(
    api_client,
    cliente,
    barbeiro,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    agendamento = criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )
    api_client.force_authenticate(barbeiro)

    resposta = api_client.patch(
        f"/api/me/agenda/{agendamento.id}/status",
        {"status": "confirmado"},
        format="json",
    )

    assert resposta.status_code == 200
    assert resposta.data["status"] == "confirmado"


def test_cliente_nao_acessa_agenda_profissional(
    api_client,
    cliente,
    disponibilidade,
):
    api_client.force_authenticate(cliente)

    resposta = api_client.get("/api/me/agenda")

    assert resposta.status_code == 403


def test_admin_ve_historico_geral(
    api_client,
    cliente,
    administrador,
    profissional,
    servico,
    disponibilidade,
):
    data = proxima_data_util()
    criar_agendamento(
        cliente=cliente,
        profissional=profissional,
        servico=servico,
        inicio=inicio_em(data, 10),
    )
    api_client.force_authenticate(administrador)

    resposta = api_client.get("/api/admin/history")

    assert resposta.status_code == 200
    assert len(resposta.data) == 1


def test_disponibilidade_publica_por_data(
    api_client,
    profissional,
    disponibilidade,
):
    data = proxima_data_util()

    resposta = api_client.get(
        f"/api/professionals/{profissional.id}/availability"
        f"?date={data.isoformat()}"
    )

    assert resposta.status_code == 200
    assert resposta.data["date"] == data.isoformat()
    assert len(resposta.data["slots"]) == 18
