#!/usr/bin/env bash
# Usage: ./dalfox.sh

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YEL='\033[1;33m'; NC='\033[0m'

# Check dalfox is installed
if ! command -v dalfox &>/dev/null; then
    echo -e "${RED}[!] dalfox not found. Install it:${NC}"
    echo "    go install github.com/hahwul/dalfox/v2@latest"
    exit 1
fi

while true; do
    clear
    echo -e "${CYAN}"
    cat <<'EOF'
   ╔══════════════════════════════════════════════════════════════════════╗
   ║                           DALFOX TUI SCAN                            ║
   ║           dalfox is not made by or maintained by octogon             ║
   ║                           --BeysonSec                                ║
   ╚══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    read -rp "Enter target URL (e.g. https://example.com/search?q=1) or 'q' to quit: " URL

    case "$URL" in
        q|Q|quit|exit) echo -e "${GREEN}[*] Bye.${NC}"; exit 0 ;;
        "") echo -e "${YEL}[!] No URL entered.${NC}"; sleep 2; continue ;;
    esac

    # Basic URL validation
    if [[ ! "$URL" =~ ^https?:// ]]; then
        echo -e "${YEL}[!] URL must start with http:// or https://${NC}"
        sleep 2
        continue
    fi

    echo -e "${GREEN}[*] Starting dalfox scan on: $URL${NC}"
    echo -e "${YEL}[*] Ctrl+C to abort scan.${NC}\n"
    dalfox url "$URL"

    echo -e "\n${GREEN}[*] Scan finished.${NC}"
    read -rp "Scan another target? [y/N]: " AGAIN
    [[ "$AGAIN" =~ ^[Yy]$ ]] || break
done