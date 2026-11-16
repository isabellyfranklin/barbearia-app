from datetime import datetime, timedelta

from tests.helpers import availability, next_service_date, shop_resources
from app.utils import get_timezone


def _local_hour(iso_utc: str) -> int:
    return datetime.fromisoformat(iso_utc.replace("Z", "+00:00")).astimezone(
        get_timezone("America/Sao_Paulo")
    ).hour


def test_availability_has_slots_within_working_hours(client, demo):
    shop_id = demo["barbershop_id"]
    service, _ = shop_resources(client, shop_id)
    target_date = next_service_date()

    response = availability(client, shop_id, service["id"], target_date)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["barbers"]) == 2
    for barber in body["barbers"]:
        assert barber["slots"]
        hours = {_local_hour(slot["start"]) for slot in barber["slots"]}
        assert hours <= {9, 10, 11, 13, 14, 15, 16, 17, 18}
        assert 12 not in hours


def test_availability_rejects_barber_without_the_service(client, demo, admin_headers):
    shop_id = demo["barbershop_id"]
    service, _ = shop_resources(client, shop_id)

    created = client.post(
        f"/api/v1/barbershops/{shop_id}/barbers",
        headers=admin_headers,
        json={
            "name": "Sem Servico",
            "email": "semservico@barbearia.com",
            "password": "senha123",
            "service_ids": [],
        },
    )
    assert created.status_code == 201, created.text

    response = availability(
        client, shop_id, service["id"], next_service_date(), created.json()["id"]
    )
    assert response.status_code == 404


def test_time_off_blocks_slots(client, demo, admin_headers):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()
    target = target_date.isoformat()

    created = client.post(
        f"/api/v1/barbers/{barber['id']}/time-off",
        headers=admin_headers,
        json={
            "starts_at": f"{target}T09:00:00-03:00",
            "ends_at": f"{target}T10:00:00-03:00",
            "reason": "Compromisso pessoal",
        },
    )
    assert created.status_code == 201, created.text

    slots = availability(
        client, shop_id, service["id"], target_date, barber["id"]
    ).json()["barbers"][0]["slots"]
    local_times = [
        datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
        .astimezone(get_timezone("America/Sao_Paulo"))
        .strftime("%H:%M")
        for slot in slots
    ]
    assert "09:00" not in local_times
    assert "09:30" not in local_times
    assert "10:00" in local_times

    listing = client.get(
        f"/api/v1/barbers/{barber['id']}/time-off", headers=admin_headers
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_time_off_rejects_period_with_active_appointment(client, demo, client_headers, admin_headers):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()

    slots = availability(
        client, shop_id, service["id"], target_date, barber["id"]
    ).json()["barbers"][0]["slots"]
    booked = client.post(
        "/api/v1/appointments",
        headers=client_headers,
        json={
            "barbershop_id": shop_id,
            "service_id": service["id"],
            "barber_id": barber["id"],
            "start_at": slots[0]["start"],
        },
    )
    assert booked.status_code == 201, booked.text

    response = client.post(
        f"/api/v1/barbers/{barber['id']}/time-off",
        headers=admin_headers,
        json={
            "starts_at": f"{target_date.isoformat()}T09:00:00-03:00",
            "ends_at": f"{target_date.isoformat()}T11:00:00-03:00",
        },
    )
    assert response.status_code == 409


def test_working_hours_validation_and_sunday(client, demo, admin_headers):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)

    overlap = client.post(
        f"/api/v1/barbers/{barber['id']}/working-hours",
        headers=admin_headers,
        json={"weekday": 0, "start_time": "10:00:00", "end_time": "11:00:00"},
    )
    assert overlap.status_code == 409

    invalid = client.post(
        f"/api/v1/barbers/{barber['id']}/working-hours",
        headers=admin_headers,
        json={"weekday": 2, "start_time": "15:00:00", "end_time": "14:00:00"},
    )
    assert invalid.status_code == 422

    tz = get_timezone("America/Sao_Paulo")
    today = datetime.now(tz).date()
    next_sunday = today + timedelta(days=(6 - today.weekday()) % 7 or 7)
    created = client.post(
        f"/api/v1/barbers/{barber['id']}/working-hours",
        headers=admin_headers,
        json={"weekday": 6, "start_time": "09:00:00", "end_time": "12:00:00"},
    )
    assert created.status_code == 201, created.text

    slots = availability(
        client, shop_id, service["id"], next_sunday, barber["id"]
    ).json()["barbers"][0]["slots"]
    assert slots

    removed = client.delete(
        f"/api/v1/working-hours/{created.json()['id']}", headers=admin_headers
    )
    assert removed.status_code == 204

    slots_after = availability(
        client, shop_id, service["id"], next_sunday, barber["id"]
    ).json()["barbers"][0]["slots"]
    assert slots_after == []
