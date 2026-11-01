"""What kind of TV is at this address? Read only: it knocks on a few ports and asks Samsung TVs
their model over their own web address. Nothing on the TV changes and no prompt appears.

The family decides the route (docs/OTHER-TVS.md): Google TV and Android TV get our app, a
Samsung with Art Mode gets the daily picture, everything else gets honest advice.
"""
import socket
from concurrent.futures import ThreadPoolExecutor

from .discover import describe, own_network

PORTS = {8001: "samsung", 8002: "samsung", 3000: "lg", 3001: "lg", 8060: "roku",
         5555: "adb", 6466: "android-remote", 6467: "android-remote", 8009: "cast", 7000: "airplay"}
SAMSUNG_YEAR = {"T": 2020, "A": 2021, "B": 2022, "C": 2023, "D": 2024, "F": 2025, "H": 2026}


def _open(ip, port, timeout=0.8):
    try:
        socket.create_connection((ip, port), timeout=timeout).close()
        return True
    except OSError:
        return False


def knock(ip):
    with ThreadPoolExecutor(len(PORTS)) as ex:
        found = list(ex.map(lambda p: (p, _open(ip, p)), PORTS))
    return sorted(p for p, ok in found if ok)


def samsung_year(model):
    """The year letter after the size in Samsung model numbers: QA55Q60AAWXXY is 2021 (A)."""
    import re
    m = re.match(r"^(?:QA|UA|QN|UN|QE|UE|GQ|GU)\d{2}[A-Z]{1,3}\d{2,3}([A-Z])", model or "")
    return SAMSUNG_YEAR.get(m.group(1)) if m else None


def family(ip):
    ports = knock(ip)
    out = {"ip": ip, "ports": ports, "family": "unknown", "route": "", "details": {}}
    if 8001 in ports or 8002 in ports:
        d = describe(ip) or {}
        out["details"] = d
        out["details"]["year"] = samsung_year(d.get("model", ""))
        if d.get("frame"):
            out["family"], out["route"] = "samsung-art", "Art Mode: the daily print-look picture (docs/SAMSUNG-FRAME.md)"
        else:
            out["family"], out["route"] = "samsung", "No Art Mode found: see docs/OTHER-TVS.md, Samsung without Art Mode"
    elif 3000 in ports or 3001 in ports:
        out["family"], out["route"] = "lg", "LG: Always Ready first (docs/OTHER-TVS.md, LG)"
    elif 8060 in ports:
        out["family"], out["route"] = "roku", "Roku: its own screensaver only (docs/OTHER-TVS.md, Roku)"
    elif 5555 in ports or 6466 in ports or 6467 in ports:
        out["family"], out["route"] = "android", "Google TV or Android TV: our art app (docs/GOOGLE-TV.md)"
        if 5555 not in ports:
            out["route"] += ". Network debugging is off: switch it on first (docs/GOOGLE-TV.md, step 1)"
    elif 8009 in ports:
        out["family"], out["route"] = "cast-only", "Answers Cast but nothing else: check docs/OTHER-TVS.md"
    elif 7000 in ports:
        out["family"], out["route"] = "airplay", "Apple TV or an AirPlay TV: docs/OTHER-TVS.md, Apple TV"
    return out


def scan(timeout=0.4):
    """Every address on this computer's home network with a TV-like port open."""
    try:
        ips = [str(h) for h in own_network().hosts()]
    except OSError:
        return []
    tv_ports = (8001, 8002, 3000, 8060, 5555, 6466, 8009)

    def probe(ip):
        return ip if any(_open(ip, p, timeout) for p in tv_ports) else None
    with ThreadPoolExecutor(64) as ex:
        return [ip for ip in ex.map(probe, ips) if ip]
