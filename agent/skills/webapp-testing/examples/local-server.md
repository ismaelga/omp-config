# Local server + browser check

Start the server with the `hub` tool. Readiness is observed, not assumed: `ready` probes both
the log line and the port before `start` returns.

```json
{"op":"start","name":"web","application":"python3",
 "args":["-m","http.server","3000","--bind","127.0.0.1","--directory","/tmp/site"],
 "ready":{"log":"Serving HTTP","port":3000,"timeout":20}}
```

Then verify the page in the same session. `tab.run` takes the raw Puppeteer `page`, so a small
`waitUntil: "load"` plus `waitForFunction` stands in for upstream's `networkidle` wait
(`page.goto` accepts `"load"`, `"domcontentloaded"`, `"networkidle0"`, `"networkidle2"` — the bare
`"networkidle"` spelling is rejected).

```js
const tab = await browser.open({ name: "check", url: "about:blank" });

const result = await tab.run(async ({ page }) => {
  const requests = [];
  const failed = [];
  page.on("response", (r) => requests.push(`${r.status()} ${r.url()}`));
  page.on("requestfailed", (r) => failed.push(`${r.url()} ${r.failure()?.errorText ?? ""}`));

  await page.goto("http://127.0.0.1:3000/dyn.html", { waitUntil: "load" });
  await page.waitForFunction(
    () => document.getElementById("h").textContent !== "loading",
    { timeout: 10000 },
  );

  await page.click("#go");
  return { heading: await page.$eval("#h", (el) => el.textContent), requests, failed };
});

display(result);
await tab.close();
```

Server-side errors the browser cannot see (a 500 that returned HTML, a stack trace) come from the
server's own output:

```json
{"op":"logs","name":"web","lines":50}
```

And when the run is over:

```json
{"op":"stop","name":"web"}
```
