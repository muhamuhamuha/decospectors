from enum import IntEnum
from typing import (
    Any,
    Callable,
    Generator,
    NamedTuple,
    NoReturn,
    Union,
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
    """Positional args and kwargs."""
    positional_args: ValuesDict
    keywords: dict


class SafeCode(IntEnum):
    POSITIONAL = 0
    NONPOSITIONAL = 1


def decospector(func: Callable, *args: Any, **kwargs: Any) -> dict:
    snoop = Inspector(func, *args, **kwargs)
    return snoop.kwargify() | kwargs


class SafeDecospector:

    def __init__(self,
                 func: Callable,
                 *args: Any,
                 **kwargs: Any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.pos, self.nonpos = self._unify()

    def package(self) -> tuple[ValuesDict, dict]:
        return self.pos, self.nonpos

    def find_param(self,
                   param: str,
                   get_code: bool = False,
                   ) -> Union[Union[tuple[SafeCode, Any], Any], NoReturn]:
        if param in self.pos.keys():
            return (
                (SafeCode.POSITIONAL, self.pos[param])
                if get_code else
                self.pos[param]
            )

        elif param in self.nonpos.keys():
            return (
                (SafeCode.NONPOSITIONAL, self.nonpos[param])
                if get_code else
                self.nonpos[param]
            )

        else:
            raise KeyError(f'"{param}" param does not exist. Available params: '
                           f"{list(self.pos.keys())}, {list(self.nonpos.keys())}")

    def mutate(self, param: str, new_value: Any) -> Union[SafeCode, NoReturn]:
        code, _ = self.find_param(param, get_code=True)

        if code == SafeCode.POSITIONAL:
            self.pos[param] = new_value
        else:
            self.nonpos[param] = new_value
        return code

    def _unify(self) -> PargsKwargs:
        snoop = Inspector(self.func, *self.args, **self.kwargs)
        kwargified = snoop.kwargify() | self.kwargs

        if snoop.no_forced_params():
            return PargsKwargs({}, kwargified)
    
        pos_params = [param for param in snoop.params
                      if snoop.is_positional_only(param)]
        pos_args = {pos_param: kwargified[pos_param] for pos_param in pos_params}

        remaining_kwargs = {k: v
                            for k, v in kwargified.items()
                            if k not in pos_params}

        return PargsKwargs( ValuesDict(**pos_args), remaining_kwargs )
