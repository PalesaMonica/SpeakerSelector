"""Google Calendar integration (OAuth desktop flow) and .ics export."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CREDENTIALS = ROOT / "credentials.json"  # OAuth client downloaded from Google Cloud
TOKEN = ROOT / "token.json"  # created after you sign in once
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

TZ = "Africa/Johannesburg"
START_TIME, END_TIME = "10:00:00", "11:00:00"
TITLE = "Lab Talk"


def has_credentials() -> bool:
    return CREDENTIALS.exists()


def is_connected() -> bool:
    return TOKEN.exists()


def get_service(interactive: bool = True):
    """Return a Calendar API client. Opens a browser for sign-in the first time."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif interactive:
            if not CREDENTIALS.exists():
                raise FileNotFoundError("credentials.json not found in the project folder.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            return None
        TOKEN.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def disconnect() -> None:
    if TOKEN.exists():
        TOKEN.unlink()


def event_body(talk_date: date, speaker: str, email: str = "", invite: bool = False) -> dict:
    d = talk_date.isoformat()
    body = {
        "summary": f"{TITLE}: {speaker}",
        "description": f"Weekly lab talk.\nSpeaker: {speaker}",
        "start": {"dateTime": f"{d}T{START_TIME}", "timeZone": TZ},
        "end": {"dateTime": f"{d}T{END_TIME}", "timeZone": TZ},
        "status": "confirmed",
        "extendedProperties": {"private": {"speakerSelector": "1"}},
    }
    if invite and email:
        body["attendees"] = [{"email": email}]
    return body


def upsert_event(service, calendar_id: str, event_id: str, body: dict, notify: bool = False) -> str:
    """Update the event if it exists, otherwise create it. Returns the event id."""
    from googleapiclient.errors import HttpError

    send = "all" if notify else "none"
    if event_id:
        try:
            ev = service.events().update(
                calendarId=calendar_id, eventId=event_id, body=body, sendUpdates=send
            ).execute()
            return ev["id"]
        except HttpError as e:
            if e.resp.status not in (404, 410):
                raise
    ev = service.events().insert(calendarId=calendar_id, body=body, sendUpdates=send).execute()
    return ev["id"]


def delete_event(service, calendar_id: str, event_id: str) -> None:
    from googleapiclient.errors import HttpError

    if not event_id:
        return
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as e:
        if e.resp.status not in (404, 410):
            raise


def to_ics(rows) -> str:
    """Build an .ics file (works with any calendar app) from schedule rows."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RAIL Lab//Speaker Selector//EN",
        "CALSCALE:GREGORIAN",
    ]
    for r in rows:
        d = r["date"].strftime("%Y%m%d")
        # 10:00–11:00 SAST (UTC+2, no daylight saving) = 08:00–09:00 UTC
        lines += [
            "BEGIN:VEVENT",
            f"UID:lab-talk-{d}@speaker-selector",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{d}T080000Z",
            f"DTEND:{d}T090000Z",
            f"SUMMARY:{TITLE}: {r['speaker']}",
            f"DESCRIPTION:Weekly lab talk. Speaker: {r['speaker']}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
