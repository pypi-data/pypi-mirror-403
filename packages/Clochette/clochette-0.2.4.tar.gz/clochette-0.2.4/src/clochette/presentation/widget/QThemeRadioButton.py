from PySide6.QtWidgets import QVBoxLayout, QButtonGroup, QRadioButton, QWidget, QGroupBox

from clochette.domain.entity.configuration.ThemeEnum import ThemeEnum
from clochette.framework.qt.Signal import InSolidSignal, OutSolidSignal


class QThemeRadioButton(QWidget):
    """Simple widget for theme selection via radio buttons. Uses signals for communication."""

    _dark_radio: QRadioButton
    _light_radio: QRadioButton
    _generic_radio: QRadioButton

    # Inbound: set the selected theme from parent
    set_theme: InSolidSignal[ThemeEnum]

    # Outbound: emit when user selects a theme
    on_theme_changed: OutSolidSignal[ThemeEnum]

    def __init__(self, title: str):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Initialize signals
        self.set_theme = InSolidSignal(self._on_set_theme)
        self.on_theme_changed = OutSolidSignal()

        window_icon_button_group = QButtonGroup()

        group_box = QGroupBox(title)
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        self._dark_radio = QRadioButton(self.tr("Dark"))
        self._dark_radio.setChecked(True)
        self._dark_radio.toggled.connect(lambda s: self._on_toggle(s, ThemeEnum.DARK))
        self._light_radio = QRadioButton(self.tr("Light"))
        self._light_radio.toggled.connect(lambda s: self._on_toggle(s, ThemeEnum.LIGHT))
        self._generic_radio = QRadioButton(self.tr("Generic (gray)"))
        self._generic_radio.toggled.connect(lambda s: self._on_toggle(s, ThemeEnum.GENERIC))

        window_icon_button_group.addButton(self._dark_radio)
        window_icon_button_group.addButton(self._light_radio)
        window_icon_button_group.addButton(self._generic_radio)

        group_layout.addWidget(self._dark_radio)
        group_layout.addWidget(self._light_radio)
        group_layout.addWidget(self._generic_radio)

    def _on_toggle(self, state: bool, theme: ThemeEnum):
        """Handle radio button toggle - emit signal when selected."""
        if state:
            self.on_theme_changed.send(theme)

    def _on_set_theme(self, theme: ThemeEnum) -> None:
        """Handle incoming theme update - update radio button selection without triggering signals."""

        self._block_signals(True)

        if theme == ThemeEnum.DARK:
            self._dark_radio.setChecked(True)
        elif theme == ThemeEnum.LIGHT:
            self._light_radio.setChecked(True)
        elif theme == ThemeEnum.GENERIC:
            self._generic_radio.setChecked(True)

        self._block_signals(False)

    def _block_signals(self, block: bool):
        self._dark_radio.blockSignals(block)
        self._light_radio.blockSignals(block)
        self._generic_radio.blockSignals(block)

    def get_theme(self) -> ThemeEnum | None:
        """Get the currently selected theme."""
        if self._dark_radio.isChecked():
            return ThemeEnum.DARK
        elif self._light_radio.isChecked():
            return ThemeEnum.LIGHT
        elif self._generic_radio.isChecked():
            return ThemeEnum.GENERIC

        return None
