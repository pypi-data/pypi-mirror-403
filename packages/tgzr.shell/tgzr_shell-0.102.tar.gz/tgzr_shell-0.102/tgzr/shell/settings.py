from __future__ import annotations
from typing import TYPE_CHECKING, Any, TypeVar, Callable, Awaitable

import pydantic


from .services import ServiceClientPlugin

if TYPE_CHECKING:
    from .services import AsyncBroker

SettingsModelType = TypeVar("SettingsModelType", bound=pydantic.BaseModel)


class SettingsClientPlugin(ServiceClientPlugin):
    @classmethod
    def plugin_type_name(cls) -> str:
        return "SettingsClientPlugin"

    #
    # ---
    #
    async def watch_changes(
        self, callback: Callable[[AsyncBroker.Event], Awaitable[None]]
    ): ...

    #
    # ---
    #

    async def get_context_names(self) -> tuple[str, ...]: ...
    async def set_context_info(self, context_name: str, **info: Any) -> None: ...
    async def get_context_info(self, context_name: str) -> dict[str, Any]: ...
    def expand_context_name(self, context_name: str) -> list[str]: ...

    #
    # ---
    #
    async def get_context_flat(
        self,
        context: list[str],
        path: str | None = None,
        with_history: bool = False,
    ) -> dict[str, Any]: ...

    async def get_context_dict(
        self, context: list[str], path: str | None = None, with_history: bool = False
    ) -> dict[str, Any]: ...

    async def get_context(
        self,
        context: list[str],
        model_type: type[SettingsModelType],
        path: str | None = None,
    ) -> SettingsModelType: ...

    #
    # ---
    #
    async def update_context_flat(
        self, context_name: str, flat_dict: dict[str, Any], path: str | None = None
    ) -> None: ...

    async def update_context_dict(
        self,
        context_name: str,
        deep_dict: dict[str, Any | dict[str, Any]],
        path: str | None = None,
    ) -> None: ...

    async def update_context(
        self,
        context_name: str,
        model: SettingsModelType,
        path: str | None = None,
        exclude_defaults: bool = True,
    ): ...

    #
    # ---
    #

    async def set(self, context_name: str, name: str, value: Any) -> None: ...
    async def toggle(self, context_name: str, name: str) -> None: ...
    async def add(self, context_name: str, name: str, value: Any) -> None: ...
    async def sub(self, context_name: str, name: str, value: Any) -> None: ...
    async def set_item(
        self, context_name: str, name: str, index: int, item_value: Any
    ) -> None: ...
    async def del_item(self, context_name: str, name: str, index: int) -> None: ...
    async def remove(self, context_name: str, name: str, item: str) -> None: ...
    async def append(self, context_name: str, name: str, value: Any) -> None: ...
    async def env_override(
        self, context_name: str, name: str, envvar_name: str
    ) -> None: ...
    async def pop(self, context_name: str, name: str, index: int | slice) -> None: ...
    async def remove_slice(
        self,
        context_name: str,
        name: str,
        start: int,
        stop: int,
        step: int | None = None,
    ) -> None: ...
    async def call(
        self,
        context_name: str,
        name: str,
        method_name: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> None: ...
