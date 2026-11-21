import socket
import sys
import curses

BANNER = rf"""
▗▄▄▄  ▗▖  ▗▖ ▗▄▄▖    ▗▖    ▗▄▖  ▗▄▖ ▗▖ ▗▖▗▖ ▗▖▗▄▄▖ 
▐▌  █ ▐▛▚▖▐▌▐▌       ▐▌   ▐▌ ▐▌▐▌ ▐▌▐▌▗▞▘▐▌ ▐▌▐▌ ▐▌
▐▌  █ ▐▌ ▝▜▌ ▝▀▚▖    ▐▌   ▐▌ ▐▌▐▌ ▐▌▐▛▚▖ ▐▌ ▐▌▐▛▀▘ 
▐▙▄▄▀ ▐▌  ▐▌▗▄▄▞▘    ▐▙▄▄▖▝▚▄▞▘▝▚▄▞▘▐▌ ▐▌▝▚▄▞▘▐▌   
"""

def dns_lookup(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror as e:
        return False, str(e)


def run_tui(stdscr):
    curses.curs_set(1)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)

    history = []

    def draw():
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Banner
        for i, line in enumerate(BANNER.strip("\n").split("\n")):
            if i + 1 < h:
                try:
                    stdscr.addstr(i + 1, max(0, (w - len(line)) // 2), line, curses.color_pair(3))
                except curses.error:
                    pass

        banner_h = len(BANNER.strip("\n").split("\n")) + 2
        stdscr.addstr(banner_h, 2, "Type a hostname and press Enter.  ':q' to quit.")
        stdscr.hline(banner_h + 1, 0, curses.ACS_HLINE, w)

        # History (most recent at bottom, just above input line)
        max_history = h - banner_h - 5
        shown = history[-max_history:] if max_history > 0 else []
        for i, (host, ok, result) in enumerate(shown):
            row = banner_h + 2 + i
            if row >= h - 2:
                break
            color = curses.color_pair(1) if ok else curses.color_pair(2)
            arrow = "->" if ok else "x"
            try:
                stdscr.addstr(row, 2, f"{host} {arrow} {result}"[:w - 4], color)
            except curses.error:
                pass

        stdscr.hline(h - 2, 0, curses.ACS_HLINE, w)
        stdscr.addstr(h - 1, 2, "lookup> ")
        stdscr.refresh()

    curses.echo()
    while True:
        draw()
        h, w = stdscr.getmaxyx()
        stdscr.move(h - 1, 10)
        try:
            raw = stdscr.getstr(h - 1, 10, w - 12).decode("utf-8").strip()
        except Exception:
            raw = ""

        if not raw:
            continue
        if raw.lower() in (":q", "quit", "exit"):
            break

        ok, result = dns_lookup(raw)
        history.append((raw, ok, result))


def main():
    if len(sys.argv) > 1:
        # Non-interactive mode: python dns_tool.py example.com [more...]
        print(BANNER)
        for host in sys.argv[1:]:
            ok, result = dns_lookup(host)
            arrow = "->" if ok else "x"
            print(f"{host} {arrow} {result}")
    else:
        curses.wrapper(run_tui)


if __name__ == "__main__":
    main()