from dataclasses import dataclass
from datetime import datetime, date

from peewee import AutoField, TextField

from clochette.persist.database.field.DateOrTimeField import DateOrTimeField
from clochette.persist.database.field.DateTimeField import DateTimeField
from clochette.persist.database.model.BaseModel import BaseModel


class Snooze(BaseModel):
    id = AutoField()
    calendar_id = TextField(null=False)
    event_uid = TextField(null=False)

    trigger = DateTimeField(null=False)
    trigger_start = DateOrTimeField(null=False)


@dataclass(frozen=True, eq=True)
class SnoozeDTO:
    id: int
    event_uid: str
    calendar_id: str

    trigger: datetime
    trigger_start: date | datetime
