from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Barbearia(models.Model):
    """Registro único com os dados da barbearia."""

    proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="barbearias",
        limit_choices_to={"perfil": "administrador"},
        verbose_name="proprietário",
    )
    nome = models.CharField("nome", max_length=120, default="Barbearia")
    descricao = models.TextField("descrição", blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)
    cidade = models.CharField("cidade", max_length=100, blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "barbearia"
        verbose_name_plural = "barbearia"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Garante o registro único (singleton).
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Profissional(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profissional",
        limit_choices_to={"perfil": "barbeiro"},
        verbose_name="usuário",
    )
    especialidades = models.CharField("especialidades", max_length=255, blank=True)
    bio = models.TextField("bio", blank=True)
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "profissional"
        verbose_name_plural = "profissionais"
        ordering = ("usuario__first_name", "usuario__username")

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def nome(self) -> str:
        return self.usuario.get_full_name() or self.usuario.username


class Servico(models.Model):
    nome = models.CharField("nome", max_length=120)
    descricao = models.TextField("descrição", blank=True)
    duracao_minutos = models.PositiveIntegerField(
        "duração (minutos)",
        validators=[MinValueValidator(5)],
    )
    preco = models.DecimalField(
        "preço",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "serviço"
        verbose_name_plural = "serviços"
        ordering = ("nome",)

    def __str__(self):
        return f"{self.nome} ({self.duracao_minutos} min)"
