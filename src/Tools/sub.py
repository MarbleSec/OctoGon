import curses
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class SubdomainFinderTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.domain = ""
        self.status = ""
        self.results = []
        self.errors = []
        self.running = False
        self.scroll_offset = 0

        curses.curs_set(1)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(100)

        self.draw()

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        title = "Subdomain Finder (TUI)"
        self.stdscr.addstr(0, 0, title, curses.A_BOLD)
        self.stdscr.addstr(1, 0, "-" * min(width - 1, 60))

        self.stdscr.addstr(3, 0, "Domain: ")
        self.stdscr.addstr(3, 8, self.domain)

        self.stdscr.addstr(5, 0, "[Enter] Search   [Backspace] Edit   [q] Quit")

        status_line = self.status if not self.running else f"{self.status} (working...)"
        self.stdscr.addstr(7, 0, status_line[:width - 1])

        self.stdscr.addstr(9, 0, "Results:")
        list_start_row = 10
        visible_rows = max(0, height - list_start_row - 1)

        display_lines = []
        for err in self.errors:
            display_lines.append(f"[error] {err}")
        if self.results:
            display_lines.append(f"-- {len(self.results)} subdomains found --")
            display_lines.extend(sorted(self.results))
        elif not self.running and (self.errors or self.status == "Done"):
            display_lines.append("No subdomains found.")

        max_offset = max(0, len(display_lines) - visible_rows)
        self.scroll_offset = min(self.scroll_offset, max_offset)

        for i, line in enumerate(display_lines[self.scroll_offset:self.scroll_offset + visible_rows]):
            try:
                self.stdscr.addstr(list_start_row + i, 0, line[:width - 1])
            except curses.error:
                pass

        self.stdscr.move(3, 8 + len(self.domain))
        self.stdscr.refresh()

    def run(self):
        while True:
            try:
                key = self.stdscr.getch()
            except curses.error:
                key = -1

            if key == ord('q') and not self.domain:
                break
            elif key in (curses.KEY_ENTER, 10, 13):
                if self.domain and not self.running:
                    self.start_search()
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.domain = self.domain[:-1]
            elif key == curses.KEY_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif key == curses.KEY_DOWN:
                self.scroll_offset += 1
            elif 32 <= key <= 126:
                self.domain += chr(key)

            self.draw()

    def start_search(self):
        self.running = True
        self.results = []
        self.errors = []
        self.scroll_offset = 0
        self.status = "Querying crt.sh and hackertarget.com in parallel..."
        thread = threading.Thread(target=self.find_subdomains, args=(self.domain,), daemon=True)
        thread.start()

    def find_subdomains(self, domain):
        subdomains = set()
        errors = []

        finders = {
            self.search_crtsh: "crt.sh",
            self.search_hackertarget: "hackertarget.com",
        }

        with ThreadPoolExecutor(max_workers=len(finders)) as executor:
            future_to_name = {
                executor.submit(finder, domain): name for finder, name in finders.items()
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    subdomains.update(result)
                    self.status = f"{name} done ({len(result)} found)"
                except Exception as e:
                    errors.append(f"{name}: {e}")

        self.results = subdomains
        self.errors = errors
        self.status = "Done"
        self.running = False

    def search_crtsh(self, domain):
        subdomains = set()
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        response = requests.get(url, timeout=25)
        response.raise_for_status()
        data = response.json()
        for entry in data:
            name = entry.get("name_value", "")
            for line in name.splitlines():
                line = line.strip()
                if line and not line.startswith("*."):
                    subdomains.add(line)
        return subdomains

    def search_hackertarget(self, domain):
        subdomains = set()
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        text = response.text
        if "error" in text.lower() or "API count exceeded" in text:
            return subdomains
        for line in text.splitlines():
            parts = line.split(",")
            if parts and parts[0]:
                subdomains.add(parts[0].strip())
        return subdomains


def main(stdscr):
    app = SubdomainFinderTUI(stdscr)
    app.run()


if __name__ == "__main__":
    curses.wrapper(main)
