from django.contrib import admin

from .models import Barbearia, Profissional, Servico


@admin.register(Barbearia)
class BarbeariaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cidade", "telefone", "atualizado_em")

    def has_add_permission(self, request):
        return not Barbearia.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "especialidades", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "especialidades",
    )
    list_select_related = ("usuario",)


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "duracao_minutos", "preco", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")
