# config.json, every setting

Copy `config.example.json` to `config.json` and change what you need. Anything left out uses the
default shown here. `config.json` is ignored by git. A mistake in the file is reported in plain words
when any command runs, for example `config.json: TV "Lounge": panel must be "lcd" or "oled"`.

The settings file is `config.json` in the folder you run from, or the file named by `--config`, or the
`ANYTVART_CONFIG` environment variable. The `_comment` line is ignored.

## Top level

| Key | Default | Allowed | Meaning |
|---|---|---|---|
| `timezone` | this computer's | A time zone name like `"Australia/Melbourne"`; an unknown name is an error | Decides what "today" is and when the schedule fires |
| `date_order` | `"day-month"` | `"day-month"` or `"month-day"` | Tuesday 3 March, or Tuesday, March 3 |
| `clock` | `"12h"` | `"12h"` or `"24h"` | Event times as `9:30 am` or `09:30` |
| `price_kwh` | `0.40` | A number above 0 and below 5, in dollars | The price of one kWh, for `anytvart power` |
| `adb` | `""` | A path | Where `adb` is, if it is not on your path (the `ANYTVART_ADB` variable also works) |
| `chrome` | found by itself | A path (not in the defaults, add it if needed) | Where Chrome, Chromium, Edge or Brave is, if it is somewhere unusual (the `ANYTVART_CHROME` variable also works) |

## Photos

| Key | Default | Allowed | Meaning |
|---|---|---|---|
| `photos.folder` | `"photos"` | A folder; relative is inside this one; `~` works | Where your photos are |
| `photos.pick` | `"day"` | `"day"`, `"rotate"`, `"random"`, `"fixed"` | A new photo each day in name order; the next one each time a picture is made; any but never the same twice in a row; or always `photos.file` |
| `photos.file` | `""` | A photo's file name | Required when `pick` is `"fixed"` |
| `photos.focus` | `"centre"` | `"centre"`, `"top"`, `"bottom"`, `"left"`, `"right"` | Which part survives the 16:9 crop |

A photo whose name starts with a month and day (`12-25 tree.jpg`) shows on that date each year, and
on no other day. iPhone `.heic` photos work if `pillow-heif` installed.

## The look

```json
"look": {
  "style": "mat",
  "mat": {"colour": "#ece6da", "width": 0.085, "bevel": true, "light": "top-left", "shadow": 0.5},
  "grain": {"on": true, "strength": 0.5},
  "flatten": {"strength": 0.6},
  "label": {"on": true, "side": "left"}
}
```

| Key | Default | Allowed | Meaning |
|---|---|---|---|
| `look.style` | `"mat"` | `"mat"` or `"full"` | A mat round the photo with the label in the mat, or the photo to the edges with small words in a corner |
| `look.mat.colour` | `"#ece6da"` | `#` and six hex digits. **`#ffffff` and `#fefefe` are refused**: pure white glows on a screen. Try `#f1ece3` | The mat colour |
| `look.mat.width` | `0.085` | 0.03 to 0.2 | The mat's width as a share of the screen height |
| `look.mat.bevel` | `true` | true or false | A thin lit edge on the mat's inner opening |
| `look.mat.light` | `"top-left"` | `"top-left"`, `"top-right"`, `"top"` | Where the light comes from (which edge is lit, where the shadow falls) |
| `look.mat.shadow` | `0.5` | A number | How strong the mat's shadow on the photo is |
| `look.grain.on` | `true` | true or false | A paper grain. Only appears where a screen pixel is small enough to carry it |
| `look.grain.strength` | `0.5` | 0 to 1 | How strong the grain is |
| `look.flatten.strength` | `0.6` | 0 to 1 | Lifts blacks and rolls highlights toward the range of a print |
| `look.label.on` | `true` | true or false | The small label |
| `look.label.side` | `"left"` | `"left"` or `"right"` | Which side the label sits on |

### A different look for one TV

Each TV can have its own `look`. It is merged on top of the shared `look`, key by key, so a TV only
needs the keys that differ:

```json
"tvs": [
  {"name": "Lounge", "kind": "android", "ip": "192.0.2.20", "size_inch": 65,
   "look": {"mat": {"colour": "#d9d2c4", "width": 0.1}, "grain": {"on": false}}}
]
```

The same checks apply to a TV's `look` as to the shared one.

## What it shows

`blocks` is a list; the order is the order on the picture. Each entry is `{"type": "..."}` with an
optional `"on": false`. Types: `date`, `weather`, `calendar`, `reminders`, `quote`. Default: date,
weather, calendar, reminders. Any other type is an error.

| Key | Default | Meaning |
|---|---|---|
| `place.name` | `""` | A suburb or city, for the weather and sun times. Never a street. Looked up once by name |
| `place.country` | none | A country code like `"AU"`, to narrow the lookup |
| `place.latitude`, `place.longitude` | none | Use these instead of a name. Neither is a home address: rounded is fine |
| `weather.units` | `"celsius"` | `"celsius"` or `"fahrenheit"` |
| `weather.show_place` | `false` | Print the place name on the picture (this publishes where you live if you photograph it) |
| `weather.rain_chance` | `false` | Add the chance of rain when it is 20% or more |
| `calendar.ics_urls` | `[]` | Your calendar links (the public `.ics` link). A link is like a key: keep it here |
| `calendar.days` | `2` | How many days from today |
| `calendar.max` | `3` | At most this many events |
| `calendar.hide` | `[]` | Words: any event with one of them in its title is left out |
| `calendar.empty_text` | `"Nothing planned today"` | What to say when there are none |
| `reminders` | `[]` | A list of `{"text": "...", "days": ["mon"], "every_weeks": 2, "start": "2026-01-05", "dots": ["#b8483c"]}`. Every reminder needs `text`. `days` are `mon` to `sun`, others are an error. `every_weeks` with a `start` date makes it every second week and so on. `dots` are optional coloured dots |
| `quote.text` | `""` | One line of your own |
| `quote.lines` | `[]` | More lines, one per day |

In no-computer mode on Google TV, calendar and reminders are not shown (phase 1).

## Art hours and the bridge

| Key | Default | Allowed | Meaning |
|---|---|---|---|
| `art.night_off` | `"22:00"` | `"HH:MM"` | The night cut-off starts. Our own default; Google's 10 pm to 7 am is only when presence stops waking a TV |
| `art.morning_on` | `"07:00"` | `"HH:MM"` | The night cut-off ends; the morning wake time for art hours other than `idle` |
| `art.picture_hour` | `5` | 0 to 23 | From this hour the bridge makes the Samsung's daily picture |
| `bridge.port` | `5430` | A port | The bridge serves the TV app on this port (home network only) |
| `bridge.url` | `""` | An address like `"http://192.0.2.5:5430"` (this computer's address on the home network) | How a TV reaches the bridge. **Required for `apply --mode bridge`** |

## The TVs

`tvs` is a list. Each TV needs a unique `name` (not case sensitive). The `--tv` option picks one by
name; with a single TV you can leave it out.

| Key | Default | Allowed | Meaning |
|---|---|---|---|
| `name` | none, needed | Any, unique | What you call it |
| `kind` | `"android"` | `"android"` or `"samsung-art"` | Google TV and Android TV, or a Samsung with Art Mode |
| `ip` | `""` | An address | The TV's address on your Wi-Fi |
| `port` | `5555` for android, `8002` for samsung-art | A port | ADB for android, the art connection for Samsung |
| `size_inch` | `55` | 10 to 150 | Screen size, for the print look in millimetres and for `anytvart power` |
| `app_px` | `[1920, 1080]` | `[width, height]` | What the TV draws apps at. `read` shows what the TV reports. Many draw 1080p whatever the panel |
| `panel` | `"lcd"` | `"lcd"` or `"oled"` | Panel type, which cannot be read from the TV. `"oled"` turns on the slow drift |
| `watts_art` | none | A number | Measured watts showing art. Without it `power` uses a guess |
| `art_hours` | `"idle"` | `"idle"`, `"home"`, `"day"`, or a range like `"16:00-21:00"` | `idle`: art only after someone has used the TV and left it (lowest power). `day`: wake at `art.morning_on` and open the art. `home`: the same, only while someone is home. A range: wake at its start, sleep at its end |
| `look` | `{}` | As above | A look for this TV only |
| `safe` | `{}` | `{"left": 2, "top": 2, "right": 2, "bottom": 2}`, in percent of the screen | Keeps the picture and label inside the area the calibration card showed is visible (overscan) |
| `calibration` | `{}` | `dim_offset`, `warm_offset`, `frame_min`, `frame_max` | See below |
| `wake_back` | `false` | true or false | **Not built.** The key exists and nothing reads it |

### calibration

Where the photo check settled, so the light curve fits your room.

| Key | Default | Meaning |
|---|---|---|
| `calibration.dim_offset` | `0` | Added to the dimming all day. Up is dimmer |
| `calibration.warm_offset` | `0` | Added to the warmth. Up is warmer |
| `calibration.frame_min` | `1` | A Samsung's lowest art brightness, used at night |
| `calibration.frame_max` | `8` | A Samsung's highest art brightness, used in full daylight |

### More keys for each TV

| Key | Default | Meaning |
|---|---|---|
| `home_devices` | `[]` | For `art_hours: "home"`: addresses of phones on your Wi-Fi. The TV counts as "someone home" while any one answers a ping. With none listed, "home" behaves as "day" |
| `mac` | `""` | The TV's network card address, as six pairs of hex digits separated by colons (read it off the TV's network menu). With it, the bridge sends Wake-on-LAN when art is due and the TV has left the network. Built, not yet tested |
| `night_sleep` | `true` | For `art_hours: "idle"`: set to `false` to stop the bridge sleeping this TV at night. The TV is then left to its own timers |

### Checks and errors

- Two TVs with the same name, a missing name, an unknown `kind`, a `panel` that is not `lcd` or `oled`,
  a `size_inch` outside 10 to 150, or an `art_hours` that is not one of the forms above, are errors.
- `art_hours` ranges are `"HH:MM-HH:MM"` and may cross midnight.
- `night_off` and `morning_on` must be times like `"22:00"`.
