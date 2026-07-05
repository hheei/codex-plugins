#!/usr/bin/env node

import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const entrypoint = resolve(__dirname, "..", "ssh-exec-mcp.ts");
const bunBin = process.env.BUN_BIN || "bun";

const child = spawn(bunBin, [entrypoint, ...process.argv.slice(2)], {
	stdio: "inherit",
});

child.on("error", (error) => {
	if (error && "code" in error && error.code === "ENOENT") {
		process.stderr.write(
			[
				"ssh-exec-mcp requires Bun at runtime.",
				"Install Bun from https://bun.sh/ or set BUN_BIN to the Bun executable path.",
			].join("\n") + "\n",
		);
		process.exit(1);
		return;
	}

	process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
	process.exit(1);
});

child.on("exit", (code, signal) => {
	if (signal) {
		process.kill(process.pid, signal);
		return;
	}
	process.exit(code ?? 1);
});
