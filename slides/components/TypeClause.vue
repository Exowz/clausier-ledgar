<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import gsap from 'gsap'
import { useStage } from '../composables/stage'

const props = defineProps<{ clause: string, label: string }>()
const visible = ref('')
const pill = ref<HTMLElement>()
let timeline: gsap.core.Timeline | undefined
const start = () => {
  visible.value = ''
  if (pill.value) gsap.set(pill.value, { opacity: 0, scale: 0.6, y: 10, filter: 'blur(8px)' })
}
useStage({
  setup: start,
  enter() {
    timeline?.kill()
    start()
    const state = { length: 0 }
    timeline = gsap.timeline({ delay: 0.9 })
      .to(state, {
        length: props.clause.length, duration: 1.6, ease: 'none',
        onUpdate: () => { visible.value = props.clause.slice(0, Math.round(state.length)) },
      })
      .to(pill.value!, { opacity: 1, scale: 1, y: 0, filter: 'blur(0px)', duration: 0.7, ease: 'back.out(2.2)' }, '+=0.15')
  },
  final() {
    visible.value = props.clause
    if (pill.value) gsap.set(pill.value, { opacity: 1, scale: 1, y: 0, filter: 'blur(0px)' })
  },
})
onBeforeUnmount(() => timeline?.kill())
</script>

<template>
  <div class="typed-clause">
    <div class="typed-text">{{ visible }}<span class="cursor">|</span></div>
    <span ref="pill" class="label-pill">{{ label }}</span>
  </div>
</template>
