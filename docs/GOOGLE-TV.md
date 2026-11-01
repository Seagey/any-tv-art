# Google TV and Android TV

**Status: built, not yet tested on a real TV.** Every step marked "not yet run on a real TV" below
has been written and unit-tested against a pretend TV, nothing more. Labels: **T** tested by us,
**V** from a maker's or Google's own page, **R** reported by others, **G** a guess.

Our screensaver app (`app.anytvart`) shows the matted picture. It is the TV's own screensaver, so
after the TV has sat idle for 10 minutes the art appears, and any remote button brings TV back.

## Before you start

You need a way to talk to the TV over your Wi-Fi: **ADB**. Most Google TVs have no menu for picking a
third-party screensaver, so ADB is the only way in (V, AerialViews README). You do this once.

1. **Install `adb`.** It is part of Google's "platform-tools" (search for "Android platform-tools").
   On a Mac with Homebrew: `brew install --cask android-platform-tools`. Check with `adb version`. The tool
   looks for `adb` on your path, in `~/Library/Android/sdk/platform-tools/adb`, or at the path in
   config `adb` (or the `ANYTVART_ADB` environment variable).
2. **Turn on Developer options on the TV.** Google TV: Settings, System, About, then press the
   **Android TV OS build** (or Build) entry seven times. Android TV 9 to 11: Settings, Device
   Preferences, About, press Build seven times. Menu names move between years and makers (V, couch-tv
   notes).
3. **Turn on network debugging.** Settings, System, Developer options, **USB debugging**, then
   **Network debugging** (or **Wireless debugging** on some). Some Android 11 and newer TVs only have
   Wireless debugging with a pairing code and a random port. This tool uses the fixed port 5555, so
   those TVs need the pairing steps first (`adb pair`, then `adb connect`, then `adb tcpip 5555`), and
   on some TVs port 5555 closes again after a restart (R). Not yet run on a real TV.
4. **Find the TV's address:** Settings, Network, then the connected network. Give it a fixed address in
   your router ("DHCP reservation").
5. **The Allow prompt.** The first time `anytvart read` connects, the TV shows "Allow USB debugging?".
   Choose **Always allow**. If you miss it, the tool says "the TV has not allowed this computer yet"
   and you run it again.

Then, from this folder:

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .
cp config.example.json config.json         # then add your TV under "tvs"
.venv/bin/anytvart identify
.venv/bin/anytvart read --tv "Lounge"
```

On a Mac, the first time it reaches the TV, macOS asks to let the program find devices on your local
network. Choose Allow (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

## With a computer, or without

| | With the bridge (an always-on computer) | Without |
|---|---|---|
| Who makes the picture | The computer: `anytvart bridge` serves the photo, the date, the weather, the calendar, the reminders and the brightness curve. The TV app draws it. | The TV app, on its own: photo, date, weather and a quote. Photos are copied onto the TV once at setup. |
| Calendar and reminders | Yes | **Not in phase 1** |
| Morning wake | Yes, for art hours other than `idle` | **No.** The app sleeps with the TV (T on a 98 inch Google TV) |
| Night cut-off | The bridge puts the TV to sleep, skipped while something is playing, retried every 10 minutes | **None.** The TV's own inactivity timer ends the art |
| Brightness | The bridge's curve (sunrise, sunset, measured sunlight) | The app works out the sun from your place |
| Apply | `anytvart apply --tv NAME --mode bridge` (needs `bridge.url`) | `anytvart apply --tv NAME --mode alone` |

**No computer is also the lowest-power way**, because art only runs after someone has used the TV
and left it, and the TV's own timer ends it. The inactivity timer in this mode is set to how long you
want art after the last press (2 hours by default).

## The daily cycle

What happens from morning to night on this family:

- **Morning on.** With art hours other than `idle`, at the start of the window the bridge wakes the
  TV and opens the art directly (`am start -n app.anytvart/.ArtActivity`). It wakes the TV by sending
  POWER over ADB (the same remote key as the power button). In an earlier test of ours on a 98 inch
  Google TV with Android 14, "off, wait 10 s, on: on in 0.5 s (POWER works in standby; WAKEUP did not)"
  (T, before this repo; not a test of this tool). Waking after the TV has left the network (about 51
  seconds in that test) needs Wake-on-LAN. The bridge sends it when the TV has a `mac` in config.json and art is due (built, not yet
  tested on a TV of ours; in that earlier test Wake-on-LAN did not wake the TV from standby). So a TV that has
  been off for a while may not wake. Not yet run on a real TV.
- **Day.** You watch as normal. After the last button press, the TV's idle timeout (10 minutes) starts
  our art. Any button returns to TV (V, Android docs).
- **Night cut-off.** From `art.night_off` to `art.morning_on` (22:00 to 07:00 by default, our own
  default, not Google's), the bridge sleeps the TV if it is awake, showing our art, and nothing is
  playing.
- **The TV's own auto-off.** Google TV's inactivity auto-off would end the art mid-day, because art
  gets no button presses. `anytvart apply` writes `attentive_timeout` as a backstop: **4 hours with a
  bridge, 2 hours without** (the plan is to use the longest value the TV offers, never Never; the
  tool does not read that value from each TV yet, so a TV that offers longer needs it set by hand).
  Whether a given TV honours that key is a guess (G).

## Power button behaviour

- A short press **sleeps** the TV. It does not start the screensaver.
- **Apps never see the power key** (R, Android platform forum). Our app cannot catch it, and it cannot
  wake the TV, because it is suspended with the TV. `KEYCODE_WAKEUP` did not wake the 98 inch Google
  TV from standby (T). That idea is recorded as known failed.
- So the bridge, not the TV, does the waking, by POWER over the remote protocol while the TV is still
  in network standby.
- **Wake back to art** (the bridge sees you turn it off and wakes it back to art) is **not built**.
  The config key `wake_back` exists and nothing reads it. It would turn "off" into about 300 W of art
  on a 98 inch LCD, about $44 a year for every hour a day.

## Android 14 energy modes

Android 14 for TV has **Low, Optimised and Increased** energy modes (R). Low cuts the network in
standby, so no bridge wake. Optimised keeps some Wi-Fi functions. Increased keeps the most and costs
standby power.

| Feature | Needs the network up in standby? |
|---|---|
| Morning wake, night sleep from the bridge | Yes: Optimised or Increased |
| Art after idle (the screensaver) | No: any mode |
| No-computer mode | No: any mode |

The mode is read off the TV's menu (Settings, Device Preferences or System, Power and energy; the path
varies). `anytvart read` lists any setting with "energy", "power" or "standby" in its name, which
helps, but it does not decode the mode for you.

## Resolution

**No 4K claim on Android.** Many Android TVs draw apps at 1920x1080 and scale up, whatever the panel
is (R). One of ours draws at 1280x720 (T). The print look is tuned per app resolution, in millimetres
on the real screen, which is why `size_inch` and `app_px` are in the config. On a 98 inch screen at
1080p one pixel is about 1.1 mm, so paper grain is soft or off there. A test drawing a full 4K image
to see whether the panel shows more detail has not been run.

## What the app does, and the files it writes

The app has two doors into one picture: **`ArtDream`** (the screensaver; any key ends it) and
**`ArtActivity`** (full screen; the bridge opens it; any key closes it). The only permission is
INTERNET. The page can only load from its own origin. No analytics, no crash reporting, no accounts.

Files, all in `/sdcard/Android/data/app.anytvart/files/`:

- `config.json`: written by `apply`, read each time the app starts. Keys are in
  `tv/android/README.md`.
- `cache/art.json`, `cache/photo-*` (bridge mode): the last picture, kept so it still shows when the
  bridge cannot be reached.
- `cache/weather-<date>-<unit>.json` (no-computer mode): the day's weather.
- `photos/` (no-computer mode): the copied photos.
- `status.json`: `{mode, last_refresh, last_error, photo, bridge_ok}`, which `anytvart read` shows.

Settings `apply` changes, and nothing else (the tool refuses any other):
`secure/screensaver_components`, `secure/screensaver_enabled`, `system/screen_off_timeout` (10
minutes), `secure/attentive_timeout`. The code also allows `secure/screensaver_activate_on_sleep`,
`secure/screensaver_activate_on_dock` and `secure/sleep_timeout`, but `apply` does not write them.
Every old value is saved to `data/changes-<tv>.json` before it changes.

The app is installed from `dist/any-tv-art.apk`. Build it with `sh scripts/build-apk.sh` (needs JDK 21
and Android SDK platform 34). There is no download on a Releases page yet. Google is rolling out
developer verification for sideloaded apps; Google's FAQ says ADB installs are exempt (V). We install
over ADB, and we are watching it.

## Undo

```sh
.venv/bin/anytvart undo --tv "Lounge"
```

Puts every recorded setting back (deleting a setting the TV never had), then removes the app and its
photos. `--keep-app` leaves the app installed. A factory reset also puts the screensaver back. Not
yet run on a real TV.

## Known issues

- Not yet run on a real TV.
- Whether routine TV updates reset the screensaver setting is not known (G).
- On Android TV 12 and newer the screensaver may not start below a 6 minute idle time (R, one
  project's claim).
- Wi-Fi has dropped on some TVs when apps were switched off. This tool switches off no app.
- Wake-on-LAN is built but not tested; wake-back is not built. See above.
- To keep the bridge running after a restart: `sh scripts/service.sh install` (built, not yet tested).
- The calibration card on the TV is served by the bridge. In no-computer mode there is no way to put
  it on screen yet.
- Photos in no-computer mode are copied at about 2 MB each, up to 60, and the tool refuses if the TV
  would be left with less than 500 MB free.
