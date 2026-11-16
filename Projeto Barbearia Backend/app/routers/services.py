from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import (
    ensure_shop_owner,
    get_barbershop_or_404,
    require_roles,
)
from app.enums import UserRole
from app.models import Service, User
from app.schemas import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(tags=["Servicos"])


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _get_service_or_404(db: Session, service_id: int) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servico nao encontrado.")
    return service


@router.get(
    "/barbershops/{barbershop_id}/services",
    response_model=list[ServiceOut],
    summary="Servicos oferecidos pela barbearia",
)
def list_services(
    barbershop_id: int,
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[ServiceOut]:
    get_barbershop_or_404(db, barbershop_id)
    query = db.query(Service).filter(Service.barbershop_id == barbershop_id)
    if not include_inactive:
        query = query.filter(Service.active.is_(True))
    services = query.order_by(Service.name).all()
    return [ServiceOut.model_validate(service) for service in services]


@router.post(
    "/barbershops/{barbershop_id}/services",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um servico",
)
def create_service(
    barbershop_id: int,
    payload: ServiceCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ServiceOut:
    shop = get_barbershop_or_404(db, barbershop_id)
    ensure_shop_owner(current_user, shop)
    service = Service(
        barbershop_id=shop.id,
        name=payload.name.strip(),
        description=payload.description,
        price=_money(payload.price),
        duration_minutes=payload.duration_minutes,
        active=payload.active,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return ServiceOut.model_validate(service)


@router.get("/services/{service_id}", response_model=ServiceOut, summary="Detalhe do servico")
def get_service(service_id: int, db: Session = Depends(get_db)) -> ServiceOut:
    return ServiceOut.model_validate(_get_service_or_404(db, service_id))


@router.patch("/services/{service_id}", response_model=ServiceOut, summary="Atualiza o servico")
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ServiceOut:
    service = _get_service_or_404(db, service_id)
    shop = get_barbershop_or_404(db, service.barbershop_id)
    ensure_shop_owner(current_user, shop)

    data = payload.model_dump(exclude_unset=True)
    if "price" in data and data["price"] is not None:
        data["price"] = _money(data["price"])
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for field, value in data.items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return ServiceOut.model_validate(service)


@router.delete(
    "/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativa o servico (soft delete)",
)
def delete_service(
    service_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    service = _get_service_or_404(db, service_id)
    shop = get_barbershop_or_404(db, service.barbershop_id)
    ensure_shop_owner(current_user, shop)
    service.active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
