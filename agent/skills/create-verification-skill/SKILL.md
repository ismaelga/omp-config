---
name: create-verification-skill
description: "Generate a project-local verification skill that drives your app the way a user does — any language, framework, or platform. Use for /skill:create-verification-skill, \"make a control skill for this repo\", or when a project has no scripted way to prove UI/CLI/service behavior."
disable-model-invocation: true
---

# Create a verification skill

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, exercise a feature the way a user would, and capture evidence. This skill generates that as a project-local skill (`.omp/skills/verify-<app>/`) tailored to the repo. You write the generator's output for the next agent, not for a human: it will be read cold, mid-task, by an agent that has never seen the app.

`.omp/skills/<name>/SKILL.md` is omp's native project skill root — one level deep, `description` required, discovered by walking from the working directory up to the repo root, and the layout that travels with the repo in git. (`.agent/skills/` loads too, but a same-named skill there loses to the native root.) The result answers to `/skill:verify-<app>` and reads as `skill://verify-<app>` anywhere in the repo.

## 1. Interview the repo, not the user

Answer these from the codebase and reach for the `ask` tool only for what you cannot observe:

- **Surface:** what does a user actually touch? A web UI, a CLI/TUI, a desktop app, an API, a mobile app, a library? A repo can have several; pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent interact with it programmatically? Existing harnesses first — Playwright/Cypress specs, expect scripts, curl-able endpoints, a debug port. Only then pick a generic recipe: `eval`'s `browser` globals for web and Electron, a `hub` PTY session for CLI/TUI, plain HTTP for services.
- **Observe:** what evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to double-drive a shared instance beats corrupting the user's session. `hub` launch names are unique within a project directory, so pick one that encodes the instance.

If the checkout doesn't build or start as-is, fix that first (or report it precisely) before generating; a skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, clearly marked as verification scaffolding, and remove it in cleanup.

## 2. Generate the skill

Write `.omp/skills/verify-<app>/SKILL.md` with YAML frontmatter (`name: verify-<app>` and a `description` naming the app, the surface, and when to reach for it — the native provider will not register it without one) and these sections, each grounded in the interview, no placeholders left:

- **Launch:** the `hub` `op: "start"` spec — `name`, `application`, `args`, and a `ready` probe (`{log, port, timeout}`) that decides readiness (a log line, a port answering, a prompt); given both `log` and `port`, both must pass. Read output with `op: "logs"`, tear down with `op: "stop"`. Never background a server with `bash`: that loses readiness, logs, and teardown. A short-lived CLI or TUI has no server to keep alive: build the binary (or install deps) once, then give each drive its own `hub` session (PTY by default) and drive it with `op: "send"`.
- **Doctor:** one read-only check answering "is this instance worth driving?" — `hub` `op: "ps"` for process state, `op: "logs"` for the build/version banner, the ready port answering and owned by us, auth valid. Run it first whenever anything looks off.
- **Drive:** the harness recipe with real selectors and commands from this repo, not examples. Web UI: `eval`'s `browser` globals — `browser.open({name, url})`, `tab.observe()` / `tab.ariaSnapshot()` for handles, `tab.click` / `fill` / `press` / `select`, `tab.waitFor` / `waitForSelector`, `tab.run(fn)` when raw Puppeteer is needed. Navigation and re-renders invalidate handles: re-observe and act in the same `eval` cell. CLI/TUI: `hub` `op: "send"` (text, or `keys` such as `ENTER` / `CTRL_C`) into a PTY session, read back with `op: "logs"`. Prefer stable handles (ARIA labels, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Evidence:** what to capture and where it goes. `tab.screenshot()` returns the path it wrote (under `browser.screenshotDir`, else the OS temp dir) — record it, that path is the artifact; `tab.ariaSnapshot()` is the role/name transcript and `hub` `op: "logs"` the terminal transcript; over-cap tool output survives at `artifact://<id>`. Proof standards: exercise the real user path, not internal setters or test-only endpoints; capture the action and the resulting state, not just the final screen; verify side effects (files written, rows inserted, messages sent) alongside what's visible; mocks only where a production boundary already isolates the external system. When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name: some dry-runs still touch the network or open a browser.
- **Cleanup:** how to tear down what the run created. Never kill by process name; kill what you started — `hub` `op: "stop"` on your launch `name`, `browser.close({name})` on the tabs you opened (`{all: true}` when the run owns every tab). Cleanup removes instances and scratch state, never the evidence: proof artifacts survive teardown, in a location the skill names.
- **Helpers:** any script the skill ships is executable and its invocation appears in the skill body; the reader reaches it via `skill://verify-<app>/<relative-path>` or the skill directory path it was handed. A helper the reader must reverse-engineer is not a helper.

## 3. Seed the feature map

Create `.omp/skills/verify-<app>/features/README.md` plus one file per user-facing feature you can identify (aim for the top 3-5 to start, from routes, commands, menus, or docs). Follow the shape in [`references/feature-map-example/`](references/feature-map-example/), with a README index and one file per feature. Each file answers, from the user's point of view: what the feature is, how to reach it, how to drive it with the harness, and what observable end state proves it works. The four H2s are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. The map is the repo's maintained verification source; a proof that drives one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive ONE mapped feature (one is enough; the map exists so later runs can cover the rest), capture evidence, clean up. After cleanup, confirm the evidence still exists at the named location — a cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts don't strand processes and ports. A generated skill that was never executed is a draft, not a deliverable.

## 5. Offer the maintenance loop

Point the user at `/skill:maintain-verification-skill` for keeping the map honest as the app changes. Suggest a cadence only if they ask.
