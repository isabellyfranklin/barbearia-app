from django.urls import path

from .views import (
    AdminProfissionalDetailView,
    AdminProfissionalListCreateView,
    AdminServicoDetailView,
    AdminServicoListCreateView,
    BarbeariaAdminView,
    BarbeariaView,
    ProfissionalDetailView,
    ProfissionalListView,
    ServicoDetailView,
    ServicoListView,
)

urlpatterns = [
    path("barbershop", BarbeariaView.as_view(), name="barbershop"),
    path("admin/barbershop", BarbeariaAdminView.as_view(), name="admin-barbershop"),
    path("professionals", ProfissionalListView.as_view(), name="professionals"),
    path(
        "professionals/<int:pk>",
        ProfissionalDetailView.as_view(),
        name="professional-detail",
    ),
    path("services", ServicoListView.as_view(), name="services"),
    path("services/<int:pk>", ServicoDetailView.as_view(), name="service-detail"),
    path(
        "admin/professionals",
        AdminProfissionalListCreateView.as_view(),
        name="admin-professionals",
    ),
    path(
        "admin/professionals/<int:pk>",
        AdminProfissionalDetailView.as_view(),
        name="admin-professional-detail",
    ),
    path("admin/services", AdminServicoListCreateView.as_view(), name="admin-services"),
    path(
        "admin/services/<int:pk>",
        AdminServicoDetailView.as_view(),
        name="admin-service-detail",
    ),
]
