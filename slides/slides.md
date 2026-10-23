---
theme: default
title: Clausier
info: Contract clause review, with the evidence
canvasWidth: 1280
aspectRatio: 16/9
fonts:
  provider: none
favicon: /favicon.svg
transition: deck-sweep | deck-sweep-back
---

<script setup>
import { deck } from '@deck'
</script>

<div class="title-slide">
  <Stage />
  <ClauseField />
  <div class="title-copy">
    <Headline text="Clausier" eyebrow="CONTRACT REVIEW, WITH THE EVIDENCE" />
    <p data-r="1" class="presenters">Mathew Kristoffer Ewan KAPOOR · Wiyao TAKOUGNADI</p>
    <p data-r="2" class="course">Deep Learning for Sequential Data and NLP · Albert School · 23 October 2026</p>
  </div>
  <TypeClause clause="This Agreement shall be governed by the laws of the State of New York." label="Governing Laws" />
  <DeckFooter n="01" speaker="Wiyao" />
  <div class="title-promises">
    <p v-click>Sort every clause into {{ deck.label_distribution.names.length }} types</p>
    <p v-click>Find similar clauses from a question</p>
    <p v-click>Show where it works, and where it must not be trusted</p>
  </div>
</div>

<!--
**WIYAO · about 1 minute**

Good morning. Every contract review starts the same way: someone reads the contract and sorts it, clause by clause. Which one is the governing law, which one is the termination, and which one is missing. For a law firm, that is hours of expensive, repetitive reading.

Our client is a European legal-tech start-up. They asked us to build the language core of a contract-review assistant, and they asked for three things.

[click] First, sort every clause into one of the 100 clause types of the LEDGAR dataset.

[click] Second, find similar clauses in a clause bank, from a pasted clause or from a lawyer's question in plain English.

[click] Third, and they insisted on this: show the evidence. Where it works, where it fails, and what it must never be used for.

Ewan will start with the data.
-->

---

<script setup>
import { deck, integer } from '@deck'
const distribution = {
  animationDuration: 850,
  animationDelay: (index) => index * 14,
  grid: { left: 68, right: 30, top: 30, bottom: 105 },
  xAxis: { type: 'category', data: deck.label_distribution.names, axisLabel: { interval: 0, fontSize: 18, color: '#8a94a6', formatter: (value, index) => index === 0 || index === deck.label_distribution.names.length - 1 ? value : '' }, axisTick: { show: false } },
  yAxis: { type: 'log', name: 'Training clauses (log scale)', nameTextStyle: { fontSize: 18, color: '#8a94a6', align: 'left' }, axisLabel: { fontSize: 18, color: '#8a94a6' }, splitLine: { lineStyle: { color: 'rgba(244,239,230,.10)' } } },
  series: [{ type: 'bar', data: deck.label_distribution.counts.map((count, index) => ({ value: count, itemStyle: { color: index === 0 || index === deck.label_distribution.counts.length - 1 ? '#d4a853' : '#475569' }, label: { show: index === 0 || index === deck.label_distribution.counts.length - 1, position: 'top', fontSize: 20, color: '#d4a853', formatter: integer(count) } })), barWidth: '80%' }],
}
const overlap = deck.eda.overlap.exact_duplicates + deck.eda.overlap.near_duplicates
</script>

<div class="deck-slide">
  <Stage />
  <Headline :text="`${deck.label_distribution.names.length} clause types, very unequal`" eyebrow="DATA" emphasis="unequal" />
  <div class="two-col data-layout">
    <EChart :option="distribution" height="475px" />
    <div class="stat-aside">
      <div data-r="1" class="big-stat"><CountUp :value="Object.values(deck.eda.split_sizes).reduce((sum, n) => sum + n, 0)" /> <span class="stat-unit">clauses</span></div>
      <p data-r="2"><strong>{{ integer(overlap) }}</strong> test clauses are near copies of training clauses.</p>
      <p data-r="3">Every result is also shown without them.</p>
    </div>
  </div>
  <DeckFooter n="02" speaker="Ewan" />
</div>

<!--
**EWAN · about 40 seconds**

The data is LEDGAR, from the LexGLUE benchmark: 80,000 clauses from contracts filed with the US Securities and Exchange Commission, split into 60,000 for training, 10,000 for validation and 10,000 for test.

The chart shows the main difficulty: the 100 types are very unequal. Governing Laws has 3,167 training clauses, Books only 23. A model can look good on accuracy while failing every rare type, so our headline metric is macro-F1, which gives every type the same weight.

We also found that 2,241 test clauses are copies or near copies of training clauses. So every result is reported twice: on the full test set, and on the 7,759 clauses left once those copies are removed.

**If asked: why remove near copies?** Contracts reuse boilerplate, so 451 test clauses are exact copies of training clauses and 1,790 are near copies (TF-IDF cosine of at least 0.9). They make every model look better than it will be on a client's new contracts: both our best models lose 3.8 macro-F1 points without them. So the realistic figure for the client is about 0.79, not 0.83.
-->

---
transition: deck-iris | deck-sweep-back
---

<script setup>
import { deck } from '@deck'
</script>

<div class="deck-slide pipeline-slide">
  <Stage />
  <PipelineMotion />
  <Headline text="The course pipeline, end to end" eyebrow="PIPELINE" emphasis="pipeline" />

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
  style X stroke:#d4a853,stroke-dasharray:7 5,color:#f4efe6,fill:#111a2e
```

  <div class="pipeline-lines">
    <p v-click>{{ deck.results_table.length }} trained models</p>
    <p v-click>Main comparison and audit plan written before the runs</p>
    <p v-click>Every number produced by a script</p>
  </div>
  <DeckFooter n="03" speaker="Ewan" />
</div>

<!--
**EWAN · about 40 seconds**

This is our pipeline, and it follows the course checkpoints. TF-IDF with logistic regression is the baseline, checkpoint m1. An LSTM trained from scratch is m3. The fine-tuned transformers, Legal-BERT and BERT-base, with full fine-tuning and with LoRA, are m4. The MiniLM sentence-embedding index for search is m2, and the bias audit is m5. On top, our own additions: calibration, cost, label overlap, explanations and contract checks.

[click] In total we trained 8 models.

[click] Before running anything, we committed our prediction for the main comparison and our audit plan, with their decision rules. So we could not adjust the story to the results.

[click] And every number you will see is produced by a script in the repository.
-->

---
transition: deck-rise | deck-sweep-back
---

<script setup>
import { deck, legalBert, tfidf } from '@deck'
const rows = [...deck.results_table].reverse()
const comparison = deck.pairs.legal_bert_long_vs_tfidf.test
const resultOption = {
  animationDuration: 1200,
  animationDelay: 1550,
  grid: { left: 280, right: 18, top: 6, bottom: 30 },
  xAxis: { type: 'value', min: 0, max: 0.9, axisLabel: { fontSize: 18, formatter: (v) => v.toFixed(1) } },
  yAxis: { type: 'category', data: rows.map(row => row.model.replace('Legal-BERT LoRA', 'LoRA')), axisLabel: { fontSize: 18, color: '#8a94a6', width: 320, overflow: 'truncate' } },
  series: [
    { name: 'Test', type: 'bar', data: rows.map(row => ({ value: row.test_macro_f1, itemStyle: { color: row.model.startsWith('TF-IDF') ? '#d4a853' : row.model === 'Legal-BERT (up to 10 epochs)' ? '#2dd4bf' : '#475569' } })), barWidth: 12 },
    { name: 'Without near copies', type: 'bar', data: rows.map(row => ({ value: row.test_dedup_macro_f1, itemStyle: { color: row.model.startsWith('TF-IDF') ? '#806a44' : row.model === 'Legal-BERT (up to 10 epochs)' ? '#286f70' : '#334155' } })), barWidth: 12 },
  ],
}
</script>

<div class="deck-slide results-slide">
  <Stage />
  <Headline text="TF-IDF and Legal-BERT are tied" eyebrow="RESULTS" emphasis="tied" />
  <div data-r="1" class="duel">
    <div><span class="duel-label">TF-IDF</span><strong><CountUp :value="tfidf.test_macro_f1" :decimals="3" /></strong></div>
    <span class="duel-equals">≈</span>
    <div><span class="duel-label">Legal-BERT</span><strong><CountUp :value="legalBert.test_macro_f1" :decimals="3" /></strong></div>
  </div>
  <p class="results-evidence">McNemar p = {{ comparison.p_value.toFixed(2) }}, difference {{ comparison.diff_macro_f1.toFixed(3) }} [{{ comparison.diff_low.toFixed(3) }}, {{ comparison.diff_high.toFixed(3) }}]</p>
  <div data-r="4" class="results-chart"><EChart :option="resultOption" height="265px" /><p class="legend-note">Bright bar: full test set · dim bar: without near copies</p></div>
  <div v-click class="prediction-box">Predicted before the runs: <span class="wrong">Legal-BERT ahead by {{ deck.planned_advantage_points[0] }} to {{ deck.planned_advantage_points[1] }} points</span> <span class="wrong-word">Wrong.</span> <span class="rule">Our rule: recommend the cheaper TF-IDF.</span></div>
  <DeckFooter n="04" speaker="Ewan" />
</div>

<!--
**EWAN · about 1 minute 10**

This is the main result. Our tuned TF-IDF baseline reaches a test macro-F1 of 0.826. Legal-BERT, a BERT model pre-trained on legal text and fine-tuned for up to 10 epochs, reaches 0.825.

They are tied. The paired McNemar test gives p = 0.20, and the bootstrap interval on the difference, from minus 0.010 to plus 0.011, contains zero. The conclusion is the same on the deduplicated test set.

Below, all 8 models. The LSTMs are about 8 points lower. LoRA trains only 0.34% of the weights and loses 1 to 2 points. And Legal-BERT beats the general BERT-base by 1.3 points, significantly: legal pre-training does help.

[click] Our written prediction said Legal-BERT would win by 1 to 3 points. That was wrong, and we report it as wrong. But we had also written the rule: if Legal-BERT does not significantly beat TF-IDF on the deduplicated test set, recommend the cheaper model. So we recommend TF-IDF.
-->

---

<script setup>
import { deck, legalBert, tfidf } from '@deck'
const positionRows = [
  { name: 'ChatGPT few-shot', score: deck.chatgpt_zero_shot.few_shot_macro_f1, color: '#f59e0b' },
  { name: 'ChatGPT zero-shot', score: deck.chatgpt_zero_shot.macro_f1, color: '#f59e0b' },
  { name: 'LexGLUE TF-IDF + SVM', score: deck.lexglue.find(row => row.model === 'TF-IDF + SVM').macro_f1, color: '#475569' },
  { name: 'LexGLUE Legal-BERT', score: deck.lexglue.find(row => row.model === 'Legal-BERT').macro_f1, color: '#334155' },
  { name: 'Our TF-IDF', score: tfidf.test_macro_f1 * 100, color: '#d4a853' },
  { name: 'Our Legal-BERT', score: legalBert.test_macro_f1 * 100, color: '#2dd4bf' },
].reverse()
const positionOption = {
  animationDuration: 1050,
  animationDelay: (index) => (5 - index) * 250,
  grid: { left: 320, right: 380, top: 20, bottom: 40 },
  xAxis: { type: 'value', min: 0, max: 100, axisLabel: { fontSize: 18, formatter: (v) => `${v}` } },
  yAxis: { type: 'category', data: positionRows.map(row => row.name), axisLabel: { fontSize: 21, color: '#f4efe6' } },
  series: [{ type: 'bar', data: positionRows.map(row => ({ value: row.score, itemStyle: { color: row.color } })), barWidth: 37, label: { show: true, position: 'right', fontSize: 21, color: '#f4efe6', formatter: ({ value }) => value.toFixed(1) } }],
}
</script>

<div class="deck-slide position-slide">
  <Stage />
  <Headline text="State of the art, and far ahead of ChatGPT" eyebrow="POSITIONING" emphasis="ChatGPT" />
  <EChart :option="positionOption" height="420px" />
  <div class="position-gap">+{{ Math.round(tfidf.test_macro_f1 * 100 - deck.chatgpt_zero_shot.macro_f1) }}<small>macro-F1 points for our TF-IDF over ChatGPT zero-shot</small></div>
  <p data-r="6" class="caption">ChatGPT figures: Chalkidis 2023, gpt-3.5-turbo, {{ deck.chatgpt_zero_shot.source.match(/[\d,]+ LEDGAR/)?.[0].replace(' LEDGAR', '') }} test clauses. Published: LexGLUE, ACL 2022.</p>
  <DeckFooter n="05" speaker="Wiyao" />
</div>

<!--
**WIYAO · about 40 seconds**

How does this compare with the state of the art? The LexGLUE benchmark publishes results on this exact test set: 83.0 macro-F1 for their Legal-BERT. Ours reaches 82.5, with the same 88.2 micro-F1, while reading 256 tokens instead of 512. And our TF-IDF beats their published TF-IDF baseline.

Then the question every client asks: why not just use ChatGPT? A 2023 study tested it on the same task: 56.7 macro-F1 without examples, and even lower with examples. Our classifier is 26 points ahead.

To be fair, newer models may do better. But ours answers in milliseconds, offline, always with one of the 100 types, and no contract ever leaves the client's machine.

**If asked: the sources.** LexGLUE: Chalkidis and colleagues, ACL 2022, the benchmark that includes LEDGAR. ChatGPT: Chalkidis 2023, "ChatGPT may pass the bar exam soon, but has a long way to go for the LexGLUE benchmark", gpt-3.5-turbo on 1,000 LEDGAR test clauses, 70.1 micro-F1 and 56.7 macro-F1 without examples, 62.1 and 51.1 with examples.

**If asked: why not rerun a recent model?** It needs paid calls and sending contract text to a third party, which is exactly what a law firm cannot do with real contracts. We cite the published study and say clearly that newer models may do better.
-->

---

<script setup>
import { deck } from '@deck'
const lawyer = deck.retrieval.lawyer
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="Ask a question, get the clauses" eyebrow="RETRIEVAL" emphasis="clauses" />
  <div class="retrieval-layout">
    <ClauseCloud />
    <div class="retrieval-ranks">
      <p data-r="2">Right type at rank 1, {{ lawyer.dense.n }} lawyer questions</p>
      <div data-r="3"><span>MiniLM</span><strong>{{ lawyer.dense.rank1 }}</strong><i :style="{ width: `${lawyer.dense.rank1 / lawyer.dense.n * 100}%`, background: '#2dd4bf' }" /></div>
      <div data-r="4"><span>TF-IDF</span><strong>{{ lawyer.tfidf.rank1 }}</strong><i :style="{ width: `${lawyer.tfidf.rank1 / lawyer.tfidf.n * 100}%`, background: '#d4a853' }" /></div>
      <div data-r="5"><span>Keyword overlap</span><strong>{{ lawyer.overlap.rank1 }}</strong><i :style="{ width: `${lawyer.overlap.rank1 / lawyer.overlap.n * 100}%`, background: '#475569' }" /></div>
    </div>
  </div>
  <DeckFooter n="06" speaker="Wiyao" />
</div>

<!--
**WIYAO · about 1 minute**

The second part of the product is search. We embedded the 60,000 training clauses with MiniLM, a sentence-transformer from the course, and we search by cosine similarity, exactly as in lab 3.

What you see is a 3D projection of real clauses, coloured by type: each colour group is one kind of clause. When a lawyer types a question, here "termination clauses with a 30-day notice period", the question lands in the same space, next to the clauses that mean the same thing. The five closest are listed: four termination clauses and one notice clause.

We tested 18 questions written the way a lawyer writes them. MiniLM finds the right clause type in first position 13 times out of 18. TF-IDF manages 10, and simple keyword overlap only 6.
-->

---
transition: deck-iris | deck-sweep-back
---

<script setup>
import { cloud, deck, f1 } from '@deck'
const metrics = deck.retrieval.metrics
const lawyer = deck.retrieval.lawyer
const days = cloud.query.text.match(/\d+/)?.[0]
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="The right method depends on the query" eyebrow="RETRIEVAL, BY HAND" emphasis="query" />
  <div class="two-col query-compare">
    <div><h2>From a clause</h2><p><strong>TF-IDF {{ f1(metrics.tfidf.deduplicated.top_1_accuracy[0]) }}</strong> vs MiniLM {{ f1(metrics.dense.deduplicated.top_1_accuracy[0]) }} top-1</p></div>
    <div><h2>From a question</h2><p><strong>MiniLM {{ lawyer.dense.rank1 }}/{{ lawyer.dense.n }}</strong> vs TF-IDF {{ lawyer.tfidf.rank1 }}/{{ lawyer.tfidf.n }}</p></div>
  </div>
  <div v-click class="example-card">
    <p class="query-text">“which court has jurisdiction over disputes”</p>
    <p>“The parties agree irrevocably to submit to the exclusive jurisdiction of the federal courts ... located in Boston, Massachusetts”</p>
    <div><span class="label-pill">Venues</span><span class="wrong">counted wrong</span><span>A lawyer would accept it: the same-label check is strict.</span></div>
  </div>
  <div data-r="4" class="filter-note"><span class="chip">Filter: {{ days }} days</span><span>Durations in the question filter the results.</span></div>
  <DeckFooter n="07" speaker="Wiyao" />
</div>

<!--
**WIYAO · about 50 seconds**

The lesson: the right method depends on the query. When the query is itself a clause, TF-IDF is slightly ahead, 0.787 against 0.771 for the first result, because a clause shares its exact wording with clauses of the same type. When the query is a question, MiniLM wins, because a question shares meaning, not words.

[click] We also read the results by hand. Our automatic score counts an answer as right only if it carries the same label. For "which court has jurisdiction over disputes", MiniLM returns a clause where the parties submit to the courts of Boston. It is labelled Venues, so it counts as wrong, but a lawyer would accept it. Our measure is strict, so the real quality is higher.

Durations in a question, like 30 days, also filter the results automatically.

Back to Ewan, for what all this costs.
-->

---
transition: deck-rise | deck-sweep-back
---

<script setup>
import { deck, integer, legalBert } from '@deck'
const tf = deck.cost.find(row => row.configuration === 'tfidf' && row.device === 'cpu')
const bertCpu = deck.cost.find(row => row.configuration === 'legal_bert_long fp32' && row.device === 'cpu')
const bertInt8 = deck.cost.find(row => row.configuration === 'legal_bert_long int8' && row.device === 'cpu')
const speed = Math.round((bertCpu.ms_per_clause / tf.ms_per_clause) / 10) * 10
const sizeRatio = bertCpu.size_mb / bertInt8.size_mb
const qualityDrop = (deck.cost_quality.fp32.macro_f1 - deck.cost_quality.int8.macro_f1) * 100
</script>

<div class="deck-slide">
  <Stage />
  <Headline :text="`Same quality, ${integer(speed)}× faster`" eyebrow="COST" :emphasis="`${integer(speed)}×`" />
  <p data-r="1" class="chart-intro">Time to classify {{ integer(tf.n * 10) }} clauses</p>
  <TimeRace />
  <div class="cost-bottom"><p data-r="8">Training: {{ integer(deck.tfidf_train_seconds) }} s on a laptop CPU vs {{ Math.floor(legalBert.train_time_min / 60) }} h {{ Math.round(legalBert.train_time_min % 60) }} on a GPU</p><p data-r="9">int8 Legal-BERT: {{ sizeRatio.toFixed(1) }} times smaller but slower on this laptop, and {{ qualityDrop.toFixed(1) }} points lower</p></div>
  <DeckFooter n="08" speaker="Ewan" />
</div>

<!--
**EWAN · about 50 seconds**

Same quality, so what about cost? This is the time to classify 10,000 clauses on our laptop. TF-IDF: under one second. Legal-BERT on the laptop's GPU: 2 minutes 13. On its CPU: 5 minutes 18. TF-IDF is about 360 times faster, for the same quality.

Training tells the same story: 44 seconds on a laptop CPU for TF-IDF, more than two hours on a GPU for Legal-BERT.

We also tried compressing Legal-BERT to 8-bit integers. It becomes 2.4 times smaller, but on this laptop it is slower and 1.2 points less accurate, so it does not pay off here.

For a start-up, this difference is servers, cost and latency.

**If asked: how was it measured?** On our laptop, an Apple M2 Pro: the median of three timed runs on 1,000 test clauses, Legal-BERT in batches of 64. TF-IDF: 0.09 ms per clause; Legal-BERT: 31.8 ms on the CPU and 13.3 ms on the laptop GPU.

**If asked: what is int8?** Dynamic quantisation stores the weights of the linear layers as 8-bit integers instead of 32-bit floats (Zafrir and colleagues, Q8BERT, 2019). The model becomes 2.4 times smaller, but on this ARM laptop it is 2.5 times slower and loses 1.2 macro-F1 points, with 94.7% of predictions unchanged. Speed-ups are reported on server CPUs, which we did not measure.
-->

---

<script setup>
import { deck } from '@deck'
const audit = deck.counterfactual.legal_bert_long
const categories = [['party_roles', 'Party roles'], ['jurisdiction', 'Jurisdiction'], ['number_format', 'Number format']]
const threshold = deck.counterfactual_fail_threshold
const auditOption = {
  animationDuration: 1000,
  grid: { left: 65, right: 30, top: 70, bottom: 80 },
  legend: { top: 5, textStyle: { fontSize: 19, color: '#f4efe6' } },
  xAxis: { type: 'category', data: categories.map(row => row[1]), axisLabel: { fontSize: 19, color: '#f4efe6' } },
  yAxis: { type: 'value', max: 0.04, name: 'Flip rate', axisLabel: { fontSize: 18, formatter: (v) => `${Math.round(v * 100)}%` }, nameTextStyle: { fontSize: 18 } },
  series: [
    { name: 'Edit', type: 'bar', data: categories.map(row => audit[row[0]].flip_rate), itemStyle: { color: '#2dd4bf' }, barWidth: 45, markLine: { symbol: 'none', label: { formatter: 'fail threshold fixed in advance', fontSize: 17, position: 'insideEndTop', color: '#f59e0b', textBorderWidth: 0 }, lineStyle: { type: 'dashed', color: '#f59e0b' }, data: [{ yAxis: threshold }] } },
    { name: 'Control', type: 'bar', data: categories.map(row => audit[row[0]].ctrl_flip_rate), itemStyle: { color: '#475569' }, barWidth: 45 },
  ],
}
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="Robust to parties, laws and number formats" eyebrow="AUDIT" emphasis="Robust" />
  <div class="two-col audit-layout">
    <div class="audit-chart"><div class="pass-row"><span v-for="row in categories" :key="row[0]" class="pass-tag">{{ audit[row[0]].decision }}</span></div><div class="threshold-draw" /><EChart :option="auditOption" height="420px" /><p class="chart-note">Party roles: {{ (audit.party_roles.flip_rate * 100).toFixed(1) }}%, just above the line, but no more than its control ({{ (audit.party_roles.ctrl_flip_rate * 100).toFixed(1) }}%): pass by the rule.</p></div>
    <div class="audit-aside"><strong>Known weakness</strong><p>Lease contracts: accuracy {{ deck.lease_slice.accuracy.toFixed(3) }} against {{ deck.lease_slice.overall_accuracy.toFixed(3) }} overall.</p><p>Flagged for review.</p></div>
  </div>
  <DeckFooter n="09" speaker="Ewan" />
</div>

<!--
**EWAN · about 50 seconds**

Now the audit. A clause type should not change when you change who the parties are, which law is named, or how a number is written. So we edited test clauses: we swapped Buyer and Seller, moved the governing law from New York to England, and rewrote "thirty (30) days" as "30 days". Each edit has a control edit of the same size that should not matter.

The rule was fixed in advance: a test fails if more than 2% of predictions change and the change is clearly above its control. All three tests pass. Party roles sits just above 2%, but no higher than its control: the model reacts to any change of party words, not to which side holds the role.

The analysis by kind of contract still finds a real weakness: on lease contracts, accuracy drops to 0.684, against 0.882 overall. We flag it as a known limit.

**If asked: where does the method come from?** The audit was not covered in class, so it is built from published methods, each justified in the README. Slices measured with intervals: Dixon and colleagues, 2018. Invariance tests: Ribeiro and colleagues, CheckList, ACL 2020. Counterfactual edits: Garg and colleagues, 2019. The model card follows Mitchell and colleagues, 2019.

**If asked: why a control edit?** Any edit can change a prediction, just because the text changed. The control is an edit of the same size that should not matter, for example Buyer to Purchaser instead of Buyer to Seller. The test only fails if the real edit changes clearly more predictions than its control: the difference interval must be entirely above zero.

**If asked: why lease contracts?** They are only 187 test clauses, with their own vocabulary (landlord, tenant, premises), and the model sees few of them in training. We report it as a known weakness rather than hide it.
-->

---

<script setup>
import { deck } from '@deck'
const taxonomy = deck.taxonomy
const share = taxonomy.runs[1].share_errors_removed * 100
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="A fifth of the errors are the label set, not the model" eyebrow="OVERLAPPING LABELS" emphasis="fifth" />
  <div class="two-col taxonomy-layout"><LabelMerge /><div class="taxonomy-aside"><div data-r="2" class="big-stat"><CountUp :value="share" :decimals="0" suffix="%" /></div><p data-r="3">of Legal-BERT errors removed after merging overlapping labels</p><p data-r="4">Paired accuracy p = {{ taxonomy.paired_tests.test.p_value.toFixed(3) }} (exploratory)</p><p data-r="5" class="recommend-line">Recommendation: review these {{ taxonomy.pairs.length }} pairs with the start-up's lawyers.</p></div></div>
  <DeckFooter n="10" speaker="Ewan" />
</div>

<!--
**EWAN · about 50 seconds**

When we read the errors, many were not really errors. A clause like "This Agreement shall be governed by the laws of New York" appears in the data under two labels: Applicable Laws and Governing Laws. Applicable Laws is the worst class of both models, with an F1 between 0.24 and 0.30.

We found nine pairs like this, with a rule fixed before measuring: the pair must be among the ten most confused for both models, and the examples must show the same kind of clause. Merging them removes 22% of Legal-BERT's errors, and Applicable Laws jumps to 0.963.

This analysis was outside our original plan, so it does not change the recommendation. But it is a concrete message for the client: review these nine pairs with your lawyers before collecting more data.
-->

---
transition: deck-rise | deck-sweep-back
---

<script setup>
import { deck } from '@deck'
const trust = deck.calibration.legal_bert_long
const recommended = deck.calibration.tfidf
const handled = recommended.abstention.test_coverage * 100
const human = recommended.abstention.share_sent_to_human * 100
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="It knows when to ask a person" eyebrow="TRUST" emphasis="person" />
  <div class="two-col trust-layout"><Reliability /><div class="trust-aside"><ReviewFlow /><p data-r="6">TF-IDF: {{ handled.toFixed(0) }}% handled automatically, {{ (recommended.abstention.test_accuracy * 100).toFixed(1) }}% of them right; {{ human.toFixed(0) }}% sent to a person. Legal-BERT: {{ (trust.abstention.test_coverage * 100).toFixed(1) }}% handled automatically.</p><p data-r="7">Prediction sets: {{ Math.round(trust.conformal.test_coverage * 100) }}% coverage with {{ trust.conformal.mean_set_size.toFixed(2) }} types per clause.</p></div></div>
  <DeckFooter n="11" speaker="Ewan" />
</div>

<!--
**EWAN · about 50 seconds**

A legal tool must know when it is unsure. On the left, the confidence of Legal-BERT. Before correction, when it says 90%, it is right much less often than that. A single temperature parameter, fitted on validation data, brings the calibration error from 8.5% down to 3.1%, without changing a single prediction. TF-IDF was already well calibrated.

Then we chose a confidence threshold on validation data. On the test set, 83% of clauses are handled automatically, and 94.7% of those are right. The other 17% go to a person.

We also give prediction sets: instead of one answer, a small set of types that contains the right one 90% of the time, with about one type per clause on average. When the set has two types, it is most often one of our overlapping pairs.

**If asked: how does temperature scaling work?** The model's scores are divided by one number, the temperature, chosen on the validation set to make the probabilities honest (Guo and colleagues, ICML 2017). The order of the scores does not change, so no prediction changes: only the confidence becomes reliable.

**If asked: how is the threshold chosen?** On the validation set, as the lowest confidence for which the clauses above it are 95% correct. It is then applied unchanged to the test set: 83% of clauses pass it, and 94.7% of those are right.

**If asked: what is a prediction set?** Split conformal prediction (Angelopoulos and Bates, 2021): a threshold computed on validation so that the set contains the true type 90% of the time, whatever the model, as long as new contracts resemble the validation ones. We measured 89.7 to 89.8% on test. An empty set means no type is plausible enough, and the clause goes to a person.
-->

---
transition: deck-iris | deck-sweep-back
---

<script setup>
import { onMounted, ref } from 'vue'
const demoVideo = ref(false)
const demoUrl = '/demo.mp4'
onMounted(async () => {
  try {
    const response = await fetch(demoUrl, { method: 'HEAD' })
    demoVideo.value = response.ok && (response.headers.get('content-type') || '').includes('video')
  }
  catch { demoVideo.value = false }
})
</script>

<div class="deck-slide demo-slide">
  <Stage />
  <Headline text="Demo" eyebrow="DEMO" emphasis="" />
  <div data-r="1" class="demo-frame"><video v-if="demoVideo" :src="demoUrl" controls playsinline /><template v-else><h2>Live demo</h2><p>http://127.0.0.1:5050</p><div>Classify <span>·</span> Search <span>·</span> Missing clauses <span>·</span> Stress tests <span>·</span> Evidence</div></template></div>
  <DeckFooter n="12" speaker="Wiyao, then Ewan" />
</div>

<!--
**WIYAO, then EWAN · about 1 minute**

**WIYAO, search, about 25 seconds.** In the app (127.0.0.1:5050), press 2 for Search and click the "30-day termination" example. Say: "Here is a lawyer's question. The results are real clauses from the bank, each with its type and its similarity, and the filter on 30 days is applied automatically." Then hand over to Ewan.

**EWAN, about 35 seconds.** Press 1 for Classify, click "Governing law", then Classify clause. Say: "The clause type, the calibrated confidence, and the decision: handled automatically, or sent to a person. The highlighted words are the ones that drove the decision." Press 3 for Review, then Review contract. Say: "A whole contract, checked against twelve standard clause types. Governing law and severability are missing, and the model asks a person to check the clauses it is unsure of."

If the app does not respond, play the video or move on: everything in the demo is also in the slides.
-->

---

<script setup>
import { deck } from '@deck'
const human = Math.round(deck.calibration.tfidf.abstention.share_sent_to_human * 100)
</script>

<div class="deck-slide closing-slide">
  <Stage />
  <Headline text="What we recommend to the start-up" eyebrow="RECOMMENDATION" emphasis="recommend" />
  <div class="closing-list">
    <p v-click><b>1</b><span>TF-IDF to classify, with calibrated confidence and a person for the {{ human }}% it is unsure of</span></p>
    <p v-click><b>2</b><span>MiniLM to search from a lawyer's question</span></p>
    <p v-click><b>3</b><span>Review {{ deck.taxonomy.pairs.length }} overlapping label pairs before collecting more data</span></p>
    <p v-click><b>4</b><span>Not for non-US contracts, never without human review: not legal advice</span></p>
  </div>
  <svg class="signature" viewBox="0 0 720 65" aria-hidden="true"><path d="M0 46 C120 51 220 34 330 42 S565 52 710 31" /><text x="370" y="35">Clausier</text></svg>
  <p class="repo-line">Code, results and model card: github.com/Exowz/clausier-ledgar</p>
  <DeckFooter n="13" speaker="Ewan" />
</div>

<!--
**EWAN · about 40 seconds**

To conclude, what we recommend to the start-up.

[click] First, TF-IDF to classify. Same quality as Legal-BERT, 360 times cheaper, with calibrated confidence and a person for the 17% of clauses it is unsure of.

[click] Second, MiniLM to search, when the input is a lawyer's question.

[click] Third, review the nine overlapping label pairs before collecting more data: that is where many of the remaining errors are.

[click] And the limits: everything was trained on US contracts filed with the SEC. It is not for European or non-English contracts without a new evaluation, and never without human review. It is not legal advice.

Everything is reproducible from the repository, with the model card. Thank you, we are happy to take your questions.

---

**QUESTIONS AND ANSWERS · keep this slide on the projector, scroll here**

**DATA AND EVALUATION**

**Why macro-F1, not weighted F1 or accuracy?** The 100 types are very unequal (3,167 against 23 training clauses). Accuracy and weighted F1 are dominated by frequent types; macro-F1 gives each type the same weight, so rare types cannot be ignored.

**How did you detect near copies? Why 0.9?** TF-IDF cosine between each test clause and its closest training clause: 451 exact copies, 1,790 at 0.9 or more. The threshold is a choice, so we report both test sets, and the conclusion (a tie) is the same on both.

**TRAP · Did you use the test set to choose anything?** No for the models: C for TF-IDF and the best Legal-BERT run were chosen on validation only. The calibration threshold and the conformal quantile are fitted on validation too. Exception: the label merge, see below.

**How did you handle class imbalance?** TF-IDF with balanced class weights was tried: 0.812 on validation against 0.822 without, so it was not kept. Transformers: plain cross-entropy, early stopping on validation macro-F1.

**TRANSFORMERS**

**Describe your training loop.** Hand-written PyTorch, as in S06: AdamW, learning rate 3e-5, weight decay 0.01; linear warmup over 10% of the steps then linear decay; gradient clipping at 1.0; fp16; batch 32; validation each epoch; early stopping on macro-F1, patience 2 for the long runs; the best epoch's weights are restored before testing.

**How is the clause classified from BERT?** The [CLS] representation goes through a linear layer to 100 outputs, then softmax; trained with cross-entropy.

**Why 256 tokens and not 512?** 12% of training clauses are truncated at 256, 1.5% at 512, and 512 costs two to three times more. Truncated clauses are not worse (accuracy 0.896 against 0.882), because the type is usually stated at the start of the clause.

**Why is Legal-BERT not better than TF-IDF?** Many types are recognised by a few key words, which TF-IDF captures well; 22% of errors come from overlapping labels, a ceiling for every model; we read 256 tokens; and even in LexGLUE the gap is only 1.6 points.

**Why does validation loss rise while macro-F1 improves?** Cross-entropy keeps pushing confident predictions and punishes confident mistakes heavily: the model gets more clauses right but becomes overconfident on its errors. Calibration measures it: error 0.085, corrected to 0.031.

**Why not CamemBERT or a bigger model?** The contracts are English; CamemBERT is French (S03 tokeniser exercise). RoBERTa-large reaches 83.6 in LexGLUE, only 0.6 above Legal-BERT, with three times the parameters.

**LORA**

**Explain LoRA.** The pretrained weight W is frozen; we add a low-rank update W + (alpha / r) B A, rank 8, alpha 16, on the query and value projections of every layer, and train the classification head. B starts at zero, so training starts from the pretrained model. After training B A is merged into W: no extra cost at prediction time.

**0.34% of the weights, but only 21% less time per epoch?** The forward and backward passes still go through the whole network: the gradient must flow back through every frozen layer to reach the first LoRA layers. LoRA saves memory for gradients and Adam states (0.44 GB against 1.75 GB), not computation.

**Why learning rate 1e-3 for LoRA?** The adapters start at zero and are small, so they need a larger learning rate than full fine-tuning, as in TP06.

**LSTM**

**Describe the LSTM and why it is worse.** TP04 pipeline: regex tokeniser, vocabulary on train (minimum frequency 2), embeddings of size 50, one LSTM layer of 128, packed sequences, Adam. 7.7 points below TF-IDF: it learns everything from scratch, rare types have too few examples, long clauses are hard for a recurrent model. GloVe adds 0.3, not significant.

**STATISTICS**

**TRAP · Many tests: did you correct for multiple comparisons?** No. The main comparison was written in advance; the others are secondary. With Bonferroni over about 8 tests (threshold about 0.006), LoRA against full fine-tuning (p below 0.0001) still holds; Legal-BERT against BERT-base (p = 0.015) would not on accuracy, although its bootstrap interval excludes 0.

**TRAP · A single seed?** Yes, seed 42: variation between seeds is not measured, a stated limit. A gap of -0.001 is well inside typical seed variation, which supports the tie.

**Why a paired bootstrap, not a t-test?** Macro-F1 is not a mean over clauses. The bootstrap resamples the same clauses for both models and gives an interval for the difference without assuming its distribution.

**How does McNemar work?** Only disagreements count: 366 clauses only Legal-BERT gets right, 331 only TF-IDF. If the models were equal, each would be a coin flip. Chi-squared = (|366 - 331| - 1)^2 / 697 = 1.66, p = 0.20: not significant.

**RETRIEVAL**

**How does dense search work?** all-MiniLM-L6-v2 maps each clause to 384 numbers, normalised to length 1, so cosine is a dot product D @ q (TP03). Exact search over 60,000 clauses: 4 seconds for 1,000 queries, no FAISS needed.

**TRAP · Is "same label = relevant" a weak proxy?** Yes: it rewards a clause of the right type that does not answer the question, and penalises right answers filed under an overlapping label. That is why 18 lawyer questions were also read by hand.

**Why TF-IDF from a clause, MiniLM from a question?** A clause shares its exact wording with clauses of its type, ideal for TF-IDF; a question shares meaning but few words, ideal for embeddings.

**ADDITIONS**

**TRAP · The 9 label pairs were chosen from test confusions and measured on the same test set: circular?** Yes, so the 22% is optimistic, an upper bound. That is why it is labelled exploratory and does not change the recommendation. The clean design selects the pairs on validation.

**What does conformal prediction guarantee?** 90% coverage on average over clauses, if new contracts resemble the validation data. Not per class: a rare class can be under-covered.

**Why word erasure, not SHAP or attention?** Simple, works for any model including TF-IDF, and checked as faithful with ERASER. Attention weights are not a reliable explanation of the decision.

**TRAP · Is the missing-clause evaluation realistic?** Optimistic: simulated contracts are perfectly split clauses. Splitting a real contract is not evaluated; next step is real contracts with the start-up.

**Why is int8 slower?** On this ARM laptop PyTorch's int8 kernels are less optimised than full precision; reported speed-ups are on server CPUs.

**If stuck:** say what was measured, its limit, and what you would do next.
-->

---

<div class="deck-slide">
  <Stage />
  <Headline text="Backup: validation macro-F1 per epoch" eyebrow="BACKUP" emphasis="validation" />
  <div data-r="1" class="backup-card"><img src="/figures/validation_curves.png" /></div>
  <DeckFooter n="Backup" speaker="Questions" />
</div>

<!--
**QUESTIONS · backup answers**

**Why train longer than the 2 to 4 epochs of the course?** Every 4-epoch run was still improving at its last epoch, as this chart shows. We added 10-epoch runs, as the LexGLUE benchmark does, and chose the best run on validation data only. Full fine-tuning levels off from epoch 7; LoRA was still improving at epoch 10.

**Why macro-F1?** The 100 types are very unequal; macro-F1 gives each type the same weight, so rare types count.

**Why Legal-BERT and not CamemBERT?** The contracts are in English; CamemBERT is a French model.

**Why remove near copies?** 2,241 test clauses are near copies of training clauses; they make every model look better than it is on new contracts.

**Is the tie robust?** Yes: no significant difference on the full test set (p = 0.20) or on the deduplicated one (p = 0.16).

**Why LoRA?** It trains 0.34% of the weights with a quarter of the memory, for 1 to 2 points of macro-F1.
-->

---

<script setup>
import { deck } from '@deck'
const occ = deck.occlusion
const pct = (v) => `${Math.round(v * 1000) / 10}%`
const occOption = {
  animationDuration: 900,
  animationDelay: (index) => index * 160,
  grid: { left: 70, right: 30, top: 60, bottom: 60 },
  legend: { top: 0, textStyle: { fontSize: 18 } },
  xAxis: { type: 'category', data: ['TF-IDF', 'Legal-BERT'], axisLabel: { fontSize: 19, color: '#f4efe6' } },
  yAxis: { type: 'value', name: 'Drop in probability of the predicted type', nameTextStyle: { fontSize: 16, align: 'left' }, axisLabel: { fontSize: 17 } },
  series: [
    { name: 'Remove the 3 highlighted words', type: 'bar', barWidth: 70, itemStyle: { color: '#d4a853' }, label: { show: true, position: 'top', fontSize: 19, color: '#f4efe6', formatter: ({ value }) => value.toFixed(3) },
      data: [occ.tfidf.comprehensiveness.mean_top_k_drop, occ.legal_bert_long.comprehensiveness.mean_top_k_drop] },
    { name: 'Remove 3 random words', type: 'bar', barWidth: 70, itemStyle: { color: '#475569' }, label: { show: true, position: 'top', fontSize: 19, color: '#f4efe6', formatter: ({ value }) => value.toFixed(3) },
      data: [occ.tfidf.comprehensiveness.mean_random_drop, occ.legal_bert_long.comprehensiveness.mean_random_drop] },
  ],
}
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="Backup: the highlighted words really decide" eyebrow="BACKUP · EXPLANATIONS" emphasis="decide" />
  <div class="two-col backup-split">
    <EChart :option="occOption" height="440px" />
    <div class="backup-aside">
      <p data-r="1"><strong>Method.</strong> Remove each word in turn; its importance is how much the probability of the predicted type drops (word erasure).</p>
      <p data-r="2"><strong>Check.</strong> On 200 test clauses, removing the 3 most important words changes the prediction {{ pct(occ.tfidf.comprehensiveness.top_k_changed_share) }} (TF-IDF) and {{ pct(occ.legal_bert_long.comprehensiveness.top_k_changed_share) }} (Legal-BERT) of the time, against {{ pct(occ.tfidf.comprehensiveness.random_changed_share) }} and {{ pct(occ.legal_bert_long.comprehensiveness.random_changed_share) }} for 3 random words.</p>
      <p data-r="3" class="backup-source">Li, Monroe and Jurafsky 2016 (erasure) · DeYoung et al. 2020, ERASER (ACL)</p>
    </div>
  </div>
  <DeckFooter n="Backup" speaker="Questions" />
</div>

<!--
**QUESTIONS · word-level explanations**

What the app highlights: for each word, we remove it and measure how much the probability of the predicted clause type drops. That is word erasure, from Li, Monroe and Jurafsky, 2016.

Why you can trust it: an explanation is only useful if the highlighted words really drive the decision. So we ran the ERASER check from DeYoung and colleagues, 2020: on 200 test clauses, removing the 3 most important words lowers the probability about ten times more than removing 3 random words, and changes the prediction about a quarter of the time, against about 5% for random words.

The limit: in long clauses that repeat their key words, removing a single word changes little, so the importance can look low everywhere; and we explain the first 200 words only.
-->

---

<script setup>
import { deck } from '@deck'
const runs = deck.missing_clauses.runs
const settings = deck.missing_clauses.settings
const pct = (v) => `${Math.round(v * 1000) / 10}%`
</script>

<div class="deck-slide">
  <Stage />
  <Headline text="Backup: finding the clauses a contract lacks" eyebrow="BACKUP · MISSING CLAUSES" emphasis="lacks" />
  <div class="missing-grid">
    <div v-for="(run, index) in runs" :key="run.run" :data-r="index + 1" class="missing-card">
      <span class="missing-model">{{ run.run === 'tfidf' ? 'TF-IDF' : 'Legal-BERT' }}</span>
      <div><strong><CountUp :value="run.missing_recall * 100" :decimals="1" suffix="%" /></strong><span>of missing clauses found</span></div>
      <div><strong><CountUp :value="run.missing_precision * 100" :decimals="1" suffix="%" /></strong><span>of "missing" flags right</span></div>
    </div>
  </div>
  <p data-r="3" class="backup-method"><strong>How it is measured.</strong> LEDGAR has single clauses, not contracts, so we simulate {{ settings.n_contracts }} contracts: each of the {{ deck.missing_clauses.checklist.length }} standard clause types is included with probability {{ settings.keep_prob }}, plus {{ settings.n_other }} other clauses. A type is "present" when a clause of that type passes the confidence threshold, "check" when only uncertain clauses have it, "missing" otherwise.</p>
  <p data-r="4" class="backup-source">Limit: splitting a real contract into clauses is not evaluated.</p>
  <DeckFooter n="Backup" speaker="Questions" />
</div>

<!--
**QUESTIONS · missing clauses**

What it does: the app splits a contract into clauses, classifies each one, and checks the 12 most frequent clause types of the training data: governing law, notices, counterparts, entire agreement, severability, and so on. Each type is marked present, to check, or missing, using the same calibrated confidence threshold as the rest of the product.

How we measured it: LEDGAR contains single clauses, not whole contracts, so we built 500 simulated contracts from real test clauses, leaving out some standard types on purpose. About 95 to 96% of the truly missing clauses are found, and 86 to 87% of the "missing" flags are right.

The limit: splitting a real contract into clauses, at blank lines, is not evaluated. That would need real contracts, which is the natural next step with the start-up.
-->

---

<div class="deck-slide">
  <Stage />
  <Headline text="Backup: every addition, its method and its source" eyebrow="BACKUP · METHODS" emphasis="source" />
  <table data-r="1" class="sources-table">
    <thead><tr><th>Addition</th><th>Question it answers</th><th>Method</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Bias audit</td><td>Does it depend on parties or law?</td><td>Slices with intervals, edits with controls, rule fixed in advance</td><td>Dixon 2018 · Ribeiro 2020 · Garg 2019</td></tr>
      <tr><td>Near copies removed</td><td>Will it hold on new contracts?</td><td>TF-IDF cosine of at least 0.9 to a training clause</td><td>Project analysis</td></tr>
      <tr><td>Positioning</td><td>Is it the state of the art?</td><td>Published LexGLUE and ChatGPT results</td><td>Chalkidis 2022 · Chalkidis 2023</td></tr>
      <tr><td>Calibration</td><td>Can the confidence be trusted?</td><td>Temperature scaling on validation, threshold for 95% accuracy</td><td>Guo et al. 2017</td></tr>
      <tr><td>Prediction sets</td><td>"One of these two types"</td><td>Split conformal prediction, 90% coverage</td><td>Angelopoulos and Bates 2021</td></tr>
      <tr><td>Cost and int8</td><td>What does it cost to run?</td><td>Timed on a laptop; dynamic quantisation</td><td>Zafrir et al. 2019</td></tr>
      <tr><td>Overlapping labels</td><td>Model or label set?</td><td>Nine pairs merged by a rule fixed before measuring</td><td>Confusion analysis · Tuggener 2020</td></tr>
      <tr><td>Explanations</td><td>Why this type?</td><td>Word erasure, checked with ERASER</td><td>Li 2016 · DeYoung 2020</td></tr>
      <tr><td>Missing clauses</td><td>What does a contract lack?</td><td>12-type checklist, 500 simulated contracts</td><td>Project analysis</td></tr>
    </tbody>
  </table>
  <DeckFooter n="Backup" speaker="Questions" />
</div>

<!--
**QUESTIONS · the additions in one sentence**

The core of the project, checkpoints m1 to m5, follows the course and its labs. Everything beyond it answers a question the start-up would ask before buying: can I trust the confidence, what does it cost, what does it get wrong and why, and what is missing in my contract. Each addition uses a published method, cited in the README, and every number is produced by a script in the repository.
-->
