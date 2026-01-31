from clochette.application.utils.DeltaHelper import TimeUnitLiteral
from clochette.presentation.widget.QGenericComboBox import QGenericComboBox

class QTimeUnitCombobox(QGenericComboBox[TimeUnitLiteral]):
    def __init__(self):
        super().__init__()
        # Populate with translatable labels mapped to TimeUnitLiteral keys
        # Must use literal strings for lupdate to extract them
        items: list[tuple[TimeUnitLiteral, str]] = [
            ("minutes", self.tr("minutes")),
            ("hours", self.tr("hours")),
            ("days", self.tr("days")),
        ]
        self.set_items(items)
        self.clear()

    def time_unit(self) -> TimeUnitLiteral:
        """Get the current time unit (returns the key, not the display label)"""
        unit = self.current_key()
        return unit if unit is not None else "minutes"

    def set_current_unit(self, unit: TimeUnitLiteral) -> None:
        """Set the current time unit by key"""
        self.set_current_by_key(unit)

    def clear(self) -> None:
        """Reset to default time unit"""
        self.set_current_unit("minutes")
