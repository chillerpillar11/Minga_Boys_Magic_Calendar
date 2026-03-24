import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

CALENDAR_ID = "c_7f090f10dbb843c0bac91ed58594c85b7ac59c12d1764b34a586dd01ca7a8502@group.calendar.google.com"
EVENTS_PAGE = "https://racoon-rises.com/pages/events"


def _extract_google_api_key():
    """
    Holt den Google API Key direkt aus dem HTML der Events-Seite.
    Der Key ist öffentlich eingebettet, daher sicher zu verwenden.
    """
    try:
        html = requests.get(EVENTS_PAGE, timeout=10).text
    except:
        return None

    # Suche nach einem Google API Key im HTML
    match = re.search(r"AIza[0-9A-Za-z\-_]{35}", html)
    return match.group(0) if match else None


def fetch_racoon_events():
    events = []

    api_key = _extract_google_api_key()
    if not api_key:
        print("Fehler: Kein Google API Key auf der Racoon-Seite gefunden.")
        return []

    base_url = (
        "https://content.googleapis.com/calendar/v3/calendars/"
        + CALENDAR_ID
        + "/events"
    )

    now = datetime.now(TZ)
    one_year = now + timedelta(days=365)

    params = {
        "timeMin": now.isoformat(),
        "timeMax": one_year.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "2500",
        "showDeleted": "false",
        "key": api_key,
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Fehler beim Laden des Racoon-Google-Calendars:", e)
        return []

    for item in data.get("items", []):
        title = item.get("summary", "")
        title_lower = title.lower()

        # ⭐ Filter: RCQ oder Monthly Legacy
        if not (
            "rcq" in title_lower
            or "regional championship qualifier" in title_lower
            or "monthly legacy" in title_lower
        ):
            continue

        start_info = item.get("start", {})
        end_info = item.get("end", {})

        if "dateTime" not in start_info or "dateTime" not in end_info:
            continue

        start_dt = datetime.fromisoformat(start_info["dateTime"]).astimezone(TZ)
        end_dt = datetime.fromisoformat(end_info["dateTime"]).astimezone(TZ)

        desc = item.get("description", "")
        url = item.get("htmlLink", "")

        events.append({
            "title": f"Racoon Rises – {title}",
            "start": start_dt,
            "end": end_dt,
            "location": "Racoon Rises, Ulm",
            "url": url,
            "description": desc,
            "all_day": False
        })

    return events
