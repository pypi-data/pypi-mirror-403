from clochette.persist.database.model.CalendarCache import CalendarCache


class CalendarCacheDAO:
    def get_cached_calendar(self, calendar_id: str) -> str | None:
        cache = CalendarCache.select().where(CalendarCache.calendar_id == calendar_id).first()
        return cache.content if cache else None

    def cache_calendar(self, calendar_id: str, content: str) -> None:
        CalendarCache.insert(
            calendar_id=calendar_id,
            content=content,
        ).on_conflict_replace().execute()
