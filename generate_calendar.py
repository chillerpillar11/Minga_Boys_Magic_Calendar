import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

print("Script gestartet")


# ---------------------------------------------------------
# BB-SPIELE
# ---------------------------------------------------------
def fetch_bbspiele_events():
    print("Hole Events von BB-Spiele...")

    url = "https://www.bb-spiele.de/events?categories=0196a9a7d19270a89170491be8392535&p=1"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei BB-Spiele:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    items = soup.select(".event-list-item")
    for item in items:
        title_el = item.select_one(".event-title")
        date_el = item.select_one(".event-date")
        loc_el = item.select_one(".event-location")

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_str = date_el.get_text(strip=True).replace("–", "-")
        location = loc_el.get_text(strip=True) if loc_el else "BB Spiele München"

        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y - %H:%M")
        except:
            continue

        e = Event()
        e.name = title
        e.begin = dt
        e.location = location
        e.description = "Event von BB-Spiele"
        events.append(e)

    print(f"BB-Spiele Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# DD MUNICH
# ---------------------------------------------------------
def fetch_ddmunich_events():
    print("Hole Events von DD Munich...")

    url = "https://www.dd-munich.de/event-list"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei DD Munich:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    items = soup.select(".event")
    for item in items:
        title_el = item.select_one("h3")
        date_el = item.select_one(".date")
        loc_el = item.select_one(".location")

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_str = date_el.get_text(strip=True)
        location = loc_el.get_text(strip=True) if loc_el else "DD Munich"

        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        except:
            continue

        e = Event()
        e.name = title
        e.begin = dt
        e.location = location
        e.description = "Event von DD Munich"
        events.append(e)

    print(f"DD Munich Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# FUNTANIMENT
# ---------------------------------------------------------
def fetch_funtainment_events():
    print("Hole Events von Funtainment...")

    url = "https://www.funtainment.de/b2c-shop/tickets?categories=0197f53c9a997cbe8574b9211c0c8eaf&p=1"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei Funtainment:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    items = soup.select(".product--box")
    for item in items:
        title_el = item.select_one(".product--title")
        date_el = item.select_one(".product--price-info")

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_str = date_el.get_text(strip=True)

        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        except:
            continue

        e = Event()
        e.name = title
        e.begin = dt
        e.location = "Funtainment München"
        e.description = "Event von Funtainment"
        events.append(e)

    print(f"Funtainment Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# MAGIC PAPA
# ---------------------------------------------------------
def fetch_magicpapa_events():
    print("Hole Events von MagicPapa...")

    url = "https://www.magicpapa-shop.de/c/events"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei MagicPapa:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    items = soup.select(".product--box")
    for item in items:
        title_el = item.select_one(".product--title")
        date_el = item.select_one(".product--delivery")

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_str = date_el.get_text(strip=True)

        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        except:
            continue

        e = Event()
        e.name = title
        e.begin = dt
        e.location = "MagicPapa München"
        e.description = "Event von MagicPapa"
        events.append(e)

    print(f"MagicPapa Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# GENERATE ICS
# ---------------------------------------------------------
def generate_ics():
    print("Erzeuge Kalender...")

    cal = Calendar()

    bb = fetch_bbspiele_events()
    dd = fetch_ddmunich_events()
    ft = fetch_funtainment_events()
    mp = fetch_magicpapa_events()

    all_events = bb + dd + ft + mp

    print("Gesamtanzahl Events:", len(all_events))

    for e in all_events:
        cal.events.add(e)

    print("Schreibe magic.ics...")
    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("Fertig! Datei erzeugt.")


if __name__ == "__main__":
    generate_ics()
