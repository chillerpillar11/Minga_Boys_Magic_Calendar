from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from stores.bb_spiele import fetch_bb_spiele_events
from stores.funtainment import fetch_funtainment_events
from stores.dd_munich import fetch_dd_munich_events


TZ = ZoneInfo("Europe/Berlin")


def format_dt(dt: datetime) -> str:
    # ICS‑Format: YYYYMMDDTHHMMSS
    return dt.astimezone(TZ).strftime("%Y%m%dT%H%M%S")


def generate_ics(events, filename="munich_boardgame_events.ics"):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Munich Boardgame Calendar//DE",
        "CALSCALE:GREGORIAN",
    ]

    for ev in events:
        uid = f"{ev['title']}-{format_dt(ev['start'])}@munich-boardgames"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{format_dt(datetime.now(TZ))}",
                f"DTSTART:{format_dt(ev['start'])}",
                f"DTEND:{format_dt(ev['end'])}",
                f"SUMMARY:{ev['title']}",
                f"LOCATION:{ev.get('location', '')}",
                f"URL:{ev.get('url', '')}",
                f"DESCRIPTION:{ev.get('description', '').replace('\n', ' ')}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")

    Path(filename).write_text("\n".join(lines), encoding="utf-8")
    print(f"Fertig! Datei erzeugt: {filename}")


def main():
    print("Script gestartet")
    print("Erzeuge Kalender...")

    all_events = []

    print("Hole Events von BB-Spiele...")
    try:
        all_events.extend(fetch_bb_spiele_events())
    except Exception as e:
        print(f"Fehler bei BB-Spiele: {e}")

    print("Hole Events von Funtainment...")
    try:
        all_events.extend(fetch_funtainment_events())
    except Exception as e:
        print(f"Fehler bei Funtainment: {e}")

    print("Hole Events von Deck & Dice / DD Munich...")
    try:
        all_events.extend(fetch_dd_munich_events())
    except Exception as e:
        print(f"Fehler bei DD Munich: {e}")

    print(f"Gesamtanzahl Events: {len(all_events)}")
    generate_ics(all_events)


if __name__ == "__main__":
    main()
