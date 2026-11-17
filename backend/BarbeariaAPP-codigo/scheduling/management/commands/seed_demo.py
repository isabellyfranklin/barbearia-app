"""Popula o banco com dados de demonstração da barbearia."""
from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Usuario
from catalog.models import Barbearia, Profissional, Servico
from scheduling.models import Disponibilidade


class Command(BaseCommand):
    help = "Cria a barbearia, usuários, serviços e disponibilidades de exemplo."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._usuario(
            "admin",
            "admin123",
            perfil=Usuario.Perfil.ADMINISTRADOR,
            first_name="Ana",
            last_name="Proprietária",
            email="admin@barbearia.local",
            telefone="11999990000",
            is_staff=True,
            is_superuser=True,
        )

        barbearia = Barbearia.load()
        barbearia.proprietario = admin
        barbearia.nome = "Barbearia Estilo"
        barbearia.descricao = "Cortes, barba e cuidados masculinos."
        barbearia.endereco = "Rua das Tesouras, 123"
        barbearia.cidade = "São Paulo"
        barbearia.telefone = "1133334444"
        barbearia.email = "contato@barbearia.local"
        barbearia.save()
        self.stdout.write("Barbearia configurada.")

        self._profissional(
            "joao",
            "barbeiro123",
            first_name="João",
            last_name="Silva",
            telefone="11988880001",
            especialidades="Corte masculino, barba",
            bio="Barbeiro há 10 anos, especialista em degradê.",
        )
        self._profissional(
            "carlos",
            "barbeiro123",
            first_name="Carlos",
            last_name="Souza",
            telefone="11988880002",
            especialidades="Corte, barba e sobrancelha",
            bio="Atendimento clássico e social.",
        )

        self._usuario(
            "cliente",
            "cliente123",
            perfil=Usuario.Perfil.CLIENTE,
            first_name="Maria",
            last_name="Oliveira",
            email="cliente@barbearia.local",
            telefone="11977770001",
        )

        self._servico(
            "Corte masculino",
            30,
            "50.00",
            "Corte com máquina e tesoura.",
        )
        self._servico("Barba", 30, "40.00", "Aparo e modelagem da barba.")
        self._servico(
            "Corte + barba",
            60,
            "80.00",
            "Combo completo de corte e barba.",
        )
        self._servico(
            "Sobrancelha",
            15,
            "20.00",
            "Design de sobrancelha masculina.",
        )

        for profissional in Profissional.objects.all():
            self._disponibilidades(profissional)

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))

    def _usuario(self, username, senha, **campos):
        usuario, criado = Usuario.objects.get_or_create(
            username=username,
            defaults=campos,
        )
        if criado:
            usuario.set_password(senha)
            usuario.save()
            self.stdout.write(
                f"Usuário criado: {username} / {senha}"
            )
        return usuario

    def _profissional(self, username, senha, especialidades="", bio="", **campos):
        usuario = self._usuario(
            username,
            senha,
            perfil=Usuario.Perfil.BARBEIRO,
            **campos,
        )
        profissional, _ = Profissional.objects.get_or_create(
            usuario=usuario,
            defaults={
                "especialidades": especialidades,
                "bio": bio,
                "ativo": True,
            },
        )
        return profissional

    def _servico(self, nome, duracao, preco, descricao):
        servico, criado = Servico.objects.get_or_create(
            nome=nome,
            defaults={
                "duracao_minutos": duracao,
                "preco": preco,
                "descricao": descricao,
                "ativo": True,
            },
        )
        if criado:
            self.stdout.write(f"Serviço criado: {nome}")
        return servico

    def _disponibilidades(self, profissional):
        blocos = [
            (0, time(9, 0), time(12, 0)),
            (0, time(13, 0), time(19, 0)),
            (1, time(9, 0), time(12, 0)),
            (1, time(13, 0), time(19, 0)),
            (2, time(9, 0), time(12, 0)),
            (2, time(13, 0), time(19, 0)),
            (3, time(9, 0), time(12, 0)),
            (3, time(13, 0), time(19, 0)),
            (4, time(9, 0), time(12, 0)),
            (4, time(13, 0), time(19, 0)),
            (5, time(9, 0), time(14, 0)),
        ]
        for dia, inicio, fim in blocos:
            Disponibilidade.objects.get_or_create(
                profissional=profissional,
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fim=fim,
                defaults={"ativo": True},
            )
