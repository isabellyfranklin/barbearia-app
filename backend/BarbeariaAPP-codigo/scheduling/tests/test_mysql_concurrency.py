from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Barrier, Event

import pytest
from django.db import close_old_connections, connection, connections, transaction
from rest_framework.exceptions import ValidationError

from scheduling.models import Agendamento
from scheduling.services import atualizar_status, cancelar_agendamento, criar_agendamento
from scheduling.tests.test_scheduling import inicio_em, proxima_data_util

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "mysql", reason="Exige MySQL real"),
]


def _worker(operacao, barreira=None):
    close_old_connections()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT CONNECTION_ID()")
            conexao = cursor.fetchone()[0]
        if barreira is not None:
            barreira.wait(timeout=15)
        try:
            operacao()
            return conexao, "ok"
        except ValidationError:
            return conexao, "rejeitado"
    finally:
        connections.close_all()


def _reserva(cliente, profissional, servico):
    return criar_agendamento(
        cliente=cliente, profissional=profissional, servico=servico,
        inicio=inicio_em(proxima_data_util(), 10),
    )


def test_mysql_duas_reservas_simultaneas_mesmo_horario(
    cliente, profissional, servico, disponibilidade,
):
    barreira = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _worker, lambda: _reserva(cliente, profissional, servico), barreira,
            )
            for _ in range(2)
        ]
        resultados = [future.result(timeout=20) for future in futures]
    assert len({conexao for conexao, _ in resultados}) == 2
    assert sorted(resultado for _, resultado in resultados) == ["ok", "rejeitado"]
    assert Agendamento.objects.filter(profissional=profissional).count() == 1


def test_mysql_confirmacao_e_cancelamento_simultaneos(
    cliente, profissional, servico, disponibilidade,
):
    reserva = _reserva(cliente, profissional, servico)
    copia = Agendamento.objects.get(pk=reserva.pk)
    barreira = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        confirmar = executor.submit(
            _worker,
            lambda: atualizar_status(copia, Agendamento.Status.CONFIRMADO),
            barreira,
        )
        cancelar = executor.submit(
            _worker, lambda: cancelar_agendamento(reserva), barreira,
        )
        resultado_confirmar = confirmar.result(timeout=20)
        resultado_cancelar = cancelar.result(timeout=20)
    assert resultado_confirmar[0] != resultado_cancelar[0]
    assert resultado_cancelar[1] == "ok"
    assert resultado_confirmar[1] in {"ok", "rejeitado"}
    reserva.refresh_from_db()
    assert reserva.status == Agendamento.Status.CANCELADO


def test_mysql_confirmacao_aguarda_cancelamento_e_nao_reabre_reserva(
    cliente, profissional, servico, disponibilidade,
):
    reserva = _reserva(cliente, profissional, servico)
    copia_antiga = Agendamento.objects.get(pk=reserva.pk)
    iniciado = Event()

    def confirmar():
        iniciado.set()
        atualizar_status(copia_antiga, Agendamento.Status.CONFIRMADO)

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            Agendamento.objects.select_for_update().get(pk=reserva.pk)
            cancelar_agendamento(reserva)
            future = executor.submit(_worker, confirmar)
            assert iniciado.wait(timeout=10)
            # Outra conexão não deve concluir enquanto esta transação mantém o lock.
            with pytest.raises(TimeoutError):
                future.result(timeout=0.3)
        _, resultado = future.result(timeout=15)
    assert resultado == "rejeitado"
    reserva.refresh_from_db()
    assert reserva.status == Agendamento.Status.CANCELADO
