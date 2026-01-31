from clochette.provider.shared.dto.AuthCalendar import AuthCalendar


class MicrosoftCalendar(AuthCalendar):
    _id: str
    _summary: str

    def __init__(self, id: str, summary: str):
        self._id = id
        self._summary = summary

    @property
    def id(self) -> str:
        return self._id

    @property
    def summary(self) -> str:
        return self._summary
