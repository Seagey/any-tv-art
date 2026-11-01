package app.anytvart

import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import kotlin.math.*

/** Sunrise and sunset from the NOAA general solar position formulas, good to a minute or two. */
object SunTimes {
    fun compute(date: LocalDate, lat: Double, lon: Double): Pair<Instant, Instant>? {
        val jd = date.toEpochDay() + 2440587.5 + 0.5 - lon / 360.0
        val t = (jd - 2451545.0) / 36525.0
        val l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)).mod(360.0)
        val m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
        val e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
        val mr = Math.toRadians(m)
        val c = sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
            sin(2 * mr) * (0.019993 - 0.000101 * t) + sin(3 * mr) * 0.000289
        val omega = Math.toRadians(125.04 - 1934.136 * t)
        val lambda = Math.toRadians(l0 + c - 0.00569 - 0.00478 * sin(omega))
        val obliq = Math.toRadians(
            23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0 + 0.00256 * cos(omega)
        )
        val decl = asin(sin(obliq) * sin(lambda))
        val y = tan(obliq / 2).pow(2)
        val l0r = Math.toRadians(l0)
        val eqTime = 4.0 * Math.toDegrees(
            y * sin(2 * l0r) - 2 * e * sin(mr) + 4 * e * y * sin(mr) * cos(2 * l0r) -
                0.5 * y * y * sin(4 * l0r) - 1.25 * e * e * sin(2 * mr)
        )
        val latR = Math.toRadians(lat)
        val cosHa = cos(Math.toRadians(90.833)) / (cos(latR) * cos(decl)) - tan(latR) * tan(decl)
        // Polar day or night: no sunrise or sunset that date.
        if (cosHa < -1.0 || cosHa > 1.0) return null
        val ha = Math.toDegrees(acos(cosHa))
        val noon = 720.0 - 4.0 * lon - eqTime
        val base = date.atStartOfDay().toEpochSecond(ZoneOffset.UTC)
        return Instant.ofEpochSecond(base + ((noon - 4.0 * ha) * 60).toLong()) to
            Instant.ofEpochSecond(base + ((noon + 4.0 * ha) * 60).toLong())
    }
}

/** Dim and warmth in alone mode: none by day, easing in over the two hours after sunset, easing out for the hour after sunrise. */
object AloneLight {
    private const val NIGHT = 0.6
    fun at(now: Instant, sun: Pair<Instant, Instant>?): Pair<Double, Double> {
        if (sun == null) return 0.0 to 0.0
        val (rise, set) = sun
        val s = now.epochSecond
        val f = when {
            s < rise.epochSecond -> 1.0
            s < rise.epochSecond + 3600 -> 1.0 - (s - rise.epochSecond) / 3600.0
            s <= set.epochSecond -> 0.0
            s < set.epochSecond + 7200 -> (s - set.epochSecond) / 7200.0
            else -> 1.0
        }
        return NIGHT * f to NIGHT * f
    }
}

object DailyPick {
    private val exts = listOf(".jpg", ".jpeg", ".png", ".webp")
    fun pick(names: List<String>, date: LocalDate): String? {
        val photos = names.filter { n -> exts.any { n.lowercase().endsWith(it) } && !n.startsWith(".") }
            .sortedBy { it.lowercase() }
        if (photos.isEmpty()) return null
        return photos[date.dayOfYear % photos.size]
    }
}

object Wmo {
    fun text(code: Int): String = when (code) {
        0, 1 -> "Sunny"
        2 -> "Partly cloudy"
        3 -> "Cloudy"
        45, 48 -> "Fog"
        in 51..57 -> "Drizzle"
        in 61..67 -> "Rain"
        in 71..77, 85, 86 -> "Snow"
        in 80..82 -> "Showers"
        in 95..99 -> "Storms"
        else -> "Cloudy"
    }
}

object DateText {
    private val days = listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    private val months = listOf("January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December")
    fun format(date: LocalDate, order: String): String {
        val d = days[date.dayOfWeek.value - 1]
        val m = months[date.monthValue - 1]
        return if (order == "month-day") "$d $m ${date.dayOfMonth}" else "$d ${date.dayOfMonth} $m"
    }
}

object Drift {
    /** A few pixels, new each hour, the same for the same hour. Never more than 6. */
    fun forHour(epochHour: Long): Pair<Int, Int> {
        val x = (((epochHour * 7 + 3) % 13) + 13) % 13 - 6
        val y = (((epochHour * 11 + 5) % 13) + 13) % 13 - 6
        return x.toInt() to y.toInt()
    }
}

class Weather(val text: String, val high: Int, val low: Int, val unit: String)

object InfoBuilder {
    fun alone(c: Config, date: LocalDate, weather: Weather?, notSetUp: Boolean = false): JSONObject {
        val blocks = JSONArray()
        val info = JSONObject()
        val dateText = DateText.format(date, c.dateOrder)
        blocks.put("date"); info.put("date", dateText)
        if (weather != null) {
            blocks.put("weather")
            info.put("weather", "${weather.text}, ${weather.high}° / ${weather.low}°")
            info.put("wx", JSONObject().put("text", weather.text).put("high", weather.high).put("low", weather.low).put("unit", weather.unit))
        }
        val quote = if (notSetUp) "Not set up yet" else c.quoteLines.takeIf { it.isNotEmpty() }?.let { it[date.dayOfYear % it.size] }
        if (quote != null) { blocks.put("quote"); info.put("quote", quote) }
        info.put("blocks", blocks).put("events", JSONArray()).put("empty_text", "").put("reminders", JSONArray())
        if (quote == null) info.put("quote", "")
        return info
    }
}
