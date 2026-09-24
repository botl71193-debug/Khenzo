#!/data/data/com.termux/files/usr/bin/bash
# Khenzo login banner
clear
C_G='\033[1;32m'
C_C='\033[1;36m'
C_R='\033[1;91m'
C_Y='\033[1;33m'
C_D='\033[2m'
C_0='\033[0m'
C_B='\033[1m'

NAME="${KHENZO_NAME:-Khenzo}"
# load saved name
[ -f "$HOME/.khenzo_name" ] && NAME=$(cat "$HOME/.khenzo_name")

echo -e "${C_R}"
cat << 'ART'
              ............
           .............::::...
          ..........:::::::::..
         ........:::::::::::::..
        ......:::::::::::::::::.
       ....::::::::::::::::::::.
      ...:::::::'''::::::::::::.
     ..:::::'     ':::::::::::.
    .::::  ,--.  ::::::::::::.
   .::: ( 00 ) :::::::::::::.
  .::  `--'  ::::::::::::::.
 .:       .::::::::::::::.
  .........::::::::::::::.
          .::::::::::::::.
           .:::::::::::::'
            .::::::::::'
             ':::::::'
               '''''
ART
echo -e "${C_0}"

if command -v figlet >/dev/null 2>&1; then
  if command -v lolcat >/dev/null 2>&1; then
    figlet -f small "$NAME" 2>/dev/null | lolcat
  else
    echo -e "${C_C}${C_B}"
    figlet -f small "$NAME" 2>/dev/null || echo "  $NAME"
    echo -e "${C_0}"
  fi
else
  echo -e "  ${C_C}${C_B}${NAME}${C_0}"
fi

echo -e "  ${C_D}────────────────────────────────────────${C_0}"
echo -e "  ${C_G}OS${C_0}       : Termux $(uname -o 2>/dev/null || echo Android)"
echo -e "  ${C_G}Host${C_0}     : $(uname -n 2>/dev/null)"
echo -e "  ${C_G}Kernel${C_0}   : $(uname -r 2>/dev/null)"
echo -e "  ${C_G}Arch${C_0}     : $(uname -m 2>/dev/null)"
echo -e "  ${C_G}Shell${C_0}    : ${SHELL##*/}"
if [ -f /proc/uptime ]; then
  U=$(awk '{printf "%dd %dh", $1/86400, ($1%86400)/3600}' /proc/uptime)
  echo -e "  ${C_G}Uptime${C_0}   : $U"
fi
echo -e "  ${C_D}────────────────────────────────────────${C_0}"
echo -e "  ${C_Y}Ketik:${C_0}  ${C_C}mmk${C_0}  → jalankan MMK MOD"
echo -e "  ${C_Y}Hapus:${C_0}  ${C_C}bash ~/Khenzo/remove.sh${C_0}"
echo ""
