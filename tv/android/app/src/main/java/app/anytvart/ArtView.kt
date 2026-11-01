package app.anytvart

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.view.View
import android.webkit.MimeTypeMap
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import androidx.webkit.WebViewAssetLoader
import java.io.File
import java.io.FileInputStream

/** Serves the app's files dir under /files/, which the stock handlers cannot do for the external dir. */
class FilesHandler(private val root: File) : WebViewAssetLoader.PathHandler {
    override fun handle(path: String): WebResourceResponse? {
        val f = File(root, path).canonicalFile
        val base = root.canonicalFile.path + File.separator
        if (!f.path.startsWith(base) || !f.isFile) return null
        val ext = f.extension.lowercase()
        val mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) ?: "application/octet-stream"
        return WebResourceResponse(mime, null, FileInputStream(f))
    }
}

/** The one view both the dream and the activity host: the print template in a WebView, plus a black cover for the night cut-off. */
@SuppressLint("SetJavaScriptEnabled")
class ArtView(context: Context, filesRoot: File) : FrameLayout(context) {
    companion object {
        const val ORIGIN = "https://appassets.androidplatform.net"
        const val PAGE = "$ORIGIN/assets/art/print.html"
        const val FILES = "$ORIGIN/files/"
        const val HOST = "appassets.androidplatform.net"
    }

    private val web = WebView(context)
    private val cover = View(context)
    private var loaded = false
    private var pendingJson: String? = null
    private var light = "{dim:0,warm:0}"

    private val loader = WebViewAssetLoader.Builder()
        .setDomain(HOST)
        .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(context))
        .addPathHandler("/files/", FilesHandler(filesRoot))
        .build()

    init {
        setBackgroundColor(Color.BLACK)
        web.setBackgroundColor(Color.BLACK)
        web.isFocusable = false
        web.settings.javaScriptEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = false
        web.settings.mediaPlaybackRequiresUserGesture = true
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                loader.shouldInterceptRequest(request.url)?.let { return it }
                // Nothing but our own origin ever loads in the page.
                return WebResourceResponse("text/plain", "utf-8", 403, "Blocked", emptyMap(), null)
            }
            override fun onPageFinished(view: WebView, url: String) {
                loaded = true
                flush()
            }
        }
        addView(web, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        cover.setBackgroundColor(Color.BLACK)
        cover.visibility = View.GONE
        addView(cover, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        web.loadUrl(PAGE)
    }

    private fun flush() {
        val j = pendingJson ?: return
        web.evaluateJavascript("setLight($light)", null)
        web.evaluateJavascript("render($j)", null)
    }

    fun render(json: String) {
        pendingJson = json
        if (loaded) flush()
    }

    fun setLight(dim: Double, warm: Double) {
        light = "{dim:$dim,warm:$warm}"
        if (loaded) web.evaluateJavascript("setLight($light)", null)
    }

    fun setBlack(black: Boolean) {
        cover.visibility = if (black) View.VISIBLE else View.GONE
    }

    fun release() {
        web.stopLoading()
        removeAllViews()
        web.destroy()
    }
}
