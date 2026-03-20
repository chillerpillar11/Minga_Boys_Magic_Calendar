from datetime import datetime
from zoneinfo import ZoneInfo

from bb_spiele import fetch_bb_spiele_events
from funtainment import fetch_funtainment_events

TZ = ZoneInfo("Europe/Berlin")


def is_modern_or_rcq(title: str) -> bool:
    """Lässt nur Modern-Events oder RCQs durch."""
    title = title.lower()

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
    ]

    if any(x in title for x in exclude):
        return False

    return any(x in title for x in include)


def write_ics(events, filename="magic.ics"):
    """Schreibt eine ICS-Datei ohne externe Module."""
    def fmt(dt):
        return dt.strftime("%Y%m%dT%H%M%S")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Magic Calendar//DE",
        "CALSCALE:GREGORIAN",
    ]

    for ev in events:
        lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{ev['title']}",
            f"DTSTART;TZID=Europe/Berlin:{fmt(ev['start'])}",
            f"DTEND;TZID=Europe/Berlin:{fmt(ev['end'])}",
            f"LOCATION:{ev['location']}",
            f"URL:{ev['url']}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    print("Script gestartet")
    print("Erzeuge Kalender...")

    all_events = []

    # BB-Spiele
    bb_events = fetch_bb_spiele_events()
    bb_filtered = [ev for ev in bb_events if is_modern_or_rcq(ev["title"])]
    print(f"BB-Spiele Modern/RCQ: {len(bb_filtered)}")
    all_events.extend(bb_filtered)

    # Funtainment
    ft_events = fetch_funtainment_events()
    ft_filtered = [ev for ev in ft_events if is_modern_or_rcq(ev["title"])]
    print(f"Funtainment Modern/RCQ: {len(ft_filtered)}")
    all_events.extend(ft_filtered)

    print(f"Gesamtanzahl Events: {len(all_events)}")

    # Sortieren nach Datum
    all_events.sort(key=lambda e: e["start"])

    # ICS erzeugen
    write_ics(all_events)
    print("ICS erzeugt: magic.ics")


if __name__ == "__main__":
    main()
