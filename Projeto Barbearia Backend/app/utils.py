"""Funcoes utilitarias de data/hora.

Convencao do projeto: todo instante e gravado no banco em UTC "naive" (sem tzinfo).
A conversao para o fuso da barbearia acontece apenas na borda (entrada/saida da API
e calculo de disponibilidade).
"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings

UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC)


def utcnow_naive() -> datetime:
    """Instante atual em UTC sem tzinfo (formato usado nas colunas do banco)."""
    return utcnow().replace(tzinfo=None)


def to_utc_naive(value: datetime) -> datetime:
    """Normaliza um datetime (com ou sem fuso) para UTC naive.

    Datetimes sem fuso sao interpretados como UTC.
    """
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(UTC).replace(tzinfo=None, microsecond=0)


def as_aware_utc(value: datetime) -> datetime:
    """Converte um datetime do banco (UTC naive) para um datetime com tzinfo UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    return as_aware_utc(value).isoformat().replace("+00:00", "Z")


def get_timezone(name: str | None = None) -> ZoneInfo:
    """Retorna o fuso informado ou o padrao; usa -03:00 como fallback (Windows sem tzdata)."""
    tz_name = name or settings.default_timezone
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("Etc/GMT+3")  # UTC-3 (o sinal do nome "Etc" e invertido)


def is_valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def local_to_utc_naive(value: datetime, tz: ZoneInfo) -> datetime:
    """Interpreta um datetime sem fuso como horario local da barbearia e converte para UTC naive."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=tz)
    return value.astimezone(UTC).replace(tzinfo=None, microsecond=0)


def utc_naive_to_local(value: datetime, tz: ZoneInfo) -> datetime:
    return as_aware_utc(value).astimezone(tz)


def day_bounds_utc(target_date: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Retorna o inicio e o fim do dia local convertidos para UTC naive."""
    start_local = datetime.combine(target_date, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(UTC).replace(tzinfo=None),
        end_local.astimezone(UTC).replace(tzinfo=None),
    )


def combine_local(target_date: date, value: time, tz: ZoneInfo) -> datetime:
    return datetime.combine(target_date, value, tzinfo=tz)
