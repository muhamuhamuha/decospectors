from typing import (
    Any,
    Callable,
    Generator,
    NamedTuple,
)

from .inspector import Inspector


class ValuesDict(dict):
    """Like the standard python dictionary, except this collection
    yields the dictionary values instead of its keys.

    >>> normal_dict = dict(name='anakin skywalker', age=21)
    >>> print(*normal_dict)
    name age
    >>> values_dict = ValuesDict(name='anakin skywalker', age=21)
    print(*values_dict)
    anakin skywalker 21
    """
    def __iter__(self) -> Generator:
        return (v for v in self.values())


class PargsKwargs(NamedTuple):
    positional_args: ValuesDict
    keywords: dict


def decospector(func: Callable, *args: Any, **kwargs: Any) -> dict:
    snoop = Inspector(func, *args, **kwargs)
    return snoop.kwargify() | kwargs


def safe_decospector(func: Callable, *args: Any, **kwargs: Any) -> PargsKwargs:
    snoop = Inspector(func, *args, **kwargs)
    kwargified = snoop.kwargify() | kwargs

    if snoop.no_forced_params():
        return PargsKwargs({}, kwargified)
    
    pos_params = [param for param in snoop.params if snoop.is_positional_only(param)]
    pos_args = { pos_param: kwargified[pos_param] for pos_param in pos_params }

    remaining_kwargs = {k: v for k, v in kwargified.items() if k not in pos_params}

    return PargsKwargs( ValuesDict(**pos_args), remaining_kwargs )
