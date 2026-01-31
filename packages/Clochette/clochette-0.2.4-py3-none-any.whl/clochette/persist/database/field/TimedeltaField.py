from datetime import timedelta

from peewee import Field


class TimedeltaField(Field):
    field_type = "float"

    def db_value(self, value: timedelta) -> float:
        return value.total_seconds()

    def python_value(self, value: float) -> timedelta:
        return timedelta(seconds=value)
