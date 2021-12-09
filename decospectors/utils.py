from enum import IntEnum
from typing import Generator, NamedTuple


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
    keyword_args: dict


class SafeCode(IntEnum):
    POSITIONAL = 0
    NONPOSITIONAL = 1
    VARARG = 2
