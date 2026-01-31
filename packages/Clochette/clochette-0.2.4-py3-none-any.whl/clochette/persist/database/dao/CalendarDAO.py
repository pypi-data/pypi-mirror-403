from datetime import datetime

from clochette.persist.database.model.Calendar import Calendar, CalendarDTO


class CalendarDAO:

    def delete_by_id(self, id: str) -> None:
        query = Calendar.delete().where(Calendar.id == id)
        query.execute()

    def insert(self, id: str) -> None:
        Calendar.insert(id=id).execute()

    def get_all(self) -> list[CalendarDTO]:
        calendars = Calendar.select()
        return [CalendarDTO(id=calendar.id, last_download=calendar.last_download) for calendar in calendars]

    def update_last_download(self, id: str, last_download: datetime) -> None:
        query = Calendar.update(last_download=last_download).where(Calendar.id == id)
        query.execute()

    def get_by_id(self, id: str) -> CalendarDTO:
        calendar = Calendar.get(Calendar.id == id)
        return CalendarDTO(id=calendar.id, last_download=calendar.last_download)
