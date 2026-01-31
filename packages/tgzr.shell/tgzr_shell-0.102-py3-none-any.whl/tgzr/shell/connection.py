from __future__ import annotations
from typing import TYPE_CHECKING, Any

from urllib.parse import urlparse

from tgzr.package_management.plugin_manager import PluginManager, Plugin

if TYPE_CHECKING:
    from .session import Session


class Connection:
    def __init__(self, session: Session, url: str | None):
        self._session = session
        self._url = url

    @property
    def session(self) -> Session:
        return self._session

    @property
    def url(self) -> str | None:
        return self._url

    async def get_broker_connection_config(self) -> dict[str, Any]: ...


class ConnectionPlugin(Plugin):

    @classmethod
    def plugin_type_name(cls) -> str:
        return "ConnectionPlugin"

    @classmethod
    def handles(cls, url_scheme: str | None) -> bool: ...
    def get_connection(self, session: Session, url: str | None) -> Connection: ...


class ConnectionPluginManager(PluginManager[ConnectionPlugin]):
    EP_GROUP = "tgzr.shell.connection_plugin"

    def get_connection(self, session: Session, url: str | None) -> Connection:
        scheme = None
        if url is not None:
            parsed = urlparse(url)
            scheme = parsed.scheme
        for plugin in self.get_plugins():
            if plugin.handles(scheme):
                return plugin.get_connection(session, url)
        raise ValueError(
            f"No ConnectionPlugin found for {scheme=} ({url=}. "
            f"(got plugins:{[p.plugin_name() for p in self.get_plugins()]} and errors: {self._broken})"
        )
