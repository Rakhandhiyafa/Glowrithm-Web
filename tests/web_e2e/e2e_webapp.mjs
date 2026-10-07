// End-to-end test of the Glowrithm web test build in headless Chromium (mobile viewport, fake camera).
//   python make_fixtures.py fixtures             # test photos + fake-camera video
//   npm install                                  # puppeteer-core and @sparticuz/chromium
//   node e2e_webapp.mjs http://localhost:8000 out fixtures/face.y4m fixtures/face_sharp.jpg fixtures/dark.jpg
// CHROME_PATH=/path/to/chrome uses an installed Chrome or Chromium instead of @sparticuz/chromium.
// Start the backend first (demo model is fine). Writes screenshots and e2e_log.json to <out dir>.
import puppeteer from "puppeteer-core";
import fs from "node:fs";
import path from "node:path";

async function chromeLaunchOptions() {
  if (process.env.CHROME_PATH) return { executablePath: process.env.CHROME_PATH, args: ["--no-sandbox"] };
  const { default: chromium } = await import("@sparticuz/chromium");
  return { executablePath: await chromium.executablePath(), args: chromium.args };
}

const [base = "http://localhost:8000", outDir = "out", y4m, galleryPhoto, darkPhoto] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const log = { steps: [], consoleErrors: [], pageErrors: [], failedRequests: [] };
const step = (name, ok, detail = "") => { log.steps.push({ name, ok, detail }); console.log(`${ok ? "PASS" : "FAIL"} ${name} ${detail}`); };

const chrome = await chromeLaunchOptions();
const browser = await puppeteer.launch({
  executablePath: chrome.executablePath,
  headless: true,
  args: [...chrome.args, "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
    ...(y4m ? [`--use-file-for-fake-video-capture=${y4m}`] : [])],
});
const page = await browser.newPage();
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
page.on("console", (msg) => { if (msg.type() === "error") log.consoleErrors.push(msg.text()); });
page.on("pageerror", (err) => log.pageErrors.push(String(err)));
page.on("requestfailed", (req) => log.failedRequests.push(`${req.url()} ${req.failure()?.errorText}`));
// Full-page shots: grow the viewport to the page height so the sticky app bar stays at the top.
async function shot(name, full = false) {
  if (!full) return page.screenshot({ path: path.join(outDir, `${name}.png`) });
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.setViewport({ width: 390, height: Math.max(844, height), deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.screenshot({ path: path.join(outDir, `${name}.png`) });
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
}
const text = () => page.evaluate(() => document.body.innerText);
// Scroll the target to the middle of the screen first, as a person would, so the fixed bottom navigation
// or the sticky app bar never sits on top of it.
async function tap(selector) {
  await page.waitForSelector(selector, { visible: true });
  await page.$eval(selector, (el) => el.scrollIntoView({ block: "center", inline: "center" }));
  await page.click(selector);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const waitText = (needle, timeout = 20000) => page.waitForFunction((n) => document.body.innerText.includes(n), { timeout }, needle);

try {
  // 1. consent gate
  await page.goto(base + "/", { waitUntil: "networkidle0" });
  step("root redirects to consent", page.url().endsWith("/app/#/consent"), page.url());
  await shot("01_consent", true);
  const disabled = await page.$eval("#continue", (b) => b.disabled);
  await tap("#agree");
  step("continue enabled only after agreeing", disabled && !(await page.$eval("#continue", (b) => b.disabled)));
  await tap("#continue");

  // 2. profile setup with validation
  await page.waitForSelector("#profile-form");
  await tap('button[type="submit"]');
  step("empty age is rejected", (await page.$eval("#age-error", (e) => e.textContent)).includes("Enter your age"));
  await page.type("#age", "16");
  step("guardian consent shown for a 16-year-old", !(await page.$eval("#guardian-row", (e) => e.hidden)));
  await tap('[data-sex="female"]');
  await shot("02_profile_minor", true);
  await tap('button[type="submit"]');
  await sleep(300);
  step("minor without guardian consent is blocked", (await text()).includes("parent or guardian"));
  await page.$eval("#age", (e) => { e.value = ""; });
  await page.type("#age", "24");
  await tap('button[type="submit"]');
  await page.waitForFunction(() => location.hash === "#/home");
  await shot("03_home", true);
  step("home shows the hero action", (await text()).includes("Start skin analysis"));

  // 3. live camera scan
  await tap('a[href="#/scan"].btn-white');
  await page.waitForSelector("dialog[open]");
  await shot("04_scan_tips");
  await tap("dialog [data-close]");
  await page.waitForSelector("#chip:not([hidden])", { timeout: 20000 });
  await sleep(800);
  await shot("05_scan_live");
  step("live camera started with the oval guide", (await page.$$eval("#guide ellipse", (e) => e.length)) >= 2);
  await tap("#shutter");
  await page.waitForFunction(() => location.hash === "#/confirm");
  await sleep(300);
  await shot("06_confirm");
  await tap("#analyze");
  await sleep(400);
  await shot("07_analyzing");
  await page.waitForFunction(() => location.hash === "#/result", { timeout: 90000 });
  await sleep(500);
  const resultText = await text();
  step("result shows skin type and heat map", resultText.includes("Skin type") && (await page.$$eval(".cam img", (i) => i.length)) === 2);
  await shot("08_result", true);
  await tap("details.test-details summary");
  await sleep(200);
  await page.$eval("details.test-details", (e) => e.scrollIntoView());
  await shot("09_test_details");
  const record = await page.$$eval(".kv tr", (rows) => rows.map((r) => r.innerText.replace(/\s+/g, " ")));
  step("test details list timings", record.some((r) => r.startsWith("Server total")), record.join(" | "));

  // 4. recommendations, ingredient details, save
  await tap('a[href="#/recommendations"]');
  await page.waitForSelector(".ingredient");
  await shot("10_recommendations", true);
  await tap(".ingredient");
  await page.waitForSelector("dialog[open]");
  await shot("11_ingredient_details");
  await tap("dialog .dialog-actions [data-close]");
  await tap("#save");
  await sleep(200);
  step("result saved to history", await page.$eval("#save", (b) => b.disabled && b.textContent.includes("Saved")));
  await tap("#done");
  await page.waitForFunction(() => location.hash === "#/scan");
  step("done returns to the scan tab", true);

  // 5. history and saved result
  await page.goto(base + "/app/#/history", { waitUntil: "networkidle0" });
  await page.waitForSelector(".history-item");
  await shot("12_history");
  const items = await page.$$eval(".history-item", (e) => e.length);
  step("history lists one saved result", items === 1, `${items} item(s)`);
  await tap(".history-item .list-tile");
  await page.waitForFunction(() => location.hash.startsWith("#/saved/"));
  await waitText("Images are not stored").then(() => step("saved result says images are not stored", true),
    () => step("saved result says images are not stored", false));
  await shot("13_saved_result", true);

  // 6. profile and server test
  await page.goto(base + "/app/#/profile", { waitUntil: "networkidle0" });
  await page.waitForSelector("#server-status");
  await tap("#test");
  await page.waitForFunction(() => (document.querySelector("#server-status")?.textContent || "").length > 0, { timeout: 15000 });
  const status = await page.$eval("#server-status", (e) => e.textContent);
  step("connection test reports the model", status.startsWith("Connected."), status);
  await shot("14_profile", true);

  // 7. gallery upload path
  if (galleryPhoto) {
    await page.goto(base + "/app/#/scan", { waitUntil: "networkidle0" });
    const input = await page.waitForSelector("#pick-gallery");
    await input.uploadFile(galleryPhoto);
    await page.waitForFunction(() => location.hash === "#/confirm");
    await tap("#analyze");
    await page.waitForFunction(() => location.hash === "#/result", { timeout: 90000 });
    await waitText("Skin type").then(() => step("gallery photo analysed", true), () => step("gallery photo analysed", false));
  }

  // 8. quality gate: dark photo must ask for a retake
  if (darkPhoto) {
    await page.goto(base + "/app/#/scan", { waitUntil: "networkidle0" });
    const input = await page.waitForSelector("#pick-gallery");
    await input.uploadFile(darkPhoto);
    await page.waitForFunction(() => location.hash === "#/confirm");
    await tap("#analyze");
    await waitText("Retake your photo", 90000);
    await shot("15_quality_gate_retake");
    step("dark photo is rejected with advice", (await text()).includes("too dark"));
    await tap("#retake");
    await page.waitForFunction(() => location.hash === "#/scan");
  }

  // 9. withdraw consent erases local data
  await page.goto(base + "/app/#/profile", { waitUntil: "networkidle0" });
  await page.waitForSelector("#withdraw");
  await tap("#withdraw");
  await page.waitForSelector("dialog[open]");
  await tap("#dialog-confirm");
  await page.waitForFunction(() => location.hash === "#/consent");
  const stored = await page.evaluate(() => Object.keys(localStorage).filter((k) => k.startsWith("glowrithm.")));
  step("withdrawing consent erases local data", stored.length === 0, JSON.stringify(stored));
} catch (error) {
  step("unexpected error", false, error.stack || String(error));
  await shot("zz_error", true).catch(() => {});
} finally {
  log.passed = log.steps.filter((s) => s.ok).length;
  log.failed = log.steps.filter((s) => !s.ok).length;
  fs.writeFileSync(path.join(outDir, "e2e_log.json"), JSON.stringify(log, null, 2));
  console.log(`\n${log.passed} passed, ${log.failed} failed; console errors: ${log.consoleErrors.length}; page errors: ${log.pageErrors.length}`);
  if (log.consoleErrors.length || log.pageErrors.length) console.log(JSON.stringify({ c: log.consoleErrors, p: log.pageErrors }, null, 1));
  await browser.close();
}
