from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

from ..connection import ConnectionPlugin, Connection

if TYPE_CHECKING:
    from ..session import Session

logger = logging.getLogger(__name__)


class DefaultConnectionPlugin(ConnectionPlugin):
    """
    This plugin is used when no connection url is provided
    (url is None).
    """

    @classmethod
    def handles(cls, url_scheme: str | None) -> bool:
        return url_scheme is None

    def get_connection(self, session: Session, url: str | None) -> DefaultConnection:
        return DefaultConnection(session, url)


class DefaultConnection(Connection):

    def __init__(self, session: Session, url: str | None):
        super().__init__(session, url="*default*")

    async def get_broker_connection_config(self) -> dict[str, Any]:
        broker_plugin_manager = self.session._broker._plugin_manager
        broker = self.session._broker._broker_implementation
        broker_config_path = self.session.system.get_plugin_config_path(
            broker_plugin_manager,
            broker,
        )
        logger.info(f"Reading broker config from {broker_config_path}")
        user_credentials_file = broker_config_path / "broker.creds"
        if not user_credentials_file.exists():
            raise ValueError(
                f"Cannot connect broker, missing credential file: {user_credentials_file}"
            )

        # TODO: connect to tgzr.org instead of the broker, then get the creds from there!
        config = dict(
            servers="tls://connect.ngs.global",
            user_credentials=str(user_credentials_file),
        )
        return config
