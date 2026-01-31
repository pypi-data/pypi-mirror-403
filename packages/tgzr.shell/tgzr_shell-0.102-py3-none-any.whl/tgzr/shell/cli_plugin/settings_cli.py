from pathlib import Path
import ast
import asyncio

import click
import rich
import rich.table
import json

from tgzr.cli.utils import TGZRCliGroup

from .utils import pass_session, Session


@click.group(cls=TGZRCliGroup, help="Manage tgzr settings.")
def settings_group():
    pass


@settings_group.command()
@pass_session
def show(session: Session):
    rich.print(session.settings.plugin_info())


@settings_group.command()
@click.argument("key")
@click.argument("context", nargs=-1, required=True)
@click.option(
    "-f",
    "--format",
    default="text",
    help='The output format ["text", "json"] (defaults to "text").',
)
@click.option(
    "--default",
    help="The value to show if the key is not set in the given context.",
)
@pass_session
def get(session: Session, context, key, format, default):
    if default == "None":
        default = None

    if not key:
        key = None  # avoid getting a key named ""

    async def get_value(context, key):
        # NB: the -C cli arg has stored its value in session.context.connection_url
        # which makes it the default url when calling session.connect(url=None):
        await session.connect(None)
        value = await session.settings.get_context_flat(
            context, key, with_history=False
        )
        return value

    value = asyncio.run(get_value(context, key))

    if default and value is None:
        value = default

    if format == "text":
        rich.print(value)
    elif format == "json":
        rich.print(json.dumps(value))


@settings_group.command()
@click.argument("key")
@click.argument("value")
@click.argument("context_name")
@pass_session
def set(session: Session, context_name, key, value):
    """
    Set a value in a settings context
    """
    try:
        value = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass

    if not key:
        key = None  # avoid getting a key named ""

    async def set_value(context_name, key, value) -> None:
        # NB: the -C cli arg has stored its value in session.context.connection_url
        # which makes it the default url when calling session.connect(url=None):
        await session.connect(None)
        value = await session.settings.set(context_name, key, value)
        return value

    click.echo(f"session.settings.set_value({context_name!r}, {key!r}, {value!r})")
    asyncio.run(set_value(context_name, key, value))
    click.echo("Done.")


@settings_group.command()
@pass_session
def get_context_names(session: Session):
    """
    List the known context names
    """

    async def get_context_infos():
        # NB: the -C cli arg has stored its value in session.context.connection_url
        # which makes it the default url when calling session.connect(url=None):
        await session.connect(None)
        infos: dict[str, dict] = {}
        names = await session.settings.get_context_names()
        for name in names:
            info = await session.settings.get_context_info(name)
            infos[name] = info
        return infos

    infos = asyncio.run(get_context_infos())
    table = rich.table.Table("Name", "Icon", "Description")
    for name, info in infos.items():
        color = info.get("color")
        if color is not None:
            name = f"[default on {color}]{name}[/]"
        table.add_row(name, info.get("icon"), info.get("description"))
    rich.print(table)
    click.echo("Done.")
