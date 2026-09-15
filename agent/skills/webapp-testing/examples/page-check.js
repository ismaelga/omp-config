// One eval cell (language: "js"): open a page, wait for the state the app reaches,
// act via Puppeteer inside tab.run, capture console/network evidence, confirm the result, close the tab.

const URL = "http://localhost:5173/"; // app under test

const tab = await browser.open({ name: "demo", url: "about:blank" });

// tab.run does not capture cell closures; anything the run needs goes in args.
const report = await tab.run(async ({ page }, url) => {
  // Collect evidence from the moment the first document starts loading.
  const cdp = await page.target().createCDPSession();
  await cdp.send("Runtime.enable");
  await cdp.send("Network.enable");
  const console_ = [];
  const net = [];
  cdp.on("Runtime.consoleAPICalled", (e) =>
    console_.push(`[${e.type}] ` + e.args.map((a) => a.value ?? a.description).join(" ")));
  cdp.on("Runtime.exceptionThrown", (e) => console_.push(`[exception] ${e.exceptionDetails.text}`));
  cdp.on("Network.responseReceived", (e) => net.push(`${e.response.status} ${e.response.url}`));
  cdp.on("Network.loadingFailed", (e) => net.push(`FAILED ${e.errorText}`));

  await page.goto(url, { waitUntil: "load" });

  // Wait on the render state the app produces, not a fixed sleep.
  await page.waitForFunction(
    () => document.getElementById("status").textContent.startsWith("ready"),
    { timeout: 10000 },
  );
  const before = await page.$eval("#status", (el) => el.textContent);

  // Start the response wait before the action that triggers it, then confirm the new state.
  const resp = page.waitForResponse((r) => r.url().includes("/data.json"), { timeout: 10000 });
  await page.click("#save");
  await page.waitForFunction(
    () => document.getElementById("status").textContent === "saved",
    { timeout: 10000 },
  );
  const after = await page.$eval("#status", (el) => el.textContent);

  return { before, after, saved: (await resp).status(), console_, net };
}, { args: [URL] });

display(report);
display(await tab.screenshot()); // returns the saved path; pass { silent: true } to skip inline pixels
await tab.close();
