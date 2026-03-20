import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re


TZ = ZoneInfo("Europe/Berlin")

MONTHS_DE = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _parse_date_from_aria(aria_label: str) -> datetime.date:
    # Beispiel: "21. März, Samstag. 1 Veranstaltung, wähle aus, um mehr zu sehen"
    # Wir holen uns "21. März"
    m = re.match(r"\s*(\d{1,2})\.\s+([A-Za-zäöüÄÖÜ]+)", aria_label)
    if not m:
        raise ValueError(f"Konnte Datum aus aria-label nicht parsen: {aria_label!r}")

    day = int(m.group(1))
    month_name = m.group(2).lower()
    month = MONTHS_DE[month_name]

    # Jahr aus data-hook holen ist robuster – das machen wir im Aufrufer
    # Hier geben wir nur Tag/Monat zurück, Jahr kommt später
    return day, month


def fetch_dd_munich_events():
    url = "https://www.dd-munich.de/event-list"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CalendarBot/1.0; +https://github.com/...)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    events = []

    # Jede Kalenderzelle
    for cell in soup.select('[data-hook^="calendar-cell-"]'):
        aria = cell.get("aria-label", "")
        data_hook = cell.get("data-hook", "")

        # data-hook enthält ISO‑Datum, z.B. calendar-cell-2026-03-20T23:00:00.000Z
        m = re.search(r"calendar-cell-(\d{4})-(\d{2})-(\d{2})T", data_hook)
        if not m:
            continue
        year = int(m.group(1))

        try:
            day, month = _parse_date_from_aria(aria)
        except Exception:
            continue

        # Basisdatum (ohne Uhrzeit)
        base_date = datetime(year, month, day, tzinfo=TZ)

        # In der Zelle können mehrere Events sein:
        # Zeit: div.B11jYK, Titel: div.OyuNR8
        time_nodes = cell.select("div.B11jYK")
        title_nodes = cell.select("div.OyuNR8")

        # Falls Anzahl nicht matcht, gehen wir konservativ über das Minimum
        for t_node, title_node in zip(time_nodes, title_nodes):
            time_text = t_node.get_text(strip=True)  # z.B. "12:00"
            title = title_node.get_text(strip=True)

            try:
                hour, minute = map(int, time_text.split(":"))
            except Exception:
                # Wenn Zeit nicht parsebar ist, überspringen
                continue

            start = base_date.replace(hour=hour, minute=minute)
            # Endzeit grob +3h (oder was du willst)
            end = start.replace(hour=min(hour + 3, 23))

            events.append(
                {
                    "title": title,
                    "start": start,
                    "end": end,
                    "location": "Deck & Dice Munich",
                    "url": url,
                    "description": "",
                }
            )

    print(f"DD Munich Events gefunden: {len(events)}")
    return events
