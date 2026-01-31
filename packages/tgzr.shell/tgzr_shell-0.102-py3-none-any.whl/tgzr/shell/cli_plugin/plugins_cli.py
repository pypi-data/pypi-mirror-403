from __future__ import annotations
from typing import TYPE_CHECKING

import click
import rich
import rich.table, rich.tree, rich.pretty
import importlib_metadata

from tgzr.cli.utils import TGZRCliGroup

from .utils import pass_session, Session

if TYPE_CHECKING:
    from tgzr.package_management.plugin_manager import PluginManager, Plugin


def dict_table(d):
    t = rich.table.Table.grid(
        rich.table.Column("key", justify="right"), "value", padding=(0, 1)
    )
    for k, v in d.items():
        t.add_row(f"[cyan]{k}:", str(v))
    return t


@click.group(cls=TGZRCliGroup, help="Manage plugins")
def plugins_group():
    pass


@plugins_group.command()
@pass_session
def ls(session: Session):
    """
    List information about all plugin managers.
    """
    table = rich.table.Table("Name", "Entry Point", "Installed", "Broken")
    for plugin_manager in session.get_plugin_managers():
        broken = plugin_manager.get_broken_plugins()
        nb_broken = len(broken)
        if nb_broken == 1:
            nb_broken = str(broken[0])

        plugins = plugin_manager.get_plugins()
        nb_plugins = len(plugins)
        if nb_plugins == 1:
            nb_plugins = str(plugins[0])

        table.add_row(
            plugin_manager.managed_plugin_type().plugin_type_name(),
            plugin_manager.EP_GROUP,
            str(nb_plugins),
            str(nb_broken),
        )
    rich.print(table)


@plugins_group.command()
@click.argument("filter", required=False)
@pass_session
def show(session: Session, filter: str | None = None):
    """
    Show detailed information about plugin manager.
    Use [FILTER] to filter out based on entry points.
    """
    for plugin_manager in session.get_plugin_managers():
        if filter is not None and filter not in plugin_manager.EP_GROUP:
            continue

        manager_name = plugin_manager.managed_plugin_type().plugin_type_name()

        plugins: list[Plugin] = plugin_manager.get_plugins()
        if plugins:
            loaded_table = rich.table.Table(
                "Loaded",
                title=f"{plugin_manager.EP_GROUP} (loaded by [b]{manager_name}[/b])",
            )
            for plugin in plugins:
                info = plugin.plugin_info()
                info["plugin_type_name"] = f"[green]{info['plugin_type_name']}[/green]"
                info["instance"] = plugin
                info["package"] = plugin.__module__
                try:
                    info["dist-version"] = importlib_metadata.distribution(
                        plugin.__module__
                    ).version
                except:
                    info["dist-version"] = "no that easy to find..."
                loaded_table.add_row(
                    dict_table(info),
                )
            rich.print(loaded_table)

        broken = plugin_manager.get_broken_plugins()
        if broken:
            broken_table = rich.table.Table("Name", title=f"Broken in {manager_name}")
            for ep, exception in broken:
                broken_table.add_row(str(exception))

            rich.print(broken_table)
