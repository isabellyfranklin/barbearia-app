from rest_framework import serializers

from accounts.serializers import UsuarioResumoSerializer
from catalog.models import Profissional, Servico

from .models import Agendamento, Disponibilidade
from .services import criar_agendamento


class DisponibilidadeSerializer(serializers.ModelSerializer):
    profissional_nome = serializers.ReadOnlyField(source="profissional.nome")
    dia_semana_display = serializers.CharField(
        source="get_dia_semana_display",
        read_only=True,
    )

    class Meta:
        model = Disponibilidade
        fields = (
            "id",
            "profissional",
            "profissional_nome",
            "dia_semana",
            "dia_semana_display",
            "hora_inicio",
            "hora_fim",
            "ativo",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        inicio = attrs.get(
            "hora_inicio",
            getattr(self.instance, "hora_inicio", None),
        )
        fim = attrs.get("hora_fim", getattr(self.instance, "hora_fim", None))
        if inicio and fim and inicio >= fim:
            raise serializers.ValidationError(
                {"hora_fim": "O horário final deve ser maior que o inicial."}
            )
        return attrs


class AgendamentoSerializer(serializers.ModelSerializer):
    cliente = UsuarioResumoSerializer(read_only=True)
    profissional_nome = serializers.ReadOnlyField(source="profissional.nome")
    servico_nome = serializers.ReadOnlyField(source="servico.nome")
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    fim = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Agendamento
        fields = (
            "id",
            "cliente",
            "profissional",
            "profissional_nome",
            "servico",
            "servico_nome",
            "data_hora",
            "fim",
            "duracao_minutos",
            "preco",
            "status",
            "status_display",
            "observacoes",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = fields


class AgendamentoCreateSerializer(serializers.Serializer):
    profissional = serializers.PrimaryKeyRelatedField(
        queryset=Profissional.objects.filter(
            ativo=True,
            usuario__is_active=True,
        )
    )
    servico = serializers.PrimaryKeyRelatedField(
        queryset=Servico.objects.filter(ativo=True)
    )
    data_hora = serializers.DateTimeField()
    observacoes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def create(self, validated_data):
        request = self.context["request"]
        data_hora = validated_data.pop("data_hora")
        return criar_agendamento(
            cliente=request.user,
            inicio=data_hora,
            **validated_data,
        )


class AgendamentoStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Agendamento.Status.choices)
