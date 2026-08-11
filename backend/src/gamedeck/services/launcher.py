import os
from pathlib import Path
import subprocess
from sqlalchemy.orm import Session
from gamedeck.domain.errors import GameArchivedError, GameLaunchError
from gamedeck.services.games import GameService

class GameLauncher:
    def __init__(self, session: Session) -> None:
        self.session = session

    def launch(self, game_id: int) -> None:
        game = GameService(self.session).get(game_id)
        if game.archived_at is not None:
            raise GameArchivedError("Archived games cannot be launched.")
        try:
            if game.steam_app_id:
                os.startfile(f"steam://run/{game.steam_app_id}")
                return
            if not game.executable_path:
                raise GameLaunchError("This game does not have a launchable executable path.")
            executable = Path(game.executable_path)
            if not executable.is_file():
                raise GameLaunchError("The configured game executable is unavailable.")
            subprocess.Popen([str(executable)], cwd=str(executable.parent), close_fds=True)
        except OSError as exc:
            raise GameLaunchError("Windows could not launch this game.") from exc
