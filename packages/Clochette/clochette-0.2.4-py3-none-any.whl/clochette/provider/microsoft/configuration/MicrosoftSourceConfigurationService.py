import json
from configparser import SectionProxy
from typing import Any

from clochette.application.service.provider.dto.IProviderConfigurationMapper import IProviderConfigurationMapper
from clochette.persist.configuration.ConfigurationReadUtils import read_str
from clochette.provider.microsoft.configuration.MicrosoftSource import MicrosoftSource
from clochette.provider.microsoft.dto.MicrosoftCalendar import MicrosoftCalendar


class MicrosoftSourceConfigurationService(IProviderConfigurationMapper[MicrosoftSource]):
    _PROVIDER_ID = "microsoft"

    def match(self, section: SectionProxy) -> bool:
        # Check legacy format
        authentication = read_str(section, "authentication", "").lower()
        return authentication == self._PROVIDER_ID

    def read(self, section: SectionProxy) -> MicrosoftSource:
        ids_str = read_str(section, "calendars_ids", "{}")
        ids = json.loads(ids_str)

        calendars: dict[MicrosoftCalendar, bool] = {}
        for cal_id, cal_data in ids.items():
            if isinstance(cal_data, dict):
                summary = cal_data.get("summary", "")
                checked = cal_data.get("checked", False)
                calendar = MicrosoftCalendar(cal_id, summary)
                calendars[calendar] = checked

        return MicrosoftSource(calendars)

    def write(self, source: MicrosoftSource) -> dict[str, str]:
        calendars_dict: dict[str, dict[str, Any]] = {}
        for cal, checked in source.calendars.items():
            calendars_dict[cal.id] = {
                "summary": cal.summary,
                "checked": checked,
            }

        return {
            "authentication": self._PROVIDER_ID,
            "calendars_ids": json.dumps(calendars_dict),
        }
