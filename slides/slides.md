---
theme: default
title: Clausier
info: Contract clause review, with the evidence
canvasWidth: 1280
aspectRatio: 16/9
fonts:
  provider: none
favicon: /favicon.svg
transition: fade
---

<script setup>
import { deck } from './data'
</script>

<div class="title-slide">
  <div class="title-copy">
    <div class="brand-mark">C</div>
    <h1>Clausier</h1>
    <p class="title-tagline">Contract clause review, with the evidence</p>
    <p class="presenters">Ewan · Wiyao TAKOUGNADI</p>
    <p class="course">Deep Learning for Sequential Data and NLP · Albert School · 23 October 2026</p>
  </div>
  <TypeClause clause="This Agreement shall be governed by the laws of the State of New York." label="Governing Laws" />
  <div class="title-promises">
    <p v-click>Sort every clause into {{ deck.label_distribution.names.length }} types</p>
    <p v-click>Find similar clauses from a question</p>
    <p v-click>Show where it works, and where it must not be trusted</p>
  </div>
</div>

<!--
Speaker: Wiyao. Budget: 1:00.
A start-up wants to help lawyers review large collections of contracts without hiding the evidence. Clausier sorts clauses, finds relevant examples, and makes its limits visible. We will show the product need, the measured results, and the decision we would make from them.
-->

---

<script setup>
import { deck, integer } from './data'
const distribution = {
  animationDuration: 1100,
  grid: { left: 68, right: 30, top: 30, bottom: 105 },
  xAxis: { type: 'category', data: deck.label_distribution.names, axisLabel: { interval: 0, fontSize: 18, formatter: (value, index) => index === 0 || index === deck.label_distribution.names.length - 1 ? value : '' }, axisTick: { show: false } },
  yAxis: { type: 'log', name: 'Training clauses (log scale)', nameTextStyle: { fontSize: 18, align: 'left' }, axisLabel: { fontSize: 18 } },
  series: [{ type: 'bar', data: deck.label_distribution.counts.map((count, index) => ({ value: count, itemStyle: { color: index === 0 || index === deck.label_distribution.counts.length - 1 ? '#0f766e' : '#b7c1c5' }, label: { show: index === 0 || index === deck.label_distribution.counts.length - 1, position: 'top', fontSize: 20, formatter: integer(count) } })), barWidth: '80%' }],
}
const overlap = deck.eda.overlap.exact_duplicates + deck.eda.overlap.near_duplicates
</script>

<div class="deck-slide">
  <h1>{{ deck.label_distribution.names.length }} clause types, very unequal</h1>
  <div class="two-col data-layout">
    <EChart :option="distribution" height="475px" />
    <div class="stat-aside">
      <div class="big-stat"><CountUp :value="Object.values(deck.eda.split_sizes).reduce((sum, n) => sum + n, 0)" /> <span>clauses</span></div>
      <p><strong>{{ integer(overlap) }}</strong> test clauses are near copies of training clauses.</p>
      <p>Every result is also shown without them.</p>
    </div>
  </div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>02</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:40.
LEDGAR has a long tail of clause types, so accuracy alone can hide weak performance on rare types. Macro-F1 gives every type equal weight and is our headline measure. We also repeat the results after removing test clauses that are near copies of training clauses.
-->

---

<script setup>
import { deck } from './data'
</script>

<div class="deck-slide">
  <h1>The course pipeline, end to end</h1>

```mermaid {scale: 0.9}
flowchart LR
  L[LEDGAR] --> T[TF-IDF · m1]
  L --> R[LSTM · m3]
  L --> B[Legal-BERT, BERT-base<br/>full and LoRA · m4]
  T --> P[Paired tests]
  R --> P
  B --> P
  P --> A[Audit · m5]
  L --> M[MiniLM index · m2]
  M --> S[Search]
  A -.-> X[Additions: calibration, cost,<br/>labels, explanations, contracts]
  style X stroke-dasharray: 7 5
```

  <div class="pipeline-lines">
    <p v-click>{{ deck.results_table.length }} trained models</p>
    <p v-click>Main comparison and audit plan written before the runs</p>
    <p v-click>Every number produced by a script</p>
  </div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>03</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:40.
The work follows the course checkpoints from a simple classifier through retrieval and neural models to an audit. The main comparison and audit decisions were set before we looked at the final results. The additional analyses tell us what can be deployed and what still needs review.
-->

---

<script setup>
import { deck, legalBert, tfidf } from './data'
const rows = [...deck.results_table].reverse()
const comparison = deck.pairs.legal_bert_long_vs_tfidf.test
const resultOption = {
  animationDuration: 1200,
  grid: { left: 330, right: 24, top: 20, bottom: 40 },
  xAxis: { type: 'value', min: 0, max: 0.9, axisLabel: { fontSize: 18, formatter: (v) => v.toFixed(1) } },
  yAxis: { type: 'category', data: rows.map(row => row.model.replace('Legal-BERT LoRA', 'LoRA')), axisLabel: { fontSize: 18, color: '#14213d', width: 320, overflow: 'truncate' } },
  series: [
    { name: 'Test', type: 'bar', data: rows.map(row => ({ value: row.test_macro_f1, itemStyle: { color: row.model.startsWith('TF-IDF') ? '#0f766e' : row.model === 'Legal-BERT (up to 10 epochs)' ? '#14213d' : '#9facb6' } })), barWidth: 18 },
    { name: 'Without near copies', type: 'bar', data: rows.map(row => ({ value: row.test_dedup_macro_f1, itemStyle: { color: row.model.startsWith('TF-IDF') ? '#a8d7cf' : row.model === 'Legal-BERT (up to 10 epochs)' ? '#9ba9bd' : '#d5dbde' } })), barWidth: 18 },
  ],
}
</script>

<div class="deck-slide">
  <h1>TF-IDF and Legal-BERT are tied</h1>
  <div class="two-col results-layout">
    <div><EChart :option="resultOption" height="450px" /><p class="legend-note">Test macro-F1: dark bar, full test set; light bar, without near copies</p></div>
    <div class="results-aside">
      <div class="duel"><div><span>TF-IDF</span><strong><CountUp :value="tfidf.test_macro_f1" :decimals="3" /></strong></div><div><span>Legal-BERT</span><strong><CountUp :value="legalBert.test_macro_f1" :decimals="3" /></strong></div></div>
      <p>McNemar p = {{ comparison.p_value.toFixed(2) }}</p>
      <p>Difference {{ comparison.diff_macro_f1.toFixed(3) }} [{{ comparison.diff_low.toFixed(3) }}, {{ comparison.diff_high.toFixed(3) }}]</p>
      <div v-click class="prediction-box">Predicted before the runs: Legal-BERT ahead by {{ deck.planned_advantage_points[0] }} to {{ deck.planned_advantage_points[1] }} points. Wrong. Our rule: then recommend the cheaper TF-IDF.</div>
    </div>
  </div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>04</span></div>
</div>

<!--
Speaker: Ewan. Budget: 1:10.
We predicted that legal pretraining would put Legal-BERT ahead by one to three points. It did not: the two models have essentially identical macro-F1, including after near copies are removed. The paired test and uncertainty interval do not support a meaningful advantage for Legal-BERT. Our decision rule therefore points to TF-IDF.
-->

---

<script setup>
import { deck, legalBert, tfidf } from './data'
const positionRows = [
  { name: 'ChatGPT few-shot', score: deck.chatgpt_zero_shot.few_shot_macro_f1, color: '#b45309' },
  { name: 'ChatGPT zero-shot', score: deck.chatgpt_zero_shot.macro_f1, color: '#d79b4b' },
  { name: 'LexGLUE TF-IDF + SVM', score: deck.lexglue.find(row => row.model === 'TF-IDF + SVM').macro_f1, color: '#adb8be' },
  { name: 'LexGLUE Legal-BERT', score: deck.lexglue.find(row => row.model === 'Legal-BERT').macro_f1, color: '#8b99a5' },
  { name: 'Our TF-IDF', score: tfidf.test_macro_f1 * 100, color: '#0f766e' },
  { name: 'Our Legal-BERT', score: legalBert.test_macro_f1 * 100, color: '#14213d' },
].reverse()
const positionOption = {
  animationDuration: 1100,
  grid: { left: 320, right: 90, top: 20, bottom: 65 },
  xAxis: { type: 'value', min: 0, max: 100, name: 'Macro-F1 (%)', nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18 } },
  yAxis: { type: 'category', data: positionRows.map(row => row.name), axisLabel: { fontSize: 21, color: '#14213d' } },
  series: [{ type: 'bar', data: positionRows.map(row => ({ value: row.score, itemStyle: { color: row.color } })), barWidth: 37, label: { show: true, position: 'right', fontSize: 21, formatter: ({ value }) => value.toFixed(1) } }],
}
</script>

<div class="deck-slide">
  <h1>State of the art, and far ahead of ChatGPT</h1>
  <EChart :option="positionOption" height="420px" />
  <p class="caption">ChatGPT figures: Chalkidis 2023, gpt-3.5-turbo, {{ deck.chatgpt_zero_shot.source.match(/[\d,]+ LEDGAR/)?.[0].replace(' LEDGAR', '') }} test clauses. Published: LexGLUE, ACL 2022.</p>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>05</span></div>
</div>

<!--
Speaker: Wiyao. Budget: 0:40.
Our best results are in the range of the published LexGLUE reference. The ChatGPT result here is an older gpt-3.5-turbo experiment on a smaller test set, so it is context rather than a direct contest with newer systems. Our classifiers answer offline in milliseconds and always return one of the supported clause types.
-->

---

<script setup>
import { deck } from './data'
const lawyer = deck.retrieval.lawyer
</script>

<div class="deck-slide">
  <h1>Ask a question, get the clauses</h1>
  <div class="retrieval-layout">
    <ClauseCloud />
    <div class="retrieval-ranks">
      <p>Right type at rank 1, {{ lawyer.dense.n }} lawyer questions</p>
      <div><span>MiniLM</span><strong>{{ lawyer.dense.rank1 }}</strong><i :style="{ width: `${lawyer.dense.rank1 / lawyer.dense.n * 100}%`, background: '#0f766e' }" /></div>
      <div><span>TF-IDF</span><strong>{{ lawyer.tfidf.rank1 }}</strong><i :style="{ width: `${lawyer.tfidf.rank1 / lawyer.tfidf.n * 100}%`, background: '#14213d' }" /></div>
      <div><span>Keyword overlap</span><strong>{{ lawyer.overlap.rank1 }}</strong><i :style="{ width: `${lawyer.overlap.rank1 / lawyer.overlap.n * 100}%`, background: '#9facb6' }" /></div>
    </div>
  </div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>06</span></div>
</div>

<!--
Speaker: Wiyao. Budget: 1:00.
We embedded the clause bank with MiniLM and search it by cosine similarity. Each point is a real clause in the sampled projection, and the query arrives beside its nearest neighbours. On lawyer-written questions, the dense index finds the right type first more often than either comparison method. This is the retrieval checkpoint in the pipeline.
-->

---

<script setup>
import { cloud, deck, f1 } from './data'
const metrics = deck.retrieval.metrics
const lawyer = deck.retrieval.lawyer
const days = cloud.query.text.match(/\d+/)?.[0]
</script>

<div class="deck-slide">
  <h1>The right method depends on the query</h1>
  <div class="two-col query-compare">
    <div><h2>From a clause</h2><p><strong>TF-IDF {{ f1(metrics.tfidf.deduplicated.top_1_accuracy[0]) }}</strong> vs MiniLM {{ f1(metrics.dense.deduplicated.top_1_accuracy[0]) }} top-1</p></div>
    <div><h2>From a question</h2><p><strong>MiniLM {{ lawyer.dense.rank1 }}/{{ lawyer.dense.n }}</strong> vs TF-IDF {{ lawyer.tfidf.rank1 }}/{{ lawyer.tfidf.n }}</p></div>
  </div>
  <div v-click class="example-card">
    <p class="query-text">“which court has jurisdiction over disputes”</p>
    <p>“The parties agree irrevocably to submit to the exclusive jurisdiction of the federal courts ... located in Boston, Massachusetts”</p>
    <div><span class="label-pill">Venues</span><s>counted wrong</s><span>A lawyer would accept it: the same-label check is strict.</span></div>
  </div>
  <div class="filter-note"><span class="chip">Filter: {{ days }} days</span><span>Durations in the question filter the results.</span></div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>07</span></div>
</div>

<!--
Speaker: Wiyao. Budget: 0:50.
When the query is itself a clause, TF-IDF narrowly leads on the deduplicated test. For a lawyer's natural question, MiniLM leads. A same-label score can mark a useful legal result wrong, as the venue example shows. I will hand over to Ewan for the deployment trade-off and audit.
-->

---

<script setup>
import { deck, integer, legalBert } from './data'
const tf = deck.cost.find(row => row.configuration === 'tfidf' && row.device === 'cpu')
const bertCpu = deck.cost.find(row => row.configuration === 'legal_bert_long fp32' && row.device === 'cpu')
const bertInt8 = deck.cost.find(row => row.configuration === 'legal_bert_long int8' && row.device === 'cpu')
const speed = Math.round((bertCpu.ms_per_clause / tf.ms_per_clause) / 10) * 10
const sizeRatio = bertCpu.size_mb / bertInt8.size_mb
const qualityDrop = (deck.cost_quality.fp32.macro_f1 - deck.cost_quality.int8.macro_f1) * 100
</script>

<div class="deck-slide">
  <h1>Same quality, {{ integer(speed) }} times faster</h1>
  <p class="chart-intro">Time to classify {{ integer(tf.n * 10) }} clauses</p>
  <TimeRace />
  <div class="cost-bottom"><p>Training: {{ integer(deck.tfidf_train_seconds) }} s on a laptop CPU vs {{ Math.floor(legalBert.train_time_min / 60) }} h {{ Math.round(legalBert.train_time_min % 60) }} on a GPU</p><p>int8 Legal-BERT: {{ sizeRatio.toFixed(1) }} times smaller but slower on this laptop, and {{ qualityDrop.toFixed(1) }} points lower</p></div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>08</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:50.
The classification quality is tied, but the cost is not. For a large batch on this laptop CPU, TF-IDF finishes much sooner than Legal-BERT, even compared with the laptop GPU run. It also trains in seconds rather than hours. Quantization shrinks the BERT file but did not improve this laptop's speed.
-->

---

<script setup>
import { deck } from './data'
const audit = deck.counterfactual.legal_bert_long
const categories = [['party_roles', 'Party roles'], ['jurisdiction', 'Jurisdiction'], ['number_format', 'Number format']]
const threshold = deck.counterfactual_fail_threshold
const auditOption = {
  animationDuration: 1000,
  grid: { left: 65, right: 30, top: 70, bottom: 80 },
  legend: { top: 5, textStyle: { fontSize: 19 } },
  xAxis: { type: 'category', data: categories.map(row => row[1]), axisLabel: { fontSize: 19, color: '#14213d' } },
  yAxis: { type: 'value', max: 0.04, name: 'Flip rate', axisLabel: { fontSize: 18, formatter: (v) => `${Math.round(v * 100)}%` }, nameTextStyle: { fontSize: 18 } },
  series: [
    { name: 'Edit', type: 'bar', data: categories.map(row => audit[row[0]].flip_rate), itemStyle: { color: '#14213d' }, barWidth: 45, markLine: { symbol: 'none', label: { formatter: 'fail threshold fixed in advance', fontSize: 18, position: 'insideEndTop' }, lineStyle: { type: 'dashed', color: '#b91c1c' }, data: [{ yAxis: threshold }] } },
    { name: 'Control', type: 'bar', data: categories.map(row => audit[row[0]].ctrl_flip_rate), itemStyle: { color: '#aab7bf' }, barWidth: 45 },
  ],
}
</script>

<div class="deck-slide">
  <h1>Robust to parties, laws and number formats</h1>
  <div class="two-col audit-layout">
    <div class="audit-chart"><div class="pass-row"><span v-for="row in categories" :key="row[0]" class="pass-tag">{{ audit[row[0]].decision }}</span></div><EChart :option="auditOption" height="420px" /><p class="chart-note">Party roles: {{ (audit.party_roles.flip_rate * 100).toFixed(1) }}%, just above the line, but no more than its control ({{ (audit.party_roles.ctrl_flip_rate * 100).toFixed(1) }}%): pass by the rule.</p></div>
    <div class="audit-aside"><strong>Known weakness</strong><p>Lease contracts: accuracy {{ deck.lease_slice.accuracy.toFixed(3) }} against {{ deck.lease_slice.overall_accuracy.toFixed(3) }} overall.</p><p>Flagged for review.</p></div>
  </div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>09</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:50.
We used CheckList-style edits with controls and a decision rule fixed before the tests. All three edits pass that rule, including the party-role change that sits near the threshold. The slice audit still finds a serious weakness on lease contracts, so passing stress tests is not a general assurance.
-->

---

<script setup>
import { deck } from './data'
const taxonomy = deck.taxonomy
const share = taxonomy.runs[1].share_errors_removed * 100
</script>

<div class="deck-slide">
  <h1>A fifth of the errors are the label set, not the model</h1>
  <div class="two-col taxonomy-layout"><LabelMerge /><div class="taxonomy-aside"><div class="big-stat"><CountUp :value="share" :decimals="0" suffix="%" /></div><p>of Legal-BERT errors removed after merging overlapping labels</p><p>Paired accuracy p = {{ taxonomy.paired_tests.test.p_value.toFixed(3) }}</p></div></div>
  <p class="recommend-line">Recommendation: review these {{ taxonomy.pairs.length }} pairs with the start-up's lawyers.</p>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>10</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:50.
This was an exploratory analysis outside the original plan. Nine label pairs describe closely overlapping legal ideas, and merging them removes about a fifth of Legal-BERT's errors. The paired accuracy test shows a difference after merging. Lawyers should decide whether the distinctions are useful before we collect more examples.
-->

---

<script setup>
import { deck } from './data'
const trust = deck.calibration.legal_bert_long
const recommended = deck.calibration.tfidf
const handled = recommended.abstention.test_coverage * 100
const human = recommended.abstention.share_sent_to_human * 100
</script>

<div class="deck-slide">
  <h1>It knows when to ask a person</h1>
  <div class="two-col trust-layout"><Reliability /><div class="trust-aside"><div class="trust-stat"><strong><CountUp :value="handled" :decimals="0" suffix="%" /></strong><span>handled automatically, {{ (recommended.abstention.test_accuracy * 100).toFixed(1) }}% of them right</span><small>TF-IDF; Legal-BERT {{ (trust.abstention.test_coverage * 100).toFixed(1) }}%</small></div><div class="trust-stat"><strong><CountUp :value="human" :decimals="0" suffix="%" /></strong><span>sent to a person</span></div><p>Prediction sets: {{ Math.round(trust.conformal.test_coverage * 100) }}% coverage with {{ trust.conformal.mean_set_size.toFixed(2) }} types per clause.</p></div></div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>11</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:50.
Temperature scaling is fitted on validation data, then checked on the test set. Legal-BERT's confidence is much closer to its observed accuracy after scaling; TF-IDF was already well calibrated. At the chosen threshold, some clauses still go to a person, and the prediction sets are usually very small. The figures are measured outcomes, not guarantees for a new contract population.
-->

---
transition: none
---

<div class="deck-slide demo-slide">
  <h1>Demo</h1>
  <div class="demo-frame"><h2>Live demo</h2><p>http://127.0.0.1:5050</p><div>Classify <span>·</span> Search <span>·</span> Missing clauses <span>·</span> Stress tests <span>·</span> Evidence</div></div>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>12</span></div>
</div>

<!--
Speaker: Wiyao for search, then Ewan. Budget: 1:00.
Wiyao enters a lawyer question and shows the matching clauses and their types. Ewan then shows classification confidence, a missing-clause check, and the evidence view. We keep the demo short so the decision and limits remain the closing message.
-->

---

<script setup>
import { deck } from './data'
const human = Math.round(deck.calibration.tfidf.abstention.share_sent_to_human * 100)
</script>

<div class="deck-slide closing-slide">
  <h1>What we recommend to the start-up</h1>
  <div class="closing-list">
    <p v-click>TF-IDF to classify, with calibrated confidence and a person for the {{ human }}% it is unsure of</p>
    <p v-click>MiniLM to search from a lawyer's question</p>
    <p v-click>Review {{ deck.taxonomy.pairs.length }} overlapping label pairs before collecting more data</p>
    <p v-click>Not for non-US contracts, never without human review: not legal advice</p>
  </div>
  <p class="repo-line">Code, results and model card: github.com/Exowz/clausier-ledgar</p>
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>13</span></div>
</div>

<!--
Speaker: Ewan. Budget: 0:40.
The business choice is the cheaper classifier with confidence and a person in the loop. We pair it with MiniLM when the input is a lawyer's question. Before expanding the dataset, we would have lawyers resolve the overlapping labels. This is for reviewed US contract work and is not legal advice.
-->

---

<div class="deck-slide">
  <h1>Backup: validation macro-F1 per epoch</h1>
  <img src="/figures/validation_curves.png" style="height: 520px; margin: 0 auto; display: block;" />
  <div class="deck-footer"><span>Clausier · LEDGAR</span><span>Backup</span></div>
</div>

<!--
Backup for questions on training length. Every 4-epoch run was still rising at its last epoch, so we added the 10-epoch runs, decided on the validation curve only. Full fine-tuning levels off from epoch 7; LoRA is still rising at epoch 10. The 10-epoch run starts lower because its warmup lasts a whole epoch.
-->
