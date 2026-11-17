from datetime import datetime, timedelta

from app.utils import get_timezone


def test_report_summary_with_seed_data(client, demo, admin_headers):
    today = datetime.now(get_timezone("America/Sao_Paulo")).date()
    start = today - timedelta(days=10)

    response = client.get(
        f"/api/v1/barbershops/{demo['barbershop_id']}/reports/summary",
        headers=admin_headers,
        params={"start_date": start.isoformat(), "end_date": today.isoformat()},
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["total_appointments"] >= 4
    assert report["completed_appointments"] >= 4
    assert report["paid_revenue"] > 0
    assert report["average_ticket"] > 0
    assert report["top_services"]
    assert report["barbers"]
    assert report["daily"]
    assert len(report["by_status"]) >= 5


def test_report_validates_period_and_role(client, demo, admin_headers, barber_headers):
    today = datetime.now(get_timezone("America/Sao_Paulo")).date()
    base = f"/api/v1/barbershops/{demo['barbershop_id']}/reports/summary"

    inverted = client.get(
        base,
        headers=admin_headers,
        params={
            "start_date": today.isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
        },
    )
    assert inverted.status_code == 422

    too_long = client.get(
        base,
        headers=admin_headers,
        params={
            "start_date": (today - timedelta(days=400)).isoformat(),
            "end_date": today.isoformat(),
        },
    )
    assert too_long.status_code == 422

    forbidden = client.get(base, headers=barber_headers)
    assert forbidden.status_code == 403
