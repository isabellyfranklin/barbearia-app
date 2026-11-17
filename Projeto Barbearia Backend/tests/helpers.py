from datetime import datetime, timedelta

from app.utils import get_timezone


def next_service_date(days_ahead: int = 1, tz_name: str = "America/Sao_Paulo"):
    """Proxima data que nao cai em domingo (dia sem expediente no seed)."""
    tz = get_timezone(tz_name)
    target = datetime.now(tz).date() + timedelta(days=days_ahead)
    while target.weekday() == 6:
        target += timedelta(days=1)
    return target


def shop_resources(client, shop_id: int) -> tuple[dict, dict]:
    shop = client.get(f"/api/v1/barbershops/{shop_id}")
    assert shop.status_code == 200, shop.text
    data = shop.json()
    service = next(item for item in data["services"] if item["name"] == "Corte de cabelo")
    barber = data["barbers"][0]
    return service, barber


def availability(client, shop_id: int, service_id: int, target_date, barber_id: int | None = None):
    params = {"service_id": service_id, "date": target_date.isoformat()}
    if barber_id is not None:
        params["barber_id"] = barber_id
    return client.get(f"/api/v1/barbershops/{shop_id}/availability", params=params)
