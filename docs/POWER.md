# Power: what art costs, and how to pay less

**Hours are the saving.** On most LCD TVs, showing a dark or dim picture costs almost the same as a
bright one, because the backlight stays at its setting. We found no standard way for software to
lower the backlight on Google TV (none found; one maker keeps it inside its own settings app). Our
dimming changes the picture, not the backlight, so on an LCD it saves nothing. It saves some on OLED,
where each pixel makes its own light (the amount is a guess).

So the number that matters is **how many hours a day the screen is on showing art.** Labels:
**V** from a maker or the energy regulator, **R** from a retailer or owner reports, **G** a guess.

## What it costs a year

At **40 c a kWh** (an Australian regional electricity price; set your own with `price_kwh`). Every
figure scales with hours, so the "per daily hour" column is what one hour of art a day costs for a
year.

| TV | Watts showing art | Per daily hour | Idle only, 1.5 h | Home hours, 6 h | All day, 12 h |
|---|---|---|---|---|---|
| 98 inch LCD Google TV | about 300 W, range 250 to 340 W (G: other 98 inch labels are 249 W and 338 W, R) | **$44** | $66 | $263 | **$526** |
| Soundbar on HDMI CEC, if it stays on | not known, guess 10 to 30 W (G) | $1 to $4 | $2 to $7 | $9 to $26 | $18 to $53 |
| 65 inch Samsung with Art Mode | about 50 W (G: Samsung says about 30% of TV mode at 50 lux, V). Up to 130 W measured on an older 65 inch in a bright room (R) | $7 (up to $19) | $11 | $44 | **$88** (up to $228) |
| 55 inch LCD Google TV | about 90 W (G: a 55 inch label of 92 W, R) | $13 | $20 | $79 | $158 |
| A smaller TV | about 60 W (G) | $9 | $13 | $53 | $105 |
| Standby, any of them | under 0.5 W (R, labels) | | | | under $2 for the year |

Australian labels assume 10 hours a day (V, Energy Rating), so a label's yearly kWh divided by 3,650
hours gives average watts. The 98 inch figure is a range from labels of other 98 inch sets, not a
measurement of any particular TV.

## The lowest-power option

1. **Idle only** (`art_hours: "idle"`, the default). The screensaver starts only after someone has
   used the TV and left it for 10 minutes, and the TV's own timer ends it. About 1 to 2 hours a day.
2. **Home hours.** Art only while someone is home, from your own presence source: a phone on the Wi-Fi
   (`home_devices`, see [CONFIG.md](CONFIG.md)). Never cameras.
3. **A TV made for art.** A Samsung in Art Mode (its sensors and low-power mode apply), an LG with
   Always Ready, an OLED at low brightness with the burn-in rules, or a smaller TV.
4. **All day on a big LCD** works, and costs what the table says. The tool will not hide that.

`anytvart power` prints this for your own TVs, from `size_inch`, `panel` and `price_kwh`, or from
`watts_art` once you have measured it.

## Measure it

A plug-in energy meter (a smart plug with an energy meter is about $15 at a hardware shop; a plain
meter works too).

1. Put the meter between the wall and the TV's power cord (or the power board).
2. Note the watts with the TV on normal TV, then showing our art (`anytvart show --tv NAME`), then in
   standby. Give each a minute to settle.
3. Put the art reading in config:

   ```json
   "tvs": [{"name": "Lounge", "kind": "android", "ip": "192.0.2.20", "size_inch": 65, "watts_art": 118}]
   ```

4. `anytvart power` now says "measured" instead of "guess" for that TV.

If a soundbar is on the same plug, its share is in the number. Note it separately if you can.

## OLED notes

- OLED panels can keep a faint ghost of a picture that stays still. Set `"panel": "oled"` (the panel
  type is not readable over ADB, so you tell the tool).
- With `oled` set, the picture drifts by up to 6 pixels, a new offset each hour.
  Use a new picture at least hourly, a darker mat, and the night cut-off.
- **LG OLEDs dim still pictures by themselves** (V). That fights any brightness curve, which is why LG
  OLED owners should use Always Ready first ([OTHER-TVS.md](OTHER-TVS.md)).
- OLED handling is built and **not tested**: no OLED has run it.

## Standby and the wake

Waking a TV in the morning needs the network up in standby, which on Android 14 is the Optimised or
Increased energy mode. Increased costs standby power (how much is not known). A TV on Low cannot be
woken by the bridge. See [GOOGLE-TV.md](GOOGLE-TV.md).
