from dataclasses import dataclass

from clochette import log
from clochette.persist.database.dao.BaseDAO import BaseDAO
from clochette.persist.database.dao.DatabaseVersionDAO import DatabaseVersionDAO


@dataclass
class DatabaseMigrationService:
    _base_model: BaseDAO
    _database_version_dao: DatabaseVersionDAO

    def migrate(self) -> None:
        self._v1()

    def _v1(self) -> None:
        if not self._database_version_dao.table_exists():
            log.info("Database doesn't exists, creating.")
            self._base_model.create(
                """
                CREATE TABLE IF NOT EXISTS calendar (
                    id TEXT PRIMARY KEY,
                    last_download DATETIME DEFAULT '0001-01-01 00:00:00+00:00'
                )"""
            )

            self._base_model.create(
                """
                CREATE TABLE IF NOT EXISTS calendar_cache (
                    calendar_id TEXT PRIMARY KEY,
                    content TEXT,
                    FOREIGN KEY (calendar_id) REFERENCES calendar(id) ON DELETE CASCADE
                )"""
            )

            self._base_model.create(
                """
                CREATE TABLE IF NOT EXISTS snooze (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_uid TEXT NOT NULL,
                    calendar_id TEXT NOT NULL,
                    trigger DATETIME NOT NULL,
                    trigger_start TEXT NOT NULL
                )"""
            )

            self._base_model.create(
                """
                 CREATE TABLE IF NOT EXISTS database_version (
                    id INTEGER PRIMARY KEY,
                    version TEXT NOT NULL,
                    applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            )

            self._database_version_dao.insert("v1")
