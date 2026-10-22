<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import { deck, f1 } from '../data'

const active = useIsSlideActive()
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
function play(value: boolean) {
  timeline?.kill(); shown.value=0; beforeA.value=0; beforeB.value=0
  gsap.set(left.value, { x:0, opacity:1 }); gsap.set(right.value, { x:0, opacity:1 })
  gsap.set(final.value, { opacity:0 }); gsap.set(chips.value, { opacity:0, y:10 })
  if (!value) return
  if ((matchMedia('(prefers-reduced-motion: reduce)').matches || location.search.includes('print'))) {
    gsap.set([left.value,right.value], { opacity:0 })
    gsap.set(final.value, { opacity:1 }); gsap.set(chips.value, { opacity:1, y:0 }); shown.value=pair.f1_after
    beforeA.value=pair.f1_before_a; beforeB.value=pair.f1_before_b
    return
  }
  const number={value:0}
  const initial={a:0,b:0}
  timeline=gsap.timeline()
    .to(initial, { a:pair.f1_before_a, b:pair.f1_before_b, duration:.7, ease:'power2.out', onUpdate:()=>{beforeA.value=initial.a; beforeB.value=initial.b} }, 0)
    .to(left.value, { x:148, duration:1.15, ease:'power2.inOut' }, 0.3)
    .to(right.value, { x:-148, duration:1.15, ease:'power2.inOut' }, 0.3)
    .to([left.value,right.value], { opacity:0, duration:.35 }, 1.25)
    .to(final.value, { opacity:1, duration:.5 }, 1.2)
    .to(number, { value:pair.f1_after, duration:1, ease:'power2.out', onUpdate:()=>{shown.value=number.value} }, 1.35)
    .to(chips.value, { opacity:1, y:0, duration:.35, stagger:.05 }, 2.25)
}
onMounted(()=>play(active.value))
watch(active,play)
onBeforeUnmount(()=>timeline?.kill())
</script>
<template>
  <div class="merge-wrap">
    <svg viewBox="0 0 780 390" class="merge-svg" role="img" aria-label="Applicable Laws and Governing Laws merge into one label">
      <defs><filter id="merge-goo"><feGaussianBlur in="SourceGraphic" stdDeviation="11" result="blur" /><feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" result="goo" /><feComposite in="SourceGraphic" in2="goo" operator="atop" /></filter></defs>
      <g filter="url(#merge-goo)">
        <g ref="left" transform="translate(205,205)"><circle :r="radius(pair.f1_before_a)" fill="rgba(45,212,191,.13)" stroke="#2dd4bf" stroke-width="2" /><text text-anchor="middle" y="-8" class="merge-label">Applicable Laws</text><text text-anchor="middle" y="36" class="merge-number">{{ f1(beforeA) }}</text></g>
        <g ref="right" transform="translate(575,205)"><circle :r="radius(pair.f1_before_b)" fill="rgba(212,168,83,.15)" stroke="#d4a853" stroke-width="2" /><text text-anchor="middle" y="-8" class="merge-label">Governing Laws</text><text text-anchor="middle" y="36" class="merge-number">{{ f1(beforeB) }}</text></g>
      </g>
      <g ref="final" transform="translate(390,205)" opacity="0"><circle :r="radius(pair.f1_after)" fill="rgba(212,168,83,.12)" stroke="#d4a853" stroke-width="3" /><text text-anchor="middle" y="-8" class="merge-label">Merged label</text><text text-anchor="middle" y="36" class="merge-number">{{ shown.toFixed(3) }}</text></g>
    </svg>
    <div class="merge-list"><span v-for="(name,index) in names" :key="name" :ref="el => { if (el) chips[index]=el as HTMLElement }">{{ name }}</span></div>
  </div>
</template>
