<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import { deck } from '../data'

const active = useIsSlideActive()
const handled = Math.round(deck.calibration.tfidf.abstention.test_coverage * 100)
const human = 100 - handled
const dots = computed(() => Array.from({ length: 100 }, (_, index) => {
  const human_index = index - handled
  return {
    index, x: 20 + (index % 10) * 12, y: 60 + Math.floor(index / 10) * 12,
    destinationX: 225 + ((index < handled ? index : human_index) % 10) * 11,
    destinationY: index < handled ? 40 + Math.floor(index / 10) * 11 : 240 + Math.floor(human_index / 10) * 11,
  }
}))
const shownHandled = ref(0)
const shownHuman = ref(0)
const circles = ref<SVGCircleElement[]>([])
let timeline: gsap.core.Timeline | undefined

function play(value: boolean) {
  timeline?.kill()
  shownHandled.value = 0
  shownHuman.value = 0
  circles.value.forEach((circle, index) => gsap.set(circle, { attr: { cx: dots.value[index].x, cy: dots.value[index].y }, opacity: 0.7 }))
  if (!value) return
  const reduce = (window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.location.search.includes('print'))
  if (reduce) {
    circles.value.forEach((circle, index) => gsap.set(circle, { attr: { cx: dots.value[index].destinationX, cy: dots.value[index].destinationY }, opacity: 1 }))
    shownHandled.value = handled; shownHuman.value = human
    return
  }
  timeline = gsap.timeline({ delay: 0.35 })
  circles.value.forEach((circle, index) => {
    const dot = dots.value[index]
    timeline!.to(circle, {
      attr: { cx: dot.destinationX, cy: dot.destinationY }, opacity: 1,
      duration: 1.15, ease: 'power2.inOut',
      onComplete: () => { if (index < handled) shownHandled.value++; else shownHuman.value++ },
    }, index * 0.018)
  })
}
watch(active, play, { flush: 'post', immediate: true })
onMounted(() => play(active.value))
onBeforeUnmount(() => timeline?.kill())
</script>
<template>
  <div class="review-flow">
    <svg viewBox="0 0 560 320" role="img" aria-label="One hundred clauses split between automatic handling and human review">
      <text x="20" y="40" class="flow-caption">100 clauses</text>
      <path d="M172 120 H190 Q205 120 214 86" class="flow-path flow-auto" />
      <path d="M172 120 H190 Q205 120 214 238" class="flow-path flow-human" />
      <rect x="156" y="40" width="16" height="160" rx="8" class="flow-gate" />
      <circle v-for="dot in dots" :key="dot.index" :ref="el => { if (el) circles[dot.index] = el as SVGCircleElement }" :cx="dot.x" :cy="dot.y" r="3.4" :class="dot.index < handled ? 'flow-dot-auto' : 'flow-dot-human'" />
      <text x="350" y="96" class="flow-number flow-auto-text">{{ shownHandled }}</text>
      <text x="350" y="124" class="flow-text flow-auto-text">handled automatically</text>
      <text x="350" y="262" class="flow-number flow-human-text">{{ shownHuman }}</text>
      <text x="350" y="290" class="flow-text flow-human-text">a person checks it</text>
    </svg>
  </div>
</template>
