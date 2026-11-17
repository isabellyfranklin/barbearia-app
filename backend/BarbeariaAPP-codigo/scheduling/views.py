from datetime import datetime, time, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdministrador, IsBarbeiro, IsCliente
from catalog.models import Profissional, Servico

from .models import Agendamento, Disponibilidade
from .serializers import (
    AgendamentoCreateSerializer,
    AgendamentoSerializer,
    AgendamentoStatusSerializer,
    DisponibilidadeSerializer,
)
from .services import (
    INTERVALO_SLOT_MINUTOS,
    atualizar_status,
    cancelar_agendamento,
    horarios_disponiveis,
)

SELECT_RELATED = ("cliente", "profissional__usuario", "servico")


def _intervalo_do_dia(data):
    inicio = timezone.make_aware(
        datetime.combine(data, time.min),
        timezone.get_current_timezone(),
    )
    return inicio, inicio + timedelta(days=1)


def _data_ou_hoje(valor):
    if not valor:
        return timezone.localdate()
    data = parse_date(valor)
    if data is None:
        raise ValidationError(
            {"date": "Data inválida. Use o formato AAAA-MM-DD."}
        )
    return data


def _profissional_do_usuario(usuario):
    try:
        return usuario.profissional
    except Profissional.DoesNotExist:
        return None


def _id_valido(valor, campo):
    if valor in (None, ""):
        return None
    if not str(valor).isdigit():
        raise ValidationError({campo: "Informe um ID numérico válido."})
    return int(valor)


def _aplicar_filtros(qs, request):
    status_param = request.query_params.get("status")
    if status_param:
        if status_param not in Agendamento.Status.values:
            raise ValidationError({"status": "Status inválido."})
        qs = qs.filter(status=status_param)

    de = request.query_params.get("from")
    if de:
        data = parse_date(de)
        if data is None:
            raise ValidationError(
                {"from": "Data inválida. Use o formato AAAA-MM-DD."}
            )
        qs = qs.filter(data_hora__gte=_intervalo_do_dia(data)[0])

    ate = request.query_params.get("to")
    if ate:
        data = parse_date(ate)
        if data is None:
            raise ValidationError(
                {"to": "Data inválida. Use o formato AAAA-MM-DD."}
            )
        qs = qs.filter(data_hora__lt=_intervalo_do_dia(data)[1])

    return qs


def _agenda_queryset(usuario):
    qs = Agendamento.objects.select_related(*SELECT_RELATED)
    if usuario.is_barbeiro:
        profissional = _profissional_do_usuario(usuario)
        if profissional is None:
            raise PermissionDenied(
                "Usuário barbeiro sem perfil profissional cadastrado."
            )
        return qs.filter(profissional=profissional)
    if usuario.is_administrador:
        return qs
    raise PermissionDenied("Acesso restrito a barbeiros e administradores.")


class ProfissionalDisponibilidadeView(APIView):
    """Horários livres do profissional por data ou por período."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        profissional = get_object_or_404(
            Profissional.objects.filter(
                ativo=True,
                usuario__is_active=True,
            ),
            pk=pk,
        )

        if request.query_params.get("date"):
            data = _data_ou_hoje(request.query_params.get("date"))
            duracao = INTERVALO_SLOT_MINUTOS
            servico_id = _id_valido(
                request.query_params.get("service"),
                "service",
            )
            if servico_id:
                servico = Servico.objects.filter(
                    pk=servico_id,
                    ativo=True,
                ).first()
                if servico is None:
                    raise ValidationError(
                        {"service": "Serviço não encontrado."}
                    )
                duracao = servico.duracao_minutos
            slots = horarios_disponiveis(profissional, data, duracao)
            return Response(
                {
                    "date": data.isoformat(),
                    "duration_minutes": duracao,
                    "slots": [slot.isoformat() for slot in slots],
                }
            )

        de = parse_date(request.query_params.get("from") or "")
        ate = parse_date(request.query_params.get("to") or "")
        if de is None or ate is None:
            raise ValidationError(
                {
                    "from": (
                        "Informe 'date' ou o período com 'from' e 'to' "
                        "(AAAA-MM-DD)."
                    )
                }
            )
        if ate < de:
            raise ValidationError(
                {"to": "A data final deve ser maior ou igual à inicial."}
            )
        if (ate - de).days > 60:
            raise ValidationError(
                {"to": "O período máximo consultado é de 60 dias."}
            )

        dias = []
        atual = de
        while atual <= ate:
            slots = horarios_disponiveis(profissional, atual)
            if slots:
                dias.append(
                    {
                        "date": atual.isoformat(),
                        "slots": [slot.isoformat() for slot in slots],
                    }
                )
            atual += timedelta(days=1)

        return Response(
            {"from": de.isoformat(), "to": ate.isoformat(), "days": dias}
        )


class MeusAgendamentosView(generics.ListCreateAPIView):
    permission_classes = [IsCliente]

    def get_queryset(self):
        return _aplicar_filtros(
            Agendamento.objects.filter(
                cliente=self.request.user
            ).select_related(*SELECT_RELATED),
            self.request,
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AgendamentoCreateSerializer
        return AgendamentoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agendamento = serializer.save()
        return Response(
            AgendamentoSerializer(agendamento).data,
            status=status.HTTP_201_CREATED,
        )


class AgendamentoDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        usuario = self.request.user
        qs = Agendamento.objects.select_related(*SELECT_RELATED)
        if usuario.is_administrador:
            return qs
        if usuario.is_barbeiro:
            profissional = _profissional_do_usuario(usuario)
            if profissional is None:
                return qs.none()
            return qs.filter(profissional=profissional)
        return qs.filter(cliente=usuario)


class CancelarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        agendamento = get_object_or_404(
            Agendamento.objects.select_related(*SELECT_RELATED),
            pk=pk,
        )
        if (
            not request.user.is_administrador
            and agendamento.cliente_id != request.user.id
        ):
            raise PermissionDenied(
                "Você só pode cancelar os próprios agendamentos."
            )
        agendamento = cancelar_agendamento(agendamento, usuario=request.user)
        return Response(AgendamentoSerializer(agendamento).data)


class MinhaAgendaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = _agenda_queryset(request.user)
        data = _data_ou_hoje(request.query_params.get("date"))
        inicio, fim = _intervalo_do_dia(data)
        qs = qs.filter(data_hora__gte=inicio, data_hora__lt=fim)
        return Response(AgendamentoSerializer(qs, many=True).data)


class MinhaAgendaSemanaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = _agenda_queryset(request.user)
        data = _data_ou_hoje(request.query_params.get("date"))
        inicio_semana = data - timedelta(days=data.weekday())
        inicio, _ = _intervalo_do_dia(inicio_semana)
        fim = inicio + timedelta(days=7)
        qs = qs.filter(data_hora__gte=inicio, data_hora__lt=fim)
        return Response(
            {
                "from": inicio_semana.isoformat(),
                "to": (inicio_semana + timedelta(days=6)).isoformat(),
                "appointments": AgendamentoSerializer(qs, many=True).data,
            }
        )


class AtualizarStatusAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        agendamento = get_object_or_404(
            Agendamento.objects.select_related(*SELECT_RELATED),
            pk=pk,
        )
        usuario = request.user
        if usuario.is_barbeiro:
            profissional = _profissional_do_usuario(usuario)
            if (
                profissional is None
                or agendamento.profissional_id != profissional.id
            ):
                raise PermissionDenied(
                    "Você só pode alterar os próprios atendimentos."
                )
        elif not usuario.is_administrador:
            raise PermissionDenied(
                "Acesso restrito a barbeiros e administradores."
            )

        serializer = AgendamentoStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agendamento = atualizar_status(
            agendamento,
            serializer.validated_data["status"],
        )
        return Response(AgendamentoSerializer(agendamento).data)


class HistoricoClienteView(generics.ListAPIView):
    permission_classes = [IsCliente]
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        return _aplicar_filtros(
            Agendamento.objects.filter(
                cliente=self.request.user
            ).select_related(*SELECT_RELATED),
            self.request,
        )


class HistoricoProfissionalView(generics.ListAPIView):
    permission_classes = [IsBarbeiro]
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        profissional = _profissional_do_usuario(self.request.user)
        if profissional is None:
            return Agendamento.objects.none()
        return _aplicar_filtros(
            Agendamento.objects.filter(
                profissional=profissional
            ).select_related(*SELECT_RELATED),
            self.request,
        )


class HistoricoAdminView(generics.ListAPIView):
    permission_classes = [IsAdministrador]
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        return _aplicar_filtros(
            Agendamento.objects.select_related(*SELECT_RELATED),
            self.request,
        )


class AdminAgendamentoListView(generics.ListAPIView):
    permission_classes = [IsAdministrador]
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        qs = Agendamento.objects.select_related(*SELECT_RELATED)
        profissional_id = _id_valido(
            self.request.query_params.get("professional"),
            "professional",
        )
        if profissional_id:
            qs = qs.filter(profissional_id=profissional_id)
        if self.request.query_params.get("date"):
            data = _data_ou_hoje(self.request.query_params.get("date"))
            inicio, fim = _intervalo_do_dia(data)
            qs = qs.filter(data_hora__gte=inicio, data_hora__lt=fim)
        return _aplicar_filtros(qs, self.request)


class AdminDisponibilidadeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdministrador]
    serializer_class = DisponibilidadeSerializer
    queryset = Disponibilidade.objects.select_related(
        "profissional__usuario"
    ).all()

    def get_queryset(self):
        qs = super().get_queryset()
        profissional_id = _id_valido(
            self.request.query_params.get("professional"),
            "professional",
        )
        if profissional_id:
            qs = qs.filter(profissional_id=profissional_id)
        return qs


class AdminDisponibilidadeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdministrador]
    serializer_class = DisponibilidadeSerializer
    queryset = Disponibilidade.objects.select_related(
        "profissional__usuario"
    ).all()
