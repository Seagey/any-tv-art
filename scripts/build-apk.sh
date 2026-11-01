#!/bin/sh
# Builds the Any TV Art Android TV app (release APK) and prints where it is.
#   dist/any-tv-art.apk
#
# Needs JDK 21 and the Android SDK with platform 34 and build tools 34. Gradle itself is not
# needed: the wrapper (tv/android/gradlew) fetches it.
#
# Usage, from the repo root:
#   [JAVA_HOME=/path/to/jdk-21] [ANDROID_HOME=/path/to/android-sdk] [ANYTVART_KEYSTORE=/path/to/key] sh scripts/build-apk.sh
# Without ANYTVART_KEYSTORE the release is signed with the standard debug key.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)

if [ -z "${ANDROID_HOME:-}" ]; then
  for d in "$HOME/Library/Android/sdk" "$HOME/Android/Sdk" "/opt/android-sdk"; do
    [ -d "$d/platforms" ] && ANDROID_HOME=$d && break
  done
fi
[ -n "${ANDROID_HOME:-}" ] || { echo "Set ANDROID_HOME to your Android SDK."; exit 1; }
[ -d "$ANDROID_HOME/platforms/android-34" ] || { echo "No Android platform 34 in $ANDROID_HOME: sdkmanager \"platforms;android-34\" \"build-tools;34.0.0\""; exit 1; }
export ANDROID_HOME
if [ -z "${JAVA_HOME:-}" ] && [ -x /usr/libexec/java_home ]; then
  JAVA_HOME=$(/usr/libexec/java_home -v 21 2>/dev/null || true)
fi
[ -n "${JAVA_HOME:-}" ] || { echo "Set JAVA_HOME to a JDK 21."; exit 1; }
export JAVA_HOME

[ -f "$ROOT/picture/template/print.html" ] || { echo "picture/template/print.html is missing: the app has nothing to show."; exit 1; }

mkdir -p "$ROOT/dist"
"$ROOT/tv/android/gradlew" -p "$ROOT/tv/android" --no-daemon -q clean assembleRelease
cp "$ROOT/tv/android/app/build/outputs/apk/release/app-release.apk" "$ROOT/dist/any-tv-art.apk"
echo "Built:"
echo "  $ROOT/dist/any-tv-art.apk  sha256 $(shasum -a 256 "$ROOT/dist/any-tv-art.apk" | cut -d' ' -f1)"
