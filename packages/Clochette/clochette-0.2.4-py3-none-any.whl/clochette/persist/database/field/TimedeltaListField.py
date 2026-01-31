from datetime import timedelta

from peewee import Field


class TimedeltaListField(Field):
    field_type = "text"

    def db_value(self, value: list[timedelta] | None) -> str | None:
        if not value:
            return None
        seconds_list = map(lambda td: str(td.total_seconds()), value)
        return ";".join(seconds_list)

    def python_value(self, value: str | None) -> list[timedelta] | None:
        if not value:
            return None
        seconds_list = value.split(";")
        return [timedelta(seconds=float(seconds)) for seconds in seconds_list]
