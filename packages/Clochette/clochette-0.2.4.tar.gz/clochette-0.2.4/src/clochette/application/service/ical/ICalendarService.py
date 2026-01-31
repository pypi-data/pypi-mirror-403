from dataclasses import dataclass
from datetime import timedelta, datetime, date, UTC
from typing import Type, Iterator, TypeVar

from icalendar import Calendar, Event, Alarm
from icalendar.cal import Component
from icalendar.prop import vCalAddress, vDDDLists

from clochette import log
from clochette.domain.entity.CalendarEvent import CalendarEvent
from clochette.domain.entity.CalendarEventQuery import CalendarEventQuery
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.Contact import Contact
from clochette.domain.entity.EventDetails import EventDetails
from clochette.domain.entity.EventID import EventID
from clochette.domain.entity.EventUID import EventUID
from clochette.domain.entity.Trigger import Trigger
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.application.service.ical.RRuleParserService import RRuleParserService
from clochette.application.service.ical.TriggerIteratorFactory import TriggerIteratorFactory
from clochette.application.service.ical.dto.EventDTO import EventDTO
from clochette.application.service.ical.dto.ExclusionDTO import ExclusionDTO
from clochette.infrastructure.clock.DateTimeUtils import DateTimeUtils


@dataclass
class ICalendarService:
    _rrule_parser_service: RRuleParserService

    def parse_calendar(
        self, calendar_configuration: CalendarConfiguration, ics: str, last_download: datetime, calendar_id: CalendarID
    ) -> CalendarEventQuery:
        log.debug("Parsing the ics file")
        cal = Calendar.from_ical(ics)
        events: dict[str, EventDTO] = {}

        # example https://gist.github.com/meskarune/63600e64df56a607efa211b9a87fb443
        for vevent in self._walk(cal, "VEVENT", Event):
            try:
                event = self._get_event(vevent)

                if not event:
                    continue

                if isinstance(event, ExclusionDTO):
                    linked_event = events[event.uid]
                    linked_event.raw += "\n" + event.raw
                    linked_event.exdates.append(event.exclusion)
                    linked_event.rdates.append(event.inclusion)
                else:
                    event.alarms = self._get_alarm(vevent, calendar_configuration)
                    events[event.uid] = event
            except Exception:
                log.warning(f"Failed to parse event {vevent}", exc_info=True)

        res: dict[EventID, CalendarEvent] = {}
        for _, event in events.items():
            calendar_event = self._to_calendar_event(event, calendar_id, last_download)
            res[calendar_event.event_id] = calendar_event

        log.debug(f"Creating a CalendarQueryEvent starting at {last_download}, calendar_id: {calendar_id}")
        return CalendarEventQuery(res)

    def _to_calendar_event(self, event: EventDTO, calendar_id: CalendarID, last_download: datetime) -> CalendarEvent:
        trigger_iterator: Iterator[Trigger]
        log.debug(f"Creating event {event}, calendar_id: {calendar_id}, last_download: {last_download}")

        if event.rrule:
            rrule_iterator = self._rrule_parser_service.parse_rrule(
                event.rrule, event.dtstart, last_download, event.exdates, event.rdates
            )
            trigger_iterator = TriggerIteratorFactory.to_trigger_iterator(rrule_iterator)
        else:
            start: datetime
            if DateTimeUtils.is_datetime(event.dtstart):
                start = DateTimeUtils.set_tz(event.dtstart, UTC)
            else:
                start = DateTimeUtils.to_datetime(event.dtstart, UTC)

            trigger = Trigger(start, event.dtstart)
            trigger_iterator = iter([trigger])

        peekable_trigger_iterator = TriggerIteratorFactory.make_trigger_iterator(
            trigger_iterator, event.alarms, last_download
        )

        return CalendarEvent(
            EventID(EventUID(event.uid), calendar_id), event.dtstart, event.dtend, peekable_trigger_iterator, event.raw
        )

    def _get_event(self, event: Event) -> EventDTO | ExclusionDTO | None:
        rrule = event.get("RRULE")
        uid = str(event.get("UID"))
        dtstart: date | datetime = event.get("DTSTART").dt
        duration = event.get("DURATION")
        recurrence_id = event.get("RECURRENCE-ID")
        rdates = self.get_xdates(event.get("RDATE"))
        exdates = self.get_xdates(event.get("EXDATE"))

        dtend: date | datetime
        if event.get("DTEND"):
            dtend = event.get("DTEND").dt
        elif duration:
            dtend = dtstart + duration.dt
        else:
            dtend = dtstart

        raw = str(event.to_ical().decode())

        if recurrence_id:
            log.debug(f"Found recurrence exception for event with id: {uid}")
            return ExclusionDTO(uid, recurrence_id.dt, dtstart, raw)
        if rrule:
            rrule_str = rrule.to_ical().decode()
            return EventDTO(uid, dtstart, dtend, rrule_str, raw, exdates, rdates)
        else:
            return EventDTO(uid, dtstart, dtend, None, raw, exdates, rdates)

    def get_xdates(self, dates: list[vDDDLists] | None):
        res = []
        if dates:
            for date in dates:
                if date.dts:
                    for dt in date.dts:
                        res.append(dt.dt)
        return res

    def _get_alarm(self, event: Event, calendar_configuration: CalendarConfiguration) -> list[timedelta]:
        res = []

        for valarm in self._walk(event, "VALARM", Alarm):
            alarm = Alarm(valarm)
            res.append(alarm.get("TRIGGER").dt)

        dtstart: date | datetime = event.get("DTSTART").dt
        is_datetime = DateTimeUtils.is_datetime(dtstart)

        if is_datetime:
            force_alarms_td = [ad.get_timedelta() for ad in calendar_configuration.force_alarms]
            unique_alarms = set(res + force_alarms_td)
            if not unique_alarms:
                default_alarms_td = [ad.get_timedelta() for ad in calendar_configuration.default_alarms]
                unique_alarms = set(default_alarms_td)
        else:
            force_alarms_dates_td = [ad.get_timedelta() for ad in calendar_configuration.force_alarms_dates]
            unique_alarms = set(res + force_alarms_dates_td)
            if not unique_alarms:
                default_alarms_dates_td = [ad.get_timedelta() for ad in calendar_configuration.default_alarms_dates]
                unique_alarms = set(default_alarms_dates_td)

        sorted_alarms = list(unique_alarms)
        sorted_alarms.sort()
        return sorted_alarms

    def parse_event_details(self, str_event: str) -> EventDetails:
        event = self._find_event(str_event)

        summary = event.get("SUMMARY")
        description = event.get("DESCRIPTION")
        location = event.get("LOCATION")
        organizer = self._from_vcaladdress(event.get("ORGANIZER")) if event.get("ORGANIZER") else None
        attendee = self._parse_attendees(event.get("ATTENDEE"))
        duration = self._calculate_duration(event)

        return EventDetails(summary, description, location, organizer, attendee, str_event, duration)

    def _calculate_duration(self, event: Event) -> timedelta:
        dtstart_value = event.get("DTSTART")
        dtstart: date | datetime = dtstart_value.dt

        duration_field = event.get("DURATION")
        if duration_field:
            return duration_field.dt

        dtend_value = event.get("DTEND")
        if dtend_value:
            dtend: date | datetime = dtend_value.dt

            # Ensure type consistency and calculate duration with explicit type narrowing
            if DateTimeUtils.is_datetime(dtstart) and DateTimeUtils.is_datetime(dtend):
                return dtend - dtstart
            elif DateTimeUtils.is_date(dtstart) and DateTimeUtils.is_date(dtend):
                return datetime.combine(dtend, datetime.min.time()) - datetime.combine(dtstart, datetime.min.time())

        # No duration or end time specified
        return timedelta(0)

    def _find_event(self, event: str) -> Event:
        cal = Event.from_ical(event)

        for vevent in self._walk(cal, "VEVENT", Event):
            return vevent

        raise ValueError(f"No event found in string: {event}")

    def _from_vcaladdress(self, value: vCalAddress) -> Contact:
        params = value.params
        return Contact(params.get("CN"), str(value).replace("MAILTO:", ""), params.get("PARTSTAT") == "ACCEPTED")

    def _parse_attendees(self, value: list[vCalAddress] | None) -> list[Contact]:
        if value is None:
            return []
        else:
            return [self._from_vcaladdress(x) for x in value]

    _T = TypeVar("_T")

    def _walk(self, cal: Component, component_name: str, component_type: Type[_T]) -> Iterator[_T]:
        for component in cal.walk():
            if component.name == component_name and isinstance(component, component_type):
                yield component
