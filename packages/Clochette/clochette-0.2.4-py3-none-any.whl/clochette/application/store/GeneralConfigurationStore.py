from reactivex import Observable, operators as ops
from reactivex.subject import ReplaySubject

from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration


class GeneralConfigurationStore:
    """Store for general configuration state using RxPY subjects."""

    _snoozes: ReplaySubject[list[SnoozeDelta]]
    _theme: ReplaySubject[ThemeConfiguration]

    def __init__(self):
        self._snoozes = ReplaySubject(buffer_size=1)
        self._theme = ReplaySubject(buffer_size=1)

    @property
    def snoozes(self) -> Observable[list[SnoozeDelta]]:
        """Observable for the snooze deltas. Only emits when value changes."""
        return self._snoozes.pipe(
            ops.distinct_until_changed(),
        )

    @property
    def theme(self) -> Observable[ThemeConfiguration]:
        """Observable for the theme configuration. Only emits when value changes."""
        return self._theme.pipe(
            ops.distinct_until_changed(),
        )

    def set_snoozes(self, snoozes: list[SnoozeDelta]) -> None:
        """Set the snooze deltas."""
        self._snoozes.on_next(snoozes)

    def set_theme(self, theme: ThemeConfiguration) -> None:
        """Set the theme configuration."""
        self._theme.on_next(theme)
