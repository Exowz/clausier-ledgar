<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import gsap from 'gsap'
import { useStage } from '../composables/stage'

const props = withDefaults(defineProps<{ value: number, decimals?: number, prefix?: string, suffix?: string, delay?: number, duration?: number }>(), {
  decimals: 0,
  prefix: '',
  suffix: '',
  delay: 0.3,
  duration: 1.6,
})
const shown = ref(0)
let tween: gsap.core.Tween | undefined
useStage({
  setup: () => { shown.value = 0 },
  enter() {
    tween?.kill()
    const state = { value: 0 }
    shown.value = 0
    tween = gsap.to(state, {
      value: props.value, duration: props.duration, delay: props.delay, ease: 'expo.out',
      onUpdate: () => { shown.value = state.value },
    })
  },
  final: () => { shown.value = props.value },
})
onBeforeUnmount(() => tween?.kill())
</script>

<template>
  <span class="count-up">{{ prefix }}{{ shown.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) }}{{ suffix }}</span>
</template>
