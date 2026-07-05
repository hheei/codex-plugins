# SSH Exec

`SSH Exec` ships as a single package, `@hheei/ssh-exec`, and supports three usage modes:

- Codex plugin / bundled MCP
- external MCP server via `npx` or `bunx`
- pi-extension via `index.ts`

It exposes three SSH-oriented tools:

- `host`: find configured SSH aliases before you try to connect
- `mount`: mount a remote host locally through `sshfs`
- `exec`: run non-interactive remote commands over SSH

## External MCP install

Use `npx`:

```json
{
  "mcpServers": {
    "ssh": {
      "command": "npx",
      "args": ["-y", "@hheei/ssh-exec"]
    }
  }
}
```

Or `bunx`:

```json
{
  "mcpServers": {
    "ssh": {
      "command": "bunx",
      "args": ["@hheei/ssh-exec"]
    }
  }
}
```

## pi-extension install

Install the package and let pi load the extension from `index.ts`.

The extension registers:

- `host(ssh_host: string)`
- `mount(host: string)`
- `exec(host: string, command: string, timeout?: number)`

When the remote alias is uncertain, use `host` first.

## Recommended workflow

1. Call `host` with `ssh_host: "*"` or a regex like `ileqm|sccpu`.
2. Pick the alias you want from results like `alias (user@hostname)`.
3. Call `mount` before editing remote files.
4. Call `exec` to inspect state, verify changes, or reload services.

Example flow:

- `host(ssh_host: "prod|staging")`
- `mount(host: "prod")`
- edit files under the returned local path
- `exec(host: "prod", command: "systemctl reload nginx")`

## Behavior notes

- `host` reads local OpenSSH config and does not probe reachability
- `mount` always mounts the remote root `/`
- `exec` returns bounded output and exit metadata
- if you are not sure whether a host exists, use `host` first
