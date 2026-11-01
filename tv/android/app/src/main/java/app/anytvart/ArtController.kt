package app.anytvart

import android.content.Context
import android.net.Uri
import android.os.Handler
import android.os.Looper
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZonedDateTime
import java.util.concurrent.Executors

/** Decides what the ArtView shows and keeps it fresh. One per dream or activity. */
class ArtController(private val ctx: Context, private val view: ArtView) {
    private val main = Handler(Looper.getMainLooper())
    private var io = Executors.newSingleThreadExecutor()
    private val root: File = ctx.getExternalFilesDir(null) ?: ctx.filesDir
    private val cache = File(root, "cache").apply { mkdirs() }

    @Volatile private var running = false
    private var config = Config()
    private var base: JSONObject? = null
    private var lastRendered: String? = null
    private var lastArtFetch = 0L
    private var lastWeatherTry = 0L
    private var artOn = true
    private var light = 0.0 to 0.0
    private var lastError: String? = null
    private var bridgeOk = false
    private var lastRefresh = ""

    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            io.execute { cycle() }
            main.postDelayed(this, 5 * 60_000L)
        }
    }

    fun start() {
        running = true
        if (io.isShutdown) io = Executors.newSingleThreadExecutor()
        io.execute { config = Config.parse(readText(File(root, "config.json"))); base = null; lastArtFetch = 0 }
        main.post(tick)
    }

    fun stop() {
        running = false
        main.removeCallbacksAndMessages(null)
        io.shutdown()
    }

    private fun readText(f: File): String? = try { if (f.isFile) f.readText() else null } catch (e: Exception) { null }

    private fun zone(): ZoneId = try { if (config.timezone.isNotEmpty()) ZoneId.of(config.timezone) else ZoneId.systemDefault() } catch (e: Exception) { ZoneId.systemDefault() }

    private fun cycle() {
        try {
            val now = ZonedDateTime.now(zone())
            if (config.configured && config.mode == "bridge" && config.bridgeUrl.isNotEmpty()) bridgeCycle(now)
            else aloneCycle(now)
            lastRefresh = now.toString()
        } catch (e: Exception) {
            lastError = e.toString()
        }
        val data = withDrift(base)
        val dim = light
        val on = artOn
        main.post {
            if (!running) return@post
            if (data != null) {
                val s = data.toString()
                if (s != lastRendered) { lastRendered = s; view.render(s) }
            }
            view.setLight(dim.first, dim.second)
            view.setBlack(!on)
        }
        writeStatus(data)
    }

    // Bridge mode

    private fun bridgeCycle(now: ZonedDateTime) {
        val b = config.bridgeUrl
        val t = System.currentTimeMillis()
        if (base == null || t - lastArtFetch >= 30 * 60_000L) {
            try {
                val art = JSONObject(String(get("$b/art.json")))
                val p = art.getString("photo")
                val abs = if (p.startsWith("http")) p else b + (if (p.startsWith("/")) "" else "/") + p
                val name = "photo-" + File(Uri.parse(p).path ?: "photo.jpg").name.replace(Regex("[^A-Za-z0-9._-]"), "_")
                val target = File(cache, name)
                if (!target.isFile) {
                    val tmp = File(cache, "$name.part")
                    tmp.writeBytes(get(abs))
                    tmp.renameTo(target)
                }
                cache.listFiles { f -> f.name.startsWith("photo-") && f.name != name }?.forEach { it.delete() }
                art.put("photo", ArtView.FILES + "cache/" + Uri.encode(name))
                File(cache, "art.json").writeText(art.toString())
                base = art
                lastArtFetch = t
                bridgeOk = true
                lastError = null
            } catch (e: Exception) {
                bridgeOk = false
                lastError = "art: $e"
                if (base == null) base = loadCachedArt()
            }
        }
        try {
            val l = JSONObject(String(get("$b/light.json")))
            light = l.optDouble("dim", 0.0) to l.optDouble("warm", 0.0)
            artOn = l.optBoolean("art", true)
            bridgeOk = true
        } catch (e: Exception) {
            bridgeOk = false
            lastError = "light: $e"
        }
        if (base == null) base = sample(now, LocalDate.now(zone()))
    }

    private fun loadCachedArt(): JSONObject? {
        val j = readText(File(cache, "art.json"))?.let { try { JSONObject(it) } catch (e: Exception) { null } } ?: return null
        val name = Uri.decode(j.optString("photo").substringAfterLast('/'))
        return if (File(cache, name).isFile) j else null
    }

    // Alone mode

    private fun aloneCycle(now: ZonedDateTime) {
        val date = now.toLocalDate()
        val photos = File(root, "photos").list()?.toList() ?: emptyList()
        val pick = if (config.configured) DailyPick.pick(photos, date) else null
        if (pick == null) { base = sample(now, date); light = 0.0 to 0.0; artOn = true; return }
        val d = JSONObject()
        d.put("photo", ArtView.FILES + "photos/" + Uri.encode(pick))
        d.put("focus", "50% 50%")
        d.put("info", InfoBuilder.alone(config, date, weather(date)))
        passThrough(d)
        base = d
        artOn = true
        val lat = config.latitude; val lon = config.longitude
        val sun = if (lat != null && lon != null) SunTimes.compute(date, lat, lon) else null
        light = AloneLight.at(now.toInstant(), sun)
    }

    private fun sample(now: ZonedDateTime, date: LocalDate): JSONObject {
        val d = JSONObject()
        d.put("photo", "${ArtView.ORIGIN}/assets/sample.jpg")
        d.put("focus", "50% 50%")
        d.put("info", InfoBuilder.alone(config, date, null, notSetUp = !config.configured))
        passThrough(d)
        return d
    }

    private fun passThrough(d: JSONObject) {
        config.look?.let { if (!d.has("look")) d.put("look", it) }
        config.screen?.let { if (!d.has("screen")) d.put("screen", it) }
        config.safe?.let { if (!d.has("safe")) d.put("safe", it) }
    }

    private fun weather(date: LocalDate): Weather? {
        val lat = config.latitude ?: return null
        val lon = config.longitude ?: return null
        val unit = if (config.units == "fahrenheit") "F" else "C"
        val f = File(cache, "weather-$date-$unit.json")
        var text = readText(f)
        val t = System.currentTimeMillis()
        if (text == null && t - lastWeatherTry >= 30 * 60_000L) {
            lastWeatherTry = t
            try {
                val u = "https://api.open-meteo.com/v1/forecast?latitude=$lat&longitude=$lon" +
                    "&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=1" +
                    if (unit == "F") "&temperature_unit=fahrenheit" else ""
                text = String(get(u))
                cache.listFiles { x -> x.name.startsWith("weather-") }?.forEach { it.delete() }
                f.writeText(text)
            } catch (e: Exception) {
                lastError = "weather: $e"
            }
        }
        if (text == null) return null
        return try {
            val daily = JSONObject(text).getJSONObject("daily")
            Weather(
                Wmo.text(daily.getJSONArray("weather_code").getInt(0)),
                Math.round(daily.getJSONArray("temperature_2m_max").getDouble(0)).toInt(),
                Math.round(daily.getJSONArray("temperature_2m_min").getDouble(0)).toInt(),
                unit,
            )
        } catch (e: Exception) { null }
    }

    // Shared

    private fun withDrift(b: JSONObject?): JSONObject? {
        if (b == null) return null
        val d = JSONObject(b.toString())
        val oled = config.oled || (d.optJSONObject("screen")?.optBoolean("oled", false) ?: false)
        val (x, y) = if (oled) Drift.forHour(Instant.now().epochSecond / 3600) else 0 to 0
        d.put("drift", JSONObject().put("x", x).put("y", y))
        d.put("light", JSONObject().put("dim", light.first).put("warm", light.second))
        return d
    }

    private fun get(url: String): ByteArray {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 10_000
        c.readTimeout = 10_000
        try {
            if (c.responseCode != 200) throw java.io.IOException("HTTP ${c.responseCode}")
            return c.inputStream.use { it.readBytes() }
        } finally { c.disconnect() }
    }

    private fun writeStatus(data: JSONObject?) {
        try {
            val s = JSONObject()
                .put("mode", if (config.configured && config.mode == "bridge") "bridge" else "alone")
                .put("last_refresh", lastRefresh)
                .put("last_error", lastError ?: JSONObject.NULL)
                .put("photo", data?.optString("photo") ?: JSONObject.NULL)
                .put("bridge_ok", bridgeOk)
            File(root, "status.json").writeText(s.toString())
        } catch (e: Exception) { /* status is a courtesy */ }
    }
}
