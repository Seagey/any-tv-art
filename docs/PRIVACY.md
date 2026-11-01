# Privacy

## In three lines

1. Everything runs at home. No account, no cloud service, no analytics, no running costs beyond
   electricity.
2. Your settings, TV addresses and tokens stay in `config.json` and `data/`, which git ignores.
3. A photo of your room goes only to your own AI agent, never to us, to GitHub, or into the repo.

## What leaves the house

- The weather and sunlight request to Open-Meteo: a latitude and longitude rounded to three decimals
  (and, if you give a place name instead of coordinates, that name once, to look it up),
  nothing else.
- Your own calendar link, if you add one: fetched from Google, Apple or Microsoft.
- On Google TV, the app on the TV reads the bridge on your own network, and in no-computer mode asks
  Open-Meteo for the weather.

The picture is drawn on your computer (or on the TV) from fonts included in the repo. The page it
draws loads nothing from the internet. The Android app's only permission is INTERNET, and it can load a
page only from its own origin.

## Photos of your room (the photo check)

The setup agent may ask for three phone photos, taken with a sheet of white paper beside the TV, so it
can judge glare and brightness. This is what happens to them, and what the agent says out loud before
the first photo:

- **The photo shows the inside of your house.** It goes from your phone to **your own AI provider**
  (Anthropic, OpenAI or whoever runs your agent), under the terms of your account there. It never goes
  to us, to GitHub or into the repo.
- **Phone photos carry GPS and camera details.** If the agent runs on your computer, the photo goes
  through `anytvart photo-prep PHOTO` first. That strips location and camera data, shrinks it, can crop
  it to just the TV and the paper (`--crop left,top,right,bottom`), and saves it in `data/checks`. It
  prints "location data left: none". It is deleted after the check unless you keep it. The original is
  never changed.
- If the photo goes straight from your phone into a chat app, you are asked first to switch off
  location for the camera, or crop the photo, before you send it.
- **No camera is ever used for presence, or for anything else.** "Home hours" uses a phone answering on
  your Wi-Fi, if you choose it, never a camera.

## What is in `config.json` and `data/`

`config.json` holds your TV names and addresses, your place, calendar links, reminders and settings.
`data/` holds what the tool keeps for itself:

| File | What it is |
|---|---|
| `token-<tv>.txt` | The Samsung's pairing token |
| `changes-<tv>.json` | Every Android setting we changed, with its old value (for undo) |
| `state-<tv>.json` | What we uploaded to a Samsung, and the picture it had before (for undo) |
| `bridge-memory.json` | What the bridge did today, so a restart never wakes a TV twice |
| `sun.json`, `calendar-*.ics`, `today-*.jpg`, `preview-*.png`, `checks/` | Caches, previews and prepared room photos |

`.gitignore` excludes `/config.json`, `/data/`, `/photos/`, `*.token` and `token.txt`. Never commit or
paste them. A calendar link is like a key to your calendar.

## The redacted report

If you want to tell us how it went, use:

```sh
.venv/bin/anytvart report --tv "Lounge"
```

It prints the TV's family, model, system and settings with IP addresses, MAC addresses, serials,
device names, the TV's name in your config and your place name taken out. **Read it through before you
paste it**, and delete anything personal it missed. The tester form has a box for that.

## What we do not do

- Send a room photo anywhere but to your own AI agent.
- Use cameras for presence.
- Take your Wi-Fi name, password or any account. Never share one with an agent.
- Keep any copy of your pictures. Your photos are copied, never changed. The copy sent to a TV is a
  new JPEG with no location or camera details.

## Sharing your own fork

Run `scripts/privacy-scan.sh path/to/your-words.txt` first, with a file of words you never want
published (names, street, Wi-Fi name), kept outside the repo. It looks for addresses, emails, phone
numbers, MAC addresses, keys, home paths, calendar links and your words, in the files and the git
history. `scripts/install-hook.sh` runs it before every commit.
