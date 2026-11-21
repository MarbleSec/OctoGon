#!/bin/bash
# sqlmap-runner.sh - ensure sqlmap is installed, then launch the GUI
set -u

GRN=$'\e[32m'; YEL=$'\e[33m'; RED=$'\e[31m'; RST=$'\e[0m'
info(){ echo "${GRN}[+]${RST} $*"; }
warn(){ echo "${YEL}[!]${RST} $*"; }
err(){  echo "${RED}[-]${RST} $*" >&2; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then SUDO="sudo"
    else warn "Not root and no sudo - install steps may fail"; fi
fi

have_sqlmap(){ command -v sqlmap >/dev/null 2>&1 && sqlmap --version >/dev/null 2>&1; }
has_gui_flag(){ sqlmap -hh 2>/dev/null | grep -q -- '--gui'; }
has_tkinter(){ python3 -c 'import tkinter' >/dev/null 2>&1; }

install_sqlmap(){
    if command -v apt-get >/dev/null 2>&1; then
        info "Installing via apt (sqlmap + python3-tk)"
        $SUDO apt-get update -y >/dev/null 2>&1
        $SUDO apt-get install -y sqlmap python3-tk && have_sqlmap && return 0
    fi
    if command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y sqlmap python3-tkinter && have_sqlmap && return 0
    fi
    if command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -Sy --noconfirm sqlmap tk && have_sqlmap && return 0
    fi
    if command -v pip3 >/dev/null 2>&1; then
        info "Falling back to pip3"
        $SUDO pip3 install --break-system-packages --upgrade sqlmap 2>/dev/null \
            || $SUDO pip3 install --upgrade sqlmap
        have_sqlmap && return 0
    fi
    if command -v git >/dev/null 2>&1; then
        info "Falling back to git (latest development build)"
        $SUDO rm -rf /opt/sqlmap
        $SUDO git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap || return 1
        $SUDO chmod +x /opt/sqlmap/sqlmap.py
        $SUDO ln -sf /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap
        have_sqlmap && return 0
    fi
    return 1
}

main(){
    echo "[+] Starting SQLMAP SQL INJECTOR"

    if have_sqlmap; then
        info "sqlmap already installed: $(command -v sqlmap)"
        info "Version: $(sqlmap --version 2>/dev/null | head -n1)"
    else
        warn "sqlmap not found - installing"
        install_sqlmap || { err "Installation failed. Install manually: sudo apt install sqlmap"; exit 1; }
        info "Installed: $(command -v sqlmap)"
    fi

    MODE="--gui"

    if ! has_gui_flag; then
        warn "This sqlmap build has no --gui (outdated package) - upgrading from git"
        $SUDO apt-get install -y git >/dev/null 2>&1
        if command -v git >/dev/null 2>&1; then
            $SUDO rm -rf /opt/sqlmap && \
            $SUDO git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap && \
            $SUDO chmod +x /opt/sqlmap/sqlmap.py && \
            $SUDO ln -sf /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap
            has_gui_flag || MODE="--wizard"
        else
            warn "git unavailable - using --wizard instead of --gui"
            MODE="--wizard"
        fi
    fi

    if [ "$MODE" = "--gui" ] && ! has_tkinter; then
        warn "Tkinter missing - installing python3-tk"
        $SUDO apt-get install -y python3-tk >/dev/null 2>&1 \
            || { warn "Could not install python3-tk - falling back to --tui/--wizard"; MODE="--wizard"; }
    fi

    sleep 2
    info "Launching: sqlmap $MODE"
    exec sqlmap "$MODE"
}

main "$@"