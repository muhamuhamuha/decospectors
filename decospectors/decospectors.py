import inspect
import re
from collections import defaultdict
from typing import (
    Any,
    Callable,
    Generator,
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
                     **kwargs: Any) -> PargsKwargs:
    """
    Parameters
    ----------

    Returns
    -------
    PargsKwargs
        A tuple of two dictionaries that are meant to be unpacked.
    """
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

    def get(param: str,
            get_code: bool = False,
            ) -> tuple[SafeCode, dict] | dict | NoReturn:
        if param in self.check_param_kinds('VAR_') and _enumerate_varargs_:
            vals = {p: pos[p] for p in pos.keys() if p.startswith(vararg_param)}
            return (SafeCode.VARARG, vals) if get_code else vals

        elif param in pos.keys():
            vals = {param: pos[param]}
            return (SafeCode.POSITIONAL, vals) if get_code else vals

        elif param in nonpos.keys():
            vals = {param: nonpos[param]}
            return (SafeCode.NONPOSITIONAL, vals) if get_code else vals

        else:
            raise KeyError(f'"{param}" param does not exist. Available params: '
                           f"{list(pos.keys())}, {list(nonpos.keys())}")

    def mutate(param: str,
               new_value: Any | Callable,
               apply: bool = False) -> SafeCode | NoReturn:
        code, values = get(param, get_code=True)

        if code == SafeCode.POSITIONAL:
            pos[param] = new_value if not apply else new_value(values[param])

        elif code == SafeCode.VARARG and not apply:
            # check lengths match
            try:
                for i, args_param in enumerate(values.keys()):
                    pos[args_param] = new_value[i]
                # this raised UnboundLocalError for some reason:
                # pos |= dict(zip(values, new_value))
            except IndexError as e:
                error_msg = (f'Given {len(new_value)} new_values but '
                             f'{len(values)} must be mutated.')
                raise IndexError(error_msg).with_traceback(e.__traceback__)

        elif code == SafeCode.VARARG and apply:
            for args_param, args_value in values.items():
                pos[args_param] = new_value(args_value)

        else:
            nonpos[param] = new_value if not apply else new_value(values)

        return code

    context.find_param = get
    context.mutate = mutate
    return context
