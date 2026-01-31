from datetime import datetime, date

from clochette.persist.database.model.Snooze import SnoozeDTO, Snooze


class SnoozeDAO:

    def get_snoozes_by_calendar(self, calendar_id: str) -> list[SnoozeDTO]:
        snoozes = Snooze.select().where(Snooze.calendar_id == calendar_id)
        return [
            SnoozeDTO(
                id=snooze.calendar_id,
                event_uid=snooze.event_uid,
                calendar_id=snooze.calendar_id,
                trigger=snooze.trigger,
                trigger_start=snooze.trigger_start,
            )
            for snooze in snoozes
        ]

    def add_snooze(self, event_uid: str, calendar_id: str, trigger: datetime, trigger_start: date | datetime) -> int:
        result: int = Snooze.insert(
            event_uid=event_uid,
            calendar_id=calendar_id,
            trigger=trigger,
            trigger_start=trigger_start,
        ).execute()
        return result

    def delete_snooze(self, id: int) -> None:
        Snooze.delete().where(Snooze.id == id).execute()

    def delete_snooze_by_event_id(self, event_uid: str, calendar_id: str):
        Snooze.delete().where(Snooze.calendar_id == calendar_id).where(Snooze.event_uid == event_uid).execute()
