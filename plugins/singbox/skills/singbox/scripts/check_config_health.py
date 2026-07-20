#!/usr/bin/env python3
import json
import sys
from pathlib import Path


DEFAULT_CONFIG = Path.home() / ".config" / "singbox" / "config.json"


def load_config(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dns_servers(config):
    return {server.get("tag"): server for server in config.get("dns", {}).get("servers", [])}


def route_rules(config):
    return config.get("route", {}).get("rules", [])


def list_values(rule, key):
    value = rule.get(key)
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def main():
    path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_CONFIG
    config = load_config(path)
    warnings = []
    notes = []

    log_level = config.get("log", {}).get("level")
    if log_level != "error":
        notes.append(f"log.level is {log_level!r}; use 'error' after connectivity is stable")

    servers = dns_servers(config)
    for tag, server in servers.items():
        if server.get("type") == "https":
            value = str(server.get("server", ""))
            if value.startswith("http://") or value.startswith("https://"):
                warnings.append(f"{tag}: DoH server should be host/IP, not full URL: {value}")
            if not server.get("server_port"):
                notes.append(f"{tag}: consider server_port 443 for DoH")
        if server.get("type") == "tls" and server.get("server_port") == 853:
            notes.append(f"{tag}: DoT 853 may fail on campus networks; DoH 443 is often safer")

    inbound_excludes = []
    for inbound in config.get("inbounds", []):
        inbound_excludes.extend(list_values(inbound, "route_exclude_address"))
    for cidr in ("111.205.0.0/16", "162.105.0.0/16"):
        if cidr not in inbound_excludes:
            warnings.append(f"TUN route_exclude_address is missing PKU range {cidr}")
    for cidr in ("100.64.0.0/10", "100.100.100.100/32", "fd7a:115c:a1e0::/48"):
        if cidr in inbound_excludes:
            warnings.append(f"tailnet range {cidr} is excluded from TUN; built-in ts-ep may not receive it")

    rules = route_rules(config)
    tailnet_to_tsep = False
    tailnet_rejected = False
    metadata_rejected = False
    for rule in rules:
        cidrs = set(list_values(rule, "ip_cidr"))
        domains = set(list_values(rule, "domain_suffix"))
        if "169.254.169.254/32" in cidrs and rule.get("action") == "reject":
            metadata_rejected = True
        if "100.64.0.0/10" in cidrs:
            if rule.get("outbound") == "ts-ep":
                tailnet_to_tsep = True
            if rule.get("action") == "reject":
                tailnet_rejected = True
        if "ts.net" in domains and rule.get("outbound") != "ts-ep":
            warnings.append("ts.net should route to ts-ep when using built-in Tailscale")
    if tailnet_rejected:
        warnings.append("tailnet 100.64.0.0/10 is rejected")
    if not tailnet_to_tsep:
        warnings.append("tailnet 100.64.0.0/10 is not routed to ts-ep")
    if not metadata_rejected:
        notes.append("169.254.169.254/32 is not rejected; metadata probes may create harmless log noise")

    auto = None
    for outbound in config.get("outbounds", []):
        if outbound.get("tag") == "Auto":
            auto = outbound
            break
    if auto:
        auto_outbounds = set(auto.get("outbounds", []))
        for fragile in ("🇰🇷 KR-XU1", "🇰🇷 KR-XU2"):
            if fragile in auto_outbounds:
                notes.append(f"{fragile} is in Auto; remove it if campus network logs Reality/UDP failures")

    result = {"config": str(path), "warnings": warnings, "notes": notes}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
