#!/usr/bin/env bash
# =====================================================================
#  Terminal con estilo DevRootDark
#  Uso (en el servidor):  bash scripts/terminal-devrootdark.sh
#  Quitarlo:              bash scripts/terminal-devrootdark.sh --quitar
# =====================================================================
set -e
BANNER=/etc/profile.d/zz-devrootdark.sh
MARCA_INI="# >>> devrootdark prompt >>>"
MARCA_FIN="# <<< devrootdark prompt <<<"

quitar_prompt() {
  [ -f "$HOME/.bashrc" ] && sed -i "/$MARCA_INI/,/$MARCA_FIN/d" "$HOME/.bashrc"
}

if [ "${1:-}" = "--quitar" ]; then
  sudo rm -f "$BANNER"
  quitar_prompt
  rm -f "$HOME/.hushlogin"
  echo "Listo: se quitó el estilo DevRootDark. Abre una nueva sesión."
  exit 0
fi

# ---------------------------------------------------------------------
# 1) Pantalla de bienvenida (se muestra al entrar por SSH o desde el navegador)
# ---------------------------------------------------------------------
sudo tee "$BANNER" > /dev/null <<'EOF'
# Bienvenida DevRootDark (instalado por scripts/terminal-devrootdark.sh)
case $- in *i*) ;; *) return 0 2>/dev/null || exit 0 ;; esac
[ -n "$DEVROOTDARK_BANNER" ] && return 0
export DEVROOTDARK_BANNER=1

_drd() {
  local B='\033[38;2;245;246;250m' V='\033[38;2;140;240;90m' T='\033[38;2;46;230;199m'
  local G='\033[38;2;150;155;185m' N='\033[1m' R='\033[0m' ROJO='\033[38;2;255;95;95m'
  local cols; cols=$(tput cols 2>/dev/null || echo 80)

  local f=(
"     ●        "
"  ╭──┴──╮     "
"╺┫│ ▀ ▀ │┣╸   "
"  │  #  │     "
" ━┥     ┝━    "
"  ╰╯╲╱╲╱╰╯    "
  )
  local d=( "██████╗ ███████╗██╗   ██╗" "██╔══██╗██╔════╝██║   ██║" "██║  ██║█████╗  ██║   ██║" "██║  ██║██╔══╝  ╚██╗ ██╔╝" "██████╔╝███████╗ ╚████╔╝ " "╚═════╝ ╚══════╝  ╚═══╝  " )
  local r=( "██████╗  ██████╗  ██████╗ ████████╗" "██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝" "██████╔╝██║   ██║██║   ██║   ██║   " "██╔══██╗██║   ██║██║   ██║   ██║   " "██║  ██║╚██████╔╝╚██████╔╝   ██║   " "╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   " )
  local k=( "██████╗  █████╗ ██████╗ ██╗  ██╗" "██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝" "██║  ██║███████║██████╔╝█████╔╝ " "██║  ██║██╔══██║██╔══██╗██╔═██╗ " "██████╔╝██║  ██║██║  ██║██║  ██╗" "╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝" )
  local sd=( " ___  _____   __" "|   \\| __\\ \\ / /" "| |) | _| \\ V / " "|___/|___| \\_/  " )
  local sr=( " ___  ___   ___ _____ " "| _ \\/ _ \\ / _ \\_   _|" "|   / (_) | (_) || |  " "|_|_\\\\___/ \\___/ |_|  " )
  local sk=( " ___   _   ___ _  __" "|   \\ /_\\ | _ \\ |/ /" "| |) / _ \\|   / ' < " "|___/_/ \\_\\_|_\\_|\\_\\" )

  echo
  local i
  if [ "$cols" -ge 108 ]; then
    for i in 0 1 2 3 4 5; do printf "  ${T}%s${B}%s${V}%s${T}%s${R}\n" "${f[$i]}" "${d[$i]}" "${r[$i]}" "${k[$i]}"; done
  elif [ "$cols" -ge 74 ]; then
    for i in 0 1 2 3 4 5; do
      if [ "$i" -ge 1 ] && [ "$i" -le 4 ]; then j=$((i-1)); printf "  ${T}%s${N}${B}%s${V}%s${T}%s${R}\n" "${f[$i]}" "${sd[$j]}" "${sr[$j]}" "${sk[$j]}"
      else printf "  ${T}%s${R}\n" "${f[$i]}"; fi
    done
  else
    for i in 0 1 2 3; do printf "${N}${B}%s${V}%s${R}\n" "${sd[$i]}" "${sr[$i]}"; done
    for i in 0 1 2 3; do printf "${N}${T}%s${R}\n" "${sk[$i]}"; done
  fi
  if [ "$cols" -ge 74 ]; then
    printf "  ${G}> A P R E N D E   A   P R O G R A M A R   D E S D E   L A   R A Í Z_${R}\n\n"
  else
    printf "${G}> Aprende a programar desde la raíz_${R}\n\n"
  fi

  # ---- Estado del servidor ----
  local api tsurl tsip lan up disco ram
  if systemctl is-active --quiet apidevrootdark 2>/dev/null; then api="${V}● en línea${R}"; else api="${ROJO}● detenida${R}"; fi
  tsurl=$(tailscale status --json 2>/dev/null | grep -m1 '"DNSName"' | sed -E 's/.*"DNSName": *"([^"]*)\.?".*/\1/' | sed 's/\.$//')
  tsip=$(tailscale ip -4 2>/dev/null | head -n1)
  lan=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^(192\.168|10\.|172\.)' | head -n1)
  up=$(uptime -p 2>/dev/null | sed 's/^up //')
  disco=$(df -h / 2>/dev/null | awk 'NR==2{print $3" de "$2" ("$5")"}')
  ram=$(free -h 2>/dev/null | awk '/^Mem|^Mem\.|^Memoria/{print $3" de "$2; exit}')

  printf "  ${T}API${R}          %b\n" "$api"
  [ -n "$tsurl" ] && printf "  ${T}URL pública${R}  ${B}https://%s${R}\n" "$tsurl"
  printf "  ${T}Tailscale${R}    %s   ${T}Red local${R}  %s\n" "${tsip:-—}" "${lan:-sin red}"
  printf "  ${T}Encendido${R}    %s\n" "${up:-—}"
  printf "  ${T}Disco${R}        %s   ${T}RAM${R}  %s\n" "${disco:-—}" "${ram:-—}"
  echo
}
_drd
unset -f _drd
EOF
sudo chmod 644 "$BANNER"

# Ocultar los mensajes largos de Ubuntu al entrar (solo para este usuario)
touch "$HOME/.hushlogin"

# ---------------------------------------------------------------------
# 2) Prompt de colores DevRootDark
# ---------------------------------------------------------------------
quitar_prompt
cat >> "$HOME/.bashrc" <<'EOF'
# >>> devrootdark prompt >>>
__drd_git() { local b; b=$(git symbolic-ref --short HEAD 2>/dev/null) && printf ' \001\033[38;2;140;240;90m\002 ⎇ %s' "$b"; }
__drd_venv() { [ -n "$VIRTUAL_ENV" ] && printf '\001\033[38;2;150;155;185m\002(venv) '; }
PS1='\n\[\033[38;2;46;230;199m\]╭─ $(__drd_venv)\[\033[1;38;2;245;246;250m\]\u\[\033[0;38;2;150;155;185m\]@\[\033[38;2;46;230;199m\]devrootdark \[\033[38;2;245;246;250m\]\w$(__drd_git)\[\033[0m\]\n\[\033[38;2;46;230;199m\]╰─\[\033[1;38;2;140;240;90m\]❯\[\033[0m\] '
VIRTUAL_ENV_DISABLE_PROMPT=1
alias api-estado='systemctl status apidevrootdark --no-pager'
alias api-logs='sudo journalctl -u apidevrootdark -f'
alias api-reiniciar='sudo systemctl restart apidevrootdark && systemctl is-active apidevrootdark'
bienvenida() { (unset DEVROOTDARK_BANNER; . /etc/profile.d/zz-devrootdark.sh); }
# <<< devrootdark prompt <<<
EOF

echo
echo "✔ Terminal DevRootDark instalada."
echo "  Cierra la sesión y vuelve a entrar (o escribe: exec bash -l) para verla."
echo "  Comandos nuevos: api-estado, api-logs, api-reiniciar, bienvenida"
