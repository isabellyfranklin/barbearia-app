from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import (
    ensure_shop_owner,
    get_barbershop_or_404,
    get_current_user,
    require_roles,
)
from app.enums import UserRole
from app.models import Barber, Barbershop, Service, User
from app.schemas import (
    BarberOut,
    BarbershopCreate,
    BarbershopDetailOut,
    BarbershopOut,
    BarbershopUpdate,
    ServiceOut,
)
from app.utils import is_valid_timezone

router = APIRouter(prefix="/barbershops", tags=["Barbearias"])


@router.get("", response_model=list[BarbershopOut], summary="Catalogo de barbearias")
def list_barbershops(
    search: str | None = Query(default=None, max_length=120, description="Busca por nome ou cidade"),
    city: str | None = Query(default=None, max_length=120),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BarbershopOut]:
    query = db.query(Barbershop).filter(Barbershop.active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(Barbershop.name.ilike(term) | Barbershop.city.ilike(term))
    if city:
        query = query.filter(Barbershop.city.ilike(f"%{city.strip()}%"))
    shops = query.order_by(Barbershop.name).offset(skip).limit(limit).all()
    return [BarbershopOut.model_validate(shop) for shop in shops]


@router.get("/mine", response_model=list[BarbershopOut], summary="Minhas barbearias")
def my_barbershops(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BarbershopOut]:
    if current_user.role == UserRole.ADMIN:
        shops = (
            db.query(Barbershop)
            .filter(Barbershop.owner_id == current_user.id)
            .order_by(Barbershop.name)
            .all()
        )
    elif current_user.role == UserRole.BARBER:
        shops = (
            db.query(Barbershop)
            .join(Barber, Barber.barbershop_id == Barbershop.id)
            .filter(Barber.user_id == current_user.id)
            .order_by(Barbershop.name)
            .all()
        )
    else:
        shops = []
    return [BarbershopOut.model_validate(shop) for shop in shops]


@router.get("/{barbershop_id}", response_model=BarbershopDetailOut, summary="Detalhe da barbearia")
def get_barbershop(barbershop_id: int, db: Session = Depends(get_db)) -> BarbershopDetailOut:
    shop = get_barbershop_or_404(db, barbershop_id)
    services = (
        db.query(Service)
        .filter(Service.barbershop_id == shop.id, Service.active.is_(True))
        .order_by(Service.name)
        .all()
    )
    barbers = (
        db.query(Barber)
        .filter(Barber.barbershop_id == shop.id, Barber.active.is_(True))
        .order_by(Barber.id)
        .all()
    )
    base = BarbershopOut.model_validate(shop).model_dump()
    return BarbershopDetailOut(
        **base,
        services=[ServiceOut.model_validate(service) for service in services],
        barbers=[BarberOut.model_validate(barber) for barber in barbers],
    )


@router.post(
    "",
    response_model=BarbershopOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma barbearia (administrador)",
)
def create_barbershop(
    payload: BarbershopCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> BarbershopOut:
    if not is_valid_timezone(payload.timezone):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fuso horario invalido. Exemplo: America/Sao_Paulo.",
        )
    shop = Barbershop(owner_id=current_user.id, **payload.model_dump())
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return BarbershopOut.model_validate(shop)


@router.patch("/{barbershop_id}", response_model=BarbershopOut, summary="Atualiza a barbearia")
def update_barbershop(
    barbershop_id: int,
    payload: BarbershopUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> BarbershopOut:
    shop = get_barbershop_or_404(db, barbershop_id)
    ensure_shop_owner(current_user, shop)
    data = payload.model_dump(exclude_unset=True)
    if "timezone" in data and data["timezone"] and not is_valid_timezone(data["timezone"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fuso horario invalido. Exemplo: America/Sao_Paulo.",
        )
    for field, value in data.items():
        setattr(shop, field, value)
    db.commit()
    db.refresh(shop)
    return BarbershopOut.model_validate(shop)
