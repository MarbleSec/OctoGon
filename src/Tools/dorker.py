#!/usr/bin/env python3
import sys
import time
import random
import urllib.parse

import requests
from bs4 import BeautifulSoup

BANNER = r"""
    ____             __                ____               
   / __ \____  _____/ /_____  _____   / __ \   __  _______
  / / / / __ \/ ___/ //_/ _ \/ ___/  / /_/ /  / / / / ___/
 / /_/ / /_/ / /  / ,< /  __/ /     / _, _/  / /_/ (__  ) 
/_____/\____/_/  /_/|_|\___/_/     /_/ |_|   \__,_/____/  
                                                          

"""

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# {d} = domain, {p} = parameter name
TEMPLATES = {
    "1": ('Directory listing',        'site:{d} intitle:"index of"'),
    "2": ('Sensitive files',          'site:{d} ext:env OR ext:sql OR ext:bak OR ext:log'),
    "3": ('Admin/login pages',        'site:{d} inurl:admin OR inurl:login'),
    "4": ('WP - wp-content paths',    'site:{d} inurl:wp-content OR inurl:wp-admin OR inurl:wp-login'),
    "5": ('WP - config/backups',      'site:{d} inurl:wp-config OR ext:sql OR "wp-content/uploads" ext:zip'),
    "6": ('Param ?id=',               'site:{d} inurl:?id='),
    "7": ('Param ?catid=',            'site:{d} inurl:catid='),
    "8": ('Param ?cartid=',           'site:{d} inurl:cartid= OR inurl:cartID='),
    "9": ('Param ?q=',                'site:{d} inurl:q= OR inurl:search='),
    "10": ('Any param injection-ish', 'site:{d} inurl:?id= OR inurl:?catid= OR inurl:?cartid= OR inurl:?q='),
    "11": ('Open redirects',          'site:{d} inurl:url= OR inurl:redirect= OR inurl:next= OR inurl:goto='),
    "c": ('Custom query',             '{q}'),
}

def search(query, num=20):
    url = "https://www.google.com/search"
    params = {"q": query, "num": num, "hl": "en"}
    headers = {
        "User-Agent": random.choice(UA_LIST),
        "Accept-Language": "en-US,en;q=0.9",
    }
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for g in soup.select("div.g, div.tF2Cxc"):
        a = g.select_one("a")
        h3 = g.select_one("h3")
        if a and h3 and a.get("href"):
            results.append((h3.get_text(strip=True), a["href"]))
    return results

def main():
    print(BANNER)
    while True:
        print("\n--- Dork templates ---")
        for k in sorted(TEMPLATES, key=lambda x: (len(x), x)):
            print(f"  [{k:>2}] {TEMPLATES[k][0]}")
        print("   [q] quit\n")
        key = input("choice> ").strip().lower()
        if key == "q":
            break
        if key not in TEMPLATES:
            print("invalid choice")
            continue

        query = None
        if key == "c":
            query = input("query> ").strip()
        else:
            target = input("domain (or blank for no site: filter)> ").strip()
            param = ""
            if "{p}" in TEMPLATES[key][1]:
                param = input("param name> ").strip()
            query = TEMPLATES[key][1].format(d=target, p=param)
            if not target and "site:" in query:
                query = query.replace("site: ", "").replace(f"site:{target} ", "").strip()

        if not query:
            continue

        print(f"\n[*] Dork: {query}\n")
        try:
            results = search(query)
        except requests.RequestException as e:
            print(f"[!] Request failed: {e}")
            continue

        if not results:
            print("[!] No results parsed — Google may have served a CAPTCHA. "
                  "Wait, change IP, or use the 'c' option with fewer requests.")
        for i, (title, link) in enumerate(results, 1):
            print(f"  {i:>2}. {title}\n      {link}")

        # optionally save
        if results and input("\nsave to file? (y/N)> ").strip().lower() == "y":
            fname = f"results_{int(time.time())}.txt"
            with open(fname, "w") as f:
                f.write(f"# dork: {query}\n")
                for _, link in results:
                    f.write(link + "\n")
            print(f"[+] Saved -> {fname}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n[!] interrupted")