#!/bin/bash

# Dependency Checker Script (system package manager hints: pacman / apt / dnf / emerge)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0

# ─── Package manager detection ────────────────────────────────────────────────
PM=""
if   command -v pacman &>/dev/null; then PM="pacman"
elif command -v apt    &>/dev/null; then PM="apt"
elif command -v dnf    &>/dev/null; then PM="dnf"
elif command -v emerge &>/dev/null; then PM="emerge"
fi

# Package names per distro: PKGS["key:pm"]
declare -A PKGS=(
    ["python:pacman"]="python"
    ["python:apt"]="python3"
    ["python:dnf"]="python3"
    ["python:emerge"]="dev-lang/python"

    ["netdiscover:pacman"]="netdiscover"
    ["netdiscover:apt"]="netdiscover"
    ["netdiscover:dnf"]="netdiscover"
    ["netdiscover:emerge"]="net-analyzer/netdiscover"

    ["requests:pacman"]="python-requests"
    ["requests:apt"]="python3-requests"
    ["requests:dnf"]="python3-requests"
    ["requests:emerge"]="dev-python/requests"

    ["bs4:pacman"]="python-beautifulsoup4"
    ["bs4:apt"]="python3-bs4"
    ["bs4:dnf"]="python3-beautifulsoup4"
    ["bs4:emerge"]="dev-python/beautifulsoup4"

    ["rich:pacman"]="python-rich"
    ["rich:apt"]="python3-rich"
    ["rich:dnf"]="python3-rich"
    ["rich:emerge"]="dev-python/rich"

    ["tkinter:pacman"]="tk"
    ["tkinter:apt"]="python3-tk"
    ["tkinter:dnf"]="python3-tkinter"
    ["tkinter:emerge"]="dev-lang/python"

    ["pillow:pacman"]="python-pillow"
    ["pillow:apt"]="python3-pil"
    ["pillow:dnf"]="python3-pillow"
    ["pillow:emerge"]="dev-python/pillow"

    ["metasploit:apt"]="metasploit-framework"
    ["metasploit:emerge"]="net-analyzer/metasploit"
)

# Extra notes where a plain install command isn't the whole story
declare -A NOTES=(
    ["tkinter:emerge"]='enable USE="tk" for dev-lang/python, then re-emerge'
    ["metasploit:pacman"]="not in official repos; use the AUR (metasploit) or BlackArch"
    ["metasploit:dnf"]="not in Fedora repos; use https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html"
)

# Prints an install hint for the given package key
install_hint() {
    local key="$1"

    if [ -z "$PM" ]; then
        echo "install via your package manager (pacman/apt/dnf/emerge) - none detected"
        return
    fi

    local pkg="${PKGS["$key:$PM"]}"
    local note="${NOTES["$key:$PM"]}"

    if [ -z "$pkg" ]; then
        echo "${note:-no package known for $PM}"
        return
    fi

    local cmd
    case "$PM" in
        pacman) cmd="sudo pacman -S $pkg" ;;
        apt)    cmd="sudo apt install $pkg" ;;
        dnf)    cmd="sudo dnf install $pkg" ;;
        emerge) cmd="sudo emerge --ask $pkg" ;;
    esac

    if [ -n "$note" ]; then
        echo "$cmd  ($note)"
    else
        echo "$cmd"
    fi
}

print_header() {
    echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}"
}

check_ok() {
    echo -e "  ${GREEN}[✔]${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "  ${RED}[✘]${NC} $1"
    ((FAIL++))
}

# ─── Package Manager ──────────────────────────────────────────────────────────
print_header "Package Manager"

if [ -n "$PM" ]; then
    check_ok "Detected: $PM"
else
    echo -e "  ${YELLOW}[!]${NC} No supported package manager found (pacman/apt/dnf/emerge)"
fi

# ─── Python Interpreter ───────────────────────────────────────────────────────
print_header "Python Interpreter"

PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
    check_ok "$(python3 --version 2>&1)"
elif command -v python &>/dev/null; then
    PYTHON="python"
    check_ok "$(python --version 2>&1)"
else
    check_fail "No Python interpreter found  →  $(install_hint python)"
fi

# ─── Metasploit ───────────────────────────────────────────────────────────────
print_header "Metasploit Framework"

if command -v msfconsole &>/dev/null; then
    check_ok "msfconsole found: $(msfconsole --version 2>/dev/null | head -1)"
elif [ -f /usr/share/metasploit-framework/msfconsole ]; then
    check_ok "msfconsole found at /usr/share/metasploit-framework/"
elif [ -f /opt/metasploit-framework/bin/msfconsole ]; then
    check_ok "msfconsole found at /opt/metasploit-framework/bin/"
else
    check_fail "msfconsole not found  →  $(install_hint metasploit)"
fi

# ─── Netdiscover ─────────────────────────────────────────────────────────────
print_header "Network Tools"

if command -v netdiscover &>/dev/null; then
    check_ok "netdiscover found"
else
    check_fail "netdiscover not found  →  $(install_hint netdiscover)"
fi

# ─── Third-Party Python Packages ─────────────────────────────────────────────
print_header "Third-Party Python Packages"

# format: "display_name|import_name|package_key"
declare -a PKG_MAP=(
    "requests|requests|requests"
    "BeautifulSoup4|bs4|bs4"
    "rich|rich|rich"
)

if [ -n "$PYTHON" ]; then
    for entry in "${PKG_MAP[@]}"; do
        IFS='|' read -r display import_name pkg_key <<< "$entry"
        if $PYTHON -c "import $import_name" &>/dev/null; then
            VER=$($PYTHON -c "import $import_name; print(getattr($import_name, '__version__', 'unknown'))" 2>/dev/null)
            check_ok "$display v${VER}"
        else
            check_fail "$display not found  →  $(install_hint "$pkg_key")"
        fi
    done
else
    echo -e "  ${YELLOW}[!]${NC} Skipping (no Python interpreter found)"
fi

# ─── tkinter (not bundled on most Linux distros) ──────────────────────────────
print_header "tkinter"

if [ -n "$PYTHON" ]; then
    if $PYTHON -c "import tkinter" &>/dev/null; then
        check_ok "tkinter available"
    else
        check_fail "tkinter not found  →  $(install_hint tkinter)"
    fi
else
    echo -e "  ${YELLOW}[!]${NC} Skipping (no Python interpreter found)"
fi

# ─── PIL / Pillow ─────────────────────────────────────────────────────────────
print_header "PIL / Pillow"

if [ -n "$PYTHON" ]; then
    if $PYTHON -c "from PIL import Image" &>/dev/null; then
        PIL_VER=$($PYTHON -c "import PIL; print(PIL.__version__)" 2>/dev/null)
        check_ok "Pillow v${PIL_VER}"
    else
        check_fail "Pillow not found  →  $(install_hint pillow)"
    fi
else
    echo -e "  ${YELLOW}[!]${NC} Skipping (no Python interpreter found)"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────
print_header "Summary"
echo -e "  ${GREEN}Passed:${NC}  $PASS"
echo -e "  ${RED}Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}All checks passed! ✔${NC}"
else
    echo -e "  ${RED}${BOLD}$FAIL check(s) failed — see above for install hints.${NC}"
fi

echo ""
exit $FAIL
