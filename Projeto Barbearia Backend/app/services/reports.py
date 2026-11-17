"""Agregacoes para os relatorios gerenciais."""

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.enums import AppointmentStatus, PaymentStatus
from app.models import Appointment, Barbershop
from app.schemas import (
    BarberPerformanceOut,
    DailyRevenueOut,
    ReportSummaryOut,
    ServiceRevenueOut,
    StatusCountOut,
)
from app.utils import day_bounds_utc, get_timezone, utc_naive_to_local


def build_summary(
    db: Session, barbershop: Barbershop, start_date: date, end_date: date
) -> ReportSummaryOut:
    tz = get_timezone(barbershop.timezone)
    start_utc, _ = day_bounds_utc(start_date, tz)
    _, end_utc = day_bounds_utc(end_date, tz)

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.barbershop_id == barbershop.id,
            Appointment.start_at >= start_utc,
            Appointment.start_at < end_utc,
        )
        .all()
    )

    status_counter = Counter(appointment.status for appointment in appointments)
    by_status = [
        StatusCountOut(status=status, count=status_counter.get(status, 0))
        for status in AppointmentStatus
    ]

    billable = [
        appointment
        for appointment in appointments
        if appointment.status != AppointmentStatus.CANCELED
    ]
    paid = [
        appointment for appointment in billable if appointment.payment_status == PaymentStatus.PAID
    ]
    paid_revenue = sum((appointment.price for appointment in paid), Decimal("0"))
    pending_revenue = sum(
        (
            appointment.price
            for appointment in billable
            if appointment.payment_status == PaymentStatus.PENDING
            and appointment.status in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)
        ),
        Decimal("0"),
    )
    average_ticket = paid_revenue / len(paid) if paid else Decimal("0")

    service_stats: dict[int, dict] = defaultdict(
        lambda: {"name": "", "appointments": 0, "revenue": Decimal("0")}
    )
    for appointment in billable:
        stats = service_stats[appointment.service_id]
        stats["name"] = appointment.service_name
        stats["appointments"] += 1
        if appointment.payment_status == PaymentStatus.PAID:
            stats["revenue"] += appointment.price
    top_services = sorted(
        (
            ServiceRevenueOut(
                service_id=service_id,
                service_name=stats["name"],
                appointments=stats["appointments"],
                revenue=float(stats["revenue"]),
            )
            for service_id, stats in service_stats.items()
        ),
        key=lambda item: (-item.appointments, -item.revenue, item.service_name),
    )[:5]

    barber_stats: dict[int, dict] = defaultdict(
        lambda: {
            "name": "",
            "appointments": 0,
            "completed": 0,
            "revenue": Decimal("0"),
        }
    )
    for appointment in billable:
        stats = barber_stats[appointment.barber_id]
        stats["name"] = appointment.barber_name
        stats["appointments"] += 1
        if appointment.status == AppointmentStatus.COMPLETED:
            stats["completed"] += 1
        if appointment.payment_status == PaymentStatus.PAID:
            stats["revenue"] += appointment.price
    barbers = sorted(
        (
            BarberPerformanceOut(
                barber_id=barber_id,
                barber_name=stats["name"],
                appointments=stats["appointments"],
                completed=stats["completed"],
                revenue=float(stats["revenue"]),
            )
            for barber_id, stats in barber_stats.items()
        ),
        key=lambda item: (-item.revenue, item.barber_name),
    )

    daily_stats: dict[date, dict] = defaultdict(lambda: {"appointments": 0, "revenue": Decimal("0")})
    for appointment in appointments:
        local_day = utc_naive_to_local(appointment.start_at, tz).date()
        daily_stats[local_day]["appointments"] += 1
        if (
            appointment.status != AppointmentStatus.CANCELED
            and appointment.payment_status == PaymentStatus.PAID
        ):
            daily_stats[local_day]["revenue"] += appointment.price
    daily = [
        DailyRevenueOut(
            date=local_day,
            appointments=stats["appointments"],
            revenue=float(stats["revenue"]),
        )
        for local_day, stats in sorted(daily_stats.items())
    ]

    return ReportSummaryOut(
        barbershop_id=barbershop.id,
        period_start=start_date,
        period_end=end_date,
        timezone=barbershop.timezone,
        total_appointments=len(appointments),
        completed_appointments=status_counter.get(AppointmentStatus.COMPLETED, 0),
        canceled_appointments=status_counter.get(AppointmentStatus.CANCELED, 0),
        no_show_appointments=status_counter.get(AppointmentStatus.NO_SHOW, 0),
        paid_revenue=float(paid_revenue),
        pending_revenue=float(pending_revenue),
        average_ticket=float(average_ticket),
        by_status=by_status,
        top_services=top_services,
        barbers=barbers,
        daily=daily,
    )


def default_period(today: date, days: int = 30) -> tuple[date, date]:
    return today - timedelta(days=days - 1), today
