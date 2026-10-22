<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { useStage } from '../composables/stage'

const props = withDefaults(defineProps<{ option: EChartsOption, height?: string, delay?: number }>(), { height: '440px', delay: 250 })
const element = ref<HTMLElement>()
let chart: echarts.ECharts | undefined
let drawn = false
let timer: ReturnType<typeof setTimeout> | undefined
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
const build = (animate: boolean): EChartsOption => ({
  backgroundColor: 'transparent',
  color: ['#d4a853', '#2dd4bf', '#475569'],
  textStyle: { color: '#f4efe6', fontFamily: 'Inter Variable, Inter, sans-serif' },
  animationEasing: 'cubicOut',
  animationEasingUpdate: 'cubicInOut',
  ...props.option,
  xAxis: Array.isArray(props.option.xAxis) ? props.option.xAxis.map(darkAxis) : darkAxis(props.option.xAxis),
  yAxis: Array.isArray(props.option.yAxis) ? props.option.yAxis.map(darkAxis) : darkAxis(props.option.yAxis),
  // A legend is shown only when the slide asks for one; its text keeps the light colour unless the slide sets another.
  legend: props.option.legend ? { ...props.option.legend, textStyle: { color: '#f4efe6', ...((props.option.legend as any).textStyle || {}) } } : { show: false },
  animation: animate,
} as EChartsOption)
const draw = (animate: boolean) => {
  if (!chart) return
  // The chart is created while its slide is still hidden (zero size): size it first, otherwise the resize after
  // drawing redraws it without its entrance animation.
  chart.resize()
  chart.clear()
  chart.setOption(build(animate), { notMerge: true })
  drawn = true
}
onMounted(() => {
  chart = echarts.init(element.value!, undefined, { renderer: 'svg' })
  window.addEventListener('resize', resize)
})
const { still } = useStage({
  // A live chart stays empty until its slide is shown, then draws with its entrance animation.
  setup: () => { clearTimeout(timer); chart?.clear(); drawn = false },
  enter: () => { clearTimeout(timer); chart?.clear(); drawn = false; timer = setTimeout(() => draw(true), props.delay) },
  final: () => draw(false),
})
// Option changes after the first draw (for example the reliability bars after scaling) animate from the old values.
watch(() => props.option, () => { if (chart && drawn) chart.setOption(build(!still()), { notMerge: false }) }, { deep: true })
onBeforeUnmount(() => {
  clearTimeout(timer)
  window.removeEventListener('resize', resize)
  chart?.dispose()
})
</script>

<template>
  <div ref="element" class="echart" :style="{ height }" role="img" aria-label="Data chart" />
</template>
