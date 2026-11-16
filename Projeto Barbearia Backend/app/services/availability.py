"""Calculo de horarios disponiveis para agendamento."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.enums import AppointmentStatus
from app.models import Appointment, Barber, BarberService, Barbershop, Service, TimeOff, WorkingHour
from app.utils import (
    combine_local,
    day_bounds_utc,
    get_timezone,
    local_to_utc_naive,
    utc_naive_to_local,
    utcnow_naive,
)

BLOCKING_STATUSES = (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)


@dataclass(frozen=True)
class Slot:
    start: datetime  # UTC naive
    end: datetime  # UTC naive


@dataclass
class BarberSlots:
    barber_id: int
    barber_name: str
    slots: list[Slot]


def get_eligible_barbers(
    db: Session, barbershop_id: int, service_id: int, barber_id: int | None = None
) -> list[Barber]:
    query = (
        db.query(Barber)
        .join(BarberService, BarberService.barber_id == Barber.id)
        .filter(
            Barber.barbershop_id == barbershop_id,
            Barber.active.is_(True),
            BarberService.service_id == service_id,
        )
    )
    if barber_id is not None:
        query = query.filter(Barber.id == barber_id)
    return query.order_by(Barber.id).all()


def _overlaps(start: datetime, end: datetime, other_start: datetime, other_end: datetime) -> bool:
    return start < other_end and end > other_start


def compute_availability(
    db: Session,
    *,
    barbershop: Barbershop,
    service: Service,
    target_date: date,
    barber_id: int | None = None,
    now: datetime | None = None,
) -> list[BarberSlots]:
    """Gera os horarios livres (em UTC) de cada barbeiro apto para o servico."""
    tz = get_timezone(barbershop.timezone)
    weekday = target_date.weekday()
    day_start, day_end = day_bounds_utc(target_date, tz)

    barbers = get_eligible_barbers(db, barbershop.id, service.id, barber_id)
    if not barbers:
        return []

    barber_ids = [barber.id for barber in barbers]
    duration = timedelta(minutes=service.duration_minutes)

    hours_by_barber: dict[int, list[WorkingHour]] = {bid: [] for bid in barber_ids}
    hours = (
        db.query(WorkingHour)
        .filter(WorkingHour.barber_id.in_(barber_ids), WorkingHour.weekday == weekday)
        .all()
    )
    for item in hours:
        hours_by_barber[item.barber_id].append(item)

    blocks_by_barber: dict[int, list[TimeOff]] = {bid: [] for bid in barber_ids}
    blocks = (
        db.query(TimeOff)
        .filter(
            TimeOff.barber_id.in_(barber_ids),
            TimeOff.starts_at < day_end,
            TimeOff.ends_at > day_start,
        )
        .all()
    )
    for block in blocks:
        blocks_by_barber[block.barber_id].append(block)

    appointments_by_barber: dict[int, list[Appointment]] = {bid: [] for bid in barber_ids}
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.barber_id.in_(barber_ids),
            Appointment.status.in_(BLOCKING_STATUSES),
            Appointment.start_at < day_end,
            Appointment.end_at > day_start,
        )
        .all()
    )
    for appointment in appointments:
        appointments_by_barber[appointment.barber_id].append(appointment)

    current = now or utcnow_naive()
    earliest = current + timedelta(minutes=settings.min_lead_minutes)

    result: list[BarberSlots] = []
    for barber in barbers:
        slots: dict[datetime, Slot] = {}
        for working_hour in hours_by_barber[barber.id]:
            block_start = combine_local(target_date, working_hour.start_time, tz)
            block_end = combine_local(target_date, working_hour.end_time, tz)
            step = timedelta(minutes=working_hour.slot_minutes)
            cursor = block_start

            while cursor + duration <= block_end:
                slot_start = local_to_utc_naive(cursor, tz)
                slot_end = local_to_utc_naive(cursor + duration, tz)

                if slot_start >= earliest and not any(
                    _overlaps(slot_start, slot_end, appt.start_at, appt.end_at)
                    for appt in appointments_by_barber[barber.id]
                ) and not any(
                    _overlaps(slot_start, slot_end, block.starts_at, block.ends_at)
                    for block in blocks_by_barber[barber.id]
                ):
                    slots[slot_start] = Slot(start=slot_start, end=slot_end)
                cursor += step

        result.append(
            BarberSlots(
                barber_id=barber.id,
                barber_name=barber.name,
                slots=sorted(slots.values(), key=lambda slot: slot.start),
            )
        )
    return result


def validate_slot(
    db: Session,
    *,
    barbershop: Barbershop,
    service: Service,
    barber: Barber,
    start_at: datetime,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Valida as regras de negocio de um horario e devolve (inicio, fim) em UTC naive.

    Levanta `ValueError` com uma mensagem amigavel quando o horario nao pode ser usado.
    """
    tz = get_timezone(barbershop.timezone)
    if start_at.tzinfo is None:
        start_utc = local_to_utc_naive(start_at, tz)
    else:
        start_utc = start_at.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)
    end_utc = start_utc + timedelta(minutes=service.duration_minutes)

    current = now or utcnow_naive()
    earliest = current + timedelta(minutes=settings.min_lead_minutes)
    if start_utc < earliest:
        raise ValueError(
            f"O agendamento precisa ser feito com pelo menos {settings.min_lead_minutes} "
            "minutos de antecedencia."
        )

    local_start = utc_naive_to_local(start_utc, tz)
    local_end = utc_naive_to_local(end_utc, tz)
    if local_start.date() != local_end.date():
        raise ValueError("O servico nao pode terminar em outro dia.")

    hours = (
        db.query(WorkingHour)
        .filter(
            WorkingHour.barber_id == barber.id,
            WorkingHour.weekday == local_start.weekday(),
        )
        .all()
    )
    if not hours:
        raise ValueError("O barbeiro nao atende neste dia.")

    inside_hours = any(
        local_start.time() >= item.start_time and local_end.time() <= item.end_time
        for item in hours
    )
    if not inside_hours:
        raise ValueError("O horario escolhido esta fora do expediente do barbeiro.")

    block = (
        db.query(TimeOff)
        .filter(
            TimeOff.barber_id == barber.id,
            TimeOff.starts_at < end_utc,
            TimeOff.ends_at > start_utc,
        )
        .first()
    )
    if block is not None:
        raise ValueError("O barbeiro tem um bloqueio de agenda neste horario.")

    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.barber_id == barber.id,
            Appointment.status.in_(BLOCKING_STATUSES),
            Appointment.start_at < end_utc,
            Appointment.end_at > start_utc,
        )
        .first()
    )
    if conflict is not None:
        raise ValueError("Este horario ja esta ocupado para o barbeiro.")

    return start_utc, end_utc
