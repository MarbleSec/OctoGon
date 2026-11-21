#!/usr/bin/env python3
import os
import subprocess
import sys
import time

if os.geteuid() != 0:
    os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

# Everything below runs as root
print("Running as root:", os.geteuid() == 0)

SCRIPT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

BANNER = r"""

    ▲▼▲▼▲     ▲▼▲▼▲     ▲▼▲▼▲▼    ▲▼▲▼▲             ▲▼▲▼     ▲▼▲▼▲       ▲▼▲   ▲▼
   ▲▼   ▼▲   ▲▼   ▼▲     ▲▼      ▲▼   ▼▲           ▲▼  ▲▼   ▲▼   ▼▲     ▲▼▲▼  ▲▼
  ▲▼    ▲▼  ▲▼          ▲▼      ▲▼    ▲▼          ▲▼       ▲▼    ▲▼    ▲▼ ▼▲ ▲▼
 ▲▼    ▲▼  ▲▼          ▲▼      ▲▼    ▲▼          ▲▼  ▲▼▲▼ ▲▼    ▲▼    ▲▼  ▲▼▲▼
 ▼▲   ▲▼   ▼▲   ▲▼    ▲▼       ▼▲   ▲▼           ▼▲   ▲▼  ▼▲   ▲▼    ▲▼   ▼▲▼
  ▼▲▼▲▼     ▼▲▼▲▼    ▲▼         ▼▲▼▲▼             ▼▲▼▲▼    ▼▲▼▲▼    ▲▼    ▲▼
"""

SPLASH = """
 ╱╱╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍TheOctoGon Framework╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╲╲
 ┃───────────☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷───────────┃
 ┊ This Framework Comes Without Warenty Of ANY KIND and you and ONLY you     ┊
 ┃ are responsible for how you use this Framework                            ┃
 ┊ We Will Not Tell You What To Do Or How To Use This We Arent Your Parents  ┊
 ┃ Though What We Will Tell You Is This Is Supposed To Be Used Ethically     ┃
 ┊                       PRESS [ENTER] TO CONTINUE                           ┃
 ┃╾──────────☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷☷──────────╼┃
 ╲╲╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍TheOctoGon Framework╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╱╱
"""

LOGO = """
                                                 ╓─────┐ ╓──┐ ╓─╥─┐ ╓──┐           ╓────── ╓──┐ ╓──┐
                                                 ║     │ ║      ║   ║  │           ║       ║  │ ║  │
                                                 ║     │ ╙──┘   ╨   ╙──┘           ║   ┌─┐ ╙──┘ ╨  ┴
                                                 ║     │                           ║     │
                                                 ╙─────┘                           ╙─────┘
                                                ======================================================
                                                                   simple menu
"""

# category -> list of (key, label, filename_or_command)
# Set the third field to the script filename inside SCRIPT_DIR, or a shell command.
MENU = {
    "Misc": [
        ("d", "check deps", "chpkgs.sh"),
        ("f", "files", "files.sh"),
        ("s", "setup sh", "setup.py"),
        ("e", "exit", None),
    ],
    "Network": [
        ("1", "netdiscover", "src/Tools/netdiscover.sh"),
        ("2", "portscan", "src/Tools/OctoWifiPortScan.py"),
        ("3", "Deauth", "src/Tools/deauth.sh"),
        ("4", "packet cap", "src/Tools/packet-cap.py"),
        ("5", "Rouge AP", "src/Tools/rouge.py"),
    ],
    "Virus builder": [
        ("11", "RAT Builder", "src/Tools/OctogonRAT.py"),
        ("12", "backdoor maker", "src/Tools/BackdoorMaker.sh"),
    ],
    "Web": [
        ("13", "SQLinjection", "src/Tools/SqlInjector.sh"),
        ("14", "DoS Attack", "src/Tools/dos.py"),
        ("15", "xss scanner", "src/Tools/xss.sh"),
        ("16", "CmdInjection", "src/Tools/commix.sh"),
    ],
    "recon": [
        ("17", "wpscan", "src/Tools/wpscan.sh"),
        ("18", "dns", "src/Tools/dns.py"),
        ("19", "port", "src/Tools/OctoWebPortScan.py"),
        ("20", "subdomain", "src/Tools/sub.py"),
        ("21", "dorker", "src/Tools/dorker.py"),
    ],
}

# Column widths when drawing the box (adjust to taste)
COL_WIDTHS = [21, 21, 22, 24, 20,]
BOX_W = sum(COL_WIDTHS) + len(COL_WIDTHS) + 1  # + separators


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def runner_for(path):
    """Return command list to execute a script."""
    if path.endswith(".py"):
        return [sys.executable, path]
    if path.endswith(".sh"):
        return ["bash", path]
    # assume executable / raw command
    return [path]


def run_script(relpath):
    """Run a script relative to SCRIPT_DIR. Returns exit code."""
    path = os.path.join(SCRIPT_DIR, relpath)
    if not os.path.isfile(path):
        print(f"  [!] script not found: {relpath}")
        code = 1
    else:
        try:
            code = subprocess.run(runner_for(path)).returncode
        except KeyboardInterrupt:
            print("\n  [!] interrupted")
            code = -1
    try:
        input("\n  [ press ENTER to return to menu ] ")
    except (KeyboardInterrupt, EOFError):
        pass
    return code


def splash():
    """Disclaimer splash; blocks until ENTER."""
    clear()
    print(BANNER)
    print(SPLASH)
    while True:
        key = input("↓\n").strip().lower()
        if key in ("", "enter"):
            return
        if key in ("q", "exit"):
            sys.exit(0)


def draw_menu(status=""):
    clear()
    print(LOGO)

    # Header row of category names
    top = "┌" + "─" * (BOX_W - 2) + "┐"
    sep = "│" + "─" * (BOX_W - 2) + "│"
    print(top)
    header = "│"
    for name, width in zip(MENU.keys(), COL_WIDTHS):
        header += f" {name:^{width - 1}}│"
    print(header)
    print(sep)

    # Build rows: pad each category's items with blanks
    cols = list(MENU.values())
    max_rows = max(len(c) for c in cols)
    padded = [c + [("", "", "")] * (max_rows - len(c)) for c in cols]

    for row in range(max_rows):
        line = "│"
        for ci, col in enumerate(padded):
            key, label, _ = col[row]
            cell = f" [{key}] {label}" if key else ""
            line += f"{cell:<{COL_WIDTHS[ci]}}│"
        print(line)
    print("└" + "─" * (BOX_W - 2) + "┘")

    if status:
        print(f"\n {status}")
    print("\n select an option by key or number (q = quit): ", end="", flush=True)


def handle_choice(choice):
    """Find and run the matching menu entry. Returns status string."""
    choice = choice.strip().lower()
    for cat, items in MENU.items():
        for key, label, target in items:
            if choice == key.lower():
                if target is None:
                    return None  # exit
                code = run_script(target)
                return f"[{cat}] {label} -> exit {code}"
    return f"unknown option: {choice}"


def main():
    splash()
    status = ""
    while True:
        draw_menu(status)
        choice = input().strip()
        if choice.lower() in ("q", "quit"):
            clear()
            sys.exit(0)
        result = handle_choice(choice)
        if result is None:
            clear()
            sys.exit(0)
        status = result if result else ""


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n[!] aborted")
        sys.exit(1)
