from clochette.application.utils.DeltaHelper import snooze_display
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.qt.Signal import OutSolidSignal, OutHollowSignal
from clochette.presentation.widget.QConditionalScrollComboBox import QConditionalScrollComboBox


class QSnoozeComboBoxView(QConditionalScrollComboBox):
    """Simple view for snooze selection combo box."""

    on_snooze_selected: OutSolidSignal[SnoozeDelta]
    on_custom_snooze_requested: OutHollowSignal

    _is_date: bool

    def __init__(self, snoozes: list[SnoozeDelta], is_date: bool) -> None:
        super().__init__()
        self.on_snooze_selected = OutSolidSignal()
        self.on_custom_snooze_requested = OutHollowSignal()

        self._is_date = is_date

        self.set_snoozes(snoozes)

        super().activated.connect(self._on_activated)

    def set_snoozes(self, snoozes: list[SnoozeDelta]) -> None:
        """Populate the combo box with snooze options."""
        self.clear()
        for snooze in snoozes:
            # having a snooze "x minutes before start" for an all day event doesn't make much sense
            if snooze.is_positive() > 0 or not self._is_date:
                display_text = snooze_display(snooze)
                self.addItem(display_text, snooze)

        # Adding the custom option as the last item
        self.addItem(self.tr("Custom..."))

    def _on_activated(self, index: int) -> None:
        if index == self.count() - 1:
            # Custom snooze selected - emit signal instead of handling directly
            self.on_custom_snooze_requested.send()
        else:
            self.on_snooze_selected.send(self.currentData())
