from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.enums import AppointmentStatus, UserRole
from app.models import Appointment, User
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentStatusUpdate,
    PaymentCreate,
    PaymentOut,
    PaymentResultOut,
)
from app.services.appointments import (
    cancel_appointment,
    change_status,
    create_appointment,
    get_visible_appointment,
    next_appointments_query,
    pay_appointment,
)
from app.utils import to_utc_naive, utcnow_naive

router = APIRouter(prefix="/appointments", tags=["Agendamentos"])

FINISHED_STATUSES = (
    AppointmentStatus.COMPLETED,
    AppointmentStatus.CANCELED,
    AppointmentStatus.NO_SHOW,
)


def _apply_common_filters(
    query,
    *,
    user: User,
    barbershop_id: int | None,
    barber_id: int | None,
    client_id: int | None,
    start_from: datetime | None,
    start_to: datetime | None,
):
    if barbershop_id is not None:
        query = query.filter(Appointment.barbershop_id == barbershop_id)
    if barber_id is not None:
        query = query.filter(Appointment.barber_id == barber_id)
    if client_id is not None:
        if user.role != UserRole.ADMIN and client_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce so pode consultar os seus proprios agendamentos.",
            )
        query = query.filter(Appointment.client_id == client_id)
    if start_from is not None:
        query = query.filter(Appointment.start_at >= to_utc_naive(start_from))
    if start_to is not None:
        query = query.filter(Appointment.start_at <= to_utc_naive(start_to))
    return query


@router.post(
    "",
    response_model=AppointmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um agendamento",
)
def book_appointment(
    payload: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentOut:
    appointment = create_appointment(db, current_user, payload)
    return AppointmentOut.model_validate(appointment)


@router.get("", response_model=list[AppointmentOut], summary="Lista agendamentos")
def list_appointments(
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    barbershop_id: int | None = None,
    barber_id: int | None = None,
    client_id: int | None = None,
    start_from: datetime | None = Query(default=None, description="Data/hora inicial (ISO 8601)"),
    start_to: datetime | None = Query(default=None, description="Data/hora final (ISO 8601)"),
    only_upcoming: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AppointmentOut]:
    query = next_appointments_query(db, current_user)
    query = _apply_common_filters(
        query,
        user=current_user,
        barbershop_id=barbershop_id,
        barber_id=barber_id,
        client_id=client_id,
        start_from=start_from,
        start_to=start_to,
    )
    if status_filter is not None:
        query = query.filter(Appointment.status == status_filter)
    if only_upcoming:
        query = query.filter(Appointment.start_at >= utcnow_naive()).order_by(
            Appointment.start_at.asc()
        )
    else:
        query = query.order_by(Appointment.start_at.desc())

    appointments = query.offset(skip).limit(limit).all()
    return [AppointmentOut.model_validate(appointment) for appointment in appointments]


@router.get(
    "/history",
    response_model=list[AppointmentOut],
    summary="Historico de atendimentos",
)
def appointment_history(
    barbershop_id: int | None = None,
    barber_id: int | None = None,
    client_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AppointmentOut]:
    query = next_appointments_query(db, current_user).filter(
        Appointment.status.in_(FINISHED_STATUSES)
    )
    query = _apply_common_filters(
        query,
        user=current_user,
        barbershop_id=barbershop_id,
        barber_id=barber_id,
        client_id=client_id,
        start_from=start_from,
        start_to=start_to,
    )
    appointments = (
        query.order_by(Appointment.start_at.desc()).offset(skip).limit(limit).all()
    )
    return [AppointmentOut.model_validate(appointment) for appointment in appointments]


@router.get("/{appointment_id}", response_model=AppointmentOut, summary="Detalhe do agendamento")
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentOut:
    appointment = get_visible_appointment(db, current_user, appointment_id)
    return AppointmentOut.model_validate(appointment)


@router.patch(
    "/{appointment_id}/status",
    response_model=AppointmentOut,
    summary="Altera o status (barbeiro ou administrador)",
)
def update_appointment_status(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentOut:
    appointment = get_visible_appointment(db, current_user, appointment_id)
    appointment = change_status(db, current_user, appointment, payload.status)
    return AppointmentOut.model_validate(appointment)


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentOut,
    summary="Cancela o agendamento",
)
def cancel(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentOut:
    appointment = get_visible_appointment(db, current_user, appointment_id)
    appointment = cancel_appointment(db, current_user, appointment)
    return AppointmentOut.model_validate(appointment)


@router.post(
    "/{appointment_id}/payment",
    response_model=PaymentResultOut,
    summary="Registra o pagamento do agendamento",
)
def pay(
    appointment_id: int,
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResultOut:
    appointment = get_visible_appointment(db, current_user, appointment_id)
    appointment, payment = pay_appointment(db, current_user, appointment, payload.method)
    return PaymentResultOut(
        appointment=AppointmentOut.model_validate(appointment),
        payment=PaymentOut.model_validate(payment),
    )
