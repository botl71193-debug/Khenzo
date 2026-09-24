#!/data/data/com.termux/files/usr/bin/bash
# KHENZO · Termux Style — requirements
clear
echo -e "\033[1;32m"
echo "  ╔══════════════════════════════════════╗"
echo "  ║     KHENZO · Termux Style Setup      ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "\033[0m"

pkg update -y
pkg upgrade -y
pkg install -y figlet toilet cowsay nano ruby python git wget curl unzip zip openjdk-17 2>/dev/null || true
# lolcat via gem (opsional)
if command -v gem >/dev/null 2>&1; then
  gem install lolcat 2>/dev/null || true
fi

echo ""
echo -e "\033[1;32m  ✔ Dependensi siap\033[0m"
echo -e "\033[1;33m  Selanjutnya: bash install.sh\033[0m"
echo ""
