<script setup lang="ts">
import { nextTick, onBeforeUnmount, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'

const active = useIsSlideActive()
let timeline: gsap.core.Timeline | undefined
let observer: MutationObserver | undefined
let timer: ReturnType<typeof setTimeout> | undefined

function run() {
  const svg = document.querySelector('.pipeline-slide .mermaid svg')
  if (!svg || !active.value) return false
  const nodes = [...svg.querySelectorAll<SVGElement>('.node')]
  const edges = [...svg.querySelectorAll<SVGPathElement>('.edgePath path, .flowchart-link')]
  if (!nodes.length) return false
  timeline?.kill()
  const reduce = (window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.location.search.includes('print'))
  if (reduce) { gsap.set([...nodes, ...edges], { clearProps: 'all' }); return true }
  const order = ['LEDGAR', 'TF-IDF', 'LSTM', 'Legal-BERT', 'MiniLM', 'Paired tests', 'Search', 'Audit', 'Additions']
  const ordered = order.flatMap(label => nodes.filter(node => node.textContent?.includes(label)))
  gsap.set(ordered, { opacity: 0, y: 12 })
  edges.forEach(path => {
    const length = path.getTotalLength?.() || 500
    gsap.set(path, { strokeDasharray: length, strokeDashoffset: length })
  })
  timeline = gsap.timeline()
    .to(ordered, { opacity: 1, y: 0, duration: 0.55, stagger: 0.12, ease: 'power2.out' })
    .to(edges, { strokeDashoffset: 0, duration: 0.7, stagger: 0.06, ease: 'power2.out' }, 0.25)
  return true
}
watch(active, async value => {
  timeline?.kill()
  observer?.disconnect()
  clearTimeout(timer)
  if (!value) return
  await nextTick()
  if (run()) return
  observer = new MutationObserver(() => { if (run()) observer?.disconnect() })
  observer.observe(document.body, { childList: true, subtree: true })
  timer = setTimeout(() => observer?.disconnect(), 4000)
}, { immediate: true })
onBeforeUnmount(() => { timeline?.kill(); observer?.disconnect(); clearTimeout(timer) })
</script>
<template><span class="motion-anchor" aria-hidden="true" /></template>
