package app.anytvart

import android.service.dreams.DreamService
import android.view.WindowManager

/** The screensaver. Non-interactive, so any key press ends it. */
class ArtDream : DreamService() {
    private var view: ArtView? = null
    private var controller: ArtController? = null

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        isInteractive = false
        isFullscreen = true
        isScreenBright = true
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        val v = ArtView(this, getExternalFilesDir(null) ?: filesDir)
        view = v
        controller = ArtController(this, v)
        setContentView(v)
    }

    override fun onDreamingStarted() {
        super.onDreamingStarted()
        controller?.start()
    }

    override fun onDreamingStopped() {
        controller?.stop()
        super.onDreamingStopped()
    }

    override fun onDetachedFromWindow() {
        controller?.stop()
        view?.release()
        view = null
        super.onDetachedFromWindow()
    }
}
