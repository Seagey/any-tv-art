package app.anytvart

import org.junit.Assert.*
import org.junit.Test
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId

class LogicTest {
    private val sydney = ZoneId.of("Australia/Sydney")
    private fun minutes(i: Instant, d: LocalDate): Int {
        val z = i.atZone(sydney)
        assertEquals(d, z.toLocalDate())
        return z.hour * 60 + z.minute
    }

    @Test fun sunSydneySummerSolstice() {
        val d = LocalDate.of(2026, 12, 21)
        val (rise, set) = SunTimes.compute(d, -33.8688, 151.2093)!!
        assertEquals(5 * 60 + 41.toDouble(), minutes(rise, d).toDouble(), 5.0)
        assertEquals(20 * 60 + 5.toDouble(), minutes(set, d).toDouble(), 5.0)
    }

    @Test fun sunSydneyWinterSolstice() {
        val d = LocalDate.of(2026, 6, 21)
        val (rise, set) = SunTimes.compute(d, -33.8688, 151.2093)!!
        assertEquals(7 * 60 + 0.toDouble(), minutes(rise, d).toDouble(), 5.0)
        assertEquals(16 * 60 + 54.toDouble(), minutes(set, d).toDouble(), 5.0)
    }

    @Test fun polarNightHasNoSun() {
        assertNull(SunTimes.compute(LocalDate.of(2026, 12, 21), 80.0, 0.0))
    }

    @Test fun aloneLightCurve() {
        val d = LocalDate.of(2026, 12, 21)
        val sun = SunTimes.compute(d, -33.8688, 151.2093)
        val noon = d.atTime(12, 0).atZone(sydney).toInstant()
        val late = d.atTime(23, 0).atZone(sydney).toInstant()
        val early = d.atTime(3, 0).atZone(sydney).toInstant()
        assertEquals(0.0, AloneLight.at(noon, sun).first, 0.0)
        assertEquals(0.6, AloneLight.at(late, sun).first, 1e-9)
        assertEquals(0.6, AloneLight.at(early, sun).second, 1e-9)
        val mid = sun!!.second.plusSeconds(3600)
        assertEquals(0.3, AloneLight.at(mid, sun).first, 1e-9)
    }

    @Test fun dailyPickIsStableAndSorted() {
        val names = listOf("b.jpg", "A.jpg", "c.png", "notes.txt", ".hidden.jpg")
        val d = LocalDate.of(2026, 11, 1) // day 305, 305 % 3 = 2
        assertEquals("c.png", DailyPick.pick(names, d))
        assertEquals(DailyPick.pick(names, d), DailyPick.pick(names.reversed(), d))
        assertNull(DailyPick.pick(listOf("x.txt"), d))
    }

    @Test fun wmoWords() {
        assertEquals("Sunny", Wmo.text(0))
        assertEquals("Partly cloudy", Wmo.text(2))
        assertEquals("Cloudy", Wmo.text(3))
        assertEquals("Fog", Wmo.text(45))
        assertEquals("Drizzle", Wmo.text(53))
        assertEquals("Rain", Wmo.text(63))
        assertEquals("Showers", Wmo.text(81))
        assertEquals("Storms", Wmo.text(95))
        assertEquals("Snow", Wmo.text(73))
    }

    @Test fun dateText() {
        val d = LocalDate.of(2026, 11, 1)
        assertEquals("Sunday 1 November", DateText.format(d, "day-month"))
        assertEquals("Sunday November 1", DateText.format(d, "month-day"))
    }

    @Test fun driftIsBoundedAndDeterministic() {
        for (h in 480000L..480100L) {
            val (x, y) = Drift.forHour(h)
            assertTrue(Math.abs(x) <= 6 && Math.abs(y) <= 6)
            assertEquals(Drift.forHour(h), Drift.forHour(h))
        }
    }

    @Test fun configParsing() {
        val c = Config.parse("""{"mode":"bridge","bridge_url":"http://192.0.2.5:5430/","place":{"name":"M","latitude":-37.8,"longitude":144.9},"quote_lines":["a","b"],"oled":true,"units":"fahrenheit","date_order":"month-day"}""")
        assertTrue(c.configured); assertEquals("bridge", c.mode); assertEquals("http://192.0.2.5:5430", c.bridgeUrl)
        assertEquals(-37.8, c.latitude!!, 0.0); assertEquals(2, c.quoteLines.size)
        assertTrue(c.oled); assertEquals("fahrenheit", c.units); assertEquals("month-day", c.dateOrder)
        val min = Config.parse("{}")
        assertTrue(min.configured); assertEquals("alone", min.mode); assertNull(min.latitude); assertFalse(min.oled)
        assertFalse(Config.parse("not json").configured)
        assertFalse(Config.parse(null).configured)
        assertFalse(Config.parse("").configured)
    }

    @Test fun infoForAlone() {
        val c = Config(configured = true, quoteLines = listOf("q1", "q2"))
        val i = InfoBuilder.alone(c, LocalDate.of(2026, 11, 1), Weather("Partly cloudy", 24, 15, "C"))
        assertEquals("Partly cloudy, 24° / 15°", i.getString("weather"))
        assertEquals(3, i.getJSONArray("blocks").length())
        val n = InfoBuilder.alone(c, LocalDate.of(2026, 11, 1), null)
        assertEquals(2, n.getJSONArray("blocks").length())
    }
}
