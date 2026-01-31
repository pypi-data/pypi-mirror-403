# 🔔 Clochette

Clochette (from the French word meaning little bell) is a desktop reminder application written in Python and QT.
The application is currently in beta.

## Features

- Works with WebCal/ICS files
- Authentications supported:
    - Public URLs
    - Basic authentication
    - Google Agenda via OAuth2
    - Microsoft Outlook (using Microsoft Graph) via OAuth2
- Allow overriding events' alarms
- Allows customising the multiple snooze values
- Snooze events for a specific duration from now
- Snooze events at a specific time before the event start date

## Screenshot

![Screenshot](https://gitlab.com/sketyl/clochette/-/raw/main/screenshot.png)

## Languages

Clochette currently includes the following languages:

- English
- French
- Vietnamese

# Install and run

Make sure you have `python3` and `uv` installed on your system. After cloning the git repository, navigate to the
Clochette folder, then run:

    make install
    make run

# Limitations

- currently only tested on Linux.

# License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

# Resources:

## Retrieving the calendar URL

- [Outlook](https://support.microsoft.com/en-us/office/share-an-outlook-calendar-as-view-only-with-others-353ed2c1-3ec5-449d-8c73-6931a0adab88#bkmk_newpublish)
- [Google Agenda](https://support.google.com/calendar/answer/37083?hl=en#zippy=%2Cmark-your-calendar-as-public%2Cshare-a-link)
- [Fastmail](https://www.fastmail.help/hc/en-us/articles/360060590793-Calendar-sharing)
- [ICloud](https://support.apple.com/en-gb/guide/icloud/mm6b1a9479/icloud) under `Share a calendar publicly`
- [Zoho](https://www.zoho.com/calendar/help/share-calendars.html) under `URL Sharing`

## References:

- https://www.digi.com/resources/documentation/digidocs/90001488-13/reference/r_iso_8601_duration_format.htm
- https://www.ietf.org/rfc/rfc2445.txt