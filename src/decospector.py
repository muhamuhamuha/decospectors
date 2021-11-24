from typing import Any, Callable, NamedTuple, Union

from .inspector import Inspector


class PosArgsKwargs(NamedTuple):
    positional_args: list[Any]
    keywords: dict[Any]


def decospector(func: Callable, *args: Any, **kwargs: Any) -> dict:
    insp = Inspector(func, *args, **kwargs)
    return insp.kwargify() | kwargs


def safe_decospector(func: Callable, *args: Any, **kwargs: Any) -> PosArgsKwargs:
    insp = Inspector(func, *args, **kwargs)
    kwargd = insp.kwargify() | kwargs

    if insp.no_forced_params():
        return PosArgsKwargs([], kwargd)
    
    pos_params = [param for param in insp.params
                  if insp.is_positional_only(param)]
    pos_args = [kwargs[pos_param] for pos_param in pos_params]
    remaining_kwargs = {k: v for k, v in kwargs.items() if k not in pos_params}
    return PosArgsKwargs(pos_args, remaining_kwargs)
