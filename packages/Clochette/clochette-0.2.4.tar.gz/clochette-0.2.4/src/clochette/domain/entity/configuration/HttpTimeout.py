from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class HttpTimeout:
    connection_timeout: int
    read_timeout: int

    @staticmethod
    def default():
        return HttpTimeout(5, 30)
