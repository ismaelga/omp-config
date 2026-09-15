---
name: webapp-testing
description: Verify a running web app in a real browser from the eval tool's `browser` facade - recon before interacting, wait on app state instead of sleeping, capture screenshot/console/network evidence, then close the tab and stop the server.
disable-model-invocation: true
license: Complete terms in LICENSE.txt
---

# Web Application Testing

Drive the app with the `eval` tool's `browser` global (managed headless Chromium; `tab.run` hands you the raw Puppeteer `page`) and manage its server with the `hub` tool. Those two primitives replace the entire upstream toolkit.

Vendored from `anthropics/skills`, `skills/webapp-testing` (Apache-2.0, terms in `LICENSE.txt`) and rewritten against this harness: upstream's `sync_playwright` examples and its `scripts/with_server.py` server wrapper were dropped because neither runs here.

## Decision Tree: Choosing Your Approach

```
Task -> Is the answer in the source (static/SSR markup, selector, copy, config)?
    ├─ Yes -> read the file with `read`/`grep` and answer from it. Do not start a browser.
    └─ No (state, events, fetch, hydration, layout) -> is the app already served?
        ├─ No -> hub op:"start" with ready:{log, port, timeout}, then op:"logs" on failure
        └─ Yes -> recon, then act:
            1. browser.open({ name, url })
            2. wait for the state the app reaches, or observe()/screenshot() to see it
            3. choose selectors from what the rendered page reports
            4. act, re-confirm the new state, capture evidence
            5. tab.close(), hub op:"stop"
```

## Start the server

```json
{"op":"start","name":"web","application":"npm","args":["run","dev"],
 "ready":{"log":"Local:.*http","port":5173,"timeout":30}}
```

Readiness must be observed, not assumed: `ready` probes both the log line and the port. Never launch a server with `bash`. On a failed start or a request the page can't complete, read the server side with `hub` `op:"logs"` — the browser's view and the server's view disagree often enough to check both.

## Reconnaissance, then action

Look at what the page actually rendered before choosing a selector. `tab.observe()` returns the accessibility-shaped inventory (`{id, role, name, value, states}` plus viewport and scroll); `tab.id(n)` consumes those ids. `tab.ariaSnapshot(selector?, {depth, boxes})` returns a YAML tree whose `[ref=eN]` ids go to `tab.ref("eN")`, and a `tab.screenshot()` is the fastest way to see a layout the DOM describes poorly.

```js
const tab = await browser.open({ name: "check", url: "http://localhost:5173" });
const { elements } = await tab.observe();
display(elements.filter((e) => e.role === "button" || e.role === "textbox"));
```

Act through a handle, not a bare selector: `tab.id(n).click()`, `tab.ref("eN").click()` / `.fill(v)`. On this build `tab.click(selector)` and `tab.fill(selector, value)` hang until their 8 s timeout even on a plainly visible enabled element (reproduced 3/3 across fresh tabs, on a served page and on `page.setContent`); `page.click(sel)` inside `tab.run` and the handle methods work. `tab.type(selector, text)`, `tab.press`, `tab.select`, `tab.scrollIntoView`, and `tab.evaluate` are unaffected.

Navigation and re-render invalidate handles. Re-`observe()` and act in the same `eval` cell; never carry an id across a navigation.

## Wait on state, never on a clock

`page.waitForFunction` (inside `tab.run`), `tab.waitForSelector`, and `tab.waitForUrl` are the correct primitive. A fixed sleep is a race that passes on your machine and fails in CI.

```js
await page.waitForFunction(() => document.getElementById("status").textContent.startsWith("ready"));
```

Start a navigation or response wait *before* the action that triggers it, in the same `tab.run`:

```js
const pending = page.waitForResponse((r) => r.url().includes("/data.json"), { timeout: 8000 });
await page.click("#save");
const response = await pending;   // waitForResponse lives on `page`, not on `tab`
```

`page.goto` accepts `waitUntil: "load" | "domcontentloaded" | "networkidle0" | "networkidle2"`; plain `"networkidle"` is rejected.

## Evidence: console and network

Inside `tab.run`, attach listeners before the navigation or action you want to observe. `page.on("request" | "response" | "requestfailed")` works. `page.on("console")` and `page.on("pageerror")` did not deliver app console output or uncaught exceptions in this build (empty 3/3, while a network failure still surfaced); capture console and page errors over CDP instead, which did work 3/3:

```js
const cdp = await page.target().createCDPSession();
await cdp.send("Runtime.enable");
await cdp.send("Network.enable");
const logs = [];
cdp.on("Runtime.consoleAPICalled", (e) => logs.push(`[${e.type}] ` + e.args.map((a) => a.value ?? a.description).join(" ")));
cdp.on("Runtime.exceptionThrown", (e) => logs.push(`[exception] ${e.exceptionDetails.text}`));
cdp.on("Network.responseReceived", (e) => logs.push(`${e.response.status} ${e.response.url}`));
cdp.on("Network.loadingFailed", (e) => logs.push(`FAILED ${e.errorText}`));
```

Report what the app said, not what you expected it to say: a silent console plus a `saved` heading is a result; a `saved` heading with a 500 in the log is a different one. `tab.screenshot({ selector?, fullPage?, silent? })` saves the image and returns its path — pass `silent: true` when you only need a visual artifact rather than inline pixels. It takes no output path.

## Clean up

Close the tab and stop the server, always — a leaked tab holds a worker, a leaked server holds a port:

```js
await tab.close();               // or browser.close({ name: "check" }), browser.close({ all: true })
```

```json
{"op":"stop","name":"web"}
```

Relay and CDP-attached tabs are the user's real browser session: name a target, never navigate the visible tab, and closing them releases the handle only.

## Examples

- `examples/page-check.js` — one `eval` cell driving a page end to end.
- `examples/local-server.md` — a `hub`-managed static server plus the browser check against it.
