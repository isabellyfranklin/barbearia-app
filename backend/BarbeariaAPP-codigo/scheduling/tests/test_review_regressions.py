from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from rest_framework.exceptions import ValidationError

from scheduling.admin import AgendamentoAdmin
from scheduling.models import Agendamento
from scheduling.services import atualizar_status, cancelar_agendamento, criar_agendamento
from scheduling.tests.test_scheduling import inicio_em, proxima_data_util

pytestmark = pytest.mark.django_db


@pytest.fixture
def reserva(cliente, profissional, servico, disponibilidade):
    return criar_agendamento(
        cliente=cliente, profissional=profissional, servico=servico,
        inicio=inicio_em(proxima_data_util(), 10),
    )


@pytest.mark.parametrize("segundos,codigo", [(-1, 200), (0, 400), (1, 400)])
@pytest.mark.parametrize("estado", ["pendente", "confirmado"])
def test_limite_cancelamento_cliente(api_client, cliente, reserva, segundos, codigo, estado):
    Agendamento.objects.filter(pk=reserva.pk).update(status=estado)
    api_client.force_authenticate(cliente)
    instante = reserva.data_hora + timedelta(seconds=segundos)
    with patch("scheduling.services.timezone.now", return_value=instante):
        resposta = api_client.patch(f"/api/appointments/{reserva.pk}/cancel")
    assert resposta.status_code == codigo
    reserva.refresh_from_db()
    assert reserva.status == ("cancelado" if codigo == 200 else estado)


def test_admin_pode_cancelar_apos_inicio(api_client, administrador, reserva):
    api_client.force_authenticate(administrador)
    with patch("scheduling.services.timezone.now", return_value=reserva.data_hora):
        resposta = api_client.patch(f"/api/appointments/{reserva.pk}/cancel")
    assert resposta.status_code == 200


def test_confirmacao_com_objeto_desatualizado_nao_reabre_cancelamento(reserva):
    copia_antiga = Agendamento.objects.get(pk=reserva.pk)
    cancelar_agendamento(reserva)
    with pytest.raises(ValidationError):
        atualizar_status(copia_antiga, Agendamento.Status.CONFIRMADO)
    reserva.refresh_from_db()
    assert reserva.status == Agendamento.Status.CANCELADO


def test_cancelamento_desatualizado_nao_sobrescreve_conclusao(reserva):
    atualizar_status(reserva, Agendamento.Status.CONFIRMADO)
    copia_antiga = Agendamento.objects.get(pk=reserva.pk)
    atualizar_status(reserva, Agendamento.Status.CONCLUIDO)
    with pytest.raises(ValidationError):
        cancelar_agendamento(copia_antiga)
    reserva.refresh_from_db()
    assert reserva.status == Agendamento.Status.CONCLUIDO


def test_admin_agendamentos_somente_consulta(rf, administrador, reserva):
    request = rf.get("/admin/")
    request.user = administrador
    model_admin = AgendamentoAdmin(Agendamento, AdminSite())
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_delete_permission(request, reserva)
    campos = {field.name for field in Agendamento._meta.fields}
    assert set(model_admin.get_readonly_fields(request, reserva)) == campos
