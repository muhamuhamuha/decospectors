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
        self.param_kinds = defaultdict(list)
        for p in self.params:
            param_kind = self.params[p].kind.name
            self.param_kinds[param_kind].append(p)

        # mapping arguments to their parameter names
        self.binding = self.sig.bind(*args, **kwargs)
        self.binding.apply_defaults()
        self.mapped_args = self.binding.arguments.copy()

    def check_param_kinds(self, check_word: str) -> list[str]:
        matching_params = [self.param_kinds[k] for k in self.param_kinds.keys()
                           if check_word in k]
        # flatten that list
        return [param for sublist in matching_params for param in sublist]

    def unload_args(self, preserve_defaults: bool) -> dict:
        params, mapped_args, args = self.params, self.mapped_args, list(self._args)
        try:
            vararg_param, = self.param_kinds['VAR_POSITIONAL']
        except ValueError:
            # nothing to unload!
            return mapped_args
        empty = inspect.Parameter.empty

        unloading_params = {p: params[p].default
                            for p in self.check_param_kinds('POSITIONAL')
                            if p != vararg_param}

        unloaded = defaultdict(list)
        # all positional args are loading varargs, so they will be unpacked
        for i, (param, def_value) in enumerate(unloading_params.items()):
            if def_value is not empty and preserve_defaults:
                # keep default value
                unloaded[param] = def_value
            else:
                unloaded[param] = args[i]  # pop from varargs

        unloaded[vararg_param] += args[i:]  # unpack remaining varargs
        return {
            kw: unloaded[kw]
            if kw in unloaded.keys() else keep_kwargified_value
            for kw, keep_kwargified_value in mapped_args.items()
        }

    def map_args_to_params(self,
                           preserve_positional_defaults: bool = True,
                           enumerate_varargs: Optional[str] = 'args',
                           merge_varkwargs: Optional[str] = 'kwargs',
                           ) -> dict[str, Any]:
        empty = inspect.Parameter.empty
        args, kwargs, sig, params, mapped_args = self._get_attributes()

        mapped_args = self.unload_args(preserve_positional_defaults)

        # enumerate varargs or merge varkwargs
        for expectation in (enumerate_varargs, merge_varkwargs):
            if not expectation or expectation not in mapped_args:
                continue

            values = mapped_args.pop(expectation)
            mapped_args |= (
                {f'{expectation}{i}': val for i, val in enumerate(values)}  # args
                 if not isinstance(values, dict) else
                values  # kwargs
            )
        return mapped_args

    def _get_attributes(self) -> Generator:
        return_props = (list(self._args),
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
    mapped_args = self.map_args_to_params(_preserve_positional_defaults_,
                                          _enumerate_varargs_,  # don't enumerate args
                                          _merge_varkwargs_)

    pos: ValuesDict
    nonpos: dict
    if not self.check_param_kinds('_ONLY'):
        pos, nonpos = PargsKwargs({}, mapped_args)

    else:
        pos = {param: mapped_args[param]
               for param in self.param_kinds['POSITIONAL_ONLY']}
        nonpos = {k: v for k, v in mapped_args.items() if k not in pos}

    # move default arguments to positionals dict
    if _preserve_positional_defaults_:
        for param in self.check_param_kinds('POSITIONAL_OR_KEYWORD'):
            pos[param] = nonpos.pop(param)

    # move from keywords dict to positionals dict
    try:
        vararg_param, = self.check_param_kinds('VAR_POS')
        varargs = [match.group() for arg in mapped_args
                   if (match := re.match(f'{vararg_param}\\d+', arg))]

        for vararg in varargs:
            pos[vararg] = nonpos.pop(vararg)

    except ValueError:
        # no varargs!
        pass

    def context() -> PargsKwargs:
        """"""
        return PargsKwargs(ValuesDict(**pos), nonpos)

    def find_param(param: str,
                   get_code: bool = False,
                   ) -> tuple[SafeCode, Any | list] | Any | list | NoReturn:
        if param in self.check_param_kinds('VAR_') and _enumerate_varargs_:
            _args = [p for p in pos.keys() if p.startswith(vararg_param)]
            return (SafeCode.VARARG, _args) if get_code else _args

        elif param in pos.keys():
            return (SafeCode.POSITIONAL, pos[param]) if get_code else pos[param]

        elif param in nonpos.keys():
            return (SafeCode.NONPOSITIONAL, nonpos[param]) if get_code else nonpos[param]

        else:
            raise KeyError(f'"{param}" param does not exist. Available params: '
                           f"{list(pos.keys())}, {list(nonpos.keys())}")

    def mutate(param: str, new_value: Any) -> SafeCode:
        code, found_param = find_param(param, get_code=True)

        if code == SafeCode.POSITIONAL:
            pos[param] = new_value

        elif code == SafeCode.VARARG:
            for i, param in enumerate(found_param):
                pos[param] = new_value[i]
            # this raised UnboundLocalError for some reason:
            # pos |= dict(zip(found_param, new_value))

        else:
            nonpos[param] = new_value
        return code

    context.find_param = find_param
    context.mutate = mutate
    return context
