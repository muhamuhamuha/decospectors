import pytest
from typing import Any

from decospector.decospector import ValuesDict


def test_valuesdict_iterates_over_values():
    mock_dict = dict(name='anakin skywalker', age=2)

    name, age = ValuesDict(**mock_dict)
    assert name == 'anakin skywalker'
    assert age == 2


