import requests
from datetime import datetime

API_URL = "https://www.fanfinity.gg/wp-json/wp/v2/event?per_page=100"

def fetch_fanfinity_events():
    events = []

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        # API liefert eine LISTE → prüfen
        if not isinstance(data, list):
            print("Fanfinity API: Unerwartetes Format")
            return events

    except Exception as e:
        print("Fanfinity API Fehler:", e)
        return events

    for item in data:
        # Titel
        title = item.get("title", {}).get("rendered", "").strip()
        url = item.get("link", "")

        # Datum aus ACF
        acf = item.get("acf", {})
        date_str = acf.get("event_date")  # Format: YYYY-MM-DD

        if not date_str:
            continue

        try:
            start = datetime.fromisoformat(date_str)
            end = start.replace(hour=23, minute=59)
        except Exception:
            continue

        events.append({
            "title": title,
            "url": url,
            "start": start,
            "end": end,
            "store": "Fanfinity",
            "location": "Online",
            "description": f"Event von Fanfinity: {title}\n{url}"
        })

    print(f"Fanfinity Events gefunden: {len(events)}")
    return events
