# Instructions for the AI agent setting this up

You are helping someone turn their TV into a matted picture on the wall. Assume they are not
technical. Your job has eight parts, in this order, and you never skip ahead:

1. **Find the TV** with `anytvart identify`.
2. **Read it** with `anytvart read` or `anytvart check` (read only).
3. **Ask the questions** below, one or two at a time, in plain words. Wait for each answer.
4. **The photo check** (looks at the TV and the room, optional but recommended).
5. **Read the plan back** with `anytvart plan` and wait for a clear yes.
6. **Apply** with `anytvart apply` (Google TV) or `anytvart pair` then `anytvart picture` (Samsung).
7. **Test it with them watching.**
8. **Show them the undo.**

**Status you must repeat to them:** one Google TV has run this repo, and no Samsung yet. Every other
route is "built, not yet tested" ([README](README.md)). Say so before you start. If something fails, stop,
tell them in one or two lines, and offer to fill in the tester form
(`.github/ISSUE_TEMPLATE/tv-report.yml`) with `anytvart report`.

Nothing on the TV changes before step 5 is a yes. Never ask for a password or an account. Never put
a home address anywhere: a suburb or city is enough for the weather. Never change a maker's menu by
sending remote keys (that method is off). One change per photo, always.

## What is allowed before the yes

These change nothing on any TV and install nothing outside this folder:

- Checking versions, and making the private Python folder (`.venv`) inside this one.
- `anytvart identify` (it only knocks on ports and asks a Samsung its model).
- `anytvart preview` (draws on this computer only, sends nothing), `anytvart power`,
  `anytvart plan`, and `anytvart photo-prep` (works on a file on this computer).
- `anytvart read` and `anytvart check` are read only, **but they connect to the TV**. On Google TV,
  the first ADB connection makes the TV show an "Allow USB debugging" prompt. On a Samsung with no
  saved token, connecting can make the TV ask Allow. So ask first: "I need to look at your TV's
  settings. It will pop up a question on the screen, and you press Allow. It changes nothing. OK?"
  Wait for the yes.

Say what you are doing in plain words, for example: "I am setting up a small private Python folder
inside any-tv-art to look for your TV. It changes nothing on the TV."

## 0. Before you start (quietly)

1. `python3 --version` must be **3.10 or newer**. If it is missing or older, ask before installing:
   macOS `brew install python@3.12`; Debian and Ubuntu `sudo apt install python3 python3-venv`.
   On a Mac, the first `python3` or `git` may offer "install the command line developer tools":
   they press Install and wait. Normal.
2. Make the private folder:

   ```sh
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .
   ```

   If `pillow-heif` will not install, remove that line from `requirements.txt` and run it again. It
   only adds iPhone `.heic` photos.
3. Chrome or Chromium is needed to draw the picture on the computer (`/Applications/Google
   Chrome.app` on a Mac, or `which chromium google-chrome` on Linux). Note it for the plan if missing.
4. **Always-on computer?** Ask: "Will this computer stay on and at home, on the same Wi-Fi as the
   TV?" Yes means bridge mode. No means no-computer mode (Google TV only does the full job; Samsung
   gets no daily picture). Say the difference plainly, from the [README](README.md).
5. **Google TV only:** you need `adb`. Check `which adb`. If missing, see
   [docs/GOOGLE-TV.md](docs/GOOGLE-TV.md), "Before you start".
6. **Mac: Local Network permission.** macOS asks once per program before it may reach devices at
   home. They choose Allow. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 1. Find the TV

```sh
.venv/bin/anytvart identify
```

Add an address to check one TV (`anytvart identify 192.0.2.20`), or `--scan` if nothing is found. It
prints the family and the route. Read it back by family and year ("a Samsung from 2021 with Art
Mode"), and ask "Is that the one?"

Then decide by family:

- **`android`** (Google TV or Android TV): continue. Use [docs/GOOGLE-TV.md](docs/GOOGLE-TV.md).
- **`samsung-art`**: continue. Use [docs/SAMSUNG-FRAME.md](docs/SAMSUNG-FRAME.md).
- **Anything else** (`lg`, `roku`, `samsung` without Art Mode, `airplay`, `cast-only`, `unknown`):
  this is outside phase 1. Open [docs/OTHER-TVS.md](docs/OTHER-TVS.md), give them the honest route
  for their family with its label, say kindly that it is not built yet, and **stop**. Do not
  suggest workarounds that are not written there.

Ask them to give the TV a fixed address in their router ("DHCP reservation").

## 2. Read the TV

Write a first `config.json` from `config.example.json` with just the TV in it (a name, `kind`,
`ip`, `size_inch`, and for a TV you know is OLED, `"panel": "oled"`). Ask the screen size in inches
and whether it is OLED or LCD. Do not guess the panel from the brand. Then, after the yes above:

```sh
.venv/bin/anytvart read --tv "Lounge"     # Google TV: model, screen, the settings that matter
.venv/bin/anytvart check --tv "Hall"      # Samsung: Art Mode, API version, brightness, what is showing
```

Report what you found in plain words, and what you could not read. For Google TV, three things
decide what works, so find each and say it back:

- **Energy mode (Android 14 and newer).** Low, Optimised or Increased. Low cuts the network in
  standby, so the bridge cannot wake it. The mode is not read for you: ask them to read it off
  the menu (Settings, Device Preferences or System, Power and energy; the path varies). What each
  feature needs: morning wake, night sleep from the bridge, and wake-back **need the network up in
  standby (Optimised or Increased)**. Art after idle, and no-computer mode, **work in any mode**.
  Increased costs standby power (how much is not known).
- **The TV's own inactivity auto-off.** It ends the art mid-day, because art gets no key presses.
  Set it to the **longest value the TV offers, never Never** when there is a bridge (a stopped
  bridge must still end the day; the bridge's night cut-off does the real work). With no computer,
  set it to how long they want art after the last button press (default 2 hours). `anytvart apply`
  writes its own backstop value (see [docs/GOOGLE-TV.md](docs/GOOGLE-TV.md)); if the TV's menu has a
  longer one, ask them to set it by hand.
- **App resolution.** `read` shows the screen size the TV reports. Many Android TVs draw apps at
  1080p whatever the panel. Do not tell anyone they will see 4K.

## 3. The questions

Each answer goes into `config.json` (every key: [docs/CONFIG.md](docs/CONFIG.md)). One or two at a
time.

1. **Photos.** "Which folder of photos?" (`photos.folder`). Landscape looks best. Day, rotate,
   random or one fixed photo (`photos.pick`). Date photos: a name starting `12-25` shows on that day
   each year. Faces cut off in a preview: `photos.focus`.
2. **The look.** Mat colour (off-white default; pure white is refused), mat width, bevel and light
   direction, paper grain on or off, flattening strength, label left or right. Show them
   `anytvart preview --tv "Lounge"` and open the file with them. Adjust until they like it. A TV can
   have its own `look` that overrides the shared one.
3. **What to show.** Date (day first or month first), weather (a suburb or city, never a street;
   `place.name`), calendar (a calendar link is like a key: it stays in `config.json`; they can hide
   words with `calendar.hide`), reminders on set days, a quote. In no-computer mode on Google TV,
   calendar and reminders are not shown yet: say so.
4. **When.** Art hours for each TV, **after you have run `anytvart power`** (below). Night cut-off
   (`art.night_off`, default 22:00) and morning on (`art.morning_on`, default 07:00). New picture
   hour on a Samsung (`art.picture_hour`, default 5).
5. **A fixed address** for the TV, and the bridge address if there is a computer
   (`bridge.url`, for example `http://192.0.2.5:5430`, with this computer's own address).

### Power: say the dollars before they pick art hours

Run `anytvart power` and **read the dollars out loud** before they choose. On a big LCD, hours are
the saving, because dimming the picture does not dim the backlight. A 98 inch LCD all day is about
$526 a year at 40 c a kWh. **Idle only is the lowest-power option** and the default. Offer the
choices with their cost beside each: `idle`, `home`, `day`, or a range like `16:00-21:00`. Ask for
their electricity price (`price_kwh`). If they have a plug-in energy meter, put the reading in
`watts_art` ([docs/POWER.md](docs/POWER.md)). Do not recommend art on a big LCD all day.

## 4. The photo check (optional, recommended)

This looks at the TV and the room, so it can suggest settings. It is **our own method**: phones
change exposure and colour, so it judges in **categories only and never invents numbers**.

**Before the first photo, say this out loud, in your own words but all of it:**

> "This photo shows the inside of your house. It goes from your phone to your own AI provider (for
> example Anthropic or OpenAI, whoever runs me), under the terms of your account there. It does not
> go to the people who made this tool, to GitHub, or into this folder. Phone photos also carry where
> they were taken and the camera's details, so I will strip those first. No camera is ever used for
> anything else. Is that OK?"

Wait for a yes. Then:

- If the photo is on this computer: `anytvart photo-prep PHOTO` (add `--crop left,top,right,bottom`
  as fractions to keep only the TV and the paper). It strips location and camera data, shrinks it, and
  saves it in the git-ignored `data/checks`. It must say `location data left: none`. If it says YES,
  do not send it. Delete the prepared file when the check is done unless they want to keep it.
- If the photo goes straight from their phone into a chat app: first ask them to switch off
  location for the camera, or crop the photo, before they send it.

**The method (BUILD.md, "An AI should see the TV"):**

1. Tape a sheet of plain white paper on the wall beside the TV.
2. Put the calibration card on the screen. With a bridge: `anytvart card on --tv "Lounge"` then
   `anytvart show --tv "Lounge"`. The card is a mid-grey field, a patch at the mat's white, a dark
   patch and markers on every edge and corner. (`anytvart preview --card` draws it on this computer.
   Showing it on a TV needs the bridge.) Turn it off after: `anytvart card off --tv "Lounge"`.
3. Three phone photos from the sofa: **straight on**, **from where the glare is worst**, and **at
   night with the room as it is**.
4. Judge, in categories only:
   - is the screen's white **brighter or darker than the paper** in the same photo;
   - **where reflections fall**, and whether they cross the label;
   - **is an edge marker cut off** (overscan; the fix is the TV's Screen Fit, Just Scan or
     Original, which they set by hand);
   - **is the dark patch glowing grey** (LCD backlight glow: go darker at night, or off sooner).
5. **Say what you cannot tell:** exact brightness, exact colour, and anything the phone's auto
   exposure or multi-frame HDR changed. Put that in the report. **Leave colour judgement out**
   (warmer or cooler than the paper): a lit screen and paper respond differently to a phone sensor
   and this has not been shown to be reliable.
6. **One change per photo.** Change one thing, take one photo, judge. The only changes you make
   yourself are ones with a tested route: the look settings in `config.json` (`look`, `calibration`),
   and on a Samsung, art brightness through the bridge. Where there is no route, name the menu and
   the setting, and wait while they press it. **Never drive a maker's menu by remote keys.**
7. The match you settle on (this room, this time, this setting looked like the paper) becomes the
   calibration (`tvs[].calibration`, see [docs/CONFIG.md](docs/CONFIG.md)). Expect 5 to 7 photos, once
   per room.

## 5. Suggestions report

Give them a ranked list. Each line says what it fixes, what it costs, and a label:
**T** tested by us, **V** from the maker's own page, **R** reported by owners, **G** a guess. Most
will be R or G, and say so. Candidates, in the order that fits their TV:

1. The lowest-power art option for this TV (idle only, or a TV made for art), with the dollars.
2. The TV's own light sensor, if it has one.
3. The inactivity timer and the energy mode values.
4. Ethernet for a reliable wake (untested by us).
5. Moving or shading a lamp or window that reflects, or tilting the mount.
6. A light sensor for the room (untested by us).
7. A matte film, with its downsides: brightness and sharpness lost, fiddly above 65 inch.
8. On OLED, the maker's own mode first, and the burn-in rules ([docs/GLARE.md](docs/GLARE.md)).

## 6. Read the plan back and get a yes

```sh
.venv/bin/anytvart plan --tv "Lounge" --mode bridge     # or --mode alone
```

On a Samsung with Art Mode, `plan` says there is nothing to install and names `pair` then `picture`.
Read the plan back in one short list, in plain words: the TV, the look, what it shows (and the place,
never more than a suburb), which calendars (by name, not the link), the photo folder, the art hours
with the yearly dollars, the night cut-off, whether a computer must stay on, and **exactly what
changes**:

- Google TV: the art app is installed; the screensaver is set to our art after 10 minutes with no
  button presses; the TV's own switch-off is set. Every old value is written down first.
- Samsung: the TV asks Allow once for "any-tv-art". One picture a day goes to My Photos and is shown
  in Art Mode. Only pictures this tool uploaded are ever deleted.
- It never presses a power key on a Samsung and never takes it out of Art Mode.

Show them the undo before you start (below). Ask: "Ready for me to set it up? You can undo all of
it." **Wait for a clear yes.**

## 7. Apply, then test with them watching

Google TV:

```sh
.venv/bin/anytvart apply --tv "Lounge" --mode bridge     # or --mode alone
.venv/bin/anytvart bridge                                  # bridge mode only; keeps running
```

`apply` prints the plan and asks for "yes" itself. It needs `dist/any-tv-art.apk` (build it with
`sh scripts/build-apk.sh`, or download it from Releases when one exists; say plainly if there is no
release yet). `anytvart bridge` runs in the foreground. To keep it running after a restart, run
`sh scripts/service.sh install` (built, not yet tested: check `sh scripts/service.sh status` after a restart).

Samsung:

```sh
.venv/bin/anytvart pair --tv "Hall"        # they press Allow on the TV within about 30 seconds
.venv/bin/anytvart picture --tv "Hall"     # makes and shows today's picture now
.venv/bin/anytvart bridge                  # the daily picture and the art brightness
```

Test with them watching:

1. `anytvart show --tv "Lounge"` opens the art now. Ask if it looks right. Any remote button returns
   to TV.
2. Leave the remote alone for 10 minutes: the art should appear. Any button should bring TV back.
3. Check the reading on the TV: `anytvart read --tv "Lounge"` shows `app` with the last refresh and
   any error.
4. Samsung: confirm it is still in Art Mode (`anytvart check`) and that their own pictures are intact.

If the art does not appear, check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), do not retry in
a loop, and offer the tester report.

## 8. Show them the undo

```sh
.venv/bin/anytvart undo --tv "Lounge"          # add --keep-app to keep the app installed
```

Say what it does: Android settings go back to the values written down first, and the app and its
photos are removed; on a Samsung, their picture is put back, then only this tool's uploads are
deleted. Running it twice is harmless. If they say "take it off", go straight to this.

## Rules while you work

- `config.json` and `data/` hold TV addresses, the place, calendar links and TV tokens. Git ignores
  them. Never commit them, never print a token or a calendar link, never paste them into an issue.
- Only delete pictures through the tool. Never use the TV's own delete for anything, and never "tidy"
  My Photos by hand.
- Never switch an app off on their TV. This tool changes only the settings listed in
  [docs/GOOGLE-TV.md](docs/GOOGLE-TV.md).
- If the TV is being used (something playing, a person watching), do not run a test on it.
- **Never put a home address, a name or a real model number into a file in this repo.** Use
  `192.0.2.x` for examples.
- A tester report: `anytvart report --tv "Lounge"`, read it through with them, delete anything
  personal, then paste it into the tester form.
- Outside phase 1, give the honest route from [docs/OTHER-TVS.md](docs/OTHER-TVS.md) and stop.
