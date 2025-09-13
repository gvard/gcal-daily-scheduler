# gcal-daily-scheduler
Daily schedule with Google Calendar, visualized using Flask

This python application is designed to work with the [E&S Digistar](https://en.wikipedia.org/wiki/Digistar) interface, but can be easily used independently.

Note that the application uses JavaScript code to highlight past and future events (and for something else), so support for JS is desirable.

## Dependencies

* [Flask](https://flask.palletsprojects.com/)
* [Google client library](https://github.com/googleapis/google-api-python-client)

## Installation

```bash
pip install --upgrade Flask google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

For the application to work, you need:
* Get the credentials as json file, see [Authorize credentials for a desktop application](https://developers.google.com/workspace/calendar/api/quickstart/python#authorize_credentials_for_a_desktop_application).
* Specify the path to this json file in the source code: `cal.py`, `FILE_PATH` variable.
* Specify the сalendar ID from the [Google Calendar](https://calendar.google.com/) settings: `cal.py`, `CAL_ID` variable.
* If necessary, specify the IP address and port in `flask_cal.py`, `HOST` and `PORT` variables.
* Launch the application from the command line or using a shortcut on the Windows desktop.

More information on how to interact with the Google Calendar API can be found at:
* [Python quickstart guide](https://developers.google.com/workspace/calendar/api/quickstart/python)
* [Google Calendar API reference](https://developers.google.com/workspace/calendar/api/v3/reference)
