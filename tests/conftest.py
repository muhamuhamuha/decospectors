import pytest
from typing import Any
from decospectors import safe_decospector


def argskwargs_func(pos_param: Any,
                    /,
                    def_arg: str = 'bye',
                    *args: Any,
                    kw_param: Any,
                    def_kw_param: Any = 'hello',
                    **kwargs: Any) -> tuple:
    return pos_param, def_arg, args, kw_param, def_kw_param, kwargs


@pytest.fixture
def safe_argskwargs():
    pos_param = 1
    args1, args2, args3 = 2, 'abc', [1, 2, 3]
    kw_param = 'keyword_here, hello'
    kwargs_param = {'hi': [4, 4, 4], 'bye': {2, 3, 5}, 'hello': True}

    keywords = safe_decospector(argskwargs_func,
                                pos_param,
                                args1,
                                args2,
                                args3,
                                kw_param=kw_param,
                                **kwargs_param)
    return keywords
