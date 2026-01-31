from PySide6.QtCore import QFile, QIODeviceBase


def read_file(file: QFile) -> bytes:
    if file.exists():
        if file.open(QIODeviceBase.OpenModeFlag.ReadOnly):
            return bytes(file.readAll().data())
    raise Exception(f"Cannot open file, make sure it exists or the system has permissions: {file}")
