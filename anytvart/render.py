"""Making the picture on this computer with headless Chrome (or Chromium, Edge, Brave).

The same template the TV app uses (picture/template/print.html), so a preview here is what the TV
shows. Sizes: 4k is 3840x2160 (a Samsung in Art Mode), 1080 and 720 are what most Android TVs
draw their apps at, whatever the panel is.
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

from . import photos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(HERE, "fonts")
TEMPLATE = os.path.join(ROOT, "picture", "template", "print.html")
SIZES = {"4k": (1920, 1080, 2), "1080": (1920, 1080, 1), "720": (1280, 720, 1)}

FONT_FACES = [
    ("Cormorant Garamond", "normal", 500, "CormorantGaramond-Medium.ttf"),
    ("Cormorant Garamond", "normal", 600, "CormorantGaramond-SemiBold.ttf"),
    ("Cormorant Garamond", "italic", 500, "CormorantGaramond-MediumItalic.ttf"),
    ("Jost", "normal", 400, "Jost-Regular.ttf"),
    ("Jost", "normal", 500, "Jost-Medium.ttf"),
]
FOCUS_CSS = {"centre": "50% 50%", "center": "50% 50%", "top": "50% 20%", "bottom": "50% 80%",
             "left": "20% 50%", "right": "80% 50%"}

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
CHROME_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "brave-browser"]


def find_chrome(cfg=None):
    want = (cfg.get("chrome") if cfg else None) or os.environ.get("ANYTVART_CHROME")
    if want:
        return want if os.path.exists(want) else shutil.which(want)
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    for n in CHROME_NAMES:
        p = shutil.which(n)
        if p:
            return p
    return None


def _font_css():
    rules = []
    for family, style, weight, file in FONT_FACES:
        with open(os.path.join(FONTS, file), "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        rules.append('@font-face { font-family: "%s"; font-style: %s; font-weight: %d; font-display: block; '
                     'src: url(data:font/ttf;base64,%s) format("truetype"); }' % (family, style, weight, b64))
    return "\n".join(rules)


def page(data):
    """The template with the fonts and the data built in, ready for a browser with no network."""
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r"/\*FONTS\*/.*?/\*/FONTS\*/", lambda m: _font_css(), html, flags=re.S)
    return html.replace("/*DATA*/null", json.dumps(data).replace("</", "<\\/"))


def picture_data(cfg, tv, info, photo_url, light=None, drift=None):
    """The data the template draws: the same shape the bridge serves to the TV app."""
    return {"photo": photo_url, "focus": FOCUS_CSS.get(cfg["photos"].get("focus", "centre"), "50% 50%"),
            "info": info, "look": tv["look"], "screen": tv["screen"], "safe": tv.get("safe", {}),
            "drift": drift or {"x": 0, "y": 0}, "light": light or {"dim": 0, "warm": 0}}


def render(cfg, tv, photo_path, info, out_path, size="4k", light=None, extra=None):
    """Make the picture for one TV and save it (JPEG, or PNG if out_path ends in .png).
    extra is merged into the data, for example {"card": True} for the calibration card."""
    if size not in SIZES:
        raise ValueError("size must be one of %s" % ", ".join(SIZES))
    chrome = find_chrome(cfg)
    if not chrome:
        raise RuntimeError("Chrome was not found (install Google Chrome or Chromium, or set \"chrome\" in config.json)")
    w, h, scale = SIZES[size]
    with tempfile.TemporaryDirectory(prefix="anytvart-") as tmp:
        if photo_path:
            photos.prepare(photo_path, os.path.join(tmp, "photo.jpg"), cfg["photos"].get("focus", "centre"))
        data = picture_data(cfg, tv, info, "photo.jpg" if photo_path else "", light)
        data.update(extra or {})
        html = os.path.join(tmp, "picture.html")
        with open(html, "w", encoding="utf-8") as f:
            f.write(page(data))
        png = os.path.join(tmp, "shot.png")
        args = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                "--no-default-browser-check", "--disable-extensions", "--mute-audio",
                "--window-size=%d,%d" % (w, h), "--force-device-scale-factor=%d" % scale,
                "--virtual-time-budget=6000", "--user-data-dir=" + os.path.join(tmp, "profile"),
                "--screenshot=" + png, "file://" + html.replace("\\", "/")]
        if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
            args.insert(1, "--no-sandbox")   # Chromium refuses to start as root without it
        r = subprocess.run(args, capture_output=True, timeout=120)
        if not os.path.exists(png):
            raise RuntimeError("no screenshot (exit %s): %s" % (r.returncode, r.stderr.decode(errors="replace")[-300:].strip()))
        im = Image.open(png).convert("RGB")
        want = (w * scale, h * scale)
        if im.size != want:
            im = im.resize(want, Image.LANCZOS)
        if out_path.lower().endswith(".png"):
            im.save(out_path, "PNG")
        else:
            im.save(out_path, "JPEG", quality=92)
    return out_path
