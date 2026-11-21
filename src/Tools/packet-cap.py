#!/usr/bin/env python3
"""
tshark_tui.py - a very simple TUI wrapper around tshark.

Requires:
    - Python 3 with the standard 'curses' module (included on Linux/Arch)
    - tshark installed (Arch: sudo pacman -S wireshark-cli)
    - Capturing live traffic normally needs root, or a user in the
      'wireshark' group with dumpcap capabilities set
      (Arch: sudo gpasswd -a $USER wireshark, then log out/in).

Run it with:
    python3 tshark_tui.py
"""

import curses
import os
import shutil
import subprocess
import sys
import threading
import time
from collections import deque

TSHARK = shutil.which("tshark")

RAINBOW = [
    curses.COLOR_RED,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
]

BANNER_LINES = [
    "   ~ ~ ~    T S H A R K   T U I    ~ ~ ~   ",
    " (( ( (  o            tshark wrapper  o ) ) )) ",
]


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    # Pair 0 reserved. Pairs 1..6 are the rainbow colors, used only
    # for the banner. Pair 10 is plain default-on-default text.
    for i, color in enumerate(RAINBOW, start=1):
        curses.init_pair(i, color, -1)
    curses.init_pair(10, -1, -1)


def draw_banner(stdscr, top=1):
    _, width = stdscr.getmaxyx()
    for row, line in enumerate(BANNER_LINES):
        x = max((width - len(line)) // 2, 0)
        for i, ch in enumerate(line):
            pair = (i % len(RAINBOW)) + 1
            try:
                stdscr.addstr(top + row, x + i, ch,
                              curses.color_pair(pair) | curses.A_BOLD)
            except curses.error:
                pass


def draw_status(stdscr, text):
    height, width = stdscr.getmaxyx()
    text = text[: max(width - 1, 0)]
    try:
        stdscr.addstr(height - 1, 0, text.ljust(width - 1),
                       curses.color_pair(10) | curses.A_REVERSE)
    except curses.error:
        pass


def menu(stdscr, title, options):
    """Simple up/down/enter menu. Returns selected index or None if cancelled."""
    idx = 0
    while True:
        stdscr.erase()
        draw_banner(stdscr)
        height, width = stdscr.getmaxyx()
        y = 4
        stdscr.addstr(y, 2, title, curses.color_pair(10) | curses.A_BOLD)
        y += 2
        for i, opt in enumerate(options):
            marker = "> " if i == idx else "  "
            attr = curses.color_pair(10)
            if i == idx:
                attr |= curses.A_REVERSE
            try:
                stdscr.addstr(y + i, 4, f"{marker}{opt}", attr)
            except curses.error:
                pass
        draw_status(stdscr, "Up/Down: move   Enter: select   q: quit")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            return idx
        elif key in (ord("q"), 27):
            return None


def prompt(stdscr, label, default=""):
    """Prompt the user for a line of text on the status line."""
    curses.echo()
    curses.curs_set(1)
    height, width = stdscr.getmaxyx()
    stdscr.move(height - 1, 0)
    stdscr.clrtoeol()
    text = f"{label}"
    if default:
        text += f" [{default}]"
    text += ": "
    try:
        stdscr.addstr(height - 1, 0, text, curses.color_pair(10))
    except curses.error:
        pass
    stdscr.refresh()
    try:
        raw = stdscr.getstr(height - 1, len(text), width - len(text) - 1)
        value = raw.decode("utf-8").strip()
    except Exception:
        value = ""
    curses.noecho()
    curses.curs_set(0)
    return value if value else default


def pager(stdscr, lines, title):
    """Scroll through a fixed list of lines with up/down/pgup/pgdn/q."""
    top = 0
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        body_height = height - 3
        stdscr.addstr(0, 2, title, curses.color_pair(10) | curses.A_BOLD)
        for i in range(body_height):
            li = top + i
            if li >= len(lines):
                break
            try:
                stdscr.addstr(2 + i, 0, lines[li][: width - 1],
                               curses.color_pair(10))
            except curses.error:
                pass
        draw_status(stdscr, f"Line {top+1}/{max(len(lines),1)}  "
                             f"Up/Down/PgUp/PgDn: scroll   q: back")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            top = max(0, top - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            top = min(max(0, len(lines) - body_height), top + 1)
        elif key == curses.KEY_PPAGE:
            top = max(0, top - body_height)
        elif key == curses.KEY_NPAGE:
            top = min(max(0, len(lines) - body_height), top + body_height)
        elif key in (ord("q"), 27):
            return


def list_interfaces():
    """Return a list of (number, name) from `tshark -D`."""
    result = subprocess.run([TSHARK, "-D"], capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "." in line:
            num, rest = line.split(".", 1)
            interfaces.append((num.strip(), rest.strip()))
    return interfaces


def choose_interface(stdscr):
    interfaces = list_interfaces()
    if not interfaces:
        pager(stdscr, ["No interfaces found.",
                       "Try running with sudo, or add your user to the",
                       "'wireshark' group (Arch: sudo gpasswd -a $USER wireshark)."],
              "Interfaces")
        return None
    options = [f"{num}: {name}" for num, name in interfaces]
    options.append("Cancel")
    choice = menu(stdscr, "Select a capture interface", options)
    if choice is None or choice == len(options) - 1:
        return None
    return interfaces[choice][0]


def live_capture(stdscr):
    iface = choose_interface(stdscr)
    if iface is None:
        return

    capture_filter = prompt(stdscr, "Capture filter (BPF, optional)")
    display_filter = prompt(stdscr, "Display filter (optional)")
    default_save = f"/tmp/capture_{int(time.time())}.pcap"
    savefile = prompt(stdscr, "Save to file", default_save)

    cmd = [TSHARK, "-i", iface, "-l", "-P", "-w", savefile]
    if capture_filter:
        cmd += ["-f", capture_filter]
    if display_filter:
        cmd += ["-Y", display_filter]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True,
                                 bufsize=1)
    except Exception as exc:
        pager(stdscr, [f"Failed to start tshark: {exc}"], "Error")
        return

    lines = deque(maxlen=5000)
    stop_reading = threading.Event()

    def reader():
        for line in proc.stdout:
            lines.append(line.rstrip("\n"))
            if stop_reading.is_set():
                break

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    stdscr.nodelay(True)
    stopped = False
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 2, f"Capturing on {iface}  ->  {savefile}",
                       curses.color_pair(10) | curses.A_BOLD)
        body_height = height - 3
        visible = list(lines)[-body_height:]
        for i, line in enumerate(visible):
            try:
                stdscr.addstr(2 + i, 0, line[: width - 1],
                               curses.color_pair(10))
            except curses.error:
                pass
        draw_status(stdscr, "s: stop capture   q: stop and discard view")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("s"), ord("q")):
            stopped = True
            break
        time.sleep(0.05)

    stdscr.nodelay(False)
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    stop_reading.set()
    t.join(timeout=2)

    final_lines = list(lines) if lines else ["(no packets captured)"]
    final_lines.insert(0, f"Capture saved to: {savefile}")
    final_lines.insert(1, "")
    pager(stdscr, final_lines, f"Capture finished - {iface}")


def browse_pcap(stdscr):
    path = prompt(stdscr, "Path to .pcap/.pcapng file")
    if not path:
        return
    if not os.path.isfile(path):
        pager(stdscr, [f"File not found: {path}"], "Error")
        return
    display_filter = prompt(stdscr, "Display filter (optional)")

    cmd = [TSHARK, "-r", path, "-P"]
    if display_filter:
        cmd += ["-Y", display_filter]

    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if result.returncode != 0:
        lines = [f"tshark error: {result.returncode}"] + result.stderr.splitlines()
    if not lines:
        lines = ["(no matching packets)"]
    pager(stdscr, lines, f"Reading: {path}")


def main(stdscr):
    curses.curs_set(0)
    init_colors()
    stdscr.keypad(True)

    if not TSHARK:
        stdscr.erase()
        stdscr.addstr(0, 0, "tshark was not found on this system.")
        stdscr.addstr(2, 0, "Arch Linux: sudo pacman -S wireshark-cli")
        stdscr.addstr(4, 0, "Press any key to exit.")
        stdscr.refresh()
        stdscr.getch()
        return

    options = [
        "Live capture (filter + save to file)",
        "Browse an existing capture file",
        "Quit",
    ]
    while True:
        choice = menu(stdscr, "Main menu", options)
        if choice is None or choice == 2:
            break
        elif choice == 0:
            live_capture(stdscr)
        elif choice == 1:
            browse_pcap(stdscr)


if __name__ == "__main__":
    if os.name != "posix":
        print("This tool is for Linux/Unix terminals.")
        sys.exit(1)
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
