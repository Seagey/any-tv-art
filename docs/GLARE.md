# Glare

## What software cannot fix

**A glossy screen mirroring a window or a lamp.** If you can see the window in the screen, the
picture on the screen cannot hide it. Software can change what is drawn on the panel. It cannot change
what bounces off the glass. That is placement:

- Move or shade the thing that reflects: a curtain, a blind, a lamp shade, a different lamp.
- Tilt the mount a little, if it is on a bracket that tilts.
- Choose a TV with a matte screen. Some Art Mode models have one (V, Samsung).
- A matte film on the screen: it cuts reflections but costs brightness and sharpness, it is fiddly
  above 65 inch, and prices we found were US$106 to $177 for 65 inch (no Australian price found). We
  do not recommend it.

The rest of this page is about how much glare shows, which software can reduce.

## Day

Reflections show most over **dark** areas of a picture, because there is little light from the screen
to compete with the reflection. So, by day:

- A **lighter mat** helps. The mat is never pure white (it glows and never reads as paper); the
  default is off-white `#ece6da`.
- **Very dark photos** are the ones that fight glare worst. If your room is bright, choose lighter
  photos.
- The picture **follows daylight** so it keeps up with the room. On a sunny day it is brighter, on a
  dull day it eases down (never below 35% of full).
- You can move the label with `label.side` so it is not under a reflection.

This reduces how much glare you see. It does not remove it.

## Night

At night the problem is different: **backlight glow.** On an LCD, black is a dim grey, and in a dark
room the screen glows around the picture like a lit rectangle. So:

- Use a **darker mat** at night, and **no pure white**.
- The picture goes **warmer** and **dimmer** through dusk (the light curve).
- **Then the screen goes off** at the night cut-off (`art.night_off`). This is the real fix.
- On OLED black is off, so glow is much less. The burn-in rules still apply ([POWER.md](POWER.md)).

## What the photo check suggests

The setup agent can look at three phone photos (straight on, from where the glare is worst, at night)
with white paper taped beside the TV, and judge in **categories only**: is the screen's white brighter
or darker than the paper, where reflections fall and whether they cross the label, is an edge marker
cut off, and is the dark patch glowing grey. It says what it cannot tell (exact brightness and colour).
Details: [AGENTS.md](../AGENTS.md), part 4.

What it may suggest, and what each does:

| It sees | It suggests |
|---|---|
| Screen white much brighter than the paper | A dimmer curve (`tvs[].calibration.dim_offset` up), or a lower picture mode in the TV's menu |
| Screen white much darker than the paper | A brighter curve (`dim_offset` down) |
| A reflection crossing the label | `label.side` on the other side, or move the lamp or window |
| An edge marker cut off | The TV's Screen Fit, Just Scan or Original setting, set by you; or `tvs[].safe` to keep the picture inside |
| The dark patch glowing grey | More dimming (`calibration.dim_offset` up; it applies all day, not only at night), or off sooner (`art.night_off` earlier) |

Each change is one at a time, then a new photo. Where there is no tested route to change something,
the agent names the menu and waits for you to press it. It never drives a maker's menu by remote keys.
This method is our own and **has not been tested on a real TV**; phones change exposure and colour, so
colour judgement is left out.
