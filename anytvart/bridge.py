"""The bridge: the part that runs on an always-on computer at home.

- Serves each Android TV's art app its picture data (/art.json), the room light (/light.json)
  and today's photo (/photo/...). Port 5430 by default, home network only.
- Once a minute, for each TV: Android TVs get the daily cycle from schedule.py (morning wake,
  night sleep); Samsung TVs in Art Mode get the day's picture from art.picture_hour and art
  brightness on the light curve, at most every 15 minutes.

Without the bridge the Android app shows its own picture and the TV's own timers do the rest
(docs/GOOGLE-TV.md, "Without a computer").
"""
import json
import os
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from PIL import Image

from . import frame_daily, info, light, photos, schedule
from .config import screen_for
from .state import State

INFO_MINUTES = 30
FRAME_LIGHT_MINUTES = 15


def say(msg):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def wake_on_lan(mac, broadcast="255.255.255.255"):
    """The magic packet: six 0xFF bytes, then the TV's network card address sixteen times."""
    import socket
    raw = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    if len(raw) != 6:
        raise ValueError("mac must be six pairs of hex digits, separated by colons")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(b"\xff" * 6 + raw * 16, (broadcast, 9))


def _slug(tv):
    return "".join(c if c.isalnum() else "-" for c in tv["name"].lower())


class Bridge:
    def __init__(self, cfg):
        self.cfg = cfg
        self._info = (0, None)
        self.memory_file = cfg.file("bridge-memory.json")
        try:
            with open(self.memory_file, encoding="utf-8") as f:
                self.memory = json.load(f)   # so a restart never wakes a TV twice in one day
        except (OSError, ValueError):
            self.memory = {}
        self.lock = threading.Lock()

    # ------------------------------------------------------------------ what the app is served

    def details(self):
        stamp, got = self._info
        if not got or time.time() - stamp > INFO_MINUTES * 60:
            got = info.gather(self.cfg)
            self._info = (time.time(), got)
        return got

    def photo_for(self, tv, now):
        """Today's photo, cropped and sized for what this TV draws, without any metadata."""
        day = now.date().isoformat()
        name = "%s-%s.jpg" % (_slug(tv), day)
        path = self.cfg.file(name)
        if not os.path.exists(path):
            state = State(self.cfg.file("state-%s.json" % _slug(tv)))
            chosen = photos.choose(self.cfg, state, now.date())
            im = photos.prepare(os.path.join(self.cfg.photo_folder, chosen), path, self.cfg["photos"].get("focus", "centre"))
            w, h = tv["app_px"]
            if im.width > w * 2:
                im.resize((w * 2, h * 2), Image.LANCZOS).save(path, "JPEG", quality=90)
            state.save()
            for old in os.listdir(self.cfg.data_dir):   # only this TV's older daily photos
                if old.startswith(_slug(tv) + "-") and old.endswith(".jpg") and old != name:
                    os.remove(os.path.join(self.cfg.data_dir, old))
        return name

    def art(self, tv):
        now = self.cfg.now()
        lv = light.level(self.cfg, tv, now)
        from .render import FOCUS_CSS
        drift = {"x": 0, "y": 0}
        look = tv["look"]
        if tv["panel"] == "oled":
            # OLED: the picture drifts a few pixels each hour and the label swaps sides each day,
            # so no edge or letter sits on the same pixels for long (built, untested: no OLED here).
            drift = {"x": (now.hour * 7) % 13 - 6, "y": (now.hour * 5) % 9 - 4}
            side = ("left", "right")[now.toordinal() % 2]
            look = dict(look, label=dict(look.get("label") or {}, side=side))
        return {"photo": "/photo/" + self.photo_for(tv, now),
                "focus": FOCUS_CSS.get(self.cfg["photos"].get("focus", "centre"), "50% 50%"),
                "info": self.details(), "look": look, "screen": screen_for(tv), "safe": tv.get("safe", {}),
                "drift": drift, "light": {"dim": lv["dim"], "warm": lv["warm"]},
                "card": os.path.exists(self.cfg.file("card-%s" % _slug(tv)))}

    def light(self, tv):
        lv = light.level(self.cfg, tv, self.cfg.now())
        return {"dim": lv["dim"], "warm": lv["warm"], "art": lv["art"]}

    # ------------------------------------------------------------------ the minute loop

    def tick(self, android_factory=None):
        now = self.cfg.now()
        for tv in self.cfg["tvs"]:
            try:
                if tv["kind"] == "android":
                    self._android(tv, now, android_factory)
                else:
                    self._samsung(tv, now)
            except Exception as e:     # one TV's trouble never stops the others
                say("%s: %s" % (tv["name"], e))
        tmp = self.memory_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.memory, f)
        os.replace(tmp, self.memory_file)

    def _android(self, tv, now, factory=None):
        if tv["art_hours"] == "idle" and not tv.get("night_sleep", True):
            return
        from .drivers.android import Android
        a = (factory or Android)(self.cfg, tv)
        try:
            a.connect()
        except Exception:
            # Asleep and off the network (or ADB not allowed). If art is due now and we know the
            # TV's network card address, send Wake-on-LAN, at most every 10 minutes. Built, not
            # yet tested on a TV of ours. Once it is back on the Wi-Fi the next minute opens the art.
            mem = self.memory.setdefault(tv["name"], {})
            w = schedule.window(self.cfg, tv)
            m = now.hour * 60 + now.minute
            if (tv.get("mac") and w and schedule._inside(m, w) and mem.get("woke") != now.date().isoformat()
                    and not light.is_night(self.cfg, now) and self._home(tv)
                    and time.time() - mem.get("wol_at", 0) >= 600):
                wake_on_lan(tv["mac"])
                mem["wol_at"] = time.time()
                say("%s: Wake-on-LAN sent" % tv["name"])
            return
        seen = a.state()
        home = self._home(tv)
        acts, mem = schedule.decide(self.cfg, tv, now, seen, self.memory.get(tv["name"]), home)
        self.memory[tv["name"]] = mem
        for act in acts:
            if act == "wake":
                a.wake()
                time.sleep(3)
            elif act == "open_art":
                a.open_art()
            elif act == "sleep":
                a.sleep()
            say("%s: %s" % (tv["name"], act))

    def _home(self, tv):
        """Someone is home if any of the listed phones answers. Only used for art_hours "home"."""
        devices = tv.get("home_devices") or []
        if tv["art_hours"] != "home" or not devices:
            return True
        for ip in devices:
            if subprocess.run(["ping", "-c", "1", "-W", "1000" if os.uname().sysname == "Darwin" else "1", ip],
                              capture_output=True).returncode == 0:
                return True
        return False

    def _samsung(self, tv, now):
        frame_daily.run(self.cfg, tv, now, log=say)
        mem = self.memory.setdefault(tv["name"], {})
        if time.time() - mem.get("light_at", 0) >= FRAME_LIGHT_MINUTES * 60:
            mem["light_at"] = time.time()
            got = frame_daily.set_brightness(self.cfg, tv, light.level(self.cfg, tv, now)["frame_brightness"])
            if got is not None and got != mem.get("brightness"):
                mem["brightness"] = got
                say("%s: art brightness %s" % (tv["name"], got))


def handler_for(bridge):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, data, code=200):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            path, tv_name = u.path, (q.get("tv") or [None])[0]
            # Each TV's app is given its own base address, /tv/<name>, so one bridge serves many TVs.
            parts = path.split("/")
            if len(parts) > 3 and parts[1] == "tv":
                slug = parts[2]
                tv_name = next((t["name"] for t in bridge.cfg["tvs"] if _slug(t) == slug), slug)
                path = "/" + "/".join(parts[3:])
            try:
                if path.startswith("/photo/"):
                    name = os.path.basename(path)
                    path = bridge.cfg.file(name)
                    if not name.endswith(".jpg") or not os.path.exists(path):
                        return self._json({"error": "no such photo"}, 404)
                    with open(path, "rb") as f:
                        body = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if path in ("/art.json", "/light.json"):
                    tv = bridge.cfg.tv(tv_name)
                    return self._json(bridge.art(tv) if path == "/art.json" else bridge.light(tv))
                if path == "/":
                    return self._json({"any-tv-art": "bridge", "tvs": [t["name"] for t in bridge.cfg["tvs"]]})
                self._json({"error": "not found"}, 404)
            except Exception as e:
                self._json({"error": str(e)}, 500)
    return H


def serve(cfg, port=None, loop=True):
    b = Bridge(cfg)
    port = int(cfg["bridge"]["port"]) if port is None else port
    srv = ThreadingHTTPServer(("0.0.0.0", port), handler_for(b))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    say("bridge on port %d for %s" % (srv.server_address[1], ", ".join(t["name"] for t in cfg["tvs"]) or "no TVs yet"))
    if not loop:
        return srv, b
    while True:
        b.tick()
        time.sleep(60 - datetime.now().second)
