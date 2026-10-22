<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import * as d3 from 'd3'
import { deck, f1 } from '../data'

const active = useIsSlideActive()
const svg = ref<SVGSVGElement>()
const list = ref<HTMLElement>()
const pair = deck.taxonomy.runs[1].group_f1['Applicable Laws / Governing Laws']
const names = deck.taxonomy.pairs.map(pair => pair.join(' / '))
const radius = (value: number) => Math.sqrt(value) * 106
function reset() {
  if (!svg.value) return
  const root = d3.select(svg.value)
  root.selectAll('.merge-left').interrupt().attr('transform', 'translate(210,205)').style('opacity', 1)
  root.selectAll('.merge-right').interrupt().attr('transform', 'translate(570,205)').style('opacity', 1)
  root.selectAll('.merge-final').interrupt().style('opacity', 0)
  if (list.value) d3.select(list.value).interrupt().style('opacity', 0)
}
function animate() {
  reset()
  if (!svg.value) return
  const root = d3.select(svg.value)
  root.selectAll('.merge-left').transition().duration(1000).ease(d3.easeCubicOut).attr('transform', 'translate(360,205)').style('opacity', 0)
  root.selectAll('.merge-right').transition().duration(1000).ease(d3.easeCubicOut).attr('transform', 'translate(420,205)').style('opacity', 0)
  root.selectAll('.merge-final').transition().delay(650).duration(650).ease(d3.easeCubicOut).style('opacity', 1)
  if (list.value) d3.select(list.value).transition().delay(1100).duration(700).style('opacity', 1)
}
onMounted(() => { if (active.value) animate(); else reset() })
watch(active, value => { if (value) animate(); else reset() })
</script>

<template>
  <div class="merge-wrap">
    <svg ref="svg" viewBox="0 0 780 390" class="merge-svg" role="img" aria-label="Two overlapping labels merge into one">
      <g class="merge-left" transform="translate(210,205)">
        <circle :r="radius(pair.f1_before_a)" fill="#e7f3f0" stroke="#0f766e" stroke-width="2" />
        <text text-anchor="middle" y="-8" class="merge-label">Applicable Laws</text>
        <text text-anchor="middle" y="34" class="merge-number">{{ f1(pair.f1_before_a) }}</text>
      </g>
      <g class="merge-right" transform="translate(570,205)">
        <circle :r="radius(pair.f1_before_b)" fill="#e9ecf0" stroke="#14213d" stroke-width="2" />
        <text text-anchor="middle" y="-8" class="merge-label">Governing Laws</text>
        <text text-anchor="middle" y="34" class="merge-number">{{ f1(pair.f1_before_b) }}</text>
      </g>
      <g class="merge-final" transform="translate(390,205)" opacity="0">
        <circle :r="radius(pair.f1_after)" fill="#e7f3f0" stroke="#0f766e" stroke-width="3" />
        <text text-anchor="middle" y="-8" class="merge-label">Merged label</text>
        <text text-anchor="middle" y="34" class="merge-number">{{ f1(pair.f1_after) }}</text>
      </g>
    </svg>
    <div ref="list" class="merge-list"><span v-for="name in names" :key="name">{{ name }}</span></div>
  </div>
</template>
