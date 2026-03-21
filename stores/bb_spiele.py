import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")


def is_modern_or_rcq(title: str) -> bool:
    """Filtert nur Modern-Events oder RCQs heraus."""
    title = title.lower()

    include = [
        "rcq",
        "regional championship qualifier",
        "qualifier",
        "store championship",
        "championship",
    ]

    exclude = [
        "commander",
        "edh",
        "draft",
        "prerelease",
        "pre-release",
        "pauper",
        "booster",
        "casual",
        "painting",
        "workshop",
        "warhammer",
        "40k",
        "age of sigmar",
        "pokémon",
        "pokemon",
        "lorcana",
        "yu-gi-oh",
        "yugioh",
        "flesh and blood",
        "fab",
        "one piece",
        "star wars",
    ]

    if any(x in title for x in exclude):
        return False

    return any(x in title for x in include)


def fetch_bb_spiele_events():
    print("Hole Events von BB-Spiele...")

    url = "https://www.bb-spiele.de/events"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler bei BB-Spiele:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for card in soup.select(".events-card"):
        title_el = card.select_one(".netzp-events-title")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)

        # Filter anwenden
        if not is_modern_or_rcq(title):
            continue

        date_el = card.select_one(".icon-calendar + span")
        if not date_el:
            continue

        raw = date_el.get_text(strip=True)
        parts = raw.split(",")
        if len(parts) < 3:
            continue

        date_str = parts[1].strip()
        time_str = parts[2].strip().split("-")[0].strip()

        try:
            start = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M").replace(tzinfo=TZ)
        except:
            continue

        end = start + timedelta(hours=3)

        loc_el = card.select_one(".icon-marker + b")
        location = loc_el.get_text(strip=True) if loc_el else "BB-Spiele"

        desc_el = card.select_one(".card-text.lead")
        description = desc_el.get_text(strip=True) if desc_el else ""

        events.append({
            "title": title,
            "start": start,
            "end": end,
            "location": location,
            "url": "https://www.bb-spiele.de",
            "description": description,
        })

    print(f"BB-Spiele Modern/RCQ Events gefunden: {len(events)}")
    return events
