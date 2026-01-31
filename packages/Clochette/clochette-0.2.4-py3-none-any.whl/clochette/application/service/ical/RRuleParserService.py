from datetime import datetime, date
from typing import Iterator

from dateutil.rrule import rrulestr, rruleset

from clochette import log
from clochette.infrastructure.clock.DateTimeUtils import DateTimeUtils


class RRuleParserService:

    # doc: https://dateutil.readthedocs.io/en/stable/rrule.html
    def parse_rrule(
        self,
        rule: str,
        dtstart: date | datetime,
        after: datetime,
        exclusion: list[datetime] | None = None,
        inclusion: list[datetime] | None = None,
    ) -> Iterator[date] | Iterator[datetime]:
        log.debug(f"Parsing rrule: {rule}, dtstart: {dtstart}, after: {after}")

        exclusion = exclusion or []
        inclusion = inclusion or []

        if DateTimeUtils.is_datetime(dtstart):
            return self._parse_rrule_datetime(rule, dtstart, after, exclusion, inclusion)
        else:
            return self._parse_rrule_date(rule, dtstart, after, exclusion, inclusion)

    def _parse_rrule_date(
        self,
        rule: str,
        dtstart: date,
        after: datetime,
        exclusion: list[datetime],
        inclusion: list[datetime],
    ) -> Iterator[date]:
        after = DateTimeUtils.set_tz(after, None)
        after = DateTimeUtils.to_datetime(after.date())

        ruleset = rruleset()
        ruleset.rrule(rrulestr(rule, dtstart=dtstart))  # pyright: ignore [reportArgumentType]

        for ex in exclusion:
            ruleset.exdate(DateTimeUtils.to_datetime(ex))

        for inc in inclusion:
            ruleset.rdate(DateTimeUtils.to_datetime(inc))

        for res in ruleset.xafter(after, inc=True):
            yield res.date()

    def _parse_rrule_datetime(
        self,
        rule: str,
        dtstart: datetime,
        after: datetime,
        exclusion: list[datetime],
        inclusion: list[datetime],
    ) -> Iterator[datetime]:

        original_tz = dtstart.tzinfo
        until: datetime | None = rrulestr(rule)._until  # pyright: ignore [reportAttributeAccessIssue]

        if until:
            dtstart, after = DateTimeUtils.normalize_tz(until.tzinfo, [dtstart, after])
        else:
            after = DateTimeUtils.set_tz(after, dtstart.tzinfo)

        ruleset = rruleset()
        ruleset.rrule(rrulestr(rule, dtstart=dtstart))  # pyright: ignore [reportArgumentType]

        for ex in exclusion:
            ex = DateTimeUtils.set_tz(ex, dtstart.tzinfo)
            ruleset.exdate(ex)

        for inc in inclusion:
            inc = DateTimeUtils.set_tz(inc, dtstart.tzinfo)
            ruleset.rdate(inc)

        for event in ruleset.xafter(after, inc=True):
            if until:
                yield DateTimeUtils.set_tz(event, original_tz)
            else:
                yield event
