"""anytvart: the commands.

  Read only (nothing on any TV changes):
  anytvart identify [IP] [--scan]     what kind of TV is this, and which route fits it
  anytvart read --tv NAME             the TV's model, screen and settings that matter (Android)
  anytvart check --tv NAME            Art Mode, brightness, what is showing (Samsung)
  anytvart preview [--tv NAME]        make the picture on this computer to look at
  anytvart power                      what art costs a year on each TV, at your price per kWh
  anytvart plan --tv NAME --mode M    what `apply` would change, in plain words
  anytvart report --tv NAME           a tester report with names, addresses and serials removed
  anytvart photo-prep PHOTO           strip location and camera data from a room photo

  Changes (only after the owner has said yes, AGENTS.md):
  anytvart apply --tv NAME --mode bridge|alone    put the art on an Android TV
  anytvart show --tv NAME             open the art now, to look at it
  anytvart card on|off --tv NAME      show the calibration card instead of the picture
  anytvart pair --tv NAME             Samsung: press Allow on the TV once
  anytvart picture --tv NAME          Samsung: make and show today's picture now
  anytvart bridge                     run the bridge (serve the apps, the daily cycle)
  anytvart undo --tv NAME             put every setting back and take our app or pictures off
"""
import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime

from . import __version__, config, info, photos, power, render

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(REPO, "samples", "photos")


def _cfg(args, required=True):
    return config.load(args.config, required=required)


def _yes(args, what):
    if args.yes:
        return True
    return input('%s Type "yes" to go ahead: ' % what).strip().lower() == "yes"


# ------------------------------------------------------------------ read only

def cmd_identify(args):
    from . import identify
    ips = [args.ip] if args.ip else []
    if args.scan or not ips:
        print("Looking for TVs on this network (about 20 seconds)...")
        ips = identify.scan()
    if not ips:
        print("No TV answered. Is it on, and on the same Wi-Fi as this computer?")
        return 1
    for ip in ips:
        f = identify.family(ip)
        d = f["details"]
        extra = " %s %s" % (d.get("model", ""), "(%s)" % d["year"] if d.get("year") else "") if d else ""
        print("%-15s  %-12s%s\n                 %s" % (ip, f["family"], extra, f["route"] or "no TV ports open"))
    return 0


def cmd_read(args):
    from .drivers.android import Android
    cfg = _cfg(args)
    a = Android(cfg, cfg.tv(args.tv))
    a.connect()
    print(json.dumps({"identify": a.identify(), "settings": a.read(), "now": a.state(),
                      "app": a.app_status()}, indent=2))
    return 0


def cmd_check(args):
    from .drivers.samsung_art import Frame

    async def go(cfg, tv):
        async with Frame(cfg, tv) as frame:
            return {"art_mode": await frame.art_mode(), "has_art_mode": await frame.has_art_mode(),
                    "api": await frame.api_version(), "brightness": await frame.brightness(),
                    "colour_temperature": await frame.colour_temperature(), "showing": await frame.current()}
    cfg = _cfg(args)
    print(json.dumps(asyncio.run(go(cfg, cfg.tv(args.tv))), indent=2, default=str))
    return 0


def cmd_preview(args):
    cfg = _cfg(args, required=False)
    if cfg["tvs"]:
        tv = cfg.tv(args.tv)
    else:
        tv = config.Config({"tvs": [{"name": "preview", "size_inch": args.inch}]}).data["tvs"][0]
    size = args.size or ("4k" if tv["kind"] == "samsung-art" else "1080" if tv["app_px"][0] >= 1920 else "720")
    drawn = {"4k": 3840, "1080": 1920, "720": 1280}[size]
    tv = dict(tv, screen=config.screen_for(tv, drawn))
    if args.photo:
        photo = args.photo
    else:
        try:
            photo = os.path.join(cfg.photo_folder, photos.list_photos(cfg.photo_folder)[0])
        except photos.PhotoError:
            photo = os.path.join(SAMPLES, sorted(os.listdir(SAMPLES))[0])
    details = info.sample_info(cfg) if args.sample or not cfg.path or not os.path.exists(cfg.path) else info.gather(cfg)
    out = args.out or cfg.file("preview-%s-%s.png" % (re.sub(r"\W+", "-", tv["name"].lower()), size))
    if args.card:
        out = args.out or cfg.file("card-%s.png" % size)
        render.render(cfg, tv, None, details, out, size, extra={"card": True})
        print(out)
        return 0
    render.render(cfg, tv, photo, details, out, size)
    print(out)
    return 0


def cmd_power(args):
    cfg = _cfg(args)
    print(power.report(cfg))
    return 0


def cmd_plan(args):
    from . import setup_android
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    if tv["kind"] != "android":
        print("For a Samsung with Art Mode there is nothing to install: `anytvart pair`, then `anytvart picture`.")
        return 0
    for line in setup_android.plan(cfg, tv, args.mode):
        print("- " + line)
    return 0


REDACT = [(re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "<ip>"),
          (re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b"), "<mac>"),
          (re.compile(r'"(?:serial|ro\.serialno|device_name|bluetooth_name|name)"\s*:\s*"[^"]*"'), '"<name>": "<removed>"')]


def redact(text, words=()):
    for rx, sub in REDACT:
        text = rx.sub(sub, text)
    for w in words:
        if w:
            text = re.sub(re.escape(w), "<removed>", text, flags=re.I)
    return text


def cmd_report(args):
    """What a tester pastes into the GitHub form: the TV's family, model, system and settings,
    with addresses, names and serial numbers taken out. They read it before they paste it."""
    from . import identify
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    rep = {"tool": __version__, "family": identify.family(tv["ip"])}
    if tv["kind"] == "android":
        from .drivers.android import Android
        a = Android(cfg, tv)
        a.connect()
        rep.update({"identify": a.identify(), "settings": a.read(), "app": a.app_status()})
    words = [tv["name"], cfg["place"].get("name", "")]
    print(redact(json.dumps(rep, indent=2, default=str), words))
    print("\nRead it through before you paste it: if you see anything personal, delete it.")
    return 0


def cmd_photo_prep(args):
    from . import photoprep
    cfg = _cfg(args, required=False)
    crop = tuple(float(x) for x in args.crop.split(",")) if args.crop else None
    out = photoprep.prep(args.photo, os.path.join(cfg.data_dir, "checks"), crop)
    print(out)
    print("location data left: %s" % ("YES, do not send it" if photoprep.has_location(out) else "none"))
    return 0


# ------------------------------------------------------------------ changes

def cmd_apply(args):
    from . import setup_android
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    if tv["kind"] != "android":
        print("apply is for Android TVs. For a Samsung with Art Mode: `anytvart pair`, then `anytvart picture`.")
        return 1
    print("This will:")
    for line in setup_android.plan(cfg, tv, args.mode):
        print("- " + line)
    if not _yes(args, "Nothing has changed yet."):
        print("Nothing changed.")
        return 1
    apk = args.apk or os.path.join(REPO, "dist", "any-tv-art.apk")
    setup_android.apply(cfg, tv, args.mode, apk, say=lambda m: print("  " + m))
    print("Done. Leave the remote alone for %d minutes and the art appears; any button brings TV back." % (setup_android.IDLE_TO_ART_MS // 60000))
    return 0


def cmd_show(args):
    from . import setup_android
    cfg = _cfg(args)
    setup_android.show(cfg, cfg.tv(args.tv))
    return 0


def cmd_card(args):
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    flag = cfg.file("card-" + "".join(c if c.isalnum() else "-" for c in tv["name"].lower()))
    if args.state == "on":
        open(flag, "w").close()
        print("The bridge now serves the calibration card to %s. `anytvart show --tv \"%s\"` puts it on screen." % (tv["name"], tv["name"]))
    elif os.path.exists(flag):
        os.remove(flag)
        print("Back to the picture.")
    return 0


def cmd_pair(args):
    from .drivers.samsung_art import FrameError, pair
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    print("Connecting to %s. If the TV asks to allow \"any-tv-art\", choose Allow." % tv["name"])
    try:
        r = asyncio.run(pair(cfg, tv))
    except FrameError as e:
        print(e)
        return 1
    print("Paired%s in %ss." % ("" if r["token"] else " (this TV needs no token)", r["seconds"]))
    return 0


def cmd_picture(args):
    from . import frame_daily
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    got = frame_daily.run(cfg, tv, cfg.now(), force=True)
    if got is None:
        print("%s is not answering. Is it on (TV or Art Mode)?" % tv["name"])
    return 0 if got else 1


def cmd_bridge(args):
    from .bridge import serve
    serve(_cfg(args), args.port)
    return 0


def cmd_undo(args):
    cfg = _cfg(args)
    tv = cfg.tv(args.tv)
    if not _yes(args, "This puts back every setting this tool changed on %s and removes what it added." % tv["name"]):
        print("Nothing changed.")
        return 1
    if tv["kind"] == "android":
        from . import setup_android
        for line in setup_android.undo(cfg, tv, remove_app=not args.keep_app):
            print("  " + line)
    else:
        from . import frame_daily
        print(frame_daily.undo(cfg, tv))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="anytvart", description="Any TV as a matted picture on the wall.")
    p.add_argument("--config", help="settings file (default: config.json here)")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def tv_arg(sp):
        sp.add_argument("--tv", help="which TV, by its name in config.json")
        return sp
    i = sub.add_parser("identify", help="what kind of TV is at this address (read only)")
    i.add_argument("ip", nargs="?")
    i.add_argument("--scan", action="store_true")
    tv_arg(sub.add_parser("read", help="Android: model, screen and settings (read only)"))
    tv_arg(sub.add_parser("check", help="Samsung: Art Mode state (read only)"))
    v = tv_arg(sub.add_parser("preview", help="make the picture here, send nothing"))
    v.add_argument("--size", choices=["4k", "1080", "720"])
    v.add_argument("--photo")
    v.add_argument("--out")
    v.add_argument("--inch", type=float, default=55, help="screen size when no TV is set up yet")
    v.add_argument("--sample", action="store_true", help="made-up details instead of your own")
    v.add_argument("--card", action="store_true", help="the calibration card, as an HTML file")
    sub.add_parser("power", help="what art costs a year on each TV")
    pl = tv_arg(sub.add_parser("plan", help="what apply would change"))
    pl.add_argument("--mode", choices=["bridge", "alone"], default="bridge")
    tv_arg(sub.add_parser("report", help="a redacted tester report"))
    pp = sub.add_parser("photo-prep", help="strip location from a room photo")
    pp.add_argument("photo")
    pp.add_argument("--crop", help="left,top,right,bottom as fractions, e.g. 0.1,0.2,0.9,0.8")
    a = tv_arg(sub.add_parser("apply", help="put the art on an Android TV"))
    a.add_argument("--mode", choices=["bridge", "alone"], required=True)
    a.add_argument("--apk")
    a.add_argument("--yes", action="store_true")
    tv_arg(sub.add_parser("show", help="open the art now"))
    c = tv_arg(sub.add_parser("card", help="calibration card on or off"))
    c.add_argument("state", choices=["on", "off"])
    tv_arg(sub.add_parser("pair", help="Samsung: press Allow on the TV"))
    tv_arg(sub.add_parser("picture", help="Samsung: today's picture now"))
    b = sub.add_parser("bridge", help="run the bridge")
    b.add_argument("--port", type=int)
    u = tv_arg(sub.add_parser("undo", help="put everything back"))
    u.add_argument("--keep-app", action="store_true")
    u.add_argument("--yes", action="store_true")

    args = p.parse_args(argv)
    try:
        return globals()["cmd_" + args.cmd.replace("-", "_")](args)
    except config.ConfigError as e:
        print("config.json: %s" % e)
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print("%s: %s" % (type(e).__name__, e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
