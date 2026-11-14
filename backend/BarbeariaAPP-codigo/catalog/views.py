from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdministrador

from .models import Barbearia, Profissional, Servico
from .serializers import (
    AdminProfissionalCreateSerializer,
    AdminProfissionalSerializer,
    BarbeariaSerializer,
    ProfissionalSerializer,
    ServicoSerializer,
)


class BarbeariaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        barbearia = Barbearia.load()
        return Response(BarbeariaSerializer(barbearia).data)


class BarbeariaAdminView(APIView):
    permission_classes = [IsAdministrador]

    def patch(self, request):
        barbearia = Barbearia.load()
        serializer = BarbeariaSerializer(
            barbearia,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProfissionalListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProfissionalSerializer

    def get_queryset(self):
        return Profissional.objects.filter(
            ativo=True, usuario__is_active=True
        ).select_related("usuario")


class ProfissionalDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProfissionalSerializer

    def get_queryset(self):
        return Profissional.objects.filter(
            ativo=True, usuario__is_active=True
        ).select_related("usuario")


class ServicoListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ServicoSerializer
    queryset = Servico.objects.filter(ativo=True)


class ServicoDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ServicoSerializer
    queryset = Servico.objects.filter(ativo=True)


class AdminProfissionalListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdministrador]
    queryset = Profissional.objects.select_related("usuario").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminProfissionalCreateSerializer
        return AdminProfissionalSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profissional = serializer.save()
        return Response(
            AdminProfissionalSerializer(profissional).data,
            status=status.HTTP_201_CREATED,
        )


class AdminProfissionalDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdministrador]
    queryset = Profissional.objects.select_related("usuario").all()
    serializer_class = AdminProfissionalSerializer

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save(update_fields=["ativo"])
        instance.usuario.is_active = False
        instance.usuario.save(update_fields=["is_active"])


class AdminServicoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdministrador]
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer


class AdminServicoDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdministrador]
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save(update_fields=["ativo"])
