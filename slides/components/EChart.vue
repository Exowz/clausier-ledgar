<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const props = withDefaults(defineProps<{ option: EChartsOption, height?: string }>(), { height: '440px' })
const element = ref<HTMLElement>()
const active = useIsSlideActive()
let chart: echarts.ECharts | undefined
const resize = () => chart?.resize()
const darkAxis = (axis: unknown) => {
  const value = axis as Record<string, any>
  if (!value) return value
  return {
    ...value,
    nameTextStyle: { color: '#8a94a6', ...(value.nameTextStyle || {}) },
    axisLine: { show: true, lineStyle: { color: 'rgba(244,239,230,.10)', ...(value.axisLine?.lineStyle || {}) } },
    axisLabel: { color: '#8a94a6', ...(value.axisLabel || {}) },
    splitLine: { lineStyle: { color: 'rgba(244,239,230,.10)', ...(value.splitLine?.lineStyle || {}) } },
  }
}
const draw = () => {
  if (!chart) return
  chart.clear()
  if (!active.value) return
  const reduce = (window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.location.search.includes('print'))
  chart.setOption({
    backgroundColor: 'transparent',
    color: ['#d4a853', '#2dd4bf', '#475569'],
    textStyle: { color: '#f4efe6', fontFamily: 'Inter Variable, Inter, sans-serif' },
    ...props.option,
    xAxis: Array.isArray(props.option.xAxis) ? props.option.xAxis.map(darkAxis) : darkAxis(props.option.xAxis),
    yAxis: Array.isArray(props.option.yAxis) ? props.option.yAxis.map(darkAxis) : darkAxis(props.option.yAxis),
    // A legend is shown only when the slide asks for one; its text keeps the light colour unless the slide sets another.
    legend: props.option.legend ? { ...props.option.legend, textStyle: { color: '#f4efe6', ...((props.option.legend as any).textStyle || {}) } } : { show: false },
    animation: !reduce,
  } as EChartsOption, { notMerge: true })
  requestAnimationFrame(resize)
}
onMounted(() => {
  chart = echarts.init(element.value!, undefined, { renderer: 'svg' })
  window.addEventListener('resize', resize)
  draw()
})
watch(active, draw)
watch(() => props.option, option => {
  if (active.value) chart?.setOption(option, { notMerge: false })
}, { deep: true })
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})
</script>

<template>
  <div ref="element" class="echart" :style="{ height }" role="img" aria-label="Data chart" />
</template>
