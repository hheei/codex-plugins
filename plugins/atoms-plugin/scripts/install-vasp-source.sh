#!/usr/bin/env bash
set -euo pipefail

marketplace="${CODEX_MARKETPLACE:-codex-mono}"
plugin="atoms-plugin"
submodule_path="plugins/atoms-plugin/skills/vasp-helper/source"
codex_home="${CODEX_HOME:-$HOME/.codex}"

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

command -v codex >/dev/null 2>&1 || fail "codex is not on PATH"
command -v git >/dev/null 2>&1 || fail "git is not on PATH"

marketplace_root="$(
  codex plugin marketplace list 2>/dev/null |
    awk -v name="$marketplace" '$1 == name { $1 = ""; sub(/^[[:space:]]+/, ""); print; exit }'
)"

[[ -n "$marketplace_root" ]] || fail "marketplace not registered: $marketplace"
[[ -d "$marketplace_root" ]] || fail "marketplace root does not exist: $marketplace_root"
[[ -f "$marketplace_root/.gitmodules" ]] || fail "marketplace has no .gitmodules: $marketplace_root"

printf 'Marketplace root: %s\n' "$marketplace_root"
git -C "$marketplace_root" submodule sync --recursive
git -C "$marketplace_root" submodule update --init --recursive "$submodule_path"

source_path="$marketplace_root/$submodule_path"
[[ -f "$source_path/src/fftlib/README.md" ]] || fail "vasp-source submodule is empty: $source_path"

# Reinstall so Codex copies the now-initialized submodule into its plugin cache.
codex plugin remove "$plugin@$marketplace" >/dev/null 2>&1 || true
codex plugin add "$plugin@$marketplace"

plugin_cache="$codex_home/plugins/cache/$marketplace/$plugin"
installed_version="$(find "$plugin_cache" -mindepth 1 -maxdepth 1 -type d -print -quit 2>/dev/null || true)"
installed_source="$installed_version/skills/vasp-helper/source"
[[ -f "$installed_source/src/fftlib/README.md" ]] || fail "plugin cache has no initialized vasp-source"

printf 'Installed: %s@%s\n' "$plugin" "$marketplace"
printf 'Plugin cache: %s\n' "$installed_version"
printf 'vasp-source: ready\n'
