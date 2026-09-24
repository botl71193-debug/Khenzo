#!/data/data/com.termux/files/usr/bin/bash
# Khenzo · pasang style Termux + (opsional) MMK script
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
HOME_TX="${HOME:-/data/data/com.termux/files/home}"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
TERMUX_H="$HOME_TX/.termux"

clear
echo -e "\033[1;32m"
echo "  ╭──────────────────────────────────────╮"
echo "  │     KHENZO · Install Termux Style    │"
echo "  ╰──────────────────────────────────────╯"
echo -e "\033[0m"

# nama banner
read -p "  Nama di banner [Khenzo]: " BNAME
BNAME="${BNAME:-Khenzo}"
echo "$BNAME" > "$HOME_TX/.khenzo_name"

# style colors
mkdir -p "$TERMUX_H"
cp -f "$REPO/style/colors.properties" "$TERMUX_H/colors.properties"
cp -f "$REPO/style/termux.properties" "$TERMUX_H/termux.properties"

# banner ke bashrc
BANNER_LINE="bash $REPO/khenzo-ban.sh"
# backup bashrc
[ -f "$HOME_TX/.bashrc" ] && cp -f "$HOME_TX/.bashrc" "$HOME_TX/.bashrc.khenzo.bak" || touch "$HOME_TX/.bashrc"
# hapus entry lama khenzo
grep -v "khenzo-ban.sh" "$HOME_TX/.bashrc" > "$HOME_TX/.bashrc.tmp" || true
mv "$HOME_TX/.bashrc.tmp" "$HOME_TX/.bashrc"
echo "" >> "$HOME_TX/.bashrc"
echo "# Khenzo Termux Banner" >> "$HOME_TX/.bashrc"
echo "$BANNER_LINE" >> "$HOME_TX/.bashrc"

# copy repo ke ~/Khenzo untuk path stabil
mkdir -p "$HOME_TX/Khenzo"
cp -f "$REPO/khenzo-ban.sh" "$HOME_TX/Khenzo/"
cp -f "$REPO/remove.sh" "$HOME_TX/Khenzo/" 2>/dev/null || true
cp -f "$REPO/requirement.sh" "$HOME_TX/Khenzo/" 2>/dev/null || true
# update bashrc path ke ~/Khenzo
grep -v "khenzo-ban.sh" "$HOME_TX/.bashrc" > "$HOME_TX/.bashrc.tmp" || true
mv "$HOME_TX/.bashrc.tmp" "$HOME_TX/.bashrc"
echo "" >> "$HOME_TX/.bashrc"
echo "# Khenzo Termux Banner" >> "$HOME_TX/.bashrc"
echo "bash $HOME_TX/Khenzo/khenzo-ban.sh" >> "$HOME_TX/.bashrc"

# MMK script jika ada
if [ -f "$REPO/bin/mmk_mods.py" ]; then
  mkdir -p "$HOME_TX/mmk-mod/menu/app" \
           "$HOME_TX/mmk-mod/menu/out/protect" \
           "$HOME_TX/mmk-mod/menu/out/patched" \
           "$HOME_TX/mmk-mod/menu/out/app" \
           "$HOME_TX/mmk-mod/menu/out/injected" \
           "$HOME_TX/mmk-mod/menu/files"
  cp -f "$REPO/bin/mmk_mods.py" "$HOME_TX/mmk-mod/mmk_mods.py"
  cat > "$PREFIX/bin/mmk" << LAUNCH
#!/data/data/com.termux/files/usr/bin/bash
export MMK_ROOT="$HOME_TX/mmk-mod/menu"
cd "$HOME_TX/mmk-mod"
exec python3 "$HOME_TX/mmk-mod/mmk_mods.py" "\$@"
LAUNCH
  chmod +x "$PREFIX/bin/mmk" "$HOME_TX/mmk-mod/mmk_mods.py"
  echo -e "  \033[1;32m✔ MMK script → mmk\033[0m"
fi

if command -v termux-reload-settings >/dev/null 2>&1; then
  termux-reload-settings 2>/dev/null || true
fi

echo ""
echo -e "  \033[1;32m✔ Warna     : ~/.termux/colors.properties\033[0m"
echo -e "  \033[1;32m✔ Banner    : tiap buka Termux\033[0m"
echo -e "  \033[1;32m✔ Nama      : $BNAME\033[0m"
echo -e "  \033[1;33m  Restart Termux atau: source ~/.bashrc\033[0m"
echo ""
