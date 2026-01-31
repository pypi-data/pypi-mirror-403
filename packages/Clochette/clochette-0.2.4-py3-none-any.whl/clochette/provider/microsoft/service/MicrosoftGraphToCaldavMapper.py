import json
from datetime import UTC, datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event, vMonth

RecurrenceType = Literal["daily", "weekly", "absoluteMonthly", "relativeMonthly", "absoluteYearly", "relativeYearly"]
WeekIndexType = Literal["first", "second", "third", "fourth", "last"]
DaysOfWeekType = Literal["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
AttendeeType = Literal["required", "optional", "resource"]
RangeType = Literal["endDate", "noEnd", "numbered"]

_WEEK_DAY_MAPPING: dict[DaysOfWeekType, str] = {
    "monday": "MO",
    "tuesday": "TU",
    "wednesday": "WE",
    "thursday": "TH",
    "friday": "FR",
    "saturday": "SA",
    "sunday": "SU",
}

_FREQ_MAPPING: dict[RecurrenceType, str] = {
    "daily": "DAILY",
    "weekly": "WEEKLY",
    "absoluteMonthly": "MONTHLY",
    "relativeMonthly": "MONTHLY",
    "absoluteYearly": "YEARLY",
    "relativeYearly": "YEARLY",
}

_ATTENDEE_TYPE_MAPPING: dict[AttendeeType, str] = {
    "required": "REQ-PARTICIPANT",
    "optional": "OPT-PARTICIPANT",
    "resource": "NON-PARTICIPANT",
}

_WEEK_INDEX_MAPPING: dict[WeekIndexType, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "last": -1,
}


class MicrosoftGraphToCaldavMapper:

    def to_ical(self, json_data: dict[str, dict] | str) -> Calendar:
        if type(json_data) is str:
            data = json.loads(json_data, strict=False)
            return self._to_ical(data)
        elif type(json_data) is dict:
            return self._to_ical(json_data)
        else:
            raise Exception(f"Unsupported data type: {type(json_data)}")

    def _to_ical(self, json_data: dict[str, dict]) -> Calendar:
        # Create a new calendar
        cal = Calendar()

        # Loop through each event in the JSON data
        for event_data in json_data.get("value", []):
            event = self._get_event(event_data)

            # Add other properties as needed
            event.add("dtstamp", datetime.now(UTC))

            # Add the event to the calendar
            cal.add_component(event)

        return cal

    def get_event(self, json_data: dict[str, dict] | str) -> Event:
        if type(json_data) is str:
            data = json.loads(json_data, strict=False)
            return self._get_event(data)
        elif type(json_data) is dict:
            return self._get_event(json_data)
        else:
            raise Exception(f"Unsupported data type: {type(json_data)}")

    def _get_event(self, event_data: dict[str, Any]) -> Event:
        # basic event data
        event = Event()
        event.add("SUMMARY", event_data.get("subject", ""))
        event.add("UID", event_data.get("uid", ""))
        event.add("DESCRIPTION", event_data.get("bodyPreview", ""))

        # location
        location = event_data["location"].get("displayName", None)

        if location is not None and location != "":
            event.add("LOCATION", location)

        # datetimes
        createdDateTime = datetime.fromisoformat(event_data["createdDateTime"]).replace(microsecond=0)
        lastModifiedDateTime = datetime.fromisoformat(event_data["lastModifiedDateTime"]).replace(microsecond=0)

        event.add("CREATED", createdDateTime)
        event.add("DTSTAMP", createdDateTime)
        event.add("LAST-MODIFIED", lastModifiedDateTime)

        # start and end times
        is_all_day = event_data.get("isAllDay", False)

        if is_all_day:
            start_time = datetime.fromisoformat(event_data["start"]["dateTime"])
            end_time = datetime.fromisoformat(event_data["end"]["dateTime"])

            event.add("DTSTART", start_time.date())
            event.add("DTEND", end_time.date())
        else:
            start_time = datetime.fromisoformat(event_data["start"]["dateTime"])
            start_time = start_time.replace(tzinfo=ZoneInfo(event_data["start"]["timeZone"]))

            end_time = datetime.fromisoformat(event_data["end"]["dateTime"])
            end_time = end_time.replace(tzinfo=ZoneInfo(event_data["end"]["timeZone"]))

            event.add("DTSTART", start_time, parameters={"TZID": event_data["start"]["timeZone"]})
            event.add("DTEND", end_time, parameters={"TZID": event_data["end"]["timeZone"]})

        # organizer
        organizer = event_data.get("organizer", {}).get("emailAddress", {})

        if organizer:
            parameters = {}
            name = organizer.get("name", None)

            if name is not None:
                parameters["cn"] = name

            event.add("organizer", f"MAILTO:{organizer.get('address', '')}", parameters=parameters)

        # attendees
        for attendee in event_data.get("attendees", []):
            attendee_email = attendee.get("emailAddress", None)

            if attendee_email is not None:
                parameters = {
                    "CN": attendee_email.get("name", ""),
                    "ROLE": _ATTENDEE_TYPE_MAPPING[attendee.get("type")],
                }

                name = attendee_email.get("name", None)
                if name is not None:
                    parameters["CN"] = name

                event.add(
                    "ATTENDEE",
                    f"MAILTO:{attendee_email.get('address', '')}",
                    parameters=parameters,
                )

        # Add recurrence rule if it exists
        recurrence = event_data.get("recurrence")
        if recurrence:
            rule = self._get_rrule(recurrence)
            event.add("RRULE", rule)

        return event

    def get_rrule(self, json_data: str) -> dict[str, Any]:
        data = json.loads(json_data, strict=False)
        recurrence = data.get("recurrence")
        return self._get_rrule(recurrence)

    # https://learn.microsoft.com/en-us/graph/api/resources/recurrencepattern?view=graph-rest-1.0
    # https://learn.microsoft.com/en-us/graph/api/resources/recurrencerange?view=graph-rest-1.0
    # https://dateutil.readthedocs.io/en/stable/rrule.html
    # https://datatracker.ietf.org/doc/html/rfc5545.html
    # - search for recur-rule-part
    def _get_rrule(self, recurrence: dict[str, Any]) -> dict[str, Any]:
        pattern = recurrence["pattern"]
        _day_of_month: int | None = pattern.get("dayOfMonth", None)
        days_of_week: list[DaysOfWeekType] = pattern.get("daysOfWeek", [])
        _first_day_of_week: DaysOfWeekType = pattern.get("firstDayOfWeek", "sunday")
        index: WeekIndexType = pattern.get("index", "first")
        interval: int = pattern["interval"]
        month: int = pattern.get("month", 1)
        recurrence_type: RecurrenceType = pattern["type"]

        range = recurrence["range"]
        _start_date = range["startDate"]
        end_date = range.get("endDate", None)
        number_of_occurrences: int | None = range.get("numberOfOccurrences", None)
        range_type: RangeType = range["type"]

        rule: dict[str, Any] = {
            "FREQ": [_FREQ_MAPPING[pattern["type"]]],
        }

        if interval != 1:
            rule["INTERVAL"] = [interval]

        if recurrence_type == "weekly" and len(days_of_week) > 1:
            rule["BYDAY"] = [_WEEK_DAY_MAPPING[d] for d in days_of_week]

        if recurrence_type == "relativeMonthly" or recurrence_type == "relativeYearly":
            nth = _WEEK_INDEX_MAPPING[index]
            weekday = [_WEEK_DAY_MAPPING[d] for d in days_of_week]
            rule["BYDAY"] = [str(nth) + weekday[0]]

            if recurrence_type == "relativeYearly":
                rule["BYMONTH"] = [vMonth(month)]

        if range_type == "endDate":
            rule["UNTIL"] = [datetime.fromisoformat(end_date).date()]
        elif range_type == "numbered":
            rule["COUNT"] = number_of_occurrences

        return rule
