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
const draw = () => {
  if (!chart) return
  chart.clear()
  if (!active.value) return
  chart.setOption(props.option, { notMerge: true })
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
