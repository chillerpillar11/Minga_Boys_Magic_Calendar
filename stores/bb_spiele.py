import requests
from datetime import datetime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Berlin")


def fetch_bb_spiele_events():
    url = "https://www.bb-spiele.de/api/events"  # deine bestehende URL hier
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for item in data:
        # Passe diese Keys an deine bestehende Struktur an
        start = datetime.fromisoformat(item["start"]).replace(tzinfo=TZ)
        end = datetime.fromisoformat(item["end"]).replace(tzinfo=TZ)

        events.append(
            {
                "title": item["title"],
                "start": start,
                "end": end,
                "location": "BB-Spiele",
                "url": item.get("url", "https://www.bb-spiele.de"),
                "description": item.get("description", ""),
            }
        )

    print(f"BB-Spiele Events gefunden: {len(events)}")
    return events
