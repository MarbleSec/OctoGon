#!/usr/bin/env bash
#
# netdiscover-tui.sh — a dialog-based TUI wrapper around netdiscover
#
# Requirements: bash, dialog, netdiscover, root privileges (for raw sockets)

set -euo pipefail

TMPDIR=$(mktemp -d /tmp/netdiscover-tui.XXXXXX)
RESULTS_FILE="$TMPDIR/results.txt"
trap 'rm -rf "$TMPDIR"' EXIT

DIALOG_HEIGHT=20
DIALOG_WIDTH=70

# ---------- sanity checks ----------

check_deps() {
    local missing=()
    for cmd in dialog netdiscover; do
        command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
    done
    if [ "${#missing[@]}" -ne 0 ]; then
        echo "Missing required command(s): ${missing[*]}" >&2
        echo "Install them (e.g. 'sudo apt install dialog netdiscover') and re-run." >&2
        exit 1
    fi
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "netdiscover needs raw socket access. Re-run with sudo." >&2
        exit 1
    fi
}

# ---------- UI helpers ----------

msg() {
    dialog --title "${2:-Notice}" --msgbox "$1" "$DIALOG_HEIGHT" "$DIALOG_WIDTH"
}

list_interfaces() {
    # Prefer `ip`, fall back to `ifconfig`
    if command -v ip >/dev/null 2>&1; then
        ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$'
    else
        ifconfig -a | awk '/^[a-zA-Z0-9]/{print $1}' | sed 's/://' | grep -v '^lo$'
    fi
}

choose_interface() {
    local ifaces=()
    while IFS= read -r iface; do
        [ -n "$iface" ] && ifaces+=("$iface" "")
    done < <(list_interfaces)

    if [ "${#ifaces[@]}" -eq 0 ]; then
        msg "No network interfaces found." "Error"
        exit 1
    fi

    dialog --title "Select Interface" \
        --menu "Choose a network interface to scan on:" \
        "$DIALOG_HEIGHT" "$DIALOG_WIDTH" 10 \
        "${ifaces[@]}" \
        3>&1 1>&2 2>&3
}

choose_mode() {
    dialog --title "Scan Mode" \
        --menu "Choose scan mode:" \
        "$DIALOG_HEIGHT" "$DIALOG_WIDTH" 4 \
        "active"  "Send ARP requests (default, faster)" \
        "passive" "Listen only, no packets sent (stealthy, slower)" \
        3>&1 1>&2 2>&3
}

choose_range() {
    dialog --title "IP Range (optional)" \
        --inputbox "Enter an IP range/CIDR to scan, or leave blank for auto:\n(e.g. 192.168.1.0/24)" \
        "$DIALOG_HEIGHT" "$DIALOG_WIDTH" \
        3>&1 1>&2 2>&3
}

choose_duration() {
    dialog --title "Scan Duration" \
        --inputbox "Scan time in seconds (blank = run until Ctrl+C-equivalent / default sleep):" \
        "$DIALOG_HEIGHT" "$DIALOG_WIDTH" "30" \
        3>&1 1>&2 2>&3
}

# ---------- core scan ----------

run_scan() {
    local iface="$1" mode="$2" range="$3" duration="$4"
    local args=(-i "$iface" -P)   # -P: print results and exit (parseable), no ncurses UI

    [ "$mode" = "passive" ] && args+=(-p)
    [ -n "$range" ] && args+=(-r "$range")

    : > "$RESULTS_FILE"

    # Run netdiscover in background, capture output, respect duration via timeout
    if [ -n "$duration" ]; then
        timeout "${duration}s" netdiscover "${args[@]}" > "$RESULTS_FILE" 2>&1 || true
    else
        netdiscover "${args[@]}" > "$RESULTS_FILE" 2>&1 || true
    fi
}

scan_with_progress() {
    local iface="$1" mode="$2" range="$3" duration="$4"

    (
        echo 10 ; echo "XXX" ; echo "Starting netdiscover on $iface..." ; echo "XXX"
        run_scan "$iface" "$mode" "$range" "$duration" &
        local pid=$!
        local pct=10
        while kill -0 "$pid" 2>/dev/null; do
            sleep 1
            pct=$(( pct < 90 ? pct + 5 : 90 ))
            echo "$pct" ; echo "XXX" ; echo "Scanning... (PID $pid)" ; echo "XXX"
        done
        wait "$pid" 2>/dev/null || true
        echo 100 ; echo "XXX" ; echo "Scan complete." ; echo "XXX"
    ) | dialog --title "Scanning" --gauge "Initializing..." 10 "$DIALOG_WIDTH" 0
}

view_results() {
    if [ ! -s "$RESULTS_FILE" ]; then
        msg "No results yet. Run a scan first." "Results"
        return
    fi
    dialog --title "Scan Results" --textbox "$RESULTS_FILE" "$DIALOG_HEIGHT" "$DIALOG_WIDTH"
}

save_results() {
    if [ ! -s "$RESULTS_FILE" ]; then
        msg "No results to save. Run a scan first." "Save"
        return
    fi
    local dest
    dest=$(dialog --title "Save Results" \
        --inputbox "Save results to path:" \
        "$DIALOG_HEIGHT" "$DIALOG_WIDTH" "$HOME/netdiscover-results.txt" \
        3>&1 1>&2 2>&3) || return
    [ -n "$dest" ] && cp "$RESULTS_FILE" "$dest" && msg "Saved to $dest" "Save"
}

# ---------- main menu ----------

main_menu() {
    local iface="" mode="active" range="" duration="30"

    while true; do
        local choice
        choice=$(dialog --title "netdiscover TUI" \
            --menu "Interface: ${iface:-<none>}   Mode: $mode   Range: ${range:-auto}" \
            "$DIALOG_HEIGHT" "$DIALOG_WIDTH" 8 \
            1 "Select interface" \
            2 "Select mode (active/passive)" \
            3 "Set IP range (optional)" \
            4 "Set scan duration" \
            5 "Run scan" \
            6 "View last results" \
            7 "Save last results" \
            8 "Quit" \
            3>&1 1>&2 2>&3) || break

        case "$choice" in
            1) iface=$(choose_interface) || true ;;
            2) mode=$(choose_mode) || true ;;
            3) range=$(choose_range) || true ;;
            4) duration=$(choose_duration) || true ;;
            5)
                if [ -z "$iface" ]; then
                    msg "Select an interface first." "Error"
                else
                    scan_with_progress "$iface" "$mode" "$range" "$duration"
                    view_results
                fi
                ;;
            6) view_results ;;
            7) save_results ;;
            8) break ;;
        esac
    done
}

# ---------- entry point ----------

check_deps
check_root
main_menu
clear
