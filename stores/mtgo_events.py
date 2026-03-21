import re
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

LA_TZ = ZoneInfo("America/Los_Angeles")
LOCAL_TZ = ZoneInfo("Europe/Berlin")

SCHEDULE_DATA_URL = "https://www.mtgoupdate.com/scheduleData.js"
SCHEDULE_JS_URL = "https://www.mtgoupdate.com/schedule.js"


# ------------------------------------------------------------
# 1. Dauer pro Eventtyp
# ------------------------------------------------------------

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
    return 4


# ------------------------------------------------------------
# 2. Helpers
# ------------------------------------------------------------

def is_modern_event(s: str) -> bool:
    s = s.lower()
    return "modern" in s and "premodern" not in s and "nbl" not in s


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


# ------------------------------------------------------------
# 3. scheduleData.js automatisch laden & parsen
# ------------------------------------------------------------

_cached_schedule_data = None

def load_schedule_js():
    global _cached_schedule_data
    if _cached_schedule_data:
        return _cached_schedule_data

    js = requests.get(SCHEDULE_DATA_URL, timeout=10).text

    def extract_array(name):
        pattern = rf"const {name}\s*=\s*

\[(.*?)\]

;"
        m = re.search(pattern, js, re.S)
        if not m:
            return []
        raw = "[" + m.group(1) + "]"
        raw = raw.replace("null", "None")
        raw = raw.replace("`", "'")
        raw = raw.replace("plus&", "plus&")
        return eval(raw)

    sun  = extract_array("sun")
    mon  = extract_array("mon")
    tues = extract_array("tues")
    wed  = extract_array("wed")
    thur = extract_array("thur")
    fri  = extract_array("fri")
    sat  = extract_array("sat")

    # RCQs, Showcases, LCQs, Cube, Vegas
    def extract_function_array(func_name):
        pattern = rf"function {func_name}\s*\(\)\s*\{{\s*return\s*

\[(.*?)\]

;"
        m = re.search(pattern, js, re.S)
        if not m:
            return []
        raw = "[" + m.group(1) + "]"
        raw = raw.replace("null", "None")
        raw = raw.replace("`", "'")
        return eval(raw)

    rcq_raw = extract_function_array("getRCQData")
    showcase_raw = extract_function_array("getShowcaseData")
    hackish_raw = extract_function_array("getHackishLCQCorrections")
    cube_raw = extract_function_array("getCubeEvents")
    vegas_raw = extract_function_array("getVegasQualifiers")

    _cached_schedule_data = {
        "base": sun + mon + tues + wed + thur + fri + sat,
        "rcq": rcq_raw,
        "showcase": showcase_raw,
        "hackish": hackish_raw,
        "cube": cube_raw,
        "vegas": vegas_raw,
    }
    return _cached_schedule_data


# ------------------------------------------------------------
# 4. Base Schedule
# ------------------------------------------------------------

def get_base_schedule():
    data = load_schedule_js()
    return data["base"]


# ------------------------------------------------------------
# 5. RCQs, Showcases, LCQs, Cube, Vegas
# ------------------------------------------------------------

def get_rcq_data(today: datetime):
    data = load_schedule_js()["rcq"]
    out = []
    for entry in data:
        y, m, d, events = supply_year_and_decrement_month(today, entry)
        out.append((y, m, d, events))
    return out


def get_showcase_data(today: datetime):
    data = load_schedule_js()["showcase"]
    out = []
    for entry in data:
        y, m, d, events = supply_year_and_decrement_month(today, entry)
        out.append((y, m, d, events))
    return out


def get_hackish_lcq_corrections(today: datetime):
    data = load_schedule_js()["hackish"]
    out = []
    for entry in data:
        y, m, d, hour, ev = supply_year_and_decrement_month(today, entry)
        out.append((y, m, d, hour, ev))
    return out


def get_cube_events(today: datetime):
    data = load_schedule_js()["cube"]
    out = []
    for dates, times in data:
        new_dates = [supply_year_and_decrement_month(today, d) for d in dates]
        out.append((new_dates, times))
    return out


def get_vegas_qualifiers(today: datetime):
    data = load_schedule_js()["vegas"]
    out = []
    for dates, times in data:
        new_dates = [supply_year_and_decrement_month(today, d) for d in dates]
        out.append((new_dates, times))
    return out


# ------------------------------------------------------------
# 6. Monster Schedule (aus schedule.js)
# ------------------------------------------------------------

def get_monster_schedule(today: datetime):
    base = get_base_schedule()
    monster_monster = base + base + base
    day = today.weekday()
    start_idx = 24 * (7 + day - 1)
    end_idx = 24 * (7 + day + 8) + 1
    monster = monster_monster[start_idx:end_idx]
    insert_rcqs_showcases_and_lcqs(monster, today)
    return monster


def insert_rcqs_showcases_and_lcqs(monster, today):
    insert_into_monster(monster, today, get_showcases_and_lcqs(today), True)
    insert_into_monster(monster, today, get_rcqs(today), False)


def insert_into_monster(monster, today, special_events, is_replacement):
    day = today - timedelta(days=1)
    for i in range(9):
        key = day.date().isoformat()
        events = special_events.get(key)
        if events:
            for hour, ev in events.items():
                idx = 24 * i + hour
                if not is_replacement or (ev and "Pauper Showcase" in ev):
                    monster[idx] = ev if not monster[idx] else insert_event(monster[idx], ev, False)
                else:
                    monster[idx] = ev if not monster[idx] else insert_event(monster[idx], ev or "", True)
        day += timedelta(days=1)


def insert_event(normal, special, is_replacement):
    delim = "plus&"
    if delim not in normal and delim not in special:
        return special if is_replacement else normal + "&" + special
    if (delim in normal) != (delim in special):
        return special + "&" + normal if delim in normal else normal + "&" + special
    if is_replacement:
        return normal.split(delim)[0] + "&" + special
    return normal.split("&minus")[0] + "&" + special.split(delim)[1]


# ------------------------------------------------------------
# 7. RCQs + Showcases + LCQs zusammenbauen
# ------------------------------------------------------------

def get_rcqs(today):
    out = {}

    # RCQs
    for y, m, d, events in get_rcq_data(today):
        key = datetime(y, m, d).date().isoformat()
        out[key] = events

    # Showcases
    for y, m, d, events in get_showcase_data(today):
        key = datetime(y, m, d).date().isoformat()
        out.setdefault(key, {}).update(events)

    # Hackish LCQ corrections
    for y, m, d, hour, ev in get_hackish_lcq_corrections(today):
        key = datetime(y, m, d).date().isoformat()
        out.setdefault(key, {})[hour] = ev + " LCQ"

    # Cube
    for dates, times in get_cube_events(today):
        for y, m, d in dates:
            key = datetime(y, m, d).date().isoformat()
            for t in times:
                hour = int(t)
                out.setdefault(key, {})[hour] = "Cube 64-player Single Elim"

    # Vegas
    for dates, times in get_vegas_qualifiers(today):
        for y, m, d in dates:
            key = datetime(y, m, d).date().isoformat()
            for t in times:
                hour = int(t)
                out.setdefault(key, {})[hour] = "Vegas Qualifier"

    return out


def get_showcases_and_lcqs(today):
    # Showcases replace Challenges
    out = {}
    for y, m, d, events in get_showcase_data(today):
        key = datetime(y, m, d).date().isoformat()
        out[key] = events
    return out


# ------------------------------------------------------------
# 8. Events generieren
# ------------------------------------------------------------

def generate_mtgo_events(days=30):
    today_local = datetime.now(LOCAL_TZ)
    start_date_local = today_local - timedelta(days=1)
    start_date_la = datetime(start_date_local.year, start_date_local.month, start_date_local.day, 0, 0, tzinfo=LA_TZ)

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
            if start_local.date() > today_local.date() + timedelta(days=days):
                continue

            dur = mtgo_duration_hours(name)
            end_local = start_local + timedelta(hours=dur)

            events.append({
                "title": f"MTGO: {name}",
                "start": start_local,
                "end": end_local,
                "location": "MTGO",
                "url": "https://www.mtgoupdate.com/",
                "description": "",
            })

    return events


def fetch_mtgo_events():
    return generate_mtgo_events(30)
