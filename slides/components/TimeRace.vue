<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import { compactTime, deck } from '../data'

const active = useIsSlideActive()
const bars = ref<HTMLElement[]>([])
const labels = ref<HTMLElement[]>([])
let timeline: gsap.core.Timeline | undefined
const rows = computed(() => [
  { name: 'TF-IDF · CPU', key: 'tfidf', device: 'cpu', color: '#0f766e' },
  { name: 'Legal-BERT · laptop GPU', key: 'legal_bert_long fp32', device: 'mps', color: '#8190a3' },
  { name: 'Legal-BERT · CPU', key: 'legal_bert_long fp32', device: 'cpu', color: '#14213d' },
].map(row => ({
  ...row,
  seconds: deck.cost.find(cost => cost.configuration === row.key && cost.device === row.device)!.seconds_per_1000 * 10,
})))
const slowest = computed(() => Math.max(...rows.value.map(row => row.seconds)))
function play(isActive: boolean) {
  timeline?.kill()
  bars.value.forEach(bar => gsap.set(bar, { width: 0 }))
  labels.value.forEach(label => gsap.set(label, { opacity: 0 }))
  if (!isActive) return
  timeline = gsap.timeline()
  rows.value.forEach((row, index) => {
    timeline!.to(bars.value[index], {
      width: `${Math.max(1.2, row.seconds / slowest.value * 100)}%`,
      duration: Math.max(0.6, row.seconds / slowest.value * 6),
      ease: 'power2.out',
      onComplete: () => gsap.to(labels.value[index], { opacity: 1, duration: 0.4 }),
    }, 0)
  })
}
watch(active, play)
onMounted(() => play(active.value))
</script>

<template>
  <div class="time-race">
    <div v-for="(row, index) in rows" :key="row.name" class="race-row">
      <div class="race-name">{{ row.name }}</div>
      <div class="race-track"><div :ref="el => { if (el) bars[index] = el as HTMLElement }" class="race-fill" :style="{ background: row.color }" /></div>
      <div :ref="el => { if (el) labels[index] = el as HTMLElement }" class="race-time">{{ compactTime(row.seconds) }}</div>
    </div>
  </div>
</template>
