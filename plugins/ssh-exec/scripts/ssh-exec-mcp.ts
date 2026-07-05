#!/usr/bin/env bun

import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { isAbsolute, join } from "node:path";

import { SessionManager } from "./session-manager";
import type { ProcessResult, SshMountResult } from "./session-manager";
import { executeSshMount, validateSshMountArgs, type SshMountArgs } from "./ssh-mount";
import {
	executeSshExec,
	readProcessOutputTail,
	validateSshExecArgs,
	type SshExecArgs,
	type SshExecResult,
} from "./ssh-exec";

type JsonRpcId = string | number | null;

interface JsonRpcRequest {
	jsonrpc: "2.0";
	id?: JsonRpcId;
	method?: string;
	params?: unknown;
}

interface JsonRpcResponse {
	jsonrpc: "2.0";
	id: JsonRpcId;
	result?: unknown;
	error?: {
		code: number;
		message: string;
		data?: unknown;
	};
}

interface McpServerOptions {
	execute?: (args: SshExecArgs) => Promise<SshExecResult>;
	mount?: (args: SshMountArgs) => Promise<SshMountResult>;
	findHosts?: (pattern: string) => Promise<SshHostRecord[]>;
	manager?: SessionManager;
}

interface SshExecStructuredContent {
	host: string;
	exitCode: number | null;
	output?: string;
	durationMs: number;
	truncated: boolean;
	totalBytes?: number;
	outputBytes?: number;
	totalLines?: number;
	outputLines?: number;
	notice?: string;
}

interface SshMountStructuredContent {
	host: string;
	localPath: string;
	status: SshMountResult["status"];
}

interface SshHostStructuredContent {
	hosts: SshHostRecord[];
}

interface SshHostRecord {
	alias: string;
	user?: string;
	hostname: string;
	display: string;
}

const PROTOCOL_VERSION = "2025-06-18";
const SERVER_INFO = { name: "ssh", version: "0.1.0" };

const SSH_EXEC_TOOL = {
	name: "exec",
	description:
		"Run a non-interactive command on a remote OpenSSH host. Use this after mount when you want to inspect state, verify a change, or restart or reload a service. Returns bounded output and exit metadata. Timeout defaults to 10 seconds.",
	inputSchema: {
		type: "object",
		properties: {
			host: { type: "string" },
			command: { type: "string" },
			timeout: { type: "number", default: 10 },
		},
		required: ["host", "command"],
	},
};

const SSH_MOUNT_TOOL = {
	name: "mount",
	description:
		"Mount a remote OpenSSH host locally through sshfs so built-in read, edit, and write tools can work on the returned local path. Reuses a healthy mount and remounts a stale one when needed. Supported on Linux and macOS.",
	inputSchema: {
		type: "object",
		properties: {
			host: { type: "string" },
		},
		required: ["host"],
	},
};

const SSH_HOST_TOOL = {
	name: "host",
	description:
		"Find SSH hosts from the local OpenSSH config. Use `*` to list all hosts, or pass a regex-like pattern such as `ileqm|sccpu` to filter aliases.",
	inputSchema: {
		type: "object",
		properties: {
			ssh_host: { type: "string" },
		},
		required: ["ssh_host"],
	},
};

export function createMcpServer(options: McpServerOptions = {}) {
	const manager = options.manager ?? new SessionManager();
	const execute =
		options.execute ?? (async (args: SshExecArgs) => await executeSshExec(manager, args, { timeoutMode: "result" }));
	const mount = options.mount ?? (async (args: SshMountArgs) => {
		const runner = async (runnerArgs: string[], timeoutMs?: number) =>
			await runCleanupSshProcess(manager.sshBin, runnerArgs, timeoutMs, manager.sensitiveValues(args.host));
		return await executeSshMount(manager, args, runner);
	});
	const findHosts = options.findHosts ?? (async (pattern: string) => await findConfiguredHosts(pattern));

	return {
		manager,
		async handle(message: JsonRpcRequest): Promise<JsonRpcResponse | undefined> {
			const id = message.id ?? null;
			try {
				switch (message.method) {
					case "initialize":
						return resultResponse(id, {
							protocolVersion: requestedProtocolVersion(message.params),
							serverInfo: SERVER_INFO,
							capabilities: { tools: {} },
						});
					case "notifications/initialized":
						return undefined;
					case "ping":
						return resultResponse(id, {});
					case "tools/list":
						return resultResponse(id, { tools: [SSH_EXEC_TOOL, SSH_MOUNT_TOOL, SSH_HOST_TOOL] });
					case "tools/call":
						return await handleToolCall(id, message.params, execute, mount, findHosts);
					default:
						return errorResponse(id, -32601, `Method not found: ${message.method}`);
				}
			} catch (error) {
				return errorResponse(id, -32603, error instanceof Error ? error.message : String(error));
			}
		},
	};
}

async function handleToolCall(
	id: JsonRpcId,
	params: unknown,
	execute: (args: SshExecArgs) => Promise<SshExecResult>,
	mount: (args: SshMountArgs) => Promise<SshMountResult>,
	findHosts: (pattern: string) => Promise<SshHostRecord[]>,
): Promise<JsonRpcResponse> {
	if (!params || typeof params !== "object" || Array.isArray(params)) {
		return errorResponse(id, -32602, "tools/call params must be an object");
	}

	const record = params as Record<string, unknown>;

	if (record.name === "host") {
		try {
			const pattern = validateSshHostPattern(record.arguments);
			const hosts = await findHosts(pattern);
			return resultResponse(id, toolResultFromHostLookup(pattern, hosts));
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			return resultResponse(id, {
				isError: true,
				content: [{ type: "text", text: message }],
				structuredContent: { hosts: [] } satisfies SshHostStructuredContent,
			});
		}
	}

	if (record.name === "mount") {
		let args: SshMountArgs;
		try {
			args = validateSshMountArgs(record.arguments);
		} catch (error) {
			return errorResponse(id, -32602, error instanceof Error ? error.message : String(error));
		}

		try {
			const result = await mount(args);
			return resultResponse(id, toolResultFromMount(result));
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			return resultResponse(id, {
				isError: true,
				content: [{ type: "text", text: message }],
			});
		}
	}

	if (record.name !== "exec") {
		return errorResponse(id, -32602, "Unknown tool");
	}

	let args: SshExecArgs;
	try {
		args = validateSshExecArgs(record.arguments);
	} catch (error) {
		return errorResponse(id, -32602, error instanceof Error ? error.message : String(error));
	}

	try {
		const result = await execute(args);
		return resultResponse(id, toolResultFromSsh(result, result.exitCode !== 0 || result.exitCode === null));
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		return resultResponse(id, {
			isError: true,
			content: [{ type: "text", text: message }],
			structuredContent: {
				host: args.host,
				exitCode: null,
				durationMs: 0,
				truncated: false,
				notice: message,
			} satisfies SshExecStructuredContent,
		});
	}
}

function toolResultFromSsh(result: SshExecResult, isError: boolean) {
	const notice =
		result.notice ??
		(isError && result.exitCode !== null && result.exitCode !== 0
			? `Command exited with code ${result.exitCode}`
			: undefined);
	const outputText = result.output ?? `${result.stdout}${result.stderr}`;
	const displayOutput = outputText ? outputText.trimEnd() : "(no output)";
	const text = notice ? `${displayOutput}\n\n${notice}` : outputText || "(no output)";

	const payload: Record<string, unknown> = {
		content: [{ type: "text", text }],
		structuredContent: structuredContentFromSsh(result, notice),
	};
	if (isError) payload.isError = true;
	return payload;
}

function structuredContentFromSsh(result: SshExecResult, notice?: string): SshExecStructuredContent {
	return {
		host: result.host,
		exitCode: result.exitCode,
		output: result.output,
		durationMs: result.durationMs,
		truncated: result.truncated,
		totalBytes: result.totalBytes,
		outputBytes: result.outputBytes,
		totalLines: result.totalLines,
		outputLines: result.outputLines,
		...(notice ? { notice } : {}),
	};
}

function toolResultFromMount(result: SshMountResult) {
	const displayPath = ensureTrailingSlash(formatDisplayPath(result.localPath));
	const text = ["Success.", `Local path: ${displayPath}`, `Home path: ${displayPath}...`].join("\n");
	return {
		content: [{ type: "text", text }],
		structuredContent: {
			host: result.host,
			localPath: result.localPath,
			status: result.status,
		} satisfies SshMountStructuredContent,
	};
}

function toolResultFromHostLookup(pattern: string, hosts: SshHostRecord[]) {
	const text = hosts.length > 0 ? hosts.map((host) => host.display).join("\n") : `No \`${pattern}\` host.`;
	return {
		content: [{ type: "text", text }],
		structuredContent: { hosts } satisfies SshHostStructuredContent,
	};
}

function formatDisplayPath(path: string): string {
	const home = homedir();
	if (path === home) return "~";
	if (path.startsWith(`${home}/`)) return `~${path.slice(home.length)}`;
	return path;
}

function ensureTrailingSlash(path: string): string {
	return path.endsWith("/") ? path : `${path}/`;
}

function validateSshHostPattern(value: unknown): string {
	if (!value || typeof value !== "object" || Array.isArray(value)) {
		throw new Error("host arguments must be an object");
	}
	const pattern = (value as Record<string, unknown>).ssh_host;
	if (typeof pattern !== "string" || !pattern.trim()) {
		throw new Error("host.ssh_host must be a non-empty string");
	}
	return pattern.trim();
}

async function findConfiguredHosts(pattern: string, configPath = join(homedir(), ".ssh", "config")): Promise<SshHostRecord[]> {
	const hosts: SshHostRecord[] = [];
	await collectHostsFromConfig(configPath, new Set<string>(), hosts, new Set<string>());
	if (pattern === "*") return hosts;
	const matcher = new RegExp(pattern);
	return hosts.filter((host) => matcher.test(host.alias));
}

async function collectHostsFromConfig(
	configPath: string,
	seenFiles: Set<string>,
	hosts: SshHostRecord[],
	seenHosts: Set<string>,
): Promise<void> {
	if (seenFiles.has(configPath)) return;
	seenFiles.add(configPath);

	const raw = await readFile(configPath, "utf8").catch(() => "");
	if (!raw) return;

	const baseDir = configPath.includes("/") ? configPath.slice(0, configPath.lastIndexOf("/")) : ".";
	let currentAliases: string[] = [];
	let currentUser: string | undefined;
	let currentHostName: string | undefined;

	const flushCurrent = () => {
		for (const alias of currentAliases) {
			if (seenHosts.has(alias)) continue;
			seenHosts.add(alias);
			const hostname = currentHostName ?? alias;
			const user = currentUser;
			hosts.push({
				alias,
				user,
				hostname,
				display: `${alias} (${user ? `${user}@` : ""}${hostname})`,
			});
		}
	};

	for (const rawLine of raw.split(/\r?\n/)) {
		const line = rawLine.trim();
		if (!line || line.startsWith("#")) continue;

		const includeMatch = line.match(/^Include\s+(.+)$/i);
		if (includeMatch) {
			flushCurrent();
			currentAliases = [];
			currentUser = undefined;
			currentHostName = undefined;
			for (const token of splitConfigArgs(includeMatch[1])) {
				if (token.includes("*") || token.includes("?")) continue;
				const includePath = token.startsWith("~")
					? join(homedir(), token.slice(1))
					: isAbsolute(token)
						? token
						: join(baseDir, token);
				await collectHostsFromConfig(includePath, seenFiles, hosts, seenHosts);
			}
			continue;
		}

		const hostMatch = line.match(/^Host\s+(.+)$/i);
		if (hostMatch) {
			flushCurrent();
			currentAliases = [];
			currentUser = undefined;
			currentHostName = undefined;
			for (const token of splitConfigArgs(hostMatch[1])) {
				if (!isConcreteHostToken(token)) continue;
				currentAliases.push(token);
			}
			continue;
		}

		if (currentAliases.length === 0) continue;

		const userMatch = line.match(/^User\s+(.+)$/i);
		if (userMatch) {
			currentUser = splitConfigArgs(userMatch[1])[0];
			continue;
		}

		const hostNameMatch = line.match(/^HostName\s+(.+)$/i);
		if (hostNameMatch) {
			currentHostName = splitConfigArgs(hostNameMatch[1])[0];
		}
	}

	flushCurrent();
}

function splitConfigArgs(value: string): string[] {
	return value
		.split(/\s+/)
		.map((token) => token.trim())
		.filter(Boolean);
}

function isConcreteHostToken(token: string): boolean {
	return !(token.startsWith("!") || /[*?]/.test(token));
}

function requestedProtocolVersion(params: unknown): string {
	if (!params || typeof params !== "object" || Array.isArray(params)) return PROTOCOL_VERSION;
	const version = (params as Record<string, unknown>).protocolVersion;
	return typeof version === "string" && version.trim() ? version : PROTOCOL_VERSION;
}

function resultResponse(id: JsonRpcId, result: unknown): JsonRpcResponse {
	return { jsonrpc: "2.0", id, result };
}

function errorResponse(id: JsonRpcId, code: number, message: string, data?: unknown): JsonRpcResponse {
	const error: JsonRpcResponse["error"] = { code, message };
	if (data !== undefined) error.data = data;
	return { jsonrpc: "2.0", id, error };
}

export async function runCleanupSshProcess(
	sshBin: string,
	args: string[],
	timeoutMs = 10_000,
	sensitiveValues: string[] = [],
): Promise<ProcessResult> {
	const child = Bun.spawn([sshBin, ...args], {
		stdin: "ignore",
		stdout: "pipe",
		stderr: "pipe",
	});

	let timedOut = false;
	let killTimer: Timer | undefined;
	const timeout = setTimeout(() => {
		timedOut = true;
		child.kill("SIGTERM");
		killTimer = setTimeout(() => child.kill("SIGKILL"), 1000);
	}, timeoutMs);

	try {
		const [output, exitCode] = await Promise.all([
			readProcessOutputTail(child.stdout, child.stderr, sensitiveValues),
			child.exited,
		]);
		return {
			exitCode: timedOut ? null : exitCode,
			output: output.text,
			stdout: output.stdout,
			stderr: output.stderr,
			truncated: output.truncated,
			totalBytes: output.totalBytes,
			outputBytes: output.outputBytes,
			totalLines: output.totalLines,
			outputLines: output.outputLines,
			...(timedOut ? { notice: `SSH cleanup timed out after ${Math.round(timeoutMs / 1000)}s` } : {}),
		};
	} finally {
		clearTimeout(timeout);
		if (killTimer) clearTimeout(killTimer);
	}
}

export async function runStdio(server: ReturnType<typeof createMcpServer>): Promise<void> {
	const decoder = new TextDecoder();
	let buffer = "";

	for await (const chunk of Bun.stdin.stream()) {
		buffer += decoder.decode(chunk, { stream: true });
		let newlineIndex = buffer.indexOf("\n");
		while (newlineIndex >= 0) {
			const line = buffer.slice(0, newlineIndex);
			buffer = buffer.slice(newlineIndex + 1);
			await handleLine(server, line);
			newlineIndex = buffer.indexOf("\n");
		}
	}

	buffer += decoder.decode();
	if (buffer.trim()) await handleLine(server, buffer);
}

async function handleLine(server: ReturnType<typeof createMcpServer>, line: string): Promise<void> {
	if (!line.trim()) return;

	let response: JsonRpcResponse | undefined;
	try {
		response = await server.handle(JSON.parse(line));
	} catch (error) {
		response = errorResponse(null, -32700, "Parse error", error instanceof Error ? error.message : String(error));
	}

	if (response) process.stdout.write(`${JSON.stringify(response)}\n`);
}

if (import.meta.main) {
	const server = createMcpServer();
	const runner = (args: string[], timeoutMs?: number) =>
		runCleanupSshProcess(server.manager.sshBin, args, timeoutMs, server.manager.sensitiveValues());

	let cleanupPromise: Promise<void> | undefined;
	const cleanup = async (budgetMs = 1_500) => {
		cleanupPromise ??= Promise.race([
			server.manager.closeAll(runner, Math.min(1_000, budgetMs)),
			new Promise<void>((resolve) => setTimeout(resolve, budgetMs)),
		]).then(() => undefined);
		await cleanupPromise;
	};

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
}
