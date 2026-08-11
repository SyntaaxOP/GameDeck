"""Errors raised by application services."""


class DomainError(Exception):
    code = "domain_error"
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class GameNotFoundError(DomainError):
    code = "game_not_found"
    status_code = 404


class ExecutableConflictError(DomainError):
    code = "executable_conflict"
    status_code = 409


class InvalidGamePathError(DomainError):
    code = "invalid_game_path"
    status_code = 422


class GameArchivedError(DomainError):
    code = "game_archived"
    status_code = 409

class GameLaunchError(DomainError):
    code = "game_launch_failed"
    status_code = 409


class SessionNotFoundError(DomainError):
    code = "session_not_found"
    status_code = 404


class SessionOverlapError(DomainError):
    code = "session_overlap"
    status_code = 409


class InvalidSessionError(DomainError):
    code = "invalid_session"
    status_code = 422


class ActiveSessionMutationError(DomainError):
    code = "active_session_mutation"
    status_code = 409


class PurchaseNotFoundError(DomainError):
    code = "purchase_not_found"
    status_code = 404


class FiveMServerNotFoundError(DomainError):
    code = "fivem_server_not_found"
    status_code = 404


class FiveMServerConflictError(DomainError):
    code = "fivem_server_conflict"
    status_code = 409


class GameNightNotFoundError(DomainError):
    code = "game_night_not_found"
    status_code = 404


class SteamConfigurationError(DomainError):
    code = "steam_not_configured"
    status_code = 409


class SteamUnavailableError(DomainError):
    code = "steam_unavailable"
    status_code = 503
