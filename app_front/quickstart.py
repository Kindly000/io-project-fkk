import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.

class Calendar:
    def __init__(self):
        self.SCOPES = ["https://www.googleapis.com/auth/calendar"]
        self.creds = None
        self.set_credentials()


    def main(self):
      """Shows basic usage of the Google Calendar API.
      Prints the start and name of the next 10 events on the user's calendar.
      """
      creds = None
      # The file token.json stores the user's access and refresh tokens, and is
      # created automatically when the authorization flow completes for the first
      # time.
      if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)
      # If there are no (valid) credentials available, let the user log in.
      if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
        else:
          flow = InstalledAppFlow.from_client_secrets_file(
              "../secrets/credentials.json", self.SCOPES
          )
          creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
          token.write(creds.to_json())

      try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
          print("No upcoming events found.")
          return

        # Prints the start and name of the next 10 events
        for event in events:
          start = event["start"].get("dateTime", event["start"].get("date"))
          print(start, event["summary"])

      except HttpError as error:
        print(f"An error occurred: {error}")

    def set_credentials(self):
        try:
            if os.path.exists("token.json"):
                self.creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "../secrets/credentials.json", self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(self.creds.to_json())
        except Exception as e:
            print(f"google auth error: {e}")
            exit(-1)


    def add_event(self,title,date,url):
        try:
            # Refer to the Python quickstart on how to setup the environment:
            # https://developers.google.com/calendar/quickstart/python
            # Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
            # stored credentials.
            service = build("calendar", "v3", credentials=self.creds)

            event = {
                'summary': f"{title}",
                'location': 'on-line',
                'description': f"{url}",
                'start': {
                    'dateTime': date,#time +8h
                    'timeZone': 'Europe/Warsaw',
                },
                'end': {
                    'dateTime': date,
                    'timeZone': 'Europe/Warsaw',
                },
                'recurrence': [
                    # 'RRULE:FREQ=DAILY;COUNT=2'
                ],
                'attendees': [
                    # {'email': 'lpage@example.com'},
                    # {'email': 'sbrin@example.com'},
                ],
                'reminders': {
                    # 'useDefault': False,
                    # 'overrides': [
                    #     {'method': 'email', 'minutes': 24 * 60},
                    #     {'method': 'popup', 'minutes': 10},
                    # ],
                },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            print('Event created: %s' % (event.get('htmlLink')))
            'Event created: %s' % (event.get('htmlLink'))


        except HttpError as error:
            print(f"An error occurred: {error}")



if __name__ == "__main__":
  Calendar().add_event("test","2021-01-01","https://www.youtube.com/watch?v=dQw4w9WgXcQ")