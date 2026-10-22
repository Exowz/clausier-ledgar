<script setup lang="ts">
// Slide footer: the deck name, who is speaking on this slide, and the slide number.
defineProps<{ n: string, speaker: string }>()
</script>

<template>
  <div class="deck-footer">
    <span>Clausier · LEDGAR</span>
    <span class="footer-speaker" :class="speaker.toLowerCase().startsWith('wiyao') ? 'is-wiyao' : speaker.toLowerCase().startsWith('ewan') ? 'is-ewan' : ''"><i />{{ speaker }}</span>
    <span>{{ n }}</span>
  </div>
</template>
