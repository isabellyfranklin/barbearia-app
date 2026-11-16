"""Cria dados de demonstracao para testar a API rapidamente.

Uso:
    python -m app.seed
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal, create_all
from app.enums import AppointmentStatus, PaymentMethod, PaymentStatus, UserRole
from app.models import (
    Appointment,
    Barber,
    BarberService,
    Barbershop,
    Payment,
    Service,
    User,
    WorkingHour,
)
from app.security import hash_password
from app.utils import get_timezone, local_to_utc_naive, utcnow

DEMO_PASSWORD = "senha123"


def _create_user(
    db: Session, *, name: str, email: str, role: UserRole, phone: str | None = None
) -> User:
    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(DEMO_PASSWORD),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def seed_demo(db: Session) -> dict:
    """Popula o banco com uma barbearia de exemplo. Seguro para chamar mais de uma vez."""
    existing_shop = db.query(Barbershop).filter(Barbershop.name == "Barbearia Estilo").first()
    if existing_shop is not None:
        return {
            "created": False,
            "barbershop_id": existing_shop.id,
            "admin": "carlos@barbearia.com",
            "barber": "joao@barbearia.com",
            "client": "lucas@cliente.com",
            "password": DEMO_PASSWORD,
        }

    owner = _create_user(
        db,
        name="Carlos Felipino da Silva",
        email="carlos@barbearia.com",
        role=UserRole.ADMIN,
        phone="(11) 99999-0001",
    )
    shop = Barbershop(
        owner_id=owner.id,
        name="Barbearia Estilo",
        description="Cortes classicos e modernos, barba e cuidados masculinos.",
        address="Rua das Tesouras, 123",
        city="Sao Paulo",
        phone="(11) 3333-1000",
        timezone="America/Sao_Paulo",
    )
    db.add(shop)
    db.flush()

    services_data = [
        ("Corte de cabelo", "Corte masculino tradicional ou degradê.", "45.00", 45),
        ("Barba", "Modelagem e finalizacao de barba.", "35.00", 30),
        ("Corte + Barba", "Combo completo.", "70.00", 75),
        ("Pezinho", "Acabamento rapido.", "20.00", 15),
        ("Selagem", "Tratamento capilar.", "120.00", 90),
        ("Platinado", "Descoloracao completa.", "200.00", 120),
    ]
    services: dict[str, Service] = {}
    for name, description, price, duration in services_data:
        service = Service(
            barbershop_id=shop.id,
            name=name,
            description=description,
            price=Decimal(price),
            duration_minutes=duration,
        )
        db.add(service)
        services[name] = service
    db.flush()

    barbers_data = [
        ("Joao Vitor Santos", "joao@barbearia.com", "(11) 99999-0002", "Especialista em cortes e barba."),
        ("Rafael Lima", "rafael@barbearia.com", "(11) 99999-0003", "Cortes modernos e platinado."),
    ]
    barbers: list[Barber] = []
    for name, email, phone, bio in barbers_data:
        user = _create_user(db, name=name, email=email, role=UserRole.BARBER, phone=phone)
        barber = Barber(user=user, barbershop_id=shop.id, bio=bio)
        db.add(barber)
        db.flush()
        for service in services.values():
            db.add(BarberService(barber_id=barber.id, service_id=service.id))
        for weekday in range(6):  # segunda a sabado
            db.add(
                WorkingHour(
                    barber_id=barber.id,
                    weekday=weekday,
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    slot_minutes=30,
                )
            )
            db.add(
                WorkingHour(
                    barber_id=barber.id,
                    weekday=weekday,
                    start_time=time(13, 0),
                    end_time=time(19, 0),
                    slot_minutes=30,
                )
            )
        barbers.append(barber)

    client = _create_user(
        db,
        name="Lucas Pereira Ramos",
        email="lucas@cliente.com",
        role=UserRole.CLIENT,
        phone="(11) 98888-0004",
    )

    # Alguns atendimentos concluidos no passado para alimentar os relatorios.
    tz = get_timezone(shop.timezone)
    today = utcnow().astimezone(tz).date()
    past_days = [7, 5, 3, 2]
    for index, days_ago in enumerate(past_days):
        service = services["Corte + Barba" if index % 2 == 0 else "Corte de cabelo"]
        start_local = datetime.combine(today - timedelta(days=days_ago), time(10, 0), tzinfo=tz)
        start_utc = local_to_utc_naive(start_local, tz)
        appointment = Appointment(
            barbershop_id=shop.id,
            barber_id=barbers[index % len(barbers)].id,
            service_id=service.id,
            client_id=client.id,
            start_at=start_utc,
            end_at=start_utc + timedelta(minutes=service.duration_minutes),
            status=AppointmentStatus.COMPLETED,
            price=service.price,
            payment_status=PaymentStatus.PAID,
            payment_method=PaymentMethod.PIX,
        )
        db.add(appointment)
        db.flush()
        db.add(
            Payment(
                appointment_id=appointment.id,
                amount=service.price,
                method=PaymentMethod.PIX,
                status=PaymentStatus.PAID,
                paid_at=start_utc,
            )
        )

    db.commit()
    return {
        "created": True,
        "barbershop_id": shop.id,
        "admin": "carlos@barbearia.com",
        "barber": "joao@barbearia.com",
        "client": "lucas@cliente.com",
        "password": DEMO_PASSWORD,
    }


def main() -> None:
    create_all()
    with SessionLocal() as db:
        result = seed_demo(db)

    print("Seed concluido." if result["created"] else "Dados de demonstracao ja existiam.")
    print(f"  Administrador: {result['admin']} / {result['password']}")
    print(f"  Barbeiro:      {result['barber']} / {result['password']}")
    print(f"  Cliente:       {result['client']} / {result['password']}")
    print(f"  Barbearia ID:  {result['barbershop_id']}")
    print(f"  Documentacao:  http://localhost:8000/docs")


if __name__ == "__main__":
    main()
