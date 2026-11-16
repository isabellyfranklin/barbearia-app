"""Regras de negocio de agendamentos e pagamentos."""

import threading
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import (
    ensure_shop_owner,
    get_barber_or_404,
    get_barbershop_or_404,
    is_shop_owner,
)
from app.enums import AppointmentStatus, PaymentStatus, UserRole
from app.models import Appointment, Barber, BarberService, Barbershop, Payment, Service, User
from app.schemas import AppointmentCreate
from app.services.availability import validate_slot
from app.utils import utcnow_naive

# Serializa a criacao de agendamentos por barbeiro dentro do processo.
# Em producao com varios workers, complemente com lock no banco (ex.: SELECT ... FOR UPDATE).
_locks_guard = threading.Lock()
_barber_locks: dict[int, threading.Lock] = defaultdict(threading.Lock)


def _lock_for(barber_id: int) -> threading.Lock:
    with _locks_guard:
        return _barber_locks[barber_id]


ALLOWED_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.PENDING: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


def _resolve_client(db: Session, actor: User, requested_client_id: int | None) -> User:
    if actor.role == UserRole.CLIENT:
        if requested_client_id is not None and requested_client_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce so pode agendar para a sua propria conta.",
            )
        return actor

    # Administrador agendando em nome de um cliente.
    if requested_client_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe client_id para agendar em nome de um cliente.",
        )
    client = db.get(User, requested_client_id)
    if client is None or client.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado.")
    if not client.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cliente inativo.")
    return client


def _load_booking_resources(
    db: Session, shop_id: int, service_id: int, barber_id: int
) -> tuple[Barbershop, Service, Barber]:
    shop = get_barbershop_or_404(db, shop_id)
    if not shop.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barbearia inativa.")

    service = db.get(Service, service_id)
    if service is None or service.barbershop_id != shop.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servico nao encontrado.")
    if not service.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Servico inativo.")

    barber = get_barber_or_404(db, barber_id)
    if barber.barbershop_id != shop.id or not barber.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Barbeiro indisponivel nesta barbearia.",
        )

    performs_service = (
        db.query(BarberService)
        .filter(
            BarberService.barber_id == barber.id,
            BarberService.service_id == service.id,
        )
        .first()
    )
    if performs_service is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O barbeiro selecionado nao realiza este servico.",
        )

    return shop, service, barber


def create_appointment(db: Session, actor: User, payload: AppointmentCreate) -> Appointment:
    if actor.role not in (UserRole.CLIENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas clientes e administradores podem criar agendamentos.",
        )

    shop, service, barber = _load_booking_resources(
        db, payload.barbershop_id, payload.service_id, payload.barber_id
    )
    if actor.role == UserRole.ADMIN:
        ensure_shop_owner(actor, shop)
    client = _resolve_client(db, actor, payload.client_id)

    with _lock_for(barber.id):
        try:
            start_utc, end_utc = validate_slot(
                db,
                barbershop=shop,
                service=service,
                barber=barber,
                start_at=payload.start_at,
            )
        except ValueError as exc:
            message = str(exc)
            code = (
                status.HTTP_409_CONFLICT
                if "ocupado" in message or "bloqueio" in message
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            )
            raise HTTPException(status_code=code, detail=message) from exc

        appointment = Appointment(
            barbershop_id=shop.id,
            barber_id=barber.id,
            service_id=service.id,
            client_id=client.id,
            start_at=start_utc,
            end_at=end_utc,
            status=AppointmentStatus.PENDING,
            price=service.price,
            payment_status=PaymentStatus.PENDING,
            notes=payload.notes,
        )
        try:
            db.add(appointment)
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este horario ja esta ocupado para o barbeiro.",
            ) from exc
        db.commit()

    db.refresh(appointment)
    return appointment


def get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento nao encontrado."
        )
    return appointment


def can_view_appointment(db: Session, user: User, appointment: Appointment) -> bool:
    if user.role == UserRole.CLIENT:
        return appointment.client_id == user.id
    if user.role == UserRole.BARBER:
        return appointment.barber.user_id == user.id
    shop = db.get(Barbershop, appointment.barbershop_id)
    return shop is not None and is_shop_owner(user, shop)


def get_visible_appointment(db: Session, user: User, appointment_id: int) -> Appointment:
    appointment = get_appointment_or_404(db, appointment_id)
    if not can_view_appointment(db, user, appointment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem acesso a este agendamento.",
        )
    return appointment


def _refund_payments(db: Session, appointment: Appointment) -> None:
    for payment in appointment.payments:
        if payment.status == PaymentStatus.PAID:
            payment.status = PaymentStatus.REFUNDED
    if appointment.payment_status == PaymentStatus.PAID:
        appointment.payment_status = PaymentStatus.REFUNDED


def cancel_appointment(db: Session, actor: User, appointment: Appointment) -> Appointment:
    if appointment.status == AppointmentStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Agendamento ja esta cancelado."
        )
    if appointment.status in (AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel cancelar um agendamento ja finalizado.",
        )
    if actor.role == UserRole.CLIENT and appointment.client_id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem acesso a este agendamento.",
        )

    appointment.status = AppointmentStatus.CANCELED
    appointment.canceled_at = utcnow_naive()
    _refund_payments(db, appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def change_status(
    db: Session, actor: User, appointment: Appointment, new_status: AppointmentStatus
) -> Appointment:
    if new_status == AppointmentStatus.CANCELED:
        return cancel_appointment(db, actor, appointment)

    if actor.role == UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clientes podem apenas cancelar o proprio agendamento.",
        )
    if actor.role == UserRole.BARBER and appointment.barber.user_id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce so pode alterar os seus proprios atendimentos.",
        )

    if new_status == appointment.status:
        return appointment
    if new_status not in ALLOWED_TRANSITIONS[appointment.status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Transicao invalida: {appointment.status.value} -> {new_status.value}."
            ),
        )

    appointment.status = new_status
    db.commit()
    db.refresh(appointment)
    return appointment


def pay_appointment(
    db: Session, actor: User, appointment: Appointment, method
) -> tuple[Appointment, Payment]:
    if appointment.status == AppointmentStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel pagar um agendamento cancelado.",
        )
    if appointment.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Agendamento ja foi pago."
        )
    if actor.role == UserRole.BARBER and appointment.barber.user_id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem acesso a este agendamento.",
        )

    now = utcnow_naive()
    payment = Payment(
        appointment_id=appointment.id,
        amount=appointment.price,
        method=method,
        status=PaymentStatus.PAID,
        paid_at=now,
    )
    db.add(payment)
    appointment.payment_status = PaymentStatus.PAID
    appointment.payment_method = method
    if appointment.status == AppointmentStatus.PENDING:
        appointment.status = AppointmentStatus.CONFIRMED
    db.commit()
    db.refresh(payment)
    db.refresh(appointment)
    return appointment, payment


def next_appointments_query(db: Session, user: User):
    """Query base com o escopo de visibilidade do usuario."""
    query = db.query(Appointment)
    if user.role == UserRole.CLIENT:
        query = query.filter(Appointment.client_id == user.id)
    elif user.role == UserRole.BARBER:
        query = query.join(Barber, Barber.id == Appointment.barber_id).filter(
            Barber.user_id == user.id
        )
    else:
        query = query.join(Barbershop, Barbershop.id == Appointment.barbershop_id).filter(
            Barbershop.owner_id == user.id
        )
    return query
