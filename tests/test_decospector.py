import pytest
from functools import partial, wraps
from typing import Any, Callable

from decospectors.decospectors import (
    decospector,
    SafeDecospector,
    safe_decospector,
)
from decospectors.utils import SafeCode


# psuedo-fixtures

def get_keywords(func: Callable = None, *, safe: bool = False) -> Callable:
    if func is None:
        return partial(get_keywords, safe=safe)

    @wraps(func)
    def getter(*args, **kwargs):
        if safe:
            return SafeDecospector(func, *args, **kwargs)
        return decospector(func, *args, **kwargs)
    return getter


def all_param_func(pos_greeting: str,
                   /,
                   greeting: str,
                   def_greeting: str = 'hello',
                   *,
                   kw_farewell: str,
                   def_farewell: str = 'bye',
                   ) -> tuple:
    return (
        pos_greeting,
        greeting,
        def_greeting,
        kw_farewell,
        def_farewell,
    )

def argskwargs_func(pos_param: Any,
                    /,
                    def_arg: str = 'bye',
                    *args: Any,
                    kw_param: Any,
                    def_kw_param: Any = 'hello',
                    **kwargs: Any) -> tuple:
    return pos_param, def_arg, args, kw_param, def_kw_param, kwargs


def edge_func1(pos_param,
               def_pos_param='def_pos_param',
               /,
               *args) -> tuple:
    return pos_param, def_pos_param, args

# fixtures

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

# tests

def test_decospector():
    pos_param = 1
    args1, args2, args3 = 2, 'abc', [1, 2, 3]
    kw_param = 'keyword_here, hello'
    kwargs_param = {'hi': [4, 4, 4], 'bye': {2, 3, 5}, 'hello': True}

    kw = decospector(argskwargs_func,
                     pos_param,
                     args1,
                     args2,
                     args3,
                     kw_param=kw_param,
                     **kwargs_param)
    assert 'args' not in kw and 'kwargs' not in kw
    assert kw['pos_param'] == pos_param
    assert kw['def_arg'] == 'bye'
    assert kw['kw_param'] == 'keyword_here, hello'
    assert kw['def_kw_param'] == 'hello'
    assert kw['args0'] == 2
    assert kw['args1'] == 'abc'
    assert kw['args2'] == [1, 2, 3]
    assert kw['hi'] == [4, 4, 4]
    assert kw['bye'] == {2, 3, 5}
    assert kw['hello'] is True


def test_safe_decospector(safe_argskwargs):
    pos_param = 1
    pos, nonpos = safe_argskwargs()
    assert 'args' not in nonpos and 'kwargs' not in nonpos
    assert pos['pos_param'] == pos_param
    assert pos['def_arg'] == 'bye'
    assert nonpos['kw_param'] == 'keyword_here, hello'
    assert nonpos['def_kw_param'] == 'hello'
    assert pos['args0'] == 2
    assert pos['args1'] == 'abc'
    assert pos['args2'] == [1, 2, 3]
    assert nonpos['hi'] == [4, 4, 4]
    assert nonpos['bye'] == {2, 3, 5}
    assert nonpos['hello'] is True


def test_decospector_with_all_params_func():
    pos_greet, greet, kw_farewell = 1, True, 'byebye'
    kw = decospector(all_param_func, pos_greet, greet, kw_farewell=kw_farewell)
    assert kw['pos_greeting'] == pos_greet
    assert kw['greeting'] == greet
    assert kw['def_greeting'] == 'hello'
    assert kw['kw_farewell'] == kw_farewell
    assert kw['def_farewell'] == 'bye'


def test_safecode():
    # check truthy/falsy
    assert not SafeCode.POSITIONAL
    assert SafeCode.NONPOSITIONAL


def test_safe_decospector_manual_mutation(safe_argskwargs):
    positionals, remaining_keywords = safe_argskwargs()

    # mutate
    positionals['pos_param'] = 'hello'

    # put back into original function
    pos_param, *_ = argskwargs_func(*positionals, **remaining_keywords)
    assert pos_param == 'hello'


def test_safe_decospector_find_param_fails(safe_argskwargs):
    with pytest.raises(KeyError) as key_err:
        safe_argskwargs.find_param('does_not_exist')


@pytest.mark.parametrize('param, expect_code, expect_value', [
    ('pos_param', SafeCode.POSITIONAL, 1),
    ('def_arg', SafeCode.POSITIONAL, 'bye'),
    ('kw_param', SafeCode.NONPOSITIONAL, 'keyword_here, hello'),
    ('args1', None, 'abc'),
])
def test_safe_decospector_find_param(param, expect_code, expect_value, safe_argskwargs):
    if expect_code is not None:
        code, value = safe_argskwargs.find_param(param, get_code=True)
        assert code == expect_code
    else:
        value = safe_argskwargs.find_param(param)
    assert value == expect_value


@pytest.mark.parametrize('param, new_value', [
    ('pos_param', 'yoyoyo'),
    ('def_kw_param', 'hohoho'),
])
def test_safe_decorator_mutate(param, new_value, safe_argskwargs):
    code = safe_argskwargs.mutate(param, new_value)
    positionals, remaining_kwargs = safe_argskwargs()

    if code == SafeCode.POSITIONAL:
        assert positionals[param] == new_value
    else:
        assert remaining_kwargs[param] == new_value
