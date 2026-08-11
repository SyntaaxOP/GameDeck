from datetime import datetime

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gamedeck.models.purchase import Purchase


def create_game(client: TestClient, title: str = "Costed Game") -> int:
    response = client.post(
        "/api/v1/games",
        json={
            "title": title,
            "platform": "steam",
            "executable_name": f"{title.lower().replace(' ', '-')}.exe",
            "status": "backlog",
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def test_purchase_crud_filters_and_validation(api_client: TestClient) -> None:
    game_id = create_game(api_client)
    created = api_client.post(
        "/api/v1/purchases",
        json={
            "game_id": game_id,
            "kind": "base_game",
            "amount_minor": 59_900,
            "currency_code": "php",
            "purchased_on": "2026-08-01",
            "platform": " Steam ",
            "notes": " Launch sale ",
        },
    )
    assert created.status_code == 201
    purchase = created.json()
    assert purchase["currency_code"] == "PHP"
    assert purchase["game_title"] == "Costed Game"
    assert purchase["platform"] == "Steam"
    assert purchase["notes"] == "Launch sale"

    unassigned = api_client.post(
        "/api/v1/purchases",
        json={
            "kind": "subscription",
            "amount_minor": 999,
            "currency_code": "USD",
        },
    )
    assert unassigned.status_code == 201
    unassigned_id = unassigned.json()["id"]

    filtered = api_client.get(f"/api/v1/purchases?game_id={game_id}")
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == purchase["id"]

    unassigned_list = api_client.get("/api/v1/purchases?unassigned=true")
    assert unassigned_list.json()["total"] == 1
    assert unassigned_list.json()["items"][0]["id"] == unassigned_id

    updated = api_client.patch(
        f"/api/v1/purchases/{purchase['id']}",
        json={"kind": "dlc", "amount_minor": 12_500, "game_id": None},
    )
    assert updated.status_code == 200
    assert updated.json()["kind"] == "dlc"
    assert updated.json()["game_id"] is None

    missing_game = api_client.post(
        "/api/v1/purchases",
        json={
            "game_id": 999_999,
            "kind": "base_game",
            "amount_minor": 1,
            "currency_code": "PHP",
        },
    )
    assert missing_game.status_code == 404
    assert missing_game.json()["error"]["code"] == "game_not_found"

    invalid_amount = api_client.post(
        "/api/v1/purchases",
        json={"kind": "other", "amount_minor": -1, "currency_code": "PHP"},
    )
    assert invalid_amount.status_code == 422

    invalid_update = api_client.patch(
        f"/api/v1/purchases/{purchase['id']}", json={"currency_code": None}
    )
    assert invalid_update.status_code == 422

    deleted = api_client.delete(f"/api/v1/purchases/{purchase['id']}")
    assert deleted.status_code == 204
    missing = api_client.get(f"/api/v1/purchases/{purchase['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "purchase_not_found"


def test_spending_summary_keeps_currencies_separate(api_client: TestClient) -> None:
    game_id = create_game(api_client, "Hours Game")
    session = api_client.post(
        "/api/v1/sessions",
        json={
            "game_id": game_id,
            "started_at": "2026-08-01T10:00:00Z",
            "ended_at": "2026-08-01T12:00:00Z",
        },
    )
    assert session.status_code == 201

    for amount, currency in ((59_900, "PHP"), (10_000, "PHP"), (2_000, "USD")):
        response = api_client.post(
            "/api/v1/purchases",
            json={
                "game_id": game_id,
                "kind": "base_game" if amount == 59_900 else "dlc",
                "amount_minor": amount,
                "currency_code": currency,
            },
        )
        assert response.status_code == 201
    subscription = api_client.post(
        "/api/v1/purchases",
        json={
            "kind": "subscription",
            "amount_minor": 999,
            "currency_code": "USD",
        },
    )
    assert subscription.status_code == 201

    summary = api_client.get("/api/v1/spending/summary")
    assert summary.status_code == 200
    by_currency = {item["currency_code"]: item for item in summary.json()["currencies"]}
    assert by_currency["PHP"] == {
        "currency_code": "PHP",
        "amount_minor": 69_900,
        "purchase_count": 2,
        "attributed_amount_minor": 69_900,
        "played_seconds": 7_200,
        "cost_per_hour_minor": 34_950,
    }
    assert by_currency["USD"]["amount_minor"] == 2_999
    assert by_currency["USD"]["attributed_amount_minor"] == 2_000
    assert by_currency["USD"]["cost_per_hour_minor"] == 1_000
    assert summary.json()["unassigned_purchase_count"] == 1

    game_summary = api_client.get(f"/api/v1/spending/games/{game_id}")
    assert game_summary.status_code == 200
    assert game_summary.json()["played_seconds"] == 7_200
    assert game_summary.json()["purchase_count"] == 3
    assert len(game_summary.json()["currencies"]) == 2


def test_cost_per_hour_is_unavailable_before_play(api_client: TestClient) -> None:
    game_id = create_game(api_client, "Unplayed Game")
    api_client.post(
        "/api/v1/purchases",
        json={
            "game_id": game_id,
            "kind": "base_game",
            "amount_minor": 5_000,
            "currency_code": "PHP",
        },
    )
    summary = api_client.get(f"/api/v1/spending/games/{game_id}").json()
    assert summary["played_seconds"] == 0
    assert summary["currencies"][0]["cost_per_hour_minor"] is None


@pytest.mark.parametrize(
    ("values", "constraint"),
    [
        ({"amount_minor": -1}, "ck_purchases_amount_nonnegative"),
        ({"currency_code": "php"}, "ck_purchases_currency_code"),
        ({"game_id": 999_999}, "FOREIGN KEY"),
    ],
)
def test_purchase_constraints_are_database_enforced(
    db_session: Session, values: dict[str, object], constraint: str
) -> None:
    fields: dict[str, object] = {
        "game_id": None,
        "kind": "other",
        "amount_minor": 100,
        "currency_code": "PHP",
        "created_at": datetime(2026, 8, 11),
        "updated_at": datetime(2026, 8, 11),
    }
    fields.update(values)
    db_session.add(Purchase(**fields))
    with pytest.raises(IntegrityError, match=constraint):
        db_session.commit()
