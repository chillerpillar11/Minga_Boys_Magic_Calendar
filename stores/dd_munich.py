import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

API_URL = "https://www.dd-munich.de/_api/wix-one-events-server/web/paginated-events/viewer"

# ---------------------------------------------------------
# Modern/RCQ Filter (Premodern ausgeschlossen!)
# ---------------------------------------------------------
def is_modern_or_rcq(title: str) -> bool:
    title = title.lower()

    # Premodern explizit ausschließen
    if "premodern" in title:
        return False

    include = [
        "modern",
        "rcq",
        "regional championship qualifier",
        "qualifier",
    ]

    exclude = [
        "commander",
        "edh",
        "draft",
        "sealed",
        "prerelease",
        "pre-release",
        "standard",
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
        "spearwars",
        "spear wars",
        "spearhead",
        "tabletop",
        "boardgame",
        "brettspiel",
    ]

    if any(x in title for x in exclude):
        return False

    return any(x in title for x in include)


# ---------------------------------------------------------
# API Pagination
# ---------------------------------------------------------
def fetch_all_events():
    print("\n--- DEBUG: API Pagination ---")

    offset = 0
    limit = 16
    all_events = []

    while True:
        params = {
            "offset": offset,
            "limit": limit,
            "filter": 1,
            "byEventId": "false",
            "members": "true",
            "paidPlans": "true",
            "locale": "de-de",
            "recurringFilter": 1,
            "filterType": 2,
            "sortOrder": 0,
            "fetchBadges": "true",
            "draft": "false",
            "compId": "TPASection_lxt9b797",
        }

        print(f"  → Lade Events mit offset={offset}")

        try:
            resp = requests.get(API_URL, params=params, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print("Fehler beim API-Request:", e)
            break

        data = resp.json()
        events = data.get("events", [])

        print(f"    Gefundene Events: {len(events)}")

        if not events:
            break

        all_events.extend(events)

        # Wenn weniger als 16 Events → letzte Seite
        if len(events) < limit:
            break

        offset += limit

    print(f"Gesamt Events geladen: {len(all_events)}")
    return all_events


# ---------------------------------------------------------
# Modern-Events extrahieren
# ---------------------------------------------------------
def fetch_dd_munich_events():
    print("Hole Events von Deck & Dice / DD Munich...")

    raw_events = fetch_all_events()
    final = []

    print("\n--- DEBUG: Modern-Filter ---")

    for ev in raw_events:
        title = ev.get("title", "").strip()

        print(f"  → Prüfe: {title}")

        if not is_modern_or_rcq(title):
            print("    ✗ kein Modern/RCQ")
            continue

        sched = ev.get("scheduling", {}).get("config", {})
        start_str = sched.get("startDate")
        end_str = sched.get("endDate")

        if not start_str or not end_str:
            print("    ✗ keine Start/Endzeit")
            continue

        start = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(TZ)
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00")).astimezone(TZ)

        print("    ✓ Modern-Event übernommen")

        final.append({
            "title": title,
            "start": start,
            "end": end,
            "location": "Deck & Dice Munich",
            "url": "https://www.dd-munich.de",
            "description": ev.get("description", ""),
        })

    print(f"\n--- DEBUG: FINAL ---")
    print(f"Gesamt Modern/RCQ Events: {len(final)}")
    for ev in final:
        print(f"  ✓ {ev['title']} @ {ev['start']}")

    return final
