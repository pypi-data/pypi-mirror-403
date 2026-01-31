from __future__ import annotations
from typing import TYPE_CHECKING, Type, Any

from tgzr.package_management.plugin_manager import PluginManager, Plugin


if TYPE_CHECKING:
    from .session import Session
    from .broker import AsyncBroker  # used for type checking transitive imports


class ServiceClientPlugin(Plugin):
    @classmethod
    def plugin_type_name(cls) -> str:
        return "ServiceClientPlugin"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session: Session | None = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise ValueError("Not connected! Did you call sesssion.connect() ?")
        return self._session

    async def connect(self, session: Session) -> None:
        self._session = session

    async def disconnect(self) -> None: ...


class ServiceClientPluginManager(PluginManager[ServiceClientPlugin]):
    EP_GROUP = "tgzr.shell.service_client_plugin"
