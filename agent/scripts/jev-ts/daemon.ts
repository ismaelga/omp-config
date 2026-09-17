// jev daemon: unix-socket server holding the TLS connection to System One
// open. Started lazily by the client (jev.ts auto-spawn) or via hub start.

import { rmSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { dispatch, codeFingerprint, type CmdName, type CmdInput } from "./core";

const SOCKET_PATH = join(homedir(), ".omp", "jev.sock");
// What this daemon actually booted from; a client whose fingerprint differs
// is talking to code this process no longer is.
const FINGERPRINT = codeFingerprint();

// Line-delimited JSON request: {"cmd": "...", "input": {...}}\n
const handlers = {
  async data(socket: Bun.Socket, data: Buffer) {
    const reply = async (line: string): Promise<string> => {
      try {
        const req = JSON.parse(line) as { cmd: CmdName; input: CmdInput; code_hash?: string };
        // Stale daemon: answer stale, then exit through the normal shutdown
        // path (socket + lock swept) so the client's respawn binds cleanly.
        if (typeof req.code_hash === "string" && req.code_hash !== FINGERPRINT) {
          setTimeout(shutdown, 100); // let the reply flush first
          return JSON.stringify({ stdout: JSON.stringify({ stale: true }), exit: 3, stale: true });
        }
        const result = await dispatch(req.cmd, req.input);
        return JSON.stringify(result) + "\n";
      } catch (e) {
        return JSON.stringify({ stdout: JSON.stringify({ error: `jev daemon: bad request: ${e}` }), exit: 2 }) + "\n";
      }
    };
    for (const line of new TextDecoder().decode(data).split("\n")) {
      if (!line.trim()) continue;
      socket.write((await reply(line)) + "\n");
    }
  },
  error(_socket: Bun.Socket, err: Error) {
    console.error(`jev daemon socket error: ${err}`);
  },
};

// Bind fails when a socket file exists. It is either a live daemon's socket
// (never sweep it — that would orphan a serving daemon) or a stale file from
// a crashed process. Probe: a connect that answers means a daemon is live
// and this process should exit quietly; a failed connect means the file is
// dead, safe to unlink and rebind. This is the second line of defense —
// the client's O_EXCL lockfile prevents the spawn race in the first place.
function bindOrExit(staleNote: string): void {
  Bun.listen({ unix: SOCKET_PATH, socket: handlers });
  console.log(`jev daemon listening on ${SOCKET_PATH}${staleNote}`);
}

async function probeLive(): Promise<boolean> {
  const { promise, resolve } = Promise.withResolvers<boolean>();
  Bun.connect({
    unix: SOCKET_PATH,
    socket: {
      // connect succeeding is itself the liveness proof — the file has a
      // live listener behind it. Don't wait for a reply: the daemon only
      // answers request lines, and a probe that waited on data would
      // deadlock (nothing to answer).
      open(s) {
        s.end();
        resolve(true);
      },
      drain() {
        // Bun requires a data or drain handler; connect probes send nothing.
      },
      connectError() {
        resolve(false); // nothing listening behind the file
      },
      error() {
        resolve(false);
      },
    },
  }).catch(() => resolve(false));
  return promise;
}
try {
  bindOrExit("");
} catch {
  if (await probeLive()) {
    console.log("jev daemon: another daemon already serving, exiting");
    process.exit(0);
  }
  rmSync(SOCKET_PATH, { force: true });
  bindOrExit(" (after stale-socket sweep)");
}

const shutdown = () => {
  rmSync(SOCKET_PATH, { force: true });
  rmSync(SOCKET_PATH + ".lock", { force: true });
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
// Spawn lock is cleared once the socket is live: a crashed spawner no
// longer blocks future clients from retrying.
rmSync(SOCKET_PATH + ".lock", { force: true });