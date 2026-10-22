<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useStage } from '../composables/stage'
import gsap from 'gsap'
import { compactTime, deck } from '../data'

const bars = ref<HTMLElement[]>([])
const labels = ref<HTMLElement[]>([])
const elapsed = ref(0)
const done = ref(false)
let timeline: gsap.core.Timeline | undefined
const rows = computed(() => [
  { name: 'TF-IDF · CPU', key: 'tfidf', device: 'cpu', color: '#d4a853' },
  { name: 'Legal-BERT · laptop GPU', key: 'legal_bert_long fp32', device: 'mps', color: '#475569' },
  { name: 'Legal-BERT · CPU', key: 'legal_bert_long fp32', device: 'cpu', color: '#334155' },
].map(row => ({ ...row, seconds: deck.cost.find(cost => cost.configuration === row.key && cost.device === row.device)!.seconds_per_1000 * 10 })))
const slowest = computed(() => Math.max(...rows.value.map(row => row.seconds)))
const elapsedLabel = computed(() => elapsed.value < 60 ? `${Math.round(elapsed.value)} s` : `${Math.floor(elapsed.value / 60)} min ${Math.round(elapsed.value % 60)} s`)
const width = (index: number) => `${Math.max(1.2, rows.value[index].seconds / slowest.value * 100)}%`
function reset() {
  timeline?.kill()
  elapsed.value = 0; done.value = false
  bars.value.forEach(bar => gsap.set(bar, { width: 0 }))
  labels.value.forEach(label => gsap.set(label, { opacity: 0, x: -10 }))
}
useStage({
  setup: reset,
  enter() {
    reset()
    const clock = { value: 0 }
    timeline = gsap.timeline({ delay: 0.9 })
    timeline.to(clock, { value: slowest.value, duration: 6, ease: 'none', onUpdate: () => { elapsed.value = clock.value } }, 0)
    rows.value.forEach((row, index) => {
      timeline!.to(bars.value[index], {
        width: width(index),
        duration: index === 0 ? 0.6 : Math.max(1.2, row.seconds / slowest.value * 6),
        ease: index === 0 ? 'expo.out' : 'none',
        onComplete: () => { gsap.to(labels.value[index], { opacity: 1, x: 0, duration: 0.4, ease: 'power3.out' }); if (index === 0) done.value = true },
      }, 0)
    })
  },
  final() {
    bars.value.forEach((bar, index) => gsap.set(bar, { width: width(index) }))
    labels.value.forEach(label => gsap.set(label, { opacity: 1, x: 0 }))
    elapsed.value = slowest.value; done.value = true
  },
})
onBeforeUnmount(() => timeline?.kill())
</script>
<template>
  <div class="time-race">
    <div class="race-elapsed">{{ elapsedLabel }}</div>
    <div v-for="(row,index) in rows" :key="row.name" class="race-row">
      <div class="race-name">{{ row.name }}</div>
      <div class="race-track"><div :ref="el => { if (el) bars[index]=el as HTMLElement }" class="race-fill" :style="{background:row.color}" /></div>
      <div :ref="el => { if (el) labels[index]=el as HTMLElement }" class="race-time">{{ compactTime(row.seconds) }}<span v-if="index===0 && done" class="race-done">done</span></div>
    </div>
  </div>
</template>
