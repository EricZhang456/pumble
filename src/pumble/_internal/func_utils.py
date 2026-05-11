import inspect
from collections.abc import Callable


def get_required_params_for_func(func: Callable) -> dict[str, inspect.Parameter]:
    return {
        name: param for name, param in inspect.signature(func).parameters.items()
        if param.default is param.empty
        and param.kind not in {param.VAR_POSITIONAL, param.VAR_KEYWORD}
    }
