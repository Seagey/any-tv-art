"""A pretend Android TV for the tests: answers the adb commands drivers/android.py sends, keeps its
settings in a dict, and records every command so a test can check exactly what was sent."""
import subprocess


class FakeTV:
    def __init__(self, settings=None, wake="Asleep", playing=False, dreaming_ours=False, top="com.google.android.apps.tv.launcherx"):
        self.settings = {("secure", "screensaver_components"): "com.google.android.backdrop/.Backdrop",
                         ("secure", "screensaver_enabled"): "1", ("system", "screen_off_timeout"): "900000",
                         ("secure", "attentive_timeout"): "14400000",
                         ("secure", "sleep_timeout"): "-1"}
        self.settings.update(settings or {})
        self.wake, self.playing, self.dreaming_ours, self.top = wake, playing, dreaming_ours, top
        self.commands, self.installed, self.pushed, self.refuse = [], False, [], set()

    def __call__(self, argv, capture_output=True, text=True, timeout=None):
        self.commands.append(argv)
        if argv[1] == "connect":
            return subprocess.CompletedProcess(argv, 0, "connected to %s\n" % argv[2], "")
        if argv[1] == "devices":
            return subprocess.CompletedProcess(argv, 0, "List of devices attached\n%s\tdevice\n" % "tv", "")
        args = argv[3:]                     # after adb -s serial
        out = self._answer(args)
        return subprocess.CompletedProcess(argv, 0, out, "")

    def _answer(self, args):
        if args[0] == "install":
            self.installed = True
            return "Success\n"
        if args[0] == "uninstall":
            self.installed = False
            return "Success\n"
        if args[0] == "push":
            self.pushed.append(args[2])
            return "1 file pushed\n"
        cmd = args[1]
        if cmd.startswith("settings get "):
            _, _, ns, key = cmd.split()
            return "%s\n" % self.settings.get((ns, key), "null")
        if cmd.startswith("settings put "):
            _, _, ns, key, value = cmd.split()
            if (ns, key) not in self.refuse:
                self.settings[(ns, key)] = value
            return ""
        if cmd.startswith("settings delete "):
            _, _, ns, key = cmd.split()
            self.settings.pop((ns, key), None)
            return ""
        if cmd.startswith("settings list "):
            ns = cmd.split()[2]
            return "".join("%s=%s\n" % (k, v) for (n, k), v in self.settings.items() if n == ns) + \
                ("power_picture_off=0\n" if ns == "global" else "")
        if cmd.startswith("getprop "):
            return {"ro.product.manufacturer": "Maker", "ro.product.model": "Model 98",
                    "ro.build.version.release": "14", "ro.build.version.sdk": "34"}.get(cmd.split()[1], "") + "\n"
        if cmd == "wm size":
            return "Physical size: 1920x1080\n"
        if cmd.startswith("df "):
            return "/dev/block/dm-5 8000000 4000000 4000000 50% /data\n"
        if cmd.startswith("pm list packages"):
            pkg = cmd.split()[-1]
            if pkg == "app.anytvart":
                return "package:app.anytvart\n" if self.installed else ""
            return "package:%s\n" % pkg
        if cmd.startswith("dumpsys power"):
            return "  mWakefulness=%s\n" % self.wake
        if cmd.startswith("dumpsys dreams"):
            return "  mCurrentDream=app.anytvart/.ArtDream\n" if self.dreaming_ours and self.wake == "Dreaming" else ""
        if cmd.startswith("dumpsys activity"):
            return "  topResumedActivity=ActivityRecord{1 u0 %s/.Main t1}\n" % self.top
        if cmd.startswith("cmd package resolve-activity"):
            return "priority=0 preferredOrder=0 match=0x108000 specificIndex=-1 isDefault=true\n" \
                   "com.google.android.apps.tv.launcherx/.home.HomeActivity\n"
        if cmd.startswith("dumpsys media_session"):
            return "    state=PlaybackState {state=3, position=0}\n" if self.playing else ""
        if cmd.startswith("input keyevent KEYCODE_POWER"):
            self.wake = "Asleep" if self.wake in ("Awake", "Dreaming") else "Awake"
            return ""
        if cmd.startswith("am start"):
            self.top = "app.anytvart"
            return "Starting: Intent\n"
        if cmd.startswith("mkdir") or cmd.startswith("cat"):
            return ""
        return ""
