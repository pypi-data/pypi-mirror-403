from datetime import timedelta, datetime, UTC
from typing import Iterator

from clochette.domain.entity.Trigger import Trigger
from clochette.infrastructure.clock.DateTimeUtils import DateTimeUtils
from clochette.infrastructure.clock.Generics import DateOrDatetimeType
from clochette.infrastructure.data_structure.PeekableIterator import PeekableIterator, take_while


class TriggerIteratorFactory:
    @staticmethod
    def make_trigger_iterator(
        base_iterator: Iterator[Trigger], offsets: list[timedelta], start: datetime
    ) -> PeekableIterator[Trigger]:
        offset_iterator = TriggerIteratorFactory._make_offset_iterator(base_iterator, offsets)
        iterator: PeekableIterator[Trigger] = PeekableIterator(offset_iterator)

        # trim the first values that are before start
        def trim(trigger: Trigger) -> bool:
            return trigger.trigger <= start

        _ = take_while(iterator, trim)
        return iterator

    @staticmethod
    def to_trigger_iterator(base_iterator: Iterator[DateOrDatetimeType]) -> Iterator[Trigger]:
        for trigger in base_iterator:
            yield TriggerIteratorFactory._normalize_trigger(trigger, trigger)

    @staticmethod
    def _make_offset_iterator(base_iterator: Iterator[Trigger], offsets: list[timedelta]) -> Iterator[Trigger]:
        for trigger in base_iterator:
            for offset in offsets:
                yield Trigger(trigger.trigger + offset, trigger.start)

    @staticmethod
    def _normalize_trigger(trigger: DateOrDatetimeType, start: DateOrDatetimeType):
        if DateTimeUtils.is_datetime(trigger):
            if not trigger.tzinfo:
                return Trigger(DateTimeUtils.set_tz(trigger), start)
            else:
                return Trigger(trigger, start)
        else:
            trigger_dt = DateTimeUtils.to_datetime(trigger, UTC)
            return Trigger(trigger_dt, start)
