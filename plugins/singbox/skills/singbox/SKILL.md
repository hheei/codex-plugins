---
name: singbox
description: Use only when the user explicitly asks for the singbox skill, SFM route control, sing-box local proxy control, or Clash API routing diagnostics. Provides reusable local knowledge and optional scripts for inspecting SFM/sing-box, switching selector groups, and testing whether a domain works through direct or proxy routes.
---

# Singbox / SFM Route Control

Use this skill for local SFM/sing-box routing work. Prefer read-only inspection first, then make temporary selector changes only when the user asks to try a route or solve connectivity.

## Local Facts From This Machine

- SFM app process name may appear as `/Applications/SFM.app/Contents/MacOS/SFM`.
- SFM uses the `io.nekohasekai` sing-box runtime.
- The local HTTP proxy observed from Codex is `127.0.0.1:7890`.
- macOS system proxy may be disabled even when Codex is already using `127.0.0.1:7890` through environment variables.
- The sing-box Clash-compatible API is configured at `127.0.0.1:9090` with an empty secret.
- Relevant config file observed: `~/.config/singbox/config.json`.
- The API reported mode `rule`; selector group `Default` controlled the route used by Codex/browser requests.

## Useful Commands

Inspect app and proxy state:

```bash
ps aux | rg -i 'SFM|sing-box|singbox|mihomo|clash|7890|9090'
scutil --proxy
lsof -nP -iTCP:7890 -sTCP:LISTEN
curl -s --max-time 5 http://127.0.0.1:9090/configs
```

List selector groups:

```bash
curl -s --max-time 5 http://127.0.0.1:9090/proxies | jq '.proxies | keys'
curl -s --max-time 5 http://127.0.0.1:9090/proxies/Default | jq '{name, type, now, all}'
```

Switch `Default` temporarily:

```bash
jq -nc --arg name 'Direct-Out' '{name:$name}' \
  | curl -s -X PUT http://127.0.0.1:9090/proxies/Default \
      -H 'Content-Type: application/json' --data-binary @-
curl -s -X DELETE http://127.0.0.1:9090/connections
```

Test a domain through the local proxy:

```bash
curl -x http://127.0.0.1:7890 -I -L --max-time 20 https://invite.linuxdo.org/
```

## Linux.do Invite Case

Observed behavior on 2026-07-07:

- `https://linux.do/` opened in the in-app browser.
- `https://invite.linuxdo.org/` returned Cloudflare `403` when routed through `Default -> SG-Z1`.
- Cloudflare page said `Sorry, you have been blocked`.
- The active SFM chain for the failing request was `Default -> SG-Z1`.
- Switching `Default` to `Direct-Out`, clearing active connections, and reloading the browser changed the invite page to `200` with title `LINUX DO 邀请码`.

Recommended workflow for similar cases:

1. Record the current selector value before changing it.
2. Try the direct route first for domains where proxy egress is blocked by Cloudflare.
3. Clear active connections after switching a selector.
4. Reload the browser tab and verify visible page state.
5. Restore the original selector unless the user wants to keep the new route.

## PKU Campus Network And Tailscale Case

Observed during PKU campus-network debugging on 2026-07-08:

- Edit only `~/.config/singbox/config.json` when the user asks for persistent config changes. Do not edit SFM cache/profile copies under Group Containers.
- Validate after every config edit:

```bash
python3 -m json.tool ~/.config/singbox/config.json >/tmp/singbox-config-check.json
sing-box check -c ~/.config/singbox/config.json
```

Important working model:

- PKU campus services such as `iaaa.pku.edu.cn` and `its.pku.edu.cn` should resolve through PKU DNS and route direct.
- `iaaa.pku.edu.cn` observed as `162.105.131.147`; `its.pku.edu.cn` observed as `162.105.129.65`.
- ICMP ping to PKU services may fail while TCP 443 works; test with `nc -vz -G 3 <ip> 443` before concluding the campus network is down.
- For PKU direct access, keep TUN route exclusions for `111.205.0.0/16` and `162.105.0.0/16`.
- Use PKU DNS such as `162.105.129.122` and `162.105.129.88` for PKU/campus/bootstrap DNS.
- Do not use PKU DNS as the final resolver for Google, ChatGPT, GitHub, or other proxy-only domains. Use proxy-routed DoH/DoT for those.
- In sing-box 1.13.x, DoH server objects should use `type: "https"`, `server: "1.1.1.1"` or `"8.8.8.8"`, and `server_port: 443`. Do not put a full URL like `https://1.1.1.1/dns-query` in `server`; that can become `https://https:%2F%2F.../dns-query`.
- DNS servers routed through a selector inherit selector failures. If DNS logs show `reality verification failed`, remove failing Reality/Hysteria nodes from `Auto` or detour DNS to a known-good selector.
- On PKU campus network, DoT `:853` to public DNS may fail or EOF. Prefer DoH `:443` through a working proxy route for proxy-domain DNS.
- If `Auto` includes unstable nodes, especially Reality nodes failing with `reality verification failed` or UDP/Hysteria nodes blocked by campus network, remove them from `Auto` while leaving them available in manual selectors.
- `log.level: "error"` reduces routine SFM noise once connectivity is stable.
- `169.254.169.254:80` errors are usually metadata/link-local probes; reject `169.254.169.254/32` if the log noise matters.

Tailscale-specific notes:

- This SFM setup uses sing-box's built-in Tailscale endpoint, not a separate `tailscale` CLI/process.
- Route `ts.net`, `100.64.0.0/10`, `100.100.100.100/32`, and `fd7a:115c:a1e0::/48` to the `ts-ep` outbound when using built-in Tailscale.
- Do not permanently route those tailnet ranges to `Direct-Out`; that treats them as ordinary TCP and can timeout.
- Do not add tailnet ranges to `route_exclude_address` when built-in `ts-ep` should handle them.
- If logs show `missing Tailscale IPv4 address`, debug the `ts-ep` endpoint state next rather than switching the route to `Direct-Out`.
- If logs show `dial en0` for `100.x` addresses, check `auto_detect_interface`; binding Direct-Out to the physical interface can bypass the intended Tailscale path.

Known useful config shape:

```json
{
  "log": {
    "level": "error"
  },
  "dns": {
    "servers": [
      {
        "tag": "pku_dns",
        "type": "udp",
        "server": "162.105.129.122",
        "server_port": 53
      },
      {
        "tag": "proxy_dns",
        "type": "https",
        "server": "1.1.1.1",
        "server_port": 443,
        "detour": "Auto",
        "domain_resolver": "cn_bootstrap"
      }
    ]
  },
  "route": {
    "auto_detect_interface": false,
    "rules": [
      {
        "ip_cidr": ["169.254.169.254/32"],
        "action": "reject"
      },
      {
        "domain_suffix": ["pku.edu.cn"],
        "outbound": "Direct-Out"
      },
      {
        "domain_suffix": ["ts.net"],
        "outbound": "ts-ep"
      },
      {
        "ip_cidr": ["100.64.0.0/10", "100.100.100.100/32", "fd7a:115c:a1e0::/48"],
        "outbound": "ts-ep"
      }
    ]
  }
}
```

## Optional Scripts

Run bundled scripts from the skill directory:

```bash
python3 scripts/list_sfm_routes.py
python3 scripts/set_sfm_route.py Default Direct-Out
python3 scripts/test_sfm_routes.py https://invite.linuxdo.org/ Direct-Out 'SG-Z1'
python3 scripts/check_config_health.py ~/.config/singbox/config.json
```

Scripts assume the Clash API is at `http://127.0.0.1:9090` and the local HTTP proxy is `http://127.0.0.1:7890`. Override with:

```bash
CLASH_API=http://127.0.0.1:9090 LOCAL_PROXY=http://127.0.0.1:7890 python3 scripts/list_sfm_routes.py
```

## Safety

- Do not edit `~/.config/singbox/config.json` unless the user explicitly asks for a persistent rule.
- Before editing the persistent config, read the latest file and make a timestamped backup.
- For temporary testing, prefer the Clash API selector endpoint over config file edits.
- Always restore the previous selector if the route change was only for testing.
- Do not print secrets or full proxy server credentials from config files.
