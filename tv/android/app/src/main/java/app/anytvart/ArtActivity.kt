package app.anytvart

import android.app.Activity
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.view.WindowManager

/** The same picture as a normal screen. Any key press leaves it. */
class ArtActivity : Activity() {
    private var view: ArtView? = null
    private var controller: ArtController? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        val v = ArtView(this, getExternalFilesDir(null) ?: filesDir)
        view = v
        controller = ArtController(this, v)
        setContentView(v)
    }

    override fun onResume() {
        super.onResume()
        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        controller?.start()
    }

    override fun onPause() {
        controller?.stop()
        super.onPause()
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (event.action == KeyEvent.ACTION_DOWN) { finish(); return true }
        return super.dispatchKeyEvent(event)
    }

    override fun onDestroy() {
        view?.release()
        view = null
        super.onDestroy()
    }
}
