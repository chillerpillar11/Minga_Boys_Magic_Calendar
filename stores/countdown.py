import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

BASE_URL = "https://countdown-spielewelt.de/events/liste/seite/{}/"


def fetch_countdown_events():
    events = []
    page = 1

    while True:
        url = BASE_URL.format(page)
        print(f"Lade Countdown-Seite {page}: {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print("Fehler beim Laden:", e)
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # Alle Event-Container
        containers = soup.select(".tribe-events-calendar-list__event-details")

        if not containers:
            break  # keine Events mehr → fertig

        for c in containers:
            # Titel + URL
            a = c.select_one(".tribe-events-calendar-list__event-title a")
            if not a:
                continue

            title_raw = a.get_text(strip=True)
            title_lower = title_raw.lower()

            # ⭐ Filter: Nur Legacy-Turniere
            if "monatliches magic legacy turnier" not in title_lower:
                continue

            # Companion-Code extrahieren
            match = re.search(r"\b([A-Z0-9]{6,8})\b$", title_raw)
            code = match.group(1) if match else None

            # Titel bereinigen
            clean_title = title_raw.replace(code, "").strip() if code else title_raw

            # Event-URL
            event_url = a.get("href", "")

            # Datum + Zeiten
            time_tag = c.select_one("time.tribe-events-calendar-list__event-datetime")
            if not time_tag:
                continue

            date_str = time_tag.get("datetime")  # z.B. 2026-04-26
            start_span = c.select_one(".tribe-event-date-start")
            end_span = c.select_one(".tribe-event-time")

            if not (date_str and start_span and end_span):
                continue

            # Startzeit extrahieren
            # Beispiel: "26 April | 11:00"
            start_text = start_span.get_text(strip=True)
            start_time = start_text.split("|")[-1].strip()

            # Endzeit
            end_time = end_span.get_text(strip=True)

            # Datetime bauen
            start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
            end_dt = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)

            # Beschreibung
            desc_tag = c.select_one(".tribe-events-calendar-list__event-description p")
            desc_text = desc_tag.get_text(strip=True) if desc_tag else ""

            # Companion-Link
            companion_link = ""
            if code:
                companion_link = f"https://magic.wizards.com/en/products/companion-app/tournament/{code}"

            description = desc_text
            if code:
                description += f"\nCompanion Code: {code}\nCompanion Link: {companion_link}"

            events.append({
                "title": clean_title,
                "start": start_dt,
                "end": end_dt,
                "location": "Countdown Spielewelt Landsberg",
                "url": event_url,
                "description": description,
                "all_day": False
            })

        page += 1

    return events
