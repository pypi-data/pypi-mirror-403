from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class LoggingConfiguration:
    log_level: str
    log_console_enabled: bool
