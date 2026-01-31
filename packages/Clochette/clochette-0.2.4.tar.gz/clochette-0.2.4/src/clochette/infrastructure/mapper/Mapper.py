from dataclasses import fields, is_dataclass
from typing import TypeVar, Type, Any

_TOut = TypeVar("_TOut")


class Mapper:
    """Generic object mapper that maps fields from one type to another."""

    def map(
        self,
        type_out: Type[_TOut],
        obj: object,
        **kwargs: Any,
    ) -> _TOut:
        # Ensure type_out is a dataclass
        if not is_dataclass(type_out):
            raise TypeError(f"type_out must be a dataclass, got {type_out}")

        # Get all fields from the target type
        target_fields = fields(type_out)  # type: ignore[arg-type]

        # Build constructor arguments
        constructor_args = {}

        for field in target_fields:
            field_name = field.name

            # Try to get value from source object
            if hasattr(obj, field_name):
                constructor_args[field_name] = getattr(obj, field_name)
            # Otherwise use kwargs
            elif field_name in kwargs:
                constructor_args[field_name] = kwargs[field_name]
            else:
                raise ValueError(
                    f"Field '{field_name}' is missing in source object and not provided in kwargs. "
                    f"Available kwargs: {list(kwargs.keys())}"
                )

        # Create and return the new instance
        return type_out(**constructor_args)
