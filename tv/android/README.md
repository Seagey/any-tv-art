# Any TV Art, Android TV app

Status: **not yet run on a real TV.** It builds, the unit tests pass and the APK is signed, nothing more.

The app (package `app.anytvart`) shows the matted picture on an Android TV or Google TV. It has two
ways in, both hosting the same view (a WebView showing `picture/template/print.html`):

- **`ArtDream`**, the screensaver. It starts after the TV's idle timeout. Not interactive, so any key press ends it.
- **`ArtActivity`**, the same picture as a full screen. The bridge opens it with
  `am start -n app.anytvart/.ArtActivity`, and it has a launcher entry (with a banner) so it can be opened by hand. Any key press closes it.

The template is copied into the APK at build time (`assets/art/print.html`, fonts in `assets/art/fonts/`),
so it has one home in the repo. It loads through `WebViewAssetLoader` at
`https://appassets.androidplatform.net/`, with `/assets/` for the APK and `/files/` for the app's files folder.
Nothing else is allowed to load in the page.

## The two modes

**Bridge mode** (`"mode": "bridge"`): gets `{bridge_url}/art.json` every 30 minutes, downloads the photo into
`files/cache/`, and keeps both, so the last picture shows when the bridge cannot be reached. Every 5 minutes it
gets `{bridge_url}/light.json` (`{dim, warm, art}`) and calls `setLight`. When `art` is false (the night cut-off)
a black cover hides the picture.

**Alone mode** (`"mode": "alone"`, no computer): setup pushes photos into `files/photos/`. One is chosen per day
(names sorted, day of year modulo count). The date text, the day's weather (Open-Meteo, cached for the day), and
a quote from `quote_lines` are built on the TV. Light follows the sun: none by day, easing to 0.6 over the two hours
after sunset, easing out for the hour after sunrise, sunrise and sunset worked out on the TV from the place's
latitude and longitude. No night cut-off here: the TV's own timer ends it.

With no config file, or one that is not valid JSON, it shows the bundled sample picture with "Not set up yet".

If `oled` is true the picture drifts by up to 6 px, a new offset each hour, always the same for the same hour.

## config.json

Path on the TV: `/sdcard/Android/data/app.anytvart/files/config.json`, read each time the dream or activity starts.

| Key | Meaning |
|---|---|
| `mode` | `"bridge"` or `"alone"` (default `"alone"`) |
| `bridge_url` | e.g. `http://192.0.2.5:5430` |
| `place` | `{name, latitude, longitude}` (weather and sun times) |
| `timezone` | e.g. `Australia/Sydney` (default: the TV's) |
| `look`, `screen`, `safe` | passed through to the template untouched |
| `quote_lines` | array of strings, one per day |
| `date_order` | `"day-month"` or `"month-day"` |
| `units` | `"celsius"` or `"fahrenheit"` |
| `oled` | true or false |

## Files the app writes (all in `/sdcard/Android/data/app.anytvart/files/`)

- `cache/art.json`, `cache/photo-*` (bridge mode), `cache/weather-<date>-<unit>.json` (alone mode)
- `status.json`: `{mode, last_refresh, last_error, photo, bridge_ok}`, rewritten each cycle. Setup reads it with `adb shell cat`.

## How setup installs it

Setup reads the old values first and records them. Then, with the user's yes:

```
adb install -r dist/any-tv-art.apk
adb push config.json /sdcard/Android/data/app.anytvart/files/config.json
adb push photos/. /sdcard/Android/data/app.anytvart/files/photos/      # alone mode only
adb shell settings put secure screensaver_components app.anytvart/.ArtDream
adb shell settings put secure screensaver_enabled 1
```

(If the app's files folder does not exist yet, open the app once: `adb shell am start -n app.anytvart/.ArtActivity`.)

## Undo

Put back the `screensaver_components` and `screensaver_enabled` values setup recorded
(`adb shell settings put secure ...`, or `settings delete secure screensaver_components` if there was none), then
`adb uninstall app.anytvart`.

## Build and test

```
sh scripts/build-apk.sh                      # from the repo root, writes dist/any-tv-art.apk
cd tv/android && ./gradlew test              # JVM unit tests
```

Needs JDK 21 and the Android SDK (platform 34, build tools 34). Release builds are signed with the standard
debug key, or with the keystore named in `ANYTVART_KEYSTORE`, so one build can update the last.

## What it does not do

No analytics, no crash reporting, no accounts. The only network traffic is the bridge URL and Open-Meteo.
The only permission is INTERNET. Cleartext http is allowed app-wide (the bridge is on the LAN and its address is
only known at setup), but the page itself can only load from its own https origin.
