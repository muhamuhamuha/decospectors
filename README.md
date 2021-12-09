# Decospectors: simplifying function introspection inside decorators

## Usage

```python
# for simple inspection
from decospectors import decospector

# when mutating in place
from decospectors import SafeDecospector
```

## Installation

Add the following to your requirements.txt file:

`git+git://github.com/muhamuhamuha/decospectors.git@main#egg=decospectors`

Then run the following from a terminal:

```shell
pip install -r requirements.txt
```

## TODOs

* test when user gives varargs and wants to mutate them
* test when user gives varkwargs and wants to mutate them
* in decospector, varargs will overwrite positional defaults when 
preserve positional defaults is true but varargs are not specified
* hello
