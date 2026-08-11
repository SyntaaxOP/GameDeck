def payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "name": "Los Santos Stories",
        "address": "play.example.test:30120",
        "connect_code": "cfx.re/join/demo",
        "discord_url": "https://discord.gg/example",
        "favorite": True,
        "tracked_playtime_seconds": 7200,
    }
    value.update(overrides)
    return value


def test_fivem_server_crud_and_mark_joined(api_client) -> None:
    created = api_client.post("/api/v1/fivem/servers", json=payload())
    assert created.status_code == 201
    server_id = created.json()["id"]
    assert api_client.get("/api/v1/fivem/servers").json()["total"] == 1

    joined = api_client.post(f"/api/v1/fivem/servers/{server_id}/joined")
    updated = api_client.patch(f"/api/v1/fivem/servers/{server_id}", json={"notes": "Weekend city"})
    deleted = api_client.delete(f"/api/v1/fivem/servers/{server_id}")

    assert joined.json()["last_joined_at"] is not None
    assert updated.json()["notes"] == "Weekend city"
    assert deleted.status_code == 204
    assert api_client.get("/api/v1/fivem/servers").json()["total"] == 0


def test_fivem_duplicate_address_and_validation(api_client) -> None:
    assert api_client.post("/api/v1/fivem/servers", json=payload()).status_code == 201
    duplicate = api_client.post("/api/v1/fivem/servers", json=payload(name="Duplicate", address="PLAY.EXAMPLE.TEST:30120"))
    invalid = api_client.post("/api/v1/fivem/servers", json=payload(address="other", discord_url="http://example.test/invite"))
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "fivem_server_conflict"
    assert invalid.status_code == 422
