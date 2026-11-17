from django.urls import path

from .views import (
    AdminAgendamentoListView,
    AdminDisponibilidadeDetailView,
    AdminDisponibilidadeListCreateView,
    AgendamentoDetailView,
    AtualizarStatusAgendamentoView,
    CancelarAgendamentoView,
    HistoricoAdminView,
    HistoricoClienteView,
    HistoricoProfissionalView,
    MeusAgendamentosView,
    MinhaAgendaSemanaView,
    MinhaAgendaView,
    ProfissionalDisponibilidadeView,
)

urlpatterns = [
    path(
        "professionals/<int:pk>/availability",
        ProfissionalDisponibilidadeView.as_view(),
        name="professional-availability",
    ),
    path("appointments", MeusAgendamentosView.as_view(), name="appointments"),
    path(
        "appointments/<int:pk>",
        AgendamentoDetailView.as_view(),
        name="appointment-detail",
    ),
    path(
        "appointments/<int:pk>/cancel",
        CancelarAgendamentoView.as_view(),
        name="appointment-cancel",
    ),
    path("me/agenda", MinhaAgendaView.as_view(), name="me-agenda"),
    path(
        "me/agenda/week",
        MinhaAgendaSemanaView.as_view(),
        name="me-agenda-week",
    ),
    path(
        "me/agenda/<int:pk>/status",
        AtualizarStatusAgendamentoView.as_view(),
        name="me-agenda-status",
    ),
    path("me/history", HistoricoClienteView.as_view(), name="me-history"),
    path(
        "me/history/professional",
        HistoricoProfissionalView.as_view(),
        name="me-history-professional",
    ),
    path(
        "admin/availability",
        AdminDisponibilidadeListCreateView.as_view(),
        name="admin-availability",
    ),
    path(
        "admin/availability/<int:pk>",
        AdminDisponibilidadeDetailView.as_view(),
        name="admin-availability-detail",
    ),
    path(
        "admin/appointments",
        AdminAgendamentoListView.as_view(),
        name="admin-appointments",
    ),
    path(
        "admin/history",
        HistoricoAdminView.as_view(),
        name="admin-history",
    ),
]
