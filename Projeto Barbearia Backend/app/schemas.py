from datetime import date, datetime, time
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    model_validator,
)

from app.enums import AppointmentStatus, PaymentMethod, PaymentStatus, UserRole
from app.utils import iso_z

# Datetimes de saida sempre em ISO 8601 com fuso (UTC, sufixo "Z").
AwareDatetime = Annotated[
    datetime,
    PlainSerializer(lambda value: iso_z(value), return_type=str, when_used="json"),
]


# ---------------------------------------------------------------------------
# Autenticacao e usuarios
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = Field(default=None, max_length=20)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    active: bool
    created_at: AwareDatetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Barbearias
# ---------------------------------------------------------------------------


class BarbershopCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    timezone: str = Field(default="America/Sao_Paulo", max_length=64)


class BarbershopRegister(BarbershopCreate):
    owner_name: str = Field(min_length=2, max_length=120)
    owner_email: EmailStr
    owner_password: str = Field(min_length=6, max_length=128)
    owner_phone: str | None = Field(default=None, max_length=20)


class BarbershopUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=64)
    active: bool | None = None


class BarbershopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None
    address: str | None
    city: str | None
    phone: str | None
    timezone: str
    active: bool
    created_at: AwareDatetime


class BarbershopDetailOut(BarbershopOut):
    services: list["ServiceOut"]
    barbers: list["BarberOut"]


# ---------------------------------------------------------------------------
# Servicos
# ---------------------------------------------------------------------------


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0, le=100000)
    duration_minutes: int = Field(ge=5, le=480)
    active: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0, le=100000)
    duration_minutes: int | None = Field(default=None, ge=5, le=480)
    active: bool | None = None


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    barbershop_id: int
    name: str
    description: str | None
    price: float
    duration_minutes: int
    active: bool


# ---------------------------------------------------------------------------
# Barbeiros, expediente e bloqueios
# ---------------------------------------------------------------------------


class BarberCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = Field(default=None, max_length=20)
    bio: str | None = Field(default=None, max_length=1000)
    service_ids: list[int] = Field(default_factory=list)


class BarberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    bio: str | None = Field(default=None, max_length=1000)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    active: bool | None = None
    service_ids: list[int] | None = None


class BarberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    barbershop_id: int
    name: str
    email: EmailStr
    phone: str | None
    bio: str | None
    active: bool
    service_ids: list[int]


class WorkingHourCreate(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0 = segunda-feira ... 6 = domingo")
    start_time: time
    end_time: time
    slot_minutes: int = Field(default=30, ge=10, le=240)

    @model_validator(mode="after")
    def _validate_period(self) -> "WorkingHourCreate":
        if self.end_time <= self.start_time:
            raise ValueError("O horario final deve ser maior que o inicial.")
        return self


class WorkingHourUpdate(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_minutes: int | None = Field(default=None, ge=10, le=240)


class WorkingHourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    barber_id: int
    weekday: int
    start_time: time
    end_time: time
    slot_minutes: int


class TimeOffCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _validate_period(self) -> "TimeOffCreate":
        if (self.starts_at.tzinfo is None) != (self.ends_at.tzinfo is None):
            raise ValueError("Informe os dois horarios com fuso ou os dois sem fuso.")
        if self.ends_at <= self.starts_at:
            raise ValueError("O fim do bloqueio deve ser maior que o inicio.")
        return self


class TimeOffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    barber_id: int
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    reason: str | None


# ---------------------------------------------------------------------------
# Disponibilidade
# ---------------------------------------------------------------------------


class SlotOut(BaseModel):
    start: AwareDatetime
    end: AwareDatetime


class BarberAvailabilityOut(BaseModel):
    barber_id: int
    barber_name: str
    slots: list[SlotOut]


class AvailabilityOut(BaseModel):
    barbershop_id: int
    service_id: int
    service_name: str
    duration_minutes: int
    date: date
    timezone: str
    barbers: list[BarberAvailabilityOut]


# ---------------------------------------------------------------------------
# Agendamentos e pagamentos
# ---------------------------------------------------------------------------


class AppointmentCreate(BaseModel):
    barbershop_id: int
    service_id: int
    barber_id: int
    start_at: datetime
    notes: str | None = Field(default=None, max_length=500)
    client_id: int | None = Field(
        default=None,
        description="Somente administrador: agenda em nome de outro cliente.",
    )


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class PaymentCreate(BaseModel):
    method: PaymentMethod


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    barbershop_id: int
    barbershop_name: str
    barber_id: int
    barber_name: str
    service_id: int
    service_name: str
    client_id: int
    client_name: str
    start_at: AwareDatetime
    end_at: AwareDatetime
    duration_minutes: int
    status: AppointmentStatus
    price: float
    payment_status: PaymentStatus
    payment_method: PaymentMethod | None
    notes: str | None
    canceled_at: AwareDatetime | None
    created_at: AwareDatetime


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    paid_at: AwareDatetime | None
    created_at: AwareDatetime


class PaymentResultOut(BaseModel):
    appointment: AppointmentOut
    payment: PaymentOut


# ---------------------------------------------------------------------------
# Relatorios
# ---------------------------------------------------------------------------


class StatusCountOut(BaseModel):
    status: AppointmentStatus
    count: int


class ServiceRevenueOut(BaseModel):
    service_id: int
    service_name: str
    appointments: int
    revenue: float


class BarberPerformanceOut(BaseModel):
    barber_id: int
    barber_name: str
    appointments: int
    completed: int
    revenue: float


class DailyRevenueOut(BaseModel):
    date: date
    appointments: int
    revenue: float


class ReportSummaryOut(BaseModel):
    barbershop_id: int
    period_start: date
    period_end: date
    timezone: str
    total_appointments: int
    completed_appointments: int
    canceled_appointments: int
    no_show_appointments: int
    paid_revenue: float
    pending_revenue: float
    average_ticket: float
    by_status: list[StatusCountOut]
    top_services: list[ServiceRevenueOut]
    barbers: list[BarberPerformanceOut]
    daily: list[DailyRevenueOut]


# Resolve as referencias antecipadas (BarbershopDetailOut usa classes definidas depois).
BarbershopDetailOut.model_rebuild()
