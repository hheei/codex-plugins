# SSH Exec

`SSH Exec` lets Codex work with remote machines over OpenSSH through three MCP tools:

- `host`: find configured SSH hosts before you try to connect
- `mount`: mount a remote host locally through `sshfs`
- `exec`: run non-interactive remote commands over SSH

## Install

For external MCP clients that can launch an npm package:

```json
{
  "mcpServers": {
    "ssh": {
      "command": "npx",
      "args": ["-y", "@hheei/ssh-exec-mcp"]
    }
  }
}
```

If you prefer Bun:

```json
{
  "mcpServers": {
    "ssh": {
      "command": "bunx",
      "args": ["@hheei/ssh-exec-mcp"]
    }
  }
}
```

An example config is included at [examples/pi-agent.mcp.json](./examples/pi-agent.mcp.json).

## Recommended workflow

When you are not sure whether a remote host exists, call `host` first.

For remote file changes:

1. Call `host` with `ssh_host: "*"` or a regex like `ileqm|sccpu` to find the right alias.
2. Call `mount` with the selected host.
3. Use the returned local path with Codex built-in file tools.
4. Call `exec` to inspect state, verify the result, or reload a remote service.

Example flow:

- `host(ssh_host: "prod|staging")`
- `mount(host: "prod")`
- Read or edit files under the returned local mount path
- `exec(host: "prod", command: "systemctl reload nginx")`

## Tools

### `host`

- Finds SSH aliases from the local OpenSSH config
- Supports `*` to list all concrete hosts
- Supports regex-like matching such as `ileqm|sccpu`
- Returns entries as `alias (user@hostname)`

### `mount`

- Mounts the remote host locally through `sshfs`
- Reuses an existing healthy mount when possible
- Repairs stale mounts by remounting
- Returns a local path for Codex built-in file tools
- Supported on Linux and macOS

### `exec`

- Runs non-interactive remote commands over SSH
- Best for validation, inspection, and service operations
- Returns bounded output and exit metadata

## Notes

- `mount` always mounts the remote root `/`
- Host resolution comes from the local OpenSSH config
- `host` checks configured aliases only; it does not probe network reachability
- This plugin does not implement a separate remote file protocol; file edits are meant to go through Codex built-in file tools after `mount`
