from datetime import datetime, date

from peewee import Field


class DateOrTimeField(Field):
    field_type = "text"

    def db_value(self, value: date | datetime | None) -> str | None:
        if not value:
            return None
        return value.isoformat()

    def python_value(self, value: str | None) -> datetime | date | None:
        if not value:
            return None
        if "T" in value:
            return datetime.fromisoformat(value)
        else:
            return date.fromisoformat(value)
