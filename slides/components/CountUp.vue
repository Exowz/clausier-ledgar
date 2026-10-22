<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'

const props = withDefaults(defineProps<{ value: number, decimals?: number, prefix?: string, suffix?: string }>(), {
  decimals: 0,
  prefix: '',
  suffix: '',
})
const shown = ref(0)
const active = useIsSlideActive()
let tween: gsap.core.Tween | undefined
watch(active, (isActive) => {
  tween?.kill()
  shown.value = 0
  if (isActive) {
    if ((window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.location.search.includes('print'))) {
      shown.value = props.value
      return
    }
    const state = { value: 0 }
    tween = gsap.to(state, {
      value: props.value,
      duration: 1.3,
      ease: 'power3.out',
      onUpdate: () => { shown.value = state.value },
    })
  }
}, { immediate: true })
onBeforeUnmount(() => tween?.kill())
</script>

<template>
  <span class="count-up">{{ prefix }}{{ shown.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) }}{{ suffix }}</span>
</template>
