from django.contrib.auth.models import UserManager


class UsuarioManager(UserManager):
    """Manager que garante o perfil de administrador ao criar superusuários."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("perfil", "administrador")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        return super().create_superuser(username, email, password, **extra_fields)
