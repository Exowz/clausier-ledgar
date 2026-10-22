<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { onSlideLeave } from '@slidev/client'
import { useStage } from '../composables/stage'
import gsap from 'gsap'
import * as THREE from 'three'
import { cloud } from '../data'

const mount = ref<HTMLElement>()
const colors = ['#d4a853', '#2dd4bf', '#f4efe6', '#8a94a6', '#a88958', '#6aaea7', '#b1aaa0', '#475569']
let renderer: THREE.WebGLRenderer | undefined
let scene: THREE.Scene | undefined
let camera: THREE.PerspectiveCamera | undefined
let group: THREE.Group | undefined
let points: THREE.Points | undefined
let target: Float32Array | undefined
let scattered: Float32Array | undefined
let timeline: gsap.core.Timeline | undefined
let frame = 0
// Static contexts (presenter preview, overview, export) draw one still frame and run no loop.
let stillMode = false
let started = 0
const state = { progress: 0 }

function render(now: number) {
  if (!renderer || !scene || !camera || !points || !group || !target || !scattered) return
  const positions = points.geometry.attributes.position as THREE.BufferAttribute
  const drift = Math.min(1, Math.max(0, (now - started) / 500))
  for (let i = 0; i < target.length; i += 3) {
    const p = state.progress
    const sway = (1 - p) * Math.sin(now * 0.0008 + i) * 0.035 * drift
    positions.setXYZ(i / 3,
      scattered[i] * (1 - p) + target[i] * p + sway,
      scattered[i + 1] * (1 - p) + target[i + 1] * p,
      scattered[i + 2] * (1 - p) + target[i + 2] * p)
  }
  positions.needsUpdate = true
  if (!stillMode && !location.search.includes('print')) group.rotation.y += 2 * Math.PI / (90 * 60)
  renderer.render(scene, camera)
  if (!stillMode && !location.search.includes('print')) frame = requestAnimationFrame(render)
}
function resize() {
  if (!mount.value || !renderer || !camera) return
  const { width, height } = mount.value.getBoundingClientRect()
  renderer.setSize(width, height)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}
async function start(still = false) {
  stillMode = still
  if (renderer) return
  await nextTick()
  if (!mount.value) return
  const count = cloud.points.length
  target = new Float32Array(count * 3)
  scattered = new Float32Array(count * 3)
  const shades = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    const point = cloud.points[i]
    target.set([point[0] * 4.5 + 1.75, point[1] * 4.5, point[2] * 4.5], i * 3)
    const seed = (i * 9301 + 49297) % 233280 / 233280
    scattered.set([(seed - 0.5) * 11, (Math.sin(i * 14.13) * 0.5) * 7, (Math.cos(i * 7.31) * 0.5) * 4], i * 3)
    new THREE.Color(colors[point[3] % colors.length]).toArray(shades, i * 3)
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(scattered.slice(), 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(shades, 3))
  const canvas = document.createElement('canvas')
  canvas.width = 64; canvas.height = 64
  const context = canvas.getContext('2d')!
  const gradient = context.createRadialGradient(32, 32, 0, 32, 32, 32)
  gradient.addColorStop(0, 'rgba(255,255,255,1)')
  gradient.addColorStop(0.35, 'rgba(255,255,255,.75)')
  gradient.addColorStop(1, 'rgba(255,255,255,0)')
  context.fillStyle = gradient; context.fillRect(0, 0, 64, 64)
  const texture = new THREE.CanvasTexture(canvas)
  points = new THREE.Points(geometry, new THREE.PointsMaterial({ size: 0.11, map: texture, vertexColors: true, transparent: true, opacity: 0.7, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true }))
  group = new THREE.Group(); group.add(points)
  scene = new THREE.Scene(); scene.add(group)
  camera = new THREE.PerspectiveCamera(44, 1, 0.1, 100)
  camera.position.set(0, 0, 12)
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
  mount.value.appendChild(renderer.domElement)
  window.addEventListener('resize', resize); resize()
  const reduce = stillMode || (matchMedia('(prefers-reduced-motion: reduce)').matches || location.search.includes('print'))
  state.progress = reduce ? 1 : 0
  if (!reduce) timeline = gsap.timeline({ delay: 0.5 }).to(state, { progress: 1, duration: 2.5, ease: 'power3.inOut' })
  started = performance.now()
  if (stillMode || location.search.includes('print')) render(started)
  else frame = requestAnimationFrame(render)
}
function stop() {
  timeline?.kill(); timeline = undefined
  cancelAnimationFrame(frame)
  window.removeEventListener('resize', resize)
  const material = points?.material as THREE.PointsMaterial | undefined
  material?.map?.dispose(); material?.dispose(); points?.geometry.dispose()
  renderer?.dispose(); renderer?.forceContextLoss(); renderer?.domElement.remove()
  renderer = undefined; scene = undefined; camera = undefined; group = undefined; points = undefined
  target = undefined; scattered = undefined
}
let leaveTimer: ReturnType<typeof setTimeout> | undefined
useStage({
  enter: () => { clearTimeout(leaveTimer); stop(); nextTick(() => start()) },
  final: () => { stop(); nextTick(() => start(true)) },
})
// The scene is released only after the slide transition, so the outgoing slide never goes blank.
onSlideLeave(() => { clearTimeout(leaveTimer); leaveTimer = setTimeout(stop, 900) })
onBeforeUnmount(stop)
</script>
<template><div ref="mount" class="clause-field" aria-hidden="true" /></template>
