"""Regras de negócio de disponibilidade e agendamento.

A prevenção de conflito usa transação + ``SELECT ... FOR UPDATE`` no registro do
profissional. O MySQL não possui exclusion constraint, então o bloqueio da linha
serializa as reservas concorrentes do mesmo profissional.
"""
from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from catalog.models import Profissional

from .models import Agendamento, Disponibilidade

INTERVALO_SLOT_MINUTOS = 30

STATUS_ATIVOS = (
    Agendamento.Status.PENDENTE,
    Agendamento.Status.CONFIRMADO,
)

TRANSICOES_VALIDAS = {
    Agendamento.Status.PENDENTE: {
        Agendamento.Status.CONFIRMADO,
        Agendamento.Status.CANCELADO,
    },
    Agendamento.Status.CONFIRMADO: {
        Agendamento.Status.CONCLUIDO,
        Agendamento.Status.CANCELADO,
    },
    Agendamento.Status.CONCLUIDO: set(),
    Agendamento.Status.CANCELADO: set(),
}


def normalizar_inicio(valor: datetime) -> datetime:
    """Garante um datetime consciente de fuso no fuso local do projeto."""
    if timezone.is_naive(valor):
        return timezone.make_aware(valor, timezone.get_current_timezone())
    return timezone.localtime(valor)


def _aware(data, hora) -> datetime:
    return timezone.make_aware(
        datetime.combine(data, hora),
        timezone.get_current_timezone(),
    )


def _sobrepoe(inicio_a, fim_a, inicio_b, fim_b) -> bool:
    return inicio_a < fim_b and inicio_b < fim_a


def _intervalo_do_dia(data):
    inicio = _aware(data, time.min)
    return inicio, inicio + timedelta(days=1)


def _agendamentos_do_dia(profissional, data, excluir_pk=None):
    inicio, fim = _intervalo_do_dia(data)
    qs = _agendamentos_ativos(profissional, inicio, fim)
    if excluir_pk:
        qs = qs.exclude(pk=excluir_pk)
    return list(qs)


def _agendamentos_ativos(profissional, inicio, fim):
    return Agendamento.objects.filter(
        profissional=profissional,
        status__in=STATUS_ATIVOS,
        data_hora__gte=inicio,
        data_hora__lt=fim,
    )


def existe_conflito(profissional, inicio, fim, excluir_pk=None) -> bool:
    """Verifica sobreposição com agendamentos ativos do profissional."""
    data = timezone.localtime(inicio).date()
    for agendamento in _agendamentos_do_dia(profissional, data, excluir_pk):
        if _sobrepoe(inicio, fim, agendamento.data_hora, agendamento.fim):
            return True
    return False


def esta_dentro_da_disponibilidade(profissional, inicio, fim) -> bool:
    """Confere se todo o intervalo cabe em um bloco semanal do profissional."""
    inicio_local = timezone.localtime(inicio)
    fim_local = timezone.localtime(fim)
    if inicio_local.date() != fim_local.date():
        return False

    hora_inicio = inicio_local.time()
    hora_fim = fim_local.time()
    blocos = Disponibilidade.objects.filter(
        profissional=profissional,
        dia_semana=inicio_local.weekday(),
        ativo=True,
    )
    return any(
        bloco.hora_inicio <= hora_inicio and hora_fim <= bloco.hora_fim
        for bloco in blocos
    )


def horarios_disponiveis(
    profissional,
    data,
    duracao_minutos: int = INTERVALO_SLOT_MINUTOS,
):
    """Retorna a lista de horários livres do profissional em uma data."""
    return horarios_disponiveis_periodo(profissional, data, data, duracao_minutos).get(data, [])


def horarios_disponiveis_periodo(profissional, de, ate, duracao_minutos):
    """Calcula os dias com horários livres com leituras em lote."""
    datas = [de + timedelta(days=i) for i in range((ate - de).days + 1)]
    blocos_por_dia = defaultdict(list)
    blocos = Disponibilidade.objects.filter(
        profissional=profissional,
        dia_semana__in={data.weekday() for data in datas},
        ativo=True,
    ).values_list("dia_semana", "hora_inicio", "hora_fim")
    for dia, hora_inicio, hora_fim in blocos:
        blocos_por_dia[dia].append((hora_inicio, hora_fim))
    if not blocos_por_dia:
        return {}

    ocupados_por_data = defaultdict(list)
    inicio, _ = _intervalo_do_dia(de)
    _, fim = _intervalo_do_dia(ate)
    reservas = _agendamentos_ativos(profissional, inicio, fim).values_list(
        "data_hora", "duracao_minutos"
    )
    for inicio_reserva, duracao_reserva in reservas:
        data = timezone.localtime(inicio_reserva).date()
        ocupados_por_data[data].append(
            (inicio_reserva, inicio_reserva + timedelta(minutes=duracao_reserva))
        )

    agora = timezone.now()
    duracao = timedelta(minutes=duracao_minutos)
    resultado = {}
    for data in datas:
        slots = _slots_do_dia(
            data, blocos_por_dia[data.weekday()], ocupados_por_data[data], duracao, agora
        )
        if slots:
            resultado[data] = slots
    return resultado


def _slots_do_dia(data, blocos, ocupados, duracao, agora):
    livres = set()
    passo = timedelta(minutes=INTERVALO_SLOT_MINUTOS)
    for hora_inicio, hora_fim in blocos:
        candidato = _aware(data, hora_inicio)
        fim_bloco = _aware(data, hora_fim)
        while candidato + duracao <= fim_bloco:
            fim_candidato = candidato + duracao
            if candidato > agora and not any(
                _sobrepoe(candidato, fim_candidato, inicio, fim)
                for inicio, fim in ocupados
            ):
                livres.add(candidato)
            candidato += passo
    return sorted(livres)


def criar_agendamento(*, cliente, profissional, servico, inicio, observacoes=""):
    """Cria um agendamento validando disponibilidade e conflito de forma atômica."""
    inicio = normalizar_inicio(inicio)

    if not cliente.is_cliente:
        raise ValidationError(
            {"detail": "Apenas clientes podem criar agendamentos."}
        )
    if not servico.ativo:
        raise ValidationError({"servico": "Serviço indisponível."})
    if inicio <= timezone.now():
        raise ValidationError(
            {"data_hora": "Não é possível agendar em data/hora passada."}
        )

    fim = inicio + timedelta(minutes=servico.duracao_minutos)

    with transaction.atomic():
        # Bloqueia o profissional para serializar reservas concorrentes.
        profissional = Profissional.objects.select_for_update().get(
            pk=profissional.pk
        )
        if not profissional.ativo:
            raise ValidationError({"profissional": "Profissional indisponível."})
        if not esta_dentro_da_disponibilidade(profissional, inicio, fim):
            raise ValidationError(
                {
                    "data_hora": (
                        "Horário fora da disponibilidade do profissional."
                    )
                }
            )
        if existe_conflito(profissional, inicio, fim):
            raise ValidationError({"data_hora": "Horário já está ocupado."})

        return Agendamento.objects.create(
            cliente=cliente,
            profissional=profissional,
            servico=servico,
            data_hora=inicio,
            duracao_minutos=servico.duracao_minutos,
            preco=servico.preco,
            observacoes=observacoes,
        )


@transaction.atomic
def atualizar_status(agendamento, novo_status, *, usuario=None):
    """Valida a transição sobre o estado atual, bloqueado até o commit."""
    original = agendamento
    agendamento = Agendamento.objects.select_for_update().get(pk=original.pk)
    if (
        novo_status == Agendamento.Status.CANCELADO
        and usuario is not None
        and usuario.is_cliente
        and not usuario.is_administrador
        and timezone.now() >= agendamento.data_hora
    ):
        raise ValidationError(
            {"data_hora": "O cliente só pode cancelar antes do início do atendimento."}
        )
    if novo_status == agendamento.status:
        return agendamento

    permitidos = TRANSICOES_VALIDAS.get(agendamento.status, set())
    if novo_status not in permitidos:
        raise ValidationError(
            {
                "status": (
                    f"Transição de '{agendamento.get_status_display()}' para "
                    f"'{dict(Agendamento.Status.choices).get(novo_status, novo_status)}' "
                    "não permitida."
                )
            }
        )

    agendamento.status = novo_status
    agendamento.save(update_fields=["status", "atualizado_em"])
    original.status = agendamento.status
    original.atualizado_em = agendamento.atualizado_em
    return agendamento


def cancelar_agendamento(agendamento, *, usuario=None):
    """Cancela um agendamento pendente ou confirmado, liberando o horário."""
    return atualizar_status(
        agendamento, Agendamento.Status.CANCELADO, usuario=usuario
    )
