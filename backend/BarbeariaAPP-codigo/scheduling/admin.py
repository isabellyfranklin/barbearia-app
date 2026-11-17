from django.contrib import admin

from .models import Agendamento, Disponibilidade


@admin.register(Disponibilidade)
class DisponibilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "profissional",
        "dia_semana",
        "hora_inicio",
        "hora_fim",
        "ativo",
    )
    list_filter = ("dia_semana", "ativo")
    search_fields = (
        "profissional__usuario__username",
        "profissional__usuario__first_name",
        "profissional__usuario__last_name",
    )
    list_select_related = ("profissional__usuario",)


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        "data_hora",
        "cliente",
        "profissional",
        "servico",
        "status",
        "preco",
    )
    list_filter = ("status", "profissional", "servico")
    search_fields = (
        "cliente__username",
        "cliente__first_name",
        "cliente__last_name",
        "profissional__usuario__username",
        "servico__nome",
    )
    list_select_related = ("cliente", "profissional__usuario", "servico")
    date_hierarchy = "data_hora"
    # Agendamentos devem ser alterados pelas operações validadas da API.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)
