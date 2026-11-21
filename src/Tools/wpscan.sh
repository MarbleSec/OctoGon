#!/usr/bin/env bash
# Usage: ./wpscan.sh

set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YEL='\033[1;33m'; NC='\033[0m'

# Check wpscan is installed
if ! command -v wpscan &>/dev/null; then
    echo -e "${RED}[!] wpscan not found. Install it:${NC}"
    echo "    gem install wpscan"
    exit 1
fi

while true; do
    clear
    echo -e "${CYAN}"
    cat <<'EOF'
   ╔══════════════════════════════════════════════════════════════════════╗
   ║                           WPSCAN TUI SCAN                            ║
   ║           wpscan is not made by or maintained by octogon             ║
   ║                           --BeysonSec                                ║
   ╚══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    read -rp "Enter WordPress target URL (e.g. https://example.com) or 'q' to quit: " URL

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

    # Optional: WPScan API token (needed for vulnerability data) — hidden input
    read -rsp "WPScan API token (leave empty to skip vuln data): " TOKEN
    echo

    read -rp "Run aggressive plugin/theme detection? [y/N]: " AGGR
    DETECT=(--enumerate vp,vt,u,cb)
    [[ "$AGGR" =~ ^[Yy]$ ]] && DETECT=(--enumerate ap,at,cb,dbe,u)

    # Build command as an array (safe with spaces/special chars)
    CMD=(wpscan --url "$URL" --random-user-agent "${DETECT[@]}")
    [[ -n "$TOKEN" ]] && CMD+=(--api-token "$TOKEN")

    # Optional: output file
    read -rp "Save results to file? (path, empty = no): " OUT
    if [[ -n "$OUT" ]]; then
        OUTDIR=$(dirname -- "$OUT")
        mkdir -p -- "$OUTDIR" 2>/dev/null
        CMD+=(--output "$OUT")
    fi

    echo -e "${GREEN}[*] Starting wpscan on: $URL${NC}"
    echo -e "${YEL}[*] Ctrl+C to abort scan.${NC}\n"

    "${CMD[@]}"
    STATUS=$?
    if [[ $STATUS -ne 0 ]]; then
        echo -e "${RED}[!] wpscan exited with status $STATUS${NC}"
    fi

    echo -e "\n${GREEN}[*] Scan finished.${NC}"
    read -rp "Scan another target? [y/N]: " AGAIN
    [[ "$AGAIN" =~ ^[Yy]$ ]] || break
done