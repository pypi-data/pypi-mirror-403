from datetime import datetime, date, time, tzinfo, UTC
from typing import TypeGuard

import humanize
from babel.dates import format_time, format_date

from clochette.infrastructure.clock.Generics import DateOrDatetimeType


class DateTimeUtils:
    @staticmethod
    def to_datetime(value: date, tz: tzinfo | None = None) -> datetime:
        date_time = datetime.combine(value, time(hour=0, minute=0, second=0, microsecond=0))
        return DateTimeUtils.set_tz(date_time, tz)

    @staticmethod
    def set_tz(date_time: datetime, tz: tzinfo | None = UTC) -> datetime:
        if not tz:
            return date_time.astimezone(None).replace(tzinfo=None)
        if date_time.tzinfo:
            return date_time
        else:
            return date_time.astimezone(tz)

    @staticmethod
    def normalize_tz(tzinfo: tzinfo | None, to_normalize: list[datetime]) -> list[datetime]:
        return list(map(lambda x: DateTimeUtils.set_tz(x, tzinfo), to_normalize))

    @staticmethod
    def format_date_natural(value: date) -> str:
        return humanize.naturalday(value)

    @staticmethod
    def format_time_locale(value: datetime) -> str:
        return format_time(value, format="short")

    @staticmethod
    def format_date_time_locale(value: datetime) -> str:
        return value.strftime("%x %X %Z")

    @staticmethod
    def format_date_locale(value: date) -> str:
        return format_date(value, format="short")

    @staticmethod
    def is_datetime(value: DateOrDatetimeType) -> TypeGuard[datetime]:
        return type(value) is datetime

    @staticmethod
    def is_date(value: DateOrDatetimeType) -> TypeGuard[date]:
        return not DateTimeUtils.is_datetime(value)

    @staticmethod
    def is_before(a: datetime, b: datetime) -> bool:
        return DateTimeUtils.set_tz(a) < DateTimeUtils.set_tz(b)
