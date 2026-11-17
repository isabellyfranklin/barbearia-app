from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import AppointmentStatus, PaymentMethod, PaymentStatus, UserRole
from app.utils import utcnow_naive


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=20), default=UserRole.CLIENT, index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    owned_barbershops: Mapped[list["Barbershop"]] = relationship(back_populates="owner")


class Barbershop(Base):
    __tablename__ = "barbershops"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    owner: Mapped[User] = relationship(back_populates="owned_barbershops")
    services: Mapped[list["Service"]] = relationship(back_populates="barbershop")
    barbers: Mapped[list["Barber"]] = relationship(back_populates="barbershop")


class Barber(Base):
    __tablename__ = "barbers"
    __table_args__ = (UniqueConstraint("user_id", "barbershop_id", name="uq_barber_user_shop"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    barbershop_id: Mapped[int] = mapped_column(
        ForeignKey("barbershops.id", ondelete="CASCADE"), index=True
    )
    bio: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    user: Mapped[User] = relationship(lazy="joined")
    barbershop: Mapped[Barbershop] = relationship(back_populates="barbers")
    services: Mapped[list["BarberService"]] = relationship(
        back_populates="barber", cascade="all, delete-orphan", lazy="selectin"
    )
    working_hours: Mapped[list["WorkingHour"]] = relationship(
        back_populates="barber", cascade="all, delete-orphan"
    )
    time_off: Mapped[list["TimeOff"]] = relationship(
        back_populates="barber", cascade="all, delete-orphan"
    )

    # Atalhos usados na serializacao das respostas.
    @property
    def name(self) -> str:
        return self.user.name

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def phone(self) -> str | None:
        return self.user.phone

    @property
    def service_ids(self) -> list[int]:
        return sorted(link.service_id for link in self.services)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    barbershop_id: Mapped[int] = mapped_column(
        ForeignKey("barbershops.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    barbershop: Mapped[Barbershop] = relationship(back_populates="services")
    barbers: Mapped[list["BarberService"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )


class BarberService(Base):
    """Quais servicos cada barbeiro executa."""

    __tablename__ = "barber_services"

    barber_id: Mapped[int] = mapped_column(
        ForeignKey("barbers.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )

    barber: Mapped[Barber] = relationship(back_populates="services")
    service: Mapped[Service] = relationship(back_populates="barbers")


class WorkingHour(Base):
    """Faixa de atendimento do barbeiro. weekday: 0 = segunda-feira ... 6 = domingo."""

    __tablename__ = "working_hours"
    __table_args__ = (Index("ix_working_hours_barber_weekday", "barber_id", "weekday"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)

    barber: Mapped[Barber] = relationship(back_populates="working_hours")


class TimeOff(Base):
    """Bloqueio pontual da agenda (folga, feriado, compromisso)."""

    __tablename__ = "time_off"
    __table_args__ = (Index("ix_time_off_barber_period", "barber_id", "starts_at", "ends_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id", ondelete="CASCADE"))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    barber: Mapped[Barber] = relationship(back_populates="time_off")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("barber_id", "start_at", name="uq_appointment_barber_start"),
        Index("ix_appointments_barber_start", "barber_id", "start_at"),
        Index("ix_appointments_client_start", "client_id", "start_at"),
        Index("ix_appointments_shop_start", "barbershop_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    barbershop_id: Mapped[int] = mapped_column(
        ForeignKey("barbershops.id", ondelete="RESTRICT")
    )
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id", ondelete="RESTRICT"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"))
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)

    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus, native_enum=False, length=20),
        default=AppointmentStatus.PENDING,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False, length=20), default=PaymentStatus.PENDING
    )
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(PaymentMethod, native_enum=False, length=20)
    )
    notes: Mapped[str | None] = mapped_column(Text)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow_naive, onupdate=utcnow_naive
    )

    barbershop: Mapped[Barbershop] = relationship(lazy="joined")
    barber: Mapped[Barber] = relationship(lazy="joined")
    service: Mapped[Service] = relationship(lazy="joined")
    client: Mapped[User] = relationship(lazy="joined")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan"
    )

    # Atalhos usados na serializacao das respostas.
    @property
    def barbershop_name(self) -> str:
        return self.barbershop.name

    @property
    def barber_name(self) -> str:
        return self.barber.name

    @property
    def client_name(self) -> str:
        return self.client.name

    @property
    def service_name(self) -> str:
        return self.service.name

    @property
    def duration_minutes(self) -> int:
        return int((self.end_at - self.start_at).total_seconds() // 60)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, native_enum=False, length=20)
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False, length=20), default=PaymentStatus.PAID
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    appointment: Mapped[Appointment] = relationship(back_populates="payments")
