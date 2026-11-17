from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import (
    ensure_can_manage_barber,
    ensure_shop_owner,
    get_barber_or_404,
    get_barbershop_or_404,
    get_current_user,
    is_shop_owner,
    require_roles,
)
from app.enums import UserRole
from app.models import (
    Appointment,
    Barber,
    BarberService,
    Barbershop,
    Service,
    TimeOff,
    User,
    WorkingHour,
)
from app.schemas import (
    BarberCreate,
    BarberOut,
    BarberUpdate,
    TimeOffCreate,
    TimeOffOut,
    WorkingHourCreate,
    WorkingHourOut,
    WorkingHourUpdate,
)
from app.security import hash_password
from app.services.availability import BLOCKING_STATUSES
from app.utils import get_timezone, local_to_utc_naive, to_utc_naive

router = APIRouter(tags=["Barbeiros"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_services(db: Session, barbershop_id: int, service_ids: list[int]) -> list[Service]:
    unique_ids = list(dict.fromkeys(service_ids))
    if not unique_ids:
        return []
    services = (
        db.query(Service)
        .filter(Service.id.in_(unique_ids), Service.barbershop_id == barbershop_id)
        .all()
    )
    if len(services) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Um ou mais servicos nao pertencem a esta barbearia.",
        )
    return services


def _get_working_hour_or_404(db: Session, working_hour_id: int) -> WorkingHour:
    item = db.get(WorkingHour, working_hour_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expediente nao encontrado."
        )
    return item


def _get_time_off_or_404(db: Session, time_off_id: int) -> TimeOff:
    item = db.get(TimeOff, time_off_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bloqueio nao encontrado."
        )
    return item


def _set_barber_services(barber: Barber, services: list[Service], db: Session) -> None:
    """Substitui os vinculos do barbeiro evitando conflito de chave primaria no flush."""
    barber.services.clear()
    db.flush()
    barber.services.extend(BarberService(service_id=service.id) for service in services)


def _check_overlap(
    db: Session,
    barber_id: int,
    weekday: int,
    start_time,
    end_time,
    exclude_id: int | None = None,
) -> None:
    query = db.query(WorkingHour).filter(
        WorkingHour.barber_id == barber_id, WorkingHour.weekday == weekday
    )
    if exclude_id is not None:
        query = query.filter(WorkingHour.id != exclude_id)
    for item in query.all():
        if start_time < item.end_time and end_time > item.start_time:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe um expediente que se sobrepoe a este horario.",
            )


def _to_utc(value, shop: Barbershop):
    tz = get_timezone(shop.timezone)
    if value.tzinfo is None:
        return local_to_utc_naive(value, tz)
    return to_utc_naive(value)


# ---------------------------------------------------------------------------
# Barbeiros
# ---------------------------------------------------------------------------


@router.get(
    "/barbershops/{barbershop_id}/barbers",
    response_model=list[BarberOut],
    summary="Barbeiros da barbearia",
)
def list_barbers(
    barbershop_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
) -> list[BarberOut]:
    get_barbershop_or_404(db, barbershop_id)
    query = db.query(Barber).filter(Barber.barbershop_id == barbershop_id)
    if not include_inactive:
        query = query.filter(Barber.active.is_(True))
    return [BarberOut.model_validate(barber) for barber in query.order_by(Barber.id).all()]


@router.post(
    "/barbershops/{barbershop_id}/barbers",
    response_model=BarberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um barbeiro (cria o usuario de acesso)",
)
def create_barber(
    barbershop_id: int,
    payload: BarberCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> BarberOut:
    shop = get_barbershop_or_404(db, barbershop_id)
    ensure_shop_owner(current_user, shop)

    email = str(payload.email).strip().lower()
    if db.query(User).filter(func.lower(User.email) == email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado."
        )

    services = _validate_services(db, shop.id, payload.service_ids)

    user = User(
        name=payload.name.strip(),
        email=email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.BARBER,
    )
    barber = Barber(user=user, barbershop_id=shop.id, bio=payload.bio)
    barber.services = [BarberService(service_id=service.id) for service in services]
    db.add(barber)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao foi possivel cadastrar o barbeiro.",
        ) from exc
    db.refresh(barber)
    return BarberOut.model_validate(barber)


@router.get("/barbers/me", response_model=BarberOut, summary="Meu perfil de barbeiro")
def my_barber_profile(
    current_user: User = Depends(require_roles(UserRole.BARBER)),
    db: Session = Depends(get_db),
) -> BarberOut:
    barber = db.query(Barber).filter(Barber.user_id == current_user.id).first()
    if barber is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de barbeiro nao encontrado."
        )
    return BarberOut.model_validate(barber)


@router.get("/barbers/{barber_id}", response_model=BarberOut, summary="Detalhe do barbeiro")
def get_barber(barber_id: int, db: Session = Depends(get_db)) -> BarberOut:
    return BarberOut.model_validate(get_barber_or_404(db, barber_id))


@router.patch("/barbers/{barber_id}", response_model=BarberOut, summary="Atualiza o barbeiro")
def update_barber(
    barber_id: int,
    payload: BarberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BarberOut:
    barber = get_barber_or_404(db, barber_id)
    ensure_can_manage_barber(db, current_user, barber)
    shop = get_barbershop_or_404(db, barber.barbershop_id)
    is_owner = is_shop_owner(current_user, shop)

    data = payload.model_dump(exclude_unset=True)
    if ("active" in data or "service_ids" in data) and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o proprietario pode alterar status e servicos do barbeiro.",
        )

    if data.get("name") is not None:
        barber.user.name = data["name"].strip()
    if "phone" in data:
        barber.user.phone = data["phone"]
    if "bio" in data:
        barber.bio = data["bio"]
    if data.get("password") is not None:
        barber.user.password_hash = hash_password(data["password"])
    if data.get("active") is not None:
        barber.active = data["active"]
    if data.get("service_ids") is not None:
        services = _validate_services(db, shop.id, data["service_ids"])
        _set_barber_services(barber, services, db)

    db.commit()
    db.refresh(barber)
    return BarberOut.model_validate(barber)


@router.put(
    "/barbers/{barber_id}/services",
    response_model=BarberOut,
    summary="Define os servicos executados pelo barbeiro",
)
def set_barber_services(
    barber_id: int,
    service_ids: list[int],
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> BarberOut:
    barber = get_barber_or_404(db, barber_id)
    shop = get_barbershop_or_404(db, barber.barbershop_id)
    ensure_shop_owner(current_user, shop)
    services = _validate_services(db, shop.id, service_ids)
    _set_barber_services(barber, services, db)
    db.commit()
    db.refresh(barber)
    return BarberOut.model_validate(barber)


# ---------------------------------------------------------------------------
# Expediente (working hours)
# ---------------------------------------------------------------------------


@router.get(
    "/barbers/{barber_id}/working-hours",
    response_model=list[WorkingHourOut],
    summary="Expediente do barbeiro",
)
def list_working_hours(
    barber_id: int, db: Session = Depends(get_db)
) -> list[WorkingHourOut]:
    get_barber_or_404(db, barber_id)
    items = (
        db.query(WorkingHour)
        .filter(WorkingHour.barber_id == barber_id)
        .order_by(WorkingHour.weekday, WorkingHour.start_time)
        .all()
    )
    return [WorkingHourOut.model_validate(item) for item in items]


@router.post(
    "/barbers/{barber_id}/working-hours",
    response_model=WorkingHourOut,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona uma faixa de expediente",
)
def create_working_hour(
    barber_id: int,
    payload: WorkingHourCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkingHourOut:
    barber = get_barber_or_404(db, barber_id)
    ensure_can_manage_barber(db, current_user, barber)
    _check_overlap(
        db, barber.id, payload.weekday, payload.start_time, payload.end_time
    )
    item = WorkingHour(
        barber_id=barber.id,
        weekday=payload.weekday,
        start_time=payload.start_time,
        end_time=payload.end_time,
        slot_minutes=payload.slot_minutes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return WorkingHourOut.model_validate(item)


@router.patch(
    "/working-hours/{working_hour_id}",
    response_model=WorkingHourOut,
    summary="Atualiza uma faixa de expediente",
)
def update_working_hour(
    working_hour_id: int,
    payload: WorkingHourUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkingHourOut:
    item = _get_working_hour_or_404(db, working_hour_id)
    barber = get_barber_or_404(db, item.barber_id)
    ensure_can_manage_barber(db, current_user, barber)

    data = payload.model_dump(exclude_unset=True)
    weekday = data.get("weekday", item.weekday)
    start_time = data.get("start_time", item.start_time)
    end_time = data.get("end_time", item.end_time)
    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O horario final deve ser maior que o inicial.",
        )
    _check_overlap(db, barber.id, weekday, start_time, end_time, exclude_id=item.id)

    item.weekday = weekday
    item.start_time = start_time
    item.end_time = end_time
    if data.get("slot_minutes") is not None:
        item.slot_minutes = data["slot_minutes"]
    db.commit()
    db.refresh(item)
    return WorkingHourOut.model_validate(item)


@router.delete(
    "/working-hours/{working_hour_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma faixa de expediente",
)
def delete_working_hour(
    working_hour_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    item = _get_working_hour_or_404(db, working_hour_id)
    barber = get_barber_or_404(db, item.barber_id)
    ensure_can_manage_barber(db, current_user, barber)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Bloqueios de agenda (folgas, imprevistos)
# ---------------------------------------------------------------------------


@router.get(
    "/barbers/{barber_id}/time-off",
    response_model=list[TimeOffOut],
    summary="Bloqueios de agenda do barbeiro",
)
def list_time_off(
    barber_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TimeOffOut]:
    barber = get_barber_or_404(db, barber_id)
    ensure_can_manage_barber(db, current_user, barber)
    items = (
        db.query(TimeOff)
        .filter(TimeOff.barber_id == barber_id)
        .order_by(TimeOff.starts_at)
        .all()
    )
    return [TimeOffOut.model_validate(item) for item in items]


@router.post(
    "/barbers/{barber_id}/time-off",
    response_model=TimeOffOut,
    status_code=status.HTTP_201_CREATED,
    summary="Bloqueia um periodo na agenda",
)
def create_time_off(
    barber_id: int,
    payload: TimeOffCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimeOffOut:
    barber = get_barber_or_404(db, barber_id)
    ensure_can_manage_barber(db, current_user, barber)
    shop = get_barbershop_or_404(db, barber.barbershop_id)

    starts_at = _to_utc(payload.starts_at, shop)
    ends_at = _to_utc(payload.ends_at, shop)
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O fim do bloqueio deve ser maior que o inicio.",
        )

    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.barber_id == barber.id,
            Appointment.status.in_(BLOCKING_STATUSES),
            Appointment.start_at < ends_at,
            Appointment.end_at > starts_at,
        )
        .first()
    )
    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Existem agendamentos ativos nesse periodo. Cancele-os antes de bloquear.",
        )

    item = TimeOff(
        barber_id=barber.id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=payload.reason,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return TimeOffOut.model_validate(item)


@router.delete(
    "/time-off/{time_off_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um bloqueio de agenda",
)
def delete_time_off(
    time_off_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    item = _get_time_off_or_404(db, time_off_id)
    barber = get_barber_or_404(db, item.barber_id)
    ensure_can_manage_barber(db, current_user, barber)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
