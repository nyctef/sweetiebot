import logging
import random
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar, overload
import requests

S = TypeVar("S")
P = ParamSpec("P")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


def logerrors(
    func: Callable[Concatenate[S, P], R],
) -> Callable[Concatenate[S, P], R | str]:
    from functools import wraps

    @wraps(func)
    def logged(self: S, *args: P.args, **kwargs: P.kwargs) -> R | str:
        try:
            return func(self, *args, **kwargs)
        except requests.exceptions.Timeout:
            return "[timeout] The internet is problematic :sweetieskeptical:"
        except Exception as e:
            print("\n\n####\n\n")
            logging.exception("Error in " + func.__name__)
            print("\n\n####\n\n")
            return "[{}] My code is problematic :sweetieoops:".format(type(e).__name__)

    # `self` can be passed by keyword to `logged`, which Concatenate doesn't allow for
    return logged  # type: ignore[return-value]


def randomstr() -> str:
    return "%08x" % random.randrange(16 ** 8)


@overload
def botcmd(func: F, /) -> F: ...


@overload
def botcmd(
    *, hidden: bool = False, name: str | None = None, thread: bool = False
) -> Callable[[F], F]: ...


def botcmd(*args: Any, **kwargs: Any) -> Any:
    """Decorator for bot command functions
    based on http://sourceforge.net/p/pythonjabberbot/code/ci/master/tree/jabberbot.py
    """

    def decorate(
        func: F, hidden: bool = False, name: str | None = None, thread: bool = False
    ) -> F:
        setattr(func, "_bot_command", True)
        setattr(func, "_bot_command_hidden", hidden)
        setattr(func, "_bot_command_name", name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)
