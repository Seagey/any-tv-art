# Samsung TVs with Art Mode

**Status: built, not yet tested on a real TV by this repo.** The upload code is a copy of the code in
[smart-frame-tv](https://github.com/Seagey/smart-frame-tv), which has run on a 2021 Samsung with Art
Mode (an upload, select and delete all worked there). This repo's tool around it has not. Labels:
**T** tested by us, **V** from Samsung's own pages, **R** reported by others, **G** a guess.

Art Mode is Samsung's own feature: the TV shows a picture instead of going dark, with a motion sensor
and a brightness sensor, at a fraction of the power of TV mode. This tool puts a fresh matted picture
in it every day. It stays real Art Mode, so the sensors and the low power keep working.

Art Mode shows **still pictures only**. So there is no live clock: it would be wrong a minute later.

## What you need

- A Samsung TV with Art Mode on your Wi-Fi: a 2021 to 2024 model is the best case. 2025 and newer
  models are in the section below.
- **A computer that stays on**, on the same Wi-Fi, to make and send the daily picture. Without one,
  Art Mode keeps working but there is no daily picture (add one by hand with Samsung's phone app).
- Python 3.10 or newer, and Chrome or Chromium on that computer (the picture is drawn there).

## Pairing

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .
cp config.example.json config.json         # add the TV under "tvs" with "kind": "samsung-art"
.venv/bin/anytvart identify                # finds it, says if it has Art Mode and its year
.venv/bin/anytvart check --tv "Hall"       # read only: Art Mode state, brightness, what is showing
.venv/bin/anytvart pair --tv "Hall"        # the TV asks Allow once for "any-tv-art": press Allow
```

You have about 30 to 40 seconds to press Allow. "This TV needs no token" is fine too. Some TVs ask
nothing at all. If it times out, check **Settings, General, External Device Manager, Device
Connection Manager** and set **Access Notification** to **First Time Only**. The **Device List**
there shows "any-tv-art" and lets you remove it. A factory reset, or a long time unplugged, can make
the TV forget the pairing: run `pair` again.

`anytvart check` asks the art channel itself whether the TV has Art Mode, rather than trusting
the support flag in Samsung's own device info, because some 2025 sets report that flag false while having Art Mode
(R). This check has not been run on a TV that does not have Art Mode.

## The daily picture

```sh
.venv/bin/anytvart picture --tv "Hall"     # make and show today's picture now
.venv/bin/anytvart bridge                  # run the daily cycle (needs the computer to stay on)
```

- From `art.picture_hour` (5 am by default) the bridge makes a new 3840x2160 picture once the TV is
  answering, uploads it to **My Photos** (10 to 15 seconds, T on a 2021 model), shows it, and then
  deletes the picture it uploaded the day before. So My Photos holds one of ours plus your own.
- If the TV is fully off at 5 am it drops off the network and misses the picture. The bridge tries
  again every minute until the TV answers.
- The tool remembers your picture the first time (what was showing), so undo can put it back.
- `anytvart bridge` runs in the foreground. `sh scripts/service.sh install` keeps it running after a restart (built, not yet tested).

## Art brightness on the light curve

The bridge sets the TV's own art brightness from a curve that follows the sun: sunrise and sunset and
measured sunlight from Open-Meteo, at most every 15 minutes, and only while the TV is in Art Mode. At
night it goes to its lowest. The range is `tvs[].calibration.frame_min` (default 1) and `frame_max`
(default 8), on the TV's 0 to 10 scale. Unlike dimming a picture on an LCD, Samsung's art brightness
is the TV's real backlight, so it can save power (the amount is a guess, G).

## TV settings to check

Menu names move between years. These are the 2021 to 2024 names, from Settings.

1. **Same Wi-Fi as the computer**, not a guest network, and the router must not keep devices apart
   (client isolation).
2. **Motion sensor** so the screen goes dark in an empty room: in Art Mode settings, **Sleep After**
   (or Motion Detector) at 15 or 30 minutes, sensitivity medium. The screen comes back when someone
   walks in (V, T on a 2021 model).
3. **Brightness sensor** on, in the same Art Mode settings.
4. **Auto Power Off off**: Settings, General, Eco Solution, Auto Power Off. Left on, the TV can switch
   itself fully off after hours without a button press (V, manual), and fully off it drops off the
   network and misses the picture (T). This setting cannot be changed over the network (G), so the
   setup agent gives you the menu path and asks you to set it.
5. **Night Mode on, on 2022 and newer models** (V, Samsung AU): it turns the screen off in a dark
   room. On a 2021 model the motion sleep and the brightness sensor do this job (T).
6. **Power On with Mobile and IP Remote on**, if your TV has them: Settings, General, Network, Expert
   Settings. They help the TV answer the computer. Waking a fully off TV over the network did not work
   on the 2021 model we tested (T), so the tool never relies on it.
7. **A fixed address** for the TV in your router.

## What it never does

- **It never presses a power key** and **never takes the TV out of Art Mode**. A short press of the
  power button toggles between TV and Art Mode, and a hold of at least 3 seconds is real off (V,
  Samsung AU, T). That is yours.
- **It only deletes pictures it uploaded itself**, recorded in `data/state-<tv>.json`, and only if the
  TV still describes them the way they were sent. Your own photos are never touched.
- **It never deletes the picture on screen** before a new one is showing. On a 2021 model, after the
  picture on screen was deleted, the TV ignored every request to show a photo for hours (T).
- The brightness step only runs while the TV is in Art Mode.

## Undo

```sh
.venv/bin/anytvart undo --tv "Hall"
```

Your own picture is put back first, then this tool's uploads are deleted. If the TV shows one of
Samsung's own artworks afterwards, choose your photo with the remote: Art Mode, My Photos. Running
undo twice is harmless. To remove the pairing, delete "any-tv-art" from the Device List on the TV.

## 2025 and newer QLED, Neo QLED and OLED with Art Mode

Samsung's 2025 QLED and Neo QLED, and some 2026 OLED TVs, have Art Mode with the Art Store (V). Our
upload on these is **built, not tested**: they may report that they have no Art Mode support even when
they do (R), which is why `check` asks the art channel itself. If the upload is refused, `pair`
and `check` will say so. Their sleep and power behaviour is not known (G). Art Mode Options has Sleep
After, Motion Detector and Night Mode (V). Please use the tester form if you try one.

Samsung's art channel has changed with firmware before: it was removed in one 2022 update and later
came back (R). A future update could change things.

## Known issues

- Not yet run by this repo on a real TV.
- A fully off TV does not answer and gets no picture that day.
- A 2021 model ignored a "show this picture" request while in Art Mode after the picture on screen was
  deleted. The tool retries and says "kept another picture for now" (T on the code we copied).
- The daily picture needs the bridge to be running. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
