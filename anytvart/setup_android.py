"""Putting the art on a Google TV or Android TV, and taking it off again.

apply() does, in order, and only after the owner has said yes (AGENTS.md):
  1. installs our app (dist/any-tv-art.apk, or the Releases download),
  2. gives it its settings file (bridge address or "alone"), and in "alone" mode copies the photos
     onto the TV, after checking there is room,
  3. sets the TV's screensaver to our art and the idle time before it starts,
  4. sets the TV's inactivity auto-off: the longest it offers with a bridge (the bridge does the
     real night cut-off; this is the backstop if the bridge stops), or 2 hours without one.
Every setting is read and recorded first (drivers/android.py), so undo() puts it all back.
"""
import json
import os
import tempfile

from . import photos
from .config import screen_for
from .drivers.android import ACTIVITY, Android, DREAM

IDLE_TO_ART_MS = 10 * 60 * 1000              # 10 minutes: long enough for a paused show
BACKSTOP_MS = {"bridge": 4 * 3600 * 1000,     # G: 4 hours is the longest we have seen offered
               "alone": 2 * 3600 * 1000}
PHOTO_LIMIT = 60                               # photos copied in "alone" mode
SPARE_MB = 500                                 # always leave the TV at least this much room


def app_config(cfg, tv, mode):
    """The settings file the art app reads (tv/android/README.md lists every key)."""
    from .info import find_place
    q = cfg["quote"]
    try:
        lat, lon, name = find_place(cfg)
        place = {"name": name, "latitude": lat, "longitude": lon}
    except Exception:
        place = cfg["place"]           # no weather or sun curve on the TV until a place is set
    slug = "".join(c if c.isalnum() else "-" for c in tv["name"].lower())
    base = (cfg["bridge"].get("url") or "").rstrip("/")
    return {"mode": mode, "bridge_url": "%s/tv/%s" % (base, slug) if mode == "bridge" else "",
            "tv": tv["name"], "place": place, "timezone": cfg.get("timezone") or "",
            "look": tv["look"], "screen": screen_for(tv), "safe": tv.get("safe", {}),
            "quote_lines": ([q["text"]] if q.get("text") else []) + list(q.get("lines") or []),
            "date_order": cfg["date_order"], "units": cfg["weather"]["units"], "oled": tv["panel"] == "oled"}


def plan(cfg, tv, mode):
    """What apply() would change, in plain words, for the owner to read before saying yes."""
    out = ["Install the art app (app.anytvart) on %s." % tv["name"],
           "Give it its settings: %s." % ("pictures from the bridge at %s" % cfg["bridge"].get("url") if mode == "bridge"
                                          else "it makes its own picture, no computer needed"),
           "Set the screensaver to the art, starting after %d minutes with no remote presses." % (IDLE_TO_ART_MS // 60000),
           "Set the TV's own switch-off to %d hours with no remote presses (%s)." % (
               BACKSTOP_MS[mode] // 3600000,
               "a backstop: the bridge switches it off at night" if mode == "bridge" else "this is what ends the art each day")]
    if mode == "alone":
        out.insert(2, "Copy up to %d photos onto the TV (in the app's own folder; removed with the app)." % PHOTO_LIMIT)
    out.append("Every old value is written down first. `anytvart undo --tv \"%s\"` puts them all back." % tv["name"])
    return out


def apply(cfg, tv, mode, apk, say=print, android=None):
    if mode not in ("bridge", "alone"):
        raise ValueError('mode is "bridge" or "alone"')
    if mode == "bridge" and not cfg["bridge"].get("url"):
        raise ValueError('set bridge.url in config.json first, for example "http://192.0.2.5:5430"')
    a = android or Android(cfg, tv)
    a.connect()
    if not os.path.exists(apk):
        raise FileNotFoundError("no app at %s: run sh scripts/build-apk.sh, or download it from Releases" % apk)
    a.install(apk)
    say("installed the art app")
    with tempfile.TemporaryDirectory(prefix="anytvart-") as tmp:
        cfg_path = os.path.join(tmp, "config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(app_config(cfg, tv, mode), f)
        a.push_config(cfg_path)
        say("gave it its settings (%s)" % mode)
        if mode == "alone":
            free = a.identify().get("free_mb")
            names = photos.list_photos(cfg.photo_folder)[:PHOTO_LIMIT]
            need = len(names) * 2              # about 2 MB each at 1080p
            if free is not None and free - need < SPARE_MB:
                raise RuntimeError("the TV has %d MB free; copying %d photos needs about %d MB and we leave %d MB spare"
                                   % (free, len(names), need, SPARE_MB))
            for i, n in enumerate(names):
                out = os.path.join(tmp, "%03d.jpg" % i)
                im = photos.prepare(os.path.join(cfg.photo_folder, n), out, cfg["photos"].get("focus", "centre"))
                w, h = tv["app_px"]
                im.resize((w, h)).save(out, "JPEG", quality=90)   # pixels only: no GPS, no camera details
                a.push_photo(out, "%03d.jpg" % i)
            say("copied %d photos" % len(names))
    a.put("secure", "screensaver_components", DREAM)
    a.put("secure", "screensaver_enabled", "1")
    a.put("system", "screen_off_timeout", str(IDLE_TO_ART_MS))
    a.put("secure", "attentive_timeout", str(BACKSTOP_MS[mode]))
    say("screensaver set to the art after %d minutes; switch-off after %d hours" % (IDLE_TO_ART_MS // 60000, BACKSTOP_MS[mode] // 3600000))
    return True


def show(cfg, tv, android=None):
    """Open the art now, to look at it (any remote button closes it)."""
    a = android or Android(cfg, tv)
    a.connect()
    return a.shell("am start -n " + ACTIVITY)


def undo(cfg, tv, remove_app=True, android=None):
    a = android or Android(cfg, tv)
    a.connect()
    done = a.undo()
    if remove_app and a.installed():
        a.uninstall()
        done.append("removed the art app and its photos")
    return done
