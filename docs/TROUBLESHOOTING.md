# Troubleshooting

Nothing in this repo has been run on a real TV yet, so some rows below come from problems we hit
building other TV tools, not from this one. They are marked **seen before** when so. First, always:

```sh
.venv/bin/anytvart read --tv "Lounge"      # Google TV: reachable? what does the app say?
.venv/bin/anytvart check --tv "Hall"       # Samsung: answering? in Art Mode?
```

If you are stuck, `anytvart report --tv NAME` makes a version of the state with addresses and names
removed, for [the tester form](../.github/ISSUE_TEMPLATE/tv-report.yml).

## Google TV and Android TV

| Symptom | Why | Fix |
|---|---|---|
| `could not reach 192.0.2.20:5555 over ADB` | Network debugging is off, the TV is asleep, or the address changed. The port 5555 closes again after a restart on some TVs (R) | Turn on **Network debugging** (Settings, System, Developer options). Wake the TV. Check the address. [GOOGLE-TV.md](GOOGLE-TV.md), "Before you start" |
| `the TV has not allowed this computer yet: choose Allow (and Always allow) on the TV` | adb shows "unauthorized": the "Allow USB debugging?" box on the TV was missed or refused | Run the command again and choose **Always allow** while looking at the TV. If the box never appears, turn Developer options off and on, or on the TV's Developer options choose "Revoke USB debugging authorisations", then reconnect |
| Only **Wireless debugging** is offered, with a pairing code and a random port | Many Android 11 and newer TVs offer nothing else (seen before) | `adb pair` with the code, `adb connect`, then `adb tcpip 5555` so the fixed port opens. Not yet run on a real TV |
| `adb was not found` | platform-tools is not installed or not on the path | `brew install --cask android-platform-tools` on a Mac, or set `adb` in `config.json` to its full path |
| **Mac:** works from Terminal, fails as a background service with **"No route to host"** (seen before) | macOS gives the Local Network permission to a program, but not to the separate `adb` helper it starts, so `adb` is blocked even when Python is allowed | Run `anytvart bridge` from the Terminal you have allowed. **This tool's bridge runs the `adb` program, so it can hit this as a service.** The earlier fix was to speak ADB from Python instead; that is not built here. Do not rely on a background service on a Mac until you have checked it works |
| **Mac:** macOS asks "allow to find devices on your local network" | Normal, once per program | Choose **Allow**. If you said no: System Settings, Privacy and Security, **Local Network**, switch the program on |
| The TV's **Wi-Fi dropped** after apps were switched off (seen before) | Switching off Google's setup apps and similar made the Wi-Fi drop on two TVs | This tool switches **no** app off. If it happens anyway after a power-off, re-join the Wi-Fi on the TV, and send us a report |
| `apply` fails: no app at `dist/any-tv-art.apk` | The app has not been built, and there is no Releases download yet | `sh scripts/build-apk.sh` (needs JDK 21 and Android SDK platform 34) |
| Sideloading blocked, or "developer verification" | Google is rolling out developer verification for sideloaded apps (from September 2026 in four countries, worldwide in 2027, R). Google's FAQ says ADB installs are exempt (V) | We install over ADB. If an install is refused, report it. Do not try another install route |
| `the TV did not keep secure/... (it says ...)` | This TV ignores that setting key | Run `anytvart undo`, then report the TV's model and the key. The idle and inactivity keys are not tested on any real TV |
| Art never appears after 10 minutes idle | The TV's screensaver is off or set elsewhere, the TV went to sleep first (its inactivity timer is shorter), or the app has not started once | `anytvart read` and look at `secure/screensaver_components` (should be `app.anytvart/.ArtDream`) and `attentive_timeout`. `anytvart show` opens the art now. Lengthen the TV's own auto-off in its menu |
| Art appears, then the TV switches off mid-day | The TV's inactivity auto-off. Art gets no button presses | Set the TV's own timer to the longest it offers, never Never ([GOOGLE-TV.md](GOOGLE-TV.md)) |
| The TV does not wake in the morning | Energy mode Low (cuts the network in standby), or the TV was off long enough to leave the network. Without a `mac` for the TV the bridge sends POWER only | Set Optimised or Increased, or use Ethernet, and add the TV's `mac` to config.json (Wake-on-LAN, built, not yet tested). Art after idle needs none of this |
| The picture is cut off at the edges (**overscan**) | The TV is zooming the picture slightly | The TV's picture size: Screen Fit, Just Scan or Original (names vary). Or set `tvs[].safe` in percent. The calibration card's edge markers show it |
| Looks soft or low resolution | Many Android TVs draw apps at 1080p or even 720p whatever the panel (R, T on one) | Expected. We make no 4K claim on Android. `app_px` tunes the look |
| The picture is stuck on "Not set up yet" | The app has no valid `config.json`, or it is not valid JSON | `anytvart apply` again. `anytvart read` shows `app.last_error` |
| The app shows an old picture | The bridge could not be reached, so it shows its last cached picture | Check the bridge is running and `bridge.url` is right. The app asks again every 30 minutes |
| Back to normal after a factory reset | A factory reset puts the screensaver back | Run `apply` again |

## Samsung with Art Mode

| Symptom | Why | Fix |
|---|---|---|
| `... is not answering` | The TV is **fully off** (a long power press) so it dropped off the Wi-Fi, or it is on another network (seen before: fully off, it does not answer on its art ports) | Press power once so it is in Art Mode and run again. The bridge waits and tries every minute. Waking a fully off TV over the network did not work on the 2021 model we know (T) |
| `did not accept this computer` | The TV forgot the pairing (factory reset, a long time unplugged, or the device was removed) | `anytvart pair --tv NAME` and press **Allow** on the TV |
| No Allow prompt appears | The TV's Access Notification is Off, or "any-tv-art" was set to Deny | Settings, General, External Device Manager, **Device Connection Manager**: Access Notification to **First Time Only**, check the Device List, then pair again |
| The picture uploaded but the TV keeps showing **another picture** (seen before) | A 2021 model ignored "show this" while in Art Mode, after the picture on screen was once deleted. The picture is on the TV | The tool says "kept another picture for now" and tries again. Or choose it yourself: Art Mode, My Photos. **Never delete the picture on screen**, which is why the tool never does |
| After `undo` the TV shows one of Samsung's own artworks | Undo asks for your previous picture first, but the TV picked its own | Choose your photo with the remote: Art Mode, My Photos |
| No daily picture, but Art Mode works | `anytvart bridge` is not running, or the TV was fully off at the picture hour | Run the bridge. `anytvart picture --tv NAME` sends today's picture now |
| The TV switches itself fully off after some hours | Auto Power Off (Eco Solution) | Settings, General, Eco Solution, Auto Power Off: Off. It cannot be set over the network |
| The screen never goes dark when the room is empty | Motion sensor settings | Art Mode settings: Sleep After 15 or 30 minutes, sensitivity medium |
| Art brightness does not change | The TV is not in Art Mode (the tool only sets it there), or it is more than 15 minutes since the last step (the curve changes it at most every 15 minutes) | Put it in Art Mode and wait. If the TV's own brightness sensor is on, it may fight the curve |
| `check` says there is no Art Mode | A Samsung without Art Mode, or a 2025 and newer set that does not answer the art channel | [OTHER-TVS.md](OTHER-TVS.md), Samsung without Art Mode. Report a 2025 set through the tester form |

## The picture and the computer

| Symptom | Why | Fix |
|---|---|---|
| `render: Chrome did not work` or no Chrome found | Chrome or Chromium is missing | Install Chrome on a Mac, or `sudo apt install chromium` on Linux. Or set `chrome` in `config.json` ([CONFIG.md](CONFIG.md)) |
| `config.json: ... must be ...` | A setting is out of range | Fix the line named. [CONFIG.md](CONFIG.md) lists the allowed values |
| `config.json: pure white glows on a screen` | The mat colour is `#ffffff` | Use `#f1ece3` or any off-white |
| No weather | No internet, or the place was not found | Add `place.country`, or set `place.latitude` and `place.longitude` |
| No calendar | The link does not give back a `.ics` file | Open the link in a browser: it should download a calendar. iCloud calendars must be public |
| The words are hard to read on a dark photo | Dark areas show reflections and the label sits on them | A lighter mat, `label.side`, or a lighter photo ([GLARE.md](GLARE.md)) |
| `anytvart preview` shows a different look from the TV | The TV draws at a different size | Use `--size 1080` or `--size 720` |
| After a reboot the TV showed a blank page before Wi-Fi came up (seen before) | The page asked for data before the network was ready | The app keeps and shows its last picture. Report it if it stays blank |
