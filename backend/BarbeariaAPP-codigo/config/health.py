from django.db import connection
from django.db.utils import DatabaseError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        auth=[],
        responses={200: inline_serializer("Health", {
            "status": serializers.CharField(),
            "database": serializers.CharField(),
        }), 503: inline_serializer("HealthUnavailable", {
            "status": serializers.CharField(),
            "database": serializers.CharField(),
        })},
        description="Prontidão da API e da conexão com o banco. Não retorna credenciais.",
    )
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            return Response({"status": "unavailable", "database": "unavailable"}, status=503)
        return Response({"status": "ok", "database": "ok"})
