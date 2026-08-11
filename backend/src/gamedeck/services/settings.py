"""Singleton application settings service."""

from datetime import UTC

from sqlalchemy.orm import Session

from gamedeck.models.settings import Settings
from gamedeck.schemas.settings import SettingsResponse, SettingsUpdate
from gamedeck.services.games import utc_now


class SettingsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_model(self) -> Settings:
        settings = self.session.get(Settings, 1)
        if settings is None:
            settings = Settings(id=1, updated_at=utc_now())
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings

    def get(self) -> SettingsResponse:
        return self.to_response(self.get_model())

    def update(self, payload: SettingsUpdate) -> SettingsResponse:
        settings = self.get_model()
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(settings, field, value)
        settings.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(settings)
        return self.to_response(settings)

    @staticmethod
    def to_response(settings: Settings) -> SettingsResponse:
        return SettingsResponse(
            scan_interval_seconds=settings.scan_interval_seconds,
            restart_grace_seconds=settings.restart_grace_seconds,
            tracking_enabled=settings.tracking_enabled,
            week_starts_on=settings.week_starts_on,
            time_zone=settings.time_zone,
            theme=settings.theme,
            currency_code=settings.currency_code,
            updated_at=settings.updated_at.replace(tzinfo=UTC),
        )
