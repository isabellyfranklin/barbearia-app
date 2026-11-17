from rest_framework.permissions import BasePermission


class IsCliente(BasePermission):
    message = "Acesso permitido apenas para clientes."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "perfil", None) == "cliente"
        )


class IsBarbeiro(BasePermission):
    message = "Acesso permitido apenas para barbeiros."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "perfil", None) == "barbeiro"
        )


class IsAdministrador(BasePermission):
    message = "Acesso permitido apenas para o administrador/proprietário."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                getattr(user, "perfil", None) == "administrador"
                or user.is_superuser
            )
        )
