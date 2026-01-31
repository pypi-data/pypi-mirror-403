
import click
from tgzr.shell.session import Session

# import copied from click.decorators: 
import typing as t
from functools import update_wrapper
from click.globals import get_current_context

# if t.TYPE_CHECKING:
import typing_extensions as te
P = te.ParamSpec("P")

R = t.TypeVar("R")
T = t.TypeVar("T")


def _make_pass_session_decorator() -> t.Callable[[t.Callable[te.Concatenate[T, P], R]], t.Callable[P, R]]:
    """
    Like `click.decorators.make_pass_decorator()` but with better error msg.
    """
    def decorator(f: t.Callable[te.Concatenate[T, P], R]) -> t.Callable[P, R]:
        def new_func(*args: P.args, **kwargs: P.kwargs) -> R:
            ctx = get_current_context()

            obj: T | None
            obj = ctx.find_object(Session)

            if obj is None:
                raise click.UsageError("No session found. Use 'tgzr -H <home-path> GROUP COMMAND' to specify the home path for a command ('tgzr -h' for details).")

            return ctx.invoke(f, obj, *args, **kwargs)

        return update_wrapper(new_func, f)

    return decorator

# pass_session = click.make_pass_decorator(Session, ensure=False)
pass_session = _make_pass_session_decorator()
