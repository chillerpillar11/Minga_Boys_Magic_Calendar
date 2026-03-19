import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

print("Script gestartet")

# Wizards API: RCQs + Store Championships im Umkreis München
WIZARDS_URL = (
    "https://locator.wizards.com/api/search?"
    "query=81547%20M%C3%BCnchen-Untergiesing-Harlaching,%20Deutschland"
    "&distance=100"
    "&searchType=magic-events"
    "&tag=regional_championship_qualifier"
    "&tag=store_championship"
    "&sort=date"
    "&sortDirection=Asc"
    "&page=1"
)

# MTGO Update Seite
MTGO_URL = "https://mtgoupdate.com/"


def fetch_wizards_events():
    print("Hole Wizards Events...")

    events = []

    # Browser-Header, damit Wizards uns nicht blockiert
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Referer": "https://locator.wizards.com/",
    }

    resp = requests.get(WIZARDS_URL, headers=headers)

    # Wenn Wizards HTML statt JSON liefert → blockiert
    if "text/html" in resp.headers.get("Content-Type", ""):
        print("⚠️ Wizards API liefert HTML statt JSON – blockiert.")
        return events

    data = resp.json()

    for item in data.get("results", []):
        title = item.get("title")
        start = item.get("startDate")
        store = item.get("store", {}).get("name", "")
        address = item.get("store", {}).get("address", "")

        if not start:
            continue

        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))

        e = Event()
        e.name = f"{title} – {store}"
        e.begin = start_dt
        e.location = address
        e.description = "WPN Event (RCQ oder Store Championship)"
        events.append(e)

    print(f"Wizards Events gefunden: {len(events)}")
    return events


def fetch_mtgo_events():
    print("Hole MTGO Events...")

    events = []
    resp = requests.get(MTGO_URL)
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.select("table tbody tr")
    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue

        name, format_, date_str, time_str = cols[:4]

        # Nur Modern-Events
        if "Modern" not in format_:
            continue

        dt_str = f"{date_str} {time_str}"
        try:
            start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        e = Event()
        e.name = f"MTGO {name} ({format_})"
        e.begin = start_dt
        e.description = "MTGO Modern Event"
        events.append(e)

    print(f"MTGO Events gefunden: {len(events)}")
    return events


def generate_ics():
    print("Erzeuge Kalender...")

    cal = Calendar()

    wizards = fetch_wizards_events()
    mtgo = fetch_mtgo_events()

    print("Wizards Events:", len(wizards))
    print("MTGO Events:", len(mtgo))

    for e in wizards:
        cal.events.add(e)

    for e in mtgo:
        cal.events.add(e)

    print("Schreibe magic.ics...")
    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("Fertig! Datei erzeugt.")


if __name__ == "__main__":
    generate_ics()