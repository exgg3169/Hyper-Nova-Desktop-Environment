#!/usr/bin/env bash
# Builds the HyperNova OS live ISO on an Arch Linux machine.
#
# It starts from Arch's official "releng" archiso profile, adds the packages in
# packages.x86_64, overlays airootfs/ and installs the HyperNova desktop from
# this checkout into the image.
#
#   sudo pacman -S --needed archiso
#   sudo ./iso/build-iso.sh            # ISO is written to ./out/
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Bu betik root olarak çalıştırılmalı: sudo $0" >&2
    exit 1
fi
if ! command -v mkarchiso >/dev/null; then
    echo "archiso bulunamadı. Kurmak için: pacman -S archiso" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${WORK:-/tmp/hypernova-iso}"
OUT="${OUT:-$ROOT/out}"
PROFILE="$WORK/profile"
AIROOTFS="$PROFILE/airootfs"

rm -rf "$WORK"
mkdir -p "$WORK" "$OUT"
cp -r /usr/share/archiso/configs/releng "$PROFILE"

# Packages and files
grep -v '^\s*#' "$ROOT/iso/packages.x86_64" | grep -v '^\s*$' >> "$PROFILE/packages.x86_64"
cp -a "$ROOT/iso/airootfs/." "$AIROOTFS/"
make -C "$ROOT" DESTDIR="$AIROOTFS" PREFIX=/usr install

# Services: graphical boot, LightDM, NetworkManager and the live user
SYSTEMD="$AIROOTFS/etc/systemd/system"
mkdir -p "$SYSTEMD/multi-user.target.wants"
ln -sf /usr/lib/systemd/system/graphical.target "$SYSTEMD/default.target"
ln -sf /usr/lib/systemd/system/lightdm.service "$SYSTEMD/display-manager.service"
ln -sf /usr/lib/systemd/system/NetworkManager.service "$SYSTEMD/multi-user.target.wants/NetworkManager.service"
ln -sf /etc/systemd/system/hypernova-live-user.service "$SYSTEMD/multi-user.target.wants/hypernova-live-user.service"
# NetworkManager replaces releng's systemd-networkd + iwd setup.
rm -f "$SYSTEMD/multi-user.target.wants/systemd-networkd.service" \
      "$SYSTEMD/multi-user.target.wants/iwd.service" \
      "$SYSTEMD/network-online.target.wants/systemd-networkd-wait-online.service" \
      "$SYSTEMD/sockets.target.wants/systemd-networkd.socket"

# Password-less sudo for the live user
mkdir -p "$AIROOTFS/etc/sudoers.d"
echo "nova ALL=(ALL) NOPASSWD: ALL" > "$AIROOTFS/etc/sudoers.d/10-hypernova-live"

# Branding and permissions
sed -i \
    -e 's/^iso_name=.*/iso_name="hypernova-os"/' \
    -e 's/iso_label="ARCH_/iso_label="HYPERNOVA_/' \
    -e 's/^iso_publisher=.*/iso_publisher="HyperNova OS <https:\/\/github.com\/exgg3169\/Hyper-Nova-Desktop-Environment>"/' \
    -e 's/^iso_application=.*/iso_application="HyperNova OS Live"/' \
    "$PROFILE/profiledef.sh"
cat >> "$PROFILE/profiledef.sh" <<'PERMS'
file_permissions+=(
  ["/usr/local/bin/hypernova-live-user"]="0:0:755"
  ["/usr/bin/hypernova-shell"]="0:0:755"
  ["/usr/bin/hypernova-settings"]="0:0:755"
  ["/usr/bin/hypernova-session"]="0:0:755"
  ["/etc/sudoers.d/10-hypernova-live"]="0:0:440"
)
PERMS

mkarchiso -v -w "$WORK/work" -o "$OUT" "$PROFILE"
echo "Hazır: $(ls -1 "$OUT"/hypernova-os-*.iso | tail -1)"
