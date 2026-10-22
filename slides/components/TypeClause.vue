<script setup lang="ts">
import { ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'

const props = defineProps<{ clause: string, label: string }>()
const active = useIsSlideActive()
const visible = ref('')
const pill = ref<HTMLElement>()
let tween: gsap.core.Tween | undefined
watch(active, (isActive) => {
  tween?.kill()
  visible.value = ''
  if (pill.value) gsap.set(pill.value, { opacity: 0, rotateX: -85, transformOrigin: 'center bottom' })
  if (!isActive) return
  const state = { length: 0 }
  tween = gsap.to(state, {
    length: props.clause.length,
    duration: 1.45,
    ease: 'none',
    onUpdate: () => { visible.value = props.clause.slice(0, Math.round(state.length)) },
    onComplete: () => gsap.to(pill.value, { opacity: 1, rotateX: 0, duration: 0.65, ease: 'back.out(1.4)' }),
  })
}, { immediate: true })
</script>

<template>
  <div class="typed-clause">
    <div class="typed-text">{{ visible }}<span class="cursor">|</span></div>
    <span ref="pill" class="label-pill">{{ label }}</span>
  </div>
</template>
