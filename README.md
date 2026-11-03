# Any TV Art

Turn the TV you already own into a matted picture on the wall. A photo of yours, set in an
off-white mat with a thin bevel and a small label (the day, the weather, what is on today), the
way a print sits in a frame. It is like Samsung's The Frame, without buying one.

## Where this is up to (read this first)

**Phase 1: Google TV and Samsung TVs with Art Mode only.** One Google TV has run it (a 98 inch LCD,
2 November 2026): setup with and without a computer, art after 10 minutes idle, any button back to
TV, the label with date, weather and calendar from the bridge, and the undo. Not yet checked on that
TV: a restart, and a film holding sleep off. **No Samsung has run this repo yet**, and no other
Google TV. Every other route in the table says "Built, not yet tested" until a real TV has run it.
If you try it, please tell us what happened: [the tester form](.github/ISSUE_TEMPLATE/tv-report.yml).

## Will it work on my TV?

| TV | Works, tested by us | Built, not yet tested | Reported by owners | Not possible, and why |
|---|---|---|---|---|
| **Google TV and Android TV** (Sony, TCL, Hisense, Philips, Xiaomi, Onn, Chromecast with Google TV and others) | One 98 inch LCD Google TV, with and without a computer (2 Nov 2026) | **Yes**, every other model. Our screensaver app, set up once over ADB. With or without a computer. [GOOGLE-TV.md](docs/GOOGLE-TV.md) | none yet | |
| **Samsung with Art Mode** (2021 and newer) | none yet | **Yes.** A fresh picture in real Art Mode each day, from a computer. The upload code comes from [smart-frame-tv](https://github.com/Seagey/smart-frame-tv), which has run on a 2021 Samsung with Art Mode, but this repo has not. [Samsung guide](docs/SAMSUNG-FRAME.md) | none yet | |
| Samsung 2025 and newer QLED, Neo QLED and OLED with Art Mode | none yet | **Yes**, but we do not know if these accept our upload at all | none yet | |
| LG, Sony Linux models, Fire TV, Roku, Apple TV, Hisense VIDAA, Samsung without Art Mode, any TV through an HDMI box | none yet | **No.** Not built in phase 1 | none yet | Some of these have no way in at all (Roku has no network power-on, Fire TV Vega OS has no sideloading). Each family's honest route is in [OTHER-TVS.md](docs/OTHER-TVS.md) |

If your TV is not in the first two rows, it is not supported yet. [OTHER-TVS.md](docs/OTHER-TVS.md)
says what to do instead, and why.

## Two ways to run it

**With an always-on computer at home** (a Mac that stays on; Linux and Raspberry Pi are built
from the sibling repo's scripts and not tested):

- Google TV: the TV app shows the art as its screensaver. The computer feeds it the weather,
  the calendar and reminders, and the brightness curve. It can wake the TV in the morning and
  put it to sleep at night.
- Samsung with Art Mode: the computer makes a new picture each morning and uploads it. Art
  brightness follows the room on a curve.

**Without a computer** (a one-time setup from a laptop, then nothing has to stay on):

- Google TV: the TV app makes the picture itself: photo, date, weather and a quote. Photos are
  copied onto the TV once. No calendar or reminders yet, no morning wake. The TV's own inactivity
  timer ends the art. This is also the lowest-power way.
- Samsung with Art Mode: Art Mode keeps working, but there is no daily picture. You can add a
  picture by hand with Samsung's phone app.

Why a one-time setup on Google TV? Most Google TVs have no menu for picking a third-party
screensaver. ADB (a developer connection over your Wi-Fi) is the only way in.

## What it costs to run

Honest answer first: **on a big LCD, the only real saving is fewer hours.** Dimming the picture
does not dim the backlight on most LCD TVs, so a dark picture costs nearly the same as a bright
one. A 98 inch LCD showing art all day is about **$526 a year** at 40 c a kWh (an Australian
regional electricity price; set your own with `price_kwh`). **Art only when the TV is idle is the
lowest-power option.** `anytvart power` prints this table for your own TVs.

| TV | Watts showing art | Per daily hour, a year | Idle only, 1.5 h a day | Home hours, 6 h | All day, 12 h |
|---|---|---|---|---|---|
| 98 inch LCD Google TV | about 300 W (a guess, range 250 to 340 W) | $44 | $66 | $263 | **$526** |
| 65 inch Samsung with Art Mode | about 50 W (a guess; up to 130 W in a bright room) | $7 (up to $19) | $11 | $44 | $88 (up to $228) |
| 55 inch LCD Google TV | about 90 W (a guess) | $13 | $20 | $79 | $158 |
| A smaller TV | about 60 W (a guess) | $9 | $13 | $53 | $105 |
| Any of them in standby | under 0.5 W | | | | under $2 for the year |

Every watts figure is a guess until you measure it with a plug-in energy meter (about $15) and put
the result in `watts_art`. [POWER.md](docs/POWER.md) explains how. The cheapest way to have art on
a wall is a TV built for it (a Samsung with Art Mode, an LG with Always Ready, an OLED at low
brightness with the burn-in rules) or a smaller TV.

## Quick start, with an AI agent

You do not need to be technical. Give this link to Claude Code, or any AI agent that can run
commands on your computer, and say:

> Set this up on my TV.

The agent follows [AGENTS.md](AGENTS.md). It finds the TV, asks you plain questions, reads the plan
back, and changes nothing until you say yes. It tests with you watching and shows you the undo.

By hand, the commands are in [docs/GOOGLE-TV.md](docs/GOOGLE-TV.md) and
the [Samsung guide](docs/SAMSUNG-FRAME.md), and every setting is in
[docs/CONFIG.md](docs/CONFIG.md). The first step is the same for both:

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .
.venv/bin/anytvart identify
```

`identify` only looks. It changes nothing on any TV.

## What it does to the picture

- **Mat:** off-white (never pure white, which glows on a screen), a thin lit bevel, a shadow onto
  the photo.
- **Paper grain:** optional, only where a screen pixel is small enough to carry it.
- **Flattening:** lifts the blacks and rolls off the highlights, the range of a print.
- **Light:** the picture follows the sun, dimmer and warmer through dusk, then off at night.
- **Glare:** software can reduce how much glare shows. It cannot remove it. [GLARE.md](docs/GLARE.md)
  says what it cannot fix first.

On Android we make **no 4K claim**: many Android TVs draw apps at 1080p and scale up.

## Undo

```sh
.venv/bin/anytvart undo --tv "Lounge"
```

Android: every setting we changed goes back to the value we wrote down first, and our app and its
photos are removed. Samsung: your own picture is put back, then only the pictures this tool
uploaded are deleted. Running it twice is harmless.

## Privacy, in three lines

1. Everything runs at home. No account, no cloud service, no analytics. The only traffic out is the
   weather request to Open-Meteo (a rounded latitude and longitude) and, if you add one, your own
   calendar link.
2. Your settings, TV addresses and tokens live in `config.json` and `data/`, which git ignores.
   If an agent looks at a photo of your room, it goes to your own AI provider and nowhere else.
3. Never post your own `config.json`. `anytvart report` makes a version with addresses and names
   taken out. [PRIVACY.md](docs/PRIVACY.md) has the detail.

## Docs

[GOOGLE-TV.md](docs/GOOGLE-TV.md) ·
[Samsung guide](docs/SAMSUNG-FRAME.md) ·
[OTHER-TVS.md](docs/OTHER-TVS.md) ·
[POWER.md](docs/POWER.md) ·
[GLARE.md](docs/GLARE.md) ·
[PRIVACY.md](docs/PRIVACY.md) ·
[CONFIG.md](docs/CONFIG.md) ·
[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Credits

- [smart-frame-tv](https://github.com/Seagey/smart-frame-tv) (MIT, same author): the picture
  template, the info blocks and the Samsung upload code began as a copy of it.
- [samsungtvws](https://github.com/NickWaterton/samsung-tv-ws-api) by Xchwarze and Nick Waterton
  (LGPL-3.0), for the Samsung art connection.
- [Open-Meteo](https://open-meteo.com/) for weather and sunlight (CC BY 4.0). Pillow, icalendar and
  recurring-ical-events for images and calendars.
- Fonts: Cormorant Garamond and Jost (SIL Open Font License, in `anytvart/fonts`).

Not made by or affiliated with Samsung or any TV maker.

## Licence

MIT. See [LICENSE](LICENSE).
