#!/usr/bin/python3

from clochette.Clochette import Clochette
from clochette.infrastructure.LoggingService import LoggingService
from clochette.infrastructure.inject.Container import Container
from clochette.presentation.QMainApplication import QMainApplication


def main():
    container = Container()
    _ = container.instantiate(QMainApplication)

    container.instantiate(LoggingService).setup()
    container.instantiate(Clochette).start()


if __name__ == "__main__":
    main()
