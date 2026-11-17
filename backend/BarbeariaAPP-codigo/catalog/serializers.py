from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Barbearia, Profissional, Servico

Usuario = get_user_model()


class BarbeariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barbearia
        fields = (
            "id",
            "nome",
            "descricao",
            "endereco",
            "cidade",
            "telefone",
            "email",
            "atualizado_em",
        )
        read_only_fields = ("id", "atualizado_em")


class ProfissionalSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(read_only=True)

    class Meta:
        model = Profissional
        fields = ("id", "nome", "especialidades", "bio", "ativo")
        read_only_fields = fields


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = ("id", "nome", "descricao", "duracao_minutos", "preco", "ativo")
        read_only_fields = ("id",)


class AdminProfissionalCreateSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=Usuario.objects.all(),
                message="Já existe um usuário com este nome de usuário.",
            )
        ]
    )
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    telefone = serializers.CharField(
        max_length=20,
        validators=[
            UniqueValidator(
                queryset=Usuario.objects.all(),
                message="Já existe um usuário com este telefone.",
            )
        ]
    )
    password = serializers.CharField(write_only=True, min_length=8)
    especialidades = serializers.CharField(required=False, allow_blank=True, max_length=255)
    bio = serializers.CharField(required=False, allow_blank=True)
    ativo = serializers.BooleanField(required=False, default=True)

    def validate_email(self, value):
        if value and Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")
        return value

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], Usuario(
                username=attrs.get("username", ""), email=attrs.get("email", ""),
                first_name=attrs.get("first_name", ""), last_name=attrs.get("last_name", ""),
            ))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        usuario_data = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email", ""),
            "first_name": validated_data.pop("first_name", ""),
            "last_name": validated_data.pop("last_name", ""),
            "telefone": validated_data.pop("telefone"),
        }
        password = validated_data.pop("password")
        usuario = Usuario.objects.create_user(
            perfil=Usuario.Perfil.BARBEIRO,
            is_active=validated_data.get("ativo", True),
            password=password,
            **usuario_data,
        )
        return Profissional.objects.create(usuario=usuario, **validated_data)


class AdminProfissionalSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="usuario.username", read_only=True)
    nome = serializers.CharField(read_only=True)
    email = serializers.EmailField(
        source="usuario.email", required=False, allow_blank=True, max_length=254
    )
    first_name = serializers.CharField(
        source="usuario.first_name", required=False, allow_blank=True, max_length=150
    )
    last_name = serializers.CharField(
        source="usuario.last_name", required=False, allow_blank=True, max_length=150
    )
    telefone = serializers.CharField(source="usuario.telefone", required=False, max_length=20)

    class Meta:
        model = Profissional
        fields = (
            "id",
            "username",
            "nome",
            "email",
            "first_name",
            "last_name",
            "telefone",
            "especialidades",
            "bio",
            "ativo",
        )
        read_only_fields = ("id", "username", "nome")

    def validate_email(self, value):
        if not value:
            return value
        qs = Usuario.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.usuario_id)
        if qs.exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")
        return value

    def validate_telefone(self, value):
        qs = Usuario.objects.filter(telefone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.usuario_id)
        if qs.exists():
            raise serializers.ValidationError("Já existe um usuário com este telefone.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        usuario_data = validated_data.pop("usuario", {})
        for attr, value in usuario_data.items():
            setattr(instance.usuario, attr, value)
        if "ativo" in validated_data:
            instance.usuario.is_active = validated_data["ativo"]
        instance.usuario.save()
        return super().update(instance, validated_data)
