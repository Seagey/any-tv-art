"""Settings, the daily cycle, the light curve, power, privacy. No TV and no network.
Run: .venv/bin/python -m unittest discover tests"""
import os
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

from anytvart import config, light, photoprep, power, schedule
from anytvart.cli import redact

TZ = ZoneInfo("Australia/Sydney")
SUN = {"sunrise": "05:45", "sunset": "19:30", "radiation": None}


def cfg(**extra):
    base = {"timezone": "Australia/Sydney", "tvs": [{"name": "Lounge", "ip": "192.0.2.20", "size_inch": 98}]}
    base.update(extra)
    return config.Config(base, os.path.join(tempfile.mkdtemp(), "config.json"))


def at(h, m=0, day=1):
    return datetime(2026, 11, day, h, m, tzinfo=TZ)


SEEN_ART = {"reachable": True, "awake": True, "ours": True, "playing": False}


class ConfigTests(unittest.TestCase):
    def test_defaults_and_tv_look_merge(self):
        c = cfg(tvs=[{"name": "A", "look": {"mat": {"colour": "#e0d8cc"}}}])
        tv = c.tv()
        self.assertEqual(tv["look"]["mat"]["colour"], "#e0d8cc")
        self.assertEqual(tv["look"]["mat"]["width"], 0.085)     # the rest from the shared look
        self.assertEqual(tv["port"], 5555)

    def test_refuses_pure_white_and_bad_hours(self):
        with self.assertRaises(config.ConfigError):
            cfg(look={"mat": {"colour": "#ffffff"}})
        with self.assertRaises(config.ConfigError):
            cfg(tvs=[{"name": "A", "art_hours": "evenings"}])
        with self.assertRaises(config.ConfigError):
            cfg(art={"night_off": "25:00"})

    def test_screen_millimetres(self):
        tv = cfg().tv()
        s = config.screen_for(tv)
        self.assertAlmostEqual(s["mm_per_px"], 1.13, places=2)          # a 98 inch at 1080p
        self.assertAlmostEqual(config.screen_for(dict(tv, size_inch=65), 3840)["device_mm_per_px"], 0.375, places=2)


class ScheduleTests(unittest.TestCase):
    def test_idle_tv_is_only_slept_at_night(self):
        c = cfg()
        tv = c.tv()
        self.assertEqual(schedule.decide(c, tv, at(15), SEEN_ART, {})[0], [])
        self.assertEqual(schedule.decide(c, tv, at(22, 30), SEEN_ART, {})[0], ["sleep"])

    def test_never_sleeps_while_playing_or_on_something_else(self):
        c = cfg()
        tv = c.tv()
        self.assertEqual(schedule.decide(c, tv, at(23), dict(SEEN_ART, playing=True), {})[0], [])
        self.assertEqual(schedule.decide(c, tv, at(23), dict(SEEN_ART, ours=False), {})[0], [])

    def test_night_sleep_retries_every_ten_minutes(self):
        c = cfg()
        tv = c.tv()
        acts, mem = schedule.decide(c, tv, at(22, 0), SEEN_ART, {})
        self.assertEqual(acts, ["sleep"])
        self.assertEqual(schedule.decide(c, tv, at(22, 5), SEEN_ART, mem)[0], [])
        self.assertEqual(schedule.decide(c, tv, at(22, 10), SEEN_ART, mem)[0], ["sleep"])

    def test_day_art_wakes_once_in_the_morning(self):
        c = cfg(tvs=[{"name": "Lounge", "art_hours": "day"}])
        tv = c.tv()
        asleep = {"reachable": True, "awake": False, "ours": False, "playing": False}
        acts, mem = schedule.decide(c, tv, at(6, 59), asleep, {})
        self.assertEqual(acts, [])                                        # still night
        acts, mem = schedule.decide(c, tv, at(7, 0), asleep, mem)
        self.assertEqual(acts, ["wake", "open_art"])
        self.assertEqual(schedule.decide(c, tv, at(9), asleep, mem)[0], [])   # once a day: off by hand stays off

    def test_range_ends_with_sleep(self):
        c = cfg(tvs=[{"name": "Lounge", "art_hours": "16:00-21:00"}])
        tv = c.tv()
        self.assertEqual(schedule.decide(c, tv, at(16), {"reachable": True, "awake": True, "ours": False, "playing": True}, {})[0], [])
        self.assertEqual(schedule.decide(c, tv, at(21, 1), SEEN_ART, {"woke": "2026-11-01"})[0], ["sleep"])

    def test_home_hours_need_someone_home(self):
        c = cfg(tvs=[{"name": "Lounge", "art_hours": "home"}])
        tv = c.tv()
        asleep = {"reachable": True, "awake": False}
        self.assertEqual(schedule.decide(c, tv, at(10), asleep, {}, home=False)[0], [])
        self.assertEqual(schedule.decide(c, tv, at(10), asleep, {}, home=True)[0], ["wake", "open_art"])

    def test_unreachable_tv_gets_nothing(self):
        c = cfg()
        self.assertEqual(schedule.decide(c, c.tv(), at(23), {"reachable": False}, {})[0], [])


class LightTests(unittest.TestCase):
    def test_curve_follows_the_sun(self):
        c = cfg()
        tv = c.tv()
        noon, dusk, night = (light.level(c, tv, at(h, m), SUN) for h, m in ((13, 0), (19, 40), (23, 0)))
        self.assertEqual(noon["dim"], 0)
        self.assertTrue(0 < dusk["dim"] < night["dim"] or dusk["dim"] == night["dim"])
        self.assertTrue(night["warm"] > noon["warm"])
        self.assertFalse(night["art"])
        self.assertTrue(noon["art"])
        self.assertEqual(night["frame_brightness"], 1)
        self.assertEqual(noon["frame_brightness"], 8)

    def test_dull_day_is_dimmer(self):
        c = cfg()
        tv = c.tv()
        dull = dict(SUN, radiation=[100] * 24)
        self.assertGreater(light.level(c, tv, at(13), dull)["dim"], 0)

    def test_offline_falls_back(self):
        c = cfg()
        s = light.sun(c, at(12).date(), fetch=lambda *a: (_ for _ in ()).throw(OSError("no network")))
        self.assertEqual((s["sunrise"], s["sunset"]), light.FALLBACK)


class PowerTests(unittest.TestCase):
    def test_big_screen_size_guess_and_dollars(self):
        c = cfg()
        w, src = power.watts(c.tv())
        self.assertTrue(250 <= w <= 340, w)                                # BUILD.md: about 300 W
        self.assertIn("guess", src)
        self.assertAlmostEqual(power.per_year(300, 12, 0.40), 525.6)
        self.assertEqual(power.watts(dict(c.tv(), watts_art=287))[1], "measured")


class PrivacyTests(unittest.TestCase):
    def test_photo_prep_strips_location(self):
        d = tempfile.mkdtemp()
        src = os.path.join(d, "room.jpg")
        im = Image.new("RGB", (4000, 3000), (200, 190, 180))
        exif = Image.Exif()
        exif[0x010F] = "PhoneMaker"
        exif.get_ifd(0x8825)[2] = (28.0, 50.0, 0.0)                       # a GPS latitude
        im.save(src, exif=exif)
        self.assertTrue(photoprep.has_location(src))
        out = photoprep.prep(src, os.path.join(d, "out"))
        self.assertFalse(photoprep.has_location(out))
        with Image.open(out) as o:
            self.assertLessEqual(max(o.size), photoprep.LONG_EDGE)
            self.assertNotIn(0x010F, o.getexif())

    def test_report_redaction(self):
        # Built at run time so the repo's own privacy scan does not flag the test itself.
        ip = ".".join(["10", "0", "0", "20"])
        mac = ":".join(["02", "AB", "CD", "00", "00", "01"])
        text = redact('{"ip": "%s", "mac": "%s", "name": "Lounge TV"} at Exampleton' % (ip, mac), ["Exampleton"])
        self.assertNotIn(ip, text)
        self.assertNotIn(mac, text)
        self.assertNotIn("Lounge", text)
        self.assertNotIn("Exampleton", text)


if __name__ == "__main__":
    unittest.main()
