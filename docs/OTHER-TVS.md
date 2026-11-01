# Other TVs: the honest route for each

Only Google TV / Android TV and Samsung TVs with Art Mode are built (phase 1), and **even those have
not been run on a real TV yet**. Everything on this page is research, labelled so you can judge it:
**T** tested by us, **V** from the maker's own page or an official doc, **R** reported by owners or
open-source projects (usually right, sometimes stale), **G** a guess. A family only moves to "works"
after someone outside our house reports it through [the tester form](../.github/ISSUE_TEMPLATE/tv-report.yml).

Status words: **built, not tested** means the code exists. **not built** means a route exists but we
have not written it (phase 2 or 3: **not built yet**). **not possible** means we found no way in.

| Family | Best route | Needs a computer? | Status | Why |
|---|---|---|---|---|
| LG, 2022 and newer (Always Ready) | LG's own Always Ready: press off and it shows Clock, Art, Movement, Moment (your photos) or Sound Palette (V) | No | Not built (phase 2) | Our picture could reach Moment through Google Photos, ThinQ or USB (G on 2022 sets). LG OLEDs dim still pictures by themselves (V), so Always Ready first |
| LG app route (before 2022, or by choice) | Our app via LG Developer Mode, opened by a computer each time the TV comes on (R) | Yes | Not built (phase 2) | Developer Mode lapses without a computer. Changes the picture preset (R). Poor fit on OLED |
| Sony Bravia (Google TV) | The Google TV route, plus Sony's REST API for brightness and the light sensor (V) | Optional | Google TV part: built, not tested. REST part: not built (phase 2) | Needs a pre-shared key set on the TV. Sony's own "Turn off TV after" is on by default (V) |
| Sony Linux Bravias (some cheaper Full HD) | None | n/a | Not possible | No app route found. Use an HDMI box |
| Hisense VIDAA (including CanvasTV) | CanvasTV has its own Art Mode and sensors (V). Add pictures by hand in Hisense's phone app. Other VIDAA: an HDMI box | No | Not possible to automate | No official IP control (R). Newer firmware is encrypted. Not built, and not planned |
| Amazon Fire TV (Fire OS) | Our screensaver, with extra ADB keys on Fire OS 7.6 (R) | Yes | Not built (phase 2) | Conflicting reports on Fire OS 8.1 and newer (R). Amazon does not support third-party screensavers. ADB drops about 15 minutes after sleep (R), so no morning wake |
| Fire TV with Vega OS (2025 and newer) | None | n/a | Not possible | No Android apps and no consumer sideloading (R) |
| Roku | The maker's Backdrops with your own photos, by hand (V, snippet) | No | Not possible to automate | Roku's remote API has PowerOff but **no PowerOn** (V). Keys need "Control by mobile apps" on. A screensaver channel needs a published channel |
| Apple TV | Apple's Photos screensaver from a shared album (V) | No | Not built (phase 3) | A third-party app cannot be the screensaver (G). Idle only |
| Samsung without Art Mode | Our Tizen app via Developer Mode, opened by a computer each time the TV comes on (T on one Samsung for a sibling project) | Yes | Not built (phase 3), not recommended | Full TV power the whole time, and Auto Power Off after 4 hours (V) ends it |
| Any TV with an HDMI box (Google TV Streamer, Onn, Chromecast with Google TV, or a Raspberry Pi) | The box runs the Google TV route on its own input, with its own picture settings for that input | Optional | Not built yet (phase 2) | The box adds its own power, and CEC wake is unreliable on some TVs (R) |

## Per family

### LG
**Best route: Always Ready.** On 2022 and newer models (model dependent), pressing off starts a
standby screen with Clock, Art, Movement, Moment or Sound Palette. Settings: All Settings, General,
Always Ready (V, LG). To leave it: Home or Previous with the screen on, or Power (V, LG AE page).
LG warns energy use may increase, and one owner measured about 12 W on a C2 (R). Off at the wall it
does not run. Getting our own picture into Moment is a guess (G). **The app route** (LG Developer Mode
sessions run to 1000 hours and can be extended, R) is a poor fit on OLED, because LG OLEDs dim still
pictures by themselves and restore them when the image changes (V). Changing the backlight over the
network changes the current picture preset, so a driver must put it back on every exit from art (R,
bscpylgtv). Gallery and Gallery+ (2025 and newer) add a Google Photos source and a paid tier (V).
All of this is **not built yet**.

### Sony
Sony Google TV models use the Google TV route. Sony's REST API can set `brightness` and the
`lightSensor` with a pre-shared key set on the TV, and `getPictureQualitySettings` lists what a model
allows (V, Sony docs). Light Sensor lives under System Settings, Eco (V; the path varies by year).
Holding power shows a restart or power-off prompt (V). The REST part is **not built yet**.

### Hisense VIDAA and CanvasTV
In Australia, CanvasTV runs VIDAA with its own Art Mode, a Hi-Matte screen, a motion sensor (2 to 4 m,
in Art Mode only), an ambient light sensor and your own photos through the VIDAA phone app (V,
Hisense AU). There is no official network control; community work uses MQTT on port 36669 and newer
firmware encrypts it with PIN pairing (R). **Hisense CanvasTV by hand** (adding a picture each day in
the phone app) is the honest route. Hisense Google TV models are on the Google TV route.

### Fire TV
Fire OS 7.6 needs extra keys (`screensaver_default_component`, `contextual_screen_off_timeout`,
`screensaver_enabled`) and Fire OS 8.1 needs `amazon_ambient_enabled 0` and a reboot; another source
says it no longer works on 8.1 (R, AerialViews, conflicting). ADB comes from My Fire TV, About, then
Developer options. **Not built yet.** Vega OS has no way in at all (R).

### Roku
The remote API (ECP, port 8060) gives the model and power mode without pairing (V). Keypress calls
need Settings, System, Advanced system settings, Control by mobile apps (V, Roku OS 14.1 and newer).
`PowerOff` exists on Roku TVs and `PowerOn` does not (V). Fast TV Start keeps the network up at more
power (V). Photo Streams ended in January 2026 for Backdrops (V). No picture settings over ECP (G).
Roku is **not possible to automate** here.

### Apple TV
A Photos screensaver from your own or a shared album (V, Apple). The box wakes the TV over CEC (V). A
third-party app as the screensaver: no source either way (G). **Not built yet.** The album route needs
a test of how often it refreshes.

### Samsung without Art Mode
Samsung's Ambient Mode shows Samsung's content or a photo of your wall, and we found no way to push
our own picture (G). Our Tizen app via Developer Mode is possible (T on one Samsung for a sibling
project, about 6 to 7 seconds to open), but the TV is fully on the whole time. **Not recommended and
not built.** Auto Power Off (4 hours, V) must be off.

### HDMI box
A Google TV box (a Google TV Streamer is about AU$129 to $159, R) or a Raspberry Pi gives any TV with
HDMI the Google TV route on its own input. With a Pi, `cec-client` can send `on 0` and `as` to wake the
TV and take the input, and `standby 0` to sleep it (V, community guides). Some TVs ignore CEC (R). The
box is about 7.5 W in use for a Streamer and 3.6 W for a Pi 5 (R, retailers), on top of the TV. TVs
often count only remote presses for their inactivity timers (G), so lengthen them. **Not built yet.**

## Light sensors on the TV itself

| Maker | Setting | Label |
|---|---|---|
| Samsung | Ambient Light Detection (Eco Solution), Brightness Sensor in Art Mode | V (paths conflict between years) |
| Sony | Light Sensor | V |
| Hisense CanvasTV | Total Ambient Adaptive | V |
| LG | Energy Saving Step "Auto" | V |
| Others | read the menu | G |
