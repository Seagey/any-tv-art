"""Google TV and Android TV over ADB (the TV's developer connection on the home Wi-Fi).

Every setting this tool changes is read first and written to data/changes-<tv>.json with its old
value, before it changes. undo() puts every one back, newest first, and deleting a key the TV
never had. Running undo twice is harmless.

Nothing here switches an app off or uninstalls anything the TV came with. The only app installed
is ours (app.anytvart).
"""
import json
import os
import re
import shutil
import subprocess
import time

APP = "app.anytvart"
DREAM = APP + "/.ArtDream"
ACTIVITY = APP + "/.ArtActivity"
APP_FILES = "/sdcard/Android/data/%s/files" % APP
SDK_ADB = os.path.expanduser("~/Library/Android/sdk/platform-tools/adb")

# The settings we may change, and nothing else. (namespace, key)
ALLOWED = {
    ("secure", "screensaver_components"), ("secure", "screensaver_enabled"),
    ("secure", "screensaver_activate_on_sleep"), ("secure", "screensaver_activate_on_dock"),
    ("system", "screen_off_timeout"), ("secure", "sleep_timeout"), ("secure", "attentive_timeout"),
}
# Read only: anything with these words is listed by read(), to find picture or power levers.
LEVER_WORDS = ("picture", "backlight", "power", "sleep", "screen", "dream", "energy", "standby", "eco")


class AdbError(Exception):
    pass


def find_adb(cfg=None):
    want = (cfg.get("adb") if cfg else None) or os.environ.get("ANYTVART_ADB")
    for p in (want, shutil.which("adb"), SDK_ADB):
        if p and os.path.exists(p):
            return p
    raise AdbError("adb was not found. Install Android platform-tools (docs/GOOGLE-TV.md, \"Before you start\").")


class Android:
    def __init__(self, cfg, tv, run=subprocess.run, adb=None):
        self.cfg, self.tv, self._run = cfg, tv, run
        self.adb = adb or find_adb(cfg)
        self.serial = "%s:%s" % (tv["ip"], tv["port"])
        safe = "".join(c if c.isalnum() else "-" for c in tv["name"].lower())
        self.changes_file = cfg.file("changes-%s.json" % safe)

    # ------------------------------------------------------------------ plumbing

    def _adb(self, *args, timeout=20):
        r = self._run([self.adb, "-s", self.serial] + list(args), capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise AdbError((r.stderr or r.stdout or "adb failed").strip()[-300:])
        return r.stdout

    def connect(self):
        r = self._run([self.adb, "connect", self.serial], capture_output=True, text=True, timeout=15)
        out = (r.stdout or "") + (r.stderr or "")
        if "connected" not in out or "cannot" in out or "failed" in out:
            raise AdbError("could not reach %s over ADB: %s" % (self.serial, out.strip()[-200:]))
        if "unauthorized" in self._run([self.adb, "devices"], capture_output=True, text=True, timeout=10).stdout:
            raise AdbError("the TV has not allowed this computer yet: choose Allow (and Always allow) on the TV")
        return True

    def shell(self, cmd, timeout=20):
        return self._adb("shell", cmd, timeout=timeout)

    # ------------------------------------------------------------------ read only

    def identify(self):
        p = lambda k: self.shell("getprop " + k).strip()
        size = re.search(r"(\d+)x(\d+)", self.shell("wm size") or "")
        free = self.shell("df -k /data | tail -1").split()
        return {"maker": p("ro.product.manufacturer"), "model": p("ro.product.model"),
                "android": p("ro.build.version.release"), "sdk": p("ro.build.version.sdk"),
                "google_tv": "com.google.android.apps.tv.launcherx" in self.shell("pm list packages com.google.android.apps.tv.launcherx"),
                "app_px": [int(size.group(1)), int(size.group(2))] if size else None,
                "free_mb": int(free[3]) // 1024 if len(free) > 3 and free[3].isdigit() else None}

    def get(self, ns, key):
        v = self.shell("settings get %s %s" % (ns, key)).strip()
        return None if v in ("null", "") else v

    def read(self):
        """The settings that matter, plus every key that looks like a picture or power lever."""
        out = {"%s/%s" % k: self.get(*k) for k in sorted(ALLOWED)}
        levers = {}
        for ns in ("global", "secure", "system"):
            for line in self.shell("settings list " + ns).splitlines():
                key = line.split("=", 1)[0]
                if any(w in key.lower() for w in LEVER_WORDS):
                    levers["%s/%s" % (ns, key)] = line.split("=", 1)[1] if "=" in line else ""
        out["levers"] = levers
        return out

    def state(self):
        """{"reachable", "awake", "ours", "playing"}: what the TV is doing right now."""
        try:
            power = self.shell("dumpsys power | grep -E 'mWakefulness=|Display Power: state='")
        except (AdbError, subprocess.TimeoutExpired, OSError):
            return {"reachable": False}
        wake = re.search(r"mWakefulness=(\w+)", power)
        wake = wake.group(1) if wake else ""
        dreams = self.shell("dumpsys dreams | grep -iE 'mCurrentDream|dreamComponent|mDreamToken'")
        top = self.shell("dumpsys activity activities | grep -E 'topResumedActivity|mResumedActivity' | head -1")
        playing = "state=3" in self.shell("dumpsys media_session | grep -E 'state=PlaybackState'")
        ours = (wake == "Dreaming" and APP in dreams) or APP in top
        return {"reachable": True, "awake": wake in ("Awake", "Dreaming"), "ours": ours, "playing": playing,
                "wakefulness": wake}

    # ------------------------------------------------------------------ changes, always recorded

    def _changes(self):
        try:
            with open(self.changes_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return []

    def _save(self, changes):
        tmp = self.changes_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(changes, f, indent=2)
        os.replace(tmp, self.changes_file)

    def put(self, ns, key, value):
        if (ns, key) not in ALLOWED:
            raise AdbError("%s/%s is not on the list of settings this tool may change" % (ns, key))
        old = self.get(ns, key)
        changes = self._changes()
        if not any(c["ns"] == ns and c["key"] == key for c in changes):
            changes.append({"ns": ns, "key": key, "old": old, "at": time.time()})
            self._save(changes)          # recorded before the TV is touched
        self.shell("settings put %s %s %s" % (ns, key, value))
        now = self.get(ns, key)
        if now != str(value):
            raise AdbError("the TV did not keep %s/%s=%s (it says %s)" % (ns, key, value, now))
        return old

    def undo(self):
        """Put back every recorded value, newest first. Returns what it did."""
        done = []
        changes = self._changes()
        for c in reversed(changes):
            if c["old"] is None:
                self.shell("settings delete %s %s" % (c["ns"], c["key"]))
            else:
                self.shell("settings put %s %s %s" % (c["ns"], c["key"], c["old"]))
            done.append("%s/%s back to %s" % (c["ns"], c["key"], c["old"] if c["old"] is not None else "(not set)"))
        self._save([])
        return done

    # ------------------------------------------------------------------ the app and the remote

    def installed(self):
        return APP in self.shell("pm list packages " + APP)

    def install(self, apk):
        return self._adb("install", "-r", apk, timeout=180)

    def uninstall(self):
        return self._adb("uninstall", APP, timeout=60)

    def push_config(self, local_json):
        self.shell("mkdir -p %s/photos" % APP_FILES)
        return self._adb("push", local_json, APP_FILES + "/config.json")

    def push_photo(self, local, name):
        return self._adb("push", local, "%s/photos/%s" % (APP_FILES, name), timeout=120)

    def app_status(self):
        try:
            return json.loads(self.shell("cat %s/status.json" % APP_FILES))
        except (AdbError, ValueError):
            return None

    def open_art(self):
        return self.shell("am start -n " + ACTIVITY)

    def key(self, code):
        # POWER toggles sleep. On our 98 inch Google TV it also wakes the TV from network standby (about the
        # first 50 s after off); WAKEUP did not (our own test, 22 Oct 2026).
        return self.shell("input keyevent " + code)

    def sleep(self):
        st = self.state()
        if st.get("awake"):
            self.key("KEYCODE_POWER")
        return st

    def wake(self):
        st = self.state()
        if st.get("reachable") and not st.get("awake"):
            self.key("KEYCODE_POWER")
        return st
