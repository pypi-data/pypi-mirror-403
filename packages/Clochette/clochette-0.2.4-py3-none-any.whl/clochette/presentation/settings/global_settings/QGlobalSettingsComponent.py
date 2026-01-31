from dataclasses import dataclass, field

from clochette.framework.qt.QComponent import QComponent
from clochette.framework.qt.Signal import InHollowSignal
from clochette.presentation.window.QGlobalSettingsWindow import QGlobalSettingsWindow


@dataclass
class QGlobalSettingsComponent(QComponent[QGlobalSettingsWindow]):
    _view: QGlobalSettingsWindow

    show_window: InHollowSignal = field(init=False)

    def __post_init__(self):
        super().__init__(self._view)
        self.show_window = InHollowSignal(self._on_show)

    def _on_show(self) -> None:
        self._view.show()
