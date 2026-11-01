"""What art costs to run, in dollars a year, so the hours are picked with the price beside them.

Watts come from config (measured with a plug-in meter is best) or a rough guess by screen size.
The guess is labelled a guess everywhere it is printed.
"""

HOURS = (("idle only", 1.5), ("home hours", 6), ("all day", 12))


def guess_watts(tv):
    """A rough figure when nothing is measured. LCD art draws close to full TV power, because
    dimming the picture does not dim the backlight on most TVs (docs/POWER.md)."""
    if tv["kind"] == "samsung-art":
        inch = float(tv["size_inch"])
        return round(50.0 * (inch / 65) ** 2), "guess: Samsung Art Mode, about 30%% of TV power at %d inch" % inch
    inch = float(tv["size_inch"])
    w = 0.0315 * inch ** 2 if tv["panel"] == "lcd" else 0.022 * inch ** 2
    return round(w), "guess from the screen size (%s inch %s)" % (int(inch), tv["panel"].upper())


def watts(tv):
    if tv.get("watts_art"):
        return float(tv["watts_art"]), "measured"
    return guess_watts(tv)


def per_year(w, hours_a_day, price_kwh):
    return w / 1000.0 * hours_a_day * 365 * price_kwh


def table(cfg):
    """Rows for every TV: name, watts, source, dollars a year per daily hour and for each option."""
    price = float(cfg["price_kwh"])
    rows = []
    for tv in cfg["tvs"]:
        w, src = watts(tv)
        rows.append({"tv": tv["name"], "watts": w, "source": src, "per_hour": per_year(w, 1, price),
                     "options": [(name, h, per_year(w, h, price)) for name, h in HOURS]})
    return rows


def report(cfg):
    lines = ["Running cost of art, at $%.2f a kWh (set price_kwh in config.json to your own rate)" % cfg["price_kwh"]]
    for r in table(cfg):
        lines.append("")
        lines.append("%s: about %d W showing art (%s)" % (r["tv"], r["watts"], r["source"]))
        lines.append("  every hour a day of art costs about $%.0f a year" % r["per_hour"])
        for name, h, cost in r["options"]:
            lines.append("  %-11s %4.1f h a day  about $%.0f a year" % (name, h, cost))
    lines.append("")
    lines.append("Lowest power: art only after someone has used the TV, ended by the TV's own timer.")
    lines.append("On a Samsung with Art Mode, the motion sensor and brightness sensor cut it further.")
    return "\n".join(lines)
