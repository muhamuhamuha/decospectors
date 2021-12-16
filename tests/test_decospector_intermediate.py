import pytest

from decospectors import safe_decospector

def mock_func1(*args, **kwargs) -> tuple[tuple, dict]:
    """This function has varargs but no positionals that it accepts before them."""
    return args, kwargs


def test_mock_func1():

    dspector = safe_decospector(mock_func1, 'hello', 1, 2, hi='hello there')
    dspector.mutate('hi', 123)
    assert dspector.get('args') == {'args0': 'hello', 'args1': 1, 'args2': 2}
    assert dspector.get('hi') == {'hi': 123}
    pos, nonpos = dspector()
    args, kwargs = mock_func1(*pos, **nonpos)
    assert args[0] == 'hello'
