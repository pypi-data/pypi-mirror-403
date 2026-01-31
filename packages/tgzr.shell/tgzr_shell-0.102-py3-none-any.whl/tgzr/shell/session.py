from __future__ import annotations
from typing import TYPE_CHECKING, Type, Callable, Awaitable, Any

import os
import getpass
from pathlib import Path
import dataclasses
import logging

import pydantic

from .base_config import BaseConfig, Field, SettingsConfigDict
from .system import System
from .workspace import Workspace, WorkspaceConfig
from .studio import Studio, StudioConfig
from .project import Project, ProjectConfig
from .broker import AsyncBroker
from .services import ServiceClientPluginManager
from .settings import SettingsClientPlugin
from .connection import ConnectionPluginManager
from tgzr.package_management.plugin_manager import PluginManager, PluginManagerRegistry

if TYPE_CHECKING:
    from .app import _BaseShellApp
    from .connection import Connection

logger = logging.getLogger(__name__)
_DEFAULT_SESSION: Session | None = None


class SessionConfig(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="tgzr_")
    verbose: bool = Field(False, description="Tchatty logs")
    stream_name_prefix: str = "tgzr"
    subject_prefix: str = "tgzr.proto"


def set_default_session(session: Session):
    global _DEFAULT_SESSION
    _DEFAULT_SESSION = session
    logger.debug("Default TGZR Session set.")

    # Also set the env vars for subprocesses to build the session:
    os.environ.setdefault("tgzr_home", str(session.home))
    logger.info(f'  updated env "tgzr_home" to {str(session.home)}')

    if session.context.connection_url is not None:
        os.environ.setdefault(
            "tgzr_connection_url", str(session.context.connection_url)
        )
        logger.info(
            f'  updated env "tgzr_connection_url" to {str(session.context.connection_url)}'
        )
    if session.context.user_name is not None:
        os.environ.setdefault("tgzr_user_name", str(session.context.user_name))
        logger.info(
            f'  updated env "tgzr_user_name" to {str(session.context.user_name)}'
        )
    if session.context.studio_name is not None:
        os.environ.setdefault("tgzr_studio_name", str(session.context.studio_name))
        logger.info(
            f'  updated env "tgzr_studio_name" to {str(session.context.studio_name)}'
        )
    if session.context.project_name is not None:
        os.environ.setdefault("tgzr_project_name", str(session.context.project_name))
        logger.info(
            f'  updated env "tgzr_project_name" to {str(session.context.project_name)}'
        )


def get_default_session(ensure_set: bool = False) -> Session | None:
    """
    Return the session set as default with `set_default_session()`.
    If no session was set as default and the `tgzr_home` environment
    variable is set, a new session is created using it and set as
    default.
    If ensure_set is True, raise an EnvironmentError if no env var
    defines the session home.
    Return None in other cases.
    """
    if _DEFAULT_SESSION is None:
        env_home = os.environ.get("tgzr_home") or os.environ.get("TGZR_HOME")
        if env_home is None:
            if ensure_set:
                raise EnvironmentError(
                    "Missing 'TGZR_HOME' (or 'tgzr_home') env var. Cannot create a Session."
                )
            return None
        logger.info(
            f"Creating default TGZR session using 'tgzr_home' env var: {env_home}"
        )
        session = Session(home=env_home)
        set_default_session(session)

    return _DEFAULT_SESSION


class SessionContextConfig(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="tgzr_")
    user_name: str = pydantic.Field(
        default_factory=getpass.getuser,
        description="The current use name (used in settings etc..)",
    )
    studio_name: str | None = pydantic.Field(
        default=None,
        description="The current studio name",
    )
    project_name: str | None = pydantic.Field(
        default=None,
        description="The current project name",
    )
    entity_name: str | None = pydantic.Field(
        default=None,
        description="The current entity name",
    )


@dataclasses.dataclass
class SessionContext:
    connection_url: str | None
    user_name: str
    studio_name: str | None = None
    project_name: str | None = None
    entity_name: str | None = None
    settings_base_context: tuple[str, ...] = ("system", "admin")


class Session:

    def __init__(self, home: Path | str | None = None):
        self._config_filename = ".tgzr"

        self._home: Path | None = None
        self._workspace: Workspace | None = None
        if home is None:
            home = Path.cwd().resolve()
        else:
            home = Path(home)
        self.set_home(home)

        self._known_config_types: list[Type[BaseConfig]] = []
        self.declare_config_type(SessionConfig)
        self.declare_config_type(SessionContextConfig)
        self.declare_config_type(WorkspaceConfig)
        self.declare_config_type(StudioConfig)
        self.declare_config_type(ProjectConfig)

        self._connection_plugin_manager = ConnectionPluginManager()

        context_config = SessionContextConfig()  # read env vars
        self.context = SessionContext(
            connection_url=None,
            user_name=context_config.user_name,
            studio_name=context_config.studio_name,
            project_name=context_config.project_name,
            entity_name=context_config.entity_name,
        )

        self._system: System = System(self)
        self._broker: AsyncBroker = AsyncBroker(self)
        self._service_plugin_manager = ServiceClientPluginManager()

        settings_plugins = self._service_plugin_manager.find_plugins(
            SettingsClientPlugin
        )
        if not settings_plugins:
            raise RuntimeError("Could not find a Settings plugin :/")
        if len(settings_plugins) > 1:
            raise RuntimeError(
                "Found more than one Settings plugin! (not yet supported)."
            )
        self._settings = settings_plugins[0]

        # self._known_plugin_managers: list[PluginManager] = []
        # self.declare_plugin_manager(self._broker._plugin_manager)
        # self.declare_plugin_manager(self._service_plugin_manager)
        # TODO: refactor cli plugins to use PluginManager and declare it:
        # self.declare_plugin_manager(the_cli_plugin_manager)
        # TODO: refactor apps plugins to use PluginManager and declare it:
        # self.declare_plugin_manager(self._apps_plugin_manager)

    #
    # FILESYSTEM
    #

    @property
    def home(self) -> Path:
        if self._home is None:
            raise ValueError("Home not set. Please use `set_home(path) first.`")
        return self._home

    @property
    def system(self) -> System:
        return self._system

    @property
    def workspace(self) -> Workspace:
        if self._workspace is None:
            raise RuntimeError("Session workspace not yet configured.")
        return self._workspace

    def set_home(
        self, search_path: str | Path, ensure_config_found: bool = True
    ) -> Path | None:
        """Returns the path of the config loaded or None."""
        # FIXME: `ensure_config_found` arg is probably a bad idea / not needed anymore

        search_path = Path(search_path).resolve()
        config_path = SessionConfig.find_config_file(search_path, self._config_filename)
        if config_path is None:
            if ensure_config_found:
                raise FileNotFoundError(
                    f"Could not find a {self._config_filename} file under {search_path!r} and ancestors. "
                    # "(Use `ensure_config_found=False` to bypass this error.)"
                )
            self._home = search_path
        else:
            self._home = config_path.parent
            self._config = SessionConfig.from_file(config_path)

        try:
            self._workspace = Workspace(self)
        except FileNotFoundError:
            self._workspace = None

        # If the given path is inside a studio, let's make this studio
        # the default one:
        # FIXME: use self.context here + work out precedence between env, cli args, current dir, home, etc... + do it for project too!
        if self._workspace and search_path.is_relative_to(self._workspace.path):
            studio_name = str(search_path)[len(str(self._workspace.path)) + 1 :].split(
                os.path.sep, 1
            )[0]
            try:
                self._workspace.set_default_studio(
                    studio_name,
                    ensure_exists=True,
                    save_config=False,  # Do not save, this is just for this session.
                )
            except FileNotFoundError:
                pass
        return config_path

    #
    # CONFIG
    #

    @property
    def config(self) -> SessionConfig:
        if self._config is None:
            raise ValueError("Config not set. Please use `set_home(path) first.`")
        return self._config

    def save_config(self) -> Path:
        """Returns the path of the saved file."""
        return self.write_config_file(None, allow_overwrite=True)

    def write_config_file(
        self, path: str | Path | None, allow_overwrite: bool = False
    ) -> Path:
        """Returns the path of the saved file."""
        if path is None:
            path = self.home / self._config_filename
        path = Path(path).resolve()
        self._config.to_file(
            path,
            allow_overwrite=allow_overwrite,
            header_text="tgzr session config",
        )
        return path

    def declare_config_type(self, config_type: Type[BaseConfig]):
        """
        Declare the config type as used in the session.
        This is used for documentation and cli help.
        """
        self._known_config_types.append(config_type)

    def get_config_env_vars(self) -> list[tuple[str, list[tuple[str, str | None]]]]:
        """
        Returns a list of (name, description) for each config
        declared with `declare_config_type()`
        """
        # TODO: use config type's docstring to show their description in `tgzr help env`
        config_env_vars = []
        for config_type in self._known_config_types:
            config_env_vars.append((config_type.__name__, config_type.used_env_vars()))
        return config_env_vars

    # def declare_plugin_manager(self, plugin_manager: PluginManager):
    #     # TODO: add something like self.get_plugin_manager_info and use it in cli/manager_panel
    #     self._known_plugin_managers.append(plugin_manager)

    def get_plugin_managers(self) -> set[PluginManager]:
        # return self._known_plugin_managers.copy()
        return PluginManagerRegistry.get_plugin_managers()

    def set_verbose(self):
        self.config.verbose = True

    def set_quiet(self):
        self.config.verbose = False

    @property
    def quiet(self) -> bool:
        return not self.config.verbose

    @property
    def verbose(self) -> bool:
        return self.config.verbose

    #
    # CONTEXT
    #

    def select_studio(self, studio_name: str | None = None):
        self.context.studio_name = studio_name

    @property
    def selected_studio_name(self) -> str | None:
        return self.context.studio_name

    def get_selected_studio(self, ensure_exists: bool = True) -> Studio | None:
        if self.workspace is None:
            return None
        studio_name = self.context.studio_name
        if studio_name is None:
            studio_name = self.workspace.default_studio_name()
        if studio_name is None:
            return None
        return self.workspace.get_studio(studio_name, ensure_exists)

    @property
    def selected_project_name(self) -> str | None:
        return self.context.project_name

    def select_project(self, project_name: str | None = None):
        self.context.project_name = project_name

    def get_selected_project(self) -> Project | None:
        if self.workspace is None:
            return None

        if self.context.project_name is None:
            return None

        studio = self.get_selected_studio()
        if studio is None:
            return None

        return studio.get_project(self.context.project_name)

    #
    #   BROKER
    #

    async def connect(self, url: str | None = None):
        """
        Connect all the services.

        Auth is first done on url, and broket configuration
        is fetched from there. Then settings connects and all
        other services/clients use settings to get they configuration.

        If url is None, session.context.connection_url is used.
        How that url is used depends on the list of installed ConnectionPlugin
        (see tgzr.shell.connection.ConnectionPlugin).

        The session.context.connection_url set to url before connection
        attempt.
        """
        if self._broker.connected():
            logger.warning(
                "!!!! Sesssion already connected !!!\n(Please avoid creating duplicate session/connection)"
            )
            return

        if url is None:
            url = self.context.connection_url
        self.context.connection_url = url

        logger.info(f"Connecting session to {self.context.connection_url}")
        connection = self._connection_plugin_manager.get_connection(
            self, self.context.connection_url
        )
        logger.info("Fetching Broker config...")
        broker_connection_config = await connection.get_broker_connection_config()
        logger.info("Connecting Broker...")
        await self._broker.connect(broker_connection_config)
        logger.info("Connecting Settings client...")
        await self.settings.connect(self)
        logger.info("Connecting all Services...")
        for service_client in self._service_plugin_manager.get_plugins():
            if service_client is self.settings:
                continue
            await service_client.connect(self)

    async def disconnect(self):
        """Disconnect all the services."""
        logger.info("Closing all services.")
        for service_client in self._service_plugin_manager.get_plugins():
            await service_client.disconnect()
        await self._broker.disconnect()

    async def subscribe(
        self,
        subject_pattern: str,
        callback: Callable[[AsyncBroker.Event], Awaitable[None]],
    ) -> AsyncBroker.Subscription:
        return await self._broker.subscribe(
            subject_pattern=subject_pattern, callback=callback
        )

    async def publish(self, subject: str, **data) -> None:
        await self._broker.publish(subject=subject, **data)

    async def unsubscribe(self, subscription: AsyncBroker.Subscription) -> None:
        await self._broker.unsubscribe(subscription=subscription)

    async def execute_service_cmd(self, service_name, cmd_name, **cmd_kwargs) -> None:
        await self._broker.cmd(
            service_name=service_name, cmd_name=cmd_name, **cmd_kwargs
        )

    async def execute_service_query(
        self, service_name, query_name, **query_kwargs
    ) -> Any:
        data = await self._broker.query(
            service_name=service_name, query_name=query_name, **query_kwargs
        )
        return data

    #
    # MANAGED SERVICES
    #

    @property
    def settings(self) -> SettingsClientPlugin:
        return self._settings

    #
    # APPS
    #

    def apps(self) -> list[_BaseShellApp]:
        from .app import get_apps

        return get_apps()
