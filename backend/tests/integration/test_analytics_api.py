from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from gamedeck.services.sessions import SessionService


START = datetime(2026, 8, 10, 23, 0, tzinfo=UTC)


def create_game(client: TestClient, title: str, executable: str) -> dict:
    response = client.post("/api/v1/games", json={
        "title": title,
        "platform": "steam",
        "executable_name": executable,
        "status": "backlog",
    })
    assert response.status_code == 201, response.text
    return response.json()


def create_session(client: TestClient, game_id: int, start: datetime, end: datetime) -> None:
    response = client.post("/api/v1/sessions", json={
        "game_id": game_id,
        "started_at": start.isoformat(),
        "ended_at": end.isoformat(),
    })
    assert response.status_code == 201, response.text


def seed_analytics(client: TestClient, db_session: Session) -> tuple[dict, dict, datetime]:
    hades = create_game(client, "Hades", "hades.exe")
    celeste = create_game(client, "Celeste", "celeste.exe")
    create_session(client, hades["id"], START, START + timedelta(hours=2))
    create_session(
        client,
        celeste["id"],
        START + timedelta(hours=1, minutes=30),
        START + timedelta(hours=3),
    )
    at = START + timedelta(hours=6)
    SessionService(db_session).start_process_session(
        hades["id"], observed_at=START + timedelta(hours=4)
    )
    return hades, celeste, at


def test_playtime_clips_cross_midnight_and_counts_active_sessions(
    api_client: TestClient, db_session: Session
) -> None:
    hades, _, at = seed_analytics(api_client, db_session)
    response = api_client.get("/api/v1/analytics/playtime", params={
        "from": "2026-08-10T00:00:00Z",
        "to": "2026-08-12T00:00:00Z",
        "bucket": "day",
        "at": at.isoformat(),
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"] == {
        "total_seconds": 18_000,
        "session_count": 3,
        "average_session_seconds": 6_600,
        "longest_session_seconds": 7_200,
    }
    assert [point["total_seconds"] for point in body["series"]] == [3_600, 14_400]
    assert body["games"][0]["game_id"] == hades["id"]
    assert body["games"][0]["total_seconds"] == 14_400


def test_dashboard_contract_reconciles_cards_rankings_and_recent_items(
    api_client: TestClient, db_session: Session
) -> None:
    hades, _, at = seed_analytics(api_client, db_session)
    response = api_client.get("/api/v1/analytics/dashboard", params={"at": at.isoformat()})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["today_seconds"] == 14_400
    assert body["week_seconds"] == 18_000
    assert body["month_seconds"] == 18_000
    assert body["lifetime"]["total_seconds"] == 18_000
    assert body["top_game"]["game_id"] == hades["id"]
    assert len(body["current_sessions"]) == 1
    assert len(body["recent_sessions"]) == 2
    assert len(body["daily_series"]) == 7


def test_distribution_and_game_analytics(api_client: TestClient, db_session: Session) -> None:
    hades, _, at = seed_analytics(api_client, db_session)
    params = {
        "from": "2026-08-10T00:00:00Z",
        "to": "2026-08-12T00:00:00Z",
        "at": at.isoformat(),
    }
    weekday = api_client.get(
        "/api/v1/analytics/distribution", params={**params, "dimension": "weekday"}
    )
    game = api_client.get(f"/api/v1/analytics/games/{hades['id']}", params=params)

    assert weekday.status_code == 200
    assert [weekday.json()["buckets"][index]["total_seconds"] for index in (0, 1)] == [3_600, 14_400]
    assert game.status_code == 200
    assert game.json()["summary"]["total_seconds"] == 14_400
    assert game.json()["summary"]["session_count"] == 2


def test_saved_timezone_drives_local_day_buckets(api_client: TestClient) -> None:
    game = create_game(api_client, "Hades", "hades.exe")
    assert api_client.patch("/api/v1/settings", json={"time_zone": "Asia/Shanghai"}).status_code == 200
    create_session(
        api_client,
        game["id"],
        datetime(2026, 8, 10, 15, 30, tzinfo=UTC),
        datetime(2026, 8, 10, 16, 30, tzinfo=UTC),
    )
    response = api_client.get("/api/v1/analytics/playtime", params={
        "from": "2026-08-10T08:00:00Z",
        "to": "2026-08-11T16:00:00Z",
        "bucket": "day",
        "at": "2026-08-11T16:00:00Z",
    })

    assert response.status_code == 200
    assert response.json()["time_zone"] == "Asia/Shanghai"
    assert [point["total_seconds"] for point in response.json()["series"]] == [1_800, 1_800]


def test_local_day_bucket_respects_daylight_saving_transition(api_client: TestClient) -> None:
    game = create_game(api_client, "Hades", "hades.exe")
    assert api_client.patch("/api/v1/settings", json={"time_zone": "America/New_York"}).status_code == 200
    create_session(
        api_client,
        game["id"],
        datetime(2026, 3, 8, 5, 0, tzinfo=UTC),
        datetime(2026, 3, 9, 4, 0, tzinfo=UTC),
    )
    response = api_client.get("/api/v1/analytics/playtime", params={
        "from": "2026-03-08T05:00:00Z",
        "to": "2026-03-09T04:00:00Z",
        "bucket": "day",
        "at": "2026-03-09T04:00:00Z",
    })

    assert response.status_code == 200
    assert response.json()["series"][0]["total_seconds"] == 23 * 60 * 60


def test_analytics_empty_invalid_and_missing_game_contracts(api_client: TestClient) -> None:
    empty = api_client.get("/api/v1/analytics/dashboard", params={"at": "2026-08-11T05:00:00Z"})
    invalid = api_client.get("/api/v1/analytics/playtime", params={
        "from": "2026-08-12T00:00:00Z",
        "to": "2026-08-11T00:00:00Z",
    })
    missing = api_client.get("/api/v1/analytics/games/999", params={
        "from": "2026-08-10T00:00:00Z",
        "to": "2026-08-11T00:00:00Z",
    })

    assert empty.status_code == 200
    assert empty.json()["lifetime"]["total_seconds"] == 0
    assert empty.json()["top_game"] is None
    assert invalid.status_code == 422
    assert missing.status_code == 404
