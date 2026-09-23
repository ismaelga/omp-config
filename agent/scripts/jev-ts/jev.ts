// jev CLI client: same interface as the old Python script.
// Fast path: unix socket to the running daemon (no boot, warm TLS).
// Fallback: run the command in-process (fresh connection), and if the
// socket is missing, spawn the daemon detached first so the next call
// is fast.
import { closeSync, existsSync, openSync, statSync, unlinkSync } from "node:fs";
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { dispatch, codeFingerprint, type CmdName, type CmdInput, type CmdResult } from "./core";

const SOCKET_PATH = join(homedir(), ".omp", "jev.sock");
const HERE = import.meta.dir;

// The fingerprint rides on every request; a daemon booted from older code
// answers stale (exit 3) and shuts itself down — one retry then hits a
// freshly spawned daemon. Without it, code edits silently keep serving the
// old behavior (measured 2026-09-17: two rounds of "verified" route changes
// that were answered by a pre-edit daemon).
function trySocket(cmd: CmdName, input: CmdInput, fingerprint: string): Promise<CmdResult | null> {
  if (!existsSync(SOCKET_PATH)) return Promise.resolve(null);
  const { promise, resolve } = Promise.withResolvers<CmdResult | null>();
  let buf = "";
  const dec = new TextDecoder();
  let settled = false;
  const done = (r: CmdResult | null) => {
    if (settled) return;
    settled = true;
    resolve(r);
  };
  // socket.write takes only what the kernel buffer holds (a few hundred KB
  // at most) and returns the byte count; the rest must go out on `drain`.
  // Writing once dropped the tail of large requests, so the daemon never saw
  // the newline and the call stalled to the timeout (300 KB, 2026-09-23).
  let pending = Buffer.from(JSON.stringify({ cmd, input, code_hash: fingerprint }) + "\n");
  const flush = (s: Bun.Socket) => {
    while (pending.length) {
      const n = s.write(pending);
      if (n <= 0) return;
      pending = pending.subarray(n);
    }
  };

  Bun.connect({
    unix: SOCKET_PATH,
    socket: {
      data(_s, data) {
        buf += dec.decode(data, { stream: true });
        const nl = buf.indexOf("\n");
        if (nl !== -1) {
          try {
            done(JSON.parse(buf.slice(0, nl)) as CmdResult);
          } catch {
            done(null);
          }
        }
      },
      drain: flush,
      error() {
        // Mid-connection failure on a socket that did connect: a daemon is
        // listening, so the file must stay — unlinking it orphans that
        // daemon, and the next spawn starts a second one beside it.
        done(null);
      },
      connectError() {
        try { unlinkSync(SOCKET_PATH); } catch { /* racing another client */ }
        done(null);
      },
    },
  }).then(
    flush,
    () => done(null),
  );
  // daemon hangs -> don't block the decision on it. Longer than evaluate()'s
  // 15 s budget (core.ts), so a daemon mid-retry is not abandoned and re-run.
  setTimeout(() => done(null), 20_000);
  return promise;
}

// Lazy daemon spawn is racy: every fallback client would start its own
// daemon, and the second bind sweeps the first daemon's socket. Lockfile
// single-flight via O_CREAT|O_EXCL — exactly one client wins the spawn.
// The daemon deletes the lock once listening, so a lock that outlives any
// real boot belongs to a spawn that died first; without the sweep, every
// later call ran the 1.3 s direct path and never spawned again.
const LOCK_STALE_MS = 30_000;

function spawnDaemon(): void {
  const lockPath = SOCKET_PATH + ".lock";
  try {
    closeSync(openSync(lockPath, "wx"));
  } catch {
    try {
      if (Date.now() - statSync(lockPath).mtimeMs > LOCK_STALE_MS) unlinkSync(lockPath);
    } catch {
      // lock vanished between open and stat: its daemon just bound
    }
    return; // someone is spawning now, or the sweep lets the next call spawn
  }
  const child = spawn("bun", [join(HERE, "daemon.ts")], {
    detached: true,
    stdio: "ignore",
  });
  child.unref();
}

// Flags are dash-prefixed words (--item, --op, --human-gate, ...): strip the
// leading dashes, map hyphenated names to their field (human-gate →
// human_gate), take the next argv slot as the value.
function parseArgs(): { cmd: string; input: Record<string, unknown> } {
  const argv = Bun.argv.slice(2);
  const cmd = argv[0];
  const input: Record<string, unknown> = {};
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    // --human-gate maps to human_gate: both the value and the bare-flag
    // (boolean true) forms must land on the field cmdRoute reads.
    const field = key === "human-gate" ? "human_gate" : key;
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) {
      input[field] = true;
    } else {
      input[field] = key === "catalog" ? next.split(",") : next;
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

  const fingerprint = codeFingerprint();
  let result = await trySocket(cmd as CmdName, input as CmdInput, fingerprint);
  if (result?.stale) {
    // Daemon answered stale and is exiting; give the respawn a beat to bind,
    // then retry once on the fresh daemon (or fall through to direct dispatch).
    spawnDaemon();
    await new Promise((r) => setTimeout(r, 300));
    result = await trySocket(cmd as CmdName, input as CmdInput, fingerprint);
  }
  if (!result) {
    spawnDaemon(); // next call gets the fast path
    result = await dispatch(cmd as CmdName, input as CmdInput);
  }
  process.stdout.write(result.stdout + "\n");
  return result.exit;
}

process.exit(await main());