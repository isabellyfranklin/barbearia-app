from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import ensure_shop_owner, get_barbershop_or_404, require_roles
from app.enums import UserRole
from app.models import User
from app.schemas import ReportSummaryOut
from app.services.reports import build_summary
from app.utils import get_timezone, utcnow

router = APIRouter(prefix="/barbershops/{barbershop_id}/reports", tags=["Relatorios"])

MAX_REPORT_DAYS = 366


@router.get(
    "/summary",
    response_model=ReportSummaryOut,
    summary="Resumo gerencial do periodo",
)
def report_summary(
    barbershop_id: int,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ReportSummaryOut:
    shop = get_barbershop_or_404(db, barbershop_id)
    ensure_shop_owner(current_user, shop)

    tz = get_timezone(shop.timezone)
    today = utcnow().astimezone(tz).date()
    end = end_date or today
    start = start_date or (end - timedelta(days=29))

    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data inicial deve ser menor ou igual a data final.",
        )
    if (end - start).days + 1 > MAX_REPORT_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O periodo maximo do relatorio e de {MAX_REPORT_DAYS} dias.",
        )

    return build_summary(db, shop, start, end)
