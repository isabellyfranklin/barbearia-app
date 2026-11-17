from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from catalog.models import Profissional, Servico


class Disponibilidade(models.Model):
    """Bloco semanal de atendimento de um profissional."""

    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="disponibilidades",
        verbose_name="profissional",
    )
    dia_semana = models.PositiveSmallIntegerField(
        "dia da semana",
        choices=DiaSemana.choices,
    )
    hora_inicio = models.TimeField("hora de início")
    hora_fim = models.TimeField("hora de término")
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "disponibilidade"
        verbose_name_plural = "disponibilidades"
        ordering = ("dia_semana", "hora_inicio")
        indexes = [
            models.Index(
                fields=["profissional", "dia_semana"],
                name="disp_prof_dia_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(hora_fim__gt=F("hora_inicio")),
                name="disp_hora_fim_maior",
            ),
            models.UniqueConstraint(
                fields=["profissional", "dia_semana", "hora_inicio", "hora_fim"],
                name="disp_unica",
            ),
        ]

    def __str__(self):
        return (
            f"{self.profissional} - {self.get_dia_semana_display()} "
            f"{self.hora_inicio:%H:%M}-{self.hora_fim:%H:%M}"
        )


class Agendamento(models.Model):
    """Reserva de um serviço com um profissional."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        limit_choices_to={"perfil": "cliente"},
        verbose_name="cliente",
    )
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        verbose_name="profissional",
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        verbose_name="serviço",
    )
    data_hora = models.DateTimeField("data e hora")
    duracao_minutos = models.PositiveIntegerField(
        "duração (minutos)",
        validators=[MinValueValidator(1)],
    )
    preco = models.DecimalField(
        "preço",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    observacoes = models.TextField("observações", blank=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "agendamento"
        verbose_name_plural = "agendamentos"
        ordering = ("data_hora",)
        indexes = [
            models.Index(
                fields=["profissional", "data_hora"],
                name="agend_prof_data_idx",
            ),
            models.Index(
                fields=["cliente", "data_hora"],
                name="agend_cliente_data_idx",
            ),
            models.Index(fields=["status"], name="agend_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(duracao_minutos__gt=0),
                name="agend_duracao_positiva",
            ),
            models.CheckConstraint(
                condition=Q(preco__gte=0),
                name="agend_preco_nao_negativo",
            ),
        ]

    def __str__(self):
        return (
            f"{self.cliente} - {self.servico} com {self.profissional} "
            f"em {self.data_hora:%d/%m/%Y %H:%M}"
        )

    @property
    def fim(self):
        return self.data_hora + timedelta(minutes=self.duracao_minutos)

    @property
    def esta_ativo(self) -> bool:
        return self.status in (self.Status.PENDENTE, self.Status.CONFIRMADO)
