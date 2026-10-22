<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useStage } from '../composables/stage'
import gsap from 'gsap'
import { deck, f1 } from '../data'

const pair = deck.taxonomy.runs[1].group_f1['Applicable Laws / Governing Laws']
const names = deck.taxonomy.pairs.map(pair => pair.join(' / '))
const left = ref<SVGGElement>()
const right = ref<SVGGElement>()
const final = ref<SVGGElement>()
const chips = ref<HTMLElement[]>([])
const shown = ref(0)
const beforeA = ref(0)
const beforeB = ref(0)
let timeline: gsap.core.Timeline | undefined
const radius = (value: number) => Math.sqrt(value) * 102
const labels = () => [...(left.value?.querySelectorAll('text') || []), ...(right.value?.querySelectorAll('text') || [])]
function reset() {
  gsap.set(labels(), { opacity: 1 })
  timeline?.kill(); shown.value = 0; beforeA.value = 0; beforeB.value = 0
  gsap.set(left.value!, { x: -60, opacity: 0, scale: 0.6, transformOrigin: '0px 0px' })
  gsap.set(right.value!, { x: 60, opacity: 0, scale: 0.6, transformOrigin: '0px 0px' })
  gsap.set(final.value!, { opacity: 0, scale: 0.8, transformOrigin: '0px 0px' })
  gsap.set(chips.value, { opacity: 0, y: 10 })
}
useStage({
  setup: reset,
  enter() {
    reset()
    const number = { value: 0 }
    const initial = { a: 0, b: 0 }
    timeline = gsap.timeline({ delay: 0.6 })
      .to([left.value!, right.value!], { x: 0, opacity: 1, scale: 1, duration: 0.8, ease: 'back.out(1.6)', stagger: 0.12 }, 0)
      .to(initial, { a: pair.f1_before_a, b: pair.f1_before_b, duration: 1, ease: 'power2.out', onUpdate: () => { beforeA.value = initial.a; beforeB.value = initial.b } }, 0.3)
      // The two labels fade just before the circles touch, so their texts never overlap.
      .to(labels(), { opacity: 0, duration: 0.35, ease: 'power1.in' }, 1.45)
      .to(left.value!, { x: 148, duration: 1.1, ease: 'power3.inOut' }, 1.6)
      .to(right.value!, { x: -148, duration: 1.1, ease: 'power3.inOut' }, 1.6)
      .to([left.value!, right.value!], { opacity: 0, duration: 0.35 }, 2.5)
      .to(final.value!, { opacity: 1, scale: 1, duration: 0.6, ease: 'back.out(2)' }, 2.45)
      .to(number, { value: pair.f1_after, duration: 1.1, ease: 'expo.out', onUpdate: () => { shown.value = number.value } }, 2.55)
      .to(chips.value, { opacity: 1, y: 0, duration: 0.4, stagger: 0.06, ease: 'power3.out' }, 3.2)
  },
  final() {
    gsap.set([left.value!, right.value!], { opacity: 0 })
    gsap.set(final.value!, { opacity: 1, scale: 1 }); gsap.set(chips.value, { opacity: 1, y: 0 })
    shown.value = pair.f1_after; beforeA.value = pair.f1_before_a; beforeB.value = pair.f1_before_b
  },
})
onBeforeUnmount(()=>timeline?.kill())
</script>
<template>
  <div class="merge-wrap">
    <svg viewBox="0 0 780 390" class="merge-svg" role="img" aria-label="Applicable Laws and Governing Laws merge into one label">
      <defs><filter id="merge-goo"><feGaussianBlur in="SourceGraphic" stdDeviation="11" result="blur" /><feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" result="goo" /><feComposite in="SourceGraphic" in2="goo" operator="atop" /></filter></defs>
      <g>
        <g transform="translate(205,205)"><g ref="left"><circle :r="radius(pair.f1_before_a)" fill="rgba(45,212,191,.13)" stroke="#2dd4bf" stroke-width="2" /><text text-anchor="middle" y="-8" class="merge-label">Applicable Laws</text><text text-anchor="middle" y="36" class="merge-number">{{ f1(beforeA) }}</text></g></g>
        <g transform="translate(575,205)"><g ref="right"><circle :r="radius(pair.f1_before_b)" fill="rgba(212,168,83,.15)" stroke="#d4a853" stroke-width="2" /><text text-anchor="middle" y="-8" class="merge-label">Governing Laws</text><text text-anchor="middle" y="36" class="merge-number">{{ f1(beforeB) }}</text></g></g>
      </g>
      <g transform="translate(390,205)"><g ref="final" opacity="0"><circle :r="radius(pair.f1_after)" fill="rgba(212,168,83,.12)" stroke="#d4a853" stroke-width="3" /><text text-anchor="middle" y="-8" class="merge-label">Merged label</text><text text-anchor="middle" y="36" class="merge-number">{{ shown.toFixed(3) }}</text></g></g>
    </svg>
    <div class="merge-list"><span v-for="(name,index) in names" :key="name" :ref="el => { if (el) chips[index]=el as HTMLElement }">{{ name }}</span></div>
  </div>
</template>
