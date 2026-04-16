#!/usr/bin/env bash
# Generate macOS .icns and web favicons from assets/icon.svg.
#
# Re-run this whenever you edit assets/icon.svg. It produces:
#   - assets/icon.icns         (used by PyInstaller via --icon)
#   - assets/icon-512.png      (canonical hi-res master, useful for README)
#   - frontend/public/favicon.png  (used by index.html)
#
# Tools used: sips + iconutil, both ship with macOS — no Homebrew required.
set -e
cd "$(dirname "$0")/.."

SRC="assets/icon.svg"
ICONSET="assets/icon.iconset"
ICNS="assets/icon.icns"
MASTER_PNG="assets/icon-512.png"
FAVICON="frontend/public/favicon.png"

if [ ! -f "$SRC" ]; then
    echo "ERROR: $SRC not found"
    exit 1
fi

echo "=== Building icons from $SRC ==="

rm -rf "$ICONSET" "$ICNS"
mkdir -p "$ICONSET"

# macOS .icns wants this exact set of sizes / @2x variants.
declare -a SIZES=(
    "16:icon_16x16.png"
    "32:icon_16x16@2x.png"
    "32:icon_32x32.png"
    "64:icon_32x32@2x.png"
    "128:icon_128x128.png"
    "256:icon_128x128@2x.png"
    "256:icon_256x256.png"
    "512:icon_256x256@2x.png"
    "512:icon_512x512.png"
    "1024:icon_512x512@2x.png"
)

for entry in "${SIZES[@]}"; do
    size="${entry%%:*}"
    name="${entry##*:}"
    sips -s format png -Z "$size" "$SRC" --out "$ICONSET/$name" >/dev/null
done

iconutil -c icns "$ICONSET" -o "$ICNS"
echo "  Wrote $ICNS"

mkdir -p "$(dirname "$MASTER_PNG")" "$(dirname "$FAVICON")"
sips -s format png -Z 512 "$SRC" --out "$MASTER_PNG" >/dev/null
sips -s format png -Z 256 "$SRC" --out "$FAVICON" >/dev/null
echo "  Wrote $MASTER_PNG"
echo "  Wrote $FAVICON"

# Clean up the intermediate iconset directory; the .icns is self-contained.
rm -rf "$ICONSET"

echo ""
echo "Done."
