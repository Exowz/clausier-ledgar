<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import gsap from 'gsap'
import { useStage } from '../composables/stage'

const props = defineProps<{ text: string, emphasis?: string, eyebrow?: string, still?: boolean }>()
const words = computed(() => props.text.split(/\s+/).filter(Boolean))
const elements = ref<HTMLElement[]>([])
const eyebrowElement = ref<HTMLElement>()
let timeline: gsap.core.Timeline | undefined

const hidden = () => {
  gsap.set(elements.value, { yPercent: 110, opacity: 0, rotate: 2 })
  if (eyebrowElement.value) gsap.set(eyebrowElement.value, { opacity: 0, letterSpacing: '0.4em' })
}
const shown = () => {
  gsap.set(elements.value, { yPercent: 0, opacity: 1, rotate: 0 })
  if (eyebrowElement.value) gsap.set(eyebrowElement.value, { opacity: 1, letterSpacing: '0.16em' })
}
useStage({
  setup: () => (props.still ? shown() : hidden()),
  enter() {
    timeline?.kill()
    if (props.still) return shown()
    hidden()
    timeline = gsap.timeline({ delay: 0.15 })
    if (eyebrowElement.value) timeline.to(eyebrowElement.value, { opacity: 1, letterSpacing: '0.16em', duration: 0.9, ease: 'power3.out' }, 0)
    timeline.to(elements.value, { yPercent: 0, opacity: 1, rotate: 0, duration: 0.85, stagger: 0.055, ease: 'expo.out' }, 0.08)
  },
  final: shown,
})
onBeforeUnmount(() => timeline?.kill())
</script>

<template>
  <header class="slide-heading">
    <div v-if="eyebrow" ref="eyebrowElement" class="slide-eyebrow">{{ eyebrow }}</div>
    <h1 class="editorial-headline" :aria-label="text">
      <span v-for="(word, index) in words" :key="`${index}-${word}`" class="headline-mask" aria-hidden="true"><span :ref="el => { if (el) elements[index] = el as HTMLElement }" class="headline-word" :class="{ 'headline-emphasis': emphasis && word.toLowerCase().replace(/[^a-z0-9]/g, '') === emphasis.toLowerCase().replace(/[^a-z0-9]/g, '') }">{{ word }}</span></span>
    </h1>
  </header>
</template>
