from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_barbershop_or_404
from app.models import Service
from app.schemas import AvailabilityOut, BarberAvailabilityOut, SlotOut
from app.services.availability import compute_availability, get_eligible_barbers

router = APIRouter(tags=["Disponibilidade"])


@router.get(
    "/barbershops/{barbershop_id}/availability",
    response_model=AvailabilityOut,
    summary="Horarios disponiveis para um servico em uma data",
)
def get_availability(
    barbershop_id: int,
    service_id: int = Query(..., description="Servico desejado"),
    target_date: date = Query(alias="date", description="Data local no fuso da barbearia (AAAA-MM-DD)"),
    barber_id: int | None = Query(default=None, description="Filtra um barbeiro especifico"),
    db: Session = Depends(get_db),
) -> AvailabilityOut:
    shop = get_barbershop_or_404(db, barbershop_id)
    if not shop.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Barbearia inativa."
        )

    service = db.get(Service, service_id)
    if service is None or service.barbershop_id != shop.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Servico nao encontrado."
        )
    if not service.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Servico inativo.")

    if barber_id is not None:
        eligible = get_eligible_barbers(db, shop.id, service.id, barber_id)
        if not eligible:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Barbeiro nao encontrado ou nao realiza este servico nesta barbearia.",
            )

    availability = compute_availability(
        db,
        barbershop=shop,
        service=service,
        target_date=target_date,
        barber_id=barber_id,
    )

    return AvailabilityOut(
        barbershop_id=shop.id,
        service_id=service.id,
        service_name=service.name,
        duration_minutes=service.duration_minutes,
        date=target_date,
        timezone=shop.timezone,
        barbers=[
            BarberAvailabilityOut(
                barber_id=item.barber_id,
                barber_name=item.barber_name,
                slots=[SlotOut(start=slot.start, end=slot.end) for slot in item.slots],
            )
            for item in availability
        ],
    )
