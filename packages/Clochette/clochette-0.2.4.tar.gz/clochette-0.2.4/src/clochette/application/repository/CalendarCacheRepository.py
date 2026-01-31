from dataclasses import dataclass

from clochette.domain.entity.CalendarID import CalendarID
from clochette.persist.database.dao.CalendarCacheDAO import CalendarCacheDAO


@dataclass
class CalendarCacheRepository:
    _calendar_cache_dao: CalendarCacheDAO

    def get_calendar_cache(self, calendar_id: CalendarID) -> str | None:
        return self._calendar_cache_dao.get_cached_calendar(calendar_id.id)

    def cache_calendar(self, calendar_id: CalendarID, content: str) -> None:
        return self._calendar_cache_dao.cache_calendar(calendar_id.id, content)
