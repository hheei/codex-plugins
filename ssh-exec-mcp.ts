#!/usr/bin/env bun

import { createMcpServer, runCleanupSshProcess, runStdio } from "./plugins/ssh-exec/scripts/ssh-exec-mcp";

const server = createMcpServer();
const runner = (args: string[], timeoutMs?: number) =>
	runCleanupSshProcess(server.manager.sshBin, args, timeoutMs, server.manager.sensitiveValues());

let cleanupPromise: Promise<void> | undefined;

async function cleanup(budgetMs = 1_500): Promise<void> {
	cleanupPromise ??= Promise.race([
		server.manager.closeAll(runner, Math.min(1_000, budgetMs)),
		new Promise<void>((resolve) => setTimeout(resolve, budgetMs)),
	]).then(() => undefined);
	await cleanupPromise;
}

process.once("beforeExit", () => {
	void cleanup();
});
process.on("SIGINT", () => {
	void cleanup().finally(() => process.exit(130));
});
process.on("SIGTERM", () => {
	void cleanup().finally(() => process.exit(143));
});

runStdio(server)
	.then(async () => {
		await cleanup();
		process.exit(0);
	})
	.catch((error) => {
		process.stderr.write(`${error instanceof Error ? error.stack ?? error.message : String(error)}\n`);
		process.exit(1);
	});
