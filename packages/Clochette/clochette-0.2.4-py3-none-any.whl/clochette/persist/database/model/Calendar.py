from dataclasses import dataclass
from datetime import datetime, UTC

from peewee import AutoField

from clochette.persist.database.field.DateTimeField import DateTimeField
from clochette.persist.database.model.BaseModel import BaseModel


class Calendar(BaseModel):
    id = AutoField()
    last_download = DateTimeField(default=datetime.now(tz=UTC))


@dataclass(frozen=True, eq=True)
class CalendarDTO:
    id: str
    last_download: datetime
