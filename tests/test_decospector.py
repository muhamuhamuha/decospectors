import pytest
from functools import partial, wraps
from typing import Callable

from decospectors.decospectors import (
    SafeCode,
    decospector,
    SafeDecospector
)


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

# fixtures

@pytest.fixture
def safe_decospector():
    # apply decorator
    get_safe = get_keywords(all_param_func, safe=True)
    # decorator will now return SafeDecorator class
    return get_safe('moshimoshi', 'heya', kw_farewell='bye bye')


# tests

def test_decospector_with_all_param_kinds():
    pgreet, greet, kfarewell = 'moshimoshi', 'heya', 'bye bye'
    get_kwargs = get_keywords(all_param_func)  # applying decorator
    kw = get_kwargs(pgreet, greet, kw_farewell=kfarewell)
    # make sure keywords all line up
    assert kw['pos_greeting'] == pgreet
    assert kw['greeting'] == greet
    assert kw['def_greeting'] == 'hello'
    assert kw['kw_farewell'] == kfarewell
    assert kw['def_farewell'] == 'bye'


def test_safecode():
    # check truthy/falsy
    assert not SafeCode.POSITIONAL
    assert SafeCode.NONPOSITIONAL


def test_safe_decospector_assignment(safe_decospector):
    positionals, remaining_keywords = safe_decospector
    # values laid out correctly
    assert positionals['pos_greeting'] == 'moshimoshi'
    assert remaining_keywords['greeting'] == 'heya'
    assert remaining_keywords['def_greeting'] == 'hello'
    assert remaining_keywords['def_farewell'] == 'bye'
    assert remaining_keywords['kw_farewell'] == 'bye bye'


def test_safe_decospector_manual_mutation(safe_decospector):
    positionals, remaining_keywords = safe_decospector

    # mutate
    positionals['pos_greeting'] = 'yoyoyo'

    # put back into original function
    p1, p2, p3, p4, p5 = all_param_func(*positionals, **remaining_keywords)
    assert p1 == 'yoyoyo'
    assert p2 == 'heya'
    assert p3 == 'hello'
    assert p4 == 'bye bye'
    assert p5 == 'bye'


def test_safe_decospector_find_param_fails(safe_decospector):
    with pytest.raises(KeyError) as key_err:
        safe_decospector.find_param('does_not_exist')


@pytest.mark.parametrize('param, expect_code, expect_value', [
    ('pos_greeting', SafeCode.POSITIONAL, 'moshimoshi'),
    ('def_greeting', SafeCode.NONPOSITIONAL, 'hello'),
    ('greeting', None, 'heya'),
])
def test_safe_decospector_find_param(param, expect_code, expect_value, safe_decospector):
    if expect_code is not None:
        code, value = safe_decospector.find_param(param, get_code=True)
        assert code == expect_code
    else:
        value = safe_decospector.find_param(param)
    assert value == expect_value


@pytest.mark.parametrize('param, new_value', [
    ('pos_greeting', 'yoyoyo'),
    ('def_greeting', 'hohoho'),
])
def test_safe_decorator_mutate(param, new_value, safe_decospector):
    code = safe_decospector.mutate(param, new_value)
    positionals, remaining_kwargs = safe_decospector

    if code == SafeCode.POSITIONAL:
        assert positionals[param] == new_value
    else:
        assert remaining_kwargs[param] == new_value
