import inspect
import re
from collections import defaultdict
from functools import update_wrapper
from typing import (
    Any,
    Callable,
    Generator,
    Literal,
    NamedTuple,
    NoReturn,
    Optional,
    Union,
)

from .utils import (
    ValuesDict,
    PargsKwargs,
    SafeCode,
)


class _Decospector:

    def __init__(self,
                 func: Callable,
                 *args: Any,
                 **kwargs: Any) -> None:
        self._func = func
        self._args = args
        self._kwargs = kwargs

        # categorizing parameters
        self.sig = inspect.signature(func)
        self.params = self.sig.parameters

        # mapping arguments to their parameter names
        self.binding = self.sig.bind(*args, **kwargs)
        self.binding.apply_defaults()
        self.mapped_args = self.binding.arguments.copy()

    def expect_forced_params(self) -> bool:
        return any(
            param_kind.endswith('_ONLY')
            for param_kind in
            [self.params[p].kind.name for p in self.params]
        )

    def get_positional_params(self,
                              kind: Literal['POSITIONAL', 'POSITIONAL_ONLY']
                              ) -> list[str]:
        return [p for p in self.params
                if self.params[p].kind.name == kind]

    def map_args_to_params(self,
                           preserve_positional_defaults: bool = True,
                           enumerate_varargs: Optional[str] = 'args',
                           merge_varkwargs: Optional[str] = 'kwargs',
                           ) -> dict[str, Any]:
        empty = inspect.Parameter.empty
        args, kwargs, sig, params, mapped_args = self._get_attributes()

        pos_params = {p: params[p].default for p in
                      filter(lambda _: 'POSITIONAL' in params[_].kind.name, params)
                      if p != enumerate_varargs}
        # three conditions
        # 1. user wants to override python default behavior
        if ( preserve_positional_defaults
             # 2. positional defaults have been given
             and any( filter(lambda _: _ is not empty, pos_params) )
             # 3. variadic arguments given
             and 'VAR_POSITIONAL' in [params[p].kind.name for p in params] ):

            resolved = defaultdict(list)
            for i, param in enumerate(pos_params.keys()):
                if (value := pos_params[param]) is not None:
                    resolved[param] = value
                else:
                    resolved[param] = args[i]

            resolved[enumerate_varargs] += args[i:]  # remaining args
            # modify kwargified in place with defaults
            mapped_args = {
                kw: default_value
                if kw in resolved.keys()
                and (default_value := resolved[kw]) is not empty
                else keep_kwargified_value
                for kw, keep_kwargified_value in mapped_args.items()
            }

        for expected in (enumerate_varargs, merge_varkwargs):
            if not expected or expected not in mapped_args:
                continue

            values = mapped_args.pop(expected)
            mapped_args |= (
                {f'{expected}{i}': val for i, val in enumerate(values)}  # args
                 if not isinstance(values, dict) else
                values  # kwargs
            )
        return mapped_args

    def _get_attributes(self) -> Generator:
        return_props = (self._args,
                        self._kwargs,
                        self.sig,
                        self.params,
                        self.mapped_args)
        return (prop for prop in return_props)


def decospector(func: Callable,
                *args: Any,
                _preserve_positional_defaults_: bool = True,
                _enumerate_varargs_: Optional[str] = 'args',
                _merge_varkwargs_: Optional[str] = 'kwargs',
                **kwargs: Any,
                ) -> dict[str, Any]:
    self = _Decospector(func, *args, **kwargs)
    return self.map_args_to_params(_preserve_positional_defaults_,
                                   _enumerate_varargs_,
                                   _merge_varkwargs_)


def safe_decospector(func: Callable,
                     *args: Any,
                     _preserve_positional_defaults_: bool = True,
                     _enumerate_varargs_: Optional[str] = 'args',
                     _merge_varkwargs_: Optional[str] = 'kwargs',
                     **kwargs: Any) -> tuple[ValuesDict, dict]:
    self = _Decospector(func, *args, **kwargs)
    params = self.params
    mapped_args = self.map_args_to_params(_preserve_positional_defaults_,
                                          _enumerate_varargs_,
                                          _merge_varkwargs_)

    if not self.expect_forced_params():
        pos, nonpos = PargsKwargs({}, mapped_args)

    else:
        _positionals = {param: mapped_args[param]
                        for param in self.get_positional_params('POSITIONAL_ONLY')}
        _remaining_kwargs = {k: v
                             for k, v in mapped_args.items()
                             if k not in _positionals}

        pos, nonpos = PargsKwargs(ValuesDict(**_positionals), _remaining_kwargs)

    # add default positional arguments and variadic arguments to positionals dict
    varargs = [match.group() for arg in mapped_args
               if (match := re.match(f'{_enumerate_varargs_}\\d+', arg))]
    if ( _preserve_positional_defaults_ and
         any(varargs) ):
        for param in self.get_positional_params('POSITIONAL_OR_KEYWORD'):
            pos[param] = nonpos.pop(param)  # saving defaults
        for vararg in varargs:
            pos[vararg] = nonpos.pop(vararg)

    def context() -> PargsKwargs: return PargsKwargs(pos, nonpos)

    def find_param(param: str,
                   get_code: bool = False,
                   ) -> Union[Union[tuple[SafeCode, Any], Any], NoReturn]:
        if param in pos.keys():
            return (
                (SafeCode.POSITIONAL, pos[param])
                if get_code else
                pos[param]
            )

        elif param in nonpos.keys():
            return (
                (SafeCode.NONPOSITIONAL, nonpos[param])
                if get_code else
                nonpos[param]
            )

        else:
            raise KeyError(f'"{param}" param does not exist. Available params: '
                           f"{list(pos.keys())}, {list(nonpos.keys())}")

    def mutate(param: str, new_value: Any) -> Union[SafeCode, NoReturn]:
        code, _ = find_param(param, get_code=True)

        if code == SafeCode.POSITIONAL:
            pos[param] = new_value
        else:
            nonpos[param] = new_value
        return code

    context.find_param = find_param
    context.mutate = mutate
    return context
