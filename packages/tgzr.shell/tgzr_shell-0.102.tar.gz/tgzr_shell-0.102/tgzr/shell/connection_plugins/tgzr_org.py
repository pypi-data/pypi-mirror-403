from __future__ import annotations
from typing import TYPE_CHECKING, Any

from urllib.parse import urlparse

from tgzr.shell.session import Session

from ..connection import ConnectionPlugin, Connection

if TYPE_CHECKING:
    from ..session import Session


class TGZROrgConnectionPlugin(ConnectionPlugin):
    @classmethod
    def handles(cls, url_scheme: str | None) -> bool:
        return url_scheme in ("https", "tgzr", None)

    def get_connection(self, session: Session, url: str | None) -> TGZRConnection:
        return TGZRConnection(session, url)


class TGZRConnection(Connection):

    async def get_broker_connection_config(self) -> dict[str, Any]:
        if self.url is None:
            raise ValueError(f"Unsupported Connection URL: {self.url!r}")

        if self.url.startswith("https://"):
            raise ValueError("tgzr https connection not yet supported.")
        parsed = urlparse(self._url)

        print("Connection:", self.url, parsed._replace(scheme="tls"))
        raise ValueError("tgzr connection not yet implemented")
