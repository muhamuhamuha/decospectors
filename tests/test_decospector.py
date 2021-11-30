import re
import pytest
import itertools as it
from inspect import cleandoc
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
])
def test_safe_decospector_find_param(param, expect_code, expect_value, safe_decospector):
    code, value = safe_decospector.find_param(param)

    assert code == expect_code
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


# trying to make a bunch of tests
# def mock_builder(forced_positionals: bool,
#                  forced_keywords: bool,
#                  default_positionals: bool,
#                  default_keywords: bool,
#                  ) -> Callable:
#
#     func_blueprint = '''
#         @decor_for_decospector
#         def mock_func():
#             return
#     '''
#
#     mocks = []
#     if forced_positionals:
#         mocks += ['frc_pos: str, /']
#     if default_positionals:
#         mocks += ['def_pos: str = "default positional"']
#     if forced_keywords:
#         mocks += ['*, frc_key: str']
#     if default_keywords:
#         mocks += ['def_key: str = "default keyword"']
#
#     mock_signature = ','.join(mocks)
#     # REGEX: extract any word followed by a colon into a list
#     mock_params = ','.join( re.findall(r'\w+(?=:)', mock_signature) )
#
#     # amend call signature and return statement
#     func_blueprint = (
#         func_blueprint
#             .replace('()', f'({mock_signature})' if mock_signature else '()')
#             .replace('return', f'return {mock_params}' if mock_params else 'return')
#     )
#
#     exec(cleandoc(func_blueprint))
#     return locals()['mock_func']
#
#
# # itertools product will yield all possible combinations of True, False
# # from [False, False, False, False] to [True, True, True, True]
# inputs_outputs = [
#     list(truth_table) + ['1', dict(frc_key='2'), 'default positional', 'default keyword']
#     for truth_table in it.product([True, False], repeat=4)
# ]
# params = (
#     'forced_positionals, '
#     'forced_keywords, '
#     'default_positionals, '
#     'default_keywords, '
#     'frc_pos_input, '
#     'frc_key_input, '
#     'def_pos_output, '
#     'def_key_output '
# )
# @pytest.mark.parametrize(params, inputs_outputs)
# def test_decospector(forced_positionals,
#                      forced_keywords,
#                      default_positionals,
#                      default_keywords,
#                      frc_pos_input,
#                      frc_key_input,
#                      def_pos_output,
#                      def_key_output):
#     def decor_for_decospector(f: Callable) -> Callable:
#         @wraps(f)
#         def inner(*args, **kwargs) -> dict:
#
#             return decospectors(f, *args, **kwargs)
#         return inner
#
#     mock_func = mock_builder(forced_positionals,
#                              forced_keywords,
#                              default_positionals,
#                              default_keywords)
#
#     # apply decorator
#     mock_func = decor_for_decospector(mock_func)
#     inputs =
#     keywords = mock_func()
