from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

Usuario = get_user_model()


class UsuarioResumoSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = Usuario
        fields = ("id", "username", "nome", "first_name", "last_name", "telefone")
        read_only_fields = fields


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telefone",
            "perfil",
        )
        read_only_fields = ("id", "username", "perfil")


class RegistroSerializer(serializers.ModelSerializer):
    telefone = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=Usuario.objects.all(),
                message="Já existe um usuário com este telefone.",
            )
        ],
    )
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telefone",
            "password",
            "password_confirm",
        )
        read_only_fields = ("id",)

    def validate_email(self, value):
        if value and Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "As senhas não conferem."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return Usuario.objects.create_user(
            perfil=Usuario.Perfil.CLIENTE,
            password=password,
            **validated_data,
        )


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UsuarioSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
