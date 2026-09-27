#!/usr/bin/env python3
"""Serve the dashboard and read-only Linux metrics on the local machine."""

import json
import os
import socket
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


WEB_ROOT = Path(__file__).resolve().parent / "webserver-1.2.103" / "www"
ALLOWED_HOSTS = {"localhost:8000", "127.0.0.1:8000"}
SUSPICIOUS_TCP_PORTS = {1337, 2323, 4444, 5555, 6666, 6667, 12345, 31337}


def format_bytes(value):
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return "%.1f %s" % (size, unit)
        size /= 1024


def read_memory():
    values = {}
    try:
        with open("/proc/meminfo", encoding="ascii") as meminfo:
            for line in meminfo:
                key, raw_value = line.split(":", 1)
                values[key] = int(raw_value.split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        return {"used_percent": None, "used_text": None, "total_text": None}

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    if total <= 0:
        return {"used_percent": None, "used_text": None, "total_text": None}

    used = max(0, total - available)
    return {
        "used_percent": round(100.0 * used / total, 1),
        "used_text": format_bytes(used),
        "total_text": format_bytes(total),
    }


def read_disk():
    try:
        stats = os.statvfs("/")
    except OSError:
        return {"used_percent": None, "used_text": None, "total_text": None}

    total = stats.f_frsize * stats.f_blocks
    available = stats.f_frsize * stats.f_bavail
    if total <= 0:
        return {"used_percent": None, "used_text": None, "total_text": None}

    used = max(0, total - available)
    return {
        "used_percent": round(100.0 * used / total, 1),
        "used_text": format_bytes(used),
        "total_text": format_bytes(total),
    }


def read_interfaces():
    interfaces = []
    try:
        names = socket.if_nameindex()
    except OSError:
        names = []

    for _, name in names:
        if name == "lo":
            continue
        try:
            with open("/sys/class/net/%s/operstate" % name, encoding="ascii") as state_file:
                state = state_file.read().strip()
        except OSError:
            state = "unknown"
        interfaces.append((name, state))

    active = [name for name, state in interfaces if state == "up"]
    status = "online" if active else "offline" if interfaces else "unknown"
    detail = ", ".join("%s (%s)" % item for item in interfaces) or "لا توجد واجهات شبكة غير loopback"
    return {"status": status, "detail": detail}


def test_internet():
    started = time.monotonic()
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=1.5):
            elapsed = int((time.monotonic() - started) * 1000)
            return {"status": "online", "detail": "اختبار اتصال خارجي ناجح (%d ms)" % elapsed}
    except OSError:
        return {"status": "offline", "detail": "تعذر الاتصال بعنوان الاختبار الخارجي"}


def read_ports():
    ports = set()
    suspicious = set()
    for protocol in ("tcp", "tcp6", "udp", "udp6"):
        path = "/proc/net/%s" % protocol
        try:
            with open(path, encoding="ascii") as table:
                next(table, None)
                for line in table:
                    fields = line.split()
                    if len(fields) < 4:
                        continue
                    state = fields[3]
                    if protocol.startswith("tcp") and state != "0A":
                        continue
                    try:
                        port = int(fields[1].rsplit(":", 1)[1], 16)
                    except (IndexError, ValueError):
                        continue
                    if port:
                        label = ("tcp" if protocol.startswith("tcp") else "udp", port)
                        ports.add(label)
                        if label[0] == "tcp" and port in SUSPICIOUS_TCP_PORTS:
                            suspicious.add(port)
        except OSError:
            continue

    ordered_ports = sorted(ports)
    detail = ", ".join("%s/%d" % item for item in ordered_ports[:16])
    if len(ordered_ports) > 16:
        detail += "، و%d أخرى" % (len(ordered_ports) - 16)
    return {
        "count": len(ordered_ports),
        "detail": detail or "لم تُرصد منافذ TCP/UDP مستمعة",
    }, suspicious


def read_metrics():
    ports, suspicious = read_ports()
    if suspicious:
        backdoor = {
            "status": "warning",
            "detail": "منافذ TCP تستحق المراجعة: %s. هذا فحص استدلالي." % ", ".join(map(str, sorted(suspicious))),
        }
    else:
        backdoor = {
            "status": "clear",
            "detail": "لم تُرصد منافذ شائعة ضمن القائمة الاستدلالية؛ هذا ليس فحصاً كاملاً للبرمجيات الخبيثة.",
        }

    return {
        "ram": read_memory(),
        "disk": read_disk(),
        "internet": test_internet(),
        "ethernet": read_interfaces(),
        "ports": ports,
        "backdoor": backdoor,
    }


class MonitorHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Host") not in ALLOWED_HOSTS:
            self.send_error(403, "Local access only")
            return

        if urlsplit(self.path).path == "/api/monitor":
            body = json.dumps(read_metrics(), ensure_ascii=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()


def main():
    handler = partial(MonitorHandler, directory=str(WEB_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler)
    print("Local monitoring dashboard: http://localhost:8000/")
    print("Metrics API is restricted to this machine.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()