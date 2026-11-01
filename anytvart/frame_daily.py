"""The Samsung side: a new print-look picture in Art Mode each morning, and art brightness that
follows the room. Carried over from smart-frame-tv (which works on a real 2021 Frame), per TV.

Safety rules, unchanged: this only deletes pictures it uploaded itself (data/state-<tv>.json),
never the picture on screen before a new one is showing, and undo puts the owner's picture back
first. It never takes the TV out of Art Mode and never presses power.
"""
import asyncio
import os

from . import info, photos, render
from .config import screen_for
from .drivers.samsung_art import Frame, FrameAsleep, FrameError, reachable
from .state import State


def state_for(cfg, tv):
    safe = "".join(c if c.isalnum() else "-" for c in tv["name"].lower())
    return State(cfg.file("state-%s.json" % safe))


def due(cfg, state, now):
    if now.hour < int(cfg["art"]["picture_hour"]):
        return False
    return state.data.get("last_date") != now.date().isoformat()


async def _send(cfg, tv, state, path):
    async with Frame(cfg, tv) as frame:
        if not state.data.get("before"):
            # Remember the owner's picture once, so undo can put it back.
            cur = await frame.current() or {}
            if cur.get("content_id") and cur["content_id"] not in {u["id"] for u in state.uploaded}:
                state.data["before"] = {"id": cur["content_id"], "category": cur.get("category_id") or ""}
        cid, stamp = await frame.upload(path)
        state.add_upload(cid, stamp)
        state.save()   # recorded before anything else, so it can always be tidied later
        shown = await frame.make_current(cid)
        state.data["shown"] = shown
        older = [u for u in state.uploaded if u["id"] != cid]
        deleted, gone, skipped = await frame.delete_ours(older) if (older and shown) else ([], [], [])
        for x in deleted + gone + skipped:
            state.forget(x)
        return cid, deleted, shown


async def _show_again(cfg, tv, cid):
    async with Frame(cfg, tv) as frame:
        return await frame.make_current(cid)


async def _delete(cfg, tv, records):
    async with Frame(cfg, tv) as frame:
        return await frame.delete_ours(records)


def picture(cfg, tv, now, out):
    """Make today's 4K picture for this TV. Returns the photo's file name."""
    state = state_for(cfg, tv)
    name = photos.choose(cfg, state, now.date())
    tv4k = dict(tv, screen=screen_for(tv, 3840))
    render.render(cfg, tv4k, os.path.join(cfg.photo_folder, name), info.gather(cfg, now), out, "4k")
    state.save()
    return name


def run(cfg, tv, now, force=False, log=print):
    """Upload today's picture if it is due. Quiet (returns None) when not due or the TV is off."""
    state = state_for(cfg, tv)
    if state.data.get("shown") is False and state.data.get("current") and reachable(tv["ip"], tv["port"]):
        # Today's picture is on the TV but the Frame kept another one: a real 2021 Frame ignored
        # selects in Art Mode and took one at once while showing TV. Try again, then carry on.
        try:
            if asyncio.run(_show_again(cfg, tv, state.data["current"])):
                state.data["shown"] = True
                older = [u for u in state.uploaded if u["id"] != state.data["current"]]
                if older:
                    for x in sum(asyncio.run(_delete(cfg, tv, older))[:3], []):
                        state.forget(x)
                state.save()
                log("%s: today's picture is now showing" % tv["name"])
        except FrameError:
            pass
    if not force and not due(cfg, state, now):
        return None
    if not reachable(tv["ip"], tv["port"]):
        return None
    out = cfg.file("today-%s.jpg" % "".join(c if c.isalnum() else "-" for c in tv["name"].lower()))
    try:
        name = picture(cfg, tv, now, out)
        state = state_for(cfg, tv)
        cid, deleted, shown = asyncio.run(_send(cfg, tv, state, out))
    except FrameAsleep:
        return None
    except (FrameError, photos.PhotoError) as e:
        log("%s: failed: %s" % (tv["name"], e))
        return False
    state.data["last_photo"] = name
    state.mark_run(now.date().isoformat())
    state.save()
    log("%s: showing %s (%s), removed %s%s" % (tv["name"], cid, name, ", ".join(deleted) or "nothing",
        "" if shown else "; the Frame kept another picture for now"))
    return True


async def _brightness(cfg, tv, value):
    async with Frame(cfg, tv) as frame:
        if await frame.art_mode() != "on":
            return None              # only in Art Mode; TV mode brightness is the owner's
        now = await frame.brightness()
        if now == value:
            return now
        return await frame.set_brightness(value)


def set_brightness(cfg, tv, value):
    if not reachable(tv["ip"], tv["port"]):
        return None
    try:
        return asyncio.run(_brightness(cfg, tv, value))
    except FrameError:
        return None


async def _undo(cfg, tv, state):
    async with Frame(cfg, tv) as frame:
        # Put the owner's picture back FIRST. A real 2021 Frame whose showing picture was deleted
        # fell back to a Samsung artwork and then ignored every request to show a photo.
        before, put_back = state.data.get("before") or {}, None
        if before.get("id") and before["id"] not in {u["id"] for u in state.uploaded}:
            try:
                await frame.select(before["id"], category=before.get("category") or None)
                put_back = before["id"]
            except Exception:
                pass
        return (await frame.delete_ours(list(state.uploaded))) + (put_back,)


def undo(cfg, tv):
    state = state_for(cfg, tv)
    if not state.uploaded:
        return "nothing of ours on %s" % tv["name"]
    deleted, gone, skipped, put_back = asyncio.run(_undo(cfg, tv, state))
    for x in deleted + gone + skipped:
        state.forget(x)
    state.data["last_date"] = ""
    state.data["before"] = None
    state.save()
    return "%s: removed %d of ours%s%s" % (tv["name"], len(deleted), ", put your picture back" if put_back else "",
                                          ", left %d alone (no longer look like ours)" % len(skipped) if skipped else "")
