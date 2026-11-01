"""Android setup and undo against a pretend TV, the bridge's web answers, and the Samsung daily
picture against a pretend Frame. Run: .venv/bin/python -m unittest discover tests"""
import json
import os
import shutil
import tempfile
import unittest
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from anytvart import bridge, config, frame_daily, setup_android
from anytvart.drivers.android import AdbError, Android
from tests.fake_adb import FakeTV
from tests.fake_frame import FakeFrame

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS = os.path.join(REPO, "samples", "photos")
TZ = ZoneInfo("Australia/Sydney")


def make_cfg(d, **extra):
    base = {"timezone": "Australia/Sydney", "photos": {"folder": PHOTOS},
            "place": {"name": "Test", "latitude": -33.9, "longitude": 151.2},
            "bridge": {"url": "http://192.0.2.5:5430"},
            "tvs": [{"name": "Lounge", "ip": "192.0.2.20", "size_inch": 98}]}
    base.update(extra)
    return config.Config(base, os.path.join(d, "config.json"))


class AndroidTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="anytvart-test-")
        self.cfg = make_cfg(self.dir)
        self.fake = FakeTV()
        self.before = dict(self.fake.settings)
        self.apk = os.path.join(self.dir, "any-tv-art.apk")
        open(self.apk, "w").close()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def android(self):
        return Android(self.cfg, self.cfg.tv(), run=self.fake, adb="/fake/adb")

    def test_apply_then_undo_puts_every_value_back(self):
        setup_android.apply(self.cfg, self.cfg.tv(), "bridge", self.apk, say=lambda m: None, android=self.android())
        s = self.fake.settings
        self.assertEqual(s[("secure", "screensaver_components")], "app.anytvart/.ArtDream")
        self.assertEqual(s[("system", "screen_off_timeout")], "600000")
        self.assertTrue(self.fake.installed)
        done = setup_android.undo(self.cfg, self.cfg.tv(), android=self.android())
        self.assertEqual(self.fake.settings, self.before)
        self.assertFalse(self.fake.installed)
        self.assertIn("removed the art app and its photos", done)

    def test_undo_twice_is_harmless_and_unset_keys_are_deleted(self):
        del self.fake.settings[("secure", "attentive_timeout")]
        before = dict(self.fake.settings)
        setup_android.apply(self.cfg, self.cfg.tv(), "bridge", self.apk, say=lambda m: None, android=self.android())
        setup_android.undo(self.cfg, self.cfg.tv(), android=self.android())
        setup_android.undo(self.cfg, self.cfg.tv(), android=self.android())
        self.assertEqual(self.fake.settings, before)

    def test_old_value_recorded_before_the_change(self):
        a = self.android()
        a.connect()
        self.fake.refuse.add(("system", "screen_off_timeout"))     # a TV that will not take it
        with self.assertRaises(AdbError):
            a.put("system", "screen_off_timeout", "600000")
        with open(a.changes_file) as f:
            self.assertEqual(json.load(f)[0]["old"], "900000")

    def test_only_listed_settings_can_change(self):
        a = self.android()
        with self.assertRaises(AdbError):
            a.put("global", "power_picture_off", "1")
        self.assertNotIn(["settings put global power_picture_off 1"], [c[3:] for c in self.fake.commands])

    def test_alone_mode_copies_photos_without_metadata(self):
        setup_android.apply(self.cfg, self.cfg.tv(), "alone", self.apk, say=lambda m: None, android=self.android())
        self.assertTrue(any(p.endswith("/config.json") for p in self.fake.pushed))
        self.assertEqual(len([p for p in self.fake.pushed if "/photos/" in p]), len(os.listdir(PHOTOS)))
        self.assertEqual(self.fake.settings[("secure", "attentive_timeout")], "7200000")

    def test_app_config_points_each_tv_at_its_own_address(self):
        got = setup_android.app_config(self.cfg, self.cfg.tv(), "bridge")
        self.assertEqual(got["bridge_url"], "http://192.0.2.5:5430/tv/lounge")

    def test_state_reads_what_the_tv_is_doing(self):
        self.fake.wake, self.fake.dreaming_ours = "Dreaming", True
        st = self.android().state()
        self.assertTrue(st["awake"] and st["ours"])
        self.assertFalse(st["playing"])


class BridgeTests(unittest.TestCase):
    def test_serves_art_light_and_photo_per_tv(self):
        d = tempfile.mkdtemp(prefix="anytvart-test-")
        cfg = make_cfg(d, blocks=[{"type": "date"}], tvs=[{"name": "Lounge", "size_inch": 98},
                                                            {"name": "Bed Room", "size_inch": 55}])
        with open(cfg.file("sun.json"), "w") as f:
            json.dump({"date": cfg.now().date().isoformat(), "sunrise": "05:45", "sunset": "19:30", "radiation": None}, f)
        srv, b = bridge.serve(cfg, port=0, loop=False)
        base = "http://127.0.0.1:%d/tv/bed-room" % srv.server_address[1]
        try:
            art = json.load(urllib.request.urlopen(base + "/art.json"))
            self.assertTrue(art["photo"].startswith("/photo/bed-room-"))
            self.assertAlmostEqual(art["screen"]["mm_per_px"], 0.63, places=2)
            photo = urllib.request.urlopen(base + art["photo"]).read()
            self.assertEqual(photo[:2], b"\xff\xd8")
            lv = json.load(urllib.request.urlopen(base + "/light.json"))
            self.assertEqual(set(lv), {"dim", "warm", "art"})
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(base + "/photo/..%2Fconfig.json")
        finally:
            srv.shutdown()
            shutil.rmtree(d, ignore_errors=True)


OWNER = [{"content_id": "MY_F0001", "image_date": "2024:01:01 10:00:00"},
         {"content_id": "MY_F0002", "image_date": "2024:02:01 10:00:00"}]


class SamsungTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="anytvart-test-")
        self.fake = FakeFrame(photos=OWNER).start()
        self.cfg = make_cfg(self.dir, blocks=[{"type": "date"}],
                            tvs=[{"name": "Hall", "kind": "samsung-art", "ip": "127.0.0.1", "port": self.fake.port, "size_inch": 65}])
        self.tv = self.cfg.tv()

    def tearDown(self):
        self.fake.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_daily_picture_replaces_only_our_own(self):
        for day in (1, 2, 3):
            self.assertTrue(frame_daily.run(self.cfg, self.tv, datetime(2026, 11, day, 6, tzinfo=TZ), log=lambda m: None))
        self.assertEqual(self.fake.uploads, ["MY_F0003", "MY_F0004", "MY_F0005"])
        self.assertEqual(self.fake.ids(), ["MY_F0001", "MY_F0002", "MY_F0005"])   # owner's photos untouched
        self.assertEqual(self.fake.current, "MY_F0005")

    def test_not_due_before_picture_hour_or_twice_a_day(self):
        self.assertIsNone(frame_daily.run(self.cfg, self.tv, datetime(2026, 11, 1, 4, tzinfo=TZ)))
        frame_daily.run(self.cfg, self.tv, datetime(2026, 11, 1, 6, tzinfo=TZ), log=lambda m: None)
        self.assertIsNone(frame_daily.run(self.cfg, self.tv, datetime(2026, 11, 1, 9, tzinfo=TZ)))
        self.assertEqual(len(self.fake.uploads), 1)

    def test_undo_puts_the_owners_picture_back(self):
        frame_daily.run(self.cfg, self.tv, datetime(2026, 11, 1, 6, tzinfo=TZ), log=lambda m: None)
        frame_daily.undo(self.cfg, self.tv)
        self.assertEqual(self.fake.ids(), ["MY_F0001", "MY_F0002"])
        self.assertEqual(self.fake.current, "MY_F0001")


if __name__ == "__main__":
    unittest.main()
