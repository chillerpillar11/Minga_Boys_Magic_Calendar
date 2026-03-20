from ics import Calendar, Event
from datetime import datetime

from deck_and_dice import fetch_deck_and_dice_events
from bb_spiele import fetch_bb_spiele_events
from funtainment import fetch_funtainment_events

def main():
    print("Script gestartet")
    print("Erzeuge Kalender...")

    all_events = []

    all_events.extend(fetch_deck_and_dice_events())
    all_events.extend(fetch_bb_spiele_events())
    all_events.extend(fetch_funtainment_events())

    print(f"Gesamtanzahl Events: {len(all_events)}")

    cal = Calendar()

    for ev in all_events:
        e = Event()
        e.name = ev["title"]
        e.begin = ev["start"]
        e.end = ev["end"]
        e.location = ev["location"]
        e.url = ev["url"]
        e.description = ev["description"]
        cal.events.add(e)

    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("ICS erzeugt: magic.ics")

if __name__ == "__main__":
    main()
