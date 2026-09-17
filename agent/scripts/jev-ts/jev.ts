// jev CLI client: same interface as the old Python script.
// Fast path: unix socket to the running daemon (no boot, warm TLS).
// Fallback: run the command in-process (fresh connection), and if the
// socket is missing, spawn the daemon detached first so the next call
// is fast.
import { closeSync, existsSync, openSync, unlinkSync } from "node:fs";
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { dispatch, type CmdName, type CmdInput, type CmdResult } from "./core";

const SOCKET_PATH = join(homedir(), ".omp", "jev.sock");
const HERE = import.meta.dir;

function trySocket(cmd: CmdName, input: CmdInput): Promise<CmdResult | null> {
  if (!existsSync(SOCKET_PATH)) return Promise.resolve(null);
  const { promise, resolve } = Promise.withResolvers<CmdResult | null>();
  let buf = "";
  let settled = false;
  const done = (r: CmdResult | null) => {
    if (settled) return;
    settled = true;
    resolve(r);
  };

  Bun.connect({
    unix: SOCKET_PATH,
    socket: {
      data(_s, data) {
        buf += new TextDecoder().decode(data);
        const nl = buf.indexOf("\n");
        if (nl !== -1) {
          try {
            done(JSON.parse(buf.slice(0, nl)) as CmdResult);
          } catch {
            done(null);
          }
        }
      },
      error() {
        // dead socket: clear the stale file so we don't retry forever
        try { unlinkSync(SOCKET_PATH); } catch { /* racing another client */ }
        done(null);
      },
      connectError() {
        try { unlinkSync(SOCKET_PATH); } catch { /* racing another client */ }
        done(null);
      },
    },
  }).then(
    (socket) => {
      socket.write(JSON.stringify({ cmd, input }) + "\n");
    },
    () => done(null),
  );
  // daemon hangs -> don't block the decision on it
  setTimeout(() => done(null), 10_000);
  return promise;
}

// Lazy daemon spawn is racy: every fallback client would start its own
// daemon, and the second bind sweeps the first daemon's socket. Lockfile
// single-flight via O_CREAT|O_EXCL — exactly one client wins the spawn.
function spawnDaemon(): void {
  const lockPath = SOCKET_PATH + ".lock";
  try {
    closeSync(openSync(lockPath, "wx"));
  } catch {
    // someone else is already spawning (or the daemon died holding the
    // lock): either way, don't spawn a second one now. A future call that
    // finds no socket and a lock older than the daemon lifetime retries.
    return;
  }
  const child = spawn("bun", [join(HERE, "daemon.ts")], {
    detached: true,
    stdio: "ignore",
  });
  child.unref();
}

// All flags are single words (--item, --op, --threshold, ...): strip the
// leading dashes and take the next argv slot as the value.
function parseArgs(): { cmd: string; input: Record<string, unknown> } {
  const argv = Bun.argv.slice(2);
  const cmd = argv[0];
  const input: Record<string, unknown> = {};
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) {
      input[key] = true;
    } else {
      input[key] = key === "catalog" ? next.split(",") : next;
      i++;
    }
  }
  return { cmd, input };
}

async function main(): Promise<number> {
  const { cmd, input } = parseArgs();

  if (!process.env.TYPESAFE_API_KEY) {
    process.stderr.write(JSON.stringify({ error: "TYPESAFE_API_KEY not set" }) + "\n");
    return 2;
  }

  let result = await trySocket(cmd as CmdName, input as CmdInput);
  if (!result) {
    spawnDaemon(); // next call gets the fast path
    result = await dispatch(cmd as CmdName, input as CmdInput);
  }
  process.stdout.write(result.stdout + "\n");
  return result.exit;
}

process.exit(await main());