"""What the bridge should do to an Android TV right now. Pure decisions, no TV calls, so every case
is tested without a TV (tests/test_schedule.py).

Inputs: the time, the TV's settings, what the TV is doing (awake, showing our art, playing
something) and what the bridge did earlier today. Output: the actions to take, in order, plus
what to remember.

The rules (BUILD.md, "The daily cycle"):
- Night (art.night_off to art.morning_on): if the TV is awake and showing our art, sleep it. Never
  while something is playing. Try again every 10 minutes, so a missed press is caught.
- art_hours "idle": nothing else. The TV's own screensaver starts the art after its idle time and
  the TV's own inactivity timer ends it. Lowest power, and the default.
- "day", "home" or a range like "16:00-21:00": once, at the start of the window, wake the TV and
  open the art ("home" only while someone is home). At the end of the window, sleep it if it is
  still on our art.
"""
from . import config as configmod
from .light import is_night

RETRY_MINUTES = 10


def window(cfg, tv):
    """(start, end) in minutes after midnight, or None when the TV only shows art when idle."""
    ah = tv["art_hours"]
    if ah == "idle":
        return None
    if ah in ("day", "home"):
        return (configmod.hhmm(cfg["art"]["morning_on"], "art.morning_on"),
                configmod.hhmm(cfg["art"]["night_off"], "art.night_off"))
    a, b = ah.split("-")
    return configmod.hhmm(a, "art_hours"), configmod.hhmm(b, "art_hours")


def _inside(m, w):
    a, b = w
    return a <= m < b if a <= b else (m >= a or m < b)


def decide(cfg, tv, now, seen, memory, home=True):
    """seen: {"reachable", "awake", "ours" (our art on screen), "playing"}.
    memory: {"woke": "YYYY-MM-DD", "slept_at": epoch seconds of the last sleep try}.
    Returns (actions, memory). Actions: "wake", "open_art", "sleep"."""
    memory = dict(memory or {})
    acts = []
    today = now.date().isoformat()
    m = now.hour * 60 + now.minute
    stamp = now.timestamp()
    if not seen.get("reachable"):
        return acts, memory
    def may_sleep():
        return stamp - float(memory.get("slept_at", 0)) >= RETRY_MINUTES * 60

    if is_night(cfg, now):
        if seen.get("awake") and seen.get("ours") and not seen.get("playing") and may_sleep():
            acts.append("sleep")
            memory["slept_at"] = stamp
        return acts, memory

    w = window(cfg, tv)
    if w is None:
        return acts, memory
    want = _inside(m, w) and (home or tv["art_hours"] != "home")
    if want and memory.get("woke") != today:
        if not seen.get("awake"):
            acts.append("wake")
        if not seen.get("playing"):
            acts.append("open_art")
        memory["woke"] = today
    elif not want and seen.get("awake") and seen.get("ours") and not seen.get("playing") and may_sleep():
        acts.append("sleep")
        memory["slept_at"] = stamp
    return acts, memory
