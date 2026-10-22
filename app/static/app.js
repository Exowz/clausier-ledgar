const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[character]));
const DISPLAY = {tfidf: "TF-IDF", legal_bert_long: "Legal-BERT (up to 10 epochs)", "legal_bert_long fp32": "Legal-BERT", "legal_bert_long int8": "Legal-BERT int8", cpu: "CPU", mps: "Laptop GPU", dense: "MiniLM (dense)", overlap: "Keyword overlap"};
const display = (value) => DISPLAY[value] || value;
const percent = (value) => typeof value === "number" && Number.isFinite(value) ? Math.round(value * 100) + "%" : "not available";
const number = (value, digits = 3) => typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "not available";
const titleCase = (value) => String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const clamp = (value) => Math.max(0, Math.min(1, Number(value) || 0));
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const views = ["classify", "search", "review", "stress", "evidence"];
let sampleContract = "";
let viewTimer;

async function api(url, body) {
  const response = await fetch(url, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request could not be completed.");
  return data;
}

function animateResult(panel) {
  const root = panel.firstElementChild;
  requestAnimationFrame(() => {
    root?.classList.add("shown");
    root?.querySelectorAll("[data-width]").forEach((bar) => { bar.style.width = bar.dataset.width + "%"; });
    root?.querySelectorAll(".ring-fill").forEach((ring) => { ring.style.strokeDashoffset = String(226.2 * (1 - clamp(ring.dataset.confidence))); });
    root?.querySelectorAll("[data-count-to]").forEach(animateCount);
  });
}

function showResult(selector, html, scroll = false) {
  const panel = $(selector);
  panel.innerHTML = '<div class="result-enter">' + html + "</div>";
  animateResult(panel);
  if (scroll) requestAnimationFrame(() => panel.scrollIntoView({behavior: reducedMotion.matches ? "instant" : "smooth", block: "start"}));
}

function errorResult(selector, error) {
  showResult(selector, '<div class="error-box" role="alert">' + escapeHtml(error.message) + "</div>", true);
}

function skeleton(kind) {
  if (kind === "classify") return '<div class="skeleton-stack" aria-hidden="true"><div class="skeleton title"></div><div class="skeleton ring"></div><div class="skeleton line"></div><div class="skeleton line short"></div><div class="skeleton row"></div></div>';
  if (kind === "review") return '<div class="skeleton-stack" aria-hidden="true"><div class="skeleton title"></div><div class="skeleton row"></div><div class="skeleton row"></div><div class="skeleton row"></div></div>';
  return Array.from({length: 2}, () => '<div class="result-card skeleton-stack" aria-hidden="true"><div class="skeleton title"></div><div class="skeleton line"></div><div class="skeleton line short"></div><div class="skeleton row"></div></div>').join("");
}

async function runAction(form, resultSelector, kind, work) {
  const button = form.querySelector('button[type="submit"]');
  const original = button.innerHTML;
  button.disabled = true;
  button.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>Working...</span>';
  showResult(resultSelector, skeleton(kind));
  try { showResult(resultSelector, await work(), true); }
  catch (error) { errorResult(resultSelector, error); }
  finally { button.disabled = false; button.innerHTML = original; }
}

function statusPill(status, label) {
  return '<span class="pill ' + escapeHtml(status) + '">' + escapeHtml(label) + "</span>";
}

function explanationHtml(text, words) {
  if (!words?.length) return '<p class="explanation">' + escapeHtml(text) + "</p>";
  const ordered = [...words].sort((a, b) => a.start - b.start);
  const scale = Math.max(...ordered.map((row) => Math.abs(row.importance)), 0.000001);
  let html = "";
  let cursor = 0;
  for (const row of ordered) {
    if (row.start < cursor || row.end > text.length) continue;
    html += escapeHtml(text.slice(cursor, row.start));
    const strength = Math.min(Math.abs(row.importance) / scale, 1);
    // Words below 8% of the strongest one are shown plain, so that only the decisive words stand out.
    if (strength < 0.08) { html += escapeHtml(text.slice(row.start, row.end)); cursor = row.end; continue; }
    const color = row.importance >= 0
      ? 'rgba(212,168,83,' + (0.13 + 0.42 * strength).toFixed(3) + ')'
      : 'rgba(248,113,113,' + (0.08 + 0.20 * strength).toFixed(3) + ')';
    html += '<span class="word" style="background:' + color + '" title="Importance ' + number(row.importance) + '">' + escapeHtml(text.slice(row.start, row.end)) + "</span>";
    cursor = row.end;
  }
  return '<p class="explanation">' + html + escapeHtml(text.slice(cursor)) + "</p>";
}

function renderClassify(data) {
  const confidence = clamp(data.confidence);
  const handled = data.status === "handled";
  const threshold = percent(data.threshold);
  const target = data.target_accuracy == null ? "" : " The threshold targets " + percent(data.target_accuracy) + " validation accuracy.";
  const types = data.conformal_set?.length
    ? data.conformal_set.map((type) => '<span class="type-chip">' + escapeHtml(type) + "</span>").join("")
    : '<span class="small-note">No type is likely enough. Check by a person.</span>';
  const top = (data.top_types || []).map((row) => '<div class="top-row"><div class="top-row-head"><span>' + escapeHtml(row.type) + '</span><span>' + percent(row.probability) + '</span></div><div class="bar"><span data-width="' + Math.round(clamp(row.probability) * 100) + '"></span></div></div>').join("");
  return '<div class="result-intro"><div><span class="mini-label">Predicted clause type</span><h2 class="verdict-title">' + escapeHtml(data.type) + '</h2></div></div>' +
    '<div class="confidence-display"><svg class="confidence-ring" viewBox="0 0 92 92" role="img" aria-label="Calibrated confidence ' + percent(data.confidence) + '"><circle class="ring-track" cx="46" cy="46" r="36"/><circle class="ring-fill" cx="46" cy="46" r="36" data-confidence="' + confidence + '"/><text x="46" y="53" text-anchor="middle">' + percent(data.confidence) + '</text></svg><div class="confidence-copy"><strong>Calibrated confidence</strong><span class="small-note">Compared with a ' + threshold + ' handling threshold.' + target + '</span></div></div>' +
    '<div class="status-line">' + statusPill(data.status, handled ? "Handled automatically" : "Check by a person") + '</div><hr class="divider"><div class="conformal-label">Prediction set · One of:</div><div class="conformal-chips">' + types + '</div><hr class="divider"><span class="mini-label">Top 3 types</span><div class="top-list">' + top + '</div><hr class="divider"><div class="legend">Words that pushed toward this type</div>' + explanationHtml(data.text || "", data.explanation);
}

function renderSearch(data) {
  const method = {dense:"MiniLM", tfidf:"TF-IDF", overlap:"Keyword overlap"}[data.method] || titleCase(data.method || "");
  const seen = new Set();
  // The clause bank contains some identical clauses: show each text once.
  const rows = (data.results || []).filter((row) => !seen.has(row.text) && seen.add(row.text)).slice(0, 5).map((row, index) => ({...row, rank: index + 1}));
  const filter = data.filtered_days?.length ? '<span class="chip">Filtered on: ' + data.filtered_days.map((day) => escapeHtml(day) + " days").join(", ") + "</span>" : "";
  const header = '<div class="search-header"><span><strong>' + rows.length + '</strong> of 60,000 clauses · ' + escapeHtml(method) + '</span>' + filter + "</div>";
  if (!rows.length) return header + '<div class="result-card"><h2>No matching clauses</h2><p>Try another question or search method.</p></div>';
  return header + '<div class="search-list">' + rows.map((row) => {
    const full = String(row.text || "");
    const short = full.slice(0, 300);
    const more = full.length > 300 ? '<details><summary>Show more</summary><p>' + escapeHtml(full.slice(300)) + '</p></details>' : "";
    return '<article class="result-card search-card"><div class="search-result-head"><span class="rank">' + String(row.rank).padStart(2, "0") + '</span><span class="type-chip">' + escapeHtml(row.type) + '</span><span class="score">Similarity ' + number(row.score) + '</span></div><div class="bar" role="meter" aria-label="Similarity" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + Math.round(clamp(row.score) * 100) + '"><span data-width="' + Math.round(clamp(row.score) * 100) + '"></span></div><p>' + escapeHtml(short) + (full.length > 300 ? "…" : "") + '</p>' + more + '</article>';
  }).join("") + "</div>";
}

function renderReview(data) {
  const clauses = data.clauses || [];
  const checklist = data.checklist || [];
  const summary = data.summary || {clauses: clauses.length, found: 0, missing: []};
  const missing = summary.missing || [];
  const banner = '<div class="result-card summary-banner"><span class="mini-label">Contract overview</span><h2>' + summary.clauses + ' clauses · ' + summary.found + ' standard types found · <span class="missing-text">' + missing.length + ' missing' + (missing.length ? ': ' + missing.map(escapeHtml).join(", ") : "") + '</span></h2></div>';
  const tiles = checklist.map((row, index) => {
    const icon = row.status === "present" ? "✓" : row.status === "check" ? "?" : "×";
    return '<div class="checklist-item ' + escapeHtml(row.status) + '" style="--delay:' + (index * 40) + 'ms"><span class="status-icon" aria-hidden="true">' + icon + '</span><span>' + escapeHtml(row.type) + '</span></div>';
  }).join("");
  const timeline = clauses.map((row) => '<article class="clause-row ' + (row.status === "confident" ? "present" : "check") + '"><div class="clause-row-head"><strong>' + (row.index + 1) + '. ' + escapeHtml(row.type) + '</strong>' + statusPill(row.status === "confident" ? "present" : "check", row.status === "confident" ? "Present" : "Check") + '<span class="small-note">' + percent(row.confidence) + ' confidence</span></div><p class="clause-preview">' + escapeHtml(row.text || "") + '</p><details><summary>Show full clause</summary><p>' + escapeHtml(row.text || "") + '</p></details></article>').join("");
  return banner + '<div class="result-card"><h2>Standard clause checklist</h2><div class="checklist-grid">' + tiles + '</div></div><div class="result-card"><h2>Clauses in order</h2><div class="clause-list">' + (timeline || '<p class="small-note">No clauses found. Separate clauses with blank lines.</p>') + "</div></div>";
}

function changedText(text, indices) {
  const marked = new Set(indices || []);
  return String(text || "").split(/(\s+)/).map((part, index) => {
    if (/^\s+$/.test(part)) return escapeHtml(part);
    return marked.has(Math.floor(index / 2)) ? '<span class="changed-word">' + escapeHtml(part) + "</span>" : escapeHtml(part);
  }).join("");
}

function originalDiff(original, edited) {
  const a = String(original).split(/\s+/);
  const b = String(edited).split(/\s+/);
  let prefix = 0;
  while (prefix < Math.min(a.length, b.length) && a[prefix] === b[prefix]) prefix++;
  let suffix = 0;
  while (suffix < Math.min(a.length - prefix, b.length - prefix) && a[a.length - suffix - 1] === b[b.length - suffix - 1]) suffix++;
  return a.map((word, index) => index < prefix || index >= a.length - suffix ? escapeHtml(word) : '<span class="removed-word">' + escapeHtml(word) + "</span>").join(" ");
}

function renderStress(data) {
  const rows = data.edits || [];
  if (!rows.length) return '<div class="result-card"><h2>No audit edits available</h2></div>';
  return '<div class="result-card"><span class="mini-label">Original prediction</span><h2>' + escapeHtml(data.prediction) + '</h2></div>' + rows.map((row) => {
    if (!row.applies) return '<article class="result-card"><div class="result-intro"><h2>' + titleCase(escapeHtml(row.name)) + '</h2><span class="small-note">Not applicable to this clause</span></div></article>';
    return '<article class="result-card"><div class="result-intro"><h2>' + titleCase(escapeHtml(row.name)) + '</h2>' + statusPill(row.edit_status, row.edit_status) + '</div><div class="stress-pair"><div class="stress-text"><span class="mini-label">Original</span>' + originalDiff(data.original, row.edited_text) + '</div><div class="stress-text"><span class="mini-label">Edited</span>' + changedText(row.edited_text, row.changed_words) + '</div></div><div class="stress-predictions"><div class="prediction-box">Before<strong>' + escapeHtml(row.before) + '</strong></div><div class="prediction-box">After edit<strong>' + escapeHtml(row.after) + '</strong>' + statusPill(row.edit_status, row.edit_status) + '</div><div class="prediction-box">After control<strong>' + escapeHtml(row.control) + '</strong>' + statusPill(row.control_status, row.control_status) + "</div></div></article>";
  }).join("");
}

function table(headers, rows) {
  return '<div class="table-wrap"><table><thead><tr>' + headers.map((header) => "<th>" + escapeHtml(header) + "</th>").join("") + '</tr></thead><tbody>' + rows.map((row) => "<tr>" + row.map((cell) => "<td>" + cell + "</td>").join("") + "</tr>").join("") + "</tbody></table></div>";
}
function evidenceSection(title, content) {
  return '<section class="evidence-card"><h2>' + escapeHtml(title) + "</h2>" + content + "</section>";
}
function kpi(label, value, detail, color = "", suffix = "") {
  if (typeof value !== "number" || !Number.isFinite(value)) return '<div class="kpi-tile"><div class="kpi-label">' + label + '</div><div class="kpi-value unavailable">not available</div><div class="kpi-detail">' + detail + "</div></div>";
  const decimals = Number.isInteger(value) ? 0 : value < 1 ? 3 : 2;
  return '<div class="kpi-tile"><div class="kpi-label">' + label + '</div><div class="kpi-value ' + color + '" data-count-to="' + value + '" data-decimals="' + decimals + '" data-suffix="' + suffix + '">0</div><div class="kpi-detail">' + detail + "</div></div>";
}
function animateCount(node) {
  const target = Number(node.dataset.countTo);
  const decimals = Number(node.dataset.decimals);
  const suffix = node.dataset.suffix || "";
  if (reducedMotion.matches) { node.textContent = target.toFixed(decimals) + suffix; return; }
  const start = performance.now();
  function frame(now) {
    const progress = Math.min((now - start) / 750, 1);
    node.textContent = (target * (1 - Math.pow(1 - progress, 3))).toFixed(decimals) + suffix;
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function renderEvidence(data) {
  const missing = '<p class="small-note">not available</p>';
  const resultsRows = Array.isArray(data.results) ? data.results : [];
  const tfidf = resultsRows.find((row) => row.model?.startsWith("TF-IDF"));
  const bert = resultsRows.find((row) => row.model?.startsWith("Legal-BERT (up to"));
  const coverage = data.calibration?.tfidf?.abstention?.test_coverage;
  const time = Array.isArray(data.cost) ? data.cost.find((row) => row.configuration === "tfidf" && row.device === "cpu")?.ms_per_clause : undefined;
  const rank = data.retrieval?.tfidf?.all?.top_1_accuracy?.[0];
  const kpis = '<div class="kpi-grid">' +
    kpi("Test macro-F1 · TF-IDF", tfidf?.test_macro_f1, "Held-out test set") +
    kpi("Test macro-F1 · Legal-BERT", bert?.test_macro_f1, "Held-out test set", "teal") +
    kpi("Handled automatically", typeof coverage === "number" ? Math.round(coverage * 100) : undefined, "TF-IDF, share of clauses", "", "%") +
    kpi("TF-IDF time per clause", time, "Milliseconds · CPU", "teal") +
    kpi("Retrieval rank-1", typeof rank === "number" ? Math.round(rank * 100) : undefined, "Held-out clauses · TF-IDF", "teal", "%") + '</div>';
  const results = Array.isArray(data.results) ? table(["Model", "Test macro-F1", "Deduplicated macro-F1", "Accuracy"], resultsRows.map((row) => [escapeHtml(row.model), number(row.test_macro_f1), number(row.test_dedup_macro_f1), percent(row.test_accuracy)])) : missing;
  const pair = data.paired_test && data.paired_test !== "not available" ? table(["Comparison", "Macro-F1 difference", "95% interval", "Paired p-value"], [[escapeHtml(display(data.paired_test.a)) + " vs " + escapeHtml(display(data.paired_test.b)), number(data.paired_test.test?.diff_macro_f1, 4), number(data.paired_test.test?.diff_low, 4) + " to " + number(data.paired_test.test?.diff_high, 4), number(data.paired_test.test?.p_value, 4)]]) : missing;
  const calibration = table(["Run", "Temperature", "Confidence threshold", "Test coverage", "Covered accuracy", "Conformal coverage"], ["tfidf", "legal_bert_long"].map((run) => {
    const row = data.calibration?.[run];
    if (!row || row === "not available") return [escapeHtml(display(run)), ...Array(5).fill("not available")];
    return [escapeHtml(display(run)), number(row.temperature), percent(row.abstention?.threshold), percent(row.abstention?.test_coverage), percent(row.abstention?.test_accuracy), percent(row.conformal?.test_coverage)];
  }));
  const retrieval = data.retrieval && data.retrieval !== "not available" ? table(["Method", "Top-1 accuracy", "Precision at 5"], ["dense", "tfidf", "overlap"].map((method) => [escapeHtml(display(method)), percent(data.retrieval?.[method]?.all?.top_1_accuracy?.[0]), percent(data.retrieval?.[method]?.all?.precision_at_5?.[0])])) : missing;
  const cost = Array.isArray(data.cost) ? table(["Configuration", "Device", "Seconds per 1,000 clauses"], data.cost.map((row) => [escapeHtml(display(row.configuration)), escapeHtml(display(row.device)), number(row.seconds_per_1000, 1)])) : missing;
  return '<div class="evidence-stack">' + kpis + evidenceSection("Classification results", results) + evidenceSection("Main paired test", pair) + evidenceSection("Calibration and abstention", calibration) + evidenceSection("Clause retrieval", retrieval) + evidenceSection("Processing cost", cost) + "</div>";
}

const examples = {
  governing: "This Agreement shall be governed by the laws of the State of New York, without regard to its conflict of laws rules.",
  confidentiality: "Each party shall keep the other party's confidential information private and use it only to perform this Agreement.",
  applicable: "Each party shall comply with all applicable laws and regulations in performing its obligations under this Agreement.",
};
function updateCount(textarea) {
  const counter = document.querySelector('[data-count-for="' + textarea.id + '"]');
  if (counter) counter.textContent = textarea.value.length.toLocaleString() + " characters";
}
function setText(selector, value) {
  const textarea = $(selector);
  textarea.value = value;
  updateCount(textarea);
  textarea.focus();
}

function activateView(name, updateHash = true) {
  if (!views.includes(name)) name = "classify";
  window.clearTimeout(viewTimer);
  const change = () => {
    document.querySelectorAll(".nav-item").forEach((item) => {
      const active = item.dataset.view === name;
      item.classList.toggle("active", active);
      if (active) item.setAttribute("aria-current", "page");
      else item.removeAttribute("aria-current");
    });
    document.querySelectorAll(".view").forEach((view) => {
      const active = view.id === "view-" + name;
      view.hidden = !active;
      view.classList.toggle("active", active);
    });
  };
  if (document.querySelector(".view.active")?.id === "view-" + name) change();
  else if (document.startViewTransition && !reducedMotion.matches) document.startViewTransition(change);
  else if (reducedMotion.matches) change();
  else {
    const current = document.querySelector(".view.active");
    current?.classList.add("view-fade-out");
    viewTimer = window.setTimeout(() => {
      change();
      current?.classList.remove("view-fade-out");
      const next = document.querySelector(".view.active");
      next?.classList.add("view-fade-in");
      requestAnimationFrame(() => next?.classList.remove("view-fade-in"));
    }, 180);
  }
  if (updateHash && location.hash !== "#" + name) history.replaceState(null, "", "#" + name);
  if (name === "evidence" && !$("#view-evidence").dataset.loaded) {
    $("#view-evidence").dataset.loaded = "true";
    showResult("#evidence-result", skeleton("review"));
    api("/api/evidence").then((data) => showResult("#evidence-result", renderEvidence(data))).catch((error) => errorResult("#evidence-result", error));
  }
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => activateView(button.dataset.view)));
window.addEventListener("hashchange", () => activateView(location.hash.slice(1), false));
document.querySelectorAll("textarea").forEach((textarea) => { textarea.addEventListener("input", () => updateCount(textarea)); updateCount(textarea); });
document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", () => setText("#classify-text", examples[button.dataset.example])));
document.querySelectorAll("[data-search-example]").forEach((button) => button.addEventListener("click", () => setText("#search-query", button.dataset.searchExample)));
$("#stress-example").addEventListener("click", () => setText("#stress-text", "Licensor grants Licensee the right to use the software. This Agreement shall be governed by New York law."));
$("#load-sample").addEventListener("click", () => setText("#review-text", sampleContract));

$("#classify-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#classify-result", "classify", async () => renderClassify(await api("/api/classify", {text: $("#classify-text").value, model: $("#classify-model").value, explain: true}))); });
$("#search-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#search-result", "search", async () => renderSearch(await api("/api/search", {query: $("#search-query").value, method: $("#search-method").value, k: 10}))); });
$("#review-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#review-result", "review", async () => renderReview(await api("/api/review", {text: $("#review-text").value, model: $("#review-model").value}))); });
$("#stress-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#stress-result", "stress", async () => renderStress(await api("/api/stress", {text: $("#stress-text").value, model: $("#stress-model").value}))); });

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    const form = document.querySelector(".view.active form");
    if (form) { event.preventDefault(); form.requestSubmit(); }
    return;
  }
  if (/^[1-5]$/.test(event.key) && !event.metaKey && !event.ctrlKey && !event.altKey && !event.repeat && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || "") && !document.activeElement?.isContentEditable) {
    event.preventDefault();
    activateView(views[Number(event.key) - 1]);
  }
});

api("/api/models").then((models) => {
  document.querySelectorAll(".model-select").forEach((select) => {
    select.innerHTML = models.map((row) => '<option value="' + escapeHtml(row.id) + '">' + escapeHtml(row.name) + "</option>").join("");
    const preferred = models.find((row) => row.recommended) || models[0];
    if (preferred) select.value = preferred.id;
    const segments = document.querySelector('[data-for="' + select.id + '"]');
    segments.innerHTML = models.map((row) => '<button type="button" class="segment" data-model="' + escapeHtml(row.id) + '" aria-pressed="' + (row.id === select.value) + '">' + (row.id === "tfidf" ? "TF-IDF" : row.id === "legal_bert_long" ? "Legal-BERT" : escapeHtml(row.name)) + "</button>").join("");
    segments.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {
      select.value = button.dataset.model;
      segments.querySelectorAll("button").forEach((segment) => segment.setAttribute("aria-pressed", String(segment === button)));
    }));
  });
  const preferred = models.find((row) => row.recommended) || models[0];
  $("#default-model-badge").textContent = preferred ? (preferred.id === "tfidf" ? "TF-IDF" : preferred.name) + (preferred.recommended ? " · recommended" : "") : "No model available";
}).catch((error) => errorResult("#classify-result", error));
api("/api/sample-contract").then((data) => { sampleContract = data.text || ""; setText("#review-text", sampleContract); $("#review-text").blur(); }).catch(() => {});
activateView(location.hash.slice(1), false);
