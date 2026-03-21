import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

DEBUG = True


def dbg(*args):
    if DEBUG:
        print("[MTGO DEBUG]", *args)


# ---------------------------------------------------------
# Modern-Filter (Premodern ausgeschlossen)
# ---------------------------------------------------------
def is_modern_event(title: str) -> bool:
    t = title.lower()

    if "premodern" in t:
        return False

    return "modern" in t


# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------
def parse_day_suffix(day_str: str) -> int:
    return int(re.sub(r"(st|nd|rd|th)$", "", day_str))


def parse_time_string(t: str):
    t = t.strip().lower()

    if t == "noon":
        return 12, 0
    if t == "midnight":
        return 0, 0

    m = re.match(r"(\d{1,2})(?::(\d{2}))?(am|pm)", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)

        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return hour, minute

    return None


def extract_event(text: str):
    parts = text.split(" ", 1)
    if len(parts) < 2:
        return None

    time_str = parts[0]
    title = parts[1].strip()

    tm = parse_time_string(time_str)
    if not tm:
        return None

    hour, minute = tm
    return hour, minute, title


# ---------------------------------------------------------
# Monat/Jahr aus aktuellem Datum ableiten
# ---------------------------------------------------------
def infer_month_year(day_number: int):
    today = datetime.now(TZ)
    dbg("infer_month_year: today =", today, "day_number =", day_number)

    if day_number >= today.day - 3:
        dbg("→ gleicher Monat/Jahr:", today.month, today.year)
        return today.month, today.year

    next_month = today.month + 1
    next_year = today.year

    if next_month == 13:
        next_month = 1
        next_year += 1

    dbg("→ nächster Monat/Jahr:", next_month, next_year)
    return next_month, next_year


# ---------------------------------------------------------
# Eine Woche scrapen
# ---------------------------------------------------------
def scrape_week(container):
    events = []

    dbg("Scrape Woche gestartet")

    first_legend = container.select_one("#day0 legend span")
    dbg("first_legend:", first_legend)

    if not first_legend:
        dbg("Kein first_legend gefunden")
        return []

    first_text = first_legend.get_text(strip=True)
    dbg("first_legend text:", first_text)

    m = re.match(r"[A-Za-z]+\s+(\d{1,2}[a-z]{2})", first_text)
    if not m:
        dbg("Konnte first_legend nicht parsen")
        return []

    first_day_number = parse_day_suffix(m.group(1))
    dbg("first_day_number:", first_day_number)

    month, year = infer_month_year(first_day_number)

    for day_index in range(7):
        day_div = container.select_one(f"#day{day_index}")
        dbg(f"day{day_index} gefunden:", bool(day_div))
        if not day_div:
            continue

        legend = day_div.select_one("legend span")
        dbg(f"legend day{day_index}:", legend)
        if not legend:
            continue

        legend_text = legend.get_text(strip=True)
        dbg(f"legend_text day{day_index}:", legend_text)

        m = re.match(r"[A-Za-z]+\s+(\d{1,2}[a-z]{2})", legend_text)
        if not m:
            dbg("Konnte legend nicht parsen:", legend_text)
            continue

        day_number = parse_day_suffix(m.group(1))
        dbg(f"day_number day{day_index}:", day_number)

        for font in day_div.select("font"):
            text = font.get_text(strip=True)
            dbg("Raw event text:", text)

            parsed = extract_event(text)
            dbg("Parsed:", parsed)

            if not parsed:
                dbg("Konnte Event nicht parsen:", text)
                continue

            hour, minute, title = parsed
            dbg("Event erkannt:", hour, minute, title)

            if not is_modern_event(title):
                dbg("Nicht Modern, übersprungen:", title)
                continue

            dbg("Modern-Event akzeptiert:", title)

            t = title.lower()
            if "showcase" in t:
                tag = "[Showcase] "
            elif "prelim" in t:
                tag = "[Prelim] "
            elif "modern" in t:
                tag = "[Modern] "
            else:
                tag = ""

            final_title = f"{tag}MTGO – {title.strip()}"
            dbg("Finaler Titel:", final_title)

            start = datetime(year, month, day_number, hour, minute, tzinfo=TZ)
            end = start + timedelta(hours=3)

            dbg("Start/Ende:", start, end)

            events.append({
                "title": final_title,
                "start": start,
                "end": end,
                "location": "Magic Online",
                "url": "https://mtgoupdate.com",
                "description": "",
            })

    dbg("Anzahl Events in Woche:", len(events))
    return events


# ---------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------
def fetch_mtgo_events():
    print("Hole MTGO Events...")

    url = "https://mtgoupdate.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler bei MTGO:", e)
        return []

    dbg("Seite geladen, Länge:", len(resp.text))

    soup = BeautifulSoup(resp.text, "html.parser")

    containers = soup.select("div.container")
    dbg("Gefundene container:", len(containers))

    if not containers:
        print("MTGO: Kein div.container gefunden")
        return []

    container = containers[0]
    dbg("Nutze container 0")

    week_events = scrape_week(container)
    print(f"MTGO Modern Events gefunden: {len(week_events)}")
    return week_events
