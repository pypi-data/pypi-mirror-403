import time
from datetime import datetime, UTC


class ClockService:

    def utc_now(self) -> datetime:
        return datetime.now(UTC)

    def epoch(self) -> float:
        return time.time()
