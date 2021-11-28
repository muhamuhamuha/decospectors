import inspect
from typing import Any, Callable


class Inspector:
    """A namespace for converting a functions parameters and arguments
    into a dictionary.
    """

    def __init__(self,
                 func: Callable,
                 *args: Any,
                 **kwargs: Any,
                 ) -> None:
        self._f = func
        self.args = list(args)
        self.kwargs = kwargs
        self.params = inspect.signature(func).parameters

    def kwargify(self) -> dict:
        """Maps parameter names to their argument- or default-values. Only maps
        parameters that weren't passed as keywords."""
        return {param: self.get_safe_default(param)
                for param in self.params if param not in self.kwargs}

    def get_safe_default(self, param: Any) -> Any:
        """Returns the default value of the given parameter if a default exists
        otherwise returns the argument.
        """
        return (
            self.get_arg(param)
            if self.defaultless(param) else
            self.get_default(param)
        )

    def get_default(self, param: str) -> Any:
        """Returns the default argument of the specified parameter."""
        return self.params[param].default

    def defaultless(self, param: str) -> bool:
        """Checks if the given parameter has a default value."""
        return self.params[param].default is inspect.Parameter.empty

    def get_arg(self, param: str) -> Any:
        """Returns the argument of the specified parameter from the passed args."""
        params = list(self.params)
        return self.args[params.index(param)]

    def is_keyword_only(self, param: str) -> bool:
        """Checks if the given parameter can only be passed as a keyword."""
        return self.params[param].kind.name == 'KEYWORD_ONLY'

    def is_positional_only(self, param: str) -> bool:
        """Checks if the given parameter can only be passed positionally."""
        return self.params[param].kind.name == 'POSITIONAL_ONLY'

    def no_forced_params(self) -> bool:
        """Returns True if no positional- or keyword-only parameters in given function."""
        param_kinds = {p: self.params[p].kind.name for p in self.params}
        return not any(v.endswith('_ONLY') for v in param_kinds.values())
