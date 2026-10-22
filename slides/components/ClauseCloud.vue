<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useIsSlideActive } from '@slidev/client'
import gsap from 'gsap'
import * as THREE from 'three'
import { cloud } from '../data'

const colors = ['#d4a853', '#2dd4bf', '#f4efe6', '#8a94a6', '#a88958', '#6aaea7', '#b1aaa0', '#475569']
const active = useIsSlideActive()
const mount = ref<HTMLElement>()
const highlighted = ref(-1)
let renderer: THREE.WebGLRenderer | undefined
let scene: THREE.Scene | undefined
let camera: THREE.PerspectiveCamera | undefined
let group: THREE.Group | undefined
let query: THREE.Mesh | undefined
let lines: THREE.Line[] = []
let markers: THREE.Mesh[] = []
let timeline: gsap.core.Timeline | undefined
let frame = 0
let sprite: THREE.Texture | undefined
const lineProgress = cloud.neighbours.map(() => ({ value: 0 }))
const position = (point: number[]) => new THREE.Vector3(point[0] * 3.2, point[1] * 3.2, point[2] * 3.2)
const target = position(cloud.query.point)
function resize() {
  if (!mount.value || !renderer || !camera) return
  const { width, height } = mount.value.getBoundingClientRect()
  renderer.setSize(width, height)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}
function render() {
  if (!renderer || !scene || !camera || !group) return
  if (!location.search.includes('print')) group.rotation.y += 0.00055
  lines.forEach((line, index) => {
    const neighbor = position(cloud.points[cloud.neighbours[index].index])
    const end = target.clone().lerp(neighbor, lineProgress[index].value)
    const coords = line.geometry.attributes.position as THREE.BufferAttribute
    coords.setXYZ(0, target.x, target.y, target.z)
    coords.setXYZ(1, end.x, end.y, end.z)
    coords.needsUpdate = true
    line.visible = lineProgress[index].value > 0
  })
  renderer.render(scene, camera)
  if (!location.search.includes('print')) frame = requestAnimationFrame(render)
}
function animate() {
  if (!camera || !query) return
  timeline?.kill()
  highlighted.value = -1
  camera.position.z = 13
  query.position.copy(target).add(new THREE.Vector3(-5, 3, 2))
  lineProgress.forEach(progress => { progress.value = 0 })
  markers.forEach(marker => { marker.scale.setScalar(1) })
  const reduce = (matchMedia('(prefers-reduced-motion: reduce)').matches || location.search.includes('print'))
  if (reduce) {
    camera.position.z = 8.5
    query.position.copy(target)
    lineProgress.forEach(progress => { progress.value = 1 })
    highlighted.value = cloud.neighbours.length - 1
    return
  }
  timeline = gsap.timeline()
  timeline.to(camera.position, { z: 8.5, duration: 1.3, ease: 'power2.out' }, 0)
  timeline.to(query.position, { x: target.x, y: target.y, z: target.z, duration: 1.0, ease: 'power3.out' }, 0.5)
  lineProgress.forEach((progress, index) => {
    const at = 1.45 + index * 0.26
    timeline!.to(progress, { value: 1, duration: 0.4, ease: 'power2.out', onStart: () => { highlighted.value = index } }, at)
    timeline!.to(markers[index].scale, { x: 1.6, y: 1.6, z: 1.6, duration: 0.16, yoyo: true, repeat: 1 }, at + 0.3)
  })
}
async function start() {
  if (renderer || !active.value) return
  await nextTick()
  if (!mount.value || !active.value) return
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
  group = new THREE.Group(); group.rotation.x = 0.17; scene.add(group)
  const canvas = document.createElement('canvas'); canvas.width = 64; canvas.height = 64
  const ctx = canvas.getContext('2d')!
  const gradient = ctx.createRadialGradient(32,32,0,32,32,32)
  gradient.addColorStop(0,'#fff'); gradient.addColorStop(.35,'rgba(255,255,255,.8)'); gradient.addColorStop(1,'rgba(255,255,255,0)')
  ctx.fillStyle = gradient; ctx.fillRect(0,0,64,64)
  const texture = new THREE.CanvasTexture(canvas)
  sprite = texture
  cloud.types.forEach((_, type) => {
    const points = cloud.points.filter(point => point[3] === type)
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(points.flatMap(point => [point[0]*3.2,point[1]*3.2,point[2]*3.2]), 3))
    group!.add(new THREE.Points(geometry, new THREE.PointsMaterial({ color: colors[type], map: texture, size: 0.12, sizeAttenuation: true, transparent: true, opacity: .7, depthWrite: false, blending: THREE.AdditiveBlending })))
  })
  const star = new THREE.Shape()
  for (let index = 0; index < 10; index++) {
    const angle = -Math.PI / 2 + index * Math.PI / 5
    const radius = index % 2 ? .08 : .18
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius
    if (index === 0) star.moveTo(x,y)
    else star.lineTo(x,y)
  }
  star.closePath()
  query = new THREE.Mesh(new THREE.ShapeGeometry(star), new THREE.MeshBasicMaterial({ color:'#d4a853', side:THREE.DoubleSide }))
  group.add(query)
  cloud.neighbours.forEach(neighbor => {
    const marker = new THREE.Mesh(new THREE.SphereGeometry(.075,12,12), new THREE.MeshBasicMaterial({ color:'#2dd4bf' }))
    marker.position.copy(position(cloud.points[neighbor.index])); group!.add(marker); markers.push(marker)
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([target,target]), new THREE.LineBasicMaterial({ color:'#2dd4bf', transparent:true, opacity:.7 }))
    group!.add(line); lines.push(line)
  })
  renderer = new THREE.WebGLRenderer({ antialias:true, alpha:true })
  renderer.setPixelRatio(Math.min(devicePixelRatio,2)); mount.value.appendChild(renderer.domElement)
  window.addEventListener('resize',resize); resize(); animate()
  if (location.search.includes('print')) render()
  else frame=requestAnimationFrame(render)
}
function stop() {
  timeline?.kill(); cancelAnimationFrame(frame); window.removeEventListener('resize',resize)
  group?.traverse(object => {
    const mesh=object as THREE.Mesh
    mesh.geometry?.dispose()
    const material=mesh.material as THREE.Material | THREE.Material[] | undefined
    if (Array.isArray(material)) material.forEach(item => item.dispose()); else material?.dispose()
  })
  sprite?.dispose(); sprite=undefined
  renderer?.dispose(); renderer?.forceContextLoss(); renderer?.domElement.remove()
  renderer=undefined; scene=undefined; camera=undefined; group=undefined; query=undefined; lines=[]; markers=[]
  highlighted.value=-1
}
watch(active, value => { if (value) start(); else stop() }, { immediate:true })
onBeforeUnmount(stop)
</script>
<template>
  <div class="cloud-layout">
    <div class="cloud-stage">
      <div ref="mount" class="cloud-canvas" />
      <div class="cloud-query">{{ cloud.query.text }}</div>
      <div class="cloud-legend"><span v-for="(type,index) in cloud.types" :key="type"><i :style="{background:colors[index]}" />{{ type }}</span></div>
    </div>
    <div class="cloud-neighbors">
      <div v-for="(neighbor,index) in cloud.neighbours" :key="neighbor.index" class="cloud-neighbor" :class="{active:index<=highlighted}">
        <strong>{{ index+1 }} · {{ neighbor.type }}</strong>
        <p>{{ neighbor.text.slice(0,90) }}…</p>
      </div>
    </div>
  </div>
</template>
