from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "perfil", "telefone", "is_active", "is_staff")
    list_filter = ("perfil", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "telefone")
    fieldsets = UserAdmin.fieldsets + (
        ("Perfil", {"fields": ("perfil", "telefone")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Perfil", {"fields": ("perfil", "telefone")}),
    )
