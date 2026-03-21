from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

LA_TZ = ZoneInfo("America/Los_Angeles")
LOCAL_TZ = ZoneInfo("Europe/Berlin")


# === 1. Dauer pro Eventtyp ===

def mtgo_duration_hours(name: str) -> int:
    n = name.lower()
    if "prelim" in n:
        return 4
    if "challenge" in n:
        return 5
    if "super qualifier" in n:
        return 7
    if "showcase qualifier" in n or "showcase open" in n:
        return 8
    if "qualifier" in n:
        return 6
    if "single elim" in n or "cube" in n:
        return 3
    return 4  # fallback


# === 2. Helpers aus dem JS nachgebaut ===

def is_mocs_format(s: str) -> bool:
    return (
        "standard" in s
        or ("modern" in s and "nbl" not in s and "premodern" not in s)
        or "legacy" in s
        or ("vintage" in s and "cube" not in s)
    )


def is_modern_event(s: str) -> bool:
    s_low = s.lower()
    return "modern" in s_low and "premodern" not in s_low and "nbl" not in s_low


def get_inferred_year(today: datetime, proposed_month: int) -> int:
    current_year = today.year
    current_month = today.month
    if proposed_month - current_month > 5:
        return current_year - 1
    elif current_month - proposed_month > 5:
        return current_year + 1
    return current_year


def supply_year_and_decrement_month(today: datetime, data):
    month = data[0]
    year = get_inferred_year(today, month)
    return [year, month - 1, *data[1:]]


# === 3. Hier musst du deine JS-Daten reinkopieren ===
# getBaseSchedule, getRCQData, getShowcaseData, getHackishLCQCorrections,
# getCubeEvents, getVegasQualifiers – 1:1 aus scheduleData.js,
# nur in Python-Listen/Dicts übersetzt.
#
# Um die Antwort hier schlank zu halten, schreibe ich nur die Schnittstelle:

def get_base_schedule():
    # return Liste mit 7*24 Strings/None – aus getBaseSchedule()
    raise NotImplementedError


def get_rcq_data(today: datetime):
    # aus getRCQData() + supplyYearAndDecrementMonth()
    raise NotImplementedError


def get_showcase_data(today: datetime):
    raise NotImplementedError


def get_hackish_lcq_corrections(today: datetime):
    raise NotImplementedError


def get_cube_events(today: datetime):
    raise NotImplementedError


def get_vegas_qualifiers(today: datetime):
    raise NotImplementedError


# === 4. Monster-Schedule wie im JS ===

def get_monster_schedule(today: datetime):
    base = get_base_schedule()
    monster_monster = base + base + base  # 3 Wochen
    day = today.weekday()  # Montag=0 ... Sonntag=6
    # JS: getDay() mit Sonntag=0 → wir passen nur den Offset an:
    # wir wollen: Start = 7 + day - 1
    start_idx = 24 * (7 + day - 1)
    end_idx = 24 * (7 + day + 8) + 1
    monster = monster_monster[start_idx:end_idx]
    insert_rcqs_showcases_and_lcqs(monster, today)
    return monster


def insert_rcqs_showcases_and_lcqs(monster, today: datetime):
    insert_into_monster(monster, today, get_showcases_and_lcqs(today), True)
    insert_into_monster(monster, today, get_rcqs(today), False)


def insert_into_monster(monster, today: datetime, special_events, is_replacement: bool):
    day = today - timedelta(days=1)
    for i in range(9):
        key = day.date().isoformat()
        today_events = special_events.get(key)
        if today_events:
            for hour, event in today_events.items():
                idx = 24 * i + hour
                if not is_replacement or (event is not None and "Pauper Showcase" in event):
                    if monster[idx]:
                        monster[idx] = insert_event(monster[idx], event, False)
                    else:
                        monster[idx] = event
                else:
                    if monster[idx]:
                        monster[idx] = insert_event(monster[idx], event or "", True)
                    else:
                        monster[idx] = event
        day += timedelta(days=1)


def insert_event(normal: str, special: str, is_replacement: bool) -> str:
    delim = "plus&"
    if delim not in normal and delim not in special:
        return special if is_replacement else normal + "&" + special
    if (delim in normal) != (delim in special):
        return special + "&" + normal if delim in normal else normal + "&" + special
    if is_replacement:
        return normal.split(delim)[0] + "&" + special
    return normal.split("&minus")[0] + "&" + special.split(delim)[1]


def get_rcqs(today: datetime):
    # Map: date_iso -> {hour: event_string}
    # aus getRCQData(), addCurrentYearDSTDates, addCubeEvents, addVegasQualifiers
    raise NotImplementedError


def get_showcases_and_lcqs(today: datetime):
    # Map: date_iso -> {hour: event_string}
    raise NotImplementedError


# === 5. Zeitberechnung & Event-Generierung für N Tage ===

def generate_mtgo_events(days: int = 30):
    today_local = datetime.now(LOCAL_TZ)
    # Start wie im JS: ein Tag vorher, 00:00 LA
    start_date_local = today_local - timedelta(days=1)
    start_date_la = datetime(
        start_date_local.year, start_date_local.month, start_date_local.day,
        0, 0, tzinfo=LA_TZ
    )

    monster = get_monster_schedule(today_local)
    events = []

    timestamp = start_date_la

    for k, slot in enumerate(monster):
        if k != 0:
            timestamp += timedelta(hours=1)

        if not slot:
            continue

        parts = slot.split("&")
        ts = timestamp

        for part in parts:
            if part == "DST":
                # grob wie im JS: vor/nach Sommerzeit
                if today_local.month < 6:
                    ts -= timedelta(hours=1)
                else:
                    ts += timedelta(hours=1)
                continue
            if part == "minus":
                ts -= timedelta(minutes=30)
                continue
            if part == "plus":
                ts += timedelta(minutes=30)
                continue

            name = part.strip()
            if not is_modern_event(name):
                continue

            start_local = ts.astimezone(LOCAL_TZ)
            if start_local.date() > (today_local.date() + timedelta(days=days)):
                continue

            dur_h = mtgo_duration_hours(name)
            end_local = start_local + timedelta(hours=dur_h)

            events.append({
                "title": f"MTGO: {name}",
                "start": start_local,
                "end": end_local,
                "location": "MTGO",
                "source": "mtgo",
            })

    return events
