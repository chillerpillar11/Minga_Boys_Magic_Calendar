import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://www.fanfinity.gg/magic-the-gathering/"

def fetch_fanfinity_events():
    events = []

    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("Fanfinity Fehler:", e)
        return events

    soup = BeautifulSoup(response.text, "html.parser")

    # Jeder Event ist ein Elementor Loop Item
    items = soup.select('div[data-elementor-type="loop-item"]')
    print(f"Fanfinity: Gefundene Loop-Items: {len(items)}")

    for item in items:
        # Titel
        title_tag = item.select_one("h1.elementor-heading-title a, h2.elementor-heading-title a")
        if not title_tag:
            continue

        title = title_tag.text.strip()
        url = title_tag["href"]

        # Datumsteile holen
        date_tags = item.select(".elementor-post-info__item--type-custom")

        # Erwartet: [0] Tag, [1] Monat+Jahr, [2] Read more →
        if len(date_tags) < 2:
            continue

        day_text = date_tags[0].text.strip()
        month_year_text = date_tags[1].text.strip()

        # Tag extrahieren
        try:
            day = int(day_text)
        except:
            print("Fanfinity: Konnte Tag nicht parsen:", day_text)
            continue

        # Monat + Jahr extrahieren
        try:
            month_year = datetime.strptime(month_year_text, "%B %Y")
        except:
            print("Fanfinity: Konnte Monat/Jahr nicht parsen:", month_year_text)
            continue

        # Startdatum
        start = month_year.replace(day=day)

        # ICS-Enddatum ist EXKLUSIV → +3 Tage für Fr–So
        end = start + timedelta(days=3)

        events.append({
            "title": title,
            "url": url,
            "start": start,   # All-Day: nur Datum
            "end": end,       # All-Day: exklusives Enddatum
            "store": "Fanfinity",
            "location": "Online",
            "description": f"Event von Fanfinity: {title}\n{url}",
            "all_day": True
        })

    print(f"Fanfinity Events gefunden: {len(events)}")
    return events
