<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import { compactTime, deck } from '../data'

const active = useIsSlideActive()
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
function play(isActive: boolean) {
  timeline?.kill()
  elapsed.value = 0; done.value = false
  bars.value.forEach(bar => gsap.set(bar, { width: 0 }))
  labels.value.forEach(label => gsap.set(label, { opacity: 0 }))
  if (!isActive) return
  const reduce = (matchMedia('(prefers-reduced-motion: reduce)').matches || location.search.includes('print'))
  if (reduce) {
    bars.value.forEach((bar,index) => gsap.set(bar, { width: `${Math.max(1.2, rows.value[index].seconds / slowest.value * 100)}%` }))
    labels.value.forEach(label => gsap.set(label, { opacity: 1 }))
    elapsed.value = slowest.value; done.value = true
    return
  }
  const clock = { value: 0 }
  timeline = gsap.timeline()
  timeline.to(clock, { value: slowest.value, duration: 6, ease: 'none', onUpdate: () => { elapsed.value = clock.value } }, 0)
  rows.value.forEach((row,index) => {
    timeline!.to(bars.value[index], {
      width: `${Math.max(1.2, row.seconds / slowest.value * 100)}%`,
      duration: index === 0 ? 0.9 : Math.max(1.2, row.seconds / slowest.value * 6),
      ease: 'power2.out',
      onComplete: () => { gsap.to(labels.value[index], { opacity: 1, duration: .3 }); if (index === 0) done.value = true },
    }, 0)
  })
}
watch(active, play)
onMounted(() => play(active.value))
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
