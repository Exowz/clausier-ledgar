<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import gsap from 'gsap'
import { useStage } from '../composables/stage'

// The Mermaid diagram of this slide is drawn inside a shadow root, out of reach of the page's CSS: its nodes and
// links are found there and animated with GSAP once the diagram exists.
const anchor = ref<HTMLElement>()
let timeline: gsap.core.Timeline | undefined
let poll: ReturnType<typeof setInterval> | undefined
const order = ['LEDGAR', 'TF-IDF', 'LSTM', 'Legal-BERT', 'MiniLM', 'Paired tests', 'Search', 'Audit', 'Additions']

function parts() {
  const root = anchor.value?.parentElement?.querySelector('.mermaid')?.shadowRoot
  const nodes = [...(root?.querySelectorAll<SVGElement>('.node') || [])]
  if (!nodes.length) return undefined
  const edges = [...root!.querySelectorAll<SVGPathElement>('.flowchart-link, .edgePath path')]
  return { nodes: order.flatMap(label => nodes.filter(node => node.textContent?.includes(label))), edges }
}
function whenRendered(callback: (found: NonNullable<ReturnType<typeof parts>>) => void) {
  clearInterval(poll)
  const found = parts()
  if (found) return callback(found)
  let tries = 0
  poll = setInterval(() => {
    const late = parts()
    if (late || ++tries > 40) { clearInterval(poll); if (late) callback(late) }
  }, 75)
}
// Mermaid positions each node with its own transform attribute, so nodes only fade and sharpen: moving them with a
// transform would overwrite their position.
function hide({ nodes, edges }: NonNullable<ReturnType<typeof parts>>) {
  gsap.set(nodes, { opacity: 0, filter: 'blur(6px) brightness(2)' })
  edges.forEach((path) => { const length = path.getTotalLength?.() || 500; gsap.set(path, { strokeDasharray: length, strokeDashoffset: length }) })
}
useStage({
  setup: () => whenRendered(hide),
  enter: () => whenRendered((found) => {
    timeline?.kill()
    hide(found)
    timeline = gsap.timeline({ delay: 0.5 })
      .to(found.nodes, { opacity: 1, filter: 'blur(0px) brightness(1)', duration: 0.7, stagger: 0.16, ease: 'power2.out' })
      .to(found.edges, { strokeDashoffset: 0, duration: 0.9, stagger: 0.07, ease: 'power2.inOut' }, 0.35)
  }),
  final: () => whenRendered(({ nodes, edges }) => gsap.set([...nodes, ...edges], { clearProps: 'all' })),
})
onBeforeUnmount(() => { timeline?.kill(); clearInterval(poll) })
</script>
<template><span ref="anchor" class="motion-anchor" aria-hidden="true" /></template>
