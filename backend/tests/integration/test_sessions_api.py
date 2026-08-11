from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from gamedeck.schemas.game import GameCreate
from gamedeck.schemas.session import EndReason
from gamedeck.services.games import GameService
from gamedeck.services.sessions import SessionService


START = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def create_game(client: TestClient, *, title: str = "Hades", executable: str = "hades.exe") -> dict:
    response = client.post(
        "/api/v1/games",
        json={
            "title": title,
            "platform": "steam",
            "executable_name": executable,
            "status": "backlog",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_manual_session(
    client: TestClient,
    game_id: int,
    *,
    started_at: datetime = START,
    ended_at: datetime | None = None,
):
    response = client.post(
        "/api/v1/sessions",
        json={
            "game_id": game_id,
            "started_at": started_at.isoformat(),
            "ended_at": (ended_at or started_at + timedelta(hours=2)).isoformat(),
        },
    )
    return response


def test_create_manual_session_calculates_duration_and_returns_game(api_client: TestClient) -> None:
    game = create_game(api_client)

    response = create_manual_session(api_client, game["id"])

    assert response.status_code == 201
    session = response.json()
    assert session["game_title"] == "Hades"
    assert session["duration_seconds"] == 7_200
    assert session["detection_method"] == "manual"
    assert session["end_reason"] == "manual"
    assert session["active"] is False
    assert session["started_at"].endswith("Z")


def test_manual_session_requires_timezone_and_positive_range(api_client: TestClient) -> None:
    game = create_game(api_client)
    naive = api_client.post(
        "/api/v1/sessions",
        json={"game_id": game["id"], "started_at": "2026-08-10T10:00", "ended_at": "2026-08-10T11:00"},
    )
    reversed_range = create_manual_session(
        api_client,
        game["id"],
        started_at=START,
        ended_at=START - timedelta(minutes=1),
    )

    assert naive.status_code == 422
    assert reversed_range.status_code == 422
    assert naive.json()["error"]["code"] == "validation_error"


def test_same_game_overlap_is_rejected_but_adjacent_and_other_game_are_allowed(
    api_client: TestClient,
) -> None:
    game = create_game(api_client)
    other = create_game(api_client, title="Celeste", executable="celeste.exe")
    assert create_manual_session(api_client, game["id"]).status_code == 201

    overlap = create_manual_session(
        api_client,
        game["id"],
        started_at=START + timedelta(hours=1),
        ended_at=START + timedelta(hours=3),
    )
    adjacent = create_manual_session(
        api_client,
        game["id"],
        started_at=START + timedelta(hours=2),
        ended_at=START + timedelta(hours=3),
    )
    other_game = create_manual_session(
        api_client,
        other["id"],
        started_at=START + timedelta(hours=1),
        ended_at=START + timedelta(hours=3),
    )

    assert overlap.status_code == 409
    assert overlap.json()["error"]["code"] == "session_overlap"
    assert adjacent.status_code == 201
    assert other_game.status_code == 201


def test_update_recalculates_duration_and_delete_removes_session(api_client: TestClient) -> None:
    game = create_game(api_client)
    created = create_manual_session(api_client, game["id"]).json()

    updated = api_client.patch(
        f"/api/v1/sessions/{created['id']}",
        json={"ended_at": (START + timedelta(hours=3, minutes=30)).isoformat()},
    )
    assert updated.status_code == 200
    assert updated.json()["duration_seconds"] == 12_600

    deleted = api_client.delete(f"/api/v1/sessions/{created['id']}")
    assert deleted.status_code == 204
    assert api_client.get(f"/api/v1/sessions/{created['id']}").status_code == 404


def test_session_list_filters_by_game_activity_and_intersecting_range(api_client: TestClient) -> None:
    game = create_game(api_client)
    other = create_game(api_client, title="Celeste", executable="celeste.exe")
    create_manual_session(api_client, game["id"])
    create_manual_session(api_client, other["id"], started_at=START + timedelta(days=2))

    by_game = api_client.get("/api/v1/sessions", params={"game_id": game["id"]}).json()
    intersecting = api_client.get(
        "/api/v1/sessions",
        params={
            "from": (START + timedelta(hours=1)).isoformat(),
            "to": (START + timedelta(hours=4)).isoformat(),
            "active": False,
        },
    ).json()

    assert by_game["total"] == 1
    assert by_game["items"][0]["game_id"] == game["id"]
    assert intersecting["total"] == 1
    assert intersecting["items"][0]["game_title"] == "Hades"


def test_process_start_is_idempotent_and_active_session_is_protected(
    db_session: Session,
) -> None:
    game = GameService(db_session).create(
        GameCreate(title="Hades", platform="steam", executable_name="hades.exe")
    )
    service = SessionService(db_session)

    first = service.start_process_session(game.id, observed_at=START, process_id=101)
    repeated = service.start_process_session(
        game.id, observed_at=START + timedelta(seconds=5), process_id=101
    )

    assert repeated.id == first.id
    assert service.list(game_id=game.id, from_at=None, to_at=None, active=True, page=1, page_size=10).total == 1
    assert repeated.last_seen_at == (START + timedelta(seconds=5)).replace(tzinfo=None)

    ended = service.end_active_session(game.id, reason=EndReason.PROCESS_STOPPED)
    assert ended is not None
    assert ended.duration_seconds == 5
    assert service.end_active_session(game.id) is None


def test_immediate_process_stop_records_zero_duration_instead_of_staying_active(
    db_session: Session,
) -> None:
    game = GameService(db_session).create(
        GameCreate(title="Celeste", platform="steam", executable_name="celeste.exe")
    )
    service = SessionService(db_session)
    service.start_process_session(game.id, observed_at=START)

    ended = service.end_active_session(game.id)

    assert ended is not None
    assert ended.duration_seconds == 0
    assert ended.ended_at == START.replace(tzinfo=None)


def test_active_session_cannot_be_manually_edited_or_deleted(
    api_client: TestClient, db_session: Session
) -> None:
    # This test uses the shared migrated database but separate sessions. Create
    # through the API, then start through the service and release its transaction.
    game = create_game(api_client)
    active = SessionService(db_session).start_process_session(game["id"], observed_at=START)

    update = api_client.patch(
        f"/api/v1/sessions/{active.id}",
        json={"ended_at": (START + timedelta(hours=1)).isoformat()},
    )
    delete = api_client.delete(f"/api/v1/sessions/{active.id}")

    assert update.status_code == 409
    assert delete.status_code == 409
    assert update.json()["error"]["code"] == "active_session_mutation"


def test_archived_or_missing_games_cannot_receive_manual_sessions(api_client: TestClient) -> None:
    game = create_game(api_client)
    api_client.delete(f"/api/v1/games/{game['id']}")

    archived = create_manual_session(api_client, game["id"])
    missing = create_manual_session(api_client, 999)

    assert archived.status_code == 409
    assert archived.json()["error"]["code"] == "game_archived"
    assert missing.status_code == 404
