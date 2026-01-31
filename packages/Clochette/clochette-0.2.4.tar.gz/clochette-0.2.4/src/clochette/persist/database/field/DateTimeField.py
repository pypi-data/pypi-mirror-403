from datetime import datetime

from peewee import Field


class DateTimeField(Field):
    field_type = "text"

    def db_value(self, value: datetime) -> str:
        return value.isoformat()

    def python_value(self, value: str) -> datetime:
        return datetime.fromisoformat(value)
