from tests.helpers import availability, next_service_date, shop_resources


def test_client_cannot_manage_catalog(client, demo, client_headers):
    response = client.post(
        f"/api/v1/barbershops/{demo['barbershop_id']}/services",
        headers=client_headers,
        json={"name": "Invasao", "price": 1, "duration_minutes": 30},
    )
    assert response.status_code == 403


def test_client_cannot_read_another_clients_appointment(
    client, demo, client_headers, admin_headers
):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()

    other = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Outro Cliente",
            "email": "outro@cliente.com",
            "password": "senha123",
        },
    ).json()
    other_id = other["user"]["id"]

    slots = availability(
        client, shop_id, service["id"], target_date, barber["id"]
    ).json()["barbers"][0]["slots"]
    appointment = client.post(
        "/api/v1/appointments",
        headers=admin_headers,
        json={
            "barbershop_id": shop_id,
            "service_id": service["id"],
            "barber_id": barber["id"],
            "start_at": slots[2]["start"],
            "client_id": other_id,
        },
    )
    assert appointment.status_code == 201, appointment.text
    appointment_id = appointment.json()["id"]

    forbidden = client.get(
        f"/api/v1/appointments/{appointment_id}", headers=client_headers
    )
    assert forbidden.status_code == 403

    own_list = client.get(
        "/api/v1/appointments", headers=client_headers, params={"status": "PENDING"}
    )
    assert own_list.status_code == 200
    assert own_list.json() == []


def test_barber_only_sees_own_agenda(client, demo, barber_headers, admin_headers):
    shop_id = demo["barbershop_id"]
    shop = client.get(f"/api/v1/barbershops/{shop_id}").json()
    service = shop["services"][0]
    barbers = shop["barbers"]
    assert len(barbers) >= 2
    target_date = next_service_date()

    slots = availability(
        client, shop_id, service["id"], target_date, barbers[1]["id"]
    ).json()["barbers"][0]["slots"]

    client_user = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Cliente Agenda",
            "email": "agenda@cliente.com",
            "password": "senha123",
        },
    ).json()["user"]

    created = client.post(
        "/api/v1/appointments",
        headers=admin_headers,
        json={
            "barbershop_id": shop_id,
            "service_id": service["id"],
            "barber_id": barbers[1]["id"],
            "start_at": slots[0]["start"],
            "client_id": client_user["id"],
        },
    )
    assert created.status_code == 201, created.text

    own_agenda = client.get(
        "/api/v1/appointments", headers=barber_headers, params={"status": "PENDING"}
    )
    assert own_agenda.status_code == 200
    assert own_agenda.json() == []

    forbidden = client.get(
        f"/api/v1/appointments/{created.json()['id']}", headers=barber_headers
    )
    assert forbidden.status_code == 403


def test_admin_cannot_manage_other_shop(client, demo, admin_headers):
    other = client.post(
        "/api/v1/auth/register/barbershop",
        json={
            "name": "Concorrente",
            "owner_name": "Outro Dono",
            "owner_email": "dono@concorrente.com",
            "owner_password": "senha123",
        },
    )
    assert other.status_code == 201
    other_shop_id = client.get(
        "/api/v1/barbershops/mine",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    ).json()[0]["id"]

    response = client.patch(
        f"/api/v1/barbershops/{other_shop_id}",
        headers=admin_headers,
        json={"name": "Invadida"},
    )
    assert response.status_code == 403

    report = client.get(
        f"/api/v1/barbershops/{other_shop_id}/reports/summary", headers=admin_headers
    )
    assert report.status_code == 403
