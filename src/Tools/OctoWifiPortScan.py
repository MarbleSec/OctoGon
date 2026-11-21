#!/usr/bin/env python3

import socket
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
WHITE = "\033[97m"
YELLOW = "\033[93m"
RESET = "\033[0m"

BANNER = f"""
{RED}                                                                                             
▄████▄  ▄▄▄▄ ▄▄▄▄▄▄ ▄▄▄  ██     ██ ▄▄ ▄▄▄▄▄ ▄▄ █████▄  ▄▄▄  ▄▄▄▄  ▄▄▄▄▄▄ ▄█████  ▄▄▄▄  ▄▄▄  ▄▄  ▄▄ 
██  ██ ██▀▀▀   ██  ██▀██ ██ ▄█▄ ██ ██ ██▄▄  ██ ██▄▄█▀ ██▀██ ██▄█▄   ██   ▀▀▀▄▄▄ ██▀▀▀ ██▀██ ███▄██ 
▀████▀ ▀████   ██  ▀███▀  ▀██▀██▀  ██ ██    ██ ██     ▀███▀ ██ ██   ██   █████▀ ▀████ ██▀██ ██ ▀██ 

      Simple Wifi Port Scanner 
      -[BeysonSec]-
{RESET}
"""    

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def scan_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.timeout(0.5)

        result = sock.connect_ex((ip, port))
        soc.close

        if result == 0:
            try:
                service = socket.getservbyport(port, "tcp")
            except OSError:
                service = "unknown"

            print(f"{GREEN}[OPEN!] PORT {port:<5} | {service}")
        
    except socket.erorr:
        pass
def main():
    clear()
    print(BANNER)

    ip = input(f"{CYAN}[?] Enter target IP: {WHITE}").strip()

    try:
        socket.gethostbyname(ip)
    except socket.gaierror:
        print(f"{RED}[!] Invalid IP or hostname.{RESET}")
        return

    print(f"\n{YELLOW}[*] Target: {ip}")
    print("[*] Scanning ports 1-1024...")
    print(f"[*] Started: {datetime.now()}{RESET}\n")

    start = datetime.now()

    try:
        with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(lambda p: scan_port(ip, p), range(1, 1025))

    except KeyboardInterrupt:
        print(f"\n{RED}[!] Scan interrupted.{RESET}")
        return

    elapsed = datetime.now() - start

    print(f"\n{CYAN}[*] Scan completed!")
    print(f"[*] Time elapsed: {elapsed}")
    print(f"{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Exiting...")
        sys.exit(0)