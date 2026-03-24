import requests
import re
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

def _parse_ics_dt(line: str):
    """
    Parst eine DTSTART/DTEND-Zeile aus ICS.
    Unterstützt:
      - DTSTART:20260327T190000
      - DTSTART;VALUE=DATE:20260327
    """
    _, value = line.split(":", 1)
    value = value.strip()

    # Ganztags-Event (nur Datum)
    if "VALUE=DATE" in line or len(value) == 8:
        dt = datetime.strptime(value, "%Y%m%d")
        # Wir geben trotzdem ein datetime-Objekt zurück, aber ohne Uhrzeit
        return dt.replace(tzinfo=TZ), True  # all_day = True

    # DateTime-Event
    dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
    return dt.replace(tzinfo=TZ), False


def fetch_countdown_events():
    url = "https://countdown-spielewelt.de/?post_type=tribe_events&ical=1&eventDisplay=list"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        raw = response.text
    except Exception as e:
        print("Fehler beim Laden des Countdown-ICS:", e)
        return []

    events = []
    current = {}
    in_event = False

    for line in raw.splitlines():
        line = line.strip()

        if line == "BEGIN:VEVENT":
            in_event = True
            current = {}
            continue

        if line == "END:VEVENT":
            in_event = False

            title_lower = current.get("title", "").strip().lower()

            # ⭐ Filter: Nur Legacy-Turniere
            if "monatliches magic legacy turnier" in title_lower:

                original_title = current.get("title", "").strip()

                # ⭐ Companion-Code extrahieren (z.B. YEJ6RVV)
                match = re.search(r"\b([A-Z0-9]{6,8})\b$", original_title)
                code = match.group(1) if match else None

                # ⭐ Code aus Titel entfernen
                if code:
                    clean_title = original_title.replace(code, "").strip()
                else:
                    clean_title = original_title

                # ⭐ Description setzen (mit Companion-Link)
                desc = ""
                if code:
                    desc = (
                        f"Companion Code: {code}\n"
                        f"Companion Link: https://magic.wizards.com/en/products/companion-app/tournament/{code}"
                    )

                current["title"] = clean_title
                current["description"] = desc
                current.setdefault("location", "Countdown Spielewelt Landsberg")
                current.setdefault("url", "")
                current.setdefault("all_day", current.get("all_day", False))

                events.append(current)

            continue

        if not in_event:
            continue

        # SUMMARY
        if line.startswith("SUMMARY:"):
            current["title"] = line.replace("SUMMARY:", "").strip()

        # DTSTART
        elif line.startswith("DTSTART"):
            dt, all_day = _parse_ics_dt(line)
            current["start"] = dt
            # all_day nur setzen, wenn wir es noch nicht explizit hatten
            current.setdefault("all_day", all_day)

        # DTEND
        elif line.startswith("DTEND"):
            dt, _ = _parse_ics_dt(line)
            current["end"] = dt

        # LOCATION
        elif line.startswith("LOCATION:"):
            current["location"] = line.replace("LOCATION:", "").strip()

        # URL
        elif line.startswith("URL:"):
            current["url"] = line.replace("URL:", "").strip()

    return events
