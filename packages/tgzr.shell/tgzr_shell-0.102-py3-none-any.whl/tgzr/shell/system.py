from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path

if TYPE_CHECKING:
    from .session import Session
    from tgzr.package_management.plugin_manager import PluginManager, Plugin


class System:
    """
    Utility class to manage the "System" folder in a tgzr session home.
    """

    def __init__(self, session: Session):
        self._session = session
        self._path = self._session.home / "System"
        if not self._path.exists():
            self._path.mkdir()

    @property
    def path(self) -> Path:
        return self._path

    def get_config_path(self, app_id: str, *subdirs: str) -> Path:
        path = self.path / "etc" / app_id
        for subdir in subdirs:
            path = path / subdir
        path.mkdir(exist_ok=True, parents=True)
        return path

    def get_plugin_config_path(
        self, plugin_manager: PluginManager, plugin: Plugin
    ) -> Path:
        return self.get_config_path(
            "plugins", plugin_manager.EP_GROUP, plugin.plugin_name()
        )
