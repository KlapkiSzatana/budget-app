#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT_DIR/app"
BUILD_DIR="$ROOT_DIR/build/manual"
OUT_DIR="$ROOT_DIR/build/outputs/apk/debug"
PACKAGE_NAME="pl.klapkiszatana.budgetmobile"
MIN_SDK=29
TARGET_SDK=35
VERSION_CODE=1235
VERSION_NAME="1.3.5"

find_jdk_bin() {
    if [[ -n "${JAVA_HOME:-}" && -x "$JAVA_HOME/bin/javac" ]]; then
        printf '%s\n' "$JAVA_HOME/bin"
        return 0
    fi

    for candidate in /tmp/budget-android-root/usr/lib/jvm/java-17-openjdk/bin /usr/lib/jvm/default/bin /usr/lib/jvm/java-17-openjdk/bin; do
        if [[ -x "$candidate/javac" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

find_sdk() {
    for candidate in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}" "$ROOT_DIR/android-sdk" "$HOME/Android/Sdk" /tmp/budget-android-root/opt/android-sdk /opt/android-sdk /usr/lib/android-sdk; do
        if [[ -n "$candidate" && -d "$candidate/platforms" && -d "$candidate/build-tools" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

SDK_DIR="$(find_sdk)" || {
    echo "Nie znaleziono Android SDK. Ustaw ANDROID_HOME albo zainstaluj android-sdk/android-platform/android-sdk-build-tools." >&2
    exit 1
}

if ! command -v javac >/dev/null 2>&1; then
    JDK_BIN="$(find_jdk_bin)" || {
        echo "Brak JDK. Ustaw JAVA_HOME albo zainstaluj pakiet JDK z javac." >&2
        exit 1
    }
    export PATH="$JDK_BIN:$PATH"
fi

ANDROID_JAR="$(find "$SDK_DIR/platforms" -maxdepth 2 -name android.jar | sort -V | tail -n 1)"
BUILD_TOOLS="$(find "$SDK_DIR/build-tools" -maxdepth 1 -mindepth 1 -type d | sort -V | tail -n 1)"

AAPT2="$BUILD_TOOLS/aapt2"
D8="$BUILD_TOOLS/d8"
ZIPALIGN="$BUILD_TOOLS/zipalign"
APKSIGNER="$BUILD_TOOLS/apksigner"

for tool in javac keytool jar "$AAPT2" "$D8" "$ZIPALIGN" "$APKSIGNER"; do
    if ! command -v "$tool" >/dev/null 2>&1 && [[ ! -x "$tool" ]]; then
        echo "Brak narzędzia: $tool" >&2
        exit 1
    fi
done

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/compiled" "$BUILD_DIR/generated" "$BUILD_DIR/classes" "$BUILD_DIR/dex" "$OUT_DIR"

MANIFEST="$BUILD_DIR/AndroidManifest.xml"
sed "s|<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">|<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\" package=\"$PACKAGE_NAME\">|" \
    "$APP_DIR/src/main/AndroidManifest.xml" > "$MANIFEST"

"$AAPT2" compile --dir "$APP_DIR/src/main/res" -o "$BUILD_DIR/compiled/res.zip"
"$AAPT2" link \
    -o "$BUILD_DIR/resources.apk" \
    -I "$ANDROID_JAR" \
    --manifest "$MANIFEST" \
    --java "$BUILD_DIR/generated" \
    --min-sdk-version "$MIN_SDK" \
    --target-sdk-version "$TARGET_SDK" \
    --version-code "$VERSION_CODE" \
    --version-name "$VERSION_NAME" \
    --auto-add-overlay \
    "$BUILD_DIR/compiled/res.zip"

mapfile -t JAVA_SOURCES < <(find "$APP_DIR/src/main/java" "$BUILD_DIR/generated" -name '*.java' | sort)
javac --release 17 -classpath "$ANDROID_JAR" -d "$BUILD_DIR/classes" "${JAVA_SOURCES[@]}"

(cd "$BUILD_DIR/classes" && jar cf "$BUILD_DIR/classes.jar" .)
"$D8" --lib "$ANDROID_JAR" --min-api "$MIN_SDK" --output "$BUILD_DIR/dex" "$BUILD_DIR/classes.jar"
cp "$BUILD_DIR/resources.apk" "$BUILD_DIR/unsigned.apk"
(cd "$BUILD_DIR/dex" && jar uf "$BUILD_DIR/unsigned.apk" classes.dex)

"$ZIPALIGN" -f 4 "$BUILD_DIR/unsigned.apk" "$BUILD_DIR/aligned.apk"

KEYSTORE="$ROOT_DIR/build/debug.keystore"
if [[ ! -f "$KEYSTORE" ]]; then
    keytool -genkeypair \
        -keystore "$KEYSTORE" \
        -storepass android \
        -keypass android \
        -alias androiddebugkey \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -dname "CN=Android Debug,O=Android,C=US" \
        >/dev/null
fi

"$APKSIGNER" sign \
    --ks "$KEYSTORE" \
    --ks-pass pass:android \
    --key-pass pass:android \
    --out "$OUT_DIR/budgetapp-mobile.apk" \
    "$BUILD_DIR/aligned.apk"

"$APKSIGNER" verify "$OUT_DIR/budgetapp-mobile.apk"
echo "$OUT_DIR/budgetapp-mobile.apk"
