"""Code for making requests to the Google Calendar API and working with Google Calendar events
See Python quickstart guide:
https://developers.google.com/workspace/calendar/api/quickstart/python
Google Calendar API reference:
https://developers.google.com/workspace/calendar/api/v3/reference
"""


from google.oauth2 import service_account
from googleapiclient.discovery import build


TIMEZONE = "Europe/Moscow"
TZ_DELTA = 3  # Time difference in hours for Europe/Moscow timezone


class GoogleCalendar:
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    FILE_PATH = "your_key_filename.json"

    def __init__(self):
        creds = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build("calendar", "v3", credentials=creds)

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar(self, calendar_id):
        calendar_list_entry = {"id": calendar_id}
        return self.service.calendarList().insert(body=calendar_list_entry).execute()

    def list_event(self, calendar_id, start, end):
        return (self.service.events().list(
                calendarId=calendar_id,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
                timeZone=TIMEZONE,
                ).execute())


CAL_ID = "yourcalendaridhere.calendar.google.com"
CAL_WRK_ID = "anothercalendaridhere.calendar.google.com"

# Add calendar once
# Gcal.add_calendar(calendar_id=CAL_ID)
