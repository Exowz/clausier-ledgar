<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'

const props = defineProps<{ text: string, emphasis?: string, eyebrow?: string, still?: boolean }>()
const active = useIsSlideActive()
const words = computed(() => props.text.split(/\s+/).filter(Boolean))
const elements = ref<HTMLElement[]>([])
let timeline: gsap.core.Timeline | undefined
const reduce = () => (window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.location.search.includes('print'))

async function play(value: boolean) {
  await nextTick()
  timeline?.kill()
  if (!elements.value.length) return
  if (!value) {
    gsap.set(elements.value, { y: 24, opacity: 0 })
    return
  }
  if (props.still || reduce()) {
    gsap.set(elements.value, { y: 0, opacity: 1 })
    return
  }
  gsap.set(elements.value, { y: 24, opacity: 0 })
  timeline = gsap.timeline().to(elements.value, {
    y: 0, opacity: 1, duration: 0.7, stagger: 0.05, ease: 'power3.out',
  })
}
watch(active, play, { immediate: true })
onBeforeUnmount(() => timeline?.kill())
</script>

<template>
  <header class="slide-heading">
    <div v-if="eyebrow" class="slide-eyebrow">{{ eyebrow }}</div>
    <h1 class="editorial-headline" :aria-label="text">
      <span v-for="(word, index) in words" :key="`${index}-${word}`" class="headline-mask" aria-hidden="true"><span :ref="el => { if (el) elements[index] = el as HTMLElement }" class="headline-word" :class="{ 'headline-emphasis': emphasis && word.toLowerCase().replace(/[^a-z0-9]/g, '') === emphasis.toLowerCase().replace(/[^a-z0-9]/g, '') }">{{ word }}</span></span>
    </h1>
  </header>
</template>
