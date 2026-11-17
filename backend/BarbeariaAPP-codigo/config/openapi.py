"""Contratos dos handlers customizados; o restante é inferido pelos serializers DRF."""
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

from accounts import views as accounts
from accounts.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    RegistroSerializer,
    UsuarioSerializer,
)
from catalog import views as catalog
from catalog.serializers import (
    AdminProfissionalCreateSerializer,
    AdminProfissionalSerializer,
    BarbeariaSerializer,
)
from scheduling import views as scheduling
from scheduling.serializers import (
    AgendamentoCreateSerializer,
    AgendamentoSerializer,
    AgendamentoStatusSerializer,
)


def only_v1(endpoints):
    return [entry for entry in endpoints if entry[0].startswith("/api/v1/")]


class SessionSerializer(serializers.Serializer):
    user = UsuarioSerializer()
    access = serializers.CharField()
    refresh = serializers.CharField()


class AvailabilityDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    duration_minutes = serializers.IntegerField()
    slots = serializers.ListField(child=serializers.DateTimeField())


class DaySlotsSerializer(serializers.Serializer):
    date = serializers.DateField()
    slots = serializers.ListField(child=serializers.DateTimeField())


# "from" é palavra reservada em Python.
AvailabilityRangeSerializer = inline_serializer("AvailabilityRange", {
    "from": serializers.DateField(),
    "to": serializers.DateField(),
    "duration_minutes": serializers.IntegerField(),
    "days": DaySlotsSerializer(many=True),
})
AgendaWeekSerializer = inline_serializer("AgendaWeek", {
    "from": serializers.DateField(),
    "to": serializers.DateField(),
    "appointments": AgendamentoSerializer(many=True),
})
DATE = OpenApiParameter("date", type=OpenApiTypes.DATE, description="Data local YYYY-MM-DD.")
FILTERS = [
    OpenApiParameter("from", type=str, description="Data inicial inclusiva YYYY-MM-DD."),
    OpenApiParameter("to", type=str, description="Data final inclusiva YYYY-MM-DD."),
    OpenApiParameter("status", enum=["pendente", "confirmado", "concluido", "cancelado"]),
]


def annotate_views():
    extend_schema_view(post=extend_schema(
        request=RegistroSerializer, responses={201: SessionSerializer},
    ))(accounts.RegisterView)
    extend_schema_view(post=extend_schema(
        request=LoginSerializer, responses={200: SessionSerializer},
    ))(accounts.LoginView)
    extend_schema_view(post=extend_schema(
        request=LogoutSerializer, responses={204: None},
    ))(accounts.LogoutView)
    extend_schema_view(post=extend_schema(
        request=PasswordChangeSerializer, responses={204: None},
    ))(accounts.PasswordChangeView)
    extend_schema_view(get=extend_schema(responses=BarbeariaSerializer))(catalog.BarbeariaView)
    extend_schema_view(patch=extend_schema(
        request=BarbeariaSerializer, responses=BarbeariaSerializer,
    ))(catalog.BarbeariaAdminView)
    extend_schema_view(post=extend_schema(
        request=AdminProfissionalCreateSerializer, responses={201: AdminProfissionalSerializer},
    ))(catalog.AdminProfissionalListCreateView)
    extend_schema_view(get=extend_schema(
        parameters=[
            OpenApiParameter("service", type=int, required=True, description="ID do serviço ativo."),
            DATE, *FILTERS[:2],
        ],
        responses=PolymorphicProxySerializer(
            component_name="Availability", serializers=[
                AvailabilityDaySerializer, AvailabilityRangeSerializer,
            ], resource_type_field_name=None,
        ),
        description="Use service e date OU service, from e to. Período máximo: 60 dias.",
    ))(scheduling.ProfissionalDisponibilidadeView)
    extend_schema_view(
        get=extend_schema(parameters=FILTERS),
        post=extend_schema(request=AgendamentoCreateSerializer, responses={201: AgendamentoSerializer}),
    )(scheduling.MeusAgendamentosView)
    extend_schema_view(patch=extend_schema(
        request=None, responses=AgendamentoSerializer,
        description="Cliente cancela a própria reserva somente antes do início; administrador também pode cancelar.",
    ))(scheduling.CancelarAgendamentoView)
    extend_schema_view(get=extend_schema(
        parameters=[DATE], responses=AgendamentoSerializer(many=True),
    ))(scheduling.MinhaAgendaView)
    extend_schema_view(get=extend_schema(
        parameters=[DATE], responses=AgendaWeekSerializer,
    ))(scheduling.MinhaAgendaSemanaView)
    extend_schema_view(patch=extend_schema(
        request=AgendamentoStatusSerializer, responses=AgendamentoSerializer,
        description="Somente o barbeiro responsável ou administrador. Estados finais não são reabertos.",
    ))(scheduling.AtualizarStatusAgendamentoView)
    for cls in [
        scheduling.HistoricoClienteView, scheduling.HistoricoProfissionalView,
        scheduling.HistoricoAdminView,
    ]:
        extend_schema_view(get=extend_schema(parameters=FILTERS))(cls)
    extend_schema_view(get=extend_schema(parameters=[
        *FILTERS, DATE, OpenApiParameter("professional", type=int),
    ]))(scheduling.AdminAgendamentoListView)
    extend_schema_view(get=extend_schema(parameters=[
        OpenApiParameter("professional", type=int),
    ]))(scheduling.AdminDisponibilidadeListCreateView)
