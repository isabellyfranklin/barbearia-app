from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UsuarioManager


class Usuario(AbstractUser):
    class Perfil(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        BARBEIRO = "barbeiro", "Barbeiro"
        ADMINISTRADOR = "administrador", "Administrador/proprietário"

    perfil = models.CharField(
        "perfil",
        max_length=20,
        choices=Perfil.choices,
        default=Perfil.CLIENTE,
    )
    telefone = models.CharField(
        "telefone",
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ("username",)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_cliente(self) -> bool:
        return self.perfil == self.Perfil.CLIENTE

    @property
    def is_barbeiro(self) -> bool:
        return self.perfil == self.Perfil.BARBEIRO

    @property
    def is_administrador(self) -> bool:
        return self.perfil == self.Perfil.ADMINISTRADOR or self.is_superuser
