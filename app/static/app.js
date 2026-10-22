const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[character]);
const percent = (value) => typeof value === "number" ? `${Math.round(value * 100)}%` : "not available";
const number = (value, digits = 3) => typeof value === "number" ? value.toFixed(digits) : "not available";
const available = (value) => value === "not available" || value == null ? "not available" : escapeHtml(value);
const titleCase = (value) => String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

async function api(url, body) {
  const response = await fetch(url, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request could not be completed.");
  return data;
}

function showResult(selector, html) {
  const panel = $(selector);
  panel.innerHTML = `<div class="result-enter">${html}</div>`;
  requestAnimationFrame(() => panel.firstElementChild?.classList.add("shown"));
}

function errorResult(selector, error) {
  showResult(selector, `<div class="error-box" role="alert">${escapeHtml(error.message)}</div>`);
}

async function runAction(form, resultSelector, work) {
  const button = form.querySelector('button[type="submit"]');
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = "Working...";
  try { showResult(resultSelector, await work()); }
  catch (error) { errorResult(resultSelector, error); }
  finally { button.disabled = false; button.innerHTML = original; }
}

function statusPill(status, label) {
  return `<span class="pill ${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

function explanationHtml(text, words) {
  if (!words?.length) return `<p class="explanation">${escapeHtml(text)}</p>`;
  const scale = Math.max(...words.map((row) => Math.abs(row.importance)), 0.000001);
  let html = "";
  let cursor = 0;
  for (const row of words) {
    html += escapeHtml(text.slice(cursor, row.start));
    const strength = Math.min(Math.abs(row.importance) / scale, 1);
    const color = row.importance >= 0 ? `rgba(15,118,110,${(0.09 + 0.48 * strength).toFixed(3)})` : `rgba(185,28,28,${(0.09 + 0.40 * strength).toFixed(3)})`;
    html += `<span class="word" style="background:${color}" title="Importance ${number(row.importance)}">${escapeHtml(text.slice(row.start, row.end))}</span>`;
    cursor = row.end;
  }
  html += escapeHtml(text.slice(cursor));
  return `<p class="explanation">${html}</p>`;
}

function renderClassify(data) {
  const handled = data.status === "handled";
  const target = data.target_accuracy == null ? "" : `, chosen for ${percent(data.target_accuracy)} accuracy on validation`;
  const top = (data.top_types || []).map((row) => `<div class="top-row"><span>${escapeHtml(row.type)}</span><span>${percent(row.probability)}</span></div>`).join("");
  const conformal = data.conformal_set?.length ? `One of: ${data.conformal_set.map(escapeHtml).join(", ")}` : "No type is likely enough: check by a person";
  return `<div class="result-intro"><div><span class="mini-label">Predicted clause type</span><h2>${escapeHtml(data.type)}</h2></div>${statusPill(data.status, handled ? "Handled automatically" : "Check by a person")}</div>
    <div class="confidence-row"><span>Calibrated confidence</span><strong>${percent(data.confidence)}</strong></div><div class="bar" role="meter" aria-label="Calibrated confidence" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(data.confidence * 100)}"><span style="width:${Math.max(0, Math.min(100, data.confidence * 100))}%"></span></div>
    <div class="small-note">threshold ${percent(data.threshold)}${target}</div><hr class="divider"><div class="conformal">${escapeHtml(conformal)}</div><div class="top-list">${top}</div><hr class="divider"><span class="mini-label">Words behind the prediction</span>${explanationHtml(data.text, data.explanation)}`;
}

function renderSearch(data) {
  const chip = data.filtered_days?.length ? `<div class="chip">Filtered on: ${data.filtered_days.map((day) => `${day} days`).join(", ")}</div>` : "";
  if (!data.results?.length) return `${chip}<div class="result-card"><h2>No matching clauses</h2><p>Try another question or search method.</p></div>`;
  return `${chip}<div class="search-list">${data.results.map((row) => {
    const short = row.text.slice(0, 400);
    const more = row.text.length > 400 ? `<details><summary>Read full clause</summary><p>${escapeHtml(row.text)}</p></details>` : "";
    return `<article class="result-card"><div class="search-result-head"><span class="rank">${row.rank.toString().padStart(2, "0")}</span><strong>${escapeHtml(row.type)}</strong><span class="score">Score ${number(row.score)}</span></div><p>${escapeHtml(short)}${row.text.length > 400 ? "…" : ""}</p>${more}</article>`;
  }).join("")}</div>`;
}

function renderReview(data) {
  const summary = data.summary || {clauses: data.clauses.length, found: 0, missing: []};
  const missing = summary.missing.length ? `: ${summary.missing.map(escapeHtml).join(", ")}` : "";
  const checklist = data.checklist.map((row) => `<div class="checklist-item"><span>${escapeHtml(row.type)}</span>${statusPill(row.status, row.status)}</div>`).join("");
  const clauses = data.clauses.map((row) => `<article class="clause-row"><div class="clause-row-head"><strong>${row.index + 1}. ${escapeHtml(row.type)}</strong>${statusPill(row.status === "confident" ? "present" : "check", row.status === "confident" ? "Present" : "Check")}<span class="small-note">${percent(row.confidence)} confidence</span></div><p>${escapeHtml(row.text || "")}</p></article>`).join("");
  return `<div class="result-card"><p class="summary-line"><strong>${summary.clauses} clauses, ${summary.found} standard types found, ${summary.missing.length} missing${missing}</strong></p><h2>Standard clause checklist</h2><div class="checklist-grid">${checklist}</div></div><div class="result-card"><h2>Clauses in order</h2><div class="clause-list">${clauses || "No clauses found. Separate clauses with blank lines."}</div></div>`;
}

function changedText(text, indices) {
  const marked = new Set(indices);
  return text.split(/(\s+)/).map((part, index) => {
    if (/^\s+$/.test(part)) return escapeHtml(part);
    const wordIndex = Math.floor(index / 2);
    return marked.has(wordIndex) ? `<span class="changed-word">${escapeHtml(part)}</span>` : escapeHtml(part);
  }).join("");
}

function renderStress(data) {
  const applied = data.edits.filter((row) => row.applies);
  if (!applied.length) return `<div class="result-card"><h2>No audit edits apply</h2><p>Try a clause with named party roles, New York or Delaware law, or a duration.</p></div>`;
  return `<div class="result-card"><span class="mini-label">Original prediction</span><h2>${escapeHtml(data.prediction)}</h2></div>${applied.map((row) => `<article class="result-card"><div class="result-intro"><h2>${titleCase(row.name)}</h2>${statusPill(row.edit_status, row.edit_status)}</div><p class="explanation">${changedText(row.edited_text, row.changed_words)}</p><div class="stress-predictions"><div class="prediction-box">Before<strong>${escapeHtml(row.before)}</strong></div><div class="prediction-box">After edit<strong>${escapeHtml(row.after)}</strong></div><div class="prediction-box">After control<strong>${escapeHtml(row.control)}</strong>${statusPill(row.control_status, row.control_status)}</div></div></article>`).join("")}`;
}

function table(headers, rows) {
  return `<div class="table-wrap"><table><thead><tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function evidenceSection(title, content) {
  return `<section class="evidence-card"><h2>${escapeHtml(title)}</h2>${content}</section>`;
}

function renderEvidence(data) {
  const missing = `<p class="small-note">not available</p>`;
  const results = Array.isArray(data.results) ? table(["Model", "Test macro-F1", "Deduplicated macro-F1", "Accuracy"], data.results.map((row) => [escapeHtml(row.model), number(row.test_macro_f1), number(row.test_dedup_macro_f1), percent(row.test_accuracy)])) : missing;
  const pair = data.paired_test === "not available" ? missing : table(["Comparison", "Macro-F1 difference", "95% interval", "Paired p-value"], [[`${escapeHtml(data.paired_test.a)} vs ${escapeHtml(data.paired_test.b)}`, number(data.paired_test.test.diff_macro_f1, 4), `${number(data.paired_test.test.diff_low, 4)} to ${number(data.paired_test.test.diff_high, 4)}`, number(data.paired_test.test.p_value, 4)]]);
  const calibration = table(["Run", "Temperature", "Confidence threshold", "Test coverage", "Covered accuracy", "Conformal coverage"], ["tfidf", "legal_bert_long"].map((run) => {
    const row = data.calibration?.[run];
    if (!row || row === "not available") return [escapeHtml(run), ...Array(5).fill("not available")];
    return [escapeHtml(run), number(row.temperature), percent(row.abstention?.threshold), percent(row.abstention?.test_coverage), percent(row.abstention?.test_accuracy), percent(row.conformal?.test_coverage)];
  }));
  const retrieval = data.retrieval === "not available" ? missing : table(["Method", "Top-1 accuracy", "Precision at 5"], ["dense", "tfidf", "overlap"].map((method) => [titleCase(method), percent(data.retrieval?.[method]?.all?.top_1_accuracy?.[0]), percent(data.retrieval?.[method]?.all?.precision_at_5?.[0])]));
  const cost = Array.isArray(data.cost) ? table(["Configuration", "Device", "Seconds per 1,000 clauses"], data.cost.map((row) => [escapeHtml(row.configuration), escapeHtml(row.device), number(row.seconds_per_1000, 1)])) : missing;
  return `<div class="evidence-stack">${evidenceSection("Classification results", results)}${evidenceSection("Main paired test", pair)}${evidenceSection("Calibration and abstention", calibration)}${evidenceSection("Clause retrieval", retrieval)}${evidenceSection("Processing cost", cost)}</div>`;
}

const examples = {
  governing: "This Agreement shall be governed by the laws of the State of New York, without regard to its conflict of laws rules.",
  confidentiality: "Each party shall keep the other party's confidential information private and use it only to perform this Agreement.",
  applicable: "Each party shall comply with all applicable laws and regulations in performing its obligations under this Agreement.",
};

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach((item) => { item.classList.remove("active"); item.removeAttribute("aria-current"); });
  button.classList.add("active"); button.setAttribute("aria-current", "page");
  document.querySelectorAll(".view").forEach((view) => { view.hidden = true; view.classList.remove("active"); });
  const active = $(`#view-${button.dataset.view}`);
  active.hidden = false; active.classList.add("active");
  if (button.dataset.view === "evidence" && !active.dataset.loaded) {
    active.dataset.loaded = "true";
    showResult("#evidence-result", `<div class="result-card">Loading evidence...</div>`);
    api("/api/evidence").then((data) => showResult("#evidence-result", renderEvidence(data))).catch((error) => errorResult("#evidence-result", error));
  }
}));

document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", () => { $("#classify-text").value = examples[button.dataset.example]; $("#classify-text").focus(); }));
document.querySelectorAll("[data-search-example]").forEach((button) => button.addEventListener("click", () => { $("#search-query").value = button.dataset.searchExample; $("#search-query").focus(); }));
$("#stress-example").addEventListener("click", () => { $("#stress-text").value = "Licensor grants Licensee the right to use the software. This Agreement shall be governed by New York law."; $("#stress-text").focus(); });

$("#classify-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#classify-result", async () => renderClassify(await api("/api/classify", {text: $("#classify-text").value, model: $("#classify-model").value, explain: true}))); });
$("#search-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#search-result", async () => renderSearch(await api("/api/search", {query: $("#search-query").value, method: $("#search-method").value, k: 5}))); });
$("#review-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#review-result", async () => renderReview(await api("/api/review", {text: $("#review-text").value, model: $("#review-model").value}))); });
$("#stress-form").addEventListener("submit", (event) => { event.preventDefault(); runAction(event.currentTarget, "#stress-result", async () => renderStress(await api("/api/stress", {text: $("#stress-text").value, model: $("#stress-model").value}))); });

document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    const active = document.querySelector(".view.active form");
    if (active) { event.preventDefault(); active.requestSubmit(); }
  }
});

api("/api/models").then((models) => {
  document.querySelectorAll(".model-select").forEach((select) => {
    select.innerHTML = models.map((row) => `<option value="${escapeHtml(row.id)}">${escapeHtml(row.name)}${row.recommended ? " (recommended)" : ""}</option>`).join("");
  });
}).catch((error) => errorResult("#classify-result", error));
api("/api/sample-contract").then((data) => { $("#review-text").value = data.text; }).catch(() => {});
