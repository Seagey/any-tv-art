package app.anytvart

import org.json.JSONArray
import org.json.JSONObject

/** Settings read from config.json on each start. Missing keys take defaults, bad JSON means "not set up". */
data class Config(
    val configured: Boolean = false,
    val mode: String = "alone",
    val bridgeUrl: String = "",
    val placeName: String = "",
    val latitude: Double? = null,
    val longitude: Double? = null,
    val timezone: String = "",
    val look: JSONObject? = null,
    val screen: JSONObject? = null,
    val safe: JSONObject? = null,
    val quoteLines: List<String> = emptyList(),
    val dateOrder: String = "day-month",
    val units: String = "celsius",
    val oled: Boolean = false,
) {
    companion object {
        fun parse(text: String?): Config {
            if (text.isNullOrBlank()) return Config()
            val o = try { JSONObject(text) } catch (e: Exception) { return Config() }
            val place = o.optJSONObject("place")
            val lines = ArrayList<String>()
            val arr: JSONArray? = o.optJSONArray("quote_lines")
            if (arr != null) for (i in 0 until arr.length()) arr.optString(i, "").trim().takeIf { it.isNotEmpty() }?.let { lines.add(it) }
            val mode = o.optString("mode", "alone").let { if (it == "bridge") "bridge" else "alone" }
            return Config(
                configured = true,
                mode = mode,
                bridgeUrl = o.optString("bridge_url", "").trim().trimEnd('/'),
                placeName = place?.optString("name", "") ?: "",
                latitude = place?.takeIf { it.has("latitude") }?.optDouble("latitude"),
                longitude = place?.takeIf { it.has("longitude") }?.optDouble("longitude"),
                timezone = o.optString("timezone", ""),
                look = o.optJSONObject("look"),
                screen = o.optJSONObject("screen"),
                safe = o.optJSONObject("safe"),
                quoteLines = lines,
                dateOrder = if (o.optString("date_order") == "month-day") "month-day" else "day-month",
                units = if (o.optString("units") == "fahrenheit") "fahrenheit" else "celsius",
                oled = o.optBoolean("oled", false),
            )
        }
    }
}
