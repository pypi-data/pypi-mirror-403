from typing import Protocol

from reactivex import Observable

from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


class IDownloadCalendar(Protocol):
    """Interface for calendar downloader services.

    All calendar downloader implementations must implement this interface
    to provide a consistent download method signature.
    """

    def download(self, calendar_configuration: CalendarConfiguration) -> Observable[str | None]:
        """Download calendar data from the configured source.

        Args:
            calendar_configuration: Complete calendar configuration including source, timeouts, etc.

        Returns:
            Observable that emits the downloaded calendar data as a string (ICS format),
            or None if the download fails.
        """
        ...
