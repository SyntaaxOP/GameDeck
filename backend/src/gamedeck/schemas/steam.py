"""Steam API and local-install discovery schemas."""

from pydantic import BaseModel, Field


class SteamGamePreview(BaseModel):
    app_id: int
    name: str
    playtime_minutes: int = 0
    already_imported: bool = False


class SteamPreviewRequest(BaseModel):
    steam_id: str | None = Field(default=None, pattern=r"^\d{17}$")


class SteamPreviewResponse(BaseModel):
    steam_id: str
    games: list[SteamGamePreview]
    total: int


class SteamImportItem(BaseModel):
    app_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)


class SteamImportRequest(BaseModel):
    items: list[SteamImportItem] = Field(min_length=1, max_length=500)


class SteamImportResponse(BaseModel):
    imported_game_ids: list[int]
    skipped_app_ids: list[int]


class SteamConfigurationResponse(BaseModel):
    configured: bool
    steam_id: str | None


class SteamInstalledGame(BaseModel):
    app_id: int
    name: str
    install_directory: str
    already_imported: bool
    tracking_ready: bool = True


class SteamLocalLibraryResponse(BaseModel):
    steam_path: str | None
    library_paths: list[str]
    games: list[SteamInstalledGame]
    total: int


class SteamLocalSyncResponse(BaseModel):
    discovered: int
    imported_game_ids: list[int]
    updated_game_ids: list[int]

