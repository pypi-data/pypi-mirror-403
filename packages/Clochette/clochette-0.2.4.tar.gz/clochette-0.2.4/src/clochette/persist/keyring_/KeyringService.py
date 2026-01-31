import keyring

from clochette import log


class KeyringService:
    _service_name: str

    def __init__(self) -> None:
        self._service_name = "clochette"

    def store_value(self, key: str, value: str) -> None:
        log.debug(f"Storing value in keyring, prefix: key: {key}")
        keyring.set_password(self._service_name, key, value)

    def get_value(self, key: str) -> str | None:
        log.debug(f"Retrieving value from keyring, key: {key}")
        return keyring.get_password(self._service_name, key)

    def delete_value(self, key: str) -> None:
        log.debug(f"Deleting value from keyring, key: {key}")
        try:
            keyring.delete_password(self._service_name, key)
        except Exception:
            log.warning(f"Deleting keyring value which doesn't exists: {key}")
