from pathlib import Path

from clochette import log
from clochette.persist.configuration.PlatformConfigurationService import PlatformConfigurationService
from clochette.persist import db


class BaseDAO:
    _db_file: Path

    def __init__(self, platform_configuration_service: PlatformConfigurationService):
        data = platform_configuration_service.application_data_path()
        self._db_file = data.joinpath("database.sqlite")
        log.info(f"Database path: {self._db_file}")
        db.init(str(self._db_file), pragmas={"journal_mode": "wal"})

    def create(self, query: str) -> None:
        db.execute_sql(query)
