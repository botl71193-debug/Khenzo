#!/data/data/com.termux/files/usr/bin/bash
# Khenzo · hapus banner & kembalikan bashrc
HOME_TX="${HOME:-/data/data/com.termux/files/home}"
if [ -f "$HOME_TX/.bashrc.khenzo.bak" ]; then
  cp -f "$HOME_TX/.bashrc.khenzo.bak" "$HOME_TX/.bashrc"
  echo "  ✔ bashrc dipulihkan dari backup"
else
  if [ -f "$HOME_TX/.bashrc" ]; then
    grep -v "khenzo-ban.sh" "$HOME_TX/.bashrc" | grep -v "Khenzo Termux Banner" > "$HOME_TX/.bashrc.tmp" || true
    mv "$HOME_TX/.bashrc.tmp" "$HOME_TX/.bashrc"
    echo "  ✔ baris banner dihapus dari bashrc"
  fi
fi
rm -f "$HOME_TX/.khenzo_name"
echo "  ✔ Khenzo banner dihapus. Restart Termux."
