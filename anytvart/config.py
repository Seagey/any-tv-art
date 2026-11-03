"""Reading config.json, with defaults for everything that is left out.

The settings file lives next to the tool (config.json, git ignores it). Everything the tool saves
for itself (TV tokens, the settings it changed and their old values, the last picture) goes in a
"data" folder next to that file, also ignored by git.
"""
import copy
import json
import math
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

STYLES = ("mat", "full")
BLOCKS = ("date", "weather", "calendar", "reminders", "quote")
DAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
KINDS = ("android", "samsung-art")
ART_HOURS = ("idle", "home", "day")
LIGHTS = ("top-left", "top-right", "top")

LOOK = {
    "style": "mat",
    "mat": {"colour": "#ece6da", "width": 0.085, "bevel": True, "light": "top-left", "shadow": 0.5},
    "grain": {"on": True, "strength": 0.5},
    "flatten": {"strength": 0.6},
    "label": {"on": True, "side": "left"},
}

DEFAULTS = {
    "timezone": "",
    "photos": {"folder": "photos", "pick": "day", "file": "", "focus": "centre"},
    "look": LOOK,
    "date_order": "day-month",
    "clock": "12h",
    "blocks": [{"type": "date"}, {"type": "weather"}, {"type": "calendar"}, {"type": "reminders"}],
    "place": {"name": "", "latitude": None, "longitude": None},
    "weather": {"units": "celsius", "show_place": False, "rain_chance": False},
    "calendar": {"ics_urls": [], "days": 2, "max": 3, "hide": [], "empty_text": "Nothing planned today"},
    "reminders": [],
    "quote": {"text": "", "lines": []},
    "art": {"night_off": "22:00", "morning_on": "07:00", "picture_hour": 5},
    "price_kwh": 0.40,
    "bridge": {"port": 5430, "url": ""},
    "adb": "",
    "chrome": "",
    "tvs": [],
}

TV_DEFAULTS = {
    "name": "", "kind": "android", "ip": "", "port": 0, "size_inch": 55, "app_px": [1920, 1080],
    "panel": "lcd", "watts_art": None, "art_hours": "idle", "look": {}, "safe": {},
    "calibration": {}, "wake_back": False, "mac": "", "home_devices": [], "night_sleep": True,
}


class ConfigError(Exception):
    pass


def _merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def hhmm(text, what):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(text or ""))
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise ConfigError('%s must be a time like "22:00", not "%s"' % (what, text))
    return int(m.group(1)) * 60 + int(m.group(2))


def screen_for(tv, render_size=None):
    """Millimetres per pixel on the real screen: per 1920 wide stage pixel (for the bevel and the
    shadow) and per real pixel of what the TV draws (for the paper grain). 16:9 assumed."""
    width_mm = float(tv["size_inch"]) * 25.4 * 16 / math.hypot(16, 9)
    drawn = render_size or tv["app_px"][0]
    return {"mm_per_px": round(width_mm / 1920, 4), "device_mm_per_px": round(width_mm / drawn, 4),
            "oled": tv["panel"] == "oled"}


class Config:
    def __init__(self, data, path=None):
        self.path = os.path.abspath(path) if path else None
        self.root = os.path.dirname(self.path) if self.path else os.getcwd()
        self.data = _merge(DEFAULTS, data)
        self.data["tvs"] = [self._tv(t) for t in self.data["tvs"]]
        self.validate()

    def _tv(self, t):
        tv = _merge(TV_DEFAULTS, t)
        tv["look"] = _merge(self.data["look"], tv["look"])
        if not tv["port"]:
            tv["port"] = 5555 if tv["kind"] == "android" else 8002
        return tv

    # ---- where things live ----
    @property
    def data_dir(self):
        d = os.path.join(self.root, "data")
        os.makedirs(d, exist_ok=True)
        return d

    def file(self, name):
        return os.path.join(self.data_dir, name)

    @property
    def photo_folder(self):
        f = os.path.expanduser(self.data["photos"]["folder"])
        return f if os.path.isabs(f) else os.path.join(self.root, f)

    # ---- handy values ----
    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    @property
    def tz(self):
        name = self.data.get("timezone") or ""
        if name:
            return ZoneInfo(name)
        return datetime.now().astimezone().tzinfo

    def now(self):
        return datetime.now(self.tz)

    def block(self, kind):
        for b in self.data["blocks"]:
            if b.get("type") == kind and b.get("on", True):
                return b
        return None

    def tv(self, name=None):
        tvs = self.data["tvs"]
        if not tvs:
            raise ConfigError('no TVs in config.json yet (add one under "tvs")')
        if name is None:
            if len(tvs) > 1:
                raise ConfigError("more than one TV: say which with --tv (%s)" % ", ".join(t["name"] for t in tvs))
            return tvs[0]
        for t in tvs:
            if t["name"].lower() == name.lower():
                return t
        raise ConfigError('no TV called "%s" (TVs: %s)' % (name, ", ".join(t["name"] for t in tvs)))

    def validate(self):
        d = self.data
        self._look(d["look"], "look")
        if d["photos"]["pick"] not in ("day", "rotate", "random", "fixed"):
            raise ConfigError('photos.pick must be "day", "rotate", "random" or "fixed"')
        if d["photos"]["pick"] == "fixed" and not d["photos"].get("file"):
            raise ConfigError('photos.pick is "fixed", so photos.file must name the picture')
        if d["clock"] not in ("12h", "24h"):
            raise ConfigError('clock must be "12h" or "24h"')
        if d["date_order"] not in ("day-month", "month-day"):
            raise ConfigError('date_order must be "day-month" or "month-day"')
        if d["weather"]["units"] not in ("celsius", "fahrenheit"):
            raise ConfigError('weather.units must be "celsius" or "fahrenheit"')
        for b in d["blocks"]:
            if b.get("type") not in BLOCKS:
                raise ConfigError('unknown block "%s" (blocks are %s)' % (b.get("type"), ", ".join(BLOCKS)))
        for r in d["reminders"]:
            if not r.get("text"):
                raise ConfigError("every reminder needs a text")
            for day in r.get("days", []):
                if day.lower()[:3] not in DAY_NAMES:
                    raise ConfigError('reminder day "%s" is not a day (use mon, tue, wed ...)' % day)
        hhmm(d["art"]["night_off"], "art.night_off")
        hhmm(d["art"]["morning_on"], "art.morning_on")
        if not 0 <= int(d["art"]["picture_hour"]) <= 23:
            raise ConfigError("art.picture_hour must be 0 to 23")
        if not 0 < float(d["price_kwh"]) < 5:
            raise ConfigError("price_kwh is the price of one kWh in dollars, for example 0.40")
        names = set()
        for t in d["tvs"]:
            if not t["name"]:
                raise ConfigError("every TV needs a name")
            if t["name"].lower() in names:
                raise ConfigError('two TVs are called "%s"' % t["name"])
            names.add(t["name"].lower())
            if t["kind"] not in KINDS:
                raise ConfigError('TV "%s": kind must be one of %s' % (t["name"], ", ".join(KINDS)))
            ah = t["art_hours"]
            if ah not in ART_HOURS:
                m = re.fullmatch(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", str(ah))
                if not m:
                    raise ConfigError('TV "%s": art_hours must be "idle", "home", "day" or a range like "16:00-21:00"' % t["name"])
                hhmm(m.group(1), "art_hours"), hhmm(m.group(2), "art_hours")
            if t["panel"] not in ("lcd", "oled"):
                raise ConfigError('TV "%s": panel must be "lcd" or "oled"' % t["name"])
            if not 10 <= float(t["size_inch"]) <= 150:
                raise ConfigError('TV "%s": size_inch looks wrong (%s)' % (t["name"], t["size_inch"]))
            self._look(t["look"], 'TV "%s" look' % t["name"])
        if self.data.get("timezone"):
            try:
                ZoneInfo(self.data["timezone"])
            except Exception:
                raise ConfigError('timezone "%s" is not known (example: "Australia/Melbourne")' % self.data["timezone"])

    @staticmethod
    def _look(look, where):
        if look["style"] not in STYLES:
            raise ConfigError('%s.style must be one of %s' % (where, ", ".join(STYLES)))
        if look["mat"].get("light", "top-left") not in LIGHTS:
            raise ConfigError('%s.mat.light must be one of %s' % (where, ", ".join(LIGHTS)))
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(look["mat"].get("colour", ""))):
            raise ConfigError('%s.mat.colour must be a colour like "#ece6da"' % where)
        if look["mat"]["colour"].lower() in ("#ffffff", "#fefefe"):
            raise ConfigError("%s.mat.colour: pure white glows on a screen and never reads as paper; try #f1ece3" % where)
        if look["mat"].get("core", "white") not in ("white", "black"):
            raise ConfigError('%s.mat.core must be "white" or "black"' % where)
        if not 0.03 <= float(look["mat"].get("width", 0.085)) <= 0.2:
            raise ConfigError("%s.mat.width is a share of the screen height, 0.03 to 0.2" % where)
        if look["label"].get("side", "left") not in ("left", "right"):
            raise ConfigError('%s.label.side must be "left" or "right"' % where)
        for k in ("grain", "flatten"):
            v = look[k].get("strength", 0.5)
            if not 0 <= float(v) <= 1:
                raise ConfigError("%s.%s.strength must be 0 to 1" % (where, k))


def load(path=None, required=True):
    """Load config.json (or the file given). With required=False a missing file gives defaults."""
    path = path or os.environ.get("ANYTVART_CONFIG") or "config.json"
    if not os.path.exists(path):
        if required:
            raise ConfigError("no settings file at %s (copy config.example.json to config.json first)" % path)
        return Config({}, path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError("%s is not valid JSON: line %s, %s" % (path, e.lineno, e.msg))
    data.pop("_comment", None)
    return Config(data, path)
