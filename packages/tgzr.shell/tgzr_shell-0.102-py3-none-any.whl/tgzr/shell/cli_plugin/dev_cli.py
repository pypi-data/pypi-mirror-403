from __future__ import annotations
from typing import Literal

from pathlib import Path
import shutil
import os
import subprocess

import click

from tgzr.cli.utils import TGZRCliGroup

from ..session import Session
from ..workspace import Workspace
from ..studio import Studio

from .utils import pass_session


@click.group(cls=TGZRCliGroup)
def dev():
    """Developer tools"""
    pass


@dev.command()
@click.argument("index_name")
@pass_session
def create_local_index(session: Session, index_name: str):
    """
    Create a package index folder in *home*, and set it as default index on
    the workspace config.
    """
    workspace: Workspace = session.workspace

    pi = session.home / index_name
    pi.mkdir(exist_ok=True)
    workspace.config.default_index = "../" + index_name
    workspace.save_config()


@dev.command()
@click.option(
    "-i",
    "--index_name",
    help="Name of the local index. Default is to get it from Workspaces config.",
)
@click.option(
    "-p", "--project", help="Path of the project to build. Defaults to current path."
)
@click.option(
    "-B",
    "--builder",
    default="hatch",
    help='Builder to use, one of ["hatch", "uv", "build"] (defaults to "hatch").',
)
@pass_session
def build_to_local_index(
    session: Session,
    index_name: str | None,
    project: str | None,
    builder: Literal["hatch", "uv", "build"] = "hatch",
):
    """
    Build the project in the current directory directly in
    the specified local pacakge index (a folder in the *home*)

    Note: `hatch` must be installed, or you must use the --builder option.
    """
    workspace: Workspace = session.workspace

    if workspace is not None:
        index = workspace.resolve_index(index_name)
    else:
        index = workspaces.resolve_index(index_name)

    if index is None:
        raise click.UsageError(
            f"No index_name specified and no default index configured. Use --index-name or `tgzr ws dev create-local-index INDEX_NAME` first."
        )

    if "://" in index:
        raise click.UsageError(
            f'The index "{index}" is not a local path. Select another one with --index-name or create one with `tgzr ws dev create-local-index path/to/index`.'
        )

    local_index = Path(index)
    if not local_index.exists():
        raise click.UsageError(
            f'The folder "{index}" does not exists. Select another one with --index-name or create one with `tgzr ws dev create-local-index path/to/index` first.'
        )

    if builder == "hatch":
        cwd = None
        if project is not None:
            cwd = Path(".").resolve()
            os.chdir(project)
        cmd = f"hatch build {local_index}"
        try:
            os.system(cmd)
        finally:
            if cwd is not None:
                os.chdir(cwd)

    elif builder == "uv":
        src_option = ""
        if project is not None:
            src_option = project
        cmd = f"uv build --out-dir {local_index} {src_option}"
        os.system(cmd)

    elif builder == "build":
        src_option = ""
        if project is not None:
            src_option = project
        cmd = f"python -m build --outdir {local_index} {src_option}"
        os.system(cmd)

    else:
        raise click.UsageError(f"Unsupported builder: {builder!r}")


@dev.command()
@click.argument("project", required=False)
@click.argument("token", required=False)
@pass_session
def release_and_publish(session: Session, project: str | None, token: str | None):
    """
    Creates a new release on github, and plublish it on PyPI.

    [PROJECT]: path to the git clone, or current directory

    [TOKEN]: PyPI token to use for publishing. If not provided, PYPI_TOKEN env var is used.
    If no value is found, prompts for the token.

    \b
    You need:
      - The current branch to be 'main'.
      - To have something new since last release.
      - To have 'git', 'gh', 'hatch' and 'uv' available in your path.
      - Your 'gh' need to be logged in with appropriate credentials.
    """

    def run_cmd(command, description=None) -> bool:
        if description:
            click.echo(f"Executing: {description}...")

        try:
            subprocess.run(command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            click.echo(f"❌☠️ Command failed with exit code {e.returncode}")
            return False

    def get_current_version():
        return subprocess.check_output("hatch version", shell=True).decode().strip()

    project = project or "."

    project_path = (Path(".") / project).resolve()
    click.echo(f"Using project {project_path}")
    if not project_path.is_dir():
        raise click.UsageError(f"The path {project_path} is not a folder!")
    os.chdir(project)

    #
    #   ASSERT CURRENT BRANCH IS main
    #
    branch = (
        subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True)
        .decode()
        .strip()
    )
    if branch != "main":
        click.echo(f"❌ Error: You are on branch '{branch}'.")
        click.echo("Please merge to 'main' before releasing.")
        return
    click.echo(f"Current branch: {branch!r}")

    #
    #   ASSERT THERE'S NOTHING TO COMMIT AND NOTHING TO PULL
    #
    click.echo("Checking the project status...")
    subprocess.run("git fetch", shell=True, check=True, capture_output=True)

    # NB: --porcelain makes the output script friendly
    cmd = "git status --porcelain"
    output = subprocess.check_output(cmd, shell=True).decode().strip()
    if output:
        click.echo(
            f"❗ Error: You have uncommitted changes or untracked files:\n{output}"
        )
        click.confirm("Release anyway?", abort=True)

    cmd = "git rev-list --left-right --count main...origin/main"
    behind_ahead = subprocess.check_output(cmd, shell=True).decode().strip()
    ahead, behind = map(int, behind_ahead.split())
    if ahead > 0:
        click.echo(f"❌ Error: You have {ahead} local commit(s) not pushed to GitHub.")
        return
    if behind > 0:
        click.echo(
            f"❌ Error: Your local branch is {behind} commit(s) behind GitHub. Please 'git pull'."
        )
        return

    #
    #   ASSERT dist/ IS EMPTY OR ALLOW DELETING IT
    #
    dist_path = project_path / "dist"
    if dist_path.exists():
        click.echo(f"❗Dist folder is not empty: ({dist_path})")
        for path in dist_path.iterdir():
            click.echo(f"    - {path.name}")
        click.confirm("❗Confirm you want to delete all this ?", abort=True)

    #
    #   DEFINE THE NEW RELEASE TAG / NEW PACKAGE VERSION
    #
    try:
        current_version = get_current_version()
    except Exception as err:
        click.confirm("Got an error getting the version. Continue?", abort=True)
        current_version = "0.0.0"
    click.echo(f"Current version: {current_version!r}")

    if ".dev" not in current_version:
        click.echo(
            f"❗You have nothing to release (no .dev in version number, maybe you need to git pull?)."
        )
        click.confirm(f"Do you want to create a new release anyway ?", abort=True)
        next_version = current_version
    else:
        next_version = current_version.split(".dev")[0]

    new_version = click.prompt("New package version", default=next_version)
    if new_version == current_version:
        raise click.UsageError(
            f"Please specify a new version (not {current_version!r})"
        )

    #
    #   CREATE THE NEW RELEASE + ASSERT PACKAGE VERSION IS UPDATED
    #
    click.confirm(f"Create new release {new_version!r} ?", abort=True)
    if not run_cmd(
        f"gh release create {new_version} --generate-notes --target main",
        f"Creating GitHub release {new_version}",
    ):
        return
    if not run_cmd("git fetch --tags", "Updating tags from remote"):
        return
    verify_version = get_current_version()
    if verify_version != new_version:
        click.echo(
            f"❌ Error: the updated version ({verify_version!r}) does not match the release verions ({new_version!r})."
        )
        return

    #
    #   BUILD
    #
    if dist_path.exists():
        shutil.rmtree("dist")

    run_cmd("hatch build", "Building package")

    #
    #   PUBLISH TO PYPI
    #
    if token is None:
        token = os.getenv("PYPI_TOKEN")
        if token is None:
            click.echo(
                "No [TOKEN] option provided and 'PYPI_TOKEN' environment variable not defined."
            )
            token = click.prompt("Enter PyPI token").strip()
        else:
            click.echo("Using PyPI token from PYPI_TOKEN env-var")

    click.confirm("Confirm upload to PyPI?", abort=True)
    if not run_cmd(f"uv publish dist/* -t {token}", "Publishing to PyPI."):
        return

    click.echo(f"🎉 Successfully released {new_version}! 🎉")
