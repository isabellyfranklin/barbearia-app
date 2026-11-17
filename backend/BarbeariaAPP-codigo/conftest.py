from datetime import time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Profissional, Servico
from scheduling.models import Disponibilidade

Usuario = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def criar_usuario(db):
    def _criar(username="usuario", perfil=Usuario.Perfil.CLIENTE, senha="senha12345", **extra):
        return Usuario.objects.create_user(
            username=username,
            password=senha,
            perfil=perfil,
            **extra,
        )

    return _criar


@pytest.fixture
def cliente(criar_usuario):
    return criar_usuario(
        username="cliente",
        perfil=Usuario.Perfil.CLIENTE,
        first_name="Maria",
        last_name="Oliveira",
        telefone="11900000001",
    )


@pytest.fixture
def outro_cliente(criar_usuario):
    return criar_usuario(
        username="cliente2",
        perfil=Usuario.Perfil.CLIENTE,
        first_name="Pedro",
        last_name="Santos",
        telefone="11900000002",
    )


@pytest.fixture
def administrador(criar_usuario):
    return criar_usuario(
        username="admin",
        perfil=Usuario.Perfil.ADMINISTRADOR,
        first_name="Ana",
        last_name="Proprietária",
        telefone="11900000003",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def barbeiro(criar_usuario):
    return criar_usuario(
        username="joao",
        perfil=Usuario.Perfil.BARBEIRO,
        first_name="João",
        last_name="Silva",
        telefone="11900000004",
    )


@pytest.fixture
def profissional(barbeiro):
    return Profissional.objects.create(
        usuario=barbeiro,
        especialidades="Corte masculino",
    )


@pytest.fixture
def servico(db):
    return Servico.objects.create(
        nome="Corte masculino",
        duracao_minutos=30,
        preco=Decimal("50.00"),
    )


@pytest.fixture
def disponibilidade(profissional):
    blocos = []
    for dia in range(6):  # segunda a sábado
        blocos.append(
            Disponibilidade.objects.create(
                profissional=profissional,
                dia_semana=dia,
                hora_inicio=time(9, 0),
                hora_fim=time(18, 0),
            )
        )
    return blocos
