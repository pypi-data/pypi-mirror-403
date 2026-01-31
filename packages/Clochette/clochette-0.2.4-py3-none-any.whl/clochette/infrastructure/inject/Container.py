import inspect
from typing import Type, get_type_hints, TypeVar, Any, get_origin

from clochette import log

_T = TypeVar("_T")


class Container:
    _container: dict[Type, Any]

    def __init__(self):
        self._container = {}

    def instantiate(self, cls: Type[_T]) -> _T:

        instance = self._container.get(cls, None)
        if instance is not None:
            return instance

        cls = self._get_class_without_generic(cls)
        if inspect.isclass(cls):
            if inspect.isabstract(cls):
                raise Exception(f"Cannot instantiate abstract class: {cls}")
        else:
            raise Exception(f"Cannot instantiate type: {cls}")

        # Get the __init__ method of the class
        init_method = cls.__init__

        # Get the signature of the __init__ method
        signature = inspect.signature(init_method)

        # Extract the parameters
        parameters = signature.parameters

        # Get the type hints for the parameters
        type_hints = get_type_hints(init_method)

        # Create a dictionary to store parameter names, their types, and instances
        kwargs = {}

        for param_name, param in parameters.items():
            # Skip 'self' parameter
            if param_name == "self":
                continue

            # Skip *args and **kwargs based on parameter kind
            if param.kind == param.VAR_POSITIONAL or param.kind == param.VAR_KEYWORD:
                continue

            # skip parameter with default values
            if param.default is not inspect.Parameter.empty:
                continue

            # Get the type of the parameter from type hints
            param_type = type_hints.get(param_name, inspect.Parameter.empty)

            param_type = self._get_class_without_generic(param_type)

            if inspect.isclass(param_type):
                if inspect.isabstract(param_type):
                    raise Exception(f"Cannot instantiate abstract class: {param_type}, class {cls}")
            else:
                raise Exception(f"Cannot instantiate type: {param_type}, class {cls}")

            kwargs[param.name] = self.instantiate(param_type)

        try:
            instance = cls(**kwargs)
        except Exception:
            log.error("You might want to make your class mutable if you encounter this issue", exc_info=True)
            raise

        self._container[cls] = instance
        return instance

    def inject(self, type: Type[_T], instance: _T):
        self._container[type] = instance

    def _get_class_without_generic(self, param_type: Any):
        origin = get_origin(param_type)
        if origin is not None:
            return origin

        return param_type
