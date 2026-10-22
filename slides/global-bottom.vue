<script setup lang="ts">
import { computed } from 'vue'
import { useNav } from '@slidev/client'

// A thin brass line along the bottom edge that grows with the position in the deck.
const { currentSlideNo, total } = useNav()
const progress = computed(() => Math.min(1, currentSlideNo.value / Math.max(1, total.value - 1)))
</script>

<template>
  <div class="deck-progress" aria-hidden="true"><span :style="{ transform: `scaleX(${progress})` }" /></div>
</template>
