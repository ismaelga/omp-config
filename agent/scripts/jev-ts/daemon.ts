// jev daemon: unix-socket server holding the TLS connection to System One
// open. Started lazily by the client (jev.ts auto-spawn) or via hub start.

import { rmSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { dispatch, type CmdName, type CmdInput } from "./core";

const SOCKET_PATH = join(homedir(), ".omp", "jev.sock");

// A previous daemon's socket file can outlive the process; if bind fails on
// a stale file, remove it and bind once more before giving up.
try {
  Bun.listen({
    unix: SOCKET_PATH,
    socket: {
      async data(socket, data) {
        // Line-delimited JSON request: {"cmd": "...", "input": {...}}\n
        const reply = async (line: string): Promise<string> => {
          try {
            const req = JSON.parse(line) as { cmd: CmdName; input: CmdInput };
            const result = await dispatch(req.cmd, req.input);
            return JSON.stringify(result) + "\n";
          } catch (e) {
            return JSON.stringify({ stdout: JSON.stringify({ error: `jev daemon: bad request: ${e}` }), exit: 2 }) + "\n";
          }
        };
        for (const line of new TextDecoder().decode(data).split("\n")) {
          if (!line.trim()) continue;
          socket.write(await reply(line));
        }
      },
      error(_socket, err) {
        console.error(`jev daemon socket error: ${err}`);
      },
    },
  });
  console.log(`jev daemon listening on ${SOCKET_PATH}`);
} catch (e) {
  // EADDRINUSE on a stale socket file: sweep and retry once
  rmSync(SOCKET_PATH, { force: true });
  Bun.listen({
    unix: SOCKET_PATH,
    socket: {
      async data(socket, data) {
        const reply = async (line: string): Promise<string> => {
          try {
            const req = JSON.parse(line) as { cmd: CmdName; input: CmdInput };
            const result = await dispatch(req.cmd, req.input);
            return JSON.stringify(result) + "\n";
          } catch (e) {
            return JSON.stringify({ stdout: JSON.stringify({ error: `jev daemon: bad request: ${e}` }), exit: 2 }) + "\n";
          }
        };
        for (const line of new TextDecoder().decode(data).split("\n")) {
          if (!line.trim()) continue;
          socket.write(await reply(line));
        }
      },
      error(_socket, err) {
        console.error(`jev daemon socket error: ${err}`);
      },
    },
  });
  console.log(`jev daemon listening on ${SOCKET_PATH} (after stale-socket sweep: ${e})`);
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