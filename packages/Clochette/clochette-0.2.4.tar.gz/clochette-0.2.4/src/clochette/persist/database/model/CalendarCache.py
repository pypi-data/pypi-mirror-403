from dataclasses import dataclass

from peewee import TextField

from clochette.persist.database.model.BaseModel import BaseModel


class CalendarCache(BaseModel):
    calendar_id = TextField(primary_key=True, null=False)
    content = TextField(null=False)

    class Meta:  # pyright: ignore [reportIncompatibleVariableOverride]
        table_name = "calendar_cache"


@dataclass(frozen=True, eq=True)
class CalendarCacheDTO:
    calendar_id: str
    content: str
