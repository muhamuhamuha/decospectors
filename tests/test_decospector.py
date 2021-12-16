import pytest
from typing import Any

from decospectors.decospectors import (
    decospector,
    safe_decospector,
)
from decospectors.utils import SafeCode
from tests.conftest import argskwargs_func


# psuedo-fixtures

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


def edge_func1(pos_param,
               def_pos_param='def_pos_param',
               /,
               *args) -> tuple:
    return pos_param, def_pos_param, args


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


@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decospector(safe_argskwargs):
    pos_param = 1
    pos, nonpos = safe_argskwargs()
    assert any([k.startswith('args') for k in pos.keys()])  # they should be enumerated
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


@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decospector_get_value(safe_argskwargs):
    assert safe_argskwargs.get_value('pos_param') == 1
    assert safe_argskwargs.get_value('args') == [2, 'abc', [1, 2, 3]]


@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decospector_manual_mutation(safe_argskwargs):
    positionals, remaining_keywords = safe_argskwargs()

    # mutate
    positionals['pos_param'] = 'hello'

    # put back into original function
    pos_param, *_ = argskwargs_func(*positionals, **remaining_keywords)
    assert pos_param == 'hello'


@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decospector_get_fails(safe_argskwargs):
    with pytest.raises(KeyError) as key_err:
        safe_argskwargs.get('does_not_exist')


@pytest.mark.parametrize('param, expect_code, expect_value', [
    ('pos_param', SafeCode.POSITIONAL, 1),
    ('def_arg', SafeCode.POSITIONAL, 'bye'),
    ('kw_param', SafeCode.NONPOSITIONAL, 'keyword_here, hello'),
    ('args1', SafeCode.POSITIONAL, 'abc'),
    ('args', SafeCode.VARARG, {'args0': 2, 'args1': 'abc', 'args2': [1, 2, 3]}),
])
@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decospector_get(param, expect_code, expect_value, safe_argskwargs):
    if expect_code is not None:
        code, value = safe_argskwargs.get(param, get_code=True)
        assert code == expect_code
    else:
        value = safe_argskwargs.get(param)

    if expect_code is SafeCode.VARARG:
        assert value == expect_value

    else:
        assert value[param] == expect_value


@pytest.mark.parametrize('param, new_value', [
    ('pos_param', 'yoyoyo'),
    ('def_kw_param', 'hohoho'),
    ('args0', 'new_args0'),  # should be treated as a positional
    ('args', ['a', 'b', 'c']),
    ('def_kw_param', lambda x: x + 2),
])
@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decorator_mutate_without_apply(param, new_value, safe_argskwargs):

    code = safe_argskwargs.mutate(param, new_value)
    positionals, remaining_kwargs = safe_argskwargs()

    if code == SafeCode.POSITIONAL:
        assert positionals[param] == new_value

    elif code == SafeCode.VARARG:
        _args = safe_argskwargs.get(param)
        for i, _arg in enumerate(_args.keys()):
            assert positionals[_arg] == new_value[i]

    else:
        assert remaining_kwargs[param] == new_value


@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decorator_mutate_raises_index_error(safe_argskwargs):
    with pytest.raises(IndexError) as i_err:
        safe_argskwargs.mutate('args', [1, 2])


@pytest.mark.parametrize('param, func', [
    ('args', lambda x: x * 2),
    ('pos_param', lambda x: x + 2),
    ('kw_param', lambda x: f'{x}||{x}'),
])
@pytest.mark.usefixtures('safe_argskwargs')
def test_safe_decorator_mutate_with_apply(param, func, safe_argskwargs):
    before_mut = safe_argskwargs.get(param).copy()

    safe_argskwargs.mutate(param, func, True)

    after_mut = safe_argskwargs.get(param)

    assert all(after_mut[k] == func(before_mut[k]) for k in after_mut.keys())

