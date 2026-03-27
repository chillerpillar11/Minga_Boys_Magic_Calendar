import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

MTGO_URL = "https://www.mtgo.com/calendar.ics?format=Modern"


def parse_ics_datetime(value: str):
    value = value.strip()

    if "T" not in value:
        dt = datetime.strptime(value, "%Y%m%d").replace(tzinfo=TZ)
        return dt, True

    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=TZ)
        return dt, False

    dt = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=TZ)
    return dt, False


def is_real_modern(title: str):
    t = title.lower()

    # ❌ Premodern rausfiltern
    if "premodern" in t:
        return False

    # ✔ echtes Modern erkennen (als Wort)
    # Beispiele:
    # "Modern League" → OK
    # "MTGO Modern Challenge" → OK
    # "Premodern League" → bereits oben gefiltert
    words = t.replace("-", " ").replace("_", " ").split()
    return "modern" in words or t.startswith("modern") or " modern " in t


def fetch_mtgo_events():
    ics = None

    for attempt in range(3):
        try:
            response = requests.get(MTGO_URL, timeout=15)
            response.raise_for_status()

            if not response.text.strip():
                print(f"MTGO: Leere Antwort (Versuch {attempt+1}/3)")
                continue

            ics = response.text
            break

        except Exception as e:
            print(f"MTGO: Fehler beim Laden (Versuch {attempt+1}/3): {e}")

    if not ics:
        print("MTGO: Keine Daten nach 3 Versuchen.")
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

            # ⭐ Neuer, korrekter Modern-Check
            if not is_real_modern(title):
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
