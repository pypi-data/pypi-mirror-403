from peewee import Model

from clochette.persist import db


class BaseModel(Model):
    class Meta:
        database = db
