from fastapi.testclient import TestClient


def game_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Hades",
        "platform": "steam",
        "executable_name": "Hades.exe",
        "executable_path": r"C:\Games\Hades\Hades.exe",
        "genre": "Action roguelike",
        "status": "backlog",
        "priority": 2,
        "favorite": True,
    }
    payload.update(overrides)
    return payload


def create_game(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post("/api/v1/games", json=game_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_game_normalizes_executable(api_client: TestClient) -> None:
    created = create_game(api_client)

    assert created["title"] == "Hades"
    assert created["executable_name"] == "hades.exe"
    assert created["executable_path"] == r"C:\Games\Hades\Hades.exe"
    assert created["archived_at"] is None

    response = api_client.get(f"/api/v1/games/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_duplicate_active_executable_returns_conflict(api_client: TestClient) -> None:
    create_game(api_client)

    response = api_client.post(
        "/api/v1/games",
        json=game_payload(title="Hades II", executable_name="HADES.EXE"),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "executable_conflict"


def test_create_update_and_remove_executable_aliases(api_client: TestClient) -> None:
    created = create_game(
        api_client,
        executable_aliases=[
            {
                "executable_name": "Hades-Win64-Shipping.EXE",
                "executable_path": r"C:\Games\Hades\Hades-Win64-Shipping.exe",
            }
        ],
    )

    assert created["executable_aliases"][0]["executable_name"] == "hades-win64-shipping.exe"
    assert created["executable_aliases"][0]["id"] > 0

    updated = api_client.patch(
        f"/api/v1/games/{created['id']}",
        json={"executable_aliases": [{"executable_name": "hades-launcher.exe"}]},
    )
    assert updated.status_code == 200
    assert [item["executable_name"] for item in updated.json()["executable_aliases"]] == [
        "hades-launcher.exe"
    ]

    removed = api_client.patch(
        f"/api/v1/games/{created['id']}", json={"executable_aliases": []}
    )
    assert removed.status_code == 200
    assert removed.json()["executable_aliases"] == []


def test_alias_conflicts_with_any_active_mapping(api_client: TestClient) -> None:
    first = create_game(
        api_client,
        executable_aliases=[{"executable_name": "hades-launcher.exe"}],
    )

    primary_conflict = api_client.post(
        "/api/v1/games",
        json=game_payload(
            title="Other",
            executable_name="HADES-LAUNCHER.EXE",
            executable_path=None,
        ),
    )
    alias_conflict = api_client.post(
        "/api/v1/games",
        json=game_payload(
            title="Other",
            executable_name="other.exe",
            executable_path=None,
            executable_aliases=[{"executable_name": "HADES.EXE"}],
        ),
    )

    assert primary_conflict.status_code == 409
    assert alias_conflict.status_code == 409
    assert api_client.get(f"/api/v1/games/{first['id']}").json()["executable_name"] == "hades.exe"


def test_archived_alias_is_reusable_but_restore_is_atomic(api_client: TestClient) -> None:
    original = create_game(
        api_client,
        executable_aliases=[{"executable_name": "hades-launcher.exe"}],
    )
    api_client.delete(f"/api/v1/games/{original['id']}")
    replacement = create_game(
        api_client,
        title="Replacement",
        executable_name="replacement.exe",
        executable_path=None,
        executable_aliases=[{"executable_name": "hades-launcher.exe"}],
    )

    restored = api_client.post(f"/api/v1/games/{original['id']}/restore")

    assert restored.status_code == 409
    archived = api_client.get(f"/api/v1/games/{original['id']}").json()
    assert archived["archived_at"] is not None
    assert api_client.get(f"/api/v1/games/{replacement['id']}").status_code == 200


def test_path_filename_must_match_executable_name(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/games",
        json=game_payload(executable_path=r"C:\Games\Hades\Other.exe"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_game_path"


def test_list_supports_search_filters_sort_and_pagination(api_client: TestClient) -> None:
    create_game(api_client)
    create_game(
        api_client,
        title="Minecraft",
        platform="local",
        executable_name="minecraft.exe",
        executable_path=r"C:\Games\Minecraft\minecraft.exe",
        status="currently_playing",
        favorite=False,
    )
    create_game(
        api_client,
        title="Celeste",
        executable_name="celeste.exe",
        executable_path=r"C:\Games\Celeste\celeste.exe",
        favorite=True,
    )

    response = api_client.get(
        "/api/v1/games",
        params={"q": "e", "platform": "steam", "favorite": True, "page_size": 1, "page": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 2
    assert body["page_size"] == 1
    assert [item["title"] for item in body["items"]] == ["Hades"]


def test_play_next_sort_and_priority_filter_are_deterministic(api_client: TestClient) -> None:
    create_game(api_client, title="Favorite", executable_name="favorite.exe", executable_path=r"C:\Games\Favorite\favorite.exe", priority=5, favorite=True)
    create_game(api_client, title="First", executable_name="first.exe", executable_path=r"C:\Games\First\first.exe", priority=1, favorite=False)
    create_game(api_client, title="Second", executable_name="second.exe", executable_path=r"C:\Games\Second\second.exe", priority=2, favorite=False)
    create_game(api_client, title="Someday", executable_name="someday.exe", executable_path=r"C:\Games\Someday\someday.exe", priority=None, favorite=False)
    create_game(api_client, title="Finished Favorite", executable_name="finished.exe", executable_path=r"C:\Games\Finished\finished.exe", status="completed", priority=1, favorite=True)

    ordered = api_client.get("/api/v1/games", params={"sort": "play_next", "page_size": 100})
    filtered = api_client.get("/api/v1/games", params={"priority": 2})

    assert ordered.status_code == 200
    assert [game["title"] for game in ordered.json()["items"]] == ["Favorite", "First", "Second", "Someday", "Finished Favorite"]
    assert [game["title"] for game in filtered.json()["items"]] == ["Second"]


def test_completed_and_dropped_games_leave_queue_and_clear_priority(api_client: TestClient) -> None:
    game = create_game(api_client, priority=1)

    completed = api_client.patch(f"/api/v1/games/{game['id']}", json={"status": "completed"})
    restored = api_client.patch(f"/api/v1/games/{game['id']}", json={"status": "backlog", "priority": 2})
    dropped = api_client.patch(f"/api/v1/games/{game['id']}", json={"status": "dropped"})

    assert completed.status_code == 200
    assert completed.json()["priority"] is None
    assert completed.json()["date_completed"] is not None
    assert restored.json()["priority"] == 2
    assert restored.json()["date_completed"] is None
    assert dropped.json()["priority"] is None
    assert dropped.json()["date_completed"] is None


def test_update_status_applies_completion_date_rule(api_client: TestClient) -> None:
    created = create_game(api_client)

    completed = api_client.patch(
        f"/api/v1/games/{created['id']}", json={"status": "completed", "personal_rating": 9}
    )
    assert completed.status_code == 200
    assert completed.json()["date_completed"] is not None
    assert completed.json()["personal_rating"] == 9

    returned_to_backlog = api_client.patch(
        f"/api/v1/games/{created['id']}", json={"status": "backlog"}
    )
    assert returned_to_backlog.status_code == 200
    assert returned_to_backlog.json()["date_completed"] is None


def test_archive_hides_game_and_restore_returns_it(api_client: TestClient) -> None:
    created = create_game(api_client)

    archived = api_client.delete(f"/api/v1/games/{created['id']}")
    assert archived.status_code == 204
    assert api_client.get("/api/v1/games").json()["total"] == 0
    archived_list = api_client.get("/api/v1/games", params={"archived": True}).json()
    assert archived_list["total"] == 1

    restored = api_client.post(f"/api/v1/games/{created['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["archived_at"] is None
    assert api_client.get("/api/v1/games").json()["total"] == 1


def test_restore_reports_executable_conflict(api_client: TestClient) -> None:
    original = create_game(api_client)
    api_client.delete(f"/api/v1/games/{original['id']}")
    create_game(api_client, title="Replacement")

    response = api_client.post(f"/api/v1/games/{original['id']}/restore")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "executable_conflict"


def test_validation_and_not_found_use_consistent_errors(api_client: TestClient) -> None:
    invalid = api_client.post(
        "/api/v1/games", json=game_payload(executable_name="not-a-process")
    )
    missing = api_client.get("/api/v1/games/999")

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "game_not_found"


def test_update_rejects_null_for_required_fields(api_client: TestClient) -> None:
    created = create_game(api_client)

    response = api_client.patch(f"/api/v1/games/{created['id']}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
