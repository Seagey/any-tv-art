plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "app.anytvart"
    compileSdk = 34
    defaultConfig {
        applicationId = "app.anytvart"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
    }
    // Test builds: when ANYTVART_KEYSTORE names a keystore (a debug-style key, alias androiddebugkey,
    // password android), release builds are signed with it. Otherwise the standard debug key is used,
    // the same way couch-tv does it, so one build can update the last.
    val fixedKey = System.getenv("ANYTVART_KEYSTORE")?.let { file(it) }?.takeIf { it.isFile }
    signingConfigs {
        if (fixedKey != null) create("fixed") {
            storeFile = fixedKey
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("fixed") ?: signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/artassets"))
    testOptions { unitTests.isReturnDefaultValues = true }
}

dependencies {
    implementation("androidx.webkit:webkit:1.12.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}

/**
 * The template has one home, picture/template/print.html in the repo root. This copies it, the
 * fonts and one sample photo into the APK's assets, as assets/art/print.html with the fonts beside it
 * in art/fonts, which is where the page's relative font links point. Nothing is checked in twice.
 */
val repoRoot = rootProject.projectDir.resolve("../..")
val bundleArtAssets = tasks.register<Sync>("bundleArtAssets") {
    into(layout.buildDirectory.dir("generated/artassets"))
    from(repoRoot.resolve("picture/template")) { include("print.html"); into("art") }
    from(repoRoot.resolve("anytvart/fonts")) { include("*.ttf"); into("art/fonts") }
    from(repoRoot.resolve("samples/photos/beach.jpg")) { rename { "sample.jpg" } }
}
tasks.configureEach {
    if (name.startsWith("merge") && name.endsWith("Assets")) dependsOn(bundleArtAssets)
    if (name.startsWith("lintVitalAnalyze") || name.startsWith("generate") && name.endsWith("LintVitalReportModel")) dependsOn(bundleArtAssets)
}
