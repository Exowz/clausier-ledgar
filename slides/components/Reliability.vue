<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import { deck, percent } from '../data'

const active = useIsSlideActive()
const data = deck.calibration.legal_bert_long
const after = ref(false)
const eceShown = ref(data.ece_before * 100)
let timer: ReturnType<typeof setTimeout> | undefined
let tween: gsap.core.Tween | undefined
const option = computed(() => {
  const bins = after.value ? data.reliability_after : data.reliability_before
  return {
    animation: true,
    animationDuration: 950,
    animationDurationUpdate: 950,
    animationEasing: 'cubicOut',
    grid: { left: 65, right: 18, top: 24, bottom: 58 },
    xAxis: { type: 'category', data: bins.map(bin => percent(bin.bin_high)), name: 'Confidence', nameLocation: 'middle', nameGap: 38, axisLabel: { fontSize: 18, interval: 0, formatter: (value: string, index: number) => (index + 1) % 3 === 0 ? value : '' }, axisTick: { show: false } },
    yAxis: { type: 'value', min: 0, max: 1, name: 'Observed accuracy', nameLocation: 'middle', nameGap: 48, axisLabel: { fontSize: 18, formatter: (v: number) => percent(v) } },
    series: [
      { type: 'bar', barWidth: 24, data: bins.map(bin => bin.accuracy), itemStyle: { color: '#14213d' } },
      { type: 'line', data: bins.map(bin => bin.mean_confidence), symbol: 'none', lineStyle: { color: '#9aa8b3', type: 'dashed', width: 2 }, animation: false },
    ],
  }
})
watch(active, value => {
  clearTimeout(timer)
  tween?.kill()
  after.value = false
  eceShown.value = data.ece_before * 100
  if (value) timer = setTimeout(() => {
    after.value = true
    const state = { value: data.ece_before * 100 }
    tween = gsap.to(state, { value: data.ece_after * 100, duration: 0.95, ease: 'power2.out', onUpdate: () => { eceShown.value = state.value } })
  }, 1500)
}, { immediate: true })
onBeforeUnmount(() => { clearTimeout(timer); tween?.kill() })
</script>

<template>
  <div class="reliability-wrap">
    <div class="reliability-title">Legal-BERT on the test set, {{ after ? 'after' : 'before' }} temperature scaling</div>
    <EChart :option="option" height="360px" />
    <div class="ece-label">Calibration error <span>{{ eceShown.toFixed(1) }}%</span></div>
  </div>
</template>
