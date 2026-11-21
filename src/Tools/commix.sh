#!/bin/bash
# commix-runner.sh - ensure commix is installed, then launch the wizard
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

have_commix(){ command -v commix >/dev/null 2>&1 && commix --version >/dev/null 2>&1; }
has_wizard_flag(){ commix -h 2>/dev/null | grep -q -- '--wizard'; }

install_commix(){
    if command -v apt-get >/dev/null 2>&1; then
        info "Installing via apt (commix)"
        $SUDO apt-get update -y >/dev/null 2>&1
        $SUDO apt-get install -y commix && have_commix && return 0
    fi
    if command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y commix && have_commix && return 0
    fi
    if command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -Sy --noconfirm commix && have_commix && return 0
    fi
    if command -v git >/dev/null 2>&1; then
        info "Falling back to git (latest development build)"
        $SUDO rm -rf /opt/commix
        $SUDO git clone --depth 1 https://github.com/commixproject/commix.git /opt/commix || return 1
        $SUDO chmod +x /opt/commix/commix.py
        $SUDO ln -sf /opt/commix/commix.py /usr/local/bin/commix
        have_commix && return 0
    fi
    return 1
}

upgrade_from_git(){
    $SUDO apt-get install -y git >/dev/null 2>&1
    command -v git >/dev/null 2>&1 || return 1
    $SUDO rm -rf /opt/commix && \
    $SUDO git clone --depth 1 https://github.com/commixproject/commix.git /opt/commix && \
    $SUDO chmod +x /opt/commix/commix.py && \
    $SUDO ln -sf /opt/commix/commix.py /usr/local/bin/commix
}

main(){
    echo "[+] Starting COMMIX OS COMMAND INJECTOR"

    if have_commix; then
        info "commix already installed: $(command -v commix)"
        info "Version: $(commix --version 2>/dev/null | head -n1)"
    else
        warn "commix not found - installing"
        install_commix || { err "Installation failed. Install manually: sudo apt install commix"; exit 1; }
        info "Installed: $(command -v commix)"
    fi

    MODE="--wizard"

    if ! has_wizard_flag; then
        warn "This commix build has no --wizard (outdated package) - upgrading from git"
        if upgrade_from_git; then
            has_wizard_flag || { err "Upgraded build still lacks --wizard"; exit 1; }
        else
            err "git unavailable - cannot upgrade. Install manually from https://github.com/commixproject/commix"
            exit 1
        fi
    fi

    sleep 2
    info "Launching: commix $MODE"
    exec commix "$MODE"
}

main "$@"