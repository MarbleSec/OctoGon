
#!/usr/bin/env python3

import socket
import sys
from concurrent.futures import ThreadPoolExecutor

RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
RESET = "\033[0m"

BANNER = f"""
{RED}

▄▀▀▄  ▄▄▄ ▄█▄   ▄▄  █   █  ▄▄  █▄▄  █▀▀▄  ▄▄  ▄ ▄▄ ▄█▄  ▄▀▀▀  ▄▄▄  ▄▄▄  ▄▄▄  
█  █ █     █   █  █ █▄▀▄█ █▀▀▀ █  █ █▀▀  █  █ █▀    █    ▀▀▄ █    █  █  █  █ 
 ▀▀   ▀▀▀   ▀▀  ▀▀  ▀   ▀  ▀▀▀ ▀▀▀  ▀     ▀▀  ▀      ▀▀ ▀▀▀   ▀▀▀  ▀▀▀▀ ▀  ▀ 
                                                                             
                                                                                                                                                                           
       WEB PORT SCANNER [BeysonSec]
{RESET}
"""

def scan_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.7)
            result = s.connect_ex((ip, port))

            if result == 0:
                try:
                    service = socket.getservbyport(port, "tcp")
                except OSError:
                    service = "unknown"

                return port, service

    except OSError:
        pass

    return None


def main():
    print(BANNER)

    domain = input(
        f"{CYAN}[?] Website/domain: {WHITE}"
    ).strip()

    if "://" in domain:
        domain = domain.split("://", 1)[1]

    domain = domain.split("/")[0].split(":")[0]

    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        print(f"{RED}[!] Could not resolve domain.{RESET}")
        return

    print(f"\n{YELLOW}[*] Domain: {domain}")
    print(f"[*] IP: {ip}")
    print("[*] Scanning TCP ports 1-1024...\n")

    found = 0

    try:
        with ThreadPoolExecutor(max_workers=100) as executor:
            results = executor.map(
                lambda p: scan_port(ip, p),
                range(1, 1025)
            )

            for result in results:
                if result:
                    port, service = result
                    print(
                        f"{GREEN}[OPEN] {port:<6} "
                        f"| {service}{RESET}"
                    )
                    found += 1

    except KeyboardInterrupt:
        print(f"\n{RED}[!] Interrupted.{RESET}")
        return

    print(f"\n{CYAN}[*] Scan complete.")
    print(f"[*] Open ports: {found}{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
