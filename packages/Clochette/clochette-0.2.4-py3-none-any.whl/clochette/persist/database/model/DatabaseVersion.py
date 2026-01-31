from dataclasses import dataclass
from datetime import datetime, UTC

from peewee import AutoField, TextField

from clochette.persist.database.field.DateTimeField import DateTimeField
from clochette.persist.database.model.BaseModel import BaseModel


class DatabaseVersion(BaseModel):
    id = AutoField()
    version = TextField(null=False)
    applied_on = DateTimeField(null=False, default=datetime.now(tz=UTC))

    class Meta:  # pyright: ignore [reportIncompatibleVariableOverride]
        table_name = "database_version"


@dataclass(frozen=True, eq=True)
class DatabaseVersionDTO:
    id: int
    version: str
    applied_on: datetime
