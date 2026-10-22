<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import * as THREE from 'three'
import { cloud } from '../data'

const colors = ['#14213d', '#0f766e', '#a66c26', '#657da5', '#956779', '#64748b', '#438b86', '#949eab']
const active = useIsSlideActive()
const mount = ref<HTMLElement>()
const lineProgress = { value: 0 }
let renderer: THREE.WebGLRenderer | undefined
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let group: THREE.Group
let query: THREE.Mesh
let lines: THREE.Line[] = []
let frame = 0
let tween: gsap.core.Timeline | undefined
const position = (point: number[]) => new THREE.Vector3(point[0] * 3.2, point[1] * 3.2, point[2] * 3.2)
const target = position(cloud.query.point)

function reset() {
  tween?.kill()
  lineProgress.value = 0
  if (query) query.position.copy(target).add(new THREE.Vector3(-5, 3, 2))
  lines.forEach(line => line.visible = false)
  if (group) group.rotation.set(0.17, 0, 0)
}
function animate() {
  reset()
  if (!query) return
  tween = gsap.timeline()
  tween.to(query.position, { x: target.x, y: target.y, z: target.z, duration: 1.2, ease: 'power3.out' })
  tween.to(lineProgress, { value: 1, duration: 0.75, ease: 'power2.out' })
}
function render() {
  frame = requestAnimationFrame(render)
  if (active.value) group.rotation.y += 0.0015
  lines.forEach((line, index) => {
    const neighbor = position(cloud.points[cloud.neighbours[index].index])
    const end = target.clone().lerp(neighbor, lineProgress.value)
    const coords = line.geometry.attributes.position as THREE.BufferAttribute
    coords.setXYZ(0, target.x, target.y, target.z)
    coords.setXYZ(1, end.x, end.y, end.z)
    coords.needsUpdate = true
    line.visible = lineProgress.value > 0
  })
  renderer?.render(scene, camera)
}
function resize() {
  if (!mount.value || !renderer) return
  const { width, height } = mount.value.getBoundingClientRect()
  renderer.setSize(width, height)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}
onMounted(() => {
  scene = new THREE.Scene()
  scene.background = new THREE.Color('#f7f6f2')
  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
  camera.position.set(0, 0, 8.5)
  group = new THREE.Group()
  scene.add(group)
  cloud.types.forEach((_, type) => {
    const points = cloud.points.filter(point => point[3] === type)
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(points.flatMap(point => [point[0] * 3.2, point[1] * 3.2, point[2] * 3.2]), 3))
    group.add(new THREE.Points(geometry, new THREE.PointsMaterial({ color: colors[type], size: 0.048, sizeAttenuation: true })))
  })
  const queryGeometry = new THREE.SphereGeometry(0.13, 16, 16)
  query = new THREE.Mesh(queryGeometry, new THREE.MeshBasicMaterial({ color: '#0f766e' }))
  group.add(query)
  cloud.neighbours.forEach(neighbor => {
    const marker = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 12), new THREE.MeshBasicMaterial({ color: '#b45309' }))
    marker.position.copy(position(cloud.points[neighbor.index]))
    group.add(marker)
    const geometry = new THREE.BufferGeometry().setFromPoints([target, target])
    const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: '#0f766e', transparent: true, opacity: 0.8 }))
    group.add(line)
    lines.push(line)
  })
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  mount.value?.appendChild(renderer.domElement)
  resize()
  window.addEventListener('resize', resize)
  if (active.value) animate(); else reset()
  render()
})
watch(active, value => { if (value) animate(); else reset() })
onBeforeUnmount(() => {
  tween?.kill()
  cancelAnimationFrame(frame)
  window.removeEventListener('resize', resize)
  group?.traverse(object => {
    const mesh = object as THREE.Mesh
    if (mesh.geometry) mesh.geometry.dispose()
    if (Array.isArray(mesh.material)) mesh.material.forEach(material => material.dispose())
    else mesh.material?.dispose()
  })
  renderer?.dispose()
})
</script>

<template>
  <div class="cloud-layout">
    <div class="cloud-stage">
      <div ref="mount" class="cloud-canvas" />
      <div class="cloud-query">{{ cloud.query.text }}</div>
      <div class="cloud-legend"><span v-for="(type, index) in cloud.types" :key="type"><i :style="{ background: colors[index] }" />{{ type }}</span></div>
    </div>
    <div class="cloud-neighbors">
      <div v-for="(neighbor, index) in cloud.neighbours" :key="neighbor.index" class="cloud-neighbor">
        <strong>{{ index + 1 }} · {{ neighbor.type }}</strong>
        <p>{{ neighbor.text.slice(0, 90) }}…</p>
      </div>
    </div>
  </div>
</template>
