from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration
from clochette.domain.entity.configuration.ThemeEnum import ThemeEnum
from clochette.framework.qt.Signal import OutSolidSignal
from clochette.presentation.widget.QThemeRadioButton import QThemeRadioButton
from clochette.presentation.widget.QTimedeltaListWidget import QTimedeltaListWidget
from clochette.presentation.widget.QTitle import QTitle


class QGeneralSettingsView(QWidget):
    """Pure view for general settings - snoozes and theme configuration."""

    # Out signals
    on_snoozes_changed: OutSolidSignal[list[SnoozeDelta]]
    on_theme_changed: OutSolidSignal[ThemeConfiguration]

    _snooze_widget: QTimedeltaListWidget[SnoozeDelta]
    _window_icon_theme_radio_button: QThemeRadioButton
    _systray_icon_theme_radio_button: QThemeRadioButton

    def __init__(self):
        super().__init__()

        # Initialize signals
        self.on_snoozes_changed = OutSolidSignal()
        self.on_theme_changed = OutSolidSignal()

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Snoozes section
        main_layout.addWidget(
            QTitle(self.tr("Snoozes"), self.tr("Configure the different snooze option when a reminder appears"))
        )

        self._snooze_widget = QTimedeltaListWidget(SnoozeDelta)
        main_layout.addWidget(self._snooze_widget)

        # Wire snooze widget to signal
        self._snooze_widget.on_delta_updated.link(self._on_snoozes_updated)

        # Theme section
        main_layout.addWidget(
            QTitle(self.tr("Theme"), self.tr("Clochette cannot detect the theme so I let you choose it"))
        )

        theme_layout = QHBoxLayout()

        self._window_icon_theme_radio_button = QThemeRadioButton(self.tr("Window Icon Theme"))
        self._systray_icon_theme_radio_button = QThemeRadioButton(self.tr("System Tray Icon Theme"))

        theme_layout.addWidget(self._window_icon_theme_radio_button)
        theme_layout.addWidget(self._systray_icon_theme_radio_button)
        theme_layout.addStretch()

        main_layout.addLayout(theme_layout)

        # Wire theme widgets to signal
        self._window_icon_theme_radio_button.on_theme_changed.link(self._on_any_theme_changed)
        self._systray_icon_theme_radio_button.on_theme_changed.link(self._on_any_theme_changed)

    def set_snoozes(self, snooze_displays: list[SnoozeDelta]) -> None:
        """Set the snooze deltas."""
        self._snooze_widget.set_deltas(snooze_displays)

    def set_window_theme(self, theme: ThemeEnum) -> None:
        """Set the window icon theme."""
        self._window_icon_theme_radio_button.set_theme(theme)

    def set_systray_theme(self, theme: ThemeEnum) -> None:
        """Set the systray icon theme."""
        self._systray_icon_theme_radio_button.set_theme(theme)

    def _on_snoozes_updated(self, snoozes: list[SnoozeDelta]) -> None:
        """Handle snooze updates from widget."""
        self.on_snoozes_changed.send(snoozes)

    def _on_any_theme_changed(self, _) -> None:
        """Handle theme change from either radio button - emit both themes."""
        window_theme = self._window_icon_theme_radio_button.get_theme()
        systray_theme = self._systray_icon_theme_radio_button.get_theme()

        if window_theme is not None and systray_theme is not None:
            self.on_theme_changed.send(ThemeConfiguration(window_theme, systray_theme))
