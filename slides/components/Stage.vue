<script setup lang="ts">
import { ref } from 'vue'
import gsap from 'gsap'
import { useStage } from '../composables/stage'

// Placed once at the top of a slide. On entry it marks the slide root `is-live` (CSS animations are written under
// `.is-live`, so they start when the slide is shown, not when it is created) and reveals the elements that carry
// `data-r` in the order of their value: `data-r="2"` appears after `data-r="1"`.
const props = withDefaults(defineProps<{ delay?: number, step?: number }>(), { delay: 0.35, step: 0.14 })
const anchor = ref<HTMLElement>()
let timeline: gsap.core.Timeline | undefined

const root = () => anchor.value?.parentElement
const staged = () => Array.from(root()?.querySelectorAll<HTMLElement>('[data-r]') || [])
  .sort((a, b) => Number(a.dataset.r) - Number(b.dataset.r))

useStage({
  setup() {
    root()?.classList.remove('is-live', 'is-static')
    gsap.set(staged(), { opacity: 0, y: 26, filter: 'blur(6px)' })
  },
  enter() {
    const slide = root()
    if (!slide) return
    timeline?.kill()
    slide.classList.remove('is-live')
    void slide.offsetWidth
    slide.classList.add('is-live')
    const items = staged()
    gsap.set(items, { opacity: 0, y: 26, filter: 'blur(6px)' })
    timeline = gsap.timeline({ delay: props.delay })
    items.forEach((item) => {
      timeline!.to(item, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.75, ease: 'power3.out' },
        (Number(item.dataset.r) - 1) * props.step)
    })
  },
  final() {
    root()?.classList.add('is-live', 'is-static')
    gsap.set(staged(), { opacity: 1, y: 0, filter: 'blur(0px)' })
  },
})
</script>

<template>
  <span ref="anchor" class="stage-anchor" aria-hidden="true" />
</template>
