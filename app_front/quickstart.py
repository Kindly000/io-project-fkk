import datetime
import os.path

import app_backend.logging_f as logg

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.

class Calendar:
    def __init__(self):
        """Initializes the Calendar object with API scope and credentials."""
        self.SCOPES = [
            "https://www.googleapis.com/auth/calendar"]  # Defines the Google Calendar API scope (permissions)
        self.creds = None  # To store credentials for user authentication
        self.set_credentials()  # Calls method to set up credentials for the user

    def main(self):
        """
        Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None

        # Check if token.json exists (saved from previous authentication), and load credentials
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

        # If no valid credentials, prompt the user to authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())  # Refresh credentials if expired
            else:
                # If credentials are invalid or don't exist, initiate authentication flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    "../secrets/credentials.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)  # Opens the browser for user authentication

            # Save credentials for future use in token.json
            with open("token.json", "w") as token:
                token.write(creds.to_json())  # Save the access/refresh token

        try:
            # Build the Google Calendar API service with the credentials
            service = build("calendar", "v3", credentials=creds)

            # Get the current time in UTC and use it for querying upcoming events
            now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' denotes UTC time
            print("Getting the upcoming 10 events")

            # Fetch events from Google Calendar API
            events_result = (
                service.events()
                .list(
                    calendarId="primary",  # Primary calendar
                    timeMin=now,  # Only events after the current time
                    maxResults=10,  # Get the next 10 events
                    singleEvents=True,  # Avoid recurring events, get each instance
                    orderBy="startTime",  # Sort events by start time
                )
                .execute()
            )

            # Retrieve the list of events from the response
            events = events_result.get("items", [])

            # If no events found, print a message and return
            if not events:
                print("No upcoming events found.")
                return

            # Print the start time and name of the next 10 events
            for event in events:
                start = event["start"].get("dateTime",
                                           event["start"].get("date"))  # Get start time (with or without time)
                print(start, event["summary"])  # Print start time and event summary (name)

        except HttpError as error:
            print(f"An error occurred: {error}")  # Handle any API errors

    def set_credentials(self):
        """
        Sets up and manages user credentials for authentication.
        Retrieves stored credentials or prompts the user to authenticate.
        """
        try:
            # Check if token.json exists and load credentials
            if os.path.exists("token.json"):
                self.creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

            # If no valid credentials, prompt the user to log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())  # Refresh expired credentials
                else:
                    # If no valid credentials, initiate the login flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "../secrets/credentials.json", self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)  # Start authentication flow

                # Save the credentials for the next use
                with open("token.json", "w") as token:
                    token.write(self.creds.to_json())

        except Exception as e:
            # Handle exceptions related to authentication
            logg.app_logs(f"[ERROR] Google auth error: {e}")

            exit(-1)  # Exit the program if authentication fails

    def add_event(self, title, date, url) -> dict:
        """
        Adds a new event to the Google Calendar.
        Returns a dictionary indicating if the event was created successfully.
        """
        try:
            # Build the service object using the credentials
            service = build("calendar", "v3", credentials=self.creds)

            # Define the event details
            event = {
                'summary': f"{title}",  # Event title
                'location': 'on-line',  # Event location (can be a physical address or URL)
                'description': f"{url}",  # Event description (e.g., URL or additional info)
                'start': {
                    'dateTime': date,  # Start date and time of the event
                    'timeZone': 'Europe/Warsaw',  # Set the time zone for the event
                },
                'end': {
                    'dateTime': date,  # End date and time of the event (same as start time in this case)
                    'timeZone': 'Europe/Warsaw',
                },
                # You can add recurrence, attendees, and reminders here if needed
            }

            # Insert the event into the calendar and execute the API call
            event = service.events().insert(calendarId='primary', body=event).execute()
            logg.app_logs(f"[SUCCESS] Event created: {event.get('htmlLink')}")

            # Return a success response with the event link
            return {"is_created": True, "link": event.get('htmlLink')}

        except Exception as e:
            # Handle any errors that occur during the event creation process
            logg.app_logs(f"[Error] An error occurred: {e}")

        # Return a failure response if event creation fails
        return {"is_created": False, "link": None}


# The main execution point
if __name__ == "__main__":
    # Example usage of the add_event method
    # This adds a test event with the current date and a YouTube link as the URL
    print(Calendar().add_event("test", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                               "https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
