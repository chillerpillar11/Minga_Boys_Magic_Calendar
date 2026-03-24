import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

MTGO_URL = "https://www.mtgo.com/calendar.ics?format=Modern"


def parse_ics_datetime(value: str):
    """
    Parses ICS datetime strings like:
    - 20260412T110000Z
    - 20260412T110000
    - 20260403 (all-day)
    Returns (datetime, all_day: bool)
    """
    value = value.strip()

    # All-day date (no time part)
    if "T" not in value:
        dt = datetime.strptime(value, "%Y%m%d").replace(tzinfo=TZ)
        return dt, True

    # UTC with Z
    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=TZ)
        return dt, False

    # Local time without Z
    dt = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=TZ)
    return dt, False


def fetch_mtgo_events():
    try:
        response = requests.get(MTGO_URL, timeout=10)
        response.raise_for_status()
        ics = response.text
    except Exception as e:
        print("Fehler beim Laden des MTGO ICS:", e)
        return []

    events = []
    current = {}
    in_event = False

    for line in ics.splitlines():
        line = line.strip()

        if line == "BEGIN:VEVENT":
            in_event = True
            current = {}
            continue

        if line == "END:VEVENT":
            in_event = False

            title = current.get("SUMMARY", "")
            if not title:
                continue

            # Feed ist schon Modern, aber zur Sicherheit:
            if "modern" not in title.lower():
                continue

            start = current.get("DTSTART")
            end = current.get("DTEND")
            all_day = current.get("ALL_DAY", False)

            if not start or not end:
                continue

            events.append({
                "title": title,
                "start": start,
                "end": end,
                "location": "MTGO",
                "url": current.get("URL", ""),
                "description": current.get("DESCRIPTION", ""),
                "all_day": all_day,
            })
            continue

        if not in_event:
            continue

        if line.startswith("SUMMARY:"):
            current["SUMMARY"] = line[len("SUMMARY:"):].strip()

        elif line.startswith("DTSTART"):
            _, value = line.split(":", 1)
            dt, all_day = parse_ics_datetime(value)
            current["DTSTART"] = dt
            if all_day:
                current["ALL_DAY"] = True

        elif line.startswith("DTEND"):
            _, value = line.split(":", 1)
            dt, all_day = parse_ics_datetime(value)
            current["DTEND"] = dt
            if all_day:
                current["ALL_DAY"] = True

        elif line.startswith("DESCRIPTION:"):
            current["DESCRIPTION"] = line[len("DESCRIPTION:"):].strip()

        elif line.startswith("URL:"):
            current["URL"] = line[len("URL:"):].strip()

    return events
