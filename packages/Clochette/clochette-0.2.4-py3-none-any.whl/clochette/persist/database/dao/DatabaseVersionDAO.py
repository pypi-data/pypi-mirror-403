from clochette.persist.database.model.DatabaseVersion import DatabaseVersion


class DatabaseVersionDAO:

    def table_exists(self) -> bool:
        res: bool = DatabaseVersion.table_exists()
        return res

    def insert(self, version: str) -> None:
        DatabaseVersion.insert(version=version).execute()
