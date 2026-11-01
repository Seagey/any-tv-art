"""How bright and how warm the picture should be right now, and whether it is night.

A print on the wall is only as bright as the room. So the picture follows the sun: full by day
(scaled down on dull days by measured sunlight), dimmer and warmer through dusk, then the night
cut-off. Sun times and sunlight come from Open-Meteo (free, no key), cached for the day. With no
internet it falls back to 6:00 and 18:30.

dim and warm are what the template's setLight() takes. On a Samsung in Art Mode the same curve
sets the TV's own art brightness, which (unlike dimming a picture on an LCD) does save power.
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta

from . import config as configmod

TWILIGHT = timedelta(minutes=50)   # how long the ramp at sunrise and sunset takes
FALLBACK = ("06:00", "18:30")


def _fetch(cfg, day):
    from .info import find_place
    lat, lon, _ = find_place(cfg)
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&daily=sunrise,sunset"
           "&hourly=shortwave_radiation&timezone=auto&start_date=%s&end_date=%s"
           % (lat, lon, day.isoformat(), day.isoformat()))
    with urllib.request.urlopen(url, timeout=15) as r:
        d = json.load(r)
    return {"date": day.isoformat(), "sunrise": d["daily"]["sunrise"][0][-5:], "sunset": d["daily"]["sunset"][0][-5:],
            "radiation": d["hourly"]["shortwave_radiation"]}


def sun(cfg, day, fetch=_fetch):
    """{"sunrise": "HH:MM", "sunset": "HH:MM", "radiation": [24 hourly W/m2] or None} for that day."""
    path = cfg.file("sun.json")
    try:
        with open(path, encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("date") == day.isoformat():
            return cached
    except (OSError, ValueError):
        pass
    try:
        got = fetch(cfg, day)
    except Exception:
        got = None
    if not got:
        return {"date": day.isoformat(), "sunrise": FALLBACK[0], "sunset": FALLBACK[1], "radiation": None}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(got, f)
    return got


def is_night(cfg, now):
    """Inside the night cut-off (art.night_off to art.morning_on, across midnight)."""
    off = configmod.hhmm(cfg["art"]["night_off"], "art.night_off")
    on = configmod.hhmm(cfg["art"]["morning_on"], "art.morning_on")
    m = now.hour * 60 + now.minute
    return (m >= off or m < on) if off > on else (off <= m < on)


def daylight(now, s):
    """0 at night, 1 in full daylight, a smooth ramp through each twilight."""
    def at(hm):
        h, m = map(int, hm.split(":"))
        return now.replace(hour=h, minute=m, second=0, microsecond=0)
    rise, sets = at(s["sunrise"]), at(s["sunset"])
    if now <= rise - TWILIGHT / 2 or now >= sets + TWILIGHT / 2:
        return 0.0
    if now < rise + TWILIGHT / 2:
        return (now - (rise - TWILIGHT / 2)) / TWILIGHT
    if now > sets - TWILIGHT / 2:
        return ((sets + TWILIGHT / 2) - now) / TWILIGHT
    return 1.0


def level(cfg, tv, now, s=None):
    """{"dim", "warm", "art", "frame_brightness"} for this TV at this moment."""
    s = s or sun(cfg, now.date())
    d = daylight(now, s)
    rad = s.get("radiation")
    if d > 0 and rad and len(rad) > now.hour:
        # Overcast days are darker rooms. 600 W/m2 is a bright day; never below 0.35 of full.
        d *= max(0.35, min(1.0, rad[now.hour] / 600.0))
    cal = tv.get("calibration") or {}
    dim = (1 - d) * 0.55 + float(cal.get("dim_offset", 0))
    warm = (1 - d) * 0.6 + float(cal.get("warm_offset", 0))
    night = is_night(cfg, now)
    lo, hi = int(cal.get("frame_min", 1)), int(cal.get("frame_max", 8))
    return {"dim": round(min(0.9, max(0.0, dim)), 3), "warm": round(min(1.0, max(0.0, warm)), 3),
            "art": not night, "frame_brightness": lo if night else round(lo + (hi - lo) * d)}
