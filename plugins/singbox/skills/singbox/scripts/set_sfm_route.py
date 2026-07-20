#!/usr/bin/env python3
import json
import os
import sys
import urllib.request


CLASH_API = os.environ.get("CLASH_API", "http://127.0.0.1:9090").rstrip("/")


def request(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{CLASH_API}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def main():
    if len(sys.argv) != 3:
        print("usage: set_sfm_route.py <selector> <route>", file=sys.stderr)
        return 2
    selector, route = sys.argv[1], sys.argv[2]
    before = request("GET", f"/proxies/{selector}")
    request("PUT", f"/proxies/{selector}", {"name": route})
    request("DELETE", "/connections")
    after = request("GET", f"/proxies/{selector}")
    print(json.dumps({"selector": selector, "before": before.get("now"), "after": after.get("now")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
