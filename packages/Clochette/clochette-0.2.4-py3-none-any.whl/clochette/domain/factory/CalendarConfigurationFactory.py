from dataclasses import replace

from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.presentation.settings.calendar.dto.CalendarFormValuesDTO import CalendarFormValuesDTO


class CalendarConfigurationFactory:
    def create_from_form_values(self, form_values: CalendarFormValuesDTO) -> CalendarConfiguration:
        """
        Create a new CalendarConfiguration from form values.

        Args:
            form_values: DTO containing all form values from the UI

        Returns:
            New CalendarConfiguration with a generated ID
        """
        return CalendarConfiguration(
            id=CalendarID.new(),
            name=form_values.name,
            source=form_values.source,
            download_interval=form_values.download_interval,
            missed_reminders_past_window=form_values.missed_reminders_past_window,
            force_alarms=form_values.force_alarms,
            force_alarms_dates=form_values.force_alarms_dates,
            default_alarms=form_values.default_alarms,
            default_alarms_dates=form_values.default_alarms_dates,
            http_timeout=form_values.http_timeout,
        )

    def update_from_form_values(
        self, existing: CalendarConfiguration, form_values: CalendarFormValuesDTO
    ) -> CalendarConfiguration:
        """
        Update an existing CalendarConfiguration with new form values.

        Args:
            existing: The existing configuration to update
            form_values: DTO containing updated form values from the UI

        Returns:
            Updated CalendarConfiguration (new instance, since frozen)
        """
        return replace(
            existing,
            name=form_values.name,
            source=form_values.source,
            download_interval=form_values.download_interval,
            missed_reminders_past_window=form_values.missed_reminders_past_window,
            force_alarms=form_values.force_alarms,
            force_alarms_dates=form_values.force_alarms_dates,
            default_alarms=form_values.default_alarms,
            default_alarms_dates=form_values.default_alarms_dates,
            http_timeout=form_values.http_timeout,
        )
