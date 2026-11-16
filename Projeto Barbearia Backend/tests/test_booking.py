from tests.helpers import availability, next_service_date, shop_resources


def _book(client, headers, shop_id, service_id, barber_id, start_at):
    return client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "barbershop_id": shop_id,
            "service_id": service_id,
            "barber_id": barber_id,
            "start_at": start_at,
        },
    )


def test_full_booking_flow(
    client, demo, client_headers, barber_headers, admin_headers
):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()

    response = availability(client, shop_id, service["id"], target_date, barber["id"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["timezone"] == "America/Sao_Paulo"
    assert body["barbers"][0]["slots"], "esperava horarios livres no dia seguinte"

    slot = body["barbers"][0]["slots"][0]
    start_at = slot["start"]
    assert start_at.endswith("Z")

    created = _book(
        client, client_headers, shop_id, service["id"], barber["id"], start_at
    )
    assert created.status_code == 201, created.text
    appointment = created.json()
    assert appointment["status"] == "PENDING"
    assert appointment["payment_status"] == "PENDING"
    assert appointment["price"] == service["price"]
    assert appointment["barber_name"] == barber["name"]
    appointment_id = appointment["id"]

    conflict = _book(
        client, client_headers, shop_id, service["id"], barber["id"], start_at
    )
    assert conflict.status_code == 409

    after = availability(client, shop_id, service["id"], target_date, barber["id"]).json()
    remaining = {item["start"] for item in after["barbers"][0]["slots"]}
    assert start_at not in remaining

    payment = client.post(
        f"/api/v1/appointments/{appointment_id}/payment",
        headers=client_headers,
        json={"method": "PIX"},
    )
    assert payment.status_code == 200, payment.text
    payment_body = payment.json()
    assert payment_body["appointment"]["status"] == "CONFIRMED"
    assert payment_body["appointment"]["payment_status"] == "PAID"
    assert payment_body["payment"]["amount"] == service["price"]

    duplicate_payment = client.post(
        f"/api/v1/appointments/{appointment_id}/payment",
        headers=client_headers,
        json={"method": "PIX"},
    )
    assert duplicate_payment.status_code == 409

    agenda = client.get(
        "/api/v1/appointments", headers=barber_headers, params={"status": "PENDING"}
    )
    assert agenda.status_code == 200
    assert [item["id"] for item in agenda.json()] == [appointment_id]

    completed = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        headers=barber_headers,
        json={"status": "COMPLETED"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"

    history = client.get("/api/v1/appointments/history", headers=client_headers)
    assert history.status_code == 200
    assert appointment_id in [item["id"] for item in history.json()]

    cancel_completed = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel", headers=client_headers
    )
    assert cancel_completed.status_code == 409

    summary = client.get(
        f"/api/v1/barbershops/{shop_id}/reports/summary",
        headers=admin_headers,
        params={"start_date": target_date.isoformat(), "end_date": target_date.isoformat()},
    )
    assert summary.status_code == 200, summary.text
    report = summary.json()
    assert report["completed_appointments"] == 1
    assert report["paid_revenue"] == service["price"]


def test_cancel_and_refund(client, demo, client_headers):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()
    slots = availability(
        client, shop_id, service["id"], target_date, barber["id"]
    ).json()["barbers"][0]["slots"]
    start_at = slots[1]["start"]

    appointment = _book(
        client, client_headers, shop_id, service["id"], barber["id"], start_at
    ).json()
    client.post(
        f"/api/v1/appointments/{appointment['id']}/payment",
        headers=client_headers,
        json={"method": "CREDIT_CARD"},
    )

    canceled = client.post(
        f"/api/v1/appointments/{appointment['id']}/cancel", headers=client_headers
    )
    assert canceled.status_code == 200, canceled.text
    body = canceled.json()
    assert body["status"] == "CANCELED"
    assert body["payment_status"] == "REFUNDED"
    assert body["canceled_at"] is not None

    # O horario volta a ficar disponivel apos o cancelamento.
    free_again = availability(
        client, shop_id, service["id"], target_date, barber["id"]
    ).json()["barbers"][0]["slots"]
    assert start_at in {slot["start"] for slot in free_again}


def test_booking_outside_working_hours(client, demo, client_headers):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()

    response = _book(
        client,
        client_headers,
        shop_id,
        service["id"],
        barber["id"],
        f"{target_date.isoformat()}T23:00:00-03:00",
    )
    assert response.status_code == 422


def test_barber_must_perform_the_service(client, demo, admin_headers, client_headers):
    shop_id = demo["barbershop_id"]
    service, barber = shop_resources(client, shop_id)
    target_date = next_service_date()

    created = client.post(
        f"/api/v1/barbershops/{shop_id}/services",
        headers=admin_headers,
        json={"name": "Servico exclusivo", "price": 10, "duration_minutes": 30},
    )
    assert created.status_code == 201
    exclusive = created.json()
    start_at = f"{target_date.isoformat()}T10:00:00-03:00"

    response = _book(
        client, client_headers, shop_id, exclusive["id"], barber["id"], start_at
    )
    assert response.status_code == 422
