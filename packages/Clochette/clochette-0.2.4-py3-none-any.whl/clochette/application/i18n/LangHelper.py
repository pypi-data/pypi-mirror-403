from datetime import date, timedelta

import humanize


def precise_delta(delta: timedelta) -> str:
    return humanize.precisedelta(delta)


def natural_day(value: date) -> str:
    return humanize.naturalday(value)


def apply_i18n(lang: str) -> None:
    humanize.i18n.activate(lang)  # pyright: ignore [reportAttributeAccessIssue]
