<script setup lang="ts">
import background from '../assets/template_toc.png'
</script>

<template>
  <div
    class="slidev-layout chcnav-toc"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <div class="chcnav-toc-word">
      Contents
    </div>
    <div class="chcnav-toc-body">
      <slot />
    </div>
  </div>
</template>
