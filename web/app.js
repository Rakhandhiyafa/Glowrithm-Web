// Glowrithm web test build: the Android app's flow (mobile/lib/screens) as a browser app for quick testing.
// Consent -> profile -> scan (live camera or photo) -> check photo -> analysing -> result with Grad-CAM ->
// recommended ingredients -> history. It calls the same REST API as the Android app.
import { icon } from "./icons.js";
import * as store from "./store.js";
import * as api from "./api.js";
import * as camera from "./camera.js";

const APP_VERSION = "1.0.0 (web test build)";
const DISCLAIMER =
  "Glowrithm supports your choice of skincare ingredients. It does not diagnose skin diseases " +
  "and is not a substitute for advice from a dermatologist.";
const MIN_AGE = 13;
const ADULT_AGE = 18;
const MAX_AGE = 100;
const TABS = [
  { route: "home", label: "Home", icon: "home", active: "home_fill" },
  { route: "scan", label: "Scan", icon: "camera", active: "camera_fill" },
  { route: "history", label: "History", icon: "history", active: "history" },
  { route: "profile", label: "Profile", icon: "person", active: "person_fill" },
];
const STAGES = [
  "Uploading the photo to the server",
  "Finding and cropping your face",
  "Classifying with ResNet50V2 and EfficientNetB0",
  "Building the Grad-CAM heat map",
  "Matching ingredients to your skin",
];
const INGREDIENT_ICONS = {
  salicylic_acid: "cleaning", zinc_pca: "healing", sunscreen: "sun", hyaluronic_acid: "drop",
  ceramide: "shield", glycerin: "opacity", shea_butter: "spa", vitamin_c: "sparkle",
};
const REGULATORY = new Set(["permitted", "restricted", "prohibited"]);

const shell = document.querySelector(".shell");
const viewEl = document.getElementById("view");
const tabsEl = document.getElementById("tabs");
const dialogEl = document.getElementById("dialog");
const toastEl = document.getElementById("toast");
// In memory only: the photo being checked and the latest result (with images) are lost on reload.
const session = { photo: null, result: null, tab: "home", tipsShown: false, previous: null, current: null };
let cleanup = null;

// ---- Small helpers ----------------------------------------------------------------------------------
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const percent = (value) => `${Math.round((Number(value) || 0) * 100)}%`;
const capitalize = (text) => (text ? text[0].toUpperCase() + text.slice(1) : "");
const b64 = (value) => (typeof value === "string" && /^[A-Za-z0-9+/=]+$/.test(value) ? value : "");
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatDateTime(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${date.getDate()} ${MONTHS[date.getMonth()]} ${date.getFullYear()}, ${hh}:${mm}`;
}

const brandMark = (compact = false) =>
  `<div class="brand${compact ? " compact" : ""}"><span class="brand-badge">${icon("sparkle", { size: compact ? 20 : 26 })}</span>` +
  `<span class="brand-name">Glowrithm</span></div>`;

const note = ({ iconName, title, body, warning = false }) =>
  `<div class="note${warning ? " warning" : ""}">${icon(iconName, { size: 22 })}` +
  `<div><h3 class="title-sm">${esc(title)}</h3><p>${esc(body)}</p></div></div>`;

const disclaimer = (text) => `<p class="disclaimer">${icon("info", { size: 16 })}<span>${esc(text || DISCLAIMER)}</span></p>`;

const bullets = (items, iconName = "check_circle") =>
  `<ul class="bullets">${items.map((item) => `<li>${icon(iconName, { size: 18 })}<span>${esc(item)}</span></li>`).join("")}</ul>`;

const infoRow = (label, value) => `<div class="info-row"><span>${esc(label)}</span><span>${esc(value)}</span></div>`;

function appBar(title, { close = false } = {}) {
  return `<header class="appbar"><button class="icon-btn" id="bar-back" aria-label="${close ? "Close" : "Back"}">` +
    `${icon(close ? "close" : "back")}</button><h1>${esc(title)}</h1></header>`;
}

function bar(label, value, big = false) {
  const pct = Math.max(0, Math.min(100, Math.round((Number(value) || 0) * 100)));
  return `<div><div class="bar-row${big ? " strong" : ""}"><span>${esc(label)}</span><span class="num">${pct}%</span></div>` +
    `<div class="bar${big ? " big" : ""}" role="img" aria-label="${esc(label)}: ${pct}%"><i style="width:${pct}%"></i></div></div>`;
}

function toast(message) {
  toast.shownAt = Date.now();
  toastEl.textContent = message;
  toastEl.hidden = false;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { toastEl.hidden = true; }, 2600);
}

function openDialog(html, onClose) {
  dialogEl.returnValue = "";
  dialogEl.innerHTML = html;
  dialogEl.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => dialogEl.close()));
  dialogEl.addEventListener("close", () => {
    const value = dialogEl.returnValue;
    dialogEl.innerHTML = "";
    if (onClose) onClose(value);
  }, { once: true });
  dialogEl.showModal();
}
dialogEl.addEventListener("click", (event) => { if (event.target === dialogEl) dialogEl.close(); });

function confirmDialog({ title, message, confirmLabel, destructive = false }) {
  return new Promise((resolve) => {
    openDialog(
      `<div class="dialog-body"><h2>${esc(title)}</h2><p class="muted mt-8">${esc(message)}</p></div>` +
      `<div class="dialog-actions"><button class="btn-text" data-close>Cancel</button>` +
      `<button class="btn${destructive ? " btn-danger" : ""}" id="dialog-confirm">${esc(confirmLabel)}</button></div>`,
      (value) => resolve(value === "confirm"),
    );
    dialogEl.querySelector("#dialog-confirm").addEventListener("click", () => dialogEl.close("confirm"));
  });
}

function setPhoto(photo) {
  if (session.photo) URL.revokeObjectURL(session.photo.url);
  session.photo = photo ? { ...photo, url: URL.createObjectURL(photo.blob) } : null;
}

// ---- Routing ------------------------------------------------------------------------------------------
const ROUTES = [
  { pattern: /^consent$/, render: viewConsent },
  { pattern: /^setup$/, render: () => viewProfileForm(false) },
  { pattern: /^home$/, render: viewHome, tab: "home" },
  { pattern: /^scan$/, render: viewScan, tab: "scan" },
  { pattern: /^history$/, render: viewHistory, tab: "history" },
  { pattern: /^profile$/, render: viewProfile, tab: "profile" },
  { pattern: /^profile\/edit$/, render: () => viewProfileForm(true) },
  { pattern: /^confirm$/, render: viewConfirm },
  { pattern: /^analyzing$/, render: viewAnalyzing },
  { pattern: /^result$/, render: () => viewResult(session.result, false) },
  { pattern: /^recommendations$/, render: () => viewRecommendations(session.result, false) },
  { pattern: /^saved\/([\w-]+)$/, render: (id) => viewResult(store.findSaved(id), true) },
  { pattern: /^saved\/([\w-]+)\/recommendations$/, render: (id) => viewRecommendations(store.findSaved(id), true) },
];

function go(path, { replace = false } = {}) {
  const hash = `#/${path}`;
  if (window.location.hash === hash) render();
  else if (replace) window.location.replace(hash);
  else window.location.hash = hash;
}

/** In-app back button: use the browser history when it leads to the expected screen. */
function back(target) {
  if (session.previous === target) window.history.back();
  else go(target, { replace: true });
}

function render() {
  if (cleanup) {
    try { cleanup(); } catch { /* ignore */ }
    cleanup = null;
  }
  if (dialogEl.open) dialogEl.close();
  // A message shown while leaving a screen (e.g. "Profile updated") stays; older ones do not follow the user.
  if (!toastEl.hidden && Date.now() - (toast.shownAt || 0) > 600) toastEl.hidden = true;
  const path = decodeURIComponent(window.location.hash.replace(/^#\/?/, "")) || "home";
  const consent = store.getConsent();
  const profile = store.getProfile();
  if (!consent && path !== "consent") return go("consent", { replace: true });
  if (consent && !profile && path !== "setup") return go("setup", { replace: true });
  if (consent && profile && (path === "consent" || path === "setup")) return go("home", { replace: true });
  const route = ROUTES.find((item) => item.pattern.test(path));
  if (!route) return go("home", { replace: true });

  session.previous = session.current;
  session.current = path;
  if (route.tab) session.tab = route.tab;
  showTabs(route.tab || null);
  window.scrollTo(0, 0);
  const result = route.render(...path.match(route.pattern).slice(1));
  if (typeof result === "function") cleanup = result;
  viewEl.focus({ preventScroll: true });
  return undefined;
}

function showTabs(active) {
  shell.classList.toggle("with-tabs", Boolean(active));
  tabsEl.hidden = !active;
  if (!active) return;
  tabsEl.innerHTML = TABS.map((tab) => {
    const current = tab.route === active;
    return `<a class="tab" href="#/${tab.route}"${current ? ' aria-current="page"' : ""}>` +
      `<span class="pip">${icon(current ? tab.active : tab.icon)}</span>${tab.label}</a>`;
  }).join("");
}

// ---- Consent (UU PDP No. 27/2022) ---------------------------------------------------------------------
function viewConsent() {
  const items = [
    ["face", "What we collect", "One face photo per analysis, plus your age and biological sex."],
    ["memory", "How the photo is processed",
      "It is sent to the Glowrithm server, analysed in the server's memory and discarded right away. It is never stored or logged."],
    ["lock", "What stays in this browser",
      "Your profile and the results you save are kept only in this browser. Photos are never saved."],
    ["delete", "Your rights", "View, edit or delete your data, or withdraw consent at any time in Profile."],
    ["hospital", "Not a medical diagnosis", "Results support your skincare choices. For skin conditions, see a dermatologist."],
  ];
  viewEl.innerHTML = `<div class="page roomy">
    ${brandMark()}
    <h1 class="headline mt-28">Before we look at your skin</h1>
    <p class="lead">Glowrithm estimates your skin type from a face photo and suggests suitable skincare ingredients.
      This is exactly what happens with your data.</p>
    <ul class="policy-list">${items.map(([name, title, body]) =>
      `<li class="policy"><span class="tile-icon">${icon(name, { size: 22 })}</span>` +
      `<div><h2 class="title-sm">${title}</h2><p class="muted">${body}</p></div></li>`).join("")}</ul>
    <label class="check"><input type="checkbox" id="agree">
      <span>I agree to the processing of my photo and profile data for skin analysis as described above (UU PDP No. 27/2022).</span></label>
    <button class="btn block" id="continue" disabled>Agree and continue</button>
    <p class="muted small mt-16">${esc("This is the web test build of Glowrithm, made for testing the analysis before the Android app is released.")}</p>
  </div>`;
  const agree = viewEl.querySelector("#agree");
  const button = viewEl.querySelector("#continue");
  agree.addEventListener("change", () => { button.disabled = !agree.checked; });
  button.addEventListener("click", () => {
    store.grantConsent();
    go("setup");
  });
}

// ---- Profile form (setup and edit) -------------------------------------------------------------------
function viewProfileForm(editing) {
  const profile = store.getProfile();
  let sex = profile ? profile.sex : null;
  viewEl.innerHTML = `${editing ? appBar("Edit profile") : ""}
  <form class="page${editing ? "" : " roomy"}" id="profile-form" novalidate>
    ${editing ? "" : `${brandMark()}<div class="mt-28"></div>`}
    <h1 class="headline">Personalize your profile</h1>
    <p class="lead">Your age and biological sex adjust which ingredients are prioritised. They are not used to classify your skin.</p>
    <label class="field-label" for="age">Age</label>
    <div class="input-wrap" id="age-wrap">${icon("cake")}
      <input id="age" inputmode="numeric" autocomplete="off" maxlength="3" placeholder="e.g. 24"
        value="${esc(profile ? profile.age : "")}" aria-describedby="age-error"><span class="muted">years</span></div>
    <p class="field-error" id="age-error" hidden></p>
    <span class="field-label" id="sex-label">Biological sex</span>
    <p class="muted small">Average sebum levels differ between the sexes, so this slightly changes the ingredient order.</p>
    <div class="choice-grid" role="radiogroup" aria-labelledby="sex-label">
      ${["female", "male"].map((value) => `<button type="button" class="choice" role="radio" data-sex="${value}"
        aria-checked="${sex === value}">${icon(value, { size: 28 })}${capitalize(value)}</button>`).join("")}
    </div>
    <label class="check mt-16" id="guardian-row" hidden><input type="checkbox" id="guardian"${profile && profile.guardian_consent ? " checked" : ""}>
      <span>My parent or guardian agrees to this analysis (required under 18).</span></label>
    <button class="btn block mt-28" type="submit">${editing ? "Save changes" : "Continue"}</button>
    <p class="center muted small mt-14">${icon("lock", { size: 16 })}<span>Stored only in this browser</span></p>
  </form>`;
  const $ = (selector) => viewEl.querySelector(selector);
  const ageInput = $("#age");
  const ageValue = () => (/^\d{1,3}$/.test(ageInput.value.trim()) ? Number(ageInput.value.trim()) : null);
  const isMinor = () => { const age = ageValue(); return age !== null && age >= MIN_AGE && age < ADULT_AGE; };
  const validateAge = () => {
    const age = ageValue();
    if (age === null) return "Enter your age in years";
    if (age < MIN_AGE) return `Glowrithm is for people aged ${MIN_AGE} and over`;
    if (age > MAX_AGE) return "Enter a valid age";
    return null;
  };
  const showAgeError = (message) => {
    $("#age-error").textContent = message || "";
    $("#age-error").hidden = !message;
    $("#age-wrap").classList.toggle("invalid", Boolean(message));
    ageInput.setAttribute("aria-invalid", message ? "true" : "false");
  };
  const syncGuardian = () => { $("#guardian-row").hidden = !isMinor(); };
  syncGuardian();
  ageInput.addEventListener("input", () => {
    ageInput.value = ageInput.value.replace(/\D/g, "").slice(0, 3);
    showAgeError(null);
    syncGuardian();
  });
  viewEl.querySelectorAll(".choice").forEach((button) => button.addEventListener("click", () => {
    sex = button.dataset.sex;
    viewEl.querySelectorAll(".choice").forEach((item) => item.setAttribute("aria-checked", String(item === button)));
  }));
  if (editing) $("#bar-back").addEventListener("click", () => back("profile"));
  $("#profile-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const error = validateAge();
    showAgeError(error);
    if (error) { ageInput.focus(); return; }
    if (!sex) { toast("Select your biological sex"); return; }
    if (isMinor() && !$("#guardian").checked) { toast("Users under 18 need consent from a parent or guardian"); return; }
    store.saveProfile({ age: ageValue(), sex, guardian_consent: isMinor() && $("#guardian").checked });
    if (editing) {
      toast("Profile updated");
      back("profile");
    } else {
      go("home");
    }
  });
}

// ---- Home ---------------------------------------------------------------------------------------------
function viewHome() {
  const latest = store.getHistory()[0];
  const steps = [
    ["Take a clear photo", "Face the camera in soft, even light, without makeup or glasses."],
    ["AI reads your skin", "Two neural networks, ResNet50V2 and EfficientNetB0, classify your skin as dry, normal or oily."],
    ["See why", "A Grad-CAM heat map highlights the areas that drove the result."],
    ["Get your ingredients", "A cleanse, treat and protect routine with ingredients that suit your skin, plus their BPOM status."],
  ];
  viewEl.innerHTML = `<div class="page">
    <div class="row">${brandMark(true)}<span class="build-tag">Web test build</span><span class="grow"></span>
      <button class="icon-btn" id="about" aria-label="About Glowrithm">${icon("info")}</button></div>
    <section class="hero">
      <h1>Know your skin type before you buy</h1>
      <p>One photo gives you your skin type, the reason behind it and the ingredients worth looking for.</p>
      <a class="btn-white block" href="#/scan">${icon("camera")}Start skin analysis</a>
    </section>
    ${latest ? `<a class="list-tile mt-16" href="#/saved/${esc(latest.request_id)}">
      <span class="tile-icon">${icon("history")}</span>
      <span class="grow"><span class="muted small">Last saved result</span>
        <strong class="title block-text">${esc(latest.skin_type_label)} skin, ${percent(latest.confidence)} confidence</strong>
        <span class="muted small">${esc(formatDateTime(latest.created_at))}</span></span>${icon("chevron", { cls: "chev" })}</a>` : ""}
    <h2 class="title mt-24">How it works</h2>
    <ol class="steps mt-12">${steps.map(([title, body], index) =>
      `<li><span class="step-num">${index + 1}</span><div><h3 class="title-sm">${title}</h3><p class="muted">${body}</p></div></li>`).join("")}</ol>
    <div class="mt-16">${disclaimer()}</div>
  </div>`;
  viewEl.querySelector("#about").addEventListener("click", () => openDialog(
    `<div class="dialog-body">${brandMark(true)}<p class="mt-12"><strong>Glowrithm ${APP_VERSION}</strong></p>
      <p class="muted mt-8">This web version runs the Android app's flow in a browser so the model and the analysis can be
      tested before the app is released. It uses the same Glowrithm API.</p><p class="muted mt-8">${esc(DISCLAIMER)}</p></div>
     <div class="dialog-actions"><button class="btn" data-close>Close</button></div>`));
}

// ---- Scan -------------------------------------------------------------------------------------------
function showTips() {
  openDialog(`<div class="dialog-body"><h2>Before you scan</h2>${bullets([
    "Wash your face with a mild cleanser and wait about 1 hour without applying any product.",
    "Face a window or soft daylight. Do not use a flash or a lamp pointed at your face.",
    "Remove makeup and glasses, and turn off filters or beauty mode.",
    "Pull hair away from your forehead, keep your head straight and fill the oval.",
  ])}</div><div class="dialog-actions"><button class="btn" data-close>Got it</button></div>`);
}

function viewScan() {
  const { secure, api: hasCameraApi } = camera.support();
  viewEl.innerHTML = `<section class="scan" aria-label="Skin scan">
    <video id="video" playsinline muted aria-hidden="true"></video>
    <svg class="guide" id="guide" aria-hidden="true"></svg>
    <div class="scan-message" id="scan-message" hidden>${icon("camera", { size: 48 })}<p id="scan-text"></p>
      <button class="btn-white" id="take-photo">${icon("camera")}Take or choose a photo</button></div>
    <div class="scan-top"><h1>Skin scan</h1>
      <button class="icon-btn on-dark" id="tips" aria-label="Photo tips">${icon("lightbulb")}</button></div>
    <div class="scan-bottom">
      <div class="status-chip" id="chip" hidden><strong><span class="dot"></span>AI analysis active</strong>
        <small>Align your face inside the oval</small></div>
      <div class="scan-controls">
        <button class="round-btn" id="gallery" aria-label="Choose from gallery">${icon("gallery")}</button>
        <button class="shutter" id="shutter" aria-label="Take photo" disabled></button>
        <button class="round-btn" id="switch" aria-label="Switch camera" disabled>${icon("switch_camera")}</button>
      </div>
    </div>
    <input type="file" id="pick-gallery" accept="image/*" hidden>
    <input type="file" id="pick-camera" accept="image/*" capture="user" hidden>
  </section>`;
  const $ = (selector) => viewEl.querySelector(selector);
  const section = $(".scan");
  const video = $("#video");
  const guide = $("#guide");
  const shutter = $("#shutter");
  const switchButton = $("#switch");
  let stream = null;
  let facing = "user";
  let active = true;
  let busy = false;

  function showMessage(text) {
    $("#scan-text").textContent = text;
    $("#scan-message").hidden = false;
    $("#chip").hidden = true;
    shutter.disabled = true;
    guide.innerHTML = "";
  }

  function drawGuide() {
    const { width: w, height: h } = guide.getBoundingClientRect();
    if (!w || !h) return;
    const ow = w * 0.68;
    const oh = Math.min(ow * 1.32, h * 0.6);
    const cx = w / 2;
    const cy = h * 0.42;
    const rx = ow / 2;
    const ry = oh / 2;
    const f = { l: cx - rx - 14, r: cx + rx + 14, t: cy - ry - 14, b: cy + ry + 14 };
    const len = 26;
    const grid = [1, 2].map((i) => {
      const x = cx - rx + (ow * i) / 3;
      const y = cy - ry + (oh * i) / 3;
      return `<line x1="${x}" y1="${cy - ry}" x2="${x}" y2="${cy + ry}"/><line x1="${cx - rx}" y1="${y}" x2="${cx + rx}" y2="${y}"/>`;
    }).join("");
    const corners = [[f.l, f.t, 1, 1], [f.r, f.t, -1, 1], [f.l, f.b, 1, -1], [f.r, f.b, -1, -1]]
      .map(([x, y, sx, sy]) => `<path d="M${x + len * sx} ${y}H${x}V${y + len * sy}"/>`).join("");
    guide.setAttribute("viewBox", `0 0 ${w} ${h}`);
    guide.innerHTML = `<defs><mask id="oval-hole"><rect width="${w}" height="${h}" fill="#fff"/>
      <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#000"/></mask>
      <clipPath id="oval-clip"><ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}"/></clipPath></defs>
      <rect width="${w}" height="${h}" fill="rgba(0,0,0,0.43)" mask="url(#oval-hole)"/>
      <g clip-path="url(#oval-clip)" stroke="rgba(255,255,255,0.22)" stroke-width="1">${grid}</g>
      <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="2"/>
      <g fill="none" stroke="#7fe0d3" stroke-width="3" stroke-linecap="round">${corners}</g>
      <circle cx="${cx}" cy="${cy}" r="3" fill="#7fe0d3"/>`;
  }

  async function startCamera() {
    camera.stop(stream);
    stream = null;
    shutter.disabled = true;
    if (!secure) {
      showMessage("The live camera only works on a secure page (an https:// address or localhost). You can still take or choose a photo.");
      return;
    }
    if (!hasCameraApi) {
      showMessage("This browser cannot use the camera. You can still take or choose a photo.");
      return;
    }
    try {
      const started = await camera.start(video, facing);
      if (!active) { camera.stop(started); return; }
      stream = started;
      video.classList.toggle("mirror", facing === "user");
      $("#scan-message").hidden = true;
      $("#chip").hidden = false;
      shutter.disabled = false;
      drawGuide();
      switchButton.disabled = (await camera.videoInputs()).length < 2;
    } catch (error) {
      if (active) showMessage(camera.describeError(error));
    }
  }

  async function usePhoto(makePhoto, source) {
    if (busy) return;
    busy = true;
    shutter.classList.add("busy");
    try {
      const photo = await makePhoto();
      setPhoto({ ...photo, source });
      go("confirm");
    } catch (error) {
      toast(error.message || "The photo could not be opened.");
    } finally {
      busy = false;
      shutter.classList.remove("busy");
    }
  }

  shutter.addEventListener("click", () => usePhoto(() => camera.captureFrame(video), "live camera"));
  $("#gallery").addEventListener("click", () => $("#pick-gallery").click());
  $("#take-photo").addEventListener("click", () => $("#pick-camera").click());
  for (const [id, source] of [["#pick-gallery", "gallery"], ["#pick-camera", "camera app"]]) {
    $(id).addEventListener("change", (event) => {
      const file = event.target.files && event.target.files[0];
      event.target.value = "";
      if (file) usePhoto(() => camera.fileToJpeg(file), source);
    });
  }
  switchButton.addEventListener("click", () => {
    facing = facing === "user" ? "environment" : "user";
    startCamera();
  });
  $("#tips").addEventListener("click", showTips);
  const observer = new ResizeObserver(() => { if (stream) drawGuide(); });
  observer.observe(section);
  const onVisibility = () => {
    if (document.hidden) {
      camera.stop(stream);
      stream = null;
      shutter.disabled = true;
    } else if (active && !stream) {
      startCamera();
    }
  };
  document.addEventListener("visibilitychange", onVisibility);
  if (!session.tipsShown) {
    session.tipsShown = true;
    showTips();
  }
  startCamera();
  return () => {
    active = false;
    observer.disconnect();
    document.removeEventListener("visibilitychange", onVisibility);
    camera.stop(stream);
    stream = null;
    video.srcObject = null;
  };
}

// ---- Check photo ----------------------------------------------------------------------------------
function viewConfirm() {
  const photo = session.photo;
  if (!photo) return go("scan", { replace: true });
  viewEl.innerHTML = `${appBar("Check your photo")}
  <div class="page">
    <div class="photo-frame"><img src="${photo.url}" alt="The photo to analyse"></div>
    ${bullets(["Your whole face is visible and centred", "Soft, even daylight without flash glare or strong shadows",
      "Clean skin: no makeup, filters or beauty mode"])}
    <div class="row mt-16"><button class="btn-outline grow" id="retake">Retake</button>
      <button class="btn grow-2" id="analyze">Analyze photo</button></div>
  </div>`;
  const retake = () => { setPhoto(null); back("scan"); };
  viewEl.querySelector("#bar-back").addEventListener("click", retake);
  viewEl.querySelector("#retake").addEventListener("click", retake);
  viewEl.querySelector("#analyze").addEventListener("click", () => go("analyzing"));
  return undefined;
}

// ---- Analysing --------------------------------------------------------------------------------------
function viewAnalyzing() {
  const photo = session.photo;
  const profile = store.getProfile();
  if (!photo) return go("scan", { replace: true });
  let active = true;
  let ticker = null;

  function showProgress() {
    let stage = 0;
    viewEl.innerHTML = `${appBar("Analyzing")}<div class="page">
      <div class="spinner" role="progressbar" aria-label="Analyzing your skin"></div>
      <h1 class="headline">Analyzing your skin</h1><p class="lead">This usually takes a few seconds.</p>
      <ol class="stages mt-24" aria-live="polite">${STAGES.map((text) => `<li><span class="stage-icon"></span><span>${text}</span></li>`).join("")}</ol>
    </div>`;
    viewEl.querySelector("#bar-back").addEventListener("click", () => back("confirm"));
    const update = () => viewEl.querySelectorAll(".stages li").forEach((item, index) => {
      item.className = index < stage ? "done" : index === stage ? "now" : "";
      item.querySelector(".stage-icon").innerHTML = icon(index < stage ? "check_circle" : index === stage ? "radio_on" : "radio_off", { size: 20 });
    });
    update();
    ticker = window.setInterval(() => {
      if (stage < STAGES.length - 1) { stage += 1; update(); }
    }, 900);
  }

  function showFailure(error) {
    const retake = error instanceof api.ApiError && error.retake;
    viewEl.innerHTML = `${appBar("Analyzing")}<div class="page failure">
      ${icon(retake ? "camera" : "cloud_off", { size: 56, cls: "big-icon" })}
      <h1 class="title">${retake ? "Retake your photo" : "The analysis did not finish"}</h1>
      <p class="muted mt-8">${esc(error.message || String(error))}</p>
      <div class="actions">${retake ? '<button class="btn" id="retake">Retake photo</button>' : '<button class="btn" id="retry">Try again</button>'}
        <button class="btn-outline" id="back">Back</button></div></div>`;
    viewEl.querySelector("#bar-back").addEventListener("click", () => back("confirm"));
    viewEl.querySelector("#back").addEventListener("click", () => back("confirm"));
    if (retake) viewEl.querySelector("#retake").addEventListener("click", () => { setPhoto(null); go("scan"); });
    else viewEl.querySelector("#retry").addEventListener("click", run);
  }

  async function run() {
    showProgress();
    const started = performance.now();
    try {
      const result = await api.analyze({ blob: photo.blob, age: profile.age, sex: profile.sex });
      if (!active) return;
      result.created_at = new Date().toISOString();
      result.client = {
        round_trip_ms: Math.round(performance.now() - started),
        upload_kb: Math.round(photo.blob.size / 1024),
        photo_px: `${photo.width} x ${photo.height}`,
        photo_source: photo.source,
        server: api.baseUrl(),
      };
      session.result = result;
      go("result", { replace: true });
    } catch (error) {
      if (active) showFailure(error);
    } finally {
      window.clearInterval(ticker);
    }
  }

  run();
  return () => {
    active = false;
    window.clearInterval(ticker);
  };
}

// ---- Result ------------------------------------------------------------------------------------------
function camViewer(result) {
  return `<div class="cam" id="cam"><img src="data:image/jpeg;base64,${b64(result.face_image)}" alt="Your face as analysed by the model">
      <img class="heat" src="data:image/jpeg;base64,${b64(result.heatmap_image)}" alt="Grad-CAM heat map over your face"></div>
    <div class="slider-row">${icon("opacity", { size: 18 })}
      <input type="range" id="heat" min="0" max="100" value="55" aria-label="Heat-map opacity"><span class="num" id="heat-value">55%</span></div>
    <div class="legend mt-8"></div><div class="legend-labels"><span>Low influence</span><span>High influence</span></div>
    <p class="muted small mt-10">Warmer areas influenced the prediction most. The map shows where the model looked;
      it is not a measurement of oil or moisture.</p>`;
}

function testRecord(result) {
  return {
    recorded_at: new Date().toISOString(),
    model_version: result.model_version,
    request_id: result.request_id,
    demo_mode: result.demo_mode,
    skin_type: result.skin_type,
    confidence: result.confidence,
    probabilities: result.probabilities,
    low_confidence: result.low_confidence,
    face_detected: result.face_detected,
    quality: result.quality ? { passed: result.quality.passed, checks: (result.quality.checks || []).map(({ name, value, status }) => ({ name, value, status })) } : null,
    timings_ms: result.timings_ms,
    client: result.client || null,
    user_agent: navigator.userAgent,
  };
}

function testDetails(result) {
  const timings = result.timings_ms || {};
  const client = result.client || {};
  const ms = (value) => (value === undefined || value === null ? null : `${value} ms`);
  const rows = [
    ["Model version", result.model_version],
    ["Request ID", result.request_id],
    ["Server", client.server],
    ["Round trip in the browser", ms(client.round_trip_ms)],
    ["Server total", ms(timings.total)],
    ["Preprocessing and quality check", ms(timings.preprocess_and_quality)],
    ["Model and Grad-CAM", ms(timings.model_and_gradcam)],
    ["Image encoding", ms(timings.encode)],
    ["Photo sent", client.photo_px ? `${client.photo_px} px, ${client.upload_kb} KB, from ${client.photo_source}` : null],
    ["Face detected", result.face_detected ? "Yes" : "No"],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "");
  const checks = ((result.quality && result.quality.checks) || []).map((check) => {
    const status = ["ok", "warn", "fail"].includes(check.status) ? check.status : "ok";
    const value = check.value === null || check.value === undefined ? "" : ` (${check.value})`;
    return `<tr><th scope="row">Quality: ${esc(check.name)}</th><td><span class="status-${status}">${status}</span>${esc(value)}</td></tr>`;
  }).join("");
  return `<details class="test-details"><summary>${icon("bug", { size: 18 })}Test details</summary>
    <table class="kv"><tbody>${rows.map(([label, value]) => `<tr><th scope="row">${esc(label)}</th><td>${esc(value)}</td></tr>`).join("")}${checks}</tbody></table>
    <div class="details-actions"><button class="btn-text" id="copy-record">${icon("copy", { size: 18 })}Copy test record</button>
      <p class="muted tiny">The record has no photo, age or sex. Paste it into the team's test log.</p></div></details>`;
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast("Test record copied");
  } catch {
    openDialog(`<div class="dialog-body"><h2>Test record</h2><p class="muted mt-8">Copying is blocked here; select the text and copy it.</p>
      <textarea class="text-input mt-12" rows="10" readonly>${esc(text)}</textarea></div>
      <div class="dialog-actions"><button class="btn" data-close>Close</button></div>`);
    dialogEl.querySelector("textarea").select();
  }
}

function viewResult(result, saved) {
  if (!result) return go(saved ? "history" : "home", { replace: true });
  const probabilities = Object.entries(result.probabilities || {}).sort((a, b) => b[1] - a[1]);
  const issues = ((result.quality && result.quality.checks) || [])
    .filter((check) => check.status !== "ok" && check.name !== "face").map((check) => check.message);
  const hasImages = Boolean(b64(result.face_image) && b64(result.heatmap_image));
  const recsPath = saved ? `saved/${result.request_id}/recommendations` : "recommendations";
  viewEl.innerHTML = `${appBar(saved ? "Saved result" : "Scan results", { close: true })}
  <div class="page stack">
    ${result.demo_mode ? note({ iconName: "science", warning: true, title: "Demo mode",
      body: "The server is running an untrained demo model, so this result is random. Use it only to test the app." }) : ""}
    <p class="muted">${saved ? `Saved on ${esc(formatDateTime(result.saved_at || result.created_at))}` : "Here is what the model found in your photo."}</p>
    <section class="card"><div class="card-head">${icon("thermostat")}<h2 class="title">Grad-CAM heat map</h2></div>
      ${hasImages ? camViewer(result) : note({ iconName: "lock", title: "Images are not stored",
        body: "Photos and heat maps are never saved, to protect your privacy. Run a new scan to see the heat map." })}</section>
    <section class="card"><div class="card-head">${icon("insights")}<h2 class="title">Skin type</h2></div>
      <div class="skin-label"><strong>${esc(result.skin_type_label)}</strong><span>${esc(result.skin_type_label_id)}</span></div>
      <p class="mt-6">${esc(result.skin_type_description)}</p>
      <div class="mt-16">${bar("Model confidence", result.confidence, true)}</div>
      <p class="subhead">All skin types</p>
      <div class="bars">${probabilities.map(([name, value]) => bar(capitalize(name), value)).join("")}</div>
      <p class="muted small mt-12">${esc(result.explanation)}</p></section>
    ${result.low_confidence ? note({ iconName: "warning", warning: true, title: "Low confidence",
      body: "Retake the photo facing soft, even light, without makeup, before relying on this result." }) : ""}
    ${result.face_detected ? "" : note({ iconName: "face", warning: true, title: "No face detected",
      body: "The centre of the photo was analysed instead. Fill the oval with your face for a better result." })}
    ${issues.length ? note({ iconName: "camera", warning: true, title: "Photo quality", body: issues.join("\n") }) : ""}
    <section class="card"><div class="card-head">${icon("science")}<h2 class="title">Next step</h2></div>
      <p>${esc(result.recommendations && result.recommendations.summary)}</p>
      <a class="btn block mt-14" href="#/${esc(recsPath)}">See recommended ingredients</a></section>
    ${testDetails(result)}
    ${disclaimer(result.disclaimer)}
  </div>`;
  viewEl.querySelector("#bar-back").addEventListener("click", () => go(session.tab));
  const slider = viewEl.querySelector("#heat");
  if (slider) {
    slider.addEventListener("input", () => {
      viewEl.querySelector("#cam").style.setProperty("--heat", String(slider.value / 100));
      viewEl.querySelector("#heat-value").textContent = `${slider.value}%`;
    });
  }
  viewEl.querySelector("#copy-record").addEventListener("click", () => copyText(JSON.stringify(testRecord(result), null, 2)));
  return undefined;
}

// ---- Recommendations ---------------------------------------------------------------------------------
function regulatoryPill(regulatory) {
  const status = regulatory && REGULATORY.has(regulatory.status) ? regulatory.status : "prohibited";
  return `<span class="pill ${status}">BPOM: ${esc(regulatory ? regulatory.label : "Unknown")}</span>`;
}

function ingredientCard(item, index) {
  return `<button class="card ingredient" data-index="${index}">
    <span class="top"><span class="avatar">${icon(INGREDIENT_ICONS[item.id] || "science", { size: 22 })}</span>
      <span class="grow"><strong class="title block-text">${esc(item.name)}</strong>
        ${item.alias ? `<span class="muted small">${esc(item.alias)}</span>` : ""}</span>${icon("chevron", { cls: "chev" })}</span>
    <span class="pills"><span class="pill match">${esc(item.match_percent)}% match</span>${regulatoryPill(item.regulatory)}</span>
    <span class="block-text">${esc(item.function)}</span>
    ${(item.personal_notes || []).map((text) => `<span class="personal">${icon("person", { size: 18 })}<span>${esc(text)}</span></span>`).join("")}
  </button>`;
}

function showIngredient(item) {
  const regulatory = item.regulatory || {};
  openDialog(`<div class="dialog-body">
    <h2>${esc(item.name)}</h2>${item.inci ? `<p class="muted small">INCI: ${esc(item.inci)}</p>` : ""}
    <div class="pills mt-12"><span class="pill match">${esc(item.match_percent)}% match</span>${regulatoryPill(regulatory)}</div>
    <p class="mt-16">${esc(item.function)}</p>
    <h3 class="title-sm mt-16">Benefits</h3>${bullets(item.benefits || [])}
    <h3 class="title-sm mt-16">How to use</h3><p class="mt-6">${esc(item.how_to_use)}</p>
    ${item.caution ? `<div class="mt-16">${note({ iconName: "warning", warning: true, title: "Caution", body: item.caution })}</div>` : ""}
    ${(item.personal_notes || []).map((text) => `<div class="mt-12">${note({ iconName: "person", title: "For your profile", body: text })}</div>`).join("")}
    <h3 class="title-sm mt-16">Regulatory status (BPOM)</h3><p class="mt-6">${esc(regulatory.note)}</p>
    <p class="muted small mt-4">${esc(regulatory.reference)}</p>
    ${regulatory.verified ? "" : '<p class="small warn-text mt-4">Not yet verified against the regulation annex by the Glowrithm team.</p>'}
    ${(item.evidence || []).length ? `<h3 class="title-sm mt-16">Evidence</h3>${bullets(item.evidence, "book")}` : ""}
  </div><div class="dialog-actions"><button class="btn" data-close>Close</button></div>`);
}

function viewRecommendations(result, saved) {
  if (!result) return go(saved ? "history" : "home", { replace: true });
  const recs = result.recommendations || { steps: [], avoid: [], notes: [] };
  const items = [];
  const stepsHtml = (recs.steps || []).map((step) => {
    const cards = (step.ingredients || []).map((item) => { items.push(item); return ingredientCard(item, items.length - 1); }).join("");
    return `<div class="step-head"><span class="step-num solid">${esc(step.order)}</span><div>
      <h2 class="title">Step ${esc(step.order)}: ${esc(step.title)}</h2><p class="muted small">${esc(step.goal)}</p></div></div>${cards}`;
  }).join("");
  viewEl.innerHTML = `${appBar("Recommended ingredients")}
  <div class="page">
    <h1 class="headline">${esc(recs.headline)}</h1>
    <p class="lead">${esc(recs.summary)}</p>
    ${stepsHtml}
    ${(recs.avoid || []).length ? `<section class="card mt-14"><div class="card-head">${icon("block")}<h2 class="title">Avoid or use with care</h2></div>
      ${recs.avoid.map((item) => `<div class="avoid-item"><h3 class="title-sm">${esc(item.name)}</h3><p class="muted small">${esc(item.reason)}</p></div>`).join("")}</section>` : ""}
    ${(recs.notes || []).length ? `<section class="card mt-14"><div class="card-head">${icon("lightbulb")}<h2 class="title">Good habits</h2></div>
      ${bullets(recs.notes)}</section>` : ""}
    <div class="saved-state">${saved ? "" : '<button class="btn-outline block" id="save"></button>'}</div>
    <button class="btn block mt-10" id="done">Done</button>
    <div class="mt-16">${disclaimer(result.disclaimer)}</div>
  </div>`;
  viewEl.querySelector("#bar-back").addEventListener("click", () => back(saved ? `saved/${result.request_id}` : "result"));
  viewEl.querySelectorAll(".ingredient").forEach((card) => card.addEventListener("click", () => showIngredient(items[Number(card.dataset.index)])));
  viewEl.querySelector("#done").addEventListener("click", () => go(session.tab));
  const save = viewEl.querySelector("#save");
  if (save) {
    const sync = () => {
      const isSaved = store.isSaved(result.request_id);
      save.disabled = isSaved;
      save.innerHTML = `${icon(isSaved ? "bookmark_fill" : "bookmark", { size: 20 })}${isSaved ? "Saved to history" : "Save to history"}`;
    };
    sync();
    save.addEventListener("click", () => {
      store.saveResult(result);
      toast("Saved to history");
      sync();
    });
  }
  return undefined;
}

// ---- History --------------------------------------------------------------------------------------------
function viewHistory() {
  const list = store.getHistory();
  const item = (entry) => `<div class="history-item">
    <a class="list-tile" href="#/saved/${esc(entry.request_id)}">
      <span class="avatar">${esc((entry.skin_type_label || "?")[0])}</span>
      <span class="grow"><strong class="title block-text">${esc(entry.skin_type_label)} (${esc(entry.skin_type_label_id)})</strong>
        <span class="muted small">${percent(entry.confidence)} confidence, ${esc(formatDateTime(entry.created_at))}</span></span>
      ${entry.low_confidence ? icon("warning", { cls: "warn-icon", label: "Low confidence" }) : ""}${icon("chevron", { cls: "chev" })}</a>
    <button class="icon-btn" data-delete="${esc(entry.request_id)}" aria-label="Delete this result">${icon("delete")}</button></div>`;
  viewEl.innerHTML = `<div class="page">
    <div class="row"><h1 class="headline grow">History</h1>${list.length ? '<button class="btn-text" id="delete-all">Delete all</button>' : ""}</div>
    <p class="muted small mt-4">Saved results stay in this browser. Photos are never saved.</p>
    <div class="mt-16">${list.length ? list.map(item).join("") : `<div class="empty">${icon("history", { size: 40 })}
      <h2 class="title">No saved results yet</h2>
      <p class="muted mt-6">After a scan, tap "Save to history" on the recommendations page to keep the result here.</p>
      <a class="btn mt-16" href="#/scan">Start a scan</a></div>`}</div>
  </div>`;
  viewEl.querySelectorAll("[data-delete]").forEach((button) => button.addEventListener("click", () => {
    store.deleteResult(button.dataset.delete);
    toast("Result deleted");
    render();
  }));
  const deleteAll = viewEl.querySelector("#delete-all");
  if (deleteAll) {
    deleteAll.addEventListener("click", async () => {
      const confirmed = await confirmDialog({ title: "Delete all saved results?",
        message: "Every saved result in this browser will be removed. This cannot be undone.", confirmLabel: "Delete all", destructive: true });
      if (confirmed) { store.clearHistory(); render(); }
    });
  }
}

// ---- Profile ----------------------------------------------------------------------------------------------
function connectionNote(base) {
  if (!base) return "";
  return base.startsWith("https://") ? " The connection is encrypted (HTTPS)."
    : " The connection is not encrypted (HTTP): use it only on this computer or a private test network.";
}

function viewProfile() {
  const profile = store.getProfile();
  const consent = store.getConsent();
  const history = store.getHistory();
  const settings = store.getSettings();
  const pageServer = window.location.protocol.startsWith("http") ? window.location.origin : "";
  viewEl.innerHTML = `<div class="page stack">
    <h1 class="headline">Profile</h1>
    <section class="card"><div class="card-head">${icon("person")}<h2 class="title">Your details</h2>
      <a class="btn-text" href="#/profile/edit">${icon("edit", { size: 18 })}Edit</a></div>
      ${infoRow("Age", `${profile.age} years`)}${infoRow("Biological sex", capitalize(profile.sex))}
      ${profile.guardian_consent ? infoRow("Guardian consent", "Given") : ""}</section>
    <section class="card"><div class="card-head">${icon("privacy")}<h2 class="title">Privacy and data</h2></div>
      ${infoRow("Consent given", formatDateTime(consent.granted_at))}${infoRow("Saved results", String(history.length))}
      <button class="action-row" id="delete-history"${history.length ? "" : " disabled"}>${icon("delete")}<span>Delete saved results</span></button>
      <button class="action-row danger" id="withdraw">${icon("logout")}<span>Withdraw consent and erase data
        <small>Removes your profile, saved results and settings from this browser.</small></span></button></section>
    <section class="card"><div class="card-head">${icon("dns")}<h2 class="title">Server settings</h2></div>
      <label class="small muted" for="server-url">API address</label>
      <input class="text-input mt-6" id="server-url" type="url" inputmode="url" autocomplete="off" spellcheck="false"
        placeholder="${esc(pageServer || "https://api.example.id")}" value="${esc(settings.serverUrl)}">
      <p class="muted tiny mt-6">Leave it empty to use the server that opened this page.</p>
      <label class="small muted block-label mt-12" for="api-key">API key (only if the server requires one)</label>
      <input class="text-input mt-6" id="api-key" type="password" autocomplete="off" value="${esc(settings.apiKey)}">
      <div class="row mt-12"><button class="btn-outline grow-2" id="test">Test connection</button><button class="btn grow" id="save-server">Save</button></div>
      <div class="progress-line" id="testing" hidden></div>
      <p class="muted small mt-10" id="server-status" role="status"></p></section>
    <section class="card"><div class="card-head">${icon("info")}<h2 class="title">About</h2></div>
      <p class="muted small">Glowrithm ${esc(APP_VERSION)}. ${esc(DISCLAIMER)}</p></section>
  </div>`;
  const $ = (selector) => viewEl.querySelector(selector);
  const status = (text) => { $("#server-status").textContent = text; };
  const typedAddress = () => $("#server-url").value.trim().replace(/\/+$/, "");
  const invalid = (value) => value && !api.isValidAddress(value);

  $("#delete-history").addEventListener("click", async () => {
    const confirmed = await confirmDialog({ title: "Delete saved results?", message: "Every saved result in this browser will be removed.",
      confirmLabel: "Delete", destructive: true });
    if (confirmed) { store.clearHistory(); render(); }
  });
  $("#withdraw").addEventListener("click", async () => {
    const confirmed = await confirmDialog({ title: "Withdraw consent?",
      message: "Your profile, saved results and settings will be erased from this browser and you will return to the consent screen.",
      confirmLabel: "Withdraw and erase", destructive: true });
    if (!confirmed) return;
    store.eraseAll();
    setPhoto(null);
    session.result = null;
    go("consent", { replace: true });
  });
  $("#save-server").addEventListener("click", () => {
    const address = typedAddress();
    if (invalid(address)) { status("Enter a full address such as http://192.168.1.20:8000"); return; }
    store.saveSettings({ serverUrl: address, apiKey: $("#api-key").value.trim() });
    status(`Saved. New scans will use ${address || "the server that opened this page"}.`);
  });
  $("#test").addEventListener("click", async () => {
    const address = typedAddress();
    if (invalid(address)) { status("Enter a full address such as http://192.168.1.20:8000"); return; }
    const base = api.baseUrl(address);
    $("#testing").hidden = false;
    status("");
    try {
      const health = await api.health(address);
      const model = health.model_loaded
        ? `model ${health.model_version || "unknown"}${health.demo_mode ? " (demo mode)" : ""}`
        : `no model loaded: ${health.detail || "unknown reason"}`;
      status(`Connected. Server status ${health.status}, ${model}.${connectionNote(base)}`);
    } catch (error) {
      status(error.message);
    } finally {
      $("#testing").hidden = true;
    }
  });
}

window.addEventListener("hashchange", render);
render();
